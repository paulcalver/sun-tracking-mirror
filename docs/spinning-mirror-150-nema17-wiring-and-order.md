# 150 mm NEMA 17 trio: wiring and order list (2026-11-15)

Draft, nothing built or tested. Check every board's pinout against its own page before wiring.

## How it links up
```
24 V 5 A supply -> panel DC jack -> inline 5 A fuse -> 24 V / GND lever connectors (Wago 221)
   |-> TMC2209 x3: + and GND screw terminals, each with a 100 uF 35 V+ capacitor at the terminal
   |-> 5 V buck converter -> ESP32 5V pin (and GND)
ESP32 3.3 V -> TMC2209 VDD (x3).  Common GND between ESP32, drivers and supply.
ESP32 GPIO -> TMC2209 STEP, DIR, EN (one set per driver)
TMC2209 2A/2B/1A/1B -> NEMA 17 (one coil pair on each A, B pair)
Dial: 3.3 V, GND, wiper -> ESP32 ADC pin.   USB-C panel cable -> ESP32 USB port.
```
- **Coil pairs:** the four motor wires are two coils. Measure with a multimeter: the two wires of one coil read about 1.65 ohm, wires from different coils read open. One coil goes to 1A/1B and the other to 2A/2B. Swapping a coil's two wires only reverses the direction. Never unplug a motor while the supply is on.
- **Suggested ESP32 pins** (avoid the boot-strapping pins 0, 2, 5, 12, 15): STEP 25, 26, 27; DIR 16, 17, 18; EN 19 (shared by all three, with a 10k pull-up to 3.3 V so the drivers stay off at boot); dial on 34 (input only, ADC). Match these to the pin names on your ESP32 board.
- **Alternative controller, Adafruit QT Py ESP32-S3:** it works. It breaks out 11 GPIOs (A0 to A3, SDA, SCL, TX, RX, SCK, MISO, MOSI) and the job needs 8 (3 STEP, 3 DIR, EN, dial), or 10 if you also wire the TMC2209 UART on TX and RX. Its RMT has 4 transmit channels, enough for 3 step streams. Suggested: STEP on MOSI, MISO, SCK; DIR on A0, A1, A2; EN on SDA with a 10k pull-up to 3.3 V; dial on A3. It has no screw terminals, so solder wires or headers to the pads; feed 5 V from the buck converter to its 5V pad (check Adafruit's pinout page that the pad accepts input) and take 3.3 V from its 3V pad for the drivers' VIO. No spare pins for extras.
- **Step rate:** 300 rpm at the default 1/8 microstepping (MS1 and MS2 open) is about 8 kHz per motor; use the RMT or hardware timers, not a software loop.
- **Driver settings:** current 1.2 to 1.5 A per motor, set with the small potentiometer on the board (fully clockwise is 2 A; start at about half way and raise it only if the motor skips, checking its temperature); MS1 and MS2 left open = 1/8 microstepping, which is fine (the chip interpolates); the SPRD jumper stays open for quiet StealthChop; EN is active low (high disables the outputs); DIAG, INDEX and UART are not used. The board's VDD pin takes the 3.3 V logic supply.
- **Board layout (from Adafruit's photo):** screw terminals left to right: +, -, 2B, 2A, 1A, 1B (coil pairs 2B/2A and 1A/1B). Logic header left to right: VDD, GND, DIR, STEP, MS1, MS2, DIAG, INDEX, UART, EN. ILimit potentiometer 0 to 2 A at the top right; SPRD jumper pad (leave open). The board has its own 22 uF 35 V capacitor next to the + and - terminals.
- **Capacitor (add 100 uF 35 V+ as well):** the board's power input is a screw-terminal block in line with the motor outputs (+, GND, 1A, 1B, 2A, 2B). Solder the capacitor's legs (long leg to +, striped leg to GND) onto the ends of the +24 V and ground wires, so each pair becomes one joint, and clamp each joint in its terminal with a ferrule. Keep the legs about 10 mm long, with heat shrink on each, and glue the can down. Or solder the legs straight onto the terminal block's pins on the back of the board if you prefer.
- **UART (optional):** wire each driver's UART pin to the ESP32 only if you want to set current and microstepping from firmware.

## Connectors and wire
- **Motor end:** the motor's short cable has a small plug; check the listing photos for the type (4-pin, 2.54 mm pitch). The other end is whatever the driver needs: the Adafruit TMC2209 has a 4-way motor output (headers or screw terminals depending on the board). Buy a 4-pin 2.54 mm extension cable or crimp/solder your own if the lead is too short to reach a driver (up to about 200 mm).
- **Driver:** solder 0.1 inch headers if the board comes without them, and plug the drivers into a small perfboard or a screw-terminal carrier.
- **ESP32:** use a 38-pin dev board on a screw-terminal breakout board so there is no soldering to the board and no loose jumper wires.
- **Power:** 22 AWG silicone wire (red/black) for 24 V and the motors; 26 to 28 AWG for logic. Ferrules on every screw-terminal end.
- **Panel parts:** panel-mount 5.5 x 2.1 mm DC jack (12 mm hole), USB-C panel-mount extension cable (11 x 4.6 mm slot), 10k potentiometer with a knob (7.5 mm hole).

## Order list
Electronics
| Qty | Part | Notes |
|---|---|---|
| 3 (+0 spare) | NEMA 17 stepper 42/60 (The Pi Hut, 60 mm body) | 1.68 A, 0.64 N m, short cable |
| 3 (+1 spare) | Adafruit TMC2209 stepper driver breakout | 24 V, set 1.2 to 1.5 A; heatsink each |
| 1 | ESP32 dev board (38-pin) and screw-terminal breakout | |
| 1 | 24 V 5 A DC supply, 5.5 x 2.1 mm plug | 3 motors at 1.2 to 1.5 A |
| 1 | 5 V buck converter, 1 A or more (e.g. a 24 V input module) | powers the ESP32 |
| 1 | Panel-mount DC jack 5.5 x 2.1 mm, with leads | |
| 1 | Inline fuse holder and 5 A fuses | |
| 3 (+1) | Electrolytic capacitor 100 uF, 35 V or 50 V | one per driver, at the + and GND screw terminals |
| 3 | Heatsink for TMC2209 | if not on the board |
| 1 | USB-C panel-mount extension cable | for programming |
| 1 | 10k potentiometer and 20 mm knob | jitter amount, optional |
| 1 | Lever connectors, 5-way (Wago 221-415), 3 pcs | 24 V and GND distribution |
| 1 | 4-pin 2.54 mm extension cables or crimp kit | motor leads |
| 1 set | Silicone wire 22 AWG red/black, 26 AWG logic, ferrules, heat shrink, cable ties | |
| 1 set | M3 standoffs and screws for the boards, foam tape | |

Mechanical
| Qty | Part | Notes |
|---|---|---|
| 6 | Bearing 684ZZ (4 x 9 x 4) | 2 per unit |
| 3 | Steel or stainless rod 4 mm x 169 mm | hinge axles |
| 6 | Acrylic mirror 1.5 mm, 150 mm discs | 2 per unit; get a sample first |
| 3 | Brass slug 8 x 5 mm | weight |
| 2 | Steel flat bar 38 x 6 x 500 mm | ballast, about 0.9 kg each |
| 1 set | Heat-set inserts M3 x 5 (12) and screws: M3 x 10 (12), M3 x 18 (6), M3 x 5 grub (6), M3 x 6 (12), M3 x 20 wood screws (3) | thread-lock the grub screws |
| 4 | Rubber feet 12 mm | |
| 1 | PETG or ASA filament, matt black | about 1 kg |
| 1 | Plywood 6 mm sheet, about 1 x 0.7 m | laser-cut, DXF in `cad/out/spinning-mirror-150-nema17-trio/parts/laser/` |
| 1 | Wood glue, CA glue or retaining compound | |
