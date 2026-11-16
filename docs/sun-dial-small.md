# Smallest sun dial, 100 mm discs, no slip ring (2026-11-16)

The smallest version of the single dial: a deep 120 mm square frame holds two flush 100 mm discs on one GM2804, standing on a 140 mm round base that turns it to the azimuth. Draft CAD, nothing printed, cut or tested. Source of truth: `cad/src/sun_dial_small.py` (CadQuery). The larger 150 mm version with the slip ring is `cad/src/sun_dial_one.py` and `docs/sun-dial-one.md`.

## What it is
- **Size:** base 140 mm across and 34 mm tall, frame 120 x 120 x 44 mm, overall about 158 mm tall.
- **Frame and discs:** 3 mm black acrylic frame with a 102 mm window in each face; two 100 mm white acrylic discs flush in the windows, each with a radial slot and a black strip. Same arrangement as the larger version: one GM2804 between the discs, disc 1 on the rotor through a printed adapter, disc 2 on two 3 mm steel posts and a 6 mm centring pin, a fixed arm and bracket on the motor back, a tray carrying the XIAO RP2040 and the SimpleFOC Mini.
- **Azimuth:** a second GM2804 stands upright on the base axis. Its rotor carries the turntable through a printed adapter flange, so there is no belt, tube, bearings or slip ring.
- **Cable:** four thin wires (12 V, 5 V, ground, serial) leave the frame through a 10 mm hole in the turntable at 30 mm from the axis and wind round a fixed printed spool beside the motor, then go through a slot to the boards. Azimuth travel is about +/-150 degrees round south, which covers the Sun, Moon and planets from the UK because they never cross north. Firmware must unwind through south and never cross north.
- **Base boards (keep-outs):** XIAO ESP32-S3, the azimuth SimpleFOC Mini, compass, clock, USB-C PD board with its socket at the back rim (slot in the wall), buck converter.
- **Pose:** `--az` is the compass bearing the line points at (90 = along +X); `--el` is the elevation.

## Checks run
- `python3 cad/src/sun_dial_small.py --check`: 0 clashes at four az/el pairs including el +/-90, 0 static clashes. The frame corners swing 63.9 mm from the axis, inside the 69 mm turntable.
- Not checked: cable winding length and fatigue, compass interference, printability, strength, motor and turntable alignment, wobble of the disc on the posts.

## Things to know or decide
1. **Compass distance.** The compass is only about 58 mm from the azimuth motor, which now sits on the axis. I could not check how much its magnets disturb the compass; it needs a test, and calibration in place.
2. **Cable.** The spool and slot are a first idea; the winding length, strain relief and a hard stop (soft stop in firmware as well) still need designing.
3. **Rotor cap is 1.5 mm thick.** Both motor adapters screw into a thin cap, so use short screws with thread-lock.
4. **Pin in the bore.** A 6 mm pin in a 6.5 mm bore will rub on bare metal; a bush may be needed.
5. **Board sizes** other than the SimpleFOC Mini and the GM2804 are placeholders. The XIAO ESP32-S3 uses all 11 header pins (the SimpleFOC enable must be tied high).
6. **Not modelled:** fasteners, heat-set inserts, wiring, board standoffs, motor mounting screws into the base floor.
7. **Previews:** the matplotlib renders sort faces roughly, so thin parts can show through. Open the STEP for a proper look.

## Regenerating
```
python3 cad/src/sun_dial_small.py            # STEP, parts, DXF, BOM, previews (add --az 135 --el 30 to pose)
python3 cad/src/sun_dial_small.py --check
```
Outputs: `cad/out/sun-dial-small/`, `bom/bom-sun-dial-small.csv`, `cad/media/previews/sun-dial-small/`.
