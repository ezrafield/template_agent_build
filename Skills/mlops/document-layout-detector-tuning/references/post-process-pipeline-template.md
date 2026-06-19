# Post-process pipeline template

This is the canonical Step2 (`detect_page`) flow for a document-layout
detector after enough tuning iterations to handle the common error classes.

## Pipeline order (mandatory)

```
raw   = run_detect(img, conf=BASE_CONF)        # very loose recall pass
kept  = post_filter(raw, page_area, page_h)     # PER_CLASS_CONF + geometry
kept  = split_wide_picture_into_cells(          # break grid wides into cells
            kept, raw, page_w, page_h)
kept  = class_aware_nms(kept, iou=NMS_IOU)      # group by class, NMS within
blocks = materialize(page_img, kept)            # → LayoutBlock dataclass
blocks = link_captions(blocks)                  # caption → parent picture
if no media in blocks:
    rescued = rescue_picture_from_raw(raw, page_area, page_h)
    if rescued:
        blocks.extend(materialize(rescued))
    elif enable_layout_fallback:
        blocks.extend(opencv_picture_fallback(...))   # last resort
blocks = reading_order(blocks, page_w, page_h)  # XY-cut
```

## Why this order

1. **raw at BASE_CONF=0.05** — see everything the model emitted, even noise.
   Without this rescue gets nothing to work with.
2. **post_filter first** — drops obvious junk (header logos, banners, boxes
   below conf threshold).
3. **split_wide BEFORE NMS** — wide row dominates cells in NMS. Split first,
   then let NMS dedupe siblings normally.
4. **class-aware NMS** — global NMS lets a Caption suppress a Picture above
   it. Group by class, then NMS within class only.
5. **rescue BEFORE OpenCV fallback** — OpenCV contour detection on text-heavy
   pages emits 5+ FPs. Trust the raw model first.

## Function shapes

### post_filter (conf + geometry + header/footer)

```python
def post_filter(raw, page_area, page_h):
    kept = []
    for (x1, y1, x2, y2, conf, category) in raw:
        if category in SKIP_CLASSES:                # page_header, page_footer
            continue
        thresh = PER_CLASS_CONF.get(category)
        if thresh is None or conf < thresh:
            continue
        w, h = x2 - x1, y2 - y1
        if w < MIN_SIDE_PX or h < MIN_SIDE_PX:
            continue
        ar = (w * h) / max(page_area, 1)
        if ar < MIN_AREA_RATIO or ar > MAX_AREA_RATIO:
            continue
        if category == "picture" and ar < MIN_PICTURE_AREA_RATIO:
            continue
        if category == "picture" and page_h > 0:
            ny1, ny2 = y1 / page_h, y2 / page_h
            if ny2 <= HEADER_BAND_Y_MAX or ny1 >= FOOTER_BAND_Y_MIN:
                continue
            if w > 0:
                ar_hw = h / w
                if ar_hw < PICTURE_AR_MIN or ar_hw > PICTURE_AR_MAX:
                    continue
        kept.append((x1, y1, x2, y2, conf, category))
    return kept
```

### split_wide_picture_into_cells

```python
def split_wide_picture_into_cells(kept, raw, page_w, page_h):
    out = []
    for box in kept:
        x1, y1, x2, y2, conf, cat = box
        if cat != "picture":
            out.append(box); continue
        w, h = x2 - x1, y2 - y1
        is_wide = (w / page_w) >= 0.40 and (h / w) < 0.7
        if not is_wide:
            out.append(box); continue
        cells = []
        for (rx1, ry1, rx2, ry2, rconf, rcat) in raw:
            if rcat != "picture" or rconf < 0.10:
                continue
            rw, rh = rx2 - rx1, ry2 - ry1
            if rw >= w * 0.9 and rh >= h * 0.9:
                continue                               # is the wide itself
            inter_w = max(0, min(x2, rx2) - max(x1, rx1))
            inter_h = max(0, min(y2, ry2) - max(y1, ry1))
            if rw * rh <= 0:
                continue
            if (inter_w * inter_h) / (rw * rh) >= 0.85:
                cells.append((rx1, ry1, rx2, ry2, rconf, rcat))
        if len(cells) >= 2:
            cells = geom_filter_picture(cells, page_w * page_h, page_h)
            if cells:
                out.extend(cells); continue
        out.append(box)
    return out
```

### geom_filter_picture (geometry only — for cells)

```python
def geom_filter_picture(boxes, page_area, page_h):
    """Same geometry filters as post_filter but skips PER_CLASS_CONF
    because cells legitimately have low conf."""
    out = []
    for (x1, y1, x2, y2, conf, cat) in boxes:
        if cat != "picture":
            continue
        # ...same geometry checks (size, area, header/footer, AR)...
        out.append((x1, y1, x2, y2, conf, cat))
    return out
```

### rescue_picture_from_raw

```python
def rescue_picture_from_raw(raw, page_area, page_h):
    """Page has zero media after post_filter — pick the SINGLE highest-conf
    raw picture box that passes geometry filters, with conf ≥ 0.05."""
    candidates = []
    for (x1, y1, x2, y2, conf, cat) in raw:
        if cat != "picture" or conf < 0.05:
            continue
        # geometry checks (header/footer, AR, area)
        # rescue_max_area_ratio = 0.40 — refuse super-wide rescues that are
        # likely text blocks, even if the model said "picture"
        if (w * h) / page_area > 0.40:
            continue
        candidates.append(...)
    candidates.sort(key=lambda b: b[4], reverse=True)
    return [candidates[0]] if candidates else []
```

## Order matters for split_wide

Run split BEFORE NMS, AFTER post_filter:
- BEFORE NMS so the original wide and its split cells don't fight via IoU
- AFTER post_filter so we only consider trusted wides as candidates for
  splitting. Untrusted wides shouldn't trigger cell extraction.

If you split AFTER NMS, NMS already removed cells that overlapped the wide,
so split has nothing to find.
