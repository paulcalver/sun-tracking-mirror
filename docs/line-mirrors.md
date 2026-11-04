# Line of 7 wall mirrors: passive and wedge "out of sync" versions (concept CAD, 2026-11-04)

Status: concept model only. Nothing ordered, printed or tested. Source of truth: `cad/src/line_mirrors.py` (CadQuery). STEP: `cad/out/line-mirrors/line-mirrors-passive.step` and `line-mirrors-wedge.step` (named parts, Y up, Z out of the wall, posed for a Sun 40 deg to one side). Renders: `cad/media/previews/line-mirrors/` (`-front`, `-posed-rays`, `-mechanism`, `-inner`, `-section` for each version). Builds on `wall-mirror-nema11.md`.

## What it is
Seven 50 mm round mirrors in a horizontal line, 70 mm pitch, all tilted together to reflect the Sun to a fixed target, and a way to move the seven spots in and out of a straight line.
- Each mirror: 50 mm glass (3 mm) on a 46 mm printed carrier, on a rigid 30 mm stem. The stem passes through a 10 mm pivot ball that sits in a bore in the front plate (free to slide in Z), and ends in a 6 mm ball tip behind it. Tip position = pivot minus 30 x mirror normal, so plate shift = 30 x sin(tilt), 12.7 mm for 25 deg.
- Tip ball sits between two 2 mm lip plates with 4.4 mm slots: the pan bar (vertical slots, slides in X) and, in the passive version, the tilt plate (slots at a different small angle per mirror, slides in Y).
- Pan = X motor. Tilt = Y motor. Both NEMA 11 screw actuators (drawn as body + rod).

## The two versions
- **Passive:** tip height = Y + slope_i x X. Slopes 0.045, 0.015, 0.06, ... so the spots are a straight line only when the pan offset is 0 (Sun on the wall axis) and fan out as the Sun moves. No third motor.
- **Wedge:** a wedge bar (seven ramps, slopes -0.15 to 0.2) rides on the tilt frame and is slid in X by a third NEMA 11. Tip height = Y + slope_i x u, with u the pan offset minus the wedge slide. u = 0 is a straight line, up to +/-5 mm of u bends it. The wedge motor compensates for pan in firmware.

## Keeping the Sun's view clear (the design rule)
The whole enclosure is behind a thin front plate (top at Z = 48). The mirrors stand on stems out of that plate (glass front at 75 mm from the wall at rest), with the back face of each carrier at least 3.8 mm above the plate even at 27 deg of tilt. Nothing is in front of any mirror face except the other mirrors.
Ray-cast check (`--check`): 15 sample points per mirror, rays towards the Sun and along the reflected direction, Sun at 25, 50 and 65 deg off the wall axis in 8 directions:
- Enclosure blocks 0.0% of rays at every angle, both versions.
- Other mirrors block 0.0% at 25 and 50 deg and about 5% at 65 deg (50 mm mirrors at 70 mm pitch just clear each other at the 50 deg design limit; a tighter pitch would shade).

## Other checks
- No clashes at normal cone tilt 0 and 25 deg in 8 directions (and with wedge u of +/-5 in 4 more cases), both versions. Largest single-mirror tilt 27.1 deg when the wedge pattern adds to the cone.
- Spots at 3 m: passive, Sun 40 deg off axis: heights -85, +28, +113, +85, -28, -113, -85 mm; Sun on axis: all 0 (spread 0.0 mm, checked). Wedge u = 0: spread 0.0 mm at any Sun angle; u = +/-5: about 370 to 390 mm spread.

## What modelling changed
- The 4.4 mm slot only works as a thin lip: a tilted stem needs a stepped slot (4.4 mm contact lip, 9 mm relief behind it).
- The tip joint cannot be a ball in a thin plate (the tip height changes 2.8 mm over the tilt range). It works as a ball held between two lip faces, with the pivot ball sliding in its bore instead.
- Tilt plate arm, X motor, wedge bar and wedge motor all fought for the same corner until the X motor went high at the left (y +28) and the wedge motor low at the left (y -18).
- Layout v2 (2026-11-04): the Y motor first sat in a block below the strip at the right end. It now hangs from the top wall inside the strip and its rod pushes down on a tab on the tilt plate (return spring not modelled), so the enclosure is a plain rectangle, 660 x 96 x 48 mm. All checks re-run clean.

## Simplified or not modelled
Guides and slides for the bars and frame, return springs, ball preload and magnets (balls must be held against the lips and ramps), fasteners, the real NEMA 11 screw actuator (rod and nut drawn as plain parts), wiring, controller. The enclosure is a plain 660 x 96 x 48 mm strip; all three motors are inside it (X high and wedge low at the left, Y hanging from the top wall at the right).
Mirror glass flatness and a 50 mm round source not looked into. Hole and slot accuracy of about 0.1 mm decides how straight the line is (0.1 mm is about 0.2 deg of beam, 13 mm of spot at 2 m).

## Plain steppers instead of screw actuators (not modelled, estimates from this layout)
The model draws NEMA 11 screw actuators (body 28.2 x 34 mm + rod). UK stock of those is mostly RS (Thomson, about 260 to 360 GBP ex VAT each); cheap ones ship from abroad. A plain stepper plus a coupler, a T8 lead screw (2 mm lead) and a brass nut does the same job from UK parts:
- Pololu 1205 NEMA 11 as sold by The Pi Hut: 28 x 28 x 32 mm, 5 mm D shaft, 0.67 A, 3.8 V, about 6 Ncm. NEMA 17 42 x 34 mm and 42 x 40 mm also at The Pi Hut (about 11 to 12 GBP ex VAT).
- Y axis (vertical, in the strip): motor 32 + coupler 14 + nut 10 + 25.4 travel is about 81 mm against 90 mm of inner height, so it just fits with the tab moved lower on the tilt plate.
- X and wedge axes (horizontal, left end): coupler + nut + 25 mm travel fit in the existing 660 mm length for NEMA 11. The screw must not run through the pan bar: either shorten the plates (about +/-22 mm instead of +/-28 mm) or, with NEMA 17, run the screw above the plates in Z.
- NEMA 17 bodies are 42 mm wide, so the two left-end motors fit side by side only with about 0.7 mm to spare in the 90 mm inner height.
- The nut must be stopped from turning (a rail or slot), and a return spring is still needed.

## Wave version: NEMA 17 belts and a camshaft travelling wave (2026-11-04)
`python3 cad/src/line_mirrors.py --variant wave` writes `cad/out/line-mirrors/line-mirrors-wave.step` and renders `line-wave-*.png`. Chosen because a continuously moving wave never needs a perfect straight line, so tolerances relax from about 0.05 mm to about 0.3 mm (0.3 mm is about 60 mm of spot at 3 m, hidden by a +/-170 mm wave).
- **Pan (X):** NEMA 17 at the left end, 20T GT2 pulley, idler, short belt loop in the XZ plane; an arm on the pan bar clamps the upper run. Pan bar travel +/-12.7 mm.
- **Tilt (Y):** NEMA 17 standing on the back plate at the right end, pulley above it, idler on a post, belt loop in the XY plane; a bracket on the tilt frame clamps the left run.
- **Wave:** a 5 mm camshaft along the row carries seven 7 mm eccentric cams (1 mm throw, 60 deg phase step per mirror). Each cam lifts a slotted tab (the back lip plate for that mirror) so tip height = Y + sin(cam angle + 60 deg x i). A third NEMA 17 on the tilt frame turns the camshaft through a coupler, slowly and continuously; its speed is the wave speed. Rotate the other way and the wave runs back.
- **Tilt frame** (bar, cam plate with four motor standoffs, right bearing, bracket) carries the camshaft and tabs, so the wave rides on top of the common tilt.
- **Size:** 742 x 96 x 60 mm (front plate top at 60 mm; the NEMA 17 body is 42.3 mm so the inner depth had to grow). Glass front about 90 mm from the wall.
- **Checks:** no clashes in 15 poses (tilt 0 and 25 deg in 8 directions, cam angle varied); enclosure blocks 0.0% of Sun and reflected rays at 25, 50 and 65 deg; other mirrors block 0% at 25 and 50 deg and about 5% at 65 deg. At 3 m the spots swing about +/-170 to 195 mm and the wave moves one mirror along for every 60 deg of cam rotation.
- **Not modelled:** tab guides (each tab must slide only in Y), a light preload (spring or magnet) holding each tab and ball on its cam, bearings, wiring, the nut-free belt tensioners, fasteners. The cam angle is a pose parameter, not yet driven from time.
- **Parts:** Pi Hut NEMA 17 42 x 34 mm (about 11 GBP ex VAT) for all three; GT2 belt and pulleys not checked on UK listings.

