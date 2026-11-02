# Technical verification and limitations

Title: Design of a Smart Wearable System for Gold Jewellery Hallmark Recognition and Readability Assessment (Wearable Computing course project).

## Scope statement
The system **reads visible hallmark-style characters** and estimates how reliable that reading is. It does not verify gold purity, jewellery authenticity or BIS certification, and it never states what an item is made of. All experiments use a **synthetic** benchmark (1440 procedurally generated images of 240 fictitious inscriptions, item-level split 144/48/48); the images are not photographs of real jewellery.

## Evidence classes
| # | Class | Status | Evidence |
|---|---|---|---|
| 1 | Software image acquisition (laptop webcam, image upload) | **Tested** (webcam only with a recorded test video of synthetic frames; no physical webcam) | `tests/test_acquisition.py`, `tests/test_ui_playwright.py`, `docs/screenshots/` |
| 2 | Companion pipeline (quality, localisation, RapidOCR + Tesseract, readability RF, ExtraTrees + isotonic rejection, guidance) | **Implemented and benchmarked on synthetic data**; HTTP receiver tested with a Python client | `results/`, paper Section V, `tests/test_core.py`, `tests/test_wearable_http.py` |
| 3 | Wearable camera unit (XIAO ESP32S3 Sense + proposed camera module (OV5640 AF, unconfirmed), white LED + NPN, button, SSD1306 OLED, firmware, Wi-Fi POST) | **Proposed, unbuilt, unverified** | design only: `hardware/wearable_firmware/`, `docs/camera_subsystem_verification.md`, `diagrams/wearable_reference_schematic.*` |
| 4 | Wokwi simulation | **Run once (earlier session), limited**: compile, boot, expected camera-probe failure. Camera not simulated (no Wokwi camera part). | `hardware/wokwi_xiao_s3/`, serial screenshot |

## Consistency checks made for this package
* Architecture: three sources (wearable HTTP POST, laptop webcam, image upload) feed one `process_stored()` entry point; a wearable reply is a 3-line text response. No MQTT, broker, topics, Last Will, haptic output or device state anywhere in code, firmware, paper or slides; searches for these words find only statements that they are absent (and a test asserting the firmware contains none).
* Pin map (all documents, firmware, Wokwi `diagram.json`, schematic): OLED SDA D4/GPIO5, SCL D5/GPIO6; button D1/GPIO2 (internal pull-up); LED D0/GPIO1 (1 kΩ to NPN base in the proposed design; Wokwi has no NPN part, so Wokwi uses a 220 Ω resistor drive); 5 V USB-C supply. Camera pins are fixed by the board connector.
* Camera (re-verified against the Seeed wiki on 2026-10-31): the vendor's getting-started page lists the Sense with an OV5640 autofocus camera, but also states that boards may ship with either an OV5640 or an OV3660 (fixed focus) during a module transition, and an older vendor camera page describes an OV2640 as the default. The exact module of a delivered kit is therefore **unconfirmed** and is called a *proposed camera module* throughout. The vendor lists no field of view or focus range, so the optical values (about 23 mm field at 30 mm, about 68 px/mm) come from OV2640 figures (Arducam page) and are an illustrative placeholder, **not OV5640 values**. No physical capture, focus, power, current or image-transfer test was performed.
* Endpoint: `POST /api/wearable/upload`, body = JPEG, `Content-Type: image/jpeg`; reply `text/plain`, 3 lines; 400/422 `BAD IMAGE`, 500 `ERROR`. Images are resized to at most 640 px on the longest side by the same function for all sources.
* Paper: every figure and table is referenced in the text; citations are numbered by first appearance; all 20 cited references come from the verified list in `literature/refs.py`. The slides now cite only those 20.
* Experimental results and negative findings (enhancement lowered RapidOCR accuracy; quality features did not improve AURC; development thresholds do not transfer exactly) are unchanged.

## Known limitations
1. Synthetic data only; labels come from generator parameters; small test split (48 items), wide confidence intervals.
2. Off-the-shelf OCR engines, no fine-tuning.
3. No hardware was built; the wearable camera has never captured an image; the LED/NPN stage, power and optics are unmeasured.
4. The device-to-companion link has never been exercised with the firmware; HTTP is unauthenticated, without TLS.
5. The laptop webcam path has not been tested with a physical camera; a fixed-focus laptop webcam usually cannot resolve millimetre-high characters.
6. Latency and memory were measured on a 2-vCPU x86 sandbox, not a Raspberry Pi.
7. Wokwi could not be reopened for this package; the circuit figure is redrawn from `diagram.json`, not a screenshot.
8. Some small text inside the wiring and optics diagrams is hard to read when projected; use the PDF or the PNG/SVG at full size.
9. The browser UI test is occasionally flaky (timing).

## Files changed in this finalisation pass
Paper (readability confusion matrices added as Fig. 8, Wokwi circuit and serial output are now Figs. 9 and 10; title, figure/table cross-references, restored "proposed / not built" labels, Fig. 1 single-column, Fig. 4 result panels enlarged, new Fig. 8 Wokwi circuit), slides (title slide, slide numbers, Wokwi circuit slide, references restricted to the paper's 20), README, test and verification reports. The OCR/ML code, models and results were not modified.
