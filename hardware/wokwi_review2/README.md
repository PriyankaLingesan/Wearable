# Wokwi interface simulation (Review 2): control + display layer only

Files: `diagram.json`, `sketch.ino`, `libraries.txt`. Board: Wokwi's `board-xiao-esp32-s3`.

| Part | Pin (XIAO / GPIO) |
|---|---|
| SSD1306 OLED, I2C 0x3C | SDA D4 / GPIO5, SCL D5 / GPIO6, 3V3, GND |
| CAPTURE push button | D1 / GPIO2 to GND (`INPUT_PULLUP`) |
| White LED via 220 ohm | D0 / GPIO1 |

Behaviour: OLED `Ready` -> button press -> LED on, OLED `Capturing...` -> LED off, `Processing...` -> `Capture Complete` -> back to `Ready`; one serial line per state.

## What this is and is not
* **The capture is a timed software sequence.** Wokwi has no camera part; no camera is simulated, no image is taken, no Wi-Fi/HTTP is used here.
* No physical wearable has been built or tested. The wrist-unit firmware (`../wearable_firmware/`) is separate and untested on hardware.
* **Run status:** these files have been prepared and loaded into the Wokwi editor, but a completed run with a captured screenshot has NOT been recorded in this repository yet. Do not cite a screenshot from this folder until one is added (see below).

## How to run it yourself (about 2 minutes)
1. Open https://wokwi.com/projects/new/esp32-s3 and choose the XIAO ESP32-S3 board if asked.
2. Replace `sketch.ino` and `diagram.json` with the files here.
3. Library Manager: add **Adafruit SSD1306** and **Adafruit GFX Library** (`libraries.txt`).
4. Press Start, click the CAPTURE button, and screenshot the circuit, OLED and serial terminal together. Sign in and use Save/Share if you need a project link.
