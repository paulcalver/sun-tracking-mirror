# Single sun dial, one motor between two discs (2026-11-16)

One dial: a deep square frame on a round turning base. A flush 150 mm disc on each face shows the Sun's elevation from either side; the frame turns to show the azimuth. Draft CAD, nothing printed, cut or tested. Source of truth: `cad/src/sun_dial_one.py` (CadQuery). The behaviour is modelled in `sim/sun-dials/sun-dial-between.html`.

## What it is
- **Frame:** 170 mm square, 44 mm deep, 3 mm black acrylic: two faces with a 152 mm window each, four side strips. Overall height 240 mm, base 200 mm across and 66 mm tall.
- **Discs:** two 150 mm, 3 mm white acrylic discs, flush in the windows with a 1 mm shadow gap, each with a radial slot and a black strip pressed in.
- **Elevation drive:** one GM2804 (with the AS5048A encoder) sits between the discs. Disc 1 is bonded to a printed adapter hub bolted to the rotor cap. Disc 2 is carried round the motor on two 3 mm steel posts (at 45 and 135 degrees, 22 mm out) fixed to a small printed T-plate, and centred by a 6 mm pin into the motor's 6.5 mm bore. A printed arm rises from a tray on the frame floor to a bracket on the motor back. For elevations within +/-90 degrees the posts never reach the arm.
- **Frame electronics:** the tray carries a XIAO RP2040 and a SimpleFOC Mini (26.1 x 21 x 7.6 mm), shown as keep-out boards.
- **Azimuth drive:** a second GM2804 stands in the base, 58.6 mm off the axis, with a 20T GT2 pulley on its rotor. A 200 mm belt drives a printed 60T pulley on a 12 x 2 mm hollow tube (3:1). The tube turns in two 6701 bearings in a printed housing, and carries the turntable through a collar.
- **Slip ring:** the iPower 6.5 mm ring (28.4 mm long, 7 wires) sits inside the tube. It carries 12 V, 5 V, ground and serial to the frame.
- **Base electronics:** keep-outs for the XIAO ESP32-S3, the azimuth SimpleFOC Mini, a compass, a clock, a USB-C PD board with its socket at the back rim (a slot in the wall), and a buck converter. The compass is about 133 mm from the azimuth motor.
- **Frame and pose:** Z up, the frame turns about Z. `--az` is the compass bearing the line points at (90 = along +X) and `--el` is the elevation.

## Checks run
- `python3 cad/src/sun_dial_one.py --check`: 0 clashes at four az/el pairs including el +/-90, 0 static clashes. The frame corners swing 87.8 mm from the axis, inside the 99 mm turntable. Clearances are small: bracket to hub 2 about 0.35 mm.
- Not checked: belt (not modelled), cable routes, which end of the slip ring is fixed, tooth meshing, printability, strength, motor and tube alignment, wobble of the disc on the posts.

## Things to know or decide
1. **Slip ring fit is assumed.** I modelled its body turning with the tube and a short stub held by an anchor. Check the real part's mounting; the listing does not say which end is fixed.
2. **Rotor cap is 1.5 mm thick.** The adapter screws need a short thread plus thread-lock.
3. **Pin in the bore.** A 6 mm pin in a 6.5 mm bore will rub on bare metal; a printed or bronze bush may be needed.
4. **Board sizes** other than the SimpleFOC Mini and the GM2804 are placeholders, and the XIAO ESP32-S3 uses all 11 header pins (the SimpleFOC enable must be tied high).
5. **Not modelled:** the belt, fasteners, heat-set inserts, wiring, board standoffs, bearing retention, the arm foot screws.
6. **Previews:** the matplotlib renders sort faces roughly, so thin parts can show through. Open the STEP for a proper look.

## Regenerating
```
python3 cad/src/sun_dial_one.py            # STEP, parts, DXF, BOM, previews (add --az 135 --el 30 to pose)
python3 cad/src/sun_dial_one.py --check
```
Outputs: `cad/out/sun-dial/archive/sun-dial-one/`, `bom/sun-dials/bom-sun-dial-one.csv`, `cad/media/previews/sun-dial-one/`.
