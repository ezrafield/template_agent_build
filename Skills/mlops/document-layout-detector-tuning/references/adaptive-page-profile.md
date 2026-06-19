# Adaptive PageProfile — Generalization Without Loosening

## Problem

Hardcoded thresholds (header_y=0.11, AR_MAX=4.0, suppress_mean=222) work perfectly for portrait A4 exam papers but fail on:
- Landscape slides (header/footer smaller, pictures wider)
- Dark-background posters (FP signature inverts)
- Scanned books (different margins)

Naive fix: loosen all thresholds → precision tanks on the common case.

## Solution: Detect page type, branch thresholds

```python
@dataclass
class PageProfile:
    bg_mean: float = 255.0
    bg_std: float = 0.0
    is_dark_bg: bool = False
    is_landscape: bool = False
    header_y: float = 0.11
    footer_y: float = 0.92
    ar_min: float = 0.18
    ar_max: float = 4.0
    rescue_max_area: float = 0.15
    suppress_mean_thresh: float = 222.0
    suppress_std_thresh: float = 80.0
```

## Detection Logic

```python
def _analyze_page_profile(img_np, page_w, page_h):
    profile = PageProfile()
    profile.is_landscape = page_w > page_h
    profile.aspect_ratio = page_h / max(page_w, 1)

    # Sample background from corners + edges (avoid center content)
    h, w = img_np.shape[:2]
    samples = []
    band = max(1, int(min(h, w) * 0.05))
    # Top-left, top-right, bottom-left, bottom-right corners
    for region in [img_np[:band, :band], img_np[:band, -band:],
                   img_np[-band:, :band], img_np[-band:, -band:]]:
        if region.ndim == 3:
            region = np.mean(region, axis=2)
        samples.append(region.flatten())
    
    all_samples = np.concatenate(samples)
    profile.bg_mean = float(np.mean(all_samples))
    profile.bg_std = float(np.std(all_samples))
    profile.is_dark_bg = profile.bg_mean < 128

    # Branch thresholds
    if profile.is_landscape:
        profile.header_y = 0.08
        profile.footer_y = 0.95
        profile.ar_min = 0.12
        profile.ar_max = 6.0
        profile.rescue_max_area = 0.35
    # else: keep proven portrait defaults

    if profile.is_dark_bg:
        profile.suppress_mean_thresh = profile.bg_mean * 0.9
        profile.suppress_std_thresh = 60.0
    else:
        profile.suppress_mean_thresh = 222.0
        profile.suppress_std_thresh = 80.0

    return profile
```

## Key Principle

**Keep proven defaults for the common case. Only override when you positively detect a different page type.**

This is the opposite of "generalize by loosening":
- BAD: `AR_MAX = 6.0` for all pages → tall text columns become FP on portrait A4
- GOOD: `AR_MAX = 4.0` default, override to 6.0 only when `is_landscape=True`

## Profile table

| Page type | Detection | header_y | footer_y | AR | rescue_area | suppress |
|---|---|---|---|---|---|---|
| Portrait A4 | w < h, bg_mean > 128 | 0.11 | 0.92 | 0.18–4.0 | 15% | mean>222, std<80 |
| Landscape slide | w > h | 0.08 | 0.95 | 0.12–6.0 | 35% | same as bg |
| Dark poster | bg_mean < 128 | inherit | inherit | inherit | inherit | mean<bg*0.9, std<60 |

## Integration

Pass profile through the pipeline:
```python
profile = self._analyze_page_profile(img_np, page_w, page_h)
raw = self._run_detect(img_np, page_w, page_h, profile)
kept = self._post_filter(raw, page_area, page_h, profile)
kept = self._text_grid_suppress(kept, img_np, page_area, profile)
# rescue also receives profile for adaptive area/band limits
```

## Pitfalls

- Don't compute bg_mean from the whole page — center content skews it. Sample corners only.
- Don't use `max(222, bg_mean - 25)` for suppress threshold — on white pages (bg_mean=250) this gives 225 which is LOWER than the proven 222, letting more FP through. Just hardcode 222 for light pages.
- Profile detection adds ~1ms per page (negligible vs YOLO inference).
- When adding a new page type, add a new branch — don't modify existing defaults.
