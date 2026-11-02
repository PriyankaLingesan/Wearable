"""Capture storage: every webcam capture / uploaded image is written to disk, then the pipeline reads it BACK from disk, so both
acquisition paths enter the pipeline through exactly the same function (process_stored)."""
import hashlib
import json
import os
import re
import threading
import time
import uuid

import cv2
import numpy as np

from .validate import ALLOWED_EXT, decode_bytes, validate_frame

ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


class CaptureStore:
    def __init__(self, root):
        self.root = root
        os.makedirs(root, exist_ok=True)
        self._lock = threading.Lock()

    def new_id(self, prefix):
        return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"

    def path(self, cid):
        if not ID_RE.match(cid or ""):
            raise KeyError("invalid capture id")
        for ext in (".png",) + tuple(e for e in ALLOWED_EXT if e != ".png"):
            p = os.path.join(self.root, cid + ext)
            if os.path.isfile(p):
                return p
        raise KeyError("unknown capture id")

    def _meta(self, cid, **kw):
        with open(os.path.join(self.root, cid + ".json"), "w") as f:
            json.dump(kw, f, indent=1)

    def save_frame(self, bgr, source, note=""):
        """Webcam frames are stored losslessly as PNG."""
        cid = self.new_id("cam")
        ok, enc = cv2.imencode(".png", bgr)
        data = enc.tobytes()
        with open(os.path.join(self.root, cid + ".png"), "wb") as f:
            f.write(data)
        v = validate_frame(bgr)
        self._meta(cid, id=cid, source=source, saved_at=time.strftime("%Y-%m-%d %H:%M:%S"), sha256=hashlib.sha256(data).hexdigest(),
                   width=bgr.shape[1], height=bgr.shape[0], note=note, validation=v)
        return cid, v

    def save_upload(self, data, filename):
        """Uploaded files are stored byte-for-byte (original format kept) so what was processed can be audited."""
        ext = os.path.splitext(filename or "")[1].lower()
        if ext not in ALLOWED_EXT:
            raise ValueError(f"unsupported file type {ext or '(none)'}; allowed: {', '.join(ALLOWED_EXT)}")
        img = decode_bytes(data)
        v = validate_frame(img)
        cid = self.new_id("upl")
        with open(os.path.join(self.root, cid + ext), "wb") as f:
            f.write(data)
        self._meta(cid, id=cid, source="upload", filename=os.path.basename(filename), saved_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                   sha256=hashlib.sha256(data).hexdigest(), width=img.shape[1], height=img.shape[0], validation=v)
        return cid, v, img

    def save_wearable(self, data):
        """JPEG bytes POSTed by the (proposed) wrist unit are stored byte-for-byte, like an upload."""
        img = decode_bytes(data)
        v = validate_frame(img)
        cid = self.new_id("wrn")
        with open(os.path.join(self.root, cid + ".jpg"), "wb") as f:
            f.write(data)
        self._meta(cid, id=cid, source="wearable", saved_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                   sha256=hashlib.sha256(data).hexdigest(), width=img.shape[1], height=img.shape[0], validation=v)
        return cid, v, img

    def load(self, cid):
        """Read the stored file back from disk (the exact input of the pipeline)."""
        p = self.path(cid)
        with open(p, "rb") as f:
            data = f.read()
        return decode_bytes(data), hashlib.sha256(data).hexdigest(), p

    def log(self, entry):
        with self._lock, open(os.path.join(self.root, "processing_log.jsonl"), "a") as f:
            f.write(json.dumps(entry) + "\n")
