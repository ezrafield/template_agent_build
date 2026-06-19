# Layout-first document parsing architecture

Source skill absorbed: `document-layout-detection`.

## Decision

Prefer **layout-first** document parsing when a YOLO/DocLayNet-style detector is good enough:

1. Render PDF pages to images.
2. YOLO detects layout blocks and freezes bbox/class structure.
3. MLLM fills content per block ID only.
4. Evaluation compares layout separately from text/content.

This avoids MLLM bbox drift and removes post-hoc IoU reconciliation code.

## Model choice

- DocLayNet-style weights have classes such as Picture, Table, Formula, Caption, Section-header, Title, Text, List-item, Footnote, Page-header, Page-footer.
- COCO weights do not have document Picture/Table semantics and should not be ensemble partners for document layout detection.

## Layout-only eval format

When building no-MLLM eval output, normalize YOLO pixel boxes into evaluator format:

```python
# YOLO pixels: x1, y1, x2, y2
image_bbox = [y1 / page_h, x1 / page_w, y2 / page_h, x2 / page_w]
```

Include `_yolo_class` and `_yolo_conf` in debug JSON so FP/FN diagnosis can inspect model behavior without re-running inference.
