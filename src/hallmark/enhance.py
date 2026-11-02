"""ROI rectification and enhancement. Every step is switchable so the ablation (Exp. 2) is real."""
import cv2
import numpy as np
from . import CFG

P = CFG["pipeline"]

ENH_STEPS = ["rectify", "flatten", "glare", "denoise", "clahe", "sharpen"]


def crop_roi(gray_or_bgr, loc, pad=None):
    pad = P["roi_pad_frac"] if pad is None else pad
    h, w = gray_or_bgr.shape[:2]
    x1, y1, x2, y2 = loc["box"]
    pw, ph = (x2 - x1) * pad, (y2 - y1) * pad * 1.5
    x1, y1 = int(max(0, x1 - pw)), int(max(0, y1 - ph))
    x2, y2 = int(min(w, x2 + pw)), int(min(h, y2 + ph))
    return gray_or_bgr[y1:y2, x1:x2], (x1, y1, x2, y2)


def estimate_skew(gray_roi, max_abs=15.0):
    """Text-line skew (degrees) from the min-area rectangle of the strongest horizontal-stroke energy pixels."""
    g = cv2.GaussianBlur(gray_roi, (0, 0), 1.2).astype(np.float32)
    gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)); gy = np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
    e = np.clip(gx - 0.6 * gy, 0, None)
    thr = np.percentile(e, 88)
    ys, xs = np.nonzero(e > thr)
    if len(xs) < 50:
        return 0.0
    (cx, cy), (rw, rh), ang = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))
    if rw < rh:
        ang += 90.0
    ang = ((ang + 45.0) % 90.0) - 45.0
    return float(ang) if abs(ang) <= max_abs else 0.0


def rectify(gray, loc, pad=None):
    """In-plane rotation correction (skew estimated from stroke energy inside the localised box).
    Out-of-plane (keystone) perspective is NOT corrected: this is a stated limitation."""
    pad = P["roi_pad_frac"] if pad is None else pad
    if loc.get("fallback"):
        return None
    roi, _ = crop_roi(gray, loc, pad)
    if roi.size == 0 or min(roi.shape) < 16:
        return None
    ang = estimate_skew(roi)
    if abs(ang) < 1.0:
        return None
    h, w = roi.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
    return cv2.warpAffine(roi, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def flatten_illumination(g):
    k = max(int(min(g.shape) * 0.6) | 1, 15)
    bg = cv2.GaussianBlur(g.astype(np.float32), (0, 0), k / 3.0)
    out = g.astype(np.float32) / (bg + 1e-3) * float(np.mean(bg))
    return np.clip(out, 0, 255).astype(np.uint8)


def mitigate_glare(g):
    mask = (g >= P["glare_sat_threshold"]).astype(np.uint8)
    if mask.mean() < 0.002 or mask.mean() > 0.35:
        return g
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
    return cv2.inpaint(g, mask * 255, 5, cv2.INPAINT_TELEA)


def denoise(g, sigma_est):
    h = float(np.clip(1.6 * sigma_est, 3, 14))
    return cv2.fastNlMeansDenoising(g, None, h, 5, 15)


def unsharp(g, amount=0.9, sigma=1.2):
    b = cv2.GaussianBlur(g, (0, 0), sigma)
    return cv2.addWeighted(g, 1 + amount, b, -amount, 0)


def upscale_to_target(g):
    h = g.shape[0]
    # ROI height includes padding; text ~ 55% of ROI height
    est_text = max(h * 0.55, 1.0)
    s = P["target_text_height_px"] / est_text
    s = float(np.clip(s, 0.25, P["max_upscale"]))
    if abs(s - 1) < 0.05:
        return g
    interp = cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA
    return cv2.resize(g, None, fx=s, fy=s, interpolation=interp)


def enhance(bgr, loc, steps=None, lapvar=None):
    """Return the enhanced single-channel ROI image (dark/light polarity untouched) and a log."""
    steps = set(ENH_STEPS if steps is None else steps)
    gray = bgr if bgr.ndim == 2 else cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    log = []
    roi = None
    if "rectify" in steps:
        roi = rectify(gray, loc)
        if roi is not None:
            log.append("rectify")
    if roi is None:
        roi, _ = crop_roi(gray, loc)
    if roi.size == 0:
        roi = gray
    if "glare" in steps:
        r2 = mitigate_glare(roi)
        if r2 is not roi:
            log.append("glare")
        roi = r2
    if "flatten" in steps:
        roi = flatten_illumination(roi); log.append("flatten")
    roi = upscale_to_target(roi); log.append("upscale")
    if "denoise" in steps:
        from .quality import noise_sigma
        roi = denoise(roi, noise_sigma(roi)); log.append("denoise")
    if "clahe" in steps:
        roi = cv2.createCLAHE(P["clahe_clip"], (P["clahe_tiles"], P["clahe_tiles"])).apply(roi); log.append("clahe")
    if "sharpen" in steps:
        from .quality import lap_var
        lv = lap_var(roi) if lapvar is None else lapvar
        if lv < P["sharpen_lapvar_below"]:
            roi = unsharp(roi); log.append("sharpen")
    return roi, log


def binarize(g, method="sauvola"):
    from skimage.filters import threshold_sauvola
    if method == "sauvola":
        th = threshold_sauvola(g, window_size=31, k=0.2)
        return ((g > th) * 255).astype(np.uint8)
    return cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8)


def pad_for_ocr(g, v=None):
    v = int(np.median(g)) if v is None else v
    return cv2.copyMakeBorder(g, 10, 10, 16, 16, cv2.BORDER_CONSTANT, value=v)
