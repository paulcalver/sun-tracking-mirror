# Wall-mounted tip-tilt sun mirror, two NEMA 11 (concept, 2026-11-04)

Status: concept model only. Nothing ordered, printed or tested. A separate idea from the v4 plinth mirror (`cad-brief.md`).
Source of truth: `cad/src/wall_mirror_nema11.py`. STEP: `cad/out/wall-mirror/wall-mirror-nema11.step` (17 named solids, Y up, Z out of the wall, posed for the example Sun). Renders: `cad/media/previews/wall-mirror/`.

## Idea
A small round mirror on a wall reflects the Sun to a fixed spot (heliostat). The mirror normal bisects the Sun and target directions, so the mirror moves half as far as the Sun. The Sun must be in front of the wall, so it only works in daylight and parks otherwise.

## Mechanism
- 60 mm round glass, 3 mm, glued to a printed 58 mm carrier. The carrier sits on a steel ball (pivot) at the glass centre.
- Two NEMA 11 motors (28.2 mm face, 31.5 mm body), each with a non-captive lead screw, push the carrier from behind through a steel ball on a 10 mm magnet pad (ball on flat: free to slide a little as the mirror tilts, no backlash, magnets also hold the carrier on). A pivot magnet holds the pivot ball.
- Push points are low, left and right of centre (+/-15.3, -16.8), so both screws together = pitch and one against the other = yaw.
- Screws are keyed by a D flat in a small plate on each motor face (a captive-type actuator would do this inside).
- Controller stack (RP2040 board, 2 x TMC2209, RTC) sits above the motors.
- Housing 70 x 70 mm outside, 81 mm deep, 2 mm printed walls, round window 66 mm. The 6 to 9 mm glass offset in front of the pivot slides the glass sideways by about 4 mm at 25 deg, which is why 66 mm was too tight.

## Checks (`--check`)
- Design cone: mirror normal within 25 deg of the wall normal (Sun up to 50 deg off the wall normal, any direction).
- No clashes at tilt 0, 25 and 30 deg in 8 directions.
- Screw movement from neutral at most 10.9 mm (13 mm allowed), screw tail stays 6 mm above the back plate, ball slip on the pad at most 3.6 mm (pad radius 5).
- Depth is set by motor length (31.5) plus screw travel, not by the NEMA 11 face. Recessing the housing about 40 mm into the wall would leave a shallow bezel.

## Coverage (`--day MM-DD --lat --lon --wall-bearing --target`)
South wall, 51.5 N, 0 E, times in UTC (24 h of clock, not BST):
- Target straight out from the wall: 21 Mar 4.7 h (09:50 to 14:20), 21 Dec 7.5 h (08:20 to 15:40), **21 Jun 0 h** (Sun too high: the mirror would need over 30 deg).
- Target 25 deg below horizontal (spot on a table or floor): 21 Jun 4.0 h (10:10 to 14:00), 21 Mar 5.8 h (09:20 to 15:00), 21 Dec 6.3 h (08:50 to 15:00).
- A wall facing east gets about 3.3 h on 21 Mar (06:10 to 09:20): the useful window follows the wall's bearing.

## Open points
- NEMA 11 non-captive lead screw actuator: confirm a real part with a 5 mm screw, 44 mm long, bore, and travel; the model uses plain rods.
- Ball on flat needs the steel balls and magnets to be chosen so the pull is enough to hold against gravity and vibration but not to drag.
- Backlash is removed by the magnets, but the screws still need a hold current or a self-locking lead.
- Controller placement is a stack in the housing; a remote controller would shrink the box.
- Mirror glass and carrier flatness, and a round 60 mm mirror source, not looked into.
