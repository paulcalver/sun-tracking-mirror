# Spinning-mirror firmware (ESP32)

**Status: nothing here has been compiled or run on hardware.** It was written from the docs and the ESP32 Arduino core 3.x API. Expect to fix small things on first build, and bench-test with one motor, no ring, before anything is attached.

Sketch: `spinning_mirror/spinning_mirror.ino`. It drives 1 to 3 NEMA 17 steppers through TMC2209 drivers on plain STEP/DIR (no UART), with acceleration-limited speed, a random-speed-shift mode, and USB serial text control for Max/MSP.

## Wiring (Seeed XIAO ESP32-S3)

The board is now the **Seeed XIAO ESP32-S3**, so the pin map differs from the 38-pin ESP32 in `docs/spinning-mirror-150-nema17-wiring-and-order.md` (GPIO 25/26/16/17/19). Why these pins: STEP and DIR must be GPIO 0 to 31 for the fast register write, D6/D7 (GPIO 43/44) are above that, and D2 (GPIO3) is a boot strapping pin, so D2 is left free.

| ESP32 | Goes to | Notes |
|---|---|---|
| D0 (GPIO1) | driver 1 STEP | motor 1 |
| D1 (GPIO2) | driver 1 DIR | |
| D3 (GPIO4) | driver 2 STEP | motor 2 (wall piece) |
| D4 (GPIO5) | driver 2 DIR | |
| D8 / D9 (GPIO7 / 8) | driver 3 STEP / DIR | spare, only if `NUM_MOTORS` is 3 |
| D5 (GPIO6) | EN on every driver | active low; 10k pull-up to 3.3 V so drivers are off at boot |
| 3V3 | each driver's VDD | |
| GND | each driver's GND | common ground with the 24 V supply |
| D10 (GPIO9), D7 (GPIO44) | (Hall sensors) | reserved, not used |

MS1, MS2, DIAG, INDEX, UART and SPRD stay open (1/8 microstepping, StealthChop). 24 V supply to each driver's + and GND, with a 100 uF capacitor at each. The 5 V buck converter feeds the ESP32.

**Driver current:** set with the ILimit potentiometer on each Adafruit TMC2209, about 1.2 to 1.5 A for the Pi Hut NEMA 17 42/60 (1.68 A rated). Start at about half way, raise only if the motor skips, and check the motor temperature (it is enclosed). The firmware cannot set current in this mode.

## Flash from the Mac (Arduino IDE)

1. Install Arduino IDE 2.x. In Boards Manager install **esp32 by Espressif Systems, version 3.x** (the timer calls need 3.x).
2. Open `firmware/spinning_mirror/spinning_mirror.ino`. Board: **XIAO_ESP32S3**. Set Tools > **USB CDC On Boot: Enabled** (otherwise Serial does not show on the USB-C port). Pick the USB port.
3. Edit the config block at the top if needed (below), then Upload. If the port does not appear, hold the XIAO's B (boot) button while plugging it in, then upload.
4. Open Serial Monitor at **115200 baud**, line ending "Newline". You should see "drivers DISABLED".

## Serial commands

One command per line (or separated by `;`). In Max use `[serial]` at 115200 and send a message like `rpm 120` followed by a newline (`10`), or a `[sprintf]` / `[itoa]` chain ending in `10`.

| Command | Effect |
|---|---|
| `enable 1` / `enable 0` | energise drivers (starts from zero, ramps to the target) / release them at once (ring freewheels) |
| `start` | same as `enable 1` |
| `stop` | ramp to zero at the acceleration limit, then release drivers after 300 ms |
| `estop` | release drivers now, clear rpm and jitter |
| `rpm <0..cap>` | target speed magnitude, clamped to `MAX_SPINDLE_RPM` (reply says `CLAMPED`) (a negative value also sets direction -1) |
| `dir 1` / `dir -1` (`cw` / `ccw`) | direction; a reversal ramps through zero |
| `accel <rad/s2>` | acceleration limit, clamped to 5..300, default 100 |
| `jitter 0` / `jitter 1` | random speed shifts off / on |
| `jrange <lo> <hi>` | jitter speed range in rpm (default 60 to 300) |
| `jtime <min> <max>` | seconds between shifts (default 2 to 8) |
| `jmode walk` / `jmode ou` / `jmode kick` | `walk`: random targets in `jrange` at random intervals. `ou`: the tumble simulator's jitter, a random wobble around the `rpm` value. `kick`: sharp bang-bang jumps to the lo or hi end of `jrange` every `jtime` seconds, flipping direction at random if `jrev 1` (the biggest speed changes the acceleration limit allows) |
| `jit <0..0.8>` | ou mode: jitter size as a fraction of `rpm` (simulator slider 45 = 0.45) |
| `jtau <0.02..5>` | ou mode: correlation time in seconds (simulator 0.2); bigger = slower, longer swells |
| `jrev 0` / `jrev 1` | ou mode: 1 lets the speed dip below zero (brief reversals, as in the simulator); 0 holds it at zero or above |
| `status` | one line with all state, easy to parse in Max |
| `help` | list |

Typical first run: `rpm 60`, `enable 1`, then `rpm 120`, `stop`. Boot state is disabled, rpm 0, jitter off. Jitter picks a random target in `jrange` at random intervals; the speed moves there at the acceleration limit, identically for every motor. Manual `rpm` applies when jitter is off.

## Tuning knobs (top of the `.ino`)

- `NUM_MOTORS`: 1 for the 150 mm test rig (default), 2 for the wall piece.
- `STEP_PIN`, `DIR_PIN`, `EN_PIN`: pin map. STEP and DIR must be GPIO 0 to 31 (see the XIAO note above).
- `DIR_INVERT[]`: per-motor physical direction. Both wall motors must turn the same way in the room, and they sit at opposite rail ends, so one probably needs inverting. Check with `dir 1` on each motor alone.
- `TIE_STEP_PINS`: 1 drives only D0 (GPIO1) and you wire both drivers' STEP inputs to it.
- `MICROSTEPS` (8) and `FULL_STEPS_PER_REV` (200): must match the driver's MS pins.
- `MAX_SPINDLE_RPM` (300): hard speed cap in spindle rpm, converted with the actual steps/rev, microstepping and `PULLEY_RATIO` (1.0). Every path is held to it: ramp target, jitter picks, `rpm`/`jrange` commands (clamped, and the reply says `CLAMPED`) and a final clamp before the step-rate conversion; all motors share the one capped value. It is printed at boot. Keep it below the speed the bench test has proved (a mirror letting go is about 1 J at 600 rpm, 3 J at 1000 rpm).
- `ACCEL_DEFAULT` (100 rad/s2), `ACCEL_MAX` (300 rad/s2, acceleration is always limited by the ramp and `accel` is clamped to this): from the torque budget in the docs. 100 rad/s2 is about 0.06 N m on the wall piece, 300 is about 0.19 N m of roughly 0.25 N m available at 24 V.
- `JITTER_*` defaults, `TICK_HZ` (step timing resolution; the step rate must stay under `TICK_HZ / 2.5`, checked at compile time).

## How lock-step works

One 100 kHz timer interrupt runs a phase accumulator per motor and raises every STEP pin that overflowed with a single GPIO register write. Speed updates for all motors are written inside one critical section, so identical speeds give identical edges on the same tick. The motors stay in step as long as neither skips a step (open loop). The Hall-sensor phase check would catch a skipped step; it is a stub called `phaseCheck()` in `loop()` and is not implemented.

## Unverified, check on first power-up

- Compile: not built. Core 3.x API names (`timerBegin(freq)`, `timerAlarm`, `ARDUINO_ISR_ATTR`) were written from memory.
- Nothing has been run: no step pulses, direction, ramp feel or jitter behaviour observed.
- 10 us step quantisation may make the TMC2209 audibly rougher than a smoothly timed pulse train; raise `TICK_HZ` if so (200 kHz is likely fine).
- Real torque at 300 rpm and 24 V is the docs' estimate, not measured; lower `ACCEL_MAX` or `MAX_SPINDLE_RPM` if the motor stalls, and note a stall under open loop is silent.
- Direction on each wall motor, and whether the TMC2209's MS pins give 1/8 on your board, need checking.
- No watchdog: if Max stops sending, the motors keep their last command. Use `stop` / `estop`.
- OSC over WiFi was not requested; serial only.

## 150 mm single test unit and the tumble simulator

`NUM_MOTORS 1` is the default, so the sketch is already the single-rig build. The `ou` jitter mode reproduces the speed process in `sim/spinning-mirror/spinning-mirror-gimbal-concept.html` (option D): speed = `rpm` x (1 + ou), ou an Ornstein-Uhlenbeck process with standard deviation `jit` and correlation time `jtau`. The simulator's mechanical sliders (hinge friction, edge weight) are properties of the real hinge, not firmware.

Try on the rig, all changeable while it runs:

```
rpm 180
jmode ou
jit 0.45
jtau 0.2
accel 200
enable 1
jitter 1
```

Notes:
- At `rpm 180`, `jit 0.45` the peaks exceed 300 rpm; those are clamped by `MAX_SPINDLE_RPM`, which flattens the tops. Lower `rpm` or `jit`, or raise the cap only after the bench test.
- That wobble asks for roughly 60 rad/s2 rms with peaks over 150, so the default 100 rad/s2 limit will round it off. A 150 mm mirror and ring are about 3.4e-4 to 4.8e-4 kg m2 (docs), so 200 rad/s2 is about 0.1 N m, within the motor's budget but start at 100 and raise `accel` live.
- The simulator runs slowed (time scale 0.08). The firmware runs in real time, so `jtau 0.2` is 0.2 real seconds.
- With `jrev 1` the ring reverses through zero speed at the acceleration limit; stepper torque there is fine, but watch the mirror mount.

## Laptop control panel (`ui/spinning_mirror_control.html`)

A single HTML page that talks to the ESP32 over USB serial using the browser's Web Serial API, so there is nothing to install.

1. Flash the sketch, close the Arduino Serial Monitor and Max (only one program can hold the port).
2. Open `firmware/ui/spinning_mirror_control.html` in **Chrome or Edge** (Safari and Firefox have no Web Serial). If it will not connect from a `file://` address, run `python3 -m http.server 8000` in `firmware/ui` and open `http://localhost:8000/spinning_mirror_control.html`.
3. Click Connect and pick the ESP32's port. Opening the port resets the ESP32; the drivers stay off until you press Start.

It has Start, Stop (ramp down) and Emergency stop buttons, sliders for speed, acceleration, jitter size, correlation time, range and interval, direction and reversal switches, a 20 s live speed plot from the firmware's `status` line, and a raw command box. Sliders send their commands as you drag them, and the controls take the firmware's current values on connect. The speed sliders' maximum follows the firmware cap, which is read from the boot line. The page cannot raise the cap; the firmware always clamps.

Tuning features: nine built-in presets (swing, tumble, wild, fast wobble, slow wobble that crosses zero, slow and big kicks, random targets), a **Randomise** button, **Copy as one line** (paste into the Arduino Serial Monitor), and a **Settings that work** section: save the current settings with a name and a note, then Apply, Copy line or Delete each one, plus Copy all as text and Download or Load a file to back them up. All three jitter modes (wobble, random targets, sharp kicks) have sliders, including the reversal switch.

Unverified: only the page's status parsing and layout were checked in a browser pane with fake status lines; the serial connection itself has not been tried.

## Wiring diagram for the 150 mm test unit

`electronics/spinning-mirrors/150mm-test-unit/wiring.svg` (open it in a browser). It matches this firmware's default pins. As a checklist:

| From | To |
|---|---|
| 24 V supply + | DC jack breakout + , through a 3 A fuse, to the driver's + terminal (100 uF 35 V+ capacitor across + and GND at the terminal) |
| 24 V supply - | driver GND terminal |
| ESP32 GND | driver GND (logic pin) and the supply ground: all grounds joined |
| ESP32 3V3 | driver VDD |
| XIAO D0 (GPIO1) | driver STEP |
| XIAO D1 (GPIO2) | driver DIR |
| XIAO D5 (GPIO6) | driver EN, with a 10k pull-up from EN to 3V3 |
| Motor coil A (one wire pair, about 1.65 ohm) | driver 1A / 1B |
| Motor coil B (the other pair) | driver 2A / 2B |
| ESP32 USB | the laptop (5 V power and programming) |
| (later) dial wiper | D10 (GPIO9, an ADC pin); dial ends to 3V3 and GND |

Leave MS1, MS2, DIAG, INDEX, UART and SPRD open. Set the driver current pot to about half way (1.2 to 1.5 A). Never unplug the motor with 24 V on.

## Wiring the 100 mm wall piece (two motors)

Diagram: `electronics/spinning-mirrors/wall-row-100/wiring.svg`. Set `NUM_MOTORS 2` in the sketch. **No pin changes** were needed: motor 1 uses STEP 25, DIR 16; motor 2 uses STEP 26, DIR 17; EN 19 is shared.

Layout in the box: both TMC2209s and the ESP32 on one 70 x 90 mm perfboard. Left end wall: DC jack with its lead, and motor 1's lead (motor 1 is at the left end of the rail, mirrors 1 to 4). Right end wall: USB-C panel cable, and motor 2's lead (right end, mirrors 5 to 8). Power chain: 24 V bench supply, DC jack, 5 A fuse in the +24 V lead, Wago +24 V and GND blocks, then each driver's + and GND terminals with a 100 uF 35 V+ capacitor across them.

**Lock-step, and what is shared**
- STEP and DIR are on separate ESP32 pins, one pair per driver, not one shared wire. The firmware writes both STEP pins in one register write from one timer, so the edges are identical (set `TIE_STEP_PINS 1` and join both STEP inputs to GPIO 25 if you would rather have one physical wire). DIR is kept separate so a motor mounted at the opposite end can be reversed in firmware (`DIR_INVERT`) instead of re-soldering; check on the bench that both rings turn the same way in the room.
- EN is shared on D5 (GPIO6) with one 10k pull-up to 3V3: both drivers must start, stop and fail off together, and a single pull-up keeps both off while the ESP32 boots.
- MS1 and MS2 are left open on both drivers, so both run 1/8 step. They are not wired to the ESP32. If you ever change one, change both, or the motors will run at different speeds.
- All grounds join: ESP32 GND to each driver's logic GND, supply GND to each driver's power GND.

**Open points, answered**
- **Wire gauge:** 22 AWG for 24 V and GND (the 5 A fuse protects it, and the real draw is about 2 A with both motors at 1.2 to 1.5 A). 26 AWG for STEP, DIR, EN and 3V3. Keep the 3V3 and GND logic runs short and twisted with the signal where you can.
- **Motor lead connector:** the Pi Hut's motor has a short cable with a small plug (listed as 4-pin, 2.54 mm pitch; check the listing photo and your cable before ordering). Plug the 0.5 m extension onto the motor, strip the other end and clamp it in the driver's screw terminal with ferrules (Adafruit's TMC2209 motor terminals are screws). That way no connector has to pass through the 14 mm grommet holes. Extension wire order may not match the driver, so find the two coil pairs with a multimeter (about 1.65 ohm within a pair, open between pairs) before connecting.
- **Hall sensor:** left out of the build. D10 (GPIO9, half 1) and D7 (GPIO44, half 2) are reserved. These GPIOs have internal pull-ups, but add 10k to 3V3 if the sensor is open-collector. The firmware has only an empty `phaseCheck()` hook.
- **Power-up order:** (1) with everything off, check coil pairs, wiring and that no wire touches another; (2) set the bench supply to 24 V with the current limit at 3 A, output off; (3) plug in USB so the ESP32 boots with drivers disabled; (4) switch the 24 V output on; (5) `enable 1`, then bring `rpm` up. Power down with `stop`, wait for the ring to stop, switch the 24 V off, then unplug USB.
- **Bench supply cautions:** do not cut the 24 V while the rings are spinning, and do not rely on a supply with no current sink to absorb regenerated energy; use `stop` first. A current limit set too low makes the rail sag on acceleration peaks and the motors skip steps silently. Never hot-plug a motor with 24 V on. Power the ESP32 from USB only (no buck, and never both). If the laptop and bench supply both have earth, the USB ground and 24 V negative are joined by the driver boards; if you hear mains hum or the USB drops out, power the laptop from its battery or add a USB isolator.

Nothing here is built or tested; check every pin label on the actual boards before wiring.

## Remote dial (two pots, wireless)

A second ESP32 with two 10k linear pots sends their positions to the main unit over ESP-NOW (the built-in radio; no router, no pairing). Sketch: `remote_dial/remote_dial.ino`. Diagram: `electronics/spinning-mirrors/remote-dial/wiring.svg`. Planned range: under 3 m with USB power at the dial.

| Remote ESP32 | Goes to |
|---|---|
| 3V3 / GND | both pots' outer ends |
| XIAO A0 (GPIO1) | SPEED pot wiper |
| XIAO A1 (GPIO2) | JITTER pot wiper |
| USB | power bank or wall adapter |

Parts: a second XIAO ESP32-S3 (or any ESP32 with the two `SPEED_PIN`/`JITTER_PIN` numbers changed), two 10k linear (B) pots with knobs, an enclosure, optionally 2 x 100 nF capacitors, a USB cable and power source.

- **Flash:** open `remote_dial/remote_dial.ino` the same way as the main sketch (esp32 core 3.x). The main sketch has `ENABLE_REMOTE_DIAL 1` by default and needs no wiring; both units use WiFi channel 1 and the same `REMOTE_KEY`.
- **Mapping:** the speed pot gives 0 to `REMOTE_RPM_MAX` (200 rpm, bottom 4 % = zero, always under the speed cap); the jitter pot gives wobble size 0 to `REMOTE_JIT_MAX` (0.8). Moving the jitter pot switches the main unit to `ou` jitter mode and turns jitter on.
- **Takes over only when moved:** each pot is ignored until it has moved about 4 % from its reading when the main unit first heard it. Switching the remote on never changes a running setting, and serial or the laptop panel can still set values; a dial change then overrides them. `remote 0` makes the main unit ignore the dial, `remote 1` re-baselines it. `status` shows `remote`, `remote_seen` and `remote_age_ms` (milliseconds since the last packet).
- **Does not start the motors:** drivers are still enabled from serial or the panel. Set `REMOTE_CAN_ENABLE 1` in the main sketch for a standalone installation: the speed dial above zero then enables the drivers and turning it to zero does a `stop`.
- **Link loss:** the main unit keeps the last setting. Safe limits (speed cap, acceleration cap) apply to everything the dial can ask for.
- **Pin note:** the dial's pots sit on the remote board only, so there is no pin conflict with the main unit.
- **Not secure:** broadcast ESP-NOW is not encrypted and the key is a constant, so anyone nearby who knew it could send values. The caps still bound what they could do. Unicast with encryption would need the main unit's MAC address.

Unverified: both sketches compile for the XIAO ESP32-S3 (core 3.3.x) but neither has run on hardware; range and pot noise untested.

### Desk remote controller (enclosure, stop/go button, LED, LiPo)

The remote is now a printed desk wedge: `cad/src/spinning_mirror_remote.py` (previews in `cad/media/previews/spinning-mirror-remote/`), parts in `bom/spinning-mirrors/bom-spinning-mirror-remote.csv`, wiring in `electronics/spinning-mirrors/remote-dial/wiring.svg`. 120 x 76 mm, 15 degree panel, two 36 mm knobs, a 16 mm latching STOP/GO switch with an LED ring (also the SEND light), USB-C in the back wall for charging and programming, a slide switch that breaks the LiPo lead.

| XIAO ESP32-S3 | Goes to |
|---|---|
| A0 (GPIO1) | SPEED pot wiper (outer ends on 3V3 and GND) |
| A1 (GPIO2) | JITTER pot wiper |
| A2 (GPIO3) | middle of two 100k resistors from BAT+ to GND (battery level; optional, `BATT_SENSE 0` if left out) |
| D3 (GPIO4) | STOP/GO switch: common to GND, normally-open to the pin (internal pull-up) |
| D4 (GPIO5) | 330 ohm, then the LED ring +; ring - to GND |
| BAT+ / BAT- pads (underside) | LiPo through the slide switch in the + lead |

- **Stop/go needs no change to the main sketch.** The packet format is unchanged (key 0x5A3C, version 1, 8 bytes). The switch is latching: off sends speed 0 (`LATCHING_SWITCH 0` makes a momentary button toggle instead), which the main sketch already treats as 0 rpm; GO ramps back up to the dial over about 2 s. The drivers stay enabled (holding torque) unless `REMOTE_CAN_ENABLE 1`, which also disables them at 0 rpm. A hard stop that always disables the drivers would need a spare bit in the packet and a handler in the main sketch (not requested).
- **LED:** one blink a second = running, steady dim = stopped, 5 Hz flicker = battery below 3.5 V or the radio failed to start. It shows that this unit is sending. ESP-NOW broadcast has no acknowledgement, so it cannot show that the main unit hears it; `status` on the main unit (`remote_age_ms`) is the check for that.
- **Charging:** the XIAO charges the cell from USB-C at about 100 mA by default, so a 1000 mAh cell takes around 10 hours; the radio draws roughly 80 to 120 mA, so expect 6 to 10 hours per charge (estimate). Switch off to save the cell; USB also powers the unit with the switch on.
- **Compiled, not run on hardware:** `arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:CDCOnBoot=cdc firmware/remote_dial` builds. Not tested: pot and ADC readings, the button, LED patterns, range, battery life, charging, the printed case fit (USB-C cutout, switch cutout, pot and button hole sizes, screw posts).

## Solderable breadboard layout (wall piece)

`electronics/spinning-mirrors/wall-row-100/breadboard-layout.svg` shows the two-motor build on a half-size solderable breadboard with the XIAO ESP32-S3: a wire list by column and row, what stays off the board (24 V and the motor leads go straight to each driver's screw terminals), and a check list. Its dimensions, the driver header order and the XIAO orientation are drawn from the docs and the Seeed pin chart and were not measured on real parts.
