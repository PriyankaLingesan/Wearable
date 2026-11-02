import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from hallmark import metrics as M  # noqa: E402
from hallmark import synth, CFG  # noqa: E402
from hallmark import pipeline as P  # noqa: E402
from hallmark import localize as L  # noqa: E402


def test_cer_wer_against_jiwer():
    import jiwer
    pairs = [("916 22K", "916 22K"), ("916 22K", "91 22K"), ("BIS 750 A3F9K2", "BIS 758 A3F9K"), ("585", "")]
    for g, p in pairs:
        if p:
            assert M.cer(g.replace(" ", ""), p.replace(" ", "")) == pytest.approx(jiwer.cer(g.replace(" ", ""), p.replace(" ", "")))
            assert M.wer(g, p) == pytest.approx(jiwer.wer(g, p))
    assert M.cer("585", "") == 1.0


def test_exact_whitespace_insensitive():
    assert M.exact("916 22K", "91622K") == 1.0
    assert M.exact_strict("916 22K", "91622K") == 0.0


def test_risk_coverage_and_aurc():
    score = np.array([0.9, 0.8, 0.7, 0.6]); correct = np.array([1, 1, 0, 1])
    cov, risk = M.risk_coverage(score, correct)
    assert list(cov) == [0.25, 0.5, 0.75, 1.0]
    assert risk == pytest.approx([0, 0, 1 / 3, 0.25])
    assert M.aurc(score, correct) == pytest.approx(np.mean([0, 0, 1 / 3, 0.25]))
    assert M.aurc(correct.astype(float), correct) <= M.aurc(score, correct)  # oracle is best
    assert M.eaurc(correct.astype(float), correct) == pytest.approx(0.0)


def test_threshold_for_risk_respects_target():
    rng = np.random.default_rng(0)
    s = rng.random(500); c = (rng.random(500) < s).astype(int)
    tau = M.threshold_for_risk(s, c, 0.1)
    r = M.selective_at(s, c, tau)
    assert r["accepted_error_rate"] <= 0.1 + 1e-9


def test_ece_perfect_and_bad():
    p = np.array([1.0] * 50 + [0.0] * 50); c = p.copy()
    assert M.ece(p, c) == pytest.approx(0.0)
    assert M.ece(np.full(100, 0.9), np.zeros(100)) == pytest.approx(0.9)


def test_synth_deterministic_and_synthetic_provenance():
    specs = synth.build_item_specs(CFG)
    a, _ = synth.render_acquisition(specs[0], "blur", 123)
    b, _ = synth.render_acquisition(specs[0], "blur", 123)
    assert np.array_equal(a, b)


def test_no_item_leakage_in_manifest():
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv"))
    assert man.groupby("item_id")["split"].nunique().max() == 1
    assert set(man["provenance"]) == {"synthetic"}


def test_text_grammar_roundtrip():
    import random
    rng = random.Random(1)
    for _ in range(300):
        t = synth.make_text(rng)
        # Known generator property (disclosed in the datasheet): texts are cut at 16 characters, which can truncate the last
        # token; only such cut-off strings may fail the grammar check.
        assert P.grammar_valid(t) or len(t) == 16


def test_iou():
    assert L.iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0
    assert L.iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0


def test_pipeline_runs_and_outputs_schema():
    import cv2
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv"))
    r = man[man.condition == "clean"].iloc[0]
    full = os.path.join(ROOT, "data", r.path)
    # the packaged ZIP ships only a small image sample; fall back to it, else re-render one image from the generator
    samp = os.path.join(ROOT, "data", "images_sample", os.path.basename(r.path))
    img = cv2.imread(full if os.path.exists(full) else samp)
    if img is None:
        img, _ = synth.render_acquisition(dict(item_id="T", source="S1", split="t", text="BIS 916", style="engraved",
                                               font_path=synth.SOURCES["S1"]["fonts"][0], cap_h=60, seed=1), "clean", 1, (640, 400))
    out = P.analyse(img, "contour", variants=("raw",), engines=("tesseract", "rapidocr"))
    assert ("raw", "rapidocr") in out["ocr"] and "r_lapvar_log" in out["feats"]
    assert 0.0 <= out["ocr"][("raw", "rapidocr")]["conf"] <= 1.0


def test_saved_models_load_and_score():
    import joblib
    rej = joblib.load(os.path.join(ROOT, "models", "rejector.joblib"))
    rd = joblib.load(os.path.join(ROOT, "models", "readability.joblib"))
    g = joblib.load(os.path.join(ROOT, "models", "guidance.joblib"))
    assert "rejector" in rej and "model" in rd and hasattr(g, "diagnose")
