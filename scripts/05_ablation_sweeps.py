"""Experiments 2 (step ablation) and 3-6 (controlled robustness sweeps). Runs on the TEST items only.

Ablation: contour ROI + enhancement-step subsets, scored with both OCR engines.
Sweeps  : for each test item a pristine render is degraded along ONE axis at increasing severity
          (blur, illumination, glare, resolution, viewing angle) and the full pipeline (raw/red/enh variants,
          both engines) is run, so CER/exact accuracy can be plotted against severity and the rejector's
          behaviour can be inspected on the same images.
"""
import json
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hallmark import CFG, ROOT  # noqa: E402
from hallmark import enhance as E  # noqa: E402
from hallmark import localize as L  # noqa: E402
from hallmark import ocr as O  # noqa: E402
from hallmark import pipeline as P  # noqa: E402
from hallmark import synth  # noqa: E402

R = os.path.join(ROOT, "results")
ABL = [("base(raw)", []),
       ("+rectify", ["rectify"]), ("+glare", ["glare"]), ("+flatten", ["flatten"]),
       ("+denoise", ["denoise"]), ("+clahe", ["clahe"]), ("+sharpen", ["sharpen"]),
       ("full", E.ENH_STEPS)] + [(f"full-{s}", [x for x in E.ENH_STEPS if x != s]) for s in E.ENH_STEPS]

SWEEPS = {
    "blur": ("blur_sigma", [0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0]),
    "lighting": ("illum", [0.0, 0.25, 0.5, 0.75, 1.0]),
    "glare": ("glare_s", [0.0, 0.4, 0.8, 1.2, 1.6]),
    "resolution": ("scale", [1.0, 0.75, 0.5, 0.35, 0.25, 0.15]),
    "angle": ("theta", [0.0, 15.0, 30.0, 45.0, 60.0, 70.0]),
}


def base_params():
    return dict(blur_sigma=0.0, motion_len=0, scale=1.0, illum=0.0, glare_n=0, glare_s=0.0, contrast=1.0, theta=0.0,
                inplane=0.0, occ=0.0, noise=2.0, jpeg=95)


def ablation_work(row):
    img = cv2.imread(os.path.join(ROOT, "data", row["path"]))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    loc = L.locate(gray, "contour")
    out = {"image_id": row["image_id"]}
    for name, steps in ABL:
        roi, _ = E.enhance(img, loc, steps=steps)
        g = P.ocr_input(roi, False)
        for e in ("tesseract", "rapidocr"):
            out[f"{e}|{name}"] = O.recognise(g, e)["text"]
    return out


def sweep_work(job):
    spec, axis, val, seed = job
    p = base_params()
    key = SWEEPS[axis][0]
    p[key] = val
    if axis == "glare" and val > 0:
        p["glare_n"] = 1
    img, ann = synth.render_acquisition(spec, "clean", seed, tuple(CFG["dataset"]["image_size"]), params=p)
    rr = P.analyse(img, "contour", variants=("raw", "red", "enh", "bin"))
    r = {"item_id": spec["item_id"], "source": spec["source"], "text": spec["text"], "axis": axis, "level": val,
         "readability": ann["readability"], "sweep_loc_iou": L.iou(rr["loc"]["box"], ann["bbox"])}
    r.update(rr["feats"])
    for (v, e), o in rr["ocr"].items():
        r[f"{e}_{v}_text"] = o["text"]; r[f"{e}_{v}_conf"] = o["conf"]; r[f"{e}_{v}_confmin"] = o["conf_min"]
        r[f"{e}_{v}_ntok"] = o["n_tokens"]
    return r


def main():
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv"))
    test = man[man.split == "test"]
    t = time.time()
    with ProcessPoolExecutor(max_workers=2) as ex:
        ab = pd.DataFrame(list(ex.map(ablation_work, test.to_dict("records"), chunksize=6)))
    ab.to_csv(os.path.join(R, "ablation_raw.csv"), index=False)
    print("ablation done", round(time.time() - t), "s")
    specs = [s for s in synth.build_item_specs(CFG) if s["split"] == "test"]
    rng = random.Random(CFG["seed"] + 7)
    jobs = []
    for axis, (_, levels) in SWEEPS.items():
        for lv in levels:
            for s in specs:
                jobs.append((s, axis, lv, rng.randint(0, 2 ** 31 - 1)))
    t = time.time()
    with ProcessPoolExecutor(max_workers=2) as ex:
        sw = pd.DataFrame(list(ex.map(sweep_work, jobs, chunksize=8)))
    sw.to_csv(os.path.join(R, "sweeps_raw.csv"), index=False)
    print("sweeps done", len(sw), round(time.time() - t), "s")


if __name__ == "__main__":
    main()
