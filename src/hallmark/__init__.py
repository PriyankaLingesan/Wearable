"""Quality-aware wearable hallmark recognition with confidence-based recapture guidance.

SOFTWARE-SIMULATION RESEARCH CODE. No physical wearable was built. The bundled dataset is
SYNTHETIC. The system reads visible inscriptions only; it never judges authenticity,
purity, or composition of any jewellery item.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_config(path=None):
    path = path or os.path.join(ROOT, "configs", "default.json")
    with open(path) as f:
        return json.load(f)


CFG = load_config()
