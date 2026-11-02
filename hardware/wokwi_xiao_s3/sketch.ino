/*
 * Wrist unit for the hallmark reader: Seeed XIAO ESP32S3 Sense (camera board) + OLED + button + white LED.
 * STATUS: PROPOSED. Never run with a camera. (Wokwi can only boot it; it has no camera part.)
 *
 *   button -> LED on -> camera JPEG -> one HTTP POST to the laptop -> show the 3-line text reply on the OLED.
 *
 * The laptop runs `python -m acquisition.server --host 0.0.0.0`. The reply to POST /api/wearable/upload is three text lines:
 *   READ OK | RETAKE | NO MARK  /  transcription or retake hint  /  readability.
 * No OCR, ML, MQTT or other protocol on this board.
 *
 * Pins (XIAO label/GPIO): OLED SDA D4/5, SCL D5/6 | button D1/2 to GND | LED driver D0/1 (1 k -> NPN base).
 * Camera pins are fixed by the Sense board (Seeed wiki). Libraries: Adafruit SSD1306, Adafruit GFX. Arduino board "XIAO_ESP32S3", PSRAM "OPI PSRAM".
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "esp_camera.h"

const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASS = "";
const char *SERVER_URL = "http://192.168.1.50:5060/api/wearable/upload";   // the laptop's LAN address

const int PIN_SDA = 5, PIN_SCL = 6, PIN_BUTTON = 2, PIN_LED = 1;
Adafruit_SSD1306 oled(128, 64, &Wire, -1);
bool cameraOk = false;

void show(const String &title, const String &body = "") {
  oled.clearDisplay(); oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(2); oled.setCursor(0, 0); oled.println(title);
  oled.setTextSize(1); oled.println(body); oled.display();
}

bool initCamera() {
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0; c.ledc_timer = LEDC_TIMER_0;
  c.pin_d0 = 15; c.pin_d1 = 17; c.pin_d2 = 18; c.pin_d3 = 16; c.pin_d4 = 14; c.pin_d5 = 12; c.pin_d6 = 11; c.pin_d7 = 48;
  c.pin_xclk = 10; c.pin_pclk = 13; c.pin_vsync = 38; c.pin_href = 47; c.pin_sccb_sda = 40; c.pin_sccb_scl = 39;
  c.pin_pwdn = -1; c.pin_reset = -1; c.xclk_freq_hz = 20000000;
  c.pixel_format = PIXFORMAT_JPEG; c.frame_size = FRAMESIZE_UXGA; c.jpeg_quality = 10;
  c.fb_count = 1; c.fb_location = CAMERA_FB_IN_PSRAM; c.grab_mode = CAMERA_GRAB_LATEST;
  return esp_camera_init(&c) == ESP_OK;
}

void capture() {
  digitalWrite(PIN_LED, HIGH); show("CAPTURE", "LED on");
  delay(300);                                                  // let exposure settle with the LED on
  for (int i = 0; i < 2; i++) { camera_fb_t *w = esp_camera_fb_get(); if (w) esp_camera_fb_return(w); }
  camera_fb_t *fb = esp_camera_fb_get();
  digitalWrite(PIN_LED, LOW);
  if (!fb) { show("NO IMAGE", "frame grab failed"); return; }
  show("SENDING", "to laptop");
  HTTPClient http; http.setTimeout(20000); http.begin(SERVER_URL); http.addHeader("Content-Type", "image/jpeg");
  int code = http.POST(fb->buf, fb->len);                      // 200 = result in body; 4xx/5xx = one-line error in body
  String reply = code > 0 ? http.getString() : String();
  http.end(); esp_camera_fb_return(fb);
  if (code <= 0) { show("NO LINK", "laptop unreachable"); return; }
  int a = reply.indexOf('\n'), b = reply.indexOf('\n', a + 1);
  if (a < 0 || b < 0) { show("REPLY", reply); return; }
  show(reply.substring(0, a), reply.substring(a + 1, b) + "\n" + reply.substring(b + 1));
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUTTON, INPUT_PULLUP); pinMode(PIN_LED, OUTPUT);
  Wire.begin(PIN_SDA, PIN_SCL); oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  cameraOk = initCamera(); Serial.println(cameraOk ? "camera ok" : "camera init failed");
  show("WI-FI", "connecting"); WiFi.begin(WIFI_SSID, WIFI_PASS, 6);
  while (WiFi.status() != WL_CONNECTED) delay(200);
  Serial.println("wifi connected"); show(cameraOk ? "READY" : "NO CAMERA", "press the button");
}

void loop() {
  if (digitalRead(PIN_BUTTON) == LOW) {
    delay(30);
    if (digitalRead(PIN_BUTTON) == LOW) {
      if (cameraOk) capture(); else show("NO CAMERA", "camera init failed");
      while (digitalRead(PIN_BUTTON) == LOW) delay(10);
    }
  }
  delay(10);
}
