# Wave version, print-in-place redesign (concept CAD, 2026-11-12)

Status: concept model. Nothing printed, built or tested; the printed-joint clearances are unproven. Source: `cad/src/line_wave_pip.py` (CadQuery, reuses helpers from `line_mirrors.py`). STEP: `cad/out/earlier-concepts/line-mirrors/line-mirrors-wave-pip.step` (`--step`). Renders: `cad/media/previews/line-mirrors/pip-*.png` (`--render`). Checks: `--check`, `--sun`. The earlier design is unchanged in [line-mirrors-wave-full.md](line-mirrors-wave-full.md).

Same brief: 7 x 50 mm mirrors at 70 mm pitch, +/-25 deg cone, pan + tilt + travelling wave, 3 steppers. Printer assumed: Bambu P1S, 0.4 mm nozzle, AMS (support-interface material).

## The idea
The earlier design slides things (pan bar in rails, tilt frame on two belts) and builds each mirror joint from a drilled ball, a jig, epoxy, a tab, a spring and a retainer. This one only rotates things, and each mirror is one print.

- **Cartridge (one print, x7):** pedestal + pan frame + carrier, printed together with captive joints.
  - The pan frame's 8 mm vertical journal passes through the pedestal block. Its crank is printed above the block and its fork below, so it cannot come out and could not be assembled from separate parts.
  - The carrier's axle is captive between the fork cheeks on two 5 mm trunnions. A spigot goes forward through a 22 mm hole in the front plate to the mirror disc. A 3 mm steel pin (the tail) is pressed in, pointing down and back.
  - Bores are diamonds (a square turned 45 deg), 0.25 mm clear per side. A journal sits in one corner on two lines.
- **No springs.** The mirror is front-heavy. Gravity seats each journal in its corner and presses the tail on its cam (about 0.2 to 0.3 N), so joint play does not reach the mirror angle. This only works wall-mounted, the right way up.
- **Pan:** seven cranks (16 mm) and an identical crank on a vertical NEMA 17 are joined by one tie bar. A parallelogram: mirror pan = motor angle, no slides, no belt.
- **Tilt:** a 5 mm cradle shaft sits directly on a NEMA 17 (rigid coupler, no belt or gears). Four arms on it carry the camshaft 16.5 mm away. Turning the cradle +/-41 deg swings the cams and tilts all mirrors +/-25 deg.
- **Wave:** seven eccentric drums (10 mm, 0.75 mm throw, 60 deg steps) on the camshaft, turned by a 28BYJ-48 on the left arm. Each tail rests on its drum.
- **Trim:** each mirror disc clamps on a 9 mm ball at the spigot end (one M2 screw), so each mirror can be aimed once by hand.

Strip: 730 x 96 x 52.5 mm (was 824 x 96 x 62). Glass front 74 mm from the wall (was about 90). Pivot plane 40 mm from the wall.

## Compared with the full-detail wave model
| | Earlier | This one |
|---|---|---|
| Parts in the model | 240+ and 130 fasteners | 76 (fasteners not drawn, about 40 expected) |
| Belts, pulleys, idlers | 4 belts, 8 pulleys | none |
| Springs and flexure pads | 7 + 14 | none |
| Per-mirror assembly | ball drilled, jigged, epoxied; tab, spring, retainer | glue glass, press in pin, 2 screws |
| Tilt frame | 0.5 kg lifted, drops if unpowered | about 0.1 kg cradle, near balance |
| Sliding guides | pan rails, PTFE skids, comb | none |

## Checks
- `--check`: 24 poses (cone 0, 12 and 25 deg in 8 directions, cam angle varied), 76 parts: **0 clashes**. Mirror disc stays at least 1.1 mm above the front plate.
- `--sun`: enclosure blocks 0.0 % of rays at 25, 50 and 65 deg. Other mirrors block 0 % up to 50 deg and 5.7 % at 65 deg.
- Pan and tilt are coupled a little (the tail swings sideways over its drum when panning). It is the same for all mirrors, so `solve()` in the script gives the cradle angle for any pan and tilt; firmware needs the same formula.

## Known trade-offs
- **Wave size changes with tilt.** The cradle cannot share the mirrors' axis, so the tail's lever runs from 30 mm to 16.5 mm:

| Tilt (deg) | Lever (mm) | Wave (deg) | Spot swing at 3 m (mm) |
|---|---|---|---|
| -25 | 30.4 | +/-1.40 | +/-147 |
| 0 | 24.5 | +/-1.72 | +/-180 |
| +25 | 16.5 | +/-2.49 | +/-262 |

- **Resolution.** Direct drive at 1/16 microstep is 0.11 deg of pan and about 0.07 deg of tilt per step (about 12 and 7 mm of spot at 3 m). The error is common to all mirrors, so the line stays straight; it only moves as a whole. Use 1/64 if steps show.
- **Sensitivity.** 0.1 mm of error at a crank pin is 0.36 deg of pan; 0.1 mm of drum run-out is about 0.25 deg of tilt. The trim ball is there for this.
- **Tilt motor must stay powered** (holding current). Load is small, about 2 N cm.

## Printing notes (to test, not proven)
- Test files (`--print`): `cad/out/earlier-concepts/line-mirrors/print/pip-cartridge-test.step` and `.stl` (pedestal, pan frame and carrier as three bodies in one file, crank side down, 34 x 65.5 x 40.7 mm) and `pip-mirror-disc.step` and `.stl` (glass face down). Import the cartridge as one object; do not let the slicer split or re-arrange the bodies.
- The tail pin presses into a 3 mm hole in a boss on the carrier, 8 mm deep. Ream or drill it to size after printing.
- Print the cartridge upside down (crank on the bed), PETG or ASA, 0.2 mm layers, with support-interface material from the AMS under the pedestal column, the carrier and the spigot.
- Print one cartridge first. If the joints fuse, raise `CLR` (0.25) in the script; if they rattle, the diamond bores should still seat them.
- Drums and arms need a D bore or grub screw on the 5 mm shafts (not drawn).

## Not drawn
Fasteners, the trim clamp screw and socket slit, sprung (slit) holes in the tie bar, 28BYJ mounting ears and cable loop, home switches (or TMC2209 stall homing), wiring.

## Bill of materials (rough, unchecked prices)
**3D printed:** 7 cartridges, 7 mirror discs, 7 cam drums, 4 cradle arms, 4 cradle shaft blocks, 2 motor mounts, pan motor crank, cam motor plate.

**Laser cut:** back plate 730 x 96, front plate 730 x 96 with 7 x 22 mm holes, top and bottom walls, 2 end walls (3 mm acrylic or ply); pan tie bar 515 x 10 x 3 with a dog-leg (acetal). Parts over 600 mm still need a large bed or a split.

| Qty | Bought item | Est. GBP |
|---|---|---|
| 2 | NEMA 17 stepper 42 x 34, 5 mm D shaft (pan, tilt) | 22 |
| 1 | 28BYJ-48 geared stepper (cam) | 3 |
| 3 | TMC2209 driver | 15 |
| 1 | Raspberry Pi Pico | 5 |
| 1 | DS3231 clock module | 4 |
| 1 | 12 V 2 A adapter, DC jack, 5 V buck converter | 13 |
| 1 | 5 mm silver steel, 1 m (cradle shaft 490, camshaft 478) | 6 |
| 2 | Rigid coupler 5 to 5 mm | 6 |
| 7 | Steel dowel pin 3 x 32 mm (tails) | 3 |
| 7 | Mirror disc 50 mm, 3 mm glass | 14 |
| - | M3 and M2 screws, glue, wall fixings, cable | 20 |

About 110 GBP (earlier design: about 191).
