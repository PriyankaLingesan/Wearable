"""Image validation applied to EVERY frame (webcam capture or uploaded file) before it reaches the recognition pipeline."""
import cv2
import numpy as np

MIN_SIDE, MAX_SIDE = 64, 8000
ALLOWED_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff")


def decode_bytes(data):
    """Decode image bytes to BGR. Raises ValueError with a user-readable reason."""
    if not data:
        raise ValueError("empty file")
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("file is not a decodable image (png/jpg/bmp/webp/tiff expected)")
    return img


def validate_frame(bgr):
    """Return dict(ok, errors, warnings, stats). `ok` False means the frame must not be processed."""
    errors, warnings = [], []
    if not isinstance(bgr, np.ndarray) or bgr.ndim != 3 or bgr.shape[2] != 3 or bgr.dtype != np.uint8:
        return dict(ok=False, errors=["frame is not an 8-bit 3-channel image"], warnings=[], stats={})
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    mean, std = float(gray.mean()), float(gray.std())
    sat = float((gray >= 250).mean())
    stats = dict(width=w, height=h, mean=round(mean, 1), std=round(std, 1), saturated_fraction=round(sat, 3))
    if min(h, w) < MIN_SIDE:
        errors.append(f"image too small ({w}x{h}); minimum side is {MIN_SIDE}px")
    if max(h, w) > MAX_SIDE:
        errors.append(f"image too large ({w}x{h}); maximum side is {MAX_SIDE}px")
    if std < 2.0:
        errors.append("image is blank or uniform (no content to read)")
    if not errors:
        if max(h, w) < 320:
            warnings.append("low resolution: tiny hallmark characters may be unreadable; use a close-up/macro image")
        if mean < 20:
            warnings.append("very dark image: increase illumination")
        if sat > 0.5:
            warnings.append("more than half of the pixels are saturated (glare/overexposure)")
    return dict(ok=not errors, errors=errors, warnings=warnings, stats=stats)
