# Alternative: eight 100 mm mirrors on one rail, a NEMA 17 at each end (2026-11-17)

Draft, nothing built or tested. The 100 mm version of the wall piece in `spinning-mirror-wall-row-50.md`; read that for the drive, tension, printing and assembly details, which carry over. Build it with `python3 cad/src/spinning_mirror_wall_row_50.py --mirror100` (add `--check` for the clash sweep; the full build takes a few minutes). Output: `cad/out/spinning-mirror/spinning-mirror-wall-row-100/`, previews in `cad/media/previews/spinning-mirror-wall-row-100/`, BOM `bom/spinning-mirrors/bom-spinning-mirror-wall-row-100.csv`.

## Layout
One 1150 mm 2020 rail (X = -85 to 1065; the motor hangs about 55 mm past each rail end, supported by the 40 mm of bracket that sits on the rail) on three standoffs (X = 70, 490, 910), the spindle line 70 mm from the wall. **Eight units at 140 mm pitch.** A NEMA 17 sits at each end (X = -140 and 1120) on a bracket, the right-hand bracket being the mirror image (`print_motor_bracket_2`). Each motor drives its own **four** units through a chain of 320 mm GT2 loops (motor to unit 1 to 2 to 3 to 4, and mirrored from the right), with the middle 140 mm gap left without a belt. The electronics box (two drivers, one ESP32) hangs under the middle of the rail: DC jack and a motor lead on the left wall, USB-C and the other motor lead on the right wall, so each motor lead is about 0.6 m from the box (use the 0.5 m extension cables). The piece is about 0.45 m tall and 1.38 m wide.

## What changes from the 50 mm piece
- **Mirrors:** 100 mm x 1.5 mm **acrylic** by default (glass at 2 mm would add about 40 g a unit and make the torque problem worse; the thickness and material are in the 100 mm block at the top of the script).
- **Spindle:** an **8 mm rod** in two **608ZZ** (8 x 22 x 7) bearings, spaced 25 mm apart in a taller block (32 mm), with an 8 mm bore double-head pulley and an **M8 x 12 x 1 shim washer** as the spacer (12 mm OD, so it sits on the inner race only). The ring is held by an **M4** grub screw into an M4 heat-set insert, on a flat filed on the rod.
- **Hinge:** a **4 mm axle** on two **684ZZ** (4 x 9 x 4) bearings in a 12 mm wide ring with 14 mm bosses; 6 mm carrier with 5.4 mm hubs; the axle bore through the carrier is 4.15 mm with a flat-topped teardrop roof (printed holes shrink and a sideways bore sags), so the 4 mm rod slides in and is glued; ream with a 4.0 mm drill only if it is tight.
- **Pitch and belts:** **140 mm** pitch (22 mm between the 118 mm swept rings) on **320 mm** closed GT2 loops with 20-tooth pulleys. Check 160-tooth 320 mm loops are sold; if not, the pitch follows the nearest loop (a 300 mm loop gives 130 mm, a 340 mm loop on 30-tooth pulleys 140 mm).
- **Block screws** are M5 x 35; the wall standoffs take M5 x 50, the electronics box M5 x 8 and the ring-foot grub screws are M4 x 10 (see the review notes below). The electronics box is the same, now centred under the rail.
- Ring centre 157 mm and ring top 216 mm above its rail bottom; the piece is about 0.45 m tall and 1.38 m wide.
- **Mirror retention:** see below.

## Mirror fitting: rimless, glued (default since 2026-11-18)
The first bezel version (a printed push-and-twist cup on each face) printed clunky and heavy and was removed, so the carrier has no bezels: the two acrylic discs are **glued flat to the carrier faces**, as on the 150 mm test unit, and the fitting is permanent. The carrier edge is 0.5 mm inside the disc (R 49.5 mm), so no printed edge shows from the front; the rim is 3 mm wide with one cross bar and the hinge hubs, with no pegs. Each unit drops the two bezels (10.8 g of the 63 g mirror group), and the ring clearance to the carrier grows from 0.5 mm to about 3.8 mm (the disc corner at R 50.2 against the 54 mm ring bore).

Glue: a ring of 1 mm acrylic foam tape (VHB type) on the rim and a strip on the bar per face, plus a few spots of clear 2-part epoxy for the permanent bond. Test on a scrap disc first (CA glue can craze acrylic) and leave the protective film on until the end. Press each disc flat while it sets. Keep the printed carrier flat, because a warped carrier shows through the mirror.

## Hinge bearing pockets (2026-11-18)
The turning inner race of each 684ZZ used to sit 0.1 mm from a flat printed floor, so it could rub on the PLA behind it. The pocket is now 0.4 mm deeper than the bearing, and there is a 6.4 mm counterbore 1.5 mm deep in the floor, wider than the inner race, so only the outer race touches the floor. Update after the first print: the pockets were too tight, which squeezes the thin 684ZZ outer race and adds drag. The pocket is now **9.25 mm across** (a slip fit) with a 0.4 mm lead-in chamfer at the mouth and a flat-topped teardrop roof so it prints round (the ring prints flat, +Y up). The floor relief is **7.2 mm** across with a 0.2 mm chamfer, so the ledge under the outer race is only about 1 mm wide and the inner race has about 0.6 mm of clearance even after shrinkage. Hold each bearing in place with a small drop of retaining compound or CA on the **outer race only**, never on the inner race or the shields.

## Rail screws (2026-11-18)
The 20-series rail has a 6.13 mm slot opening, 1.8 mm lips and a slot 6.1 mm deep; the M5 slide-in nut is 9 x 10 x 4.4 mm (6 mm neck 1.4 high, wings 1.4, chamfer 1.6). The screw-head counterbore in the spindle blocks and motor brackets is 2 mm deep (was 3), so an M5 x 35 stops about 1 mm short of the slot floor with the full nut thread engaged. A 3 mm counterbore left only 0.1 mm to the floor. The wall standoffs are 60 mm long, so their head seat is now 15 mm in from the wall and they take **M5 x 50** (tip about 1 mm short of the slot floor); an M5 x 35 there would end about 15 mm short of the nut.

## Pre-order review (2026-11-18)
A second review of everything you buy changed these lines. **Box screws M5 x 8** (an M5 x 12 bottoms on the rail's slot floor before the head seats). **Ring-foot grub screws M4 x 10** (the foot face is 10 mm from the rod, a 6 mm grub would not reach). **VHB tape 3 mm wide for the rim (about 5 m) plus 6 mm for the bars (about 2 m)**, and a line for clear 2-part epoxy. The lower 608ZZ now goes into the block from below and is pressed up against the cone ceiling, which leaves it 0.5 mm off the rail. Fit the standoffs to the rail before the rail goes on the wall (the screw heads are on the wall side), and fit the electronics box last, because it hides the middle standoff's lower wall screw; use pan-head M4 wall screws, as the flange holes have no countersink. Still to check with real parts: pulley length (28 mm), motor shaft length (24 mm; 22 mm is marginal, 20 mm too short), nothing else on the washer (now an 8 x 12 x 1 shim) and the motor lead connector.

## Printing material (2026-11-18)
Matt PLA throughout is fine for this prototype: indoors, out of daylight, short runs. PETG or ASA would add nothing here, so there is no need to buy PETG. Two cautions with plain PLA, which softens at about 55 to 60 C and creeps under steady load:
- **Motor bracket in PLA-CF** (needs a hardened nozzle): it carries the 0.5 kg motor about 55 mm past the rail end plus the belt pull, and bolts to the warm motor face. The spindle blocks can be PLA-CF too, for the belt tension. Keep the TMC2209 at the low end of 1.2 to 1.5 A with idle current reduction on.
- **Plain PLA for the carriers and rings**: PLA-CF is more brittle, and the thin walls around the hinge bearing pockets need some give.
- Press heat-set inserts in gently and a little cooler than for PETG; thread-lock the M4 grub screws and recheck them, as PLA relaxes under clamp load over time.

## Checks and load
No clashes at any of three random tumble poses or two poses with random ring angles, none in the static pose, and every printed part is a single solid. Frame, motors and box about 2.0 kg plus 8 units about 1.8 kg: about 3.8 kg on the wall.

One unit turns about 138 g (mirror group 49 g, discs and carrier) with spin inertia about 1.1 to 1.6e-4 kg m2. With the rotor, four units on one motor are about 4.5 to 6.3e-4 kg m2, so **100 rad/s2 needs about 0.06 N m and 300 rad/s2 about 0.19 N m before friction**, against roughly 0.25 N m from a NEMA 17 at 24 V. That is a workable margin for each half; friction over four links is the thing to measure. The two halves are driven independently, so they can run different patterns.

## Open points
- 320 mm GT2 loops and 8 mm bore double-head pulleys are not in the baskets; check they exist before committing to the pitch.
- Print the new carrier (rim edge 0.5 mm inside the disc) and a ring with the relief behind the bearing pockets, and check that the tumble joint swings freely before the rest.
- 1.5 mm acrylic discs at 100 mm: dish and finish are unknown, so order one first. The spacer is now an 8 x 12 x 1 shim, so it should clear the 608ZZ shield and outer race; check it on the bench.
- The 4 mm ring walls and the 0.95 to 1.5 mm walls around the hinge bearing pockets are thin: press the bearings in gently (PLA is stiff but brittle, so ream the pockets rather than forcing them).
- Everything else (pulley length, motor shaft length, thread depth) is as in the 50 mm doc.

## Option: open low-drag hinge bearings (saved 2026-11-18, not adopted)
If the 684ZZ hinge bearings (medium friction from shields and grease) hold back the tumble, an open version is the upgrade route: [Ashley Bearings, budget 684 open miniature ball bearing 4 x 9 x 2.5 mm](https://www.ashleybearings.co.uk/budget-684-open-miniature-ball-bearing-4mm-x-9mm-x-25mm), £18.40 ex VAT for 20 plus about £7 postage.
- It is 2.5 mm wide, not 4 mm, so the CAD (`BRG = (4.0, 9.0, 4.0)` in the 100 mm variant) needs the pocket depth and axial positions changed. Radial fit (4 mm bore, 9 mm OD) is unchanged. **No CAD change made**: test the cheaper 684ZZ first (degrease, light oil) and decide after.
- Check whether they arrive oiled or dry; add a drop of light oil. The 608ZZ spindle bearings stay as they are.
