"""Run the full pipeline (3 preprocessing variants x 2 OCR engines + oracle-ROI condition) on every image
and store raw outputs. This is the expensive step; all later analyses read results/ocr_raw.csv."""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hallmark import ROOT  # noqa: E402
from hallmark import localize as L  # noqa: E402
from hallmark import pipeline as P  # noqa: E402

ENGINES = ("tesseract", "rapidocr")


def work(row):
    img = cv2.imread(os.path.join(ROOT, "data", row["path"]))
    out = P.analyse(img, "contour", variants=("raw", "red", "enh", "bin"), engines=ENGINES)
    r = {"image_id": row["image_id"]}
    r.update(out["feats"])
    r["loc_box"] = json.dumps([round(float(v), 1) for v in out["loc"]["box"]])
    gt = json.loads(row["bbox"])
    r["loc_iou"] = L.iou(out["loc"]["box"], gt)
    for (v, e), o in out["ocr"].items():
        r[f"{e}_{v}_text"] = o["text"]; r[f"{e}_{v}_conf"] = o["conf"]
        r[f"{e}_{v}_confmin"] = o["conf_min"]; r[f"{e}_{v}_ntok"] = o["n_tokens"]; r[f"{e}_{v}_ms"] = o["ms"]
    # oracle localisation (ground-truth box): separates localisation errors from recognition errors
    from hallmark import enhance as E
    from hallmark import ocr as O
    x1, y1, x2, y2 = gt
    oloc = dict(box=tuple(gt), rect=(((x1 + x2) / 2, (y1 + y2) / 2), (x2 - x1, y2 - y1), 0.0), score=1.0)
    for tag, steps in (("oracleraw", []), ("oracleenh", [s_ for s_ in E.ENH_STEPS if s_ != "rectify"])):
        roi, _ = E.enhance(img, oloc, steps=steps)
        g = P.ocr_input(roi, False)
        for e in ENGINES:
            o = O.recognise(g, e)
            r[f"{e}_{tag}_text"] = o["text"]; r[f"{e}_{tag}_conf"] = o["conf"]
    return r


def main():
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv"))
    rows = man.to_dict("records")
    t = time.time()
    with ProcessPoolExecutor(max_workers=2) as ex:
        res = list(ex.map(work, rows, chunksize=8))
    df = pd.DataFrame(res)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    df.to_csv(os.path.join(ROOT, "results", "ocr_raw.csv"), index=False)
    print("done", len(df), "images in", round(time.time() - t), "s")


if __name__ == "__main__":
    main()
