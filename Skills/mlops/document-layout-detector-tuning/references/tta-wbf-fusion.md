# TTA + Weighted Box Fusion for Document Layout Detection

## Problem

Single-pass YOLO detection misses pictures that are:
- Small cells in a grid layout (conf 0.05–0.15)
- Asymmetrically positioned (flip reveals them)
- Scale-dependent (visible at 1600px but not 1280px)

## Solution: Multi-scale + Flip + WBF

### Pipeline

```python
TTA_IMG_SIZES = (1280, 1600)
TTA_USE_FLIP = True

def _run_detect(img_np, page_w, page_h):
    passes = []
    for imgsz in TTA_IMG_SIZES:
        passes.append(predict_one(img_np, page_w, page_h, imgsz))

    if TTA_USE_FLIP:
        flipped = img_np[:, ::-1, :]
        flip_boxes = predict_one(flipped, page_w, page_h, IMG_SIZE)
        # Unflip x-coordinates
        mapped = []
        for (x1, y1, x2, y2, conf, cat) in flip_boxes:
            mapped.append((page_w - x2, y1, page_w - x1, y2, conf, cat))
        passes.append(mapped)

    if len(passes) == 1:
        return passes[0]
    return fuse_passes(passes, fuse_iou=0.5)
```

### WBF Fusion Algorithm

```python
def _fuse_passes(passes: list[list[tuple]], fuse_iou=0.5) -> list[tuple]:
    """Weighted Box Fusion across TTA passes.
    
    Key insight: conf_fused = 1 - Π(1 - conf_i)
    A box seen by 3 passes at conf=0.07 each → fused conf ≈ 0.20
    This pushes "cohort" boxes above the per-class threshold.
    """
    all_boxes = []
    for pass_idx, boxes in enumerate(passes):
        for box in boxes:
            all_boxes.append((*box, pass_idx))

    # Group by IoU overlap
    groups = []  # each group = list of (box, pass_idx)
    used = [False] * len(all_boxes)

    for i, box_i in enumerate(all_boxes):
        if used[i]:
            continue
        group = [box_i]
        used[i] = True
        for j, box_j in enumerate(all_boxes):
            if used[j]:
                continue
            if box_i[5] != box_j[5]:  # same category only
                continue
            if iou(box_i[:4], box_j[:4]) >= fuse_iou:
                group.append(box_j)
                used[j] = True
        groups.append(group)

    # Merge each group
    fused = []
    for group in groups:
        confs = [b[4] for b in group]
        # Probabilistic fusion: 1 - Π(1 - conf_i)
        fused_conf = 1.0 - math.prod(1.0 - c for c in confs)
        # Weighted average bbox (weight = conf)
        total_w = sum(confs)
        x1 = sum(b[0] * b[4] for b in group) / total_w
        y1 = sum(b[1] * b[4] for b in group) / total_w
        x2 = sum(b[2] * b[4] for b in group) / total_w
        y2 = sum(b[3] * b[4] for b in group) / total_w
        category = group[0][5]
        fused.append((int(x1), int(y1), int(x2), int(y2), fused_conf, category))

    return fused
```

### When to use TTA

- Always: when recall is critical and inference time is acceptable (3x cost)
- Conditional: only when pass-1 finds < 2 strong pictures (conf > 0.30)
  - Caveat: conditional TTA can miss edge cases where split logic depends on fusion output. Prefer always-on for accuracy-critical pipelines.

### Real-world impact (B1_Germany exam)

- Without TTA: p14 cell [0.63, 0.76, 0.77, 0.95] missed entirely (only flip/1280 sees it at conf=0.071)
- With TTA + WBF: cell detected, fused conf=0.071 (single pass), rescued via split logic
- Overall: recall 87.5% → 100%

### Pitfalls

- TTA at imgsz=2048 adds FP without helping recall on standard A4 docs. Stick to 1280+1600.
- Flip pass should use IMG_SIZE (1280), not all scales — diminishing returns.
- Conditional TTA (skip when ≥2 strong pics) can cause subtle regressions when split logic depends on fusion having all passes. Test carefully before enabling.
