# Wearable camera subsystem: verification report (simplified design)

Scope: the camera on the **wrist unit**. The laptop-webcam path (`acquisition/`) is a *separate, implemented software path* and is **not** evidence for anything below.
Rule: nothing is called implemented or tested unless it was actually run; everything else is labelled PROPOSED.

## 1. Bottom line

| Question | Answer |
|---|---|
| Camera in the design? | Yes: Seeed **XIAO ESP32S3 Sense** with its proposed camera module: OV5640 with autofocus as listed by the vendor for the Sense; Seeed states boards may ship with an OV5640 or an OV3660 (fixed focus) and older pages describe an OV2640, so the fitted module is **unconfirmed** (one board). |
| Built? | **No.** |
| A frame ever captured by it, in hardware or simulation? | **No.** |
| Does Wokwi support the camera? | **No.** No camera part exists. Camera init fails in the simulator by design. |
| What was run? | The firmware was loaded on Wokwi's XIAO ESP32-S3 board (with OLED, button, LED), **compiled and booted**; the camera probe failed with `0x106 ESP_ERR_NOT_SUPPORTED` and the firmware printed `camera init failed`. The companion's HTTP receiver was tested with a Python client. |
| What remains proposed? | Everything physical: board + camera, wiring, power, LED stage, optics/focus, the firmware's capture and POST, and the end-to-end wearable path. |

## 2. Hardware (exact)

| Item | Selection | Status |
|---|---|---|
| Controller + camera host | Seeed **XIAO ESP32S3 Sense** (ESP32-S3R8, 8 MB PSRAM, 8 MB flash, 2.4 GHz Wi-Fi, USB-C, 21 x 17.8 mm) | vendor data, not measured |
| Camera | **Proposed** OV5640 AF module (board-to-board connector, 8-bit DVP). Verified against the vendor getting-started page (2026-10-31): it lists the OV5640 with auto-focus, says boards may ship with either an OV5640 or an OV3660 during a module transition, and says the OV3660 and OV2640 are fixed focus; an older vendor camera page describes an OV2640 as default. The fitted module is therefore unconfirmed. Optical estimates use OV2640 Arducam numbers only as an illustrative placeholder, not as OV5640 values | PROPOSED |
| Illumination | White LED + NPN stage from the 5 V supply (a GPIO-and-resistor drive would be dim: the white-LED Vf is near 3.3 V) | PROPOSED |
| Display / input | SSD1306 128x64 OLED (I2C 0x3C), one push button | OLED/button present in the Wokwi project; their behaviour was not exercised |
| Power | USB-C 5 V (power bank). Battery operation is not designed | PROPOSED |
| Link | Wi-Fi 2.4 GHz, one HTTP POST | PROPOSED |

No motor, no haptic driver, no extra rail.

## 3. Why a single camera-equipped board
* **ESP32 DevKit-C V4 + camera breakout: rejected.** A DVP camera needs 14 signals; the DevKit-C has no camera connector and PSRAM was not verified.
* **AI-Thinker ESP32-CAM: rejected.** Only GPIO2/4/12/13/14/15 spare, shared with microSD/flash LED, no USB, 5 V >= 2 A advised (JLCPCB guide; secondary source).
* **XIAO ESP32S3 Sense: selected.** One board acquires the image and runs the small interface.

## 4. Pin mapping (Seeed's published tables)

| Function | XIAO label / GPIO | Status |
|---|---|---|
| Camera XCLK / PCLK / VSYNC / HREF | GPIO10 / 13 / 38 / 47 | fixed by the board; in firmware |
| Camera data Y2..Y9 | GPIO15, 17, 18, 16, 14, 12, 11, 48 | fixed; in firmware |
| Camera SCCB SDA / SCL | GPIO40 / 39 | fixed; in firmware |
| OLED SDA / SCL | D4 / GPIO5, D5 / GPIO6 | in firmware + Wokwi project |
| Capture button (to GND, internal pull-up) | D1 / GPIO2 | in firmware + Wokwi project |
| Illumination LED stage | D0 / GPIO1 | in firmware; Wokwi: 220 ohm + LED stand-in |
| Not used | D8-D10 / GPIO7-9 (microSD SPI), GPIO21, GPIO41/42 (mic), D2 / GPIO3 (strapping) | avoided |

## 5. Electrical notes (PROPOSED, unmeasured)
* Vendor figures for current draw are inconsistent or unlisted; no power budget or battery life is claimed.
* LED stage: GPIO -> 1 k -> NPN base; LED + series resistor from 5 V to the collector; emitter to GND. Resistor value comes from the real LED's datasheet (not chosen here).
* OLED: add 4.7 k I2C pull-ups only if the module lacks them.
* Field of view and minimum focus distance of the fitted module: not listed by the vendor; every optical value in this project is an estimate (OV2640 placeholder) and must be measured on the delivered module.

## 6. Communication
One HTTP POST: `POST /api/wearable/upload`, `Content-Type: image/jpeg`, body = JPEG bytes (UXGA 1600x1200, quality 10, PSRAM frame buffer, two warm-up frames discarded). The reply is three text lines. See `wearable_http_interface.md`. The firmware does not check the status code beyond "request failed" and parses the reply as text.

## 7. Wokwi support status
* Wokwi supports the XIAO ESP32-S3 board; its supported-hardware page lists **no camera**; the parts menu has no camera, transistor or vibration motor.
* Therefore **no camera simulation exists and none is claimed**.

## 8. What was actually tested

| Item | Result | Evidence |
|---|---|---|
| Firmware compiles for XIAO ESP32-S3 (Wokwi build service; Adafruit SSD1306 + GFX; esp_camera and HTTPClient from the core) | Compiled | Wokwi run |
| Boots in the Wokwi simulator | Yes | `hardware/wokwi_xiao_s3/serial_output_screenshot.jpg` |
| Camera initialisation in the simulator | Fails as expected: `Detected camera not supported ... 0x106 (ESP_ERR_NOT_SUPPORTED)`, then `camera init failed` | same screenshot |
| Companion receiver | Python-client tests: reply equals a direct pipeline call, stored bytes identical, bad bodies rejected | `tests/test_wearable_http.py` |
| Firmware size/scope | static check: under 100 non-empty lines, no messaging/OCR/ML code, camera pins and endpoint present | same file |

## 9. What was NOT done
* No physical board, camera, LED stage or OLED was built, wired or powered.
* **No image was ever captured by the wearable camera.**
* The firmware's HTTP POST never executed; only a Python client exercised the receiver.
* In the Wokwi run: no button press, no OLED screen and no Wi-Fi connection of this final firmware were observed.
* No power, focus, field-of-view or Wi-Fi throughput measurement.
* The compile was in Wokwi's cloud build service; it is not a build for physical hardware (board package and PSRAM option not verified).

## 10. Files
`hardware/wearable_firmware/wrist_unit/wrist_unit.ino`, `hardware/wokwi_xiao_s3/`, `diagrams/wearable_reference_schematic.*`, `diagrams/wrist_unit_layout.*`, `diagrams/comm_architecture.*`, `diagrams/camera_sensing_schematic.*`, `docs/wearable_http_interface.md`.
