/*
 * Spinning-mirror sculpture: ESP32 stepper firmware
 * ==================================================
 * Drives 1..3 NEMA 17 steppers through TMC2209 drivers on plain STEP/DIR.
 *   - 1 motor : the 150 mm single test rig
 *   - 2 motors: the 100 mm wall piece (one motor at each rail end)
 *
 * Board: Seeed XIAO ESP32-S3. In the Arduino IDE choose "XIAO_ESP32S3" and set
 * Tools > USB CDC On Boot > Enabled, or Serial will not appear on the USB-C port.
 *
 * NOT RUN ON HARDWARE, NOT EVEN COMPILED. Written against the ESP32 Arduino
 * core 3.x API (timerBegin(freq) / timerAttachInterrupt / timerAlarm).
 * Read README.md first.
 *
 * How it works
 *   1. A 100 kHz hardware timer interrupt runs a phase accumulator per motor.
 *      When an accumulator overflows, that motor's STEP pin goes high; it goes
 *      low again on the next tick (about 10 us pulse). All motors that overflow
 *      on the same tick are raised with ONE register write, so motors with the
 *      same speed step on exactly the same tick = exact lock-step.
 *   2. loop() runs a 1 kHz ramp: it moves the current speed toward the target
 *      with a limited acceleration (trapezoid ramp), then hands every motor's
 *      new step rate to the ISR inside one critical section, so all motors
 *      always receive the same update on the same tick.
 *   3. The random-shift ("jitter") mode only changes the TARGET speed at random
 *      times; the ramp limiter keeps the acceleration inside the torque budget.
 *   4. Serial text commands (from Max/MSP or any serial monitor) set everything.
 *
 * Step-rate budget: tick 100 kHz, so the step rate must stay under 50 kHz and
 * is checked at compile time. At 1/8 microstepping 300 rpm is 8 kHz; at 1/16
 * it is 16 kHz. Step timing is quantised to the 10 us tick (8 % of a step
 * period at 8 kHz). If the TMC2209 sounds rough, raise TICK_HZ (more ISR CPU).
 */

#include <Arduino.h>
#include "soc/gpio_reg.h"

// ----------------------------------------------------------------------------
// Remote dial (ESP-NOW). Set to 0 to leave the radio out entirely.
// The remote unit is firmware/remote_dial/remote_dial.ino: two pots (speed and
// jitter) on a second ESP32. The packet layout and key must match it.
// ----------------------------------------------------------------------------
#define ENABLE_REMOTE_DIAL 1
#if ENABLE_REMOTE_DIAL
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#endif

// ----------------------------------------------------------------------------
// CONFIGURATION  (everything you are likely to edit is in this block)
// ----------------------------------------------------------------------------

// Number of motors: 1 = 150 mm test rig, 2 = 100 mm wall piece, max 3.
#define NUM_MOTORS 1

// Pins for the Seeed XIAO ESP32-S3 (D-number = GPIO in brackets).
// STEP and DIR pins must be GPIO 0..31 (the fast register write used below).
// D6 and D7 (GPIO43, 44) are 32 or above, and D2 (GPIO3) is a boot strapping
// pin, so none of those is used for STEP, DIR or EN.
//   motor 1: STEP D0 (GPIO1), DIR D1 (GPIO2)
//   motor 2: STEP D3 (GPIO4), DIR D4 (GPIO5)
//   motor 3: STEP D8 (GPIO7), DIR D9 (GPIO8)   (only if NUM_MOTORS is 3)
//   EN (shared, active LOW): D5 (GPIO6), with a 10k pull-up to 3V3
//   reserved for the optional Hall inputs: D10 (GPIO9) and D7 (GPIO44)
// If you use a different ESP32 board, change these numbers (and the diagrams).
const uint8_t STEP_PIN[3] = {1, 4, 7};
const uint8_t DIR_PIN[3]  = {2, 5, 8};
const uint8_t EN_PIN      = 6;
// const uint8_t HALL_PIN[2] = {9, 44};   // see the phaseCheck() hook

// 1 = drive only STEP_PIN[0] and wire every driver's STEP input to it
// (identical edges by construction; no independent patterns). DIR pins stay separate.
#define TIE_STEP_PINS 0

// Physical direction per motor. The two wall motors sit at opposite rail ends,
// and every ring must turn the SAME way in the room. If a ring turns the wrong
// way for "dir 1", flip that motor's entry (or swap one coil's two wires).
// Verify on the bench with a mark on the ring.
const bool DIR_INVERT[3] = {false, false, false};

// Per-motor speed scale. All 1.0 = identical (lock-step). Hook for later
// independent patterns; leave at 1.0 for the wall piece.
const float MOTOR_SCALE[3] = {1.0f, 1.0f, 1.0f};

// Driver microstepping. MS1/MS2 open on the Adafruit TMC2209 = 1/8 (the chip
// interpolates to 1/256 internally). If you pull MS1/MS2 for 1/16, check the
// board's table and set MICROSTEPS to 16.
#define MICROSTEPS 8
#define FULL_STEPS_PER_REV 200
// Motor revolutions per spindle (ring) revolution. The belts are 1:1 20T GT2
// pulleys on both wall pieces. Change this if a different pulley pair is used.
constexpr float PULLEY_RATIO = 1.0f;
// Driver steps per SPINDLE revolution; all rpm in this sketch are spindle rpm.
constexpr float STEPS_PER_REV = (float)(FULL_STEPS_PER_REV * MICROSTEPS) * PULLEY_RATIO;

// Step generator tick (Hz). Max step rate is TICK_HZ / 2.
#define TICK_HZ 100000UL

// HARD SPEED CAP, in SPINDLE (ring) rpm. Every path that sets speed (ramp
// target, random shifts, serial commands, final step-rate conversion) is held
// to this. It exists because a mirror that let go of its pegs carries energy
// that scales with speed squared (about 1 J at 600 rpm, 3 J at 1000 rpm for a
// 63 g mirror 0.1 m out). It MUST stay below whatever speed the bench test has
// actually proved safe; do not raise it just because the motor can go faster.
constexpr float MAX_SPINDLE_RPM = 300.0f;

// Acceleration (rad/s^2). Budget from the docs: about 100 is comfortable
// (0.06 N m for the wall piece), 300 is the absolute ceiling (0.19 N m of
// about 0.25 N m available at 24 V).
constexpr float ACCEL_DEFAULT = 100.0f;   // at boot
constexpr float ACCEL_MIN     = 5.0f;     // floor, so a ramp always finishes
constexpr float ACCEL_MAX     = 300.0f;   // hard cap; the "accel" command cannot exceed it

// Jitter defaults (changeable by serial).
constexpr float JITTER_RPM_LO_DEFAULT = 60.0f;
constexpr float JITTER_RPM_HI_DEFAULT = 300.0f;
constexpr float JITTER_T_MIN_DEFAULT  = 2.0f;   // seconds between speed changes, min
constexpr float JITTER_T_MAX_DEFAULT  = 8.0f;   // seconds between speed changes, max

// Remote dial mapping (used only if ENABLE_REMOTE_DIAL).
constexpr float REMOTE_RPM_MAX     = 200.0f;  // speed dial full scale (rpm), kept below MAX_SPINDLE_RPM
constexpr float REMOTE_JIT_MAX     = 0.8f;    // jitter dial full scale (jit fraction)
constexpr int   REMOTE_DEADBAND    = 12;      // permille a pot must move before it counts
constexpr int   REMOTE_ENGAGE      = 40;      // permille a pot must move from its first reading to take over
// 1 lets the speed dial start and stop the drivers by itself (for a standalone
// installation with no laptop). 0 (default) = the dial only changes settings;
// start the drivers from serial or the laptop panel.
#define REMOTE_CAN_ENABLE 0
constexpr uint16_t REMOTE_KEY = 0x5A3C;       // must equal the remote's key; not real security

// After "stop" the drivers are released this long after the motors reach zero.
constexpr uint32_t DISABLE_DELAY_MS = 300;
// Pause between enabling the drivers and the first step (driver power-up).
constexpr uint32_t ENABLE_SETTLE_MS = 20;

// Driver current: set on the Adafruit TMC2209 with its ILimit potentiometer,
// not here. Target 1.2 to 1.5 A per motor on the Pi Hut NEMA 17 42/60
// (1.68 A rated) with the 24 V supply; start at about half way. Heat is the
// limit (about 9 W per motor at full current, motors enclosed).

// ----------------------------------------------------------------------------
// Compile-time checks
// ----------------------------------------------------------------------------
static_assert(NUM_MOTORS >= 1 && NUM_MOTORS <= 3, "NUM_MOTORS must be 1..3");
static_assert(MAX_SPINDLE_RPM / 60.0f * STEPS_PER_REV < (float)TICK_HZ / 2.5f,
              "Step rate at MAX_SPINDLE_RPM too high for TICK_HZ; raise TICK_HZ or lower MICROSTEPS");

// ----------------------------------------------------------------------------
// Step generator (ISR side)
// ----------------------------------------------------------------------------
static hw_timer_t *stepTimer = nullptr;
static portMUX_TYPE stepMux = portMUX_INITIALIZER_UNLOCKED;

static uint32_t stepMask[NUM_MOTORS];        // GPIO bit for each motor's STEP pin
static volatile uint32_t phaseInc[NUM_MOTORS];  // accumulator increment per tick
static uint32_t phaseAcc[NUM_MOTORS];        // touched by the ISR only
static uint32_t pendingClear = 0;            // ISR only

void ARDUINO_ISR_ATTR onStepTick() {
  // End the pulse raised on the previous tick.
  if (pendingClear) {
    REG_WRITE(GPIO_OUT_W1TC_REG, pendingClear);
    pendingClear = 0;
  }
  uint32_t rise = 0;
  for (int i = 0; i < NUM_MOTORS; i++) {
    uint32_t a = phaseAcc[i];
    uint32_t n = a + phaseInc[i];
    phaseAcc[i] = n;
    if (n < a) rise |= stepMask[i];          // overflow = one step
  }
  if (rise) {
    REG_WRITE(GPIO_OUT_W1TS_REG, rise);      // all steps of this tick in ONE write
    pendingClear = rise;
  }
}

// ----------------------------------------------------------------------------
// Motion state (loop side)
// ----------------------------------------------------------------------------
static bool   enabled      = false;   // drivers energised
static bool   stopping     = false;   // ramping to zero, then disable
static uint32_t stopDoneAt = 0;       // millis when speed hit zero while stopping
static uint32_t enabledAt  = 0;       // millis of last enable (settle time)

static float  accelLimit   = ACCEL_DEFAULT;   // rad/s^2
static float  manualRpm    = 0.0f;            // magnitude set by "rpm"
static int    dirSign      = 1;               // +1 / -1 as seen in the room
static float  velRad       = 0.0f;            // current signed speed, rad/s
static float  targetRad    = 0.0f;            // signed target, rad/s

static bool   jitterOn     = false;
static float  jRpmLo       = JITTER_RPM_LO_DEFAULT;
static float  jRpmHi       = JITTER_RPM_HI_DEFAULT;
static float  jTMin        = JITTER_T_MIN_DEFAULT;
static float  jTMax        = JITTER_T_MAX_DEFAULT;
static uint32_t jNextAt    = 0;               // millis of next jitter change
static float  jCurrentRpm  = 0.0f;

// Jitter mode 1 ("ou"): the same random process as the tumble simulator
// (sim/spinning-mirror/spinning-mirror-gimbal-concept.html, option D). Speed = base * (1 + ou),
// where ou is an Ornstein-Uhlenbeck process: zero mean, standard deviation
// jSigma (the simulator's "Motor speed jitter" slider, 0..0.8, 0.45 default) and
// correlation time jTau seconds (the simulator uses 0.2). The base is the
// "rpm" command. With jRev on, 1 + ou may go negative so the ring reverses
// briefly, as in the simulator; with jRev off it is held at zero or above.
// Mode 0 ("walk") is the earlier scheme: a uniform random target in jrange at
// random intervals.
// Mode 2 ("kick"): bang-bang. Every jtime seconds the target jumps to near one
// END of jrange (lo or hi, chosen at random, with a little spread), and with
// jrev on it also flips direction at random. Every change is as sharp as the
// acceleration limit allows and as big as the range (up to lo+hi when it flips).
static const char *const JMODE_NAME[3] = {"walk", "ou", "kick"};
static int    jMode        = 0;       // 0 walk, 1 ou, 2 kick
static float  jKickSign    = 1.0f;    // +1 or -1, used by kick mode
static float  jSigma       = 0.45f;
static float  jTau         = 0.2f;
static bool   jRev         = true;
static float  ouState      = 0.0f;

#if ENABLE_REMOTE_DIAL
// Remote dial state (see the receiver section below).
struct __attribute__((packed)) DialPacket {   // identical in remote_dial.ino
  uint16_t key;
  uint8_t  ver;     // 1
  uint8_t  seq;
  uint16_t speed;   // 0..1000
  uint16_t jitter;  // 0..1000
};
static volatile DialPacket rxPkt;
static volatile bool rxNew = false;
static volatile uint32_t rxAtMs = 0;
static bool remoteEnabled = true;
static bool remoteSeen = false;
static int  baseSpeed = 0, baseJit = 0;       // first readings after boot
static bool speedEngaged = false, jitEngaged = false;
static int  lastSpeed = -1000, lastJit = -1000;
#endif

static uint32_t lastRampUs = 0;

constexpr float RPM_TO_RAD = 2.0f * PI / 60.0f;
constexpr float MAX_SPINDLE_RAD = MAX_SPINDLE_RPM * RPM_TO_RAD;

// Clamp an rpm magnitude to the hard cap; *clamped is set if it was reduced.
static float capRpm(float rpm, bool *clamped) {
  rpm = fabsf(rpm);
  if (rpm > MAX_SPINDLE_RPM) { if (clamped) *clamped = true; return MAX_SPINDLE_RPM; }
  return rpm;
}

// ---- helpers ---------------------------------------------------------------

static float randomFloat(float lo, float hi) {
  if (hi < lo) { float t = lo; lo = hi; hi = t; }
  return lo + (hi - lo) * ((float)(esp_random() >> 8) / 16777216.0f);
}

static void driversEnable(bool on) {
  digitalWrite(EN_PIN, on ? LOW : HIGH);    // active low
  enabled = on;
  if (on) enabledAt = millis();
}

// Push the current speed to every motor atomically.
static void applySpeed() {
  // Last line of defence: whatever got here, never exceed the cap. One value
  // is computed once and used for every motor, so they stay in lock-step.
  if (velRad > MAX_SPINDLE_RAD) velRad = MAX_SPINDLE_RAD;
  else if (velRad < -MAX_SPINDLE_RAD) velRad = -MAX_SPINDLE_RAD;
  float stepsPerSec = fabsf(velRad) / (2.0f * PI) * STEPS_PER_REV;
  bool forward = velRad >= 0.0f;
  uint32_t inc[NUM_MOTORS];
  bool dirLevel[NUM_MOTORS];
  for (int i = 0; i < NUM_MOTORS; i++) {
    float sps = stepsPerSec * MOTOR_SCALE[i];
    float f = sps * (4294967296.0f / (float)TICK_HZ);
    if (f > 2147483000.0f) f = 2147483000.0f;   // never above half the tick rate
    inc[i] = (uint32_t)f;
    dirLevel[i] = (forward != DIR_INVERT[i]);
  }
  portENTER_CRITICAL(&stepMux);
  for (int i = 0; i < NUM_MOTORS; i++) {
    digitalWrite(DIR_PIN[i], dirLevel[i] ? HIGH : LOW);
    phaseInc[i] = inc[i];
  }
  portEXIT_CRITICAL(&stepMux);
}

static float gaussian() {   // Box-Muller
  float u1 = ((float)(esp_random() >> 8) + 1.0f) / 16777217.0f;   // (0,1]
  float u2 = (float)(esp_random() >> 8) / 16777216.0f;
  return sqrtf(-2.0f * logf(u1)) * cosf(2.0f * PI * u2);
}

static void scheduleJitter(uint32_t now) {
  jNextAt = now + (uint32_t)(randomFloat(jTMin, jTMax) * 1000.0f);
}

static void pickJitterTarget() {
  if (jMode == 2) {
    float end = (esp_random() & 1) ? jRpmHi : jRpmLo;
    jCurrentRpm = capRpm(end * randomFloat(0.85f, 1.0f), nullptr);
    jKickSign = (jRev && (esp_random() & 1)) ? -1.0f : 1.0f;
  } else {
    jCurrentRpm = capRpm(randomFloat(jRpmLo, jRpmHi), nullptr);
    jKickSign = 1.0f;
  }
}

// ---- Hall / phase-check hook (NOT IMPLEMENTED) ------------------------------
// Optional later: one Hall sensor + magnet on one ring per wall half (D10 / GPIO9 and D7 / GPIO44). Attach an interrupt per sensor that stores micros()
// of each revolution, compare the two once per revolution, and nudge one motor's
// phase (add or skip a few steps in its accumulator, inside stepMux) to correct
// drift. Open-loop steppers with identical pulses should not drift unless a
// motor skips steps, which this would catch. Call phaseCheck() from loop().
static inline void phaseCheck() { /* hook: intentionally empty */ }

// ---- ramp ------------------------------------------------------------------
static void rampStep() {
  uint32_t nowUs = micros();
  uint32_t dtUs = nowUs - lastRampUs;
  if (dtUs < 1000) return;                  // run at 1 kHz
  lastRampUs = nowUs;
  float dt = dtUs * 1e-6f;
  if (dt > 0.05f) dt = 0.05f;               // after a stall, don't jump

  uint32_t nowMs = millis();

  if (!enabled || (nowMs - enabledAt) < ENABLE_SETTLE_MS) {
    velRad = 0.0f;
    applySpeed();
    return;
  }

  // Choose the target.
  if (stopping) {
    targetRad = 0.0f;
  } else if (jitterOn) {
    if ((int32_t)(nowMs - jNextAt) >= 0) {
      pickJitterTarget();
      scheduleJitter(nowMs);
    }
    if (jMode == 1) {
      // exact OU update: ou += -ou/tau*dt + sigma*sqrt(2*dt/tau)*N(0,1)
      float k = dt / jTau;
      if (k > 1.0f) k = 1.0f;
      ouState += -ouState * k + jSigma * sqrtf(2.0f * k) * gaussian();
      float f = 1.0f + ouState;
      if (!jRev && f < 0.0f) f = 0.0f;
      targetRad = dirSign * manualRpm * f * RPM_TO_RAD;   // capped below
    } else {
      targetRad = dirSign * jKickSign * jCurrentRpm * RPM_TO_RAD;
    }
  } else {
    targetRad = dirSign * manualRpm * RPM_TO_RAD;
  }

  if (targetRad > MAX_SPINDLE_RAD) targetRad = MAX_SPINDLE_RAD;
  else if (targetRad < -MAX_SPINDLE_RAD) targetRad = -MAX_SPINDLE_RAD;

  // Trapezoid ramp: move velRad toward targetRad by at most accel * dt.
  float maxDelta = accelLimit * dt;
  float diff = targetRad - velRad;
  if (diff > maxDelta) diff = maxDelta;
  else if (diff < -maxDelta) diff = -maxDelta;
  velRad += diff;

  applySpeed();

  // Release drivers a moment after a requested stop completes.
  if (stopping) {
    if (velRad == 0.0f) {
      if (stopDoneAt == 0) stopDoneAt = nowMs;
      else if (nowMs - stopDoneAt >= DISABLE_DELAY_MS) {
        driversEnable(false);
        stopping = false;
        stopDoneAt = 0;
      }
    } else {
      stopDoneAt = 0;
    }
  }
}

// ----------------------------------------------------------------------------
// Commands
// ----------------------------------------------------------------------------
static void cmdEnable(bool on) {
  if (on) {
    stopping = false;
    stopDoneAt = 0;
    if (!enabled) {
      velRad = 0.0f;                        // soft start: always from zero
      applySpeed();
      driversEnable(true);
    }
  } else {
    // Hard disable: the ring freewheels. Use "stop" for a clean ramp down.
    velRad = 0.0f;
    applySpeed();
    driversEnable(false);
    stopping = false;
  }
}

static void cmdStop() {
  if (enabled) { stopping = true; stopDoneAt = 0; }
}

static void cmdEstop() {
  jitterOn = false;
  manualRpm = 0.0f;
  cmdEnable(false);
}

static void printStatus() {
  Serial.printf("status en=%d stopping=%d motors=%d dir=%d rpm_set=%.1f rpm_now=%.1f rpm_target=%.1f "
                "accel=%.0f jitter=%d jmode=%s jit=%.2f jtau=%.2f jrev=%d jrpm=%.0f..%.0f jtime=%.1f..%.1f"
#if ENABLE_REMOTE_DIAL
                " remote=%d remote_seen=%d remote_age_ms=%ld\n",
#else
                "\n",
#endif
                enabled, stopping, NUM_MOTORS, dirSign, manualRpm,
                velRad / RPM_TO_RAD, targetRad / RPM_TO_RAD, accelLimit,
                jitterOn, JMODE_NAME[jMode], jSigma, jTau, jRev, jRpmLo, jRpmHi, jTMin, jTMax
#if ENABLE_REMOTE_DIAL
                , remoteEnabled, remoteSeen, remoteSeen ? (long)(millis() - rxAtMs) : -1L
#endif
                );
}

static void printHelp() {
  Serial.println(
    "commands (one per line):\n"
    "  enable 0|1        energise / release drivers (starts from zero speed)\n"
    "  start             enable and apply rpm/jitter (soft start)\n"
    "  stop              ramp to zero, then release drivers\n"
    "  estop             release drivers now, clear rpm and jitter\n"
    "  rpm <0..cap>      target speed magnitude (clamped to MAX_SPINDLE_RPM)\n"
    "  dir <1|-1|cw|ccw> direction (reversal ramps through zero)\n"
    "  accel <rad/s2>    acceleration limit (5..300, default 100)\n"
    "  jitter 0|1        random speed shifts on/off\n"
    "  jrange <lo> <hi>  jitter speed range in rpm\n"
    "  jtime <min> <max> jitter interval range in seconds (walk mode)\n"
    "  jmode walk|ou|kick walk = random targets in jrange; ou = simulator-style wobble around rpm;\n"
    "                    kick = sharp jumps to the ends of jrange (flips direction if jrev 1)\n"
    "  jit <0..0.8>      ou mode: speed jitter, fraction of rpm (simulator slider /100)\n"
    "  jtau <0.02..5>    ou mode: correlation time, seconds (simulator uses 0.2)\n"
    "  jrev 0|1          ou mode: allow brief reversals (1) or hold speed at 0 or above (0)\n"
    "  remote 0|1        ignore / listen to the remote dial (1 re-baselines it)\n"
    "  status            one-line state\n"
    "  help");
}

static void handleLine(char *line) {
  // lower-case the command word, tokenise
  char *cmd = strtok(line, " \t,");
  if (!cmd) return;
  for (char *p = cmd; *p; p++) *p = tolower(*p);
  char *a1 = strtok(nullptr, " \t,");
  char *a2 = strtok(nullptr, " \t,");

  if (!strcmp(cmd, "enable")) {
    if (!a1) { Serial.println("err enable needs 0 or 1"); return; }
    cmdEnable(atoi(a1) != 0);
    Serial.println("ok enable");
  } else if (!strcmp(cmd, "start")) {
    cmdEnable(true);
    Serial.println("ok start");
  } else if (!strcmp(cmd, "stop")) {
    cmdStop();
    Serial.println("ok stop");
  } else if (!strcmp(cmd, "estop")) {
    cmdEstop();
    Serial.println("ok estop");
  } else if (!strcmp(cmd, "rpm")) {
    if (!a1) { Serial.println("err rpm needs a number"); return; }
    float v = atof(a1);
    bool clamped = false;
    manualRpm = capRpm(v, &clamped);
    // A negative number is accepted as a direction change too.
    if (v < 0.0f) dirSign = -1;
    if (clamped) Serial.printf("ok rpm %.1f CLAMPED (asked %.1f, cap %.0f)\n", manualRpm, v, MAX_SPINDLE_RPM);
    else Serial.printf("ok rpm %.1f\n", manualRpm);
  } else if (!strcmp(cmd, "dir")) {
    if (!a1) { Serial.println("err dir needs 1, -1, cw or ccw"); return; }
    if (!strcasecmp(a1, "cw")) dirSign = 1;
    else if (!strcasecmp(a1, "ccw")) dirSign = -1;
    else dirSign = (atoi(a1) < 0) ? -1 : 1;
    Serial.printf("ok dir %d\n", dirSign);
  } else if (!strcmp(cmd, "accel")) {
    if (!a1) { Serial.println("err accel needs a number"); return; }
    accelLimit = constrain(atof(a1), ACCEL_MIN, ACCEL_MAX);
    Serial.printf("ok accel %.0f\n", accelLimit);
  } else if (!strcmp(cmd, "jitter")) {
    if (!a1) { Serial.println("err jitter needs 0 or 1"); return; }
    jitterOn = atoi(a1) != 0;
    if (jitterOn) ouState = 0.0f;
    if (jitterOn) { pickJitterTarget(); scheduleJitter(millis()); }
    Serial.printf("ok jitter %d\n", jitterOn);
  } else if (!strcmp(cmd, "jrange")) {
    if (!a1 || !a2) { Serial.println("err jrange needs lo hi"); return; }
    bool clamped = false;
    float lo = capRpm(atof(a1), &clamped);
    float hi = capRpm(atof(a2), &clamped);
    if (hi < lo) { float t = lo; lo = hi; hi = t; }
    jRpmLo = lo; jRpmHi = hi;
    Serial.printf("ok jrange %.0f %.0f%s\n", jRpmLo, jRpmHi, clamped ? " CLAMPED (cap applied)" : "");
  } else if (!strcmp(cmd, "jtime")) {
    if (!a1 || !a2) { Serial.println("err jtime needs min max"); return; }
    float lo = max(0.1f, (float)atof(a1));
    float hi = max(0.1f, (float)atof(a2));
    if (hi < lo) { float t = lo; lo = hi; hi = t; }
    jTMin = lo; jTMax = hi;
    Serial.printf("ok jtime %.1f %.1f\n", jTMin, jTMax);
  } else if (!strcmp(cmd, "jmode")) {
    if (!a1) { Serial.println("err jmode needs walk or ou"); return; }
    jMode = (!strcasecmp(a1, "ou") || !strcmp(a1, "1")) ? 1 : (!strcasecmp(a1, "kick") || !strcmp(a1, "2")) ? 2 : 0;
    jKickSign = 1.0f;
    ouState = 0.0f;
    Serial.printf("ok jmode %s\n", JMODE_NAME[jMode]);
  } else if (!strcmp(cmd, "jit")) {
    if (!a1) { Serial.println("err jit needs 0..0.8"); return; }
    jSigma = constrain(atof(a1), 0.0f, 0.8f);
    Serial.printf("ok jit %.2f\n", jSigma);
  } else if (!strcmp(cmd, "jtau")) {
    if (!a1) { Serial.println("err jtau needs seconds"); return; }
    jTau = constrain(atof(a1), 0.02f, 5.0f);
    Serial.printf("ok jtau %.2f\n", jTau);
  } else if (!strcmp(cmd, "jrev")) {
    if (!a1) { Serial.println("err jrev needs 0 or 1"); return; }
    jRev = atoi(a1) != 0;
    Serial.printf("ok jrev %d\n", jRev);
#if ENABLE_REMOTE_DIAL
  } else if (!strcmp(cmd, "remote")) {
    if (!a1) { Serial.println("err remote needs 0 or 1"); return; }
    remoteEnabled = atoi(a1) != 0;
    if (remoteEnabled) { speedEngaged = jitEngaged = false; remoteSeen = false; }   // re-baseline
    Serial.printf("ok remote %d\n", remoteEnabled);
#endif
  } else if (!strcmp(cmd, "status")) {
    printStatus();
  } else if (!strcmp(cmd, "help") || !strcmp(cmd, "?")) {
    printHelp();
  } else {
    Serial.printf("err unknown command '%s' (try help)\n", cmd);
  }
}

static void pollSerial() {
  static char buf[64];
  static uint8_t n = 0;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r' || c == ';') {   // ';' lets Max send several per line
      if (n) { buf[n] = 0; handleLine(buf); n = 0; }
    } else if (n < sizeof(buf) - 1) {
      buf[n++] = c;
    }
  }
}

// ----------------------------------------------------------------------------
// Remote dial receiver
// ----------------------------------------------------------------------------
#if ENABLE_REMOTE_DIAL

static void onDialRx(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len != (int)sizeof(DialPacket)) return;
  DialPacket p; memcpy(&p, data, sizeof(p));
  if (p.key != REMOTE_KEY || p.ver != 1 || p.speed > 1000 || p.jitter > 1000) return;
  memcpy((void *)&rxPkt, &p, sizeof(p));
  rxAtMs = millis();
  rxNew = true;
}

static void remoteBegin() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);   // both units use channel 1
  if (esp_now_init() != ESP_OK) { Serial.println("remote: esp_now_init failed"); return; }
  esp_now_register_recv_cb(onDialRx);
  Serial.println("remote dial receiver on (ESP-NOW, channel 1)");
}

static void remotePoll() {
  if (!rxNew) return;
  DialPacket p; memcpy(&p, (const void *)&rxPkt, sizeof(p));
  rxNew = false;
  if (!remoteEnabled) return;
  int sp = p.speed, ji = p.jitter;
  if (!remoteSeen) { remoteSeen = true; baseSpeed = sp; baseJit = ji; return; }   // first reading: baseline only

  if (!speedEngaged && abs(sp - baseSpeed) > REMOTE_ENGAGE) speedEngaged = true;
  if (!jitEngaged   && abs(ji - baseJit)   > REMOTE_ENGAGE) jitEngaged = true;

  if (speedEngaged && abs(sp - lastSpeed) > REMOTE_DEADBAND) {
    lastSpeed = sp;
    float rpm = (sp < 40) ? 0.0f : REMOTE_RPM_MAX * sp / 1000.0f;   // bottom 4 % = zero
    manualRpm = capRpm(rpm, nullptr);
#if REMOTE_CAN_ENABLE
    if (manualRpm > 0.0f) cmdEnable(true); else cmdStop();
#endif
  }
  if (jitEngaged && abs(ji - lastJit) > REMOTE_DEADBAND) {
    lastJit = ji;
    jSigma = REMOTE_JIT_MAX * ji / 1000.0f;
    if (!jitterOn || jMode != 1) { jMode = 1; jitterOn = true; ouState = 0.0f; }
  }
}
#else
static inline void remoteBegin() {}
static inline void remotePoll() {}
#endif

// ----------------------------------------------------------------------------
// Arduino entry points
// ----------------------------------------------------------------------------
void setup() {
  // Drivers off first thing. (Fit the external 10k pull-up on EN as well, so
  // they are off while the ESP32 is still booting.)
  pinMode(EN_PIN, OUTPUT);
  digitalWrite(EN_PIN, HIGH);

  Serial.begin(115200);
  // USB CDC: wait briefly for the host so the boot banner is not lost.
  { uint32_t t0 = millis(); while (!Serial && millis() - t0 < 2000) delay(10); }

  for (int i = 0; i < NUM_MOTORS; i++) {
    pinMode(STEP_PIN[i], OUTPUT);
    digitalWrite(STEP_PIN[i], LOW);
    pinMode(DIR_PIN[i], OUTPUT);
    digitalWrite(DIR_PIN[i], DIR_INVERT[i] ? HIGH : LOW);
    phaseInc[i] = 0;
    phaseAcc[i] = 0;
#if TIE_STEP_PINS
    stepMask[i] = (i == 0) ? (1UL << STEP_PIN[0]) : 0;   // only pin 0 is driven
#else
    stepMask[i] = 1UL << STEP_PIN[i];
#endif
  }
#if TIE_STEP_PINS
  // All motors share STEP_PIN[0]: motor 0's accumulator drives it; the others
  // must follow the same increment (they do: same MOTOR_SCALE) but have no pin.
#endif

  // Timer at 1 MHz base, alarm every (1e6 / TICK_HZ) counts, auto-reload.
  stepTimer = timerBegin(1000000);
  timerAttachInterrupt(stepTimer, &onStepTick);
  timerAlarm(stepTimer, 1000000UL / TICK_HZ, true, 0);

  remoteBegin();

  lastRampUs = micros();
  jCurrentRpm = JITTER_RPM_LO_DEFAULT;

  Serial.printf("spinning-mirror firmware ready; drivers DISABLED. Type 'help'.\n"
                "speed cap MAX_SPINDLE_RPM=%.0f spindle rpm (%.0f steps/s), accel cap %.0f rad/s2, %d motor(s)\n",
                MAX_SPINDLE_RPM, MAX_SPINDLE_RPM / 60.0f * STEPS_PER_REV, ACCEL_MAX, NUM_MOTORS);
  printStatus();
}

void loop() {
  pollSerial();
  remotePoll();
  rampStep();
  phaseCheck();
}
