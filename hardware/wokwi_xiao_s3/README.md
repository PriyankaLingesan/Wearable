# Wokwi project: XIAO ESP32-S3 (no camera possible)

Files: `diagram.json` (XIAO ESP32-S3, SSD1306 OLED on D4/D5, CAPTURE button on D1, 220 ohm + white LED on D0), `sketch.ino` (the wrist firmware with `Wokwi-GUEST` Wi-Fi), `libraries.txt`.

**What the run shows** (`serial_output_screenshot.jpg`): the firmware compiles and boots; the camera probe fails with `0x106 ESP_ERR_NOT_SUPPORTED` because Wokwi has no camera part; the firmware prints `camera init failed`.

**Not observed:** button press, OLED screens, Wi-Fi connection of this firmware, HTTP POST, any frame, any contact with the companion. The simulator ran at about 3 % of real time. Wokwi does not simulate the camera and nothing here claims it does. The transistor LED driver is not part of this project.

`wokwi_circuit.png/.svg/.pdf` is the circuit of this project **redrawn from `diagram.json`** (parts and wires as in the Wokwi project). It is not a screenshot of the Wokwi site.
