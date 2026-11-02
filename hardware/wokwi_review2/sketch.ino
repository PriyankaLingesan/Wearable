/* Wokwi interface simulation of the proposed wearable's control and display layer.
 * SIMULATION ONLY: "capture" is a timed software sequence. No camera is simulated (Wokwi has none), no image is taken or sent.
 * Pins (XIAO ESP32-S3, GPIO): OLED SDA 5 (D4), SCL 6 (D5) | button 2 (D1) to GND | LED 1 (D0) via 220 ohm.
 * Libraries: Adafruit SSD1306, Adafruit GFX Library. */
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

const int PIN_SDA = 5, PIN_SCL = 6, PIN_BUTTON = 2, PIN_LED = 1;
Adafruit_SSD1306 oled(128, 64, &Wire, -1);

void show(const char *line1, const char *line2 = "") {
  oled.clearDisplay(); oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(2); oled.setCursor(0, 8); oled.println(line1);
  oled.setTextSize(1); oled.setCursor(0, 44); oled.println(line2);
  oled.display();
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUTTON, INPUT_PULLUP); pinMode(PIN_LED, OUTPUT); digitalWrite(PIN_LED, LOW);
  Wire.begin(PIN_SDA, PIN_SCL);
  oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  Serial.println("[BOOT] Wearable interface simulation (no camera)");
  show("Ready", "press CAPTURE");
  Serial.println("[STATE] Ready");
}

void loop() {
  if (digitalRead(PIN_BUTTON) == LOW) {
    delay(30);
    if (digitalRead(PIN_BUTTON) == LOW) {
      Serial.println("[EVENT] Button pressed");
      digitalWrite(PIN_LED, HIGH); show("Capturing...", "simulated, no camera"); Serial.println("[STATE] Capturing... (LED on, simulated capture)");
      delay(1500);
      digitalWrite(PIN_LED, LOW); show("Processing...", "simulated"); Serial.println("[STATE] Processing... (LED off)");
      delay(1500);
      show("Capture", "Complete (simulated)"); Serial.println("[STATE] Capture Complete (software simulation only)");
      delay(2500);
      show("Ready", "press CAPTURE"); Serial.println("[STATE] Ready");
      while (digitalRead(PIN_BUTTON) == LOW) delay(10);
    }
  }
  delay(10);
}
