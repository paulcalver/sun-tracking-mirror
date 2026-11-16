# Finger pointer (2026-11-13)

A small tabletop pointer: a flat 120 mm pointing hand on a slim shaft that turns to point at the Sun (or Moon). Draft CAD, nothing printed, cut or tested. Source of truth: `cad/src/finger_pointer.py` (CadQuery). It replaces the earlier mirror ideas for this build.

## What it is
- **Plinth:** 170 mm square, 80.3 mm tall, black laser-cut acrylic (floor, four 3 mm walls, 6 mm top frame), the same method as the hinge mirror. Both steppers stand on the floor side by side, the compass and controller sit fixed at the back.
- **Shaft:** a 12 x 2 mm aluminium tube (azimuth) with a 6 mm silver steel rod inside it (elevation). Exposed length above the plinth 177 mm; pivot 257.3 mm above the table, about 328 mm overall with the hand pointing straight up.
- **Drive:** each stepper has a 20T GT2 pulley and a stock 200 mm loop to a 60T printed pulley (3:1). The azimuth belt turns the tube, the elevation belt turns the rod. At the top a 1:1 mitre bevel pair (rod gear A, axle gear B) turns the 6 mm pointer axle. Hand elevation = rod angle minus tube angle (firmware), so there is no slip ring and both axes turn without limit.
- **Hand:** 120 mm, traced from your engraving (`cad/src/assets/finger-source.jpg`, licence not checked). The pivot is the area centroid, so the plate is balanced about the axle; the finger axis is 21.6 mm off the pivot, which does not matter for a distant target. One 3 mm acrylic plate sits in front of the exposed gear pair, so the palm hides the gears from the front; from the back and sides the two mitre gears are on show. At least 26 mm of the palm covers the pivot in every direction; the gears are 21.4 mm across.
- **Compass:** GY-271 on a post at the back, about 110 mm from the steppers. Calibrate it in place, read it with the motors off.
- **Frame and angles:** X is the azimuth 0 direction, the axle runs along Y, el 0 is horizontal, + is up (+/-90). The script's `--az` and `--el` pose the model.

## Numbers from the script
| Item | Value |
|---|---|
| Belt | 60T / 20T, 200 mm loop gives 58.6 mm between centres (so the steppers are at X +/-50, Y -30.6) |
| Resolution | 1.8 deg / 16 microsteps / 3 = 0.0375 deg per microstep at the tube, at the rod and at the hand |
| Hand | 120 mm long, 4812 mm2, about 17 g per plate in acrylic |
| Lowest fingertip (el -90) | 186 mm above the table, 106 mm clear of the plinth top |
| Head | no housing: one printed bracket (a cap on the tube end with a bushing for the rod, plus an arm that carries the axle's 686 bearing), gear A on the rod top and gear B on the axle both exposed; gear envelope 21.4 mm across, axle 21.7 mm, hand plate at Y -27.7 to -24.7 |

## Checks run
- `python3 cad/src/finger_pointer.py --check`: tests at el 0, +/-30, +/-60, +/-90 and az 0, 60, 135, 250 (all part pairs involving the rod, axle, gear and plates, bounding-box filtered): **0 interferences**; static check at az 0, el 0: 0. 
- Not checked: tooth meshing (gears are plain cones, tangent along the mesh line), belt tension, wiring, assembly order, printability (support, bridging, bed orientation), strength.

## Parts
Laser, 6 mm and 3 mm black acrylic (STEP, DXF in `cad/out/earlier-concepts/finger-pointer/parts/laser/`): floor plate, top frame, 4 wall panels (3 DXFs: long, long with a 12 mm cable notch, short x2), the hand plate. Engraving artwork: `finger-engrave-front.png` at 203 dpi, 8 px per mm in the plate frame, black = laser frosts the light areas and leaves the ink black.

Printed in PETG-CF on the P1S (13 parts): bearing housing, 2 motor cradles, rod bottom bracket, controller tray, compass post, Hall post, tube collar, tube pulley, rod pulley, head bracket, hub ring. PETG-CF rather than PLA-CF because a sun-facing piece near a window can soften PLA-CF; check the nozzle is hardened.

Bought (reference shapes in `parts/purchase/`; list in `bom/bom-finger-pointer.csv`): 2 NEMA 17 (34 mm), 2 GT2 20T pulleys, 2 GT2 200 mm loops, 12 x 2 tube, 6 mm silver steel (one 333 mm bar covers the 228 mm rod and the 21.7 mm axle), 2 x 6701, 1 x 686ZZ, 1 x 626ZZ, 2 RS PRO POM mitre gears (20T, module 1, 6 mm bore, RS 521-6058), electronics as in the mirror.

## Things to know or decide
1. **Exposed gears (2026-11-13).** The drum head is gone. The head is one printed bracket plus the two bought gears: the cap sits on the tube end (rod runs in a bushing in its roof), gear A is on the rod top, and a plate-shaped arm beyond gear B's hub end holds the 686 bearing for the axle. Like the bought L-block it copies, both gear hubs run out to the arms, so the gears sit inside the L (the cap below, the bearing arm beside) and are open on the sides and the back. The axle is short (21.7 mm), supported at the arm and carried into gear B. Much smaller than the 36 mm drum.
2. **Open gears are a pinch point.** The stepper can pull hard at stall (set the driver current limit low); consider a printed guard if people will touch it. Keep fingers away from the mesh when testing.
3. **Spring not modelled.** A balanced hand has no gravity preload, so the bevel backlash needs a light torsion spring on the axle. No space is reserved for it yet.
4. **Gears are assumed.** I could not load the RS page (403), so the cone dimensions (toe 6.5, heel 10.7 mm axial, hub 12 mm, 4 mm long) are from the module-1 formulae, not the datasheet. Gear hub ends clear the cap and arm by only about 0.5 mm, so check against the real gears before printing the bracket.
5. **Not modelled:** fasteners, grub screws, heat-set inserts, wires, glue pockets and tenons (the mirror uses them), gear and pulley teeth detail on the gears, the belt tooth profile, bearing retention, the lid bearing preload.
6. **Source image licence** is unchecked; check it before showing the artwork.

## Regenerating
```
python3 cad/src/trace_finger.py          # traces cad/src/assets/finger-source.jpg to finger-outline.json and the engraving PNGs
python3 cad/src/finger_pointer.py        # STEP, parts, DXF, BOM, previews (add --az 40 --el 35 to pose)
python3 cad/src/finger_pointer.py --check
```
Previews are in `cad/media/previews/finger-pointer/`. The matplotlib renders sort faces roughly, so thin walls can show through; open the STEP for a proper look.
