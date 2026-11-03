> **Status: historical.** The HDP30 harmonic drive was dropped with the disc design; the current drives are a lead screw and a belt (`cad-brief.md`).

# HDP30 printable harmonic drive: notes (2026-11-01)

Candidate for the arm's joint reduction, in place of belts. Source: Robrotics HDP30 v2.0 (RevC), release page https://github.com/robrotics/hdp30/releases/tag/v2.0 and the repo https://github.com/robrotics/hdp30. The release bundle (README, BOM, STEP, DXF) was downloaded to `data/_scratch/hdp30/` (git-ignored, untrusted data, read as text only). Facts below are the maker's claims, not tested by us.

## What it is
A 3D-printed strain-wave (harmonic) gearbox that bolts coaxially onto a NEMA 17 (5 mm shaft). 30:1 (60-tooth flexspline, 62-tooth circular spline), cycloidal tooth profile, all PLA including the flexspline. Hardware per unit: 8 M3x6 button head screws, 12 M3 heat-set inserts, one 30x42x7 mm bearing, 11 steel 5 mm balls, one set screw, PTFE grease. Maker's cost about $4 per actuator after about $47 of first-time packs (US prices). Licence CC BY-SA 4.0.

## Claims relevant to us
| Item | Claim |
|---|---|
| Torque | Held 1.49 N.m with no tooth skips. Cracking starts at about 1.5 N.m, wall broke at about 2.0 N.m. Treat 1.5 as a ceiling, not a working load |
| Backlash | README in the bundle: under 0.25 deg at the output. Release page: about 0.03 deg measured at 5 rpm. The two disagree; the README says it predates the later tests |
| Stiffness | 40 to 61 N.m/rad, about 1 deg of elastic twist at 0.85 N.m |
| Efficiency | 47 to 60 percent (static) |
| Back-driving | Release page says it holds about 1 N.m with the motor off (not stated in the README; verify) |
| Size | Printed parts about 54 mm across; stack of parts roughly 40 to 50 mm tall before the motor (my reading of the STEP bounding boxes, not an assembled dimension) |
| Motor | Validated with a 42x42x30 mm, 26 N.cm, 1.2 A motor under closed-loop FOC; release page suggests about 0.6 A |
| Not yet known | Fatigue life of the PLA flexspline, running efficiency under load, heat, long-term wear |
| Known issues | PLA creeps under sustained load; unit-to-unit variation up to 18 percent on its sibling drive; output preload is the main tuning knob |
| Sibling | HD20 (20:1) is stronger, tested to 3.3 N.m |

## Fit with this project (inference)
Good:
- Coaxial and round, so it matches the tubular UR-style joint housings far better than belts.
- 30:1 gives about 0.0034 deg per microstep and very slow, smooth motion, which suits the Sun's 0.25 deg per minute.
- Low backlash by the maker's numbers, and possibly self-holding with the motor off, which would cut holding heat.
- Cheap hardware after the first packs, likely less than the belt and pulley lines in the draft BOM.

Risks:
- **Torque margin.** My unmeasured shoulder load estimate is around 1 N.m, against a 1.5 N.m ceiling. Needs a lighter arm, shorter links or a spring counterbalance, or the stronger HD20 at the shoulder and elbow.
- **Creep under steady load.** The arm holds a gravity load all day, every day. PLA creep is a real concern for the shoulder and elbow. A counterbalance reduces it.
- **Fatigue is untested** and our duty is continuous. At the Sun's pace the motor turns slowly, so cycle counts are modest (inference), but it runs 24/7 for a year.
- **PLA softens in heat.** Keep it away from a sunlit window (the arm points at the Sun but should not sit in direct sun on its housings).
- **Bearing loads.** The single 30x42x7 bearing may not carry the overturning moment of a cantilevered arm; the shoulder and elbow probably need extra support (to be checked).
- **Driver and control.** Validated under closed-loop control; ours would be open-loop TMC2209 with encoders at the joints.
- **Licence.** CC BY-SA 4.0: credit Robrotics and share derivatives of their parts under the same licence. This affects the repo licence decision if we modify their files.

## Suggested next step
Add a second test-rig variant that mounts one HDP30 on the same NEMA face, with the lever arm on the output flange and the AS5600 magnet on the output side, and compare backlash, smoothness, heat and creep under a held load against the belt rig. Print order: HDP30 first, since it needs no belt tensioning.
