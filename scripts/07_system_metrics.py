"""Exp. 10: latency (per stage), peak memory, model sizes. Measured on the sandbox CPU (a laptop-class proxy),
NOT on a Raspberry Pi. Extrapolation to Pi hardware is deliberately not performed."""
import glob
import json
import os
import platform
import resource
import subprocess
import sys
import time

import cv2
import numpy as np
import pandas as pd
import psutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hallmark import ROOT  # noqa: E402

R = os.path.join(ROOT, "results")


def rss_mb():
    return psutil.Process().memory_info().rss / 1e6


CHILD = r"""
import sys, resource, json, os, cv2, numpy as np, psutil
sys.path.insert(0, os.path.join(%r, 'src'))
mode = sys.argv[1]
img = cv2.imread(sys.argv[2])
base = psutil.Process().memory_info().rss/1e6
from hallmark import pipeline as P
if mode == 'tesseract_only':
    P.analyse(img, 'contour', variants=('raw',), engines=('tesseract',))
elif mode == 'rapidocr_only':
    P.analyse(img, 'contour', variants=('raw',), engines=('rapidocr',))
elif mode == 'full_dual':
    P.analyse(img, 'contour', variants=('raw',), engines=('tesseract','rapidocr'))
    P.analyse(img, 'contour', variants=('raw',), engines=('tesseract','rapidocr'))
print(json.dumps(dict(mode=mode, rss_after_mb=psutil.Process().memory_info().rss/1e6, peak_mb=int([l for l in open('/proc/self/status') if l.startswith('VmHWM')][0].split()[1])/1024, rss_import_mb=base)))
""" % ROOT


def main():
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv"))
    test = man[man.split == "test"].sample(60, random_state=0)
    from hallmark import models as MD
    from hallmark import pipeline as P
    dep = json.load(open(os.path.join(ROOT, "models", "deployment.json")))
    rejd = MD.joblib.load(os.path.join(ROOT, "models", "rejector.joblib"))
    rej = rejd["rejector"]; pe, pv = tuple(dep["primary"]); se, sv = tuple(dep["secondary"])
    imgs = [cv2.imread(os.path.join(ROOT, "data", p)) for p in test.path]
    P.analyse(imgs[0], "contour", variants=(pv, sv), engines=(pe, se))  # warm-up
    rows = []
    cpu0 = time.process_time(); w0 = time.perf_counter()
    for img in imgs:
        T = {}
        t = time.perf_counter()
        out = P.analyse(img, "contour", variants=tuple({pv, sv}), engines=(pe, se), timings=T)
        total_pipeline = (time.perf_counter() - t) * 1000
        t = time.perf_counter()
        unc = P.uncertainty_features(out["ocr"][(pv, pe)], out["ocr"][(sv, se)])
        X = pd.DataFrame([{**out["feats"], **unc}])
        rej.score(X)
        T["reject_ms"] = (time.perf_counter() - t) * 1000
        T["total_ms"] = total_pipeline + T["reject_ms"]
        rows.append(T)
    wall = time.perf_counter() - w0; cpu = time.process_time() - cpu0
    df = pd.DataFrame(rows)
    stats = pd.DataFrame({"median_ms": df.median(), "p95_ms": df.quantile(0.95), "mean_ms": df.mean()})
    stats.to_csv(os.path.join(R, "latency_stages.csv"))
    print(stats.round(1).to_string())
    # single-engine variants
    single = {}
    for eng in ("tesseract", "rapidocr"):
        ts = []
        for img in imgs[:30]:
            t = time.perf_counter(); P.analyse(img, "contour", variants=("raw",), engines=(eng,)); ts.append((time.perf_counter() - t) * 1000)
        single[eng] = dict(median_ms=float(np.median(ts)), p95_ms=float(np.percentile(ts, 95)))
    # memory in clean child processes
    mem = {}
    for mode in ("tesseract_only", "rapidocr_only", "full_dual"):
        o = subprocess.run([sys.executable, "-c", CHILD, mode, os.path.join(ROOT, "data", test.path.iloc[0])], capture_output=True, text=True)
        mem[mode] = json.loads(o.stdout.strip().splitlines()[-1])
    # sizes
    sizes = {}
    import rapidocr_onnxruntime as ro
    for f in glob.glob(os.path.join(os.path.dirname(ro.__file__), "models", "*.onnx")):
        sizes["rapidocr:" + os.path.basename(f)] = os.path.getsize(f) / 1e6
    td = subprocess.run(["bash", "-c", "ls /usr/share/tesseract-ocr/5/tessdata/eng.traineddata"], capture_output=True, text=True).stdout.strip()
    if td:
        sizes["tesseract:eng.traineddata"] = os.path.getsize(td) / 1e6
    for f in glob.glob(os.path.join(ROOT, "models", "*.joblib")):
        sizes["ours:" + os.path.basename(f)] = os.path.getsize(f) / 1e6
    cpu_model = ""
    try:
        cpu_model = [l for l in open("/proc/cpuinfo") if l.startswith("model name")][0].split(":")[1].strip()
    except Exception:
        pass
    res = dict(n_images=len(imgs), wall_s=wall, cpu_s=cpu, cpu_utilisation=cpu / wall, single_engine=single, memory=mem, sizes_mb=sizes,
               platform=dict(cpu=cpu_model, logical_cpus=psutil.cpu_count(), ram_gb=psutil.virtual_memory().total / 1e9,
                             python=platform.python_version(), opencv=cv2.__version__, os=platform.platform()),
               note="Measured on the sandbox CPU; NOT a Raspberry Pi. No extrapolation to Pi hardware is made.")
    json.dump(res, open(os.path.join(R, "system_metrics.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "sizes_mb"}, indent=1)); print(json.dumps(sizes, indent=1))


if __name__ == "__main__":
    main()
