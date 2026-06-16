"""Pure geometry helpers: aspect detection, default overlay rects, coordinate mapping.

No Qt, no I/O. screenWH() lives in the Qt-side adapter because it needs
QGuiApplication; everything here is testable without a GUI.
"""


def detect_aspect_label(w: int, h: int) -> str:
    """
    Aspect bucketing
    32:9 if a >= 3.20
    21:9 if a >= 2.20
    else 16:9
    """
    if h <= 0:
        return "16:9"
    a = float(w) / float(h)
    if a >= 3.20:
        return "32:9"
    if a >= 2.20:
        return "21:9"
    return "16:9"


def default_rect_ratio_16_9():
    return {
        "rx": 0.308203125,
        "ry": 0.13819444444444445,
        "rw": 0.384375,
        "rh": 0.6833333333333333,
    }


def default_rect_ratio_21_9():
    return {"rx": 0.35625, "ry": 0.13796296296296295, "rw": 0.287890625, "rh": 0.6833333333333333}


def default_rect_ratio_32_9():
    return {"rx": 0.40390625, "ry": 0.1375, "rw": 0.1921875, "rh": 0.6833333333333333}


def default_rect_ratio_by_aspect():
    return {
        "16:9": default_rect_ratio_16_9(),
        "21:9": default_rect_ratio_21_9(),
        "32:9": default_rect_ratio_32_9(),
    }


def rotate90cw_norm(x, y):
    """
    Converts 4096 map coordinates into normalized u,v (0..1) after 90° clockwise rotation.
    v is top down for painting.
    """
    xr = float(y)
    yr = 4095.0 - float(x)
    u = xr / 4095.0
    v = yr / 4095.0
    if u < 0:
        u = 0.0
    if u > 1:
        u = 1.0
    if v < 0:
        v = 0.0
    if v > 1:
        v = 1.0
    return u, v


def norm_to_grid(u, v):
    """Inverse of rotate90cw_norm: normalized (u, v) back to 4096-grid (x, y).

    From the forward map  u = y/4095,  v = (4095 - x)/4095  we get
        y = u * 4095
        x = (1 - v) * 4095
    Inputs are clamped to [0, 1]; outputs are ints in [0, 4095], so a
    grid -> norm -> grid round trip returns the original coordinates.
    """
    uu = 0.0 if u < 0 else (1.0 if u > 1 else float(u))
    vv = 0.0 if v < 0 else (1.0 if v > 1 else float(v))
    x = int(round((1.0 - vv) * 4095.0))
    y = int(round(uu * 4095.0))
    return x, y


def overlay_radius_from_spec(spec_radius) -> int:
    """
    Converts poiData.json radius into a stable on screen radius baseline.
    """
    try:
        r = float(spec_radius)
    except (TypeError, ValueError):
        r = 12.0
    px = int(round(r * 0.25))
    if px < 3:
        px = 3
    if px > 10:
        px = 10
    return px
