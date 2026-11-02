"""Hallmark-region localisation: three alternatives are implemented and benchmarked (Exp. 0).

  contour : morphological-gradient energy map -> Otsu -> horizontal closing -> contour scoring
  mser    : MSER character candidates -> row clustering
  ocrdet  : DB text detector from the PP-OCR family (RapidOCR / ONNX)
  full    : whole frame (baseline)
All return an axis-aligned box (x1, y1, x2, y2), a rotated rectangle (cv2.minAreaRect) and a score.
"""
import cv2
import numpy as np

_ocr_det = None


def _prep(gray, max_side=640):
    h, w = gray.shape
    s = min(1.0, max_side / max(h, w))
    if s < 1.0:
        gray = cv2.resize(gray, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return gray, s


def locate_contour(gray, sig=1.8, k=1.5, gap_frac=0.15, kx_frac=0.05):
    """Contour-based localiser exploiting the anisotropy of brushed metal.

    Brushed texture produces mostly *vertical* gradients (horizontal streaks); character strokes produce
    strong *horizontal* gradients. Energy e = max(|Gx| - 0.6|Gy|, 0), robustly thresholded (median + k*MAD),
    horizontally closed to merge characters into text blobs, the best-scoring blob (energy * sqrt(area)) is
    selected, and vertically aligned neighbour blobs across word gaps (<= gap_frac * width) are merged into it
    so multi-token inscriptions are not truncated. Parameters tuned on DEVELOPMENT images only."""
    g, s = _prep(gray)
    h, w = g.shape
    g = cv2.GaussianBlur(g, (0, 0), sig).astype(np.float32)
    gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3))
    gy = np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
    e = cv2.GaussianBlur(np.clip(gx - 0.6 * gy, 0, None), (0, 0), 2.0)
    med = np.median(e)
    mad = np.median(np.abs(e - med)) + 1e-6
    bw = (e > med + k * 1.4826 * mad * 3).astype(np.uint8) * 255
    kx = max(int(w * kx_frac), 9)
    closed = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (kx, 7)))
    closed = cv2.morphologyEx(closed, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3)))
    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes, best, bs = [], None, 0.0
    for c in cnts:
        x, y, bw_, bh_ = cv2.boundingRect(c)
        area = bw_ * bh_
        if area < 0.0015 * w * h or area > 0.7 * w * h or bh_ < 8:
            continue
        boxes.append([x, y, x + bw_, y + bh_])
        if area < 0.004 * w * h or not (1.3 <= bw_ / bh_ <= 25):
            continue
        sc = float(e[y:y + bh_, x:x + bw_].mean() * np.sqrt(area))
        if sc > bs:
            bs, best = sc, [x, y, x + bw_, y + bh_]
    if best is None:
        return None
    for _ in range(5):  # merge vertically-aligned neighbours across word gaps
        changed = False
        for b in boxes:
            if b == best:
                continue
            vo = min(best[3], b[3]) - max(best[1], b[1])
            if vo < 0.5 * min(best[3] - best[1], b[3] - b[1]):
                continue
            gap = max(b[0] - best[2], best[0] - b[2], 0)
            if gap <= gap_frac * w:
                nb = [min(best[0], b[0]), min(best[1], b[1]), max(best[2], b[2]), max(best[3], b[3])]
                if nb != best:
                    best, changed = nb, True
        if not changed:
            break
    x1, y1, x2, y2 = best
    inv = 1.0 / s
    return dict(box=(x1 * inv, y1 * inv, x2 * inv, y2 * inv),
                rect=(((x1 + x2) / 2 * inv, (y1 + y2) / 2 * inv), ((x2 - x1) * inv, (y2 - y1) * inv), 0.0), score=bs)


def locate_mser(gray):
    g, s = _prep(gray)
    h, w = g.shape
    g = cv2.createCLAHE(2.0, (4, 4)).apply(g)
    mser = cv2.MSER_create(5, 40, int(0.05 * w * h))
    regions, boxes = mser.detectRegions(g)
    cand = []
    for (x, y, bw_, bh_) in boxes:
        a = bw_ / max(bh_, 1)
        if 0.15 <= a <= 1.6 and 0.05 * h <= bh_ <= 0.5 * h and bw_ >= 4:
            cand.append((x, y, x + bw_, y + bh_))
    if len(cand) < 3:
        return None
    cand = np.array(cand, float)
    cy = (cand[:, 1] + cand[:, 3]) / 2
    # cluster by row: the densest horizontal band wins
    best, best_n = None, 0
    for yc in np.unique(np.round(cy / 8) * 8):
        sel = np.abs(cy - yc) < 0.5 * np.median(cand[:, 3] - cand[:, 1]) + 6
        if sel.sum() > best_n:
            best_n, best = sel.sum(), cand[sel]
    if best is None or best_n < 3:
        return None
    x1, y1, x2, y2 = best[:, 0].min(), best[:, 1].min(), best[:, 2].max(), best[:, 3].max()
    inv = 1.0 / s
    box = (x1 * inv, y1 * inv, x2 * inv, y2 * inv)
    rect = (((x1 + x2) / 2 * inv, (y1 + y2) / 2 * inv), ((x2 - x1) * inv, (y2 - y1) * inv), 0.0)
    return dict(box=box, rect=rect, score=float(best_n / 20.0))


def _get_det():
    global _ocr_det
    if _ocr_det is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_det = RapidOCR(use_angle_cls=False)
    return _ocr_det


def locate_ocrdet(gray):
    eng = _get_det()
    img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR) if gray.ndim == 2 else gray
    boxes, _ = eng.text_detector(img)
    if boxes is None or len(boxes) == 0:
        return None
    res = boxes
    pts = np.array([np.array(r, dtype=np.float32).reshape(-1, 2) for r in res]).reshape(-1, 2)
    x1, y1 = pts.min(axis=0); x2, y2 = pts.max(axis=0)
    rect = cv2.minAreaRect(pts.astype(np.float32))
    return dict(box=(float(x1), float(y1), float(x2), float(y2)), rect=rect, score=float(len(res)))


def locate_full(gray):
    h, w = gray.shape[:2]
    return dict(box=(0.0, 0.0, float(w), float(h)), rect=((w / 2, h / 2), (w, h), 0.0), score=0.0)


METHODS = {"contour": locate_contour, "mser": locate_mser, "ocrdet": locate_ocrdet, "full": locate_full}


def locate(gray, method="contour", fallback=True):
    r = METHODS[method](gray)
    if r is None and fallback:
        r = locate_full(gray); r["fallback"] = True
    elif r is not None:
        r["fallback"] = False
    return r


def iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1]); ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0
