"""PROPOSED wiring reference for the wrist unit: XIAO ESP32S3 Sense + camera, button, white LED + driver, OLED. Never built, never powered.
Not a Wokwi render (Wokwi has no camera part)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlib import Canvas, OUT

c = Canvas(11.0, 6.6); ax = c.ax
c.text(5.5, 6.4, "Wrist unit wiring reference (PROPOSED, NOT BUILT, NOT TESTED)", fs=10.5, bold=True)
c.text(5.5, 6.13, "Only compile, boot and the camera-probe failure were run, on a Wokwi XIAO ESP32-S3 with OLED, button and LED (Wokwi has no camera part).", fs=6.8, color="#8a5a00")

def wire(pts, color="#333"):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=1.3, solid_capstyle="round", zorder=3)

c.section(3.3, 1.45, 4.3, 4.45, "Seeed XIAO ESP32S3 Sense (ESP32-S3R8, 8 MB PSRAM)", "B", fs=7.6)
c.box(3.5, 4.1, 3.9, 1.35, "Camera on the Sense expansion board\nproposed OV5640 AF (vendor: OV5640 or OV3660 may ship)\nboard-to-board connector: NO external wiring\nXCLK 10  PCLK 13  VSYNC 38  HREF 47\nData 15, 17, 18, 16, 14, 12, 11, 48   SCCB SDA 40 / SCL 39", "A", fs=6.2, badge="NOT TESTED")
c.box(3.5, 3.2, 3.9, 0.7, "Camera, microphone and microSD GPIOs are used by the board.\nD8-D10 share the SD pins and are left unused.", "gray", fs=6.0, bold_first=False)
c.box(3.5, 1.65, 3.9, 1.35, "Firmware (about 80 lines)\nbutton -> LED on -> JPEG frame -> HTTP POST\nreply (3 lines) -> OLED\nno OCR / ML on this unit", "B", fs=6.6, badge="NOT TESTED")

c.box(8.3, 5.0, 2.5, 0.8, "SSD1306 OLED 128x64, I2C\nVCC 3V3 | GND | SDA | SCL", "C", fs=6.4, badge="SIMULATED")
wire([(7.6, 5.55), (8.3, 5.55)]); c.text(7.95, 5.68, "D4 SDA", fs=5.6)
wire([(7.6, 5.2), (8.3, 5.2)]); c.text(7.95, 5.08, "D5 SCL", fs=5.6)
c.box(8.3, 3.85, 2.5, 0.8, "CAPTURE push-button\nD1 / GPIO2 to GND\n(internal pull-up)", "C", fs=6.4, badge="SIMULATED")
wire([(7.6, 4.25), (8.3, 4.25)]); c.text(7.95, 4.38, "D1", fs=5.8)
c.box(8.3, 2.0, 2.5, 1.55, "White illumination LED stage\nD0/GPIO1 -> 1 k -> NPN base\nLED + series resistor from 5 V to\ncollector; emitter to GND\n(resistor from the LED datasheet)", "A", fs=6.0, badge="PROPOSED")
wire([(7.6, 2.8), (8.3, 2.8)]); c.text(7.95, 2.93, "D0", fs=5.8)

c.box(0.25, 3.9, 2.6, 1.6, "Power (proposed)\nUSB-C 5 V from a power bank\n3V3 regulator on the XIAO feeds\nESP32-S3, camera and OLED;\n5 V pin feeds the LED stage\nBattery operation not designed", "A", fs=6.2, badge="NOT TESTED")
wire([(2.85, 4.7), (3.3, 4.7)])

c.section(0.25, 0.15, 10.55, 1.05, "Link to the Python companion", "C", fs=7.4)
c.box(0.45, 0.25, 4.0, 0.55, "Wi-Fi 2.4 GHz, same network as the laptop", "B", fs=6.4)
c.box(5.0, 0.25, 5.6, 0.55, "One HTTP POST: image/jpeg body to /api/wearable/upload; 3-line text reply", "B", fs=6.4, badge="TESTED")
c.arrow((4.45, 0.52), (5.0, 0.52))
c.text(7.8, 1.3, "Receiver tested with Python clients; the firmware side of the POST has not run.", fs=5.8, color="#555")
for ext, kw in (("png", {"dpi": 300}), ("svg", {}), ("pdf", {})):
    c.fig.savefig(os.path.join(OUT, f"wearable_reference_schematic.{ext}"), **kw)
print("saved")
