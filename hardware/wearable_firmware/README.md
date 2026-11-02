# Wrist unit firmware (PROPOSED, never run on hardware)

`wrist_unit/wrist_unit.ino` (about 80 lines): button -> LED on -> JPEG from the camera -> one HTTP POST -> three-line reply on the OLED.

* Board: Seeed XIAO ESP32S3 Sense (Arduino board "XIAO_ESP32S3", PSRAM "OPI PSRAM"). Libraries: Adafruit SSD1306, Adafruit GFX.
* Edit `WIFI_SSID`, `WIFI_PASS` and `SERVER_URL` (the laptop's LAN address, port 5060).
* Companion: `python -m acquisition.server --host 0.0.0.0`.
* Pins: OLED SDA D4 (GPIO5), SCL D5 (GPIO6); button D1 (GPIO2) to GND; LED driver D0 (GPIO1) -> 1 k -> NPN base. Camera pins are fixed by the Sense board.
* Error screens: NO CAMERA, NO IMAGE, NO LINK, REPLY. The unit never shows a result the companion did not send.
* Status: compiled and booted in Wokwi only (which has no camera). Never run with a camera, never sent a POST. See `docs/camera_subsystem_verification.md`.
