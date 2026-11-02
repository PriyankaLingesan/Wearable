"""OCR engine wrappers with a uniform interface.

Engines actually benchmarked:
  tesseract : Tesseract 5 (LSTM, oem 1), single-line mode, A-Z0-9 whitelist  (Smith, ICDAR 2007)
  rapidocr  : PP-OCR (PaddleOCR family) detection-free recognition head on ONNX Runtime (Du et al. 2020)
Engines NOT benchmarked here (unavailable in the sandbox: need PyTorch / model downloads): EasyOCR,
full PaddlePaddle runtime. This is a stated limitation, not an omission by oversight.
"""
import re
import time

import cv2
import numpy as np
import pytesseract

from . import CFG

_rapid = None
WL = CFG["ocr"]["tesseract_whitelist"]


def norm_text(s):
    s = (s or "").upper()
    s = re.sub(r"[^A-Z0-9 ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def get_rapid():
    global _rapid
    if _rapid is None:
        from rapidocr_onnxruntime import RapidOCR
        # recognition-only engine: the ROI is already a single text line; no angle classifier
        _rapid = RapidOCR(use_text_det=False, use_angle_cls=False)
        _rapid.text_score = 0.0  # keep low-confidence reads: the default 0.5 filter would hide the cases we study
    return _rapid


def run_tesseract(g):
    # NOTE: no character whitelist. In Tesseract 5 (LSTM) a whitelist makes every word confidence 0,
    # which would destroy the uncertainty signal; characters are filtered after recognition instead.
    cfg = f"--oem 1 --psm {CFG['ocr']['tesseract_psm']}"
    d = pytesseract.image_to_data(g, config=cfg, output_type=pytesseract.Output.DICT)
    words, confs, lens = [], [], []
    for t, c in zip(d["text"], d["conf"]):
        t = norm_text(t)
        if t and float(c) >= 0:
            words.append(t); confs.append(float(c)); lens.append(len(t))
    if not words:
        return dict(text="", conf=0.0, conf_min=0.0, n_tokens=0)
    conf = float(np.average(confs, weights=lens)) / 100.0
    return dict(text=norm_text(" ".join(words)), conf=conf, conf_min=float(min(confs)) / 100.0, n_tokens=len(words))


def run_rapid(g):
    eng = get_rapid()
    img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR) if g.ndim == 2 else g
    res, _ = eng(img)
    if not res:
        return dict(text="", conf=0.0, conf_min=0.0, n_tokens=0)
    txt = " ".join(r[1] for r in res)
    confs = [float(r[2]) for r in res]
    return dict(text=norm_text(txt), conf=float(np.mean(confs)), conf_min=float(min(confs)), n_tokens=len(res))


ENGINES = {"tesseract": run_tesseract, "rapidocr": run_rapid}


def recognise(g, engine):
    t0 = time.perf_counter()
    out = ENGINES[engine](g)
    out["ms"] = (time.perf_counter() - t0) * 1000.0
    return out
