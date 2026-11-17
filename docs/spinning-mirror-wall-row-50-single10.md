# Alternative: one row of ten 50 mm mirrors on one NEMA 17 (2026-11-17)

Draft, nothing built or tested. This is the single-row alternative to the 3 x 8 wall piece in `spinning-mirror-wall-row-50.md`; read that for the unit, drive, tension, printing, electronics-box and open-point details, which are all the same. Build it with `python3 cad/src/spinning_mirror_wall_row_50.py --single10` (add `--check` for the clash sweep). Output: `cad/out/spinning-mirror/spinning-mirror-wall-row-50-single10/` (assembly STEP, `parts/print`, `parts/print_ready`, `parts/purchase`), previews in `cad/media/previews/spinning-mirror-wall-row-50-single10/`, BOM `bom/bom-spinning-mirror-wall-row-50-single10.csv`.

## What is different
- **One row, ten units** at 80 mm pitch on one 850 mm 2020 rail, one NEMA 17 on its bracket at the left end, ten 200 mm belt loops. About 0.93 m wide and 0.35 m tall with the rings.
- **Wall fixing:** three printed wall standoffs along the rail (at X = 40, 400 and 765 mm), as in the 3 x 8 piece (which has three per rail at X = 40, 360 and 600 mm): an arm to the rail's back slot (one M5 x 35 into a T-nut, head recessed on the wall side) with a flange and two M4 wall screws. Fix the standoffs to the rail first, then screw them to the wall.
- **Electronics:** the same printed box under the rail, but with one driver placeholder and one motor-lead hole. One TMC2209, one 24 V 3 A supply and a 3 A fuse. The box is unchanged in size, so it is bigger than one driver needs; shrink it later if you like.
- **Rail:** 850 mm, the same cut the first 10-unit basket was for.

## Checks and load
No clashes at any of three random tumble poses or two poses with random ring angles, none in the static pose, and every printed part is a single solid. About 1.2 kg of frame, motor and box plus 0.9 kg of units, so about 2.1 kg on the wall. One row incl. rotor is about 1.4e-4 kg m2: 0.014 N m for 100 rad/s2 and 0.042 N m for 300 rad/s2, well inside the motor's roughly 0.25 N m at 24 V; friction over ten links is what to measure.

## BOM
`bom/bom-spinning-mirror-wall-row-50-single10.csv`, with one line per screw type. The priced lines come to about **£151 ex VAT** including the Technobots shipping from the 3 x 8 cart (assumed the same). Quantities are rounded up to whole packs, so spares are larger for bearings (40 of 625ZZ, 30 of 683ZZ), mirrors (25) and rods. The T-nut price is the 100-off price you saw; 31 pieces may cost more per piece. The 3 mm hinge rods and the heat-set inserts, M3 screws, wall screws and ESP32 side are unpriced.
