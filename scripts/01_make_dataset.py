"""Generate the SYNTHETIC hallmark dataset, manifest and datasheet. Fully deterministic given the config seed."""
import json
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hallmark import CFG, ROOT  # noqa: E402
from hallmark import synth  # noqa: E402

DATA = os.path.join(ROOT, "data")
IMG = os.path.join(DATA, "images")


def work(args):
    spec, cond, aseed, rel = args
    img, ann = synth.render_acquisition(spec, cond, aseed, tuple(CFG["dataset"]["image_size"]))
    cv2.imwrite(os.path.join(DATA, rel), img, [cv2.IMWRITE_JPEG_QUALITY, 95] if rel.endswith(".jpg") else [])
    row = dict(image_id=os.path.splitext(os.path.basename(rel))[0], item_id=spec["item_id"], source=spec["source"],
               split=spec["split"], path=rel, text=spec["text"], style=spec["style"],
               font=os.path.basename(spec["font_path"]), cap_h_px=spec["cap_h"], height=img.shape[0],
               width=img.shape[1], provenance="synthetic", licence="CC0-1.0 (procedurally generated, no third-party content)")
    row.update(ann)
    row["bbox"] = json.dumps(row["bbox"])
    return row


def main():
    os.makedirs(IMG, exist_ok=True)
    specs = synth.build_item_specs(CFG)
    rng = random.Random(CFG["seed"] + 1)
    jobs = []
    n_acq = CFG["dataset"]["acquisitions_per_item"]
    for spec in specs:
        conds = ["clean"] + [rng.choice(["blur", "lowres", "uneven_light", "glare", "lowcontrast", "angle",
                                         "occlusion", "noise", "combined", "combined", "severe", "severe"])
                             for _ in range(n_acq - 1)]
        for k, c in enumerate(conds):
            iid = f"{spec['item_id']}_a{k}"
            jobs.append((spec, c, rng.randint(0, 2 ** 31 - 1), f"images/{iid}.png"))
    with ProcessPoolExecutor(max_workers=2) as ex:
        rows = list(ex.map(work, jobs, chunksize=16))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DATA, "manifest.csv"), index=False)
    print(df.groupby(["split"]).agg(items=("item_id", "nunique"), images=("image_id", "count")))
    print(df["readability"].value_counts())
    print(df.groupby("condition")["readability"].value_counts().unstack(fill_value=0))
    # leakage check: no item in more than one split
    chk = df.groupby("item_id")["split"].nunique().max()
    assert chk == 1, "item-level leakage!"
    print("item-level split check passed; clean-render contrast stats:")
    print(df[df.condition == "clean"][["contrast_ink", "blur_ratio", "h_eff"]].describe().round(3))


if __name__ == "__main__":
    main()
