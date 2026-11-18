# Spinning-mirror firmware (ESP32)

**Status: nothing here has been compiled or run on hardware.** It was written from the docs and the ESP32 Arduino core 3.x API. Expect to fix small things on first build, and bench-test with one motor, no ring, before anything is attached.

Sketch: `spinning_mirror/spinning_mirror.ino`. It drives 1 to 3 NEMA 17 steppers through TMC2209 drivers on plain STEP/DIR (no UART), with acceleration-limited speed, a random-speed-shift mode, and USB serial text control for Max/MSP.

## Wiring (38-pin ESP32 dev board, from `docs/spinning-mirror-150-nema17-wiring-and-order.md`)

| ESP32 | Goes to | Notes |
|---|---|---|
| GPIO 25 | driver 1 STEP | motor 1 |
| GPIO 16 | driver 1 DIR | |
| GPIO 26 | driver 2 STEP | motor 2 (wall piece) |
| GPIO 17 | driver 2 DIR | |
| GPIO 27 / 18 | driver 3 STEP / DIR | spare, only if `NUM_MOTORS` is 3 |
| GPIO 19 | EN on every driver | active low; 10k pull-up to 3.3 V so drivers are off at boot |
| 3.3 V | each driver's VDD | |
| GND | each driver's GND | common ground with the 24 V supply |
| 35 | (Hall sensor) | reserved, not used |

MS1, MS2, DIAG, INDEX, UART and SPRD stay open (1/8 microstepping, StealthChop). 24 V supply to each driver's + and GND, with a 100 uF capacitor at each. The 5 V buck converter feeds the ESP32.

**Driver current:** set with the ILimit potentiometer on each Adafruit TMC2209, about 1.2 to 1.5 A for the Pi Hut NEMA 17 42/60 (1.68 A rated). Start at about half way, raise only if the motor skips, and check the motor temperature (it is enclosed). The firmware cannot set current in this mode.

## Flash from the Mac (Arduino IDE)

1. Install Arduino IDE 2.x. In Boards Manager install **esp32 by Espressif Systems, version 3.x** (the timer calls need 3.x).
2. Open `firmware/spinning_mirror/spinning_mirror.ino`. Board: "ESP32 Dev Module". Pick the USB port.
3. Edit the config block at the top if needed (below), then Upload. If upload stalls at "Connecting...", hold BOOT while it starts.
4. Open Serial Monitor at **115200 baud**, line ending "Newline". You should see "drivers DISABLED".

## Serial commands

One command per line (or separated by `;`). In Max use `[serial]` at 115200 and send a message like `rpm 120` followed by a newline (`10`), or a `[sprintf]` / `[itoa]` chain ending in `10`.

| Command | Effect |
|---|---|
| `enable 1` / `enable 0` | energise drivers (starts from zero, ramps to the target) / release them at once (ring freewheels) |
| `start` | same as `enable 1` |
| `stop` | ramp to zero at the acceleration limit, then release drivers after 300 ms |
| `estop` | release drivers now, clear rpm and jitter |
| `rpm <0..300>` | target speed magnitude (a negative value also sets direction -1) |
| `dir 1` / `dir -1` (`cw` / `ccw`) | direction; a reversal ramps through zero |
| `accel <rad/s2>` | acceleration limit, clamped to 5..300, default 100 |
| `jitter 0` / `jitter 1` | random speed shifts off / on |
| `jrange <lo> <hi>` | jitter speed range in rpm (default 60 to 300) |
| `jtime <min> <max>` | seconds between shifts (default 2 to 8) |
| `status` | one line with all state, easy to parse in Max |
| `help` | list |

Typical first run: `rpm 60`, `enable 1`, then `rpm 120`, `stop`. Boot state is disabled, rpm 0, jitter off. Jitter picks a random target in `jrange` at random intervals; the speed moves there at the acceleration limit, identically for every motor. Manual `rpm` applies when jitter is off.

## Tuning knobs (top of the `.ino`)

- `NUM_MOTORS`: 1 for the 150 mm test rig (default), 2 for the wall piece.
- `STEP_PIN`, `DIR_PIN`, `EN_PIN`: pin map. STEP and DIR must be GPIO 0 to 31.
- `DIR_INVERT[]`: per-motor physical direction. Both wall motors must turn the same way in the room, and they sit at opposite rail ends, so one probably needs inverting. Check with `dir 1` on each motor alone.
- `TIE_STEP_PINS`: 1 drives only GPIO 25 and you wire both drivers' STEP inputs to it.
- `MICROSTEPS` (8) and `FULL_STEPS_PER_REV` (200): must match the driver's MS pins.
- `MAX_RPM` (300), `ACCEL_DEFAULT` (100 rad/s2), `ACCEL_MAX` (300 rad/s2): from the torque budget in the docs. 100 rad/s2 is about 0.06 N m on the wall piece, 300 is about 0.19 N m of roughly 0.25 N m available at 24 V.
- `JITTER_*` defaults, `TICK_HZ` (step timing resolution; the step rate must stay under `TICK_HZ / 2.5`, checked at compile time).

## How lock-step works

One 100 kHz timer interrupt runs a phase accumulator per motor and raises every STEP pin that overflowed with a single GPIO register write. Speed updates for all motors are written inside one critical section, so identical speeds give identical edges on the same tick. The motors stay in step as long as neither skips a step (open loop). The Hall-sensor phase check would catch a skipped step; it is a stub called `phaseCheck()` in `loop()` and is not implemented.

## Unverified, check on first power-up

- Compile: not built. Core 3.x API names (`timerBegin(freq)`, `timerAlarm`, `ARDUINO_ISR_ATTR`) were written from memory.
- Nothing has been run: no step pulses, direction, ramp feel or jitter behaviour observed.
- 10 us step quantisation may make the TMC2209 audibly rougher than a smoothly timed pulse train; raise `TICK_HZ` if so (200 kHz is likely fine).
- Real torque at 300 rpm and 24 V is the docs' estimate, not measured; lower `ACCEL_MAX` or `MAX_RPM` if the motor stalls, and note a stall under open loop is silent.
- Direction on each wall motor, and whether the TMC2209's MS pins give 1/8 on your board, need checking.
- No watchdog: if Max stops sending, the motors keep their last command. Use `stop` / `estop`.
- OSC over WiFi was not requested; serial only.
