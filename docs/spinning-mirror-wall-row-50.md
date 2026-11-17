# Wall-mounted row: ten 50 mm mirrors on one NEMA 17 (2026-11-17)

Draft, nothing built or tested. CAD: `cad/src/spinning_mirror_wall_row_50.py`; STEP and part files in `cad/out/spinning-mirror/spinning-mirror-wall-row-50/`; previews in `cad/media/previews/spinning-mirror-wall-row-50/`; BOM `bom/bom-spinning-mirror-wall-row-50.csv`; shopping list and prices in `spinning-mirror-belt-row-test-bom.md`. Background: `spinning-mirror-150-nema17.md` (the single unit and motor).

## Layout
- A **2020 aluminium extrusion** (850 mm) runs along the wall on three printed standoffs (at X = 40, 400 and 765 mm), the spindle line 45 mm out from the wall. The rail is the structure and the slide.
- Ten units at **80 mm pitch**. Each is a printed bearing block that bolts into the rail's top T-slot with two M5 T-nuts, so it slides to set the belt tension. A 5 mm spindle runs in two 625ZZ bearings in the block.
- **Drive:** each spindle carries a double-head GT2 20-tooth pulley. Ten short closed 200 mm GT2 loops chain the row: the NEMA 17 turns the first unit through a single pulley (lower belt level), unit 1 turns unit 2 (upper level), and so on, alternating. Every spindle turns the same way. The belts and pulleys are exposed.
- The **NEMA 17** hangs below a printed bracket at the end of the rail, shaft up, 80 mm before unit 1 (a normal pitch step). The bracket's 6 mm web is the motor plate, same screws and counterbores as the 150 mm pedestal.
- **Ring and mirror:** a ring (66 mm swept diameter) clamped to the top of the spindle by one M3 grub screw into a heat-set insert, with a free 3 mm axle on two 683ZZ bearings carrying a 4 mm printed carrier and a 50 mm x 1 mm glass mirror on each face. No balance trim screws and no brass slug at this size; weigh the discs.
- **Ring angle:** every ring is fitted at the same angle (ring plane parallel to the rail, use a straight edge along the rail when you tighten the grub screws), so only the tumble differs.
- Dimensions: rail 850 mm; ring centre 117.5 mm above the rail bottom (97.5 above the rail top), ring top 150.5; 14 mm between swept circles; 12 mm from a ring's swept edge to the wall.

## Checks the script runs (`--check`)
No clashes at any of three random tumble poses (axle and bearings excepted by design), none in the static pose, and every printed part is a single solid. Mass about 1.0 kg for the frame and motor plus 0.9 kg for the ten units.

## Load
One unit turns about 50 g (mirror group 17 g) with spin inertia about 1.1e-5 to 1.3e-5 kg m2. With the rotor the whole row is about 1.4e-4 kg m2, so 100 rad/s2 needs 0.014 N m and 300 rad/s2 needs 0.042 N m, a small part of the 0.25 N m the motor should give on 24 V. Friction, not inertia, decides how far this scales: bearings, belt tension and tooth losses over ten links. Measure it (see the 150 mm test plan).

## Printing (PETG or ASA; PLA is fine for the first test)
- **Ring:** flat, +Y face up, 4 walls; ream the two 7.05 mm bearing pockets and the 5.1 mm spindle bore. Heat-set insert in the foot.
- **Carrier:** flat.
- **Spindle block:** upright. The lower bearing pocket has a 45 degree ceiling so it needs no bridge or support. Ream the pockets so a 625ZZ presses in.
- **Motor bracket:** upside down on its flat top face. **Wall standoff:** flange on the bed.
- The files in `parts/print_ready/` are already in these orientations and carry their part names. Y-up versions for Fusion are in `parts/print/`.

## Assembly and tension
1. Fit the motor to the bracket, bolt the bracket to the rail end (two T-nuts), and fix the standoffs to the wall at a sensible height (the rail bottom is the datum).
2. Fit the 625ZZ pair, the spindle, two 1 mm M5 washers as a 2 mm spacer on the upper bearing, then the pulley (grub screw into a flat on the rod). Fit units one at a time from the motor end.
3. Set each belt before the next unit: slide the new block until the loop is firm (about 10 to 20 N, a light twang), then tighten its two M5 screws. One block's position sets both the belt to its left and the belt to its right.
4. Fit the ring with the same angle on every unit, then the mirrors.

## Open points
- The double-head pulley is assumed 28 mm long (two 8 mm bands, a 10 mm boss, 1 mm flanges), 12 mm over the teeth and 16 mm over the flanges. Check the delivered part and the belt heights (49 and 67 mm).
- Motor shaft length (24 mm assumed) and the front-face thread depth, as for the single rig.
- Belt pull on the motor shaft (rated 28 N sideways): the first pulley sits close to the motor face, but keep an eye on the first loop's tension.
- 625ZZ friction over ten units, belt tooth fit with 200 mm loops at 80 mm centres (tension range is a few mm either way), and whether the 4 mm printed carrier and ring wobble at speed.
- Glass breakage: wear eye protection, and consider a guard where people can reach.
- Wall fixing (plugs, studs) and the rail height are yours to choose; the standoffs use M4 screws.
- Electronics are as for the 150 mm rig (one TMC2209, ESP32, 24 V, fuse, capacitor); no tray is modelled yet.
