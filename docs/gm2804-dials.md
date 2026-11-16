# GM2804 two-dial wall piece (2026-11-16)

A flat wall piece with two 150 mm white discs. The left disc shows the Sun's elevation and the right disc its azimuth. Each disc is turned directly by an iPower GM2804 gimbal motor with the AS5048A encoder, no gears. Draft CAD, nothing printed, cut or tested. Source of truth: `cad/src/gm2804_dials.py` (CadQuery). The behaviour is modelled in `sim/sun-dials.html`.

## What it is
- **Plate:** 550 x 220 mm, 3 mm white acrylic, 62 mm off the wall on four printed posts (M4 screws at the corners). The discs are 150 mm, 3 mm white acrylic, 5 mm in front of the plate, centres 165 and 385 mm from the left edge.
- **Disc hand:** a 3 mm radial slot from the centre to the rim, with a 3 x 75 mm black acrylic strip pressed in so the line shows flush on both faces.
- **Drive:** the motor base (stator, encoder built in) is screwed to the back wall of a printed case behind the plate, four 2.4 mm holes on a 15.8 mm circle. The rotor faces the plate and carries a printed adapter (flange and boss) screwed to the four holes in its 1.5 mm cap, on a 19 mm circle. A 6 mm pin in the boss passes through a 12 mm plate hole to a small hub bonded to the back of the disc (one M3 grub screw). From the front you see only the plain disc.
- **Driver bays:** between the motors, two printed 57 mm cubes, each with a 50 x 50 x 50 mm keep-out for a SimpleFOC Mini driver (1 mm clearance), a lid at the back, a 3 mm flange to bond to the plate. This is what sets the wall standoff: 57 mm of bay plus 5 mm to the wall is 62 mm. The disc front ends up 73 mm from the wall.
- **Frame:** X right, Y up, Z out from the wall. `--el` and `--az` pose the discs (left: line angle above horizontal; right: compass bearing, north up).

## Checks run
- `python3 cad/src/gm2804_dials.py --check`: 0 clashes with the discs posed at four angle pairs, 0 static clashes.
- Not checked: whether the motor really fits the printed case (the motor is a simplified shape taken from the supplied STEP), cable routing, screw sizes, printability, strength, wobble of the disc on the 10 mm pin.

## Things to know or decide
1. **The 50 mm driver cube sets the depth.** The real SimpleFOC Mini may be much smaller; if so the bays, and the 62 mm standoff, could shrink a lot.
2. **No space yet for the ESP32, 12 V supply or buck converter.** They need their own bay.
3. **Rotor cap is 1.5 mm thick.** The adapter screws only get a short thread; use thread-lock or adhesive.
4. **Screw sizes** for the 2.4 mm holes are not known; check with the supplier.
5. **Not modelled:** fasteners, heat-set inserts, wires, tape, bearing in the plate hole, encoder wiring position.
6. **Previews:** the matplotlib renders sort faces roughly, so thin parts can show through (the front view shows the bays through the plate). Open the STEP for a proper look; the section view is the clearest.

## Regenerating
```
python3 cad/src/gm2804_dials.py            # STEP, parts, DXF, BOM, previews (add --el 30 --az 135 to pose)
python3 cad/src/gm2804_dials.py --check
```
Outputs: `cad/out/sun-dial/archive/gm2804-dials/`, `bom/bom-gm2804-dials.csv`, `cad/media/previews/gm2804-dials/`.
