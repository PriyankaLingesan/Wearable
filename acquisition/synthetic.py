"""Renders a SYNTHETIC hallmark frame with the project's generator (used for tests and the demo test videos; never real jewellery)."""
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from hallmark import CFG, synth  # noqa: E402
from hallmark import sim_hw as HW  # noqa: E402


def render_synthetic(condition="clean", seed=None, led=True, text=None):
    """Same generation logic as simulator/app.py /api/capture. Returns (bgr, ground_truth_dict). Ground truth is for tests only."""
    seed = random.randint(0, 10 ** 9) if seed is None else int(seed)
    if condition not in synth.CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}")
    rng = random.Random(seed)
    src = rng.choice(CFG["dataset"]["sources"])
    spec = dict(item_id="SIM", source=src, split="sim", text=text or synth.make_text(rng), style=rng.choice(synth.STYLES),
                font_path=rng.choice(synth.SOURCES[src]["fonts"]), cap_h=rng.randint(52, 74), seed=rng.randint(0, 2 ** 31 - 1))
    params = HW.led_effect(synth.sample_degradation(condition, random.Random(seed + 1), level=None), led)
    img, ann = synth.render_acquisition(spec, condition, seed + 2, tuple(CFG["dataset"]["image_size"]), params=params)
    return img, dict(text=spec["text"], condition=condition, readability_proxy=ann["readability"], seed=seed)
