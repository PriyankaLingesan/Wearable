"""Create small MJPG test videos from SYNTHETIC frames. They stand in for a camera ONLY on machines without one (tests, screenshots).
They are not camera footage and not real jewellery."""
import os, sys
import cv2
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from acquisition.synthetic import render_synthetic

OUT = os.path.join(ROOT, "demo"); os.makedirs(OUT, exist_ok=True)
for name, cond, seed in [("test_feed_clean", "clean", 21), ("test_feed_glare", "glare", 13), ("test_feed_blur", "blur", 12)]:
    img, gt = render_synthetic(cond, seed, True)
    h, w = img.shape[:2]
    vw = cv2.VideoWriter(os.path.join(OUT, name + ".avi"), cv2.VideoWriter_fourcc(*"MJPG"), 15.0, (w, h))
    rng = np.random.default_rng(seed)
    for _ in range(20):                                   # static scene + sensor-like noise, so frames differ slightly
        vw.write(np.clip(img.astype(np.int16) + rng.normal(0, 1.5, img.shape), 0, 255).astype(np.uint8))
    vw.release()
    print(name, gt)
