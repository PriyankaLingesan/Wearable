# Technical documentation: Design of a Smart Wearable System for Gold Jewellery Hallmark Recognition and Readability Assessment (simulation)

**Scope reminder.** The system reads inscriptions and estimates the reliability of its reading. It never claims authenticity, purity or composition. The wrist unit is a proposed design (not built); the Python pipeline is implemented; data are synthetic.

## 1. Modules (`src/hallmark/`)
| module | role |
|---|---|
| `synth.py` | Procedural renderer (engraved/embossed/stamped/laser on brushed-metal textures), degradation model, per-factor and readability-proxy labels |
| `quality.py` | 21 quality features (frame and ROI): Laplacian variance, Tenengrad, brightness, contrast, illumination non-uniformity, saturation fraction, noise, ROI size, gradient statistic |
| `localize.py` | `contour` (default; anisotropic gradient energy + blob merging), `mser`, `ocrdet` (PP-OCR detector), `full` baseline |
| `enhance.py` | rectify, glare inpaint, flatten, NLM denoise, CLAHE, conditional unsharp, Sauvola (ablation only) |
| `ocr.py` | Tesseract (LSTM, psm 7, no whitelist) and RapidOCR (recogniser, text_score 0) wrappers |
| `pipeline.py` | `analyse()` and `uncertainty_features()` |
| `metrics.py` | CER/WER/exact, classification metrics, risk-coverage, AURC, E-AURC, ECE, Brier, Clopper-Pearson thresholds, cluster bootstrap |
| `models.py` | classifier zoo, `CalibratedRejector`, `Guidance`, persistence |
| `sim_hw.py` | simulated OLED bitmap, LED effect |

## 2. Deployed configuration (`models/deployment.json`)
Primary OCR: RapidOCR on raw grayscale ROI. Secondary: Tesseract on red channel. Rejector base model: ExtraTrees with isotonic calibration (feature set quality+OCR-uncertainty, S5). Readability: RandomForest on quality features. Thresholds (dev-selected): empirical `taus`, bound-based `taus_ucb`; the simulator uses `taus_ucb` (a target with no feasible threshold, e.g. 1 %, always yields RETAKE).

## 3. Data flow
frame -> frame quality -> localise -> ROI -> two OCR runs -> uncertainty features -> rejector score p -> compare with tau(risk target) -> ACCEPT / RETAKE(+hint) / NO MARK; readability proxy shown on OLED. Integrated architecture: `diagrams/architecture_integrated.{svg,png,pdf}` (editable source `diagrams/src/architecture_integrated.py`; SVG text is editable); camera schematic `diagrams/camera_sensing_schematic.*`. Other diagrams: `diagrams/d*.png|svg` with Graphviz sources in `diagrams/src/`.

## 4. Evaluation protocol
Item-level split (144/48/48 items). Model choice, calibration and thresholds on development items only via GroupKFold by item; test evaluated once. Cluster bootstrap over items (1000 resamples) for CIs and paired differences. Leave-one-source-out for generalisation.

## 5. Interfaces
Simulator: `GET /`, `GET /api/health`, `POST /api/capture` (JSON: condition, severity, led, risk, text, seed), `POST /api/analyze` (multipart image, risk). Responses include decision, text, p_correct, tau, readability, guidance, per-stage timings, OLED PNG, and, for synthetic captures only, ground truth.

## 5b. Wearable camera link
One HTTP exchange, no broker: the wrist unit POSTs a JPEG to `/api/wearable/upload` (`acquisition/server.py`), the companion stores it (`store.save_wearable`), validates it, runs `process_stored()` (the same entry point as webcam and upload) and replies with three lines of text. `GET /api/wearable/latest` feeds the page's "Wearable camera" tab. Details: `wearable_http_interface.md`. Firmware: `hardware/wearable_firmware/wrist_unit/wrist_unit.ino` (proposed XIAO ESP32S3 Sense firmware; compiled and booted in Wokwi only, never run with a camera). `acquisition/synthetic.py` renders the synthetic frames used by the tests. Board, pins, power notes and what was/was not tested: `camera_subsystem_verification.md`.

## 5c. Acquisition application (`acquisition/`)
| module | role |
|---|---|
| `camera.py` | `CameraManager`: `cv2.VideoCapture` on a device index (or a test video file), reader thread, MJPEG generator, states `closed/streaming/disconnected/error`, disconnect after 8 failed reads, stale-frame refusal (>2 s); `probe_cameras()` lists devices that deliver a frame |
| `validate.py` | `validate_frame`: 8-bit 3-channel, 64..8000 px, not blank; warnings for low resolution, dark, saturated; `decode_bytes` |
| `store.py` | `CaptureStore`: saves webcam frames as PNG and uploads byte-for-byte, SHA-256 + metadata JSON, `processing_log.jsonl`; id whitelist `[A-Za-z0-9_-]{1,32}` (no path traversal) |
| `server.py` | Flask routes `/api/cameras`, `/api/camera/{open,close,status,stream,capture}`, `/api/upload`, `/api/process`, `/api/job/<id>`, `/api/wearable/upload`, `/api/wearable/latest`; `process_stored()` is the single pipeline entry for both paths (read back from disk, validate, resize longest side <= 640 px, `simulator.app.analyse_image`) |
| `synthetic.py` | `render_synthetic()`: synthetic test frames (used by tests and demo videos) |
Limits: camera selection/disconnect handling verified with a recorded video, not hardware; OpenCV backend behaviour (autofocus, exposure, permissions) differs per OS and is untested; images above 640 px are downscaled (inherited from the simulator, effect on true macro photographs unevaluated); the web server binds to 127.0.0.1 and has no authentication.

## 6. Architecture selection (diagram d12)
Measured on the x86 sandbox (not a Pi): peak RSS of the full dual-engine pipeline about 176 MB (Tesseract-only 118 MB, RapidOCR-only 173 MB); median end-to-end 264 ms. A 512 MB-class board must also hold an OS, so fit is plausible but tight, and Pi latency is unmeasured. Selected design: wrist unit captures/signals/offloads to a companion (phone or laptop) with on-device processing as fallback. Pi 4/5-class and phone specifications were not verified in this work and are not claimed.

## 7. Known issues (honest list)
* Last token truncated in ~10 % of items (generator cut at 16 chars); affects the grammar feature only.
* RapidOCR drops spaces; WER is not meaningful for it, strict exact is low.
* Dev-selected thresholds transfer imperfectly (48 test items).
* Readability and factor labels are generator-defined.
* The earlier OCR extraction run (`results/ocr_raw_v1_discarded.csv`) predates a generator fix and is kept only for audit; it is not used.
