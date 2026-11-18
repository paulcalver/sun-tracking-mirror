# Smallest sun dial, 100 mm discs, no slip ring, all printed (2026-11-16)

The smallest version of the single dial: a deep 120 mm square frame holds two flush 100 mm discs on one GM2804, standing on a 140 mm round base that turns it to the azimuth. Draft CAD, nothing printed or tested. Source of truth: `cad/src/sun_dial_small.py` (CadQuery). The larger 150 mm version with the slip ring and laser-cut frame is `cad/src/sun_dial_one.py` and `docs/sun-dial-one.md`.

## What it is
- **Size:** base 140 mm across and 34 mm tall, frame 120 x 120 x 44 mm, overall about 160 mm tall.
- **Discs:** two 100 mm white discs printed in one job each, black line as a 0.6 mm inlay (3 mm wide, in the first layers) on the outer face, printed outer face down so the line is flush and glossy or textured like the plate. The back disc has hub 2 (the T-plate for the posts and pin) printed on as one piece. `--discs laser` gives the laser-cut version (through slot and a pressed strip) instead.
- **Frame in three printed pieces:** the tub (front face with its window, plus all four sides, four corner bosses for heat-set inserts), the lid (back face with its window, four corner screws), and the arm-and-tray (tray for the XIAO RP2040 and SimpleFOC Mini, the arm, and the bracket that holds the motor).
- **Elevation drive:** one GM2804 between the discs. Disc 1 is bonded to a printed adapter hub on the rotor; disc 2 hangs on two 3 mm steel posts and is centred by a 6 mm pin in the motor bore. For elevations within +/-90 degrees the posts never reach the arm.
- **Azimuth:** a second GM2804 stands upright on the base axis; its rotor carries the 5 mm printed turntable through a printed adapter. No belt, tube, bearings or slip ring.
- **Cable:** four thin wires (12 V, 5 V, ground, serial) leave the frame through a 10 mm hole in the frame floor and turntable, 30 mm from the axis, and wind round a spool printed into the base shell. Azimuth travel is about +/-150 degrees round south; firmware unwinds through south and never crosses north.
- **Base boards (keep-outs):** XIAO ESP32-S3, azimuth SimpleFOC Mini, compass, clock, USB-C PD board (socket through a slot in the back wall), buck converter.
- **Pose:** `--az` is the compass bearing the line points at (90 = along +X); `--el` is the elevation.

## Printed pieces (9 in all)
Frame tub, frame lid, arm-and-tray, turntable, base shell (spool included), azimuth adapter, elevation adapter hub, front disc, back disc (with hub 2). The two discs are two-colour. Print-ready files (each laid in its print orientation, Z up, on the bed) are in `cad/out/sun-dial/sun-dial-small/parts/print_ready/`; the discs come as `disc_*_2colour.step` with two bodies so Bambu Studio loads each as one object with two parts, and you give the strip the black filament.
- **Print orientation:** discs and tub with the outer face down; lid with its outer face down; hubs with the flange down; the arm-and-tray flat on the tray (the arm is a tall thin rib, so print it slowly or consider lying it on its side).
- **Plate:** the face that touches the plate sets the finish of the dial face and the tub front. Use a smooth plate for a glossy finish.
- **Filament:** white PETG or ASA for the discs (sun near a window), black for the line; PETG-CF for the rest.

## Assembly and access
1. Heat-set the corner inserts in the tub, the four inserts in the turntable and the four in the azimuth adapter.
2. Fix the azimuth stator to the base shell, add the adapter and turntable (four screws), and screw the boards in the base.
3. Build the elevation stack: motor on the arm bracket, adapter on the rotor, posts through the flange, disc 2 and hub 2 on the posts, pin through the bracket into the bore.
4. Drop the arm-and-tray into the tub, push disc 1 into the front window and bond it to the adapter boss, then close the lid over disc 2 with the four corner screws.
5. Screw the whole frame to the turntable through the tray (four M3).
**To get in:** remove the lid (four screws on the back face) to reach the motor, arm, tray and boards. Remove the four tray screws and unplug the cable to lift the frame off, then the four turntable screws to open the base.

## Checks run
- `python3 cad/src/sun_dial_small.py --check`: 0 clashes at four az/el pairs including el +/-90, 0 static clashes.
- Not checked: cable winding length and fatigue, compass interference, printability, strength, whether disc 1 can be bonded through the window in practice, wobble of the disc on the posts, the thin arm rib.

## Things to know or decide
1. **Compass distance.** The compass is only about 58 mm from the azimuth motor on the axis. It needs a test and calibration in place.
2. **Cable.** The spool and slot are a first idea; the winding length, strain relief, a plug at the frame end and a hard stop still need designing.
3. **Rotor cap is 1.5 mm thick.** Both motor adapters screw into it, so use short screws with thread-lock.
4. **Pin in the bore.** A 6 mm pin in a 6.5 mm bore will rub on bare metal; a bush may be needed.
5. **Board sizes** other than the SimpleFOC Mini and the GM2804 are placeholders. The XIAO ESP32-S3 uses all 11 header pins.
6. **Not modelled:** the screws, inserts, wiring, board standoffs, motor mounting screws into the base floor.
7. **Previews:** the matplotlib renders sort faces roughly, so thin parts can show through. Open the STEP for a proper look.

## Regenerating
```
python3 cad/src/sun_dial_small.py                  # STEP, parts, print-ready files, BOM, previews (add --az 135 --el 30 to pose)
python3 cad/src/sun_dial_small.py --discs laser    # laser-cut discs instead
python3 cad/src/sun_dial_small.py --check
```
The STEP files are written Y up, with the base standing on the Y = 0 plane, so they open upright in Fusion; add `--up z` for Z up. The print-ready files are always Z up.

Outputs: `cad/out/sun-dial/sun-dial-small/`, `bom/sun-dials/bom-sun-dial-small.csv`, `cad/media/previews/sun-dial-small/`.
