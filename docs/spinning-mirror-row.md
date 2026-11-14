# Spinning mirror row, 7 units (2026-11-14)

Draft CAD, nothing cut, printed or tested. Model: `cad/src/spinning_mirror_row.py` (reuses the single unit from `spinning_mirror.py`; `--check` runs 8 random poses of all 7 units against everything). Single-unit notes: `spinning-mirror-gimbal.md`.

## Layout
- 7 units at 95 mm pitch, 100 mm across the centre plate: 17 mm clear between rings, 22 mm at the plate (6 mm plate, 8 mm each side). Unit centres X = -287.5, -192.5, -97.5, 2.5, 97.5, 192.5, 287.5.
- Base 720 x 140 mm, three 6 mm plywood layers on four rubber feet. Middle layer has two windows for 38 x 6 x 620 steel flat bar (about 2.2 kg ballast) and a cable channel that opens at the left end. Top layer has a cable hole and four pilot holes per unit, and slots for the uprights and centre plate.
- Motor boss (print) bolts down with M3 x 16 self-tapping screws; the motor sits on it exactly where it sat on the single-unit puck, so the unit geometry is unchanged.
- Goalpost: two end uprights (2 x 6 mm laminated, 70 wide) and a centre plate (6 mm), all with tabs into the top layer and a 20.2 mm window for the bar. 20 x 20 x 1.5 aluminium bar, 700 mm, centre 169 mm above the table, uprights to 189 mm.
- Top support: 3 mm steel pin (19 mm) pressed into a boss on top of each ring, running in a 683ZZ in a printed block under the bar. The block is held by two M4 screws through 6 mm holes in the bar, so each can be nudged 1 mm either way to line up. The pin has 3 mm axial float, so the motor carries the weight and the top only locates sideways.
- Wiring: motor cables go down the boss, along the middle layer channel to the left end. Controller boards are off the model.

## Checks (script)
No clashes in the static pose and over 8 random poses of all units. Mass about 3.6 kg frame (2.2 kg steel) and 1.5 kg for the 7 units.

## Cutting
Bed 1219 x 914, 6 mm plywood: the whole base and every plate fits on one sheet. DXFs in `cad/out/spinning-mirror-row/parts/laser/`. Cut 3 base layers, 4 upright layers (laminate in pairs) and 1 centre plate.

## Open
- Motor size and bolt circles are still assumed.
- Ply tab slots are 0.2 mm loose; test on a scrap.
- Bar stiffness and the end plates are not analysed. A rough estimate put the bar's bending mode near 20 Hz, so check by hand.
- 7 motors need 21 PWM outputs, two boards.
- Whether neighbouring units interact through the shared base and bar (vibration). Worth watching on the first run.
