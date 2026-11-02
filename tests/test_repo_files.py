"""Repository-consistency tests: Wokwi/firmware files are well-formed and agree with each other, and the bundled SYNTHETIC sample runs
through the real pipeline. These do not test any hardware."""
import json
import os
import re
import sys

import cv2
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
W2 = os.path.join(ROOT, "hardware", "wokwi_review2")


def test_wokwi_review2_diagram_is_valid_and_matches_sketch():
    d = json.load(open(os.path.join(W2, "diagram.json")))
    types = [p["type"] for p in d["parts"]]
    assert "board-xiao-esp32-s3" in types and "board-ssd1306" in types and "wokwi-pushbutton" in types and "wokwi-led" in types
    assert not any("camera" in t.lower() for t in types)            # Wokwi has no camera part; none may be claimed
    ino = open(os.path.join(W2, "sketch.ino")).read()
    ino1 = re.sub(r"\s+", " ", ino)
    for name, gpio in [("SDA", 5), ("SCL", 6), ("BUTTON", 2), ("LED", 1)]:
        assert re.search(rf"PIN_{name}\s*=\s*{gpio}\b", ino1), name
    wires = {(a, b) for a, b, *_ in d["connections"]}
    for w in [("esp:D4", "oled:SDA"), ("esp:D5", "oled:SCL"), ("esp:D1", "btn:1.l"), ("esp:D0", "rLed:1")]:
        assert w in wires, w
    for state in ["Ready", "Capturing", "Processing", "Capture"]:
        assert state in ino


def test_wokwi_sketch_makes_no_camera_or_network_claim():
    ino = open(os.path.join(W2, "sketch.ino")).read()
    assert "esp_camera" not in ino and "WiFi" not in ino and "HTTPClient" not in ino


def test_sample_dataset_is_synthetic_and_runs_through_pipeline():
    from simulator.app import analyse_image
    from acquisition.server import prepare_for_pipeline
    m = pd.read_csv(os.path.join(ROOT, "data", "sample", "manifest_sample.csv"))
    assert len(m) >= 9 and set(m.provenance) == {"synthetic"}
    row = m[m.readability == "readable"].iloc[0]
    img = cv2.imread(os.path.join(ROOT, "data", "sample", row.path))
    assert img is not None
    out = analyse_image(prepare_for_pipeline(img), "0.05")
    assert out["decision"] in {"accept", "recapture", "no_mark"}
