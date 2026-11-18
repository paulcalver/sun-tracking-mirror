/*
 * Remote dial for the spinning mirrors: two pots on a second ESP32.
 * ==================================================================
 * Reads a SPEED pot and a JITTER pot and broadcasts their positions (0..1000)
 * over ESP-NOW to the main unit (firmware/spinning_mirror). No router, no
 * pairing, no WiFi password. Both units use WiFi channel 1.
 *
 * NOT COMPILED, NOT RUN. ESP32 Arduino core 3.x API.
 *
 * Wiring (10k linear pots, each: one end to 3V3, other end to GND, wiper to pin):
 *   SPEED  wiper -> GPIO 34
 *   JITTER wiper -> GPIO 35
 * Optional: 100 nF from each wiper to GND to calm the reading.
 * GPIO 34 and 35 are ADC1 pins, which keep working while the radio is on.
 * Power: USB (power bank or wall adapter).
 *
 * The main unit ignores each pot until it has moved a little from its reading
 * at power-up, so switching the remote on never changes a running setting.
 */
#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

const uint8_t SPEED_PIN  = 34;
const uint8_t JITTER_PIN = 35;
constexpr uint16_t REMOTE_KEY = 0x5A3C;      // must equal REMOTE_KEY in spinning_mirror.ino
constexpr uint32_t SEND_EVERY_MS = 50;       // 20 packets a second (also the heartbeat)
const bool INVERT_SPEED = false;             // flip if a pot is wired backwards
const bool INVERT_JITTER = false;

struct __attribute__((packed)) DialPacket {  // identical in spinning_mirror.ino
  uint16_t key;
  uint8_t  ver;     // 1
  uint8_t  seq;
  uint16_t speed;   // 0..1000
  uint16_t jitter;  // 0..1000
};

static const uint8_t BROADCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
static uint8_t seqNo = 0;

// Average 16 reads and smooth with a one-pole filter, returns 0..1000.
static float smoothSpeed = -1, smoothJit = -1;
static int readPermille(uint8_t pin, float &smooth, bool invert) {
  uint32_t sum = 0;
  for (int i = 0; i < 16; i++) sum += analogRead(pin);
  float v = (sum / 16.0f) / 4095.0f * 1000.0f;
  if (smooth < 0) smooth = v; else smooth += 0.3f * (v - smooth);
  int p = (int)(smooth + 0.5f);
  p = constrain(p, 0, 1000);
  return invert ? 1000 - p : p;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(SPEED_PIN, ADC_11db);     // full 0 to 3.3 V
  analogSetPinAttenuation(JITTER_PIN, ADC_11db);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);
  if (esp_now_init() != ESP_OK) { Serial.println("esp_now_init failed"); return; }
  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, BROADCAST, 6);
  peer.channel = 1;
  peer.encrypt = false;                             // broadcast cannot be encrypted
  if (esp_now_add_peer(&peer) != ESP_OK) Serial.println("add_peer failed");
  Serial.println("remote dial ready");
}

void loop() {
  static uint32_t last = 0;
  if (millis() - last < SEND_EVERY_MS) return;
  last = millis();
  DialPacket p;
  p.key = REMOTE_KEY; p.ver = 1; p.seq = seqNo++;
  p.speed  = readPermille(SPEED_PIN,  smoothSpeed, INVERT_SPEED);
  p.jitter = readPermille(JITTER_PIN, smoothJit,   INVERT_JITTER);
  esp_now_send(BROADCAST, (const uint8_t *)&p, sizeof(p));
  static uint32_t lastPrint = 0;
  if (millis() - lastPrint > 1000) { lastPrint = millis(); Serial.printf("speed %u jitter %u\n", p.speed, p.jitter); }
}
