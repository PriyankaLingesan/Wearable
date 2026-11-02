"""Exp. 0 (localisation benchmark) and Exp. 9 (leave-one-source-out generalisation)."""
import json
import os
import sys
import time
import warnings

import cv2
import numpy as np
import pandas as pd
from sklearn.base import clone

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hallmark import ROOT, CFG  # noqa: E402
from hallmark import localize as L  # noqa: E402
from hallmark import metrics as M  # noqa: E402
from hallmark import models as MD  # noqa: E402

R = os.path.join(ROOT, "results")
LABELS = ["readable", "partial", "unreadable"]


def localisation_benchmark():
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv"))
    test = man[man.split == "test"]
    rows = []
    imgs = [(cv2.cvtColor(cv2.imread(os.path.join(ROOT, "data", r.path)), cv2.COLOR_BGR2GRAY), json.loads(r.bbox), r.readability)
            for r in test.itertuples()]
    for meth in ("contour", "mser", "ocrdet", "full"):
        L.METHODS[meth](imgs[0][0])  # warm-up
        ious, ts, rd, fb = [], [], [], 0
        for g, bb, rdy in imgs:
            t = time.perf_counter(); r = L.locate(g, meth); ts.append((time.perf_counter() - t) * 1000)
            ious.append(L.iou(r["box"], bb)); rd.append(rdy); fb += int(r.get("fallback", False))
        ious, rd = np.array(ious), np.array(rd)
        row = dict(method=meth, mean_iou=ious.mean(), iou_ge_0_5=(ious >= .5).mean(), iou_ge_0_7=(ious >= .7).mean(),
                   latency_ms_median=float(np.median(ts)), latency_ms_p95=float(np.percentile(ts, 95)), fallback_rate=fb / len(imgs))
        for k in LABELS:
            row[f"iou_ge_0_5_{k}"] = float((ious[rd == k] >= .5).mean())
        rows.append(row)
    pd.DataFrame(rows).to_csv(os.path.join(R, "localisation_benchmark.csv"), index=False)
    print(pd.DataFrame(rows).round(3).to_string(index=False))


def loso():
    dep = json.load(open(os.path.join(ROOT, "models", "deployment.json")))
    primary, secondary = tuple(dep["primary"]), tuple(dep["secondary"])
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv")); raw = pd.read_csv(os.path.join(R, "ocr_raw.csv"))
    df = MD.assemble(raw, man, primary, secondary)
    out = {}
    base_rej = MD.rejector_zoo()[dep["rejector"]]
    rd_model = MD.readability_zoo()[dep["readability"]]
    for held in ("S1", "S2", "S3"):
        tr, te = df[df.source != held].reset_index(drop=True), df[df.source == held].reset_index(drop=True)
        y_tr, y_te = tr["correct"].values.astype(int), te["correct"].values.astype(int)
        rej = MD.CalibratedRejector(base_rej, MD.FEATURE_SETS["quality+ocr_unc"]).fit(tr, y_tr, tr["item_id"].values, CFG["rejection"]["target_risks"])
        s5 = rej.score(te); s1 = te["p_conf"].values
        r = dict(n=len(te), ocr_exact=float(y_te.mean()), aurc_S1=M.aurc(s1, y_te), aurc_S5=M.aurc(s5, y_te))
        for t in (0.05, 0.10):
            tau5 = rej.taus[str(t)]
            tau1 = M.threshold_for_risk(tr["p_conf"].values, y_tr, t)
            r[f"S5_at_{t}"] = M.selective_at(s5, y_te, tau5); r[f"S1_at_{t}"] = M.selective_at(s1, y_te, tau1)
        d = lambda idx: M.aurc(s5[idx], y_te[idx]) - M.aurc(s1[idx], y_te[idx])
        r["delta_aurc"] = dict(zip(("mean", "ci_lo", "ci_hi"), M.cluster_bootstrap(te["item_id"].values, d, n=500, seed=3)))
        feats = MD.FEATURE_SETS["quality_only"]
        m = clone(rd_model).fit(tr[feats].values.astype(float), tr["readability"].values)
        r["readability"] = M.clf_summary(te["readability"].values, m.predict(te[feats].values.astype(float)), LABELS)
        out[held] = r
        print(held, "OCR exact", round(r["ocr_exact"], 3), "AURC S1/S5", round(r["aurc_S1"], 3), round(r["aurc_S5"], 3),
              "readability F1", round(r["readability"]["f1_macro"], 3))
    json.dump(out, open(os.path.join(R, "loso_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("loc", "all"):
        localisation_benchmark()
    if which in ("loso", "all"):
        loso()
