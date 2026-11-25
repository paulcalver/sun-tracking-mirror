/*
 * Remote controller for the spinning mirrors (desk unit, LiPo or USB powered)
 * ==========================================================================
 * Reads a SPEED pot and a JITTER pot and broadcasts their positions (0..1000)
 * over ESP-NOW to the main unit (firmware/spinning_mirror). No router, no
 * pairing, no WiFi password. Both units use WiFi channel 1.
 *
 * Extras on the desk unit (cad/src/spinning_mirror_remote.py):
 *   STOP/GO switch a 16 mm latching on/off switch with an LED ring (LATCHING_SWITCH 1):
 *                   switch on = "send the dials", off = "send speed 0". With a momentary
 *                   button set LATCHING_SWITCH 0 and each press toggles instead.
 *                   The packet format is unchanged: stopping just sends speed 0,
 *                   which the main sketch already treats as 0 rpm (bottom 4 % of the
 *                   dial). Going again ramps the speed back up over about 2 s.
 *                   The drivers stay enabled (holding torque) unless the main
 *                   sketch has REMOTE_CAN_ENABLE 1, which also disables them at 0 rpm.
 *   SEND LED        (the switch's LED ring, or a 5 mm LED) heartbeat blink while running, steady glow while stopped,
 *                   fast flicker when the battery is low. NOTE: ESP-NOW broadcast has
 *                   no acknowledgement, so the LED shows that this unit is sending,
 *                   NOT that the main unit hears it.
 *   Battery sense   optional 2 x 100k divider from BAT+ to A2 (GPIO3); set
 *                   BATT_SENSE 0 if it is not fitted.
 *
 * COMPILES for the XIAO ESP32-S3 (arduino-cli, core esp32 3.3.x); NOT RUN ON HARDWARE.
 *
 * Pins (XIAO ESP32-S3, ADC1 only so the radio does not disturb the readings):
 *   A0  GPIO1  SPEED pot wiper         (10k linear, ends on 3V3 and GND)
 *   A1  GPIO2  JITTER pot wiper
 *   A2  GPIO3  battery divider middle  (optional)
 *   D3  GPIO4  STOP/GO switch, common to GND, normally-open to the pin (internal pull-up)
 *   D4  GPIO5  LED ring + direct (it has its own resistor, 3 to 6 V), ring - to GND.
 *              For a plain 5 mm LED use 330 ohm in series.
 * Board: XIAO ESP32-S3 (set USB CDC On Boot to Enabled to see the serial prints).
 *
 * The main unit ignores each pot until it has moved a little from its reading
 * at power-up, so switching the remote on never changes a running setting.
 */
#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

const uint8_t SPEED_PIN  = 1;     // XIAO A0 / D0
const uint8_t JITTER_PIN = 2;     // XIAO A1 / D1
const uint8_t BATT_PIN   = 3;     // XIAO A2 / D2
const uint8_t BUTTON_PIN = 4;     // XIAO D3
const uint8_t LED_PIN    = 5;     // XIAO D4
#define LATCHING_SWITCH 1         // 1 = latching on/off switch (closed = go), 0 = momentary button that toggles
#define BATT_SENSE 1              // 1 = divider fitted (two 100k from BAT+ to GND, middle to A2)
constexpr uint16_t REMOTE_KEY = 0x5A3C;      // must equal REMOTE_KEY in spinning_mirror.ino
constexpr uint32_t SEND_EVERY_MS = 50;       // 20 packets a second (also the heartbeat)
const bool INVERT_SPEED = false;             // flip if a pot is wired backwards
const bool INVERT_JITTER = false;
constexpr int ADC_LO = 40, ADC_HI = 4050;    // trim the ends so the dial really reaches 0 and 1000
constexpr int RAMP_PER_TICK = 25;            // permille per 50 ms after GO: 0 to full in 2 s
constexpr int BATT_LOW_MV = 3500;            // flicker the LED below this

struct __attribute__((packed)) DialPacket {  // identical in spinning_mirror.ino
  uint16_t key;
  uint8_t  ver;     // 1
  uint8_t  seq;
  uint16_t speed;   // 0..1000
  uint16_t jitter;  // 0..1000
};

static const uint8_t BROADCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
static uint8_t seqNo = 0;
static bool running = true;       // false = stopped: speed 0 is sent
static int  outSpeed = 0;         // what is actually sent as speed (ramps up after GO)
static bool radioOk = false;

// Average 16 reads and smooth with a one-pole filter, returns 0..1000.
static float smoothSpeed = -1, smoothJit = -1;
static int readPermille(uint8_t pin, float &smooth, bool invert) {
  uint32_t sum = 0;
  for (int i = 0; i < 16; i++) sum += analogRead(pin);
  float v = ((sum / 16.0f) - ADC_LO) / (float)(ADC_HI - ADC_LO) * 1000.0f;
  v = constrain(v, 0.0f, 1000.0f);
  if (smooth < 0) smooth = v; else smooth += 0.3f * (v - smooth);
  int p = constrain((int)(smooth + 0.5f), 0, 1000);
  return invert ? 1000 - p : p;
}

static int batteryMv() {
#if BATT_SENSE
  return analogReadMilliVolts(BATT_PIN) * 2;       // 1:1 divider
#else
  return 4000;
#endif
}

// STOP/GO input with a 30 ms debounce. Latching: returns the new running state when the switch
// changes. Momentary: toggles running on each press. Returns -1 when nothing changed.
static int stopGoChange() {
  static bool stable = HIGH, last = HIGH;
  static uint32_t changed = 0;
  bool now = digitalRead(BUTTON_PIN);
  if (now != last) { last = now; changed = millis(); }
  if (millis() - changed > 30 && now != stable) {
    stable = now;
#if LATCHING_SWITCH
    return stable == LOW ? 1 : 0;                   // closed = go
#else
    if (stable == LOW) return running ? 0 : 1;
#endif
  }
  return -1;
}

// LED: boot = 3 flashes, running = 60 ms blink each second, stopped = steady dim, battery low = 5 Hz flicker.
static void updateLed(bool lowBatt) {
  uint32_t t = millis();
  uint8_t level;
  if (lowBatt)       level = ((t / 100) & 1) ? 255 : 0;
  else if (!radioOk) level = ((t / 100) & 1) ? 255 : 0;
  else if (running)  level = (t % 1000 < 60) ? 255 : 0;
  else               level = 40;
  analogWrite(LED_PIN, level);
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(SPEED_PIN, ADC_11db);     // full 0 to 3.3 V
  analogSetPinAttenuation(JITTER_PIN, ADC_11db);
  analogSetPinAttenuation(BATT_PIN, ADC_11db);

#if LATCHING_SWITCH
  running = (digitalRead(BUTTON_PIN) == LOW);       // follow the switch position at power-up
#endif
  for (int i = 0; i < 3; i++) { digitalWrite(LED_PIN, HIGH); delay(80); digitalWrite(LED_PIN, LOW); delay(80); }

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);
  if (esp_now_init() != ESP_OK) { Serial.println("esp_now_init failed"); return; }
  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, BROADCAST, 6);
  peer.channel = 1;
  peer.encrypt = false;                             // broadcast cannot be encrypted
  if (esp_now_add_peer(&peer) != ESP_OK) { Serial.println("add_peer failed"); return; }
  radioOk = true;
  Serial.println("remote dial ready");
}

void loop() {
  static uint32_t last = 0;
  static int battMv = 4000;
  int chg = stopGoChange();
  if (chg >= 0 && (bool)chg != running) {
    running = chg;
    if (running) outSpeed = 0;                      // GO: ramp up from zero to the pot
    Serial.println(running ? "GO" : "STOP");
  }
  updateLed(battMv < BATT_LOW_MV);
  if (millis() - last < SEND_EVERY_MS) return;
  last = millis();

  int sp = readPermille(SPEED_PIN, smoothSpeed, INVERT_SPEED);
  int ji = readPermille(JITTER_PIN, smoothJit, INVERT_JITTER);
  if (!running) outSpeed = 0;
  else if (outSpeed < sp) outSpeed = min(sp, outSpeed + RAMP_PER_TICK);
  else outSpeed = sp;                               // turning down follows the pot at once
  battMv += (batteryMv() - battMv) / 8;             // slow filter

  DialPacket p;
  p.key = REMOTE_KEY; p.ver = 1; p.seq = seqNo++;
  p.speed = outSpeed; p.jitter = ji;
  if (radioOk) esp_now_send(BROADCAST, (const uint8_t *)&p, sizeof(p));
  static uint32_t lastPrint = 0;
  if (millis() - lastPrint > 1000) {
    lastPrint = millis();
    Serial.printf("speed %u (pot %d) jitter %u %s battery %d mV\n", p.speed, sp, p.jitter, running ? "GO" : "STOP", battMv);
  }
}
