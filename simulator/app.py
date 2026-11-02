"""Interactive wrist-worn hallmark-reader SIMULATOR (Flask). Every analysis request runs the REAL pipeline
(quality -> localise -> enhance -> two OCR engines -> uncertainty features -> calibrated rejector -> guidance).
Simulated: camera (synthetic generator), LED effect, button, OLED panel. Not simulated: the algorithms."""
import base64
import json
import os
import random
import sys
import time

import cv2
import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from hallmark import CFG, synth  # noqa: E402
from hallmark import localize as L  # noqa: E402
from hallmark import pipeline as P  # noqa: E402
from hallmark import sim_hw as HW  # noqa: E402

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

_state = {}


def load_models():
    if _state:
        return _state
    dep = json.load(open(os.path.join(ROOT, "models", "deployment.json")))
    rej = joblib.load(os.path.join(ROOT, "models", "rejector.joblib"))
    rd = joblib.load(os.path.join(ROOT, "models", "readability.joblib"))
    guid = joblib.load(os.path.join(ROOT, "models", "guidance.joblib"))
    # risk-controlled (upper-confidence-bound) thresholds are the default operating points
    _state.update(dep=dep, rej=rej["rejector"], taus=rej.get("taus_ucb", rej["taus"]), primary=tuple(rej["primary"]), secondary=tuple(rej["secondary"]),
                  rd=rd, guid=guid)
    return _state


def b64(img_bgr_or_gray, fmt=".png"):
    ok, enc = cv2.imencode(fmt, img_bgr_or_gray)
    return "data:image/png;base64," + base64.b64encode(enc.tobytes()).decode()


def analyse_image(bgr, risk="0.05"):
    S = load_models()
    (pe, pv), (se, sv) = S["primary"], S["secondary"]
    T = {}
    t0 = time.perf_counter()
    out = P.analyse(bgr, "contour", variants=tuple(dict.fromkeys([pv, sv])), engines=tuple(dict.fromkeys([pe, se])), timings=T)
    prim, sec = out["ocr"][(pv, pe)], out["ocr"][(sv, se)]
    unc = P.uncertainty_features(prim, sec)
    row = {**out["feats"], **unc}
    X = pd.DataFrame([row])
    t1 = time.perf_counter()
    p = float(S["rej"].score(X)[0])
    tau = float(S["taus"][risk])
    # readability (quality-only classifier)
    rdm = S["rd"]
    feats = rdm["features"]
    Xr = X[feats].values.astype(float)
    pred = str(rdm["model"].predict(Xr)[0])
    probs = {}
    if hasattr(rdm["model"], "predict_proba"):
        pr = rdm["model"].predict_proba(Xr)[0]
        probs = {str(c): float(v) for c, v in zip(rdm["model"].classes_, pr)}
    text = prim["text"]
    if not text:
        decision = "no_mark"
    else:
        decision = "accept" if p >= tau else "recapture"
    cause, guide_txt, dz = S["guid"].diagnose(row)
    oled = HW.render_oled(decision, text, p, pred, guide_txt, float(risk))
    # annotated frame
    vis = bgr.copy()
    x1, y1, x2, y2 = [int(v) for v in out["loc"]["box"]]
    col = (80, 200, 80) if decision == "accept" else (60, 60, 230)
    cv2.rectangle(vis, (x1, y1), (x2, y2), col, 2)
    roi_img = out["images"][pv]
    res = dict(
        decision=decision, text=text, p_correct=p, tau=(None if not np.isfinite(tau) else tau), risk_target=float(risk),
        readability=pred, readability_probs=probs, guidance=guide_txt, guidance_cause=cause,
        engines={"primary": dict(engine=pe, variant=pv, text=prim["text"], conf=prim["conf"]),
                 "secondary": dict(engine=se, variant=sv, text=sec["text"], conf=sec["conf"])},
        disagreement=unc["disagree"], grammar_valid=bool(unc["p_grammar"]),
        quality={k: float(out["feats"][k]) for k in ("f_lapvar_log", "r_lapvar_log", "r_contrast", "f_bright", "f_illum_nonuni",
                                                        "f_sat_frac", "r_height", "f_noise")},
        localisation=dict(box=[x1, y1, x2, y2], fallback=bool(out["loc"].get("fallback", False))),
        timings_ms={k: round(v, 1) for k, v in T.items()}, total_ms=round((t1 - t0) * 1000 + (time.perf_counter() - t1) * 1000, 1),
        images=dict(frame=b64(vis), roi=b64(roi_img), oled=base64_png(HW.oled_png(oled))),
        simulated=["camera", "LED", "buttons", "OLED panel"],
    )
    return res


def base64_png(raw):
    return "data:image/png;base64," + base64.b64encode(raw).decode()


@app.route("/")
def index():
    S = load_models()
    return render_template("index.html", risk_targets=list(S["taus"].keys()), conds=synth.CONDITIONS)


@app.route("/api/health")
def health():
    S = load_models()
    return jsonify(ok=True, primary=S["primary"], secondary=S["secondary"], taus={k: (v if np.isfinite(v) else None) for k, v in S["taus"].items()})


@app.route("/api/capture", methods=["POST"])
def capture():
    """SIMULATED camera: render a synthetic inscription under the chosen acquisition condition and run the pipeline."""
    j = request.get_json(force=True)
    cond = j.get("condition", "clean")
    seed = int(j.get("seed", random.randint(0, 10 ** 9)))
    led = bool(j.get("led", True))
    rng = random.Random(seed)
    src = rng.choice(CFG["dataset"]["sources"])
    spec = dict(item_id="SIM", source=src, split="sim", text=j.get("text") or synth.make_text(rng), style=rng.choice(synth.STYLES),
                font_path=rng.choice(synth.SOURCES[src]["fonts"]), cap_h=rng.randint(52, 74), seed=rng.randint(0, 2 ** 31 - 1))
    level = j.get("severity")
    params = synth.sample_degradation(cond, random.Random(seed + 1), level=None if level is None else float(level))
    params = HW.led_effect(params, led)
    img, ann = synth.render_acquisition(spec, cond, seed + 2, tuple(CFG["dataset"]["image_size"]), params=params)
    res = analyse_image(img, str(j.get("risk", "0.05")))
    res["simulated_ground_truth"] = dict(text=spec["text"], condition=cond, readability_proxy=ann["readability"], style=spec["style"],
                                         note="SYNTHETIC image; ground truth shown only for demonstration")
    res["images"]["input"] = b64(img)
    return jsonify(res)


@app.route("/api/analyze", methods=["POST"])
def analyze_upload():
    f = request.files.get("image")
    if f is None:
        return jsonify(error="no image uploaded"), 400
    arr = np.frombuffer(f.read(), np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify(error="could not decode image"), 400
    h, w = img.shape[:2]
    s = 640 / max(h, w)
    if s < 1:
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    res = analyse_image(img, request.form.get("risk", "0.05"))
    res["images"]["input"] = b64(img)
    return jsonify(res)


if __name__ == "__main__":
    load_models()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5055)), debug=False)
