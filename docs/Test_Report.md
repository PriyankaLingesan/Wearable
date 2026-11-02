# Test report

> Historical record of the 2026-10-31 run (24 tests). The current suite has 27 tests; see `VERIFICATION.md` for the final pass.

Final pass run on 2026-10-31 (the run below is the second of the day; results identical) in the cloud sandbox used for development (Linux x86-64, 2 vCPU, no GPU, no camera, no ESP32 hardware).
Python 3.13.18, OpenCV 5.0.0, scikit-learn 1.9.1, RapidOCR (onnxruntime) 1.2.3, Tesseract 5.3.4, Flask 3.1.3, Playwright 1.63.0 (headless Chromium), pytest 9.1.1.

## Commands run and results

| Command | Result |
|---|---|
| `python3 -m pytest tests -q` | **24 passed, 0 failed, 0 skipped** in 29.5 s |
| `python3 -m pytest tests -v` (second run, full list below) | **24 passed, 0 failed, 0 skipped** in 21.0 s |
| `python3 scripts/09_fig4_shots.py` | exit 0; wrote the three result-panel screenshots used for paper Fig. 4 (headless Chromium, test video + synthetic upload) |
| `python3 paper/build_paper.py` (3 passes, then LibreOffice PDF conversion) | exit 0; 6-page paper (checked by rendering) |
| `python3 slides/build_slides.py` (then LibreOffice PDF conversion) | exit 0; 36 slides (every slide rendered and inspected as an image) |
| `python3 diagrams/src/{wearable_reference_schematic,camera_sensing_schematic,new_diagrams,wokwi_circuit}.py` | exit 0; figures regenerated |

Static checks (not tests): text searches for the old title and for MQTT/haptic/broker terms; camera model re-checked against the Seeed wiki pages (see the verification report).

An earlier full run in a previous session had one transient failure of the browser test (`test_ui_end_to_end`) that passed on re-run; in the two runs reported here it passed both times. Treat that test as occasionally flaky (timing of the headless browser), not as a fixed result.

The dataset, feature extraction, training and benchmark scripts (`scripts/01` to `07`) were **not re-run** for this final package; the results in `results/`, `figures/` and the paper are the ones produced earlier by those scripts and are unchanged.

## What each test exercises

| File | Tests | What is exercised | Real software, or emulation / synthetic input |
|---|---|---|---|
| `tests/test_core.py` | 11 | CER/WER against `jiwer`, exact match, risk-coverage and AURC, threshold-for-risk, ECE, synthetic generator determinism and provenance, no item leakage across the split, text grammar, IoU, pipeline output schema, saved models load and score | Real library code on SYNTHETIC images |
| `tests/test_acquisition.py` | 8 | No-camera error reporting; webcam path (OpenCV `VideoCapture` on a **recorded test video of synthetic frames**) reaches the pipeline; upload PNG/JPEG; webcam and upload give the same result for the same pixels; validation and bad uploads; camera-disconnect detection; MJPEG stream delivers JPEG frames | Real OpenCV and Flask code; the "camera" is a video file |
| `tests/test_wearable_http.py` | 4 | `POST /api/wearable/upload` returns 3 text lines equal to a direct pipeline call; same bytes via upload and via the wearable endpoint give the same result; empty, non-image and truncated bodies are rejected with one text line; the firmware source is small and contains no messaging or recognition code | Real Flask endpoint driven by a **Python client**; no ESP32 involved |
| `tests/test_ui_playwright.py` | 1 | Every control of the browser UI clicked in headless Chromium: start/stop preview, capture, retake, process, upload, bad upload, wearable tab; results compared with a direct pipeline call; screenshots saved to `docs/screenshots/` | Real browser and server; camera source is the test video |

Full list of passing tests: `test_acquisition.py` (test_no_camera_errors_are_reported, test_webcam_path_frame_reaches_pipeline, test_different_input_gives_different_output, test_upload_png_and_jpeg_reach_pipeline, test_webcam_and_upload_use_the_same_pipeline, test_validation_and_bad_uploads, test_camera_disconnect_is_detected, test_mjpeg_stream_delivers_jpeg_frames); `test_core.py` (11 tests listed above); `test_ui_playwright.py::test_ui_end_to_end`; `test_wearable_http.py` (4 tests above).

## Wokwi

Observed in an earlier session (serial screenshot `hardware/wokwi_xiao_s3/serial_output_screenshot.jpg`, paper Fig. 9): the firmware compiled and booted on Wokwi's XIAO ESP32-S3 with an OLED, button and LED; the camera probe failed with `0x106 ESP_ERR_NOT_SUPPORTED` because Wokwi has no camera part; the firmware printed `camera init failed`. This was **not re-run** for the final package (wokwi.com was not reachable from the sandbox). Not observed: button press, OLED screens, Wi-Fi connection, HTTP POST, any frame.
The circuit figure `diagrams/wokwi_circuit.png` is **redrawn from `diagram.json`**; it is not a Wokwi screenshot.

## Not verified

* Any physical hardware: the wearable unit, the camera module (proposed OV5640; fitted module unconfirmed), the LED/NPN driver, the OLED, power.
* The firmware's HTTP POST, a real Wi-Fi link, a real captured frame reaching the companion, round-trip latency.
* The laptop webcam path with a physical webcam (only a recorded test video was used).
* Firmware compilation for the real board in this sandbox (not re-run; the Wokwi compile was observed earlier).
* Performance on real jewellery photographs; Raspberry-Pi-class latency; TLS and authentication.
