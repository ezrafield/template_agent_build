---
name: document-layout-detector-tuning
description: Tune a YOLO/DocLayNet document-layout detector — fix FPs (logos/banners), recover misses (grid cells, low-conf), build no-MLLM eval harness. Targets recall/precision via post-process, no retrain needed.
---

# document-layout-detector-tuning

Class of work: you have a document-layout detector (yolov10/yolov8/RT-DETR fine-tuned on DocLayNet, PubLayNet, M⁶Doc — 11ish classes including Picture/Table/Caption/Section-header) and the picture/table recall+precision on a real document is not where you want it. The model is fixed; only post-processing is tunable.

This skill is for that loop: measure → diagnose miss/FP → patch post-process → measure. Re-applies cleanly to any project parsing exam papers, scanned books, magazines, PDFs with mixed text+image grids.

## When to load

- Picture/Table mAP@50 below 70% on a new document, model already trained
- "FP từ logo header / footer / banner" — bbox at top/bottom edge consistently misclassified as Picture
- Grid-layout pages (4-up images, 2x2 photo cells) detect 1 wide box instead of N cells
- OpenCV fallback fires on text-heavy pages and spams false picture boxes
- User asks to test/tune accuracy of a layout pipeline before running expensive MLLM extraction
- Pipeline includes a step where YOLO output feeds a downstream MLLM and bbox quality matters more than text quality

## The iteration loop

Always run in this order. Skipping #1 means burning MLLM API budget on noise.

### 1. Build a layout-only eval harness (no MLLM, no API cost)

The most expensive mistake is iterating with the full pipeline. Build a tiny eval script that:
- Loads PDF → page images (Step1)
- Runs detector + post-processing (Step2 only)
- Dumps a fake `step3_raw.json` containing only `picture` blocks with `image_bbox` in the format your evaluator expects (commonly `[y_min, x_min, y_max, x_max]` normalized 0–1)
- Calls the existing IoU/mAP@50 evaluator

See `references/eval-layout-only-recipe.md` for a full template. Iterating against this is seconds per cycle vs minutes + API spend.

### 2. Inspect RAW detections before filtering

`PER_CLASS_CONF` and post-filter hide what the model actually sees. Write a 30-line probe that runs `model.predict(img, conf=0.05, imgsz=1280)` and prints every box with class/conf/bbox-norm/area. This reveals:
- Whether a missed truth has any raw box at all (model truly blind → can't fix without retrain)
- Whether a missed truth has a low-conf box just below threshold (raise recall by lowering threshold or rescuing)
- Whether wide-row boxes are dominating cell-level boxes via NMS

### 3. Diagnose each error class

For each miss / FP, classify:

| Pattern | Symptom | Fix |
|---|---|---|
| Header/footer logo as Picture | bbox y_max ≤ 0.10 or y_min ≥ 0.92 | Add header/footer band filter on category=picture |
| Banner (page divider) as Picture | h/w < 0.18 (very thin horizontal) | Add `PICTURE_AR_MIN` aspect-ratio filter |
| Grid-layout miss (model detects 1 wide row, truth is 4 cells) | wide bbox conf high, cell bboxes conf 0.10–0.20 below threshold | Implement `_split_wide_picture_into_cells`: when picture width ≥ 0.40 page_w and h/w < 0.7, look for ≥2 cell-level boxes (conf ≥ 0.10) contained ≥85% inside; replace wide with cells |
| Whole page blank (model conservative on lost trang) | post-filter returns 0 media | Rescue: take the highest-conf raw picture box conf ≥ 0.05 that passes geometry-only filters. Cap at 1 box to avoid spam. |
| OpenCV fallback fires on text-heavy page | many FPs from contour detection | Make rescue from raw-YOLO take precedence over OpenCV fallback. Only fall through to OpenCV when raw YOLO has zero picture candidates. |

### 4. Re-apply post-filter after every transformation

When you split a wide box into cells, the cells may now violate filters (header band, aspect ratio). Re-apply geometry filters after every transformation. Do NOT re-apply confidence filter — cells legitimately have low conf.

This is why splitting `_post_filter` into `_post_filter` (conf + geometry) and `_geom_filter_picture` (geometry only) matters.

### 5. Validate "FP" with vision before chasing them

Some "FPs" are model right + ground truth wrong. Use the vision tool to look at the rendered debug overlay PNG of the page and ask "is there actually a picture in this bbox?" Multiple times you'll find truth missed an annotation. Don't tune the model down to silence the model when it's correct.

## Configuration knobs (DocLayNet 11-class)

Conservative starting point:

```python
PER_CLASS_CONF = {
    "picture":        0.20,   # nới recall, lọc FP bằng geometry
    "table":          0.35,
    "formula":        0.30,
    "caption":        0.25,
    "section_header": 0.25,
    "title":          0.25,
    "text":           0.20,
    "list_item":      0.20,
    "footnote":       0.25,
}
BASE_CONF = 0.05              # raw pass — chỉ để rescue thấy được
HEADER_BAND_Y_MAX = 0.11      # picture y_max ≤ này → loại
FOOTER_BAND_Y_MIN = 0.92      # picture y_min ≥ này → loại
PICTURE_AR_MIN = 0.18         # h/w nhỏ hơn → banner
PICTURE_AR_MAX = 4.0          # h/w lớn hơn → sọc dọc (6.0 too permissive)
MIN_PICTURE_AREA_RATIO = 0.010 # < 1% trang → noise
NMS_IOU = 0.45                # class-aware NMS
IMG_SIZE = 1280
```

Wide/Large-split parameters:

```python
WIDE_W_RATIO = 0.40           # picture ≥40% page_w + h/w<0.7 → check split
MAX_AR_HW_FOR_WIDE = 0.7
TALL_H_RATIO = 0.40           # picture ≥40% page_h + h/w>1.5 → check split
LARGE_AREA_RATIO = 0.15       # picture ≥15% page area → MUST split regardless of AR
CELL_MIN_CONF = 0.10
CELL_CONTAIN_MIN = 0.85       # cell phải nằm ≥85% trong wide
# If split finds 0 cells → DROP the big box (it's wrapping a text grid)
# If split finds 1 cell and cell_area < 60% of big_area → REPLACE big with cell
```

## TTA (Test-Time Augmentation) for hard pages

When single-pass detection misses pictures (especially grid cells, small illustrations):

```python
TTA_IMG_SIZES = (1280, 1600)   # multi-scale
TTA_USE_FLIP = True            # horizontal flip catches asymmetric misses
```

Pipeline:
1. Run predict at each scale → collect passes
2. Run predict on horizontally-flipped image at IMG_SIZE → unflip boxes
3. Fuse all passes with Weighted Box Fusion (WBF):
   - Group boxes across passes by IoU > 0.5
   - Merged conf = 1 - Π(1 - conf_i) — boxes seen by multiple passes get boosted
   - This pushes low-conf cells (0.07) above threshold when 2+ passes agree

Cost: 3x inference time. Worth it when recall matters more than speed.

**WARNING: Conditional TTA is unreliable.** Attempting to skip TTA when pass-1 finds ≥2 strong pictures causes subtle fusion output changes (box ordering, merge behavior) that break downstream split logic. The recall regression is hard to diagnose because it's not a threshold issue — it's fusion non-determinism from pass reordering. Always run full TTA in production; optimize speed elsewhere (batch inference, GPU, lower DPI on easy pages).

## Adaptive PageProfile

Instead of hardcoded thresholds, analyze each page to select appropriate profile:

```python
@dataclass
class PageProfile:
    bg_mean: float       # mean intensity of page background
    is_dark_bg: bool     # dark slide/poster
    is_landscape: bool   # w > h
    header_y: float      # adaptive header band
    footer_y: float      # adaptive footer band
    ar_min: float        # adaptive AR limits
    ar_max: float
    rescue_max_area: float
    suppress_mean_thresh: float
    suppress_std_thresh: float
```

Detection logic:
- Sample corners + edges → compute bg_mean/bg_std
- `is_dark_bg = bg_mean < 128`
- `is_landscape = page_w > page_h`

Profile selection:
| Page type | header_y | footer_y | AR range | rescue_max_area | suppress |
|---|---|---|---|---|---|
| Portrait A4 (default) | 0.11 | 0.92 | 0.18–4.0 | 0.15 | mean>222, std<80 |
| Landscape slide | 0.08 | 0.95 | 0.12–6.0 | 0.35 | same |
| Dark background | same | same | same | same | mean<bg*0.9, std<60 |

Key insight: keep proven defaults for portrait A4 (most documents), only nới for detected landscape/dark. Don't generalize by loosening — generalize by detecting and branching.

## Text-grid suppress (pixel-stats FP filter)

For small picture boxes (area < 5% page, conf < 0.95) that are actually text/checkbox grids:

```python
def _text_grid_suppress(boxes, img_np, page_area, profile):
    for box in boxes:
        if area_ratio > 0.05 or conf >= 0.95:
            keep  # large or high-conf → trust model
        crop = gray[y1:y2, x1:x2]
        mean_int = np.mean(crop)
        std = np.std(crop)
        # Light page: FP has mean > 222 (near white) + std < 80 (low texture)
        # Dark page: FP has mean < bg*0.9 (near bg) + std < 60
        if matches_fp_signature:
            drop
```

This catches text grids, checkbox arrays, R/F answer grids that model misclassifies as picture. Real pictures have either low mean (dark content) or high std (rich texture).

## Pitfalls

- **BASE_CONF too high** kills rescue. The raw pass has to see boxes below your final threshold or rescue logic gets nothing to work with. Set BASE_CONF to 0.05 even if PER_CLASS_CONF["picture"] is 0.30.
- **Class-aware NMS, not global NMS.** A Caption directly under a Picture should not suppress it. Group by class then NMS within group.
- **Don't re-apply PER_CLASS_CONF to split cells.** Cells legitimately have lower conf than the wide box that contained them; that's why the model emitted a wide box in the first place.
- **OpenCV picture fallback is noisy on text pages.** A text-heavy exam page will spawn 5+ FPs from contour detection. Rescue-from-raw should take precedence; OpenCV fallback only when raw YOLO emits zero picture candidates anywhere. Better: disable OpenCV fallback entirely when model is good enough.
- **Header band cutoff must be > model's clamp.** YOLO often clamps boxes to image height producing y_max=0.0998. If `HEADER_BAND_Y_MAX = 0.10` you let those through. Use 0.11.
- **Truth ground-truth often misses pictures**. Validate FPs visually before assuming the model is wrong. Common in exam/textbook annotations: ads with mixed text+image, decorative logos, small inline icons. When the only remaining "FP" is visually a real picture, patch the truth file rather than suppressing the model.
- **DPI=220 not 200.** Sweet spot for `imgsz=1280` on yolov10/v8 doc-layout. DPI=200 truncates fine details on small picture cells.
- **Imports in package subfolders.** When the layout package lives in a subfolder (e.g. `V2/`), run as `python -m V2.pipeline` or inject `sys.path` for parent. `from .step1_pages` works inside the package; `from V2.step1_pages` works from outside.
- **AR_MAX = 4.0 not 6.0.** AR_MAX=6.0 lets through tall narrow text columns as FP. 4.0 catches real pictures while filtering vertical strips. Only nới to 6.0 for landscape slides.
- **Rescue area cap matters.** Without `rescue_max_area ≤ 0.15`, rescue grabs wide text-grid boxes (20%+ page area) that look like pictures. For portrait A4, cap at 15%. For landscape slides, allow up to 35%.
- **Split must handle 0-cell and 1-cell cases.** If a big box has 0 cells in raw → DROP it (it's wrapping a text grid, not a picture). If 1 cell and cell_area < 60% of big_area → REPLACE big with cell (the cell is the real picture, the big box is over-extended).
- **Don't generalize by loosening thresholds.** When adding adaptive support for new doc types, keep proven defaults for the common case (portrait A4). Only override when you positively detect landscape/dark. Loosening globally (e.g. AR_MIN 0.18→0.15, HEADER 0.11→0.10, MIN_PICTURE_AREA 0.010→0.008) causes precision regression on existing data. In one session, loosening 4 thresholds simultaneously dropped precision from 88% to 38% — a 50-point regression from "generalization" that wasn't tested on new data.
- **Conditional TTA causes subtle recall regression.** See TTA section above. Don't try to optimize by skipping passes — fusion is order-sensitive.
- **Eval must filter by exact class.** If your eval dumps all MEDIA_CLASSES (picture+table+formula) as `block_type=picture`, tables will count as FP against picture-only ground truth. Filter pred to match the exact class being evaluated.
- **Production cleanup: remove debug/inspect files before deploy.** After tuning, delete all `_inspect_*.py` probe scripts and patched truth files. Keep only: pipeline steps, eval harness, and test suite. The user expects a clean `V2/` folder ready to `cp -r` to production.
- **Visual content filter (edge density + hline ratio) is unreliable.** Truth pictures often have high hline ratios (>0.5) and edge density similar to text grids. Pixel-stats filters should only use mean+std (background similarity), not edge/hline features which don't discriminate well.

## Verification

A fix is good when:
1. Recall doesn't drop on previously-passing pages
2. Precision improves on the page you targeted
3. meanIoU stays ≥ 85% (bbox quality intact)
4. Total picture count is in same ballpark as truth count (within 1.5x)

A fix is wrong when meanIoU drops sharply — you've allowed loose boxes through that match by area but not shape.

## References

- `references/eval-layout-only-recipe.md` — copy-paste recipe for the no-MLLM eval harness
- `references/post-process-pipeline-template.md` — annotated post-process pipeline (run_detect → post_filter → split_wide → NMS → rescue → fallback)
- `references/case-study-b1-germany.md` — full numerical journey from 25%→87.5% recall on a real B1 German exam, with each diagnosis and fix step
- `references/tta-wbf-fusion.md` — TTA multi-scale + flip + Weighted Box Fusion implementation pattern, when to use, real-world impact
- `references/adaptive-page-profile.md` — adaptive threshold system: detect page type (portrait/landscape/dark) and branch thresholds without loosening defaults

## Architecture decision: layout-first vs MLLM-first

- **MLLM-first (V1-style):** send full page to GPT-4V/Gemini, ask for bbox + content, then crop with YOLO to verify. MLLM bbox drifts; lots of post-hoc IoU matching code.
- **Layout-first (V2-style, preferred):** YOLO detects bbox + class first, freezes structure, MLLM only fills content per `block_id`. No bbox drift, less code.

## Model selection reminder

Always check the class list before adopting a YOLO weight:

```python
from ultralytics import YOLO
m = YOLO("model.pt")
print(m.names)   # COCO has 80 classes, no Picture/Table; DocLayNet has 11
```

- `yolov10m_best.pt` / DocLayNet-style 11-class weights can detect Picture/Table/Formula/Caption/etc.
- COCO YOLO weights are not useful for document layout media detection; do not ensemble them with a doc model.
- DPI around 220 with `imgsz=1280` is a strong starting point for exam/document pages.

## Eval template notes from absorbed sibling

The older `document-layout-detection` skill carried two useful support-file ideas that belong here:

- `references/eval_layout_only_template.py` — layout-only pred JSON builder that writes `image_bbox` as `[y_min, x_min, y_max, x_max]` normalized 0–1 and invokes the project evaluator.
- `references/diagnose_fp_fn.py` — truth/pred walker that prints unmatched truth and unmatched pred per page.

If those exact scripts are needed, reconstruct them under this umbrella's `references/` or use `references/eval-layout-only-recipe.md` plus the FP/FN diagnostic recipe above.

## Related skills

- `software-development/systematic-debugging` — for the diagnosis methodology (this skill is the doc-layout-specific instantiation)
- `software-development/optimization-loop` — for running this iteratively as an autonomous loop
- `mlops/segment-anything-model` — alternative when YOLO doc-layout misses; SAM with point prompts can rescue
