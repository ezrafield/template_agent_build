# No-MLLM eval harness recipe

The point: iterating on layout post-processing against the full pipeline
(Step1→2→3 MLLM→4→5) is slow + expensive. Build a tiny eval that runs only
Step1+Step2 and produces a JSON the existing evaluator accepts.

## Skeleton

```python
"""V2/eval_layout_only.py — accuracy without MLLM call."""
from __future__ import annotations
import json, logging, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from V2.step1_pages import PDFToImages
from V2.step2_layout import LayoutDetector, MEDIA_CLASSES
from V2.step5_evaluate import JSONEvaluator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("V2.eval_layout")

TRUTH_PATH = PARENT / "groundtrust.json"
PDF_PATH = PARENT / "B1_Germany.pdf"
DEFAULT_OUT = PARENT / "output_v2" / "B1_Germany"


def page_range_from_truth(truth_path: Path) -> tuple[int, int]:
    data = json.loads(truth_path.read_text(encoding="utf-8"))
    pages = sorted({p["page_number"] for p in data})
    return pages[0], pages[-1]


def build_layoutonly_pred(pdf_path, out_path, page_range, yolo_model, dpi=220):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_to_imgs = PDFToImages(dpi=dpi)
    all_pages = pdf_to_imgs.load(str(pdf_path))
    p_lo, p_hi = page_range
    pages = [p for p in all_pages if p_lo <= p.page_number <= p_hi]

    detector = LayoutDetector(model_path=str(yolo_model))
    pages_blocks = [(pg, detector.detect_page(pg)) for pg in pages]

    pred_pages = []
    for page_img, blocks in pages_blocks:
        w, h = page_img.image.size
        exam_blocks = []
        for b in blocks:
            if b.category not in MEDIA_CLASSES:
                continue
            x1, y1, x2, y2 = b.bbox
            ny1, nx1 = max(0, y1/h), max(0, x1/w)
            ny2, nx2 = min(1, y2/h), min(1, x2/w)
            exam_blocks.append({
                "block_type": "picture",
                "section": "unknown",
                "image_bbox": [round(ny1, 4), round(nx1, 4),
                               round(ny2, 4), round(nx2, 4)],
                "_yolo_class": b.category,
                "_yolo_conf": round(b.confidence, 3),
            })
        pred_pages.append({
            "page_number": page_img.page_number,
            "page_type": "exam_content",
            "blocks": exam_blocks,
        })

    out_path.write_text(json.dumps(pred_pages, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    return out_path


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", default=str(PDF_PATH))
    p.add_argument("--truth", default=str(TRUTH_PATH))
    p.add_argument("--yolo", default=str(PARENT / "yolov10m_best.pt"))
    p.add_argument("--out", default=str(DEFAULT_OUT / "step3_raw_layoutonly.json"))
    p.add_argument("--iou-threshold", type=float, default=0.5)
    args = p.parse_args()

    pr = page_range_from_truth(Path(args.truth))
    build_layoutonly_pred(Path(args.pdf), Path(args.out), pr, Path(args.yolo))

    JSONEvaluator(
        truth_path=args.truth,
        pred_path=args.out,
        iou_threshold=args.iou_threshold,
    ).evaluate()


if __name__ == "__main__":
    main()
```

## Critical detail: bbox format

The evaluator likely uses `[y_min, x_min, y_max, x_max]` normalized 0–1 (this
is what DocLayNet / common eval harnesses use). YOLO output is `[x1, y1, x2,
y2]` in pixels. Don't ship pixels — divide by page_w/page_h FIRST, then permute.

If the eval reports recall 0% with meanIoU 0%, check format mismatch first.

## What to print on each iteration

```
=== MISSED ===
  p14: truth=[0.6324, 0.758, 0.7676, 0.9524]  bestIoU=0.000

=== FP ===
  p13: pred=[0.7335, ...] conf=0.684  bestIoU=0.000
```

This 6-line script lives next to the eval harness and tells you exactly which
pattern to fix next:

```python
import json
truth = json.load(open(TRUTH))
pred  = json.load(open(PRED))
# walk_bbox(truth) gathers all image_bbox recursively (truth often nests them)
# print missed truth + closest pred + best IoU
# print FP pred + closest truth
```

Crucially, walk truth recursively — image_bbox in DocLayNet/exam ground truth
is often nested inside non-`picture` blocks (e.g. an "instruction" block with
attached illustration).

## Iteration cadence

Targeting this harness, each fix-then-measure cycle is ~30–60 seconds (Step1
PDF render is the bottleneck). Cap each cycle at one diagnosed change. Don't
batch fixes — you lose attribution of which change moved the needle.
