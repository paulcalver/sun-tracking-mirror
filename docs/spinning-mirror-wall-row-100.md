# Alternative: eight 100 mm mirrors on one rail, a NEMA 17 at each end (2026-11-17)

Draft, nothing built or tested. The 100 mm version of the wall piece in `spinning-mirror-wall-row-50.md`; read that for the drive, tension, printing and assembly details, which carry over. Build it with `python3 cad/src/spinning_mirror_wall_row_50.py --mirror100` (add `--check` for the clash sweep; the full build takes a few minutes). Output: `cad/out/spinning-mirror/spinning-mirror-wall-row-100/`, previews in `cad/media/previews/spinning-mirror-wall-row-100/`, BOM `bom/bom-spinning-mirror-wall-row-100.csv`.

## Layout
One 1150 mm 2020 rail (X = -85 to 1065; the motor hangs about 55 mm past each rail end, supported by the 40 mm of bracket that sits on the rail) on three standoffs (X = 70, 490, 910), the spindle line 70 mm from the wall. **Eight units at 140 mm pitch.** A NEMA 17 sits at each end (X = -140 and 1120) on a bracket, the right-hand bracket being the mirror image (`print_motor_bracket_2`). Each motor drives its own **four** units through a chain of 320 mm GT2 loops (motor to unit 1 to 2 to 3 to 4, and mirrored from the right), with the middle 140 mm gap left without a belt. The electronics box (two drivers, one ESP32) hangs under the middle of the rail: DC jack and a motor lead on the left wall, USB-C and the other motor lead on the right wall, so each motor lead is about 0.6 m from the box (use the 0.5 m extension cables). The piece is about 0.45 m tall and 1.38 m wide.

## What changes from the 50 mm piece
- **Mirrors:** 100 mm x 1.5 mm **acrylic** by default (glass at 2 mm would add about 40 g a unit and make the torque problem worse; the thickness and material are in the 100 mm block at the top of the script).
- **Spindle:** an **8 mm rod** in two **608ZZ** (8 x 22 x 7) bearings, spaced 25 mm apart in a taller block (32 mm), with an 8 mm bore double-head pulley and an **M8 washer** as the spacer. The ring is held by an **M4** grub screw into an M4 heat-set insert, on a flat filed on the rod.
- **Hinge:** a **4 mm axle** on two **684ZZ** (4 x 9 x 4) bearings in a 12 mm wide ring with 14 mm bosses; 5 mm carrier with 5 mm hubs.
- **Pitch and belts:** **140 mm** pitch (22 mm between the 118 mm swept rings) on **320 mm** closed GT2 loops with 20-tooth pulleys. Check 160-tooth 320 mm loops are sold; if not, the pitch follows the nearest loop (a 300 mm loop gives 130 mm, a 340 mm loop on 30-tooth pulleys 140 mm).
- **Block screws** are M5 x 35 (the same as the standoff screws). The electronics box is the same, now centred under the rail.
- Ring centre 157 mm and ring top 216 mm above its rail bottom; the piece is about 0.45 m tall and 1.38 m wide.
- **Mirror retention:** see below.

## Mirror bezels (screwless, push and twist)
Each face has a printed **bezel**: a shallow cup over the carrier edge with a **2 mm lip** over the disc rim (the lip is 1 mm thick, so the face is nearly flush). The two bezels are the same part, one turned over. Four small **pegs** stand out from the carrier edge on each face; each bezel's skirt has four L-shaped grooves. You push the bezel on (the pegs enter the grooves from the open end), then twist about 16 degrees until the pegs reach the groove ends. Near the end of each groove is a 0.04 mm bump that gives a click and keeps the bezel from backing off. To remove, twist the other way and pull. The disc sits in a 100.6 mm pocket with 0.3 mm under the lip (room for thin tape). The pegs are at 50, 120, 250 and 300 degrees, which also keys the bezel so it only goes on one way up; the hinge hub and bosses have a swept notch in the bezel skirt so the bezel can twist past them.

The bezel is 5.0 g, the carrier 10.7 g (it dropped the second cross bar; the rim and one bar are enough because both bezels clamp the disc, and a 1.5 mm acrylic disc supported on its rim deflects only about 0.06 mm at 10 g). Measured clearance from the bezel to the ring and hinge bearings is 0.5 mm. Print the bezel lip face down (the cup opens upward, no supports); the groove legs are short bridges.

## Checks and load
No clashes at any of three random tumble poses or two poses with random ring angles, none in the static pose, and every printed part is a single solid; the bezel passes through its whole twist without touching the carrier except for the intentional click bump. Frame, motors and box about 2.0 kg plus 8 units about 1.8 kg: about 3.8 kg on the wall.

One unit turns about 135 g (mirror group 60 g, bezels included, so lighter than the 138 g unit before bezels) with spin inertia about 1.1 to 1.5e-4 kg m2. With the rotor, four units on one motor are about 4.4 to 6.1e-4 kg m2, so **100 rad/s2 needs about 0.06 N m and 300 rad/s2 about 0.18 N m before friction**, against roughly 0.25 N m from a NEMA 17 at 24 V. That is a workable margin for each half; friction over four links is the thing to measure. The two halves are driven independently, so they can run different patterns.

## Open points
- 320 mm GT2 loops and 8 mm bore double-head pulleys are not in the baskets; check they exist before committing to the pitch.
- Bezel test first: print one carrier and two bezels and check the push-and-twist fit and the click (the 0.04 mm bump and 0.15 mm groove play are tight for FDM; the numbers `PEG_R`, `TWIST` and the groove radius are at the top of the script). Clearance to the ring is only about 0.5 mm, so an oversize print will rub.
- 1.5 mm acrylic discs at 100 mm: dish and finish are unknown, so order one first. The M8 washer (16 mm) and the 608ZZ outer race (about 18 mm inside) leave little room: check it does not rub.
- The 4 mm ring walls and the 0.95 to 1.5 mm walls around the hinge bearing pockets are thin: use PETG and press the bearings gently.
- Everything else (pulley length, motor shaft length, thread depth) is as in the 50 mm doc.
