"""End-to-end hallmark reading pipeline: quality -> localise -> enhance -> OCR -> uncertainty features."""
import re
import time

import cv2
import numpy as np
from rapidfuzz.distance import Levenshtein

from . import CFG
from . import enhance as E
from . import localize as L
from . import ocr as O
from . import quality as Q

VARIANTS = {
    "raw": dict(steps=[], binar=False, channel=None),                 # grayscale ROI crop + scale normalisation only
    "red": dict(steps=[], binar=False, channel="red"),                # red channel (highest metal contrast), same
    "enh": dict(steps=E.ENH_STEPS, binar=False, channel=None),        # full enhancement chain
    "bin": dict(steps=E.ENH_STEPS, binar=True, channel=None),         # enhancement + Sauvola binarisation
}

# Documented hallmark grammar of the SYNTHETIC dataset (see data/DATASHEET.md)
_PUR = {"375", "585", "750", "916", "958", "999"}
_KAR = {"9K", "14K", "18K", "22K", "24K"}


_CODE = re.compile(r"[ABCDEFGHJKLMNPQRSTUVWXYZ1-9]{6}")
_MAKER = re.compile(r"[ABCDEFGHJKLMNPQRSTUVWXYZ]{2,3}")


def grammar_valid(text):
    """True if every token is a known purity numeral, karat label, BIS, a 6-char code, or a 2-3 letter maker mark.
    (Grammar of the SYNTHETIC dataset; the check never sees ground truth.)"""
    toks = text.split()
    if not toks or len(text.replace(" ", "")) < 4:
        return False
    return all(t in _PUR or t in _KAR or t == "BIS" or _CODE.fullmatch(t) or _MAKER.fullmatch(t) for t in toks)


def norm_edit(a, b):
    m = max(len(a), len(b), 1)
    return Levenshtein.distance(a, b) / m


def ocr_input(img_gray, binar):
    g = E.binarize(img_gray, "sauvola") if binar else img_gray
    return E.pad_for_ocr(g)


def analyse(bgr, loc_method="contour", variants=("raw", "red", "enh", "bin"), engines=("tesseract", "rapidocr"),
            timings=None):
    """Run the full pipeline. Returns dict with quality features, localisation, and OCR outputs per variant/engine."""
    T = {} if timings is None else timings
    t = time.perf_counter()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    ff = Q.frame_features(bgr)
    T["quality_frame_ms"] = (time.perf_counter() - t) * 1000; t = time.perf_counter()
    loc = L.locate(gray, loc_method)
    T["localise_ms"] = (time.perf_counter() - t) * 1000; t = time.perf_counter()
    roi_raw, roi_box = E.crop_roi(gray, loc)
    rf = Q.roi_features(roi_raw)
    h, w = gray.shape
    feats = dict(ff); feats.update(rf)
    feats["loc_score"] = float(loc["score"]); feats["loc_fallback"] = float(loc.get("fallback", False))
    feats["roi_area_frac"] = float((roi_box[2] - roi_box[0]) * (roi_box[3] - roi_box[1]) / (w * h))
    T["quality_roi_ms"] = (time.perf_counter() - t) * 1000
    out = dict(loc=loc, feats=feats, ocr={}, enh_log={})
    cache = {}
    for v in variants:
        spec = VARIANTS[v]
        t = time.perf_counter()
        key = (tuple(spec["steps"]), spec.get("channel"))
        if key not in cache:
            src = bgr[:, :, 2] if spec.get("channel") == "red" else bgr
            cache[key] = E.enhance(src, loc, steps=spec["steps"], lapvar=None)
        roi, log = cache[key]
        img = ocr_input(roi, spec["binar"])
        T[f"enhance_{v}_ms"] = (time.perf_counter() - t) * 1000
        out["enh_log"][v] = log
        out.setdefault("images", {})[v] = img
        for e in engines:
            r = O.recognise(img, e)
            out["ocr"][(v, e)] = r
            T[f"ocr_{e}_{v}_ms"] = r["ms"]
    out["timings"] = T
    return out


def uncertainty_features(primary, secondary):
    """OCR-uncertainty features from two recognisers (primary engine output, secondary engine output)."""
    return {
        "p_conf": primary["conf"], "p_conf_min": primary["conf_min"], "p_len": float(len(primary["text"].replace(" ", ""))),
        "p_ntok": float(primary["n_tokens"]),
        "s_conf": secondary["conf"], "s_len": float(len(secondary["text"].replace(" ", ""))),
        "disagree": norm_edit(primary["text"].replace(" ", ""), secondary["text"].replace(" ", "")),
        "agree_exact": float(primary["text"].replace(" ", "") == secondary["text"].replace(" ", "")),
        "p_grammar": float(grammar_valid(primary["text"])), "s_grammar": float(grammar_valid(secondary["text"])),
        "p_empty": float(len(primary["text"]) == 0),
    }
