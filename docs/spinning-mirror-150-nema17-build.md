# First test unit: 150 mm mirror on a NEMA 17, build guide (2026-11-15)

Draft, nothing built or tested. One unit, no top bar, no hood. CAD: `cad/src/spinning_mirror_150_nema17.py`; STEP and part files in `cad/out/spinning-mirror/spinning-mirror-150-nema17/parts/`; BOM `bom/bom-spinning-mirror-150-nema17.csv`. Background: `spinning-mirror-150-nema17.md`, wiring: `spinning-mirror-150-nema17-wiring-and-order.md`.

**Safety first.** A 169 mm ring spins up to about 2.7 m/s at its edge and the mirror tumbles inside it, with no guard. Clamp or weigh down the base, keep hands, hair, cables and faces clear, wear eye protection, put a switch or the supply plug within reach, and start at low speed. Acrylic is the right choice (it does not shatter like glass), but treat the rig as a machine.

## Parts to print (PETG or ASA, matt black, 0.4 mm nozzle, 0.2 mm layers, 4 walls)
STEP files for slicing: `cad/out/spinning-mirror/spinning-mirror-150-nema17/parts/print_ready/` (Z up, already in the orientation below: ring flat with +Y up, pedestal upside down, hub upright, carrier and lid flat; each file's name is its part name). The same parts, Y-up for Fusion, are in `parts/print/`.
| Part | Orientation | Mass (solid) | Notes |
|---|---|---|---|
| Ring with foot | flat, circular face on the bed (169 x 178 x 12 mm; the bosses are trimmed flush with the ring faces so it lies flat) | 45 g | bearing pockets 9.1 mm and axle holes 5 mm run along the bed: check with a drill after printing; print a test ring section first if unsure |
| Mirror carrier | flat | 27 g | must stay flat |
| Hub adapter | upright | 16 g | 100 % infill, it is the shaft clamp |
| Base pedestal | upside down (top plate on the bed) | 365 g | 150 x 150 x 72 mm, 20 to 25 % gyroid; the four corner posts are full 45 degree wedges, the wire notch and vent slots have pointed tops, so only the four small motor-screw counterbore bridges are left |
| Base lid | flat | 75 g | |
About 0.5 kg of filament in total. PLA is not suitable in sun.

## Parts to buy
The full list with quantities is in the BOM file. Highlights: the 60 mm NEMA 17 (The Pi Hut 42/60), an Adafruit TMC2209 with heatsink, an ESP32 board, a 24 V 3 A supply with jack, fuse and capacitor, two 684ZZ bearings, a 4 mm x 169 mm rod, 150 mm x 1.5 mm mirror acrylic discs (get a spare and a 2 mm sample), a brass slug, about 320 g of steel flat bar for ballast, M3 inserts and screws, thread-lock, CA glue, epoxy and rubber feet.
Tools: soldering iron with an insert tip, M3 hex key, 4 mm and 9 mm drill bits or reamers, small file, callipers, 0.1 g kitchen scale, multimeter, phone for slow-motion video.

## Build
1. **Check the motor on the bench first.** Find the two coils: wires of one coil read about 1.65 ohm, wires from different coils read open. Wire one coil to the driver's 1A/1B and the other to 2A/2B. Confirm the shaft length (24 mm assumed) and the front-face thread depth (M3, usually 4.5 mm). Spin it free with the firmware before anything is attached to it.
2. **Inserts.** Heat-set M3 inserts: four in the corner posts of the pedestal (from the lid side), two in the top of the hub (for the ring screws), two in the hub's side holes (grub screws, one each at +Y and -Y). Keep them square and flush.
3. **Motor into the pedestal.** The motor hangs under the 6 mm top plate with the shaft up through the 22 mm hole; four M3 x 6 screws go down through the counterbored holes into the front face. Seat the pilot boss in the hole. Check the thread depth first; if it is deeper than 5 mm use M3 x 8.
4. **Ballast and feet.** Cut the flat bar into three 60 mm pieces, glue them on the lid either side of the motor (about 320 g), leave the wire notch side clear. Run the motor wires out of the front notch, fit the lid with four M3 x 8, stick the rubber feet under the corners.
5. **Hub on the shaft.** Hub bore on the shaft with the +Y grub screw over the D flat, hub about 3 mm above the plate (use a 3 mm spacer). Thread-lock both grub screws and tighten. The hub top should be flush with the shaft tip.
6. **Ring on the hub.** Press the two 684ZZ bearings into the ring's pockets from the inside, then set the ring foot into the hub's top pocket and fit two M3 x 18 screws from inside the ring, down into the hub inserts (the foot sits 4.5 mm deep in the pocket). Put a drop of thread-lock on the screws; the tumbling mirror loads this joint with a reversing sideways torque. Do this before the carrier goes in.
7. **Carrier and axle.** Glue the brass slug in the carrier's pad (or leave it out for the first run). Place the carrier in the ring, slide the 4 mm rod in through the boss holes, bearings and carrier bore. Centre it so the carrier hubs trap the bearings with about 0.2 mm end float and glue the rod to the carrier with CA or retaining compound. The carrier must turn freely: it should swing like a pendulum and settle flat.
8. **Mirrors.** Glue the discs to the two faces of the carrier (thin CA spots or double-sided tape), film left on until the end.
9. **Balance.** The trim screws are in the four M3 holes (2.6 mm, 6 mm deep) in the +Y face of the ring, at 45, 135, 225 and 315 degrees round the ring on its mid-radius (82 mm from the ring centre). Without power, turn the ring by hand and see whether it stops at the same spot every time (that spot is the heavy side). Screw M3 screws, with washers if needed, into the holes on the light side until it stops anywhere. They correct left-right (in-plane) imbalance, not front-back. Weigh each disc on the scale and aim for identical discs.
10. **Wire up** as in the wiring diagram (`spinning-mirror-150-nema17-wiring.svg`) and the wiring doc: 24 V through the fuse to the TMC2209 + and GND screw terminals (100 uF across, see the wiring doc), ESP32 3.3 V to VIO, STEP and DIR and EN to three ESP32 pins, common ground, USB power for the ESP32.

## Slicer settings, Bambu P1S, matt black PLA (Bambu Studio or Orca)
Nozzle 0.4 mm, textured or smooth PEI plate, filament "Bambu PLA Matte" (or generic PLA). PLA only, so keep the motor cool (see the heat notes above).
| Setting | Value | Why |
|---|---|---|
| Layer height / first layer | 0.20 mm / 0.20 mm | standard; 0.16 mm for the hub if you want a smoother bore |
| Nozzle / bed | 220 C / 55 C | matt PLA; lower the bed to 35 C on the cool plate |
| Part cooling fan | 100 % (aux fan on), chamber door open or lid off | PLA creeps and curls when the chamber is warm |
| Walls | 4 loops (hub 6) | the ring and carrier are mostly walls anyway |
| Top / bottom shell | 5 / 4 layers | the pedestal's top plate holds the motor |
| Infill | gyroid 20 % (pedestal and lid); 30 % (ring, carrier); hub 100 % | hub is the shaft clamp |
| Wall order | inner / outer, precise wall on | dimensional accuracy for the bearing pockets |
| X-Y hole compensation | +0.10 mm | holes print small; tune after the first test print |
| Elephant foot compensation | 0.15 mm | |
| Seam | aligned, back or at a corner | away from the visible faces and bores |
| Supports | none for every part | see below |
| Brim | outer, 5 mm, on the ring and carrier; none on the pedestal and hub | stops thin flat parts lifting at the edges |
| Speed | standard profile; outer wall 60 mm/s | slower outer wall helps hole accuracy |
| Ironing, fuzzy skin, arachne tweaks | off / default | |

Per part
- **Ring:** lay it flat, as in the guide, with the +Y face up so the four trim-screw holes open upward. The two 9.1 mm bearing pockets run horizontally, so their tops sag slightly: do not add support inside them. Ream both pockets with a 9 mm drill or round file until a 684ZZ presses in with light force, and ream the 5 mm axle holes. The M3 foot holes also print horizontally, so ream them to 3.4 mm.
- **Carrier:** flat, brim on. It must stay flat; if it lifts at the rim, raise the bed temperature by 5 C.
- **Hub:** upright, 6 walls or 100 % infill. If the 5 mm bore is tight, ream it to 5.1 mm with a drill by hand.
- **Pedestal:** upside down, top plate on the bed, no supports. The corner posts are full 45 degree wedges and the wire notch and vent slots have pointed tops. Only the four 6.4 mm motor-screw counterbores bridge; if the slicer still adds support there, remove it or paint a support blocker. It takes many hours, so run it overnight.
- **Lid:** flat.
- Print the hub and a short test slice of the ring with a bearing pocket first, and check the fits before the big parts.

## Firmware outline (not written yet)
- **Pulses:** use a library that drives the pins from hardware (FastAccelStepper on the ESP32, or the RMT). 1600 steps per revolution at the board's default 1/8 microstepping (MS1 and MS2 left open; the TMC2209 interpolates internally, so it stays smooth): 60 rpm is 1600 steps/s and 300 rpm is 8000 steps/s.
- **Jitter:** a random walk (Ornstein-Uhlenbeck) on the target speed, updated about 20 times a second: mean 150 rpm, clamp 40 to 280 rpm, correlation time about 1.5 s.
- **Acceleration limit:** start at about 25000 steps/s2 (about 100 rad/s2) and raise it gradually to about 50000. If the motor stalls or squeals, lower it.
- **Safety:** drive EN high (off) at boot, add a ramp to zero on a serial or button stop, and a maximum speed constant.

## Test plan
1. Motor and hub only: speed ramp 30 to 300 rpm, check the hub runs true and the grub screws hold.
2. Ring only (carrier left out): same ramp at 60, 150, 300 rpm. Film the top of the ring in slow motion: more than about 1 mm of wobble means balance or hub fit needs work.
3. Carrier without mirrors: slowly increase jitter and check it tumbles freely.
4. Full unit: start at 60 rpm and low jitter, then raise to the full range. Check the TMC2209 and motor temperature by hand after 10 minutes (warm is fine; too hot to hold means lower the current or add airflow).
5. If it wobbles, add the top pin and bar; the unit has no pin boss yet, so tell me and I will add one.

## Open points
Motor shaft length and thread depth; wire order; whether 1.5 mm acrylic stays flat (2 mm is the fallback); the real balance and hinge friction; stepper hum and resonance rpm; and whether the ring wobbles without a top support.
