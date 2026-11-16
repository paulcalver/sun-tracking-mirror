> **Status: historical (as of 2026-11-03).** This is the decision log of the earlier arm, goal post and disc concepts. The current design is the hinged mirror on a turning drum: read `docs/cad-brief.md`, `docs/parts-sourcing.md` and `docs/handoffs/2026-11-03-sun-arm-v4.md`. Entries below are not kept up to date.

# Sun-Pointing Robot Arm: Handover Note

## Direction change (owner, 2026-11-01): simplify to a two-axis mount
The owner intends to massively simplify: one motor turns the base (azimuth), a pole carries a small polished obsidian disc that faces the Sun, and a tilt mechanism gives about ±60° (more for other regions). Two layouts being compared (see `sim/lean_over_demo.py`, `sim/output/lean-over-vs-nod.gif`): a **nod mount** (vertical pole, disc tilts up and down every day, about 77° daily range in London) and a **lean-over mount** (pole leaned at the latitude, steady 15° per hour turn, disc angle changes only with the seasons, about ±23.4° and at most about 0.4° per day). The owner finds the lean-over option interesting but **prefers the look of the straight vertical pole, so the nod mount is the working choice (2026-11-01)**. Working concept: both motors fixed in the base, no slip ring. Azimuth motor turns a hollow vertical pole (through a reduction); a second motor drives a rod up inside the pole via a lead screw and thrust bearing; a small crank at the top turns the rod's travel into the disc's tilt (about ±62° in London, design for ±65° or more). Rod travel for ±65° with a 15 mm crank is roughly 27 mm (inference). Needs the disc hinge to sit at least a disc radius above the pole top so the disc can swing past sideways.

**Decided 2026-11-02: indoors on a table, NEMA 17 + HDP30 for each axis, 12 inch disc, to-scale drawing in `cad/media/earlier-concepts/disc-head-to-scale.png` (script `cad/src/disc_head_to_scale.py`). Draft sizes: disc centre 435 mm above the table, overall height 588 mm, base 220 mm across and 110 mm tall plus ballast, tilt drive housing 64 mm across and 68 mm long in line with the axle on the right arm. The HDP30's output is solid, so the azimuth drive sits beside the pole and turns it by belt, leaving the pole's centre free for the slip ring (inference). HDP30 size comes from its STEP files (53.8 mm across, 29.4 mm thick).**

**Smaller motors considered (2026-11-02):** NEMA 14 (about 12 to 18 N.cm holding) and NEMA 11 (about 4 to 18 N.cm) could carry the tilt axle (needs about 0.1 to 0.3 N.m) with a 5:1 to 10:1 reduction, but the HDP30 itself is 54 mm across and built for a NEMA 17 face, so it sets the housing size, not the motor. Smaller housing would need a small printed belt or planetary stage. Keep NEMA 17 + HDP30 for the first prototype.

**Geared stepper check (2026-11-02, search snippets, unverified):** ready-made NEMA 11 and NEMA 14 planetary geared steppers exist (ratios about 5:1 to 27:1; one UK listing: Phidgets NEMA 11 27:1 at £39.76 on backorder at UK RobotShop, rated only as 14 kg.cm at low speed, backlash not stated; other listings quote backlash of 1.5 to 3 degrees, far worse than the HDP30's claimed 0.03 to 0.25). Backlash matters only at tilt reversals; a light spring preload on the axle would take up slack. Metal gears avoid the HDP30's PLA creep and fatigue risk. Datasheets still to obtain.

**Geared-motor version drawn (2026-11-02):** `python3 cad/src/disc_head_to_scale.py --geared` writes `cad/media/earlier-concepts/disc-head-to-scale-geared.png`. A geared NEMA 14 (35 mm flange, 26 mm gearbox, 28 mm motor body, 5:1 listing sizes; draft) gives a tilt-drive housing about 50 mm across and 59 mm long, against 64 by 68 mm for NEMA 17 + HDP30.

**FIT0349 candidate (2026-11-02):** The Pi Hut / DFRobot FIT0349, a NEMA 17 (42 x 42 x 40 mm, 1.0 A, 3.4 V, 3600 g.cm holding) with a 5.18:1 planetary gearbox (36 mm round, about 27 mm long, 8 mm D shaft with 7 mm across the flat, shaft 15 mm long, 79.2 mm overall per the datasheet drawing), £35.10 including VAT, 10 in stock on 2026-11-02, https://thepihut.com/products/bipolar-stepper-motor-with-planet-gear-box-18kg-cm. Page quotes 18 kg.cm (1.76 N.m) 'hold torque with gearbox at 200 rpm', which equals motor holding torque times the ratio, so treat it as theoretical. Backlash and rated gearbox torque are not given. Drawing: `python3 cad/src/disc_head_to_scale.py --fit0349`. Housing about 62 mm across and 72 mm long, similar to NEMA 17 + HDP30. Datasheet copy kept in git-ignored `data/_scratch/fit0349/`.

**StepperOnline MG17-G10 option (2026-11-02, from the product page):** 10:1 spur planetary gearbox only (no motor) for NEMA 17, £10.70 (VAT treatment not stated; UK dispatch backorder +£2.16, Germany 49 and US 36 in stock with small surcharges), backlash no more than 30 arcmin (0.5 deg) no-load, max permissible torque 5 N.m, 90% efficiency, 42 mm square flange, 40 mm long, 310 g, output 8 mm shaft 21.5 mm long with keyway. The MG17 fits short-shaft (5 mm, 6.5 to 10.5 mm) motors; standard 21.5 to 25 mm shafts need the MGL17-G10 (£10.86). https://www.stepperonline.co.uk/mg-series-planetary-gearbox-gear-ratio-10-1-backlash-30arc-min-for-nema-17-stepper-motor-mg17-g10.html . Pairing with the £11 Pi Hut NEMA 17 (shaft length to be checked) would give about £22 per axle for 10:1 at about 2.3 N.m theoretical output.

**Considered and set aside (2026-11-02): a 3-DOF parallel tripod (tip-tilt platform).** It suits small tilt ranges, but the disc must face the Sun through a full turn in azimuth and about plus or minus 62 degrees of tilt, which a three-leg platform cannot reach with hobby joints, and it needs three motors instead of two. It would suit a mirror that reflects the Sun to a fixed target (half the angles), or small expressive wobbles on top of the main tracking. Revisit only if the design changes to a heliostat.

**Owner sketch, goal-post mount (2026-11-02):** a round rotating platform (azimuth) carries two metal uprights (a goal post) either side of the disc. A separate horizontal axle runs through the disc's centre and turns in bearings at the top of the uprights. A pulley near one end of the axle is driven by a short belt from the tilt stepper, which sits on the rotating platform (inside the base housing). Both axes are then independent (no coupling between azimuth and tilt), tilt has no range limit, and a slip ring under the platform feeds the rotating electronics. Inferences to check: a 330 mm belt run is hidden inside a hollow upright; a 20T to 60T belt (3:1) after a 10:1 gearbox gives about 30:1 and cuts gearbox backlash at the axle to a third; the 696 mm closed GT2 loop seen in the 123-3D listing would give about 308 mm centres; a 10 mm steel axle over about 340 mm sags well under 0.3 mm with a 1.5 kg disc; the platform must be about 350 to 400 mm across, so the base is bigger than the 220 mm drawn so far; azimuth could be a belt around the platform rim driven by a small pulley (roughly 30:1 with no gearbox). Drawn to scale for a 200 mm mirror: `python3 cad/src/goalpost_to_scale.py` writes `cad/media/earlier-concepts/goalpost-to-scale.png`. Draft layout: overall height 398 mm, axle 298 mm above the table, fixed base 360 mm across and 100 mm tall, rotating drum 44 mm tall, platform 340 mm across, uprights 40 x 20 mm hollow with inner faces 220 mm apart, tilt belt 20T to 60T over 170 mm centres (loop about 421 mm), tilt motor + 10:1 MG17-class gearbox lying along the axle in the drum, azimuth NEMA 17 + gearbox vertical in the fixed base driving a hub pulley by belt (replaces the rim-belt idea, about 45:1 with a 90T-class hub pulley), slip ring under the hub, turntable bearing ring about 260 mm (to be sized). Concept only.

**Slim base (2026-11-02):** `python3 cad/src/goalpost_to_scale.py --slim` writes `cad/media/earlier-concepts/goalpost-to-scale-slim.png`. Both motors lie on their sides in one 42 mm band (z 17 to 59): the tilt motor + 10:1 gearbox in the rotating drum, the azimuth NEMA 17 fixed outside the drum under the platform's overhang, its small pinion (20 mm) meshing a crown gear ring (about 276 mm across, teeth down, about 14:1, printed in segments) fixed to the platform underside. Base is 60 mm tall (platform top 68 mm), mirror axle 208 mm, overall 308 mm, skirt 370 mm across. Tilt belt plane moved to x = 114 mm and the drum shrunk to R 128 mm so the gearbox shaft stays inside. Open: crown gear printability and backlash (my guess about 0.2 degrees at the platform), bearing ring size (about 230 mm), slip ring length. Concept only.

**Minimal goal post and exposed metal chain (2026-11-02):** `python3 cad/src/goalpost_to_scale.py --minimal` writes `cad/media/earlier-concepts/goalpost-to-scale-minimal.png`. Uprights become two 10 mm stainless or aluminium rods (centres 218 mm apart) with the axle turning in bronze bushings in cross-holes in the rod tops. A 36-tooth sprocket on the axle end sits outside the right rod; an exposed stainless ANSI 25 roller chain (6.35 mm pitch, about 496 mm, about 78 links over 170 mm centres) runs down through a slot in the platform to a 12-tooth sprocket on the tilt gearbox shaft (3:1, about 30:1 with the 10:1 gearbox). Platform now 320 mm, drum R 132 mm, chain plane x = 120 mm, crown gear about 14.2:1, azimuth motor outer end at R 182 mm inside the 185 mm skirt. Rod stiffness (my arithmetic): a 5 N sideways push at the top deflects a 10 mm steel rod about 0.05 mm (aluminium about 0.13 mm). SAFETY: at stall the drive could pull about 190 N on the chain (0.255 N.m x 10 x 0.9 divided by the 12.25 mm sprocket radius), so current-limit the driver (still about 75 N at 40%) and guard the sprockets and the platform slot. Chain play (backlash) needs a spring tensioner; tilt reverses twice a day. Metal toothed belts: no hobby source found; chain, ball chain or an anchored cable capstan are the alternatives. Not priced.

**Small sprocket on top (2026-11-02):** `python3 cad/src/goalpost_to_scale.py --minimal --smalltop` writes `cad/media/earlier-concepts/goalpost-to-scale-smalltop.png` (10T axle sprocket, 20 mm across, exposed; 20T motor sprocket, 40.6 mm, under the platform, about 1.7 mm clear of its underside; chain about 437 mm, 68 links). The slim base's 44 mm band limits the bottom sprocket to about 20 teeth, so the step-up is at most about 2:1. Compared with 36T top / 12T bottom: overall ratio 5:1 instead of 30:1 (with the 10:1 gearbox), microstep at the axle 0.0225 deg instead of 0.0037, theoretical stall axle torque 1.16 N.m instead of 6.8 (design need about 0.3), stall chain pull 113 N instead of 187 N, gearbox backlash doubled at the axle (about 1 deg), and chain slack magnified about 3.5 times because the sprocket is smaller (1 mm of slack is about 5.6 deg at the 10T, about 1.6 deg at the 36T). 10T is below the usual roller-chain minimum and adds chordal ripple (rough estimate plus or minus 0.5 deg). A 12T top / 20T bottom compromise gives about 6:1 and about 70 links. A light spring on the axle to keep the chain taut is strongly advised.

**Airy layout, smoother chain, slew times (2026-11-02):** `python3 cad/src/goalpost_to_scale.py --minimal --airy` writes `cad/media/earlier-concepts/goalpost-to-scale-airy.png`. Mirror 200 mm with 50 mm clear to each rod (rods 310 mm apart) and 100 mm clear above the platform; axle 268 mm high, overall 368 mm; platform 360 mm, skirt about 424 mm across, 60 mm tall. Chain runs between the mirror and the right rod: 32T axle sprocket (64.8 mm), 16T motor sprocket (32.5 mm), about 614 mm, 96 links over 230 mm centres; overall 20:1 with the 10:1 gearbox, 0.0056 deg per microstep, stall chain pull about 141 N (current-limit and guard), theoretical stall axle torque about 4.6 N.m. Crown gear about 16.6:1, bearing ring about 280 mm (to be sized). Axle loads (my arithmetic, 0.5 kg mirror assumed): sag at the middle about 0.08 mm (8 mm steel) or 0.03 mm (10 mm); twist about 0.27 or 0.11 deg per N.m over 150 mm, so about 0.08 or 0.03 deg at the 0.3 N.m design load. CORRECTION: chordal ripple of a roller-chain sprocket is smaller than I first said. Numerical check of the tooth geometry gives peak angle error at the sprocket of about 0.115 deg (10T), 0.066 (12T), 0.028 (16T), 0.014 (20T), 0.008 (24T), 0.003 (32T); the 0.3 to 0.5 deg figures quoted earlier were too high. Slewing (e.g. Sun to Moon or a planet): worst case about 180 deg in azimuth and about 134 deg in tilt (Moon up to about plus or minus 29 deg declination, so tilt range about plus or minus 67 deg at London; design for plus or minus 70). Both axes move together, so time is set by azimuth: 180 deg takes 3 h at 1 deg/min, 18 min at 10 deg/min, 3 min at 1 deg/s, 90 s at 2 deg/s, 36 s at 5 deg/s. Hardware could do tens of deg/s (azimuth about 100 deg/s, tilt about 90 deg/s at a 300 rpm motor), so the limit is taste, noise and vibration. Moon and planets then track at about the Sun's 0.25 deg/min rate. Needs an ephemeris source (host Python library, or precomputed tables).

**Revised (2026-11-02): owner now prefers option A, the tilt motor in the fork, for simplicity, with a 12 inch (305 mm) disc of polished stainless sheet instead of obsidian, scaled up so the steppers are hidden. Power and encoder wires then cross the azimuth joint, so a slip ring in the base is back (12 circuits at 2 A each, priced about £21). Two NEMA 17 motors, one per axis, with modest reduction look sufficient (see reply of 2026-11-02: tilt axle load about 0.1 N.m indoors if the disc is balanced about its axle, design for 0.3). Mirror safety: keep the sheet flat on a stiff backing, since a bowed or concave sheet can focus sunlight. Earlier option C text below is kept for reference.**

**Head and drive previously chosen (2026-11-01): option C.** The disc is mounted vanity-mirror style in a Y fork whose half-circle mouth is wider than the disc, on an axle through its centre. A hollow pole turns for azimuth; a thin inner shaft, turned by the tilt motor, runs up inside it; a 90 degree mitre gear pair, a cross shaft and a short belt up one arm of the fork turn the axle. Disc tilt is the difference between the inner-shaft angle and the pole angle, so both motors turn about 360 degrees a day (fastest about 0.5 degrees per minute). Drawings: `cad/src/pole_mechanism_concept.py` (output `cad/media/earlier-concepts/pole-mechanism-concept.png`) and `sim/pole_drive_plan.py` (output `sim/output/pole-drive-plan.png`). Concept only: gear sizes, bearings, backlash and rod stiffness are not engineered. Everything below about the multi-joint arm is kept as reference; the slip ring, controller, sun-position code, reduction (HDP30 or belts) and test-rig work all still apply.

## Concept

A simple, low-cost, 3D-printed robotic arm whose end effector continuously points at the live position of the sun. Functionally a two-axis tracker would do the job; the arm is a deliberate conceptual choice. Pointing only constrains two angles (azimuth and elevation), so the remaining joints are free to shape the arm's posture, and that redundancy is where the expressive side of the work lives.

## Decisions so far

- **Custom design, not a modified existing arm.** Existing open-source arms (PAROL6, Thor, Faze4) were reviewed. PAROL6 was the reference point for quality, but it is overbuilt for this use (1kg payload, fast motion, commercial gearboxes, custom control board, mains PSU, roughly £1,000+). It is also GPLv3, so any published derivative must stay GPL. Designing fresh avoids both issues; PAROL6 remains a useful reference for mechanical ideas.
- **4 degrees of freedom:** base yaw (azimuth), shoulder pitch, elbow pitch, wrist pitch. Shoulder, elbow and wrist together set elevation, with spare freedom for posture.
- **Sun position is calculated, not sensed.** Azimuth and elevation come from latitude, longitude and time. No light sensor; works through cloud.
- **Points at the Sun 24/7, including below the horizon.** (Owner decision, 2026-11-01.) At night the arm points down through the Earth. There is no rest pose and no sunrise move; the motion is one continuous slow sweep. Elevation therefore spans roughly -62° to +62° at London's latitude (inference from lat/declination: lower culmination is about latitude + declination - 90°), and azimuth makes a full 360° circuit every day.
- **Look reference: a UR-style cobot (2026-11-01, owner's image of a Universal Robots arm, not stored in the repo).** Tubular links, round joint housings, three parallel pitch joints plus a two-axis wrist. Owner's view: only the base and the head strictly need to rotate to point; the other joints are for expressive posture. This supersedes the 4-DOF decision above in direction only: Owner chose six joints with visibly elaborate posture and is open to five. Simulation shows five give the same pointing; the sixth is decorative roll only. Do not copy the manufacturer's name, logo or exact housings.
- **Five joints, slip ring on the base.** (Owner decision, 2026-11-01.) Base yaw turns endlessly through a slip ring; the other four joints are cable-limited to about ±175°. The roll joint is dropped.
- **Table mount.** (Owner decision, 2026-11-01.) The base sits on a table with the arm rising above it. Needs a stable base footprint and enough wrist height to clear the table when pointing straight down.
- **Slow motion is a design advantage.** The sun moves about 0.25° per minute, always in one direction, so stiffness and backlash requirements are far lower than a normal robot arm.

## Target hardware (draft)

| Part | Choice | Notes |
|---|---|---|
| Motors | 4 x NEMA 17 steppers | Plenty for a light end effector |
| Reduction | Candidate: printed HDP30 harmonic drive (30:1, coaxial); fallback printed belt reduction | No commercial gearboxes. See `docs/hdp30-notes.md` |
| Drivers | 4 x TMC2209 | Silent stepping suits slow, gallery-type motion |
| Controller | ESP32 | NTP time over Wi-Fi; GPS module optional for time and location |
| Homing | Limit switch per axis | Plus align base to true north on install |
| Power | 24V external power brick | No mains wiring inside the build |
| Structure | PETG (indoors) or ASA (outdoors/window) | PLA softens in direct sun |

Parts budget: about £301 for the five-joint build with slip ring (about £230 from UK listings, £71 estimated). Likely range £250 to £320. See `bom/bom-uk-draft.csv` and `docs/bom-notes.md`. Supersedes the earlier £150 to £250 guess.

## Software approach

1. **Sun position:** NREL SPA or pysolar (Python), or an equivalent C implementation on the ESP32.
2. **Direction vector:** convert azimuth and elevation into a 3D unit vector in the arm's base frame (base aligned to true north).
3. **Inverse kinematics:** solve joint angles so the end effector axis lies along that vector. Base yaw = azimuth; remaining pitch joints solved with a chosen posture rule (fixed pose, slow drift, or end effector held in place while the arm reshapes). ikpy or roboticstoolbox-python for prototyping.
4. **Motion:** update every few seconds with smooth, slow interpolation.
5. **Day/night behaviour:** none needed. The Sun vector is tracked continuously, with elevation going negative at night. The IK must cope with pointing below the base plane and with the daily azimuth wrap (see open questions).

Open architecture choice: run everything on the ESP32 (standalone, robust for installation) or run sun maths and IK in Python on a host (Pi or laptop) and stream joint targets to the ESP32 (faster to develop). Suggest prototyping host-side, then porting to standalone.

## Suggested repo structure

```

  README.md
  HANDOVER.md
  cad/            # parametric model (OpenSCAD or CadQuery), STLs exported to cad/out/hinge-mirror/parts/test-rig
  firmware/       # ESP32 (PlatformIO): steppers, homing, serial/Wi-Fi commands
  host/           # Python: sun position, IK, posture logic, simulation
  sim/            # visualise sun path and arm poses before building
  bom/            # priced UK bill of materials (CSV)
  docs/           # wiring, assembly, calibration notes
```

## Open questions

- Height and reach of the arm
- Indoors, window, or outdoors (sets material and weatherproofing)
- What is on the end: bare pointer, mirror, light, other (sets precision and load)
- Aesthetic: industrial or sculptural
- Site: London (decided). Bare pointer end effector (decided).
- Posture behaviour: what the spare joints should do
- Table clearance: with the arm pointing straight down, the wrist must sit higher above the table than the pointer is long. Size link lengths and pointer length in the simulation (inference, not yet modelled)
- Daily azimuth wrap: six-joint simulation shows the base yaw turns about 365° per day and the other joints stay within ±175°. Choose a slip ring on the base (possibly with the controller on the rotating stage) or a once-a-day unwind. See `docs/simulation.md`
- Repo licence

## Next steps

0a. Evaluate the HDP30 (printed 30:1 harmonic drive, CC BY-SA 4.0) as the joint reduction: build one on the test rig and compare with the belt (see `docs/hdp30-notes.md`). Key risks: 1.5 N.m ceiling, PLA creep and fatigue.

0. Test rig drafted (`docs/test-rig.md`, `cad/src/test_joint_rig.py`): print and build it, then measure backlash, smoothness and heat before committing to a reduction type.

1. Answer the open questions above.
2. DONE (first pass): simulation in `sim/arm_sim.py`, results in `docs/simulation.md`. Next: design a more expressive posture rule, and settle link lengths.
3. Parametric CAD of joints and links.
4. Price the BOM.
5. Firmware for one axis, then all four, then homing.
6. Integrate sun position and IK; calibrate north alignment.

## References

- PAROL6 (reference design): https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm
- Thor: https://github.com/AngelLM/Thor
- Faze4: https://github.com/PCrnjak/Faze4-Robotic-arm
- Helioduino (open-source solar tracking controller): https://github.com/topics/solar-tracker

## Option explored 2026-11-02: pedestal (vanity mirror) mount
Prompted by a photo of a dressing table mirror, because the goal post version had grown to a 480 mm base.
Drawing: `cad/src/pedestal_to_scale.py` -> `cad/media/earlier-concepts/pedestal-to-scale.png` (draft sizes, nothing tested).
- Round fixed base 250 x 70, one thin pole (17 mm tube with a 6 mm rod inside), U shaped fork, mirror in a bezel ring (about 212 mm) with two pivot pins at its sides. Pivot axis 314 mm up, overall 420 mm. Floor area about 27% of the goal post version.
- Concentric drive: tube = azimuth, rod = tilt, both motors lie flat in the base (bevel gears), so the controller stays fixed and NO slip ring is needed. Mirror tilt = 0.5 x (rod angle minus tube angle), so firmware moves the rod with the tube.
- Top: bevel pair, cross shaft in the fork bridge, ANSI 25 chain (32T/16T, 64 links, about 406 mm) on the outside of the right arm turns the right pin.
- Open: precision of two coaxial bearings, bevel backlash, ballast and tipping, whether the user prefers this to the goal post. Goal post CAD brief (`docs/cad-brief.md`) is on hold until they choose.

## Option explored 2026-11-02: hinged flat mirror on a turntable (easel / laptop lid style)
Prompted by a photo of a rectangular table mirror on a wedge. Drawing: `cad/src/hinge_to_scale.py` -> `cad/media/earlier-concepts/hinge-to-scale.png` (draft, untested).
- Rectangular mirror (200 x 200 drawn) hinged along its bottom edge on top of a turning drum, hinge on the azimuth axis. Base about 250 x 66, overall 276 mm upright.
- Tilt: NEMA 17 + 10:1 gearbox lying along the hinge inside the drum, GT2 belt 16T to 32T (2:1), 20:1 overall, 0.0056 deg per microstep. No fork, chain, axle through the mirror or concentric shafts.
- Azimuth: as the goal post (motor on the drum, power through a slip ring). Azimuth drive and slip ring layout inside a 250 mm base NOT yet worked out (goal post used a radial motor outside the drum, which widened the base).
- Hinge always above the base top so the mirror never hits it, range up to +/-90 deg. Corner sweep: 406 mm across at 62 deg tilt, 447 flat. Gravity torque flat, 0.7 kg assumed: 0.69 N.m (fine). It reverses at upright, so expect a small backlash flop at sunrise and sunset unless a counterweight or spring is added.
- Silhouette changes a lot: upright at the horizon, reclined at high Sun, leaning forward and face down for a below horizon Sun (choose a night pose).
- Comparison (upright height, base): goal post 368 and 480, pedestal 420 and 250 (no slip ring), hinge 276 and 250.

## DECISION 2026-11-02: go with the hinged flat mirror, first-pass CAD built
User chose the hinge design with a 3:4 (portrait) rectangular mirror, 200 x 267 mm. CAD: `cad/src/hinge_mirror.py` -> `cad/out/hinge-mirror/assembly/hinge-mirror-assembly.step` (and .glb, previews). Full detail in `docs/cad-brief.md`.
Changes found while detailing it (honest corrections to the earlier hinge drawing):
- A GT2 belt on the hinge is overloaded (1.0 kg mirror, 267 mm tall: 1.43 N.m flat, 139 N belt force). Changed to the ANSI 25 chain (32T/16T, 44 N). That put the hinge axis at 95.8 mm and the chain outside the right hand hinge block, so the base is 262 mm, not 250.
- Azimuth changed to a belt around a FIXED 160T hub pulley with a standing NEMA 17 on the drum (10:1, no backlash, fits the base). Not yet reviewed by the user.
- Overall height upright 379 mm. Mirror corners reach 256 mm from the axis at 62 deg tilt.
Next: user explores the STEP in Fusion; open points are listed in `docs/cad-brief.md`.

## Explored 2026-11-02: hiding the hinge (not yet in the CAD)
User found the exposed hinge (shaft, blocks, chain, sprocket, encoder) ugly. Drawing: `cad/src/hidden_hinge_concept.py` -> `cad/media/earlier-concepts/hidden-hinge-concept.png`.
- Recommended: barrel hinge with its axis level with the drum top plate. A 24 mm half round bar sits in a groove in the plate, the mirror frame clamps into the bar, bearings live in the bar's fixed end housings. Everything else is inside the drum.
- Drive hidden inside: sector worm wheel (teeth only below the hinge line, so it never rises above the plate) on the shaft end, worm below it, NEMA 17 lying along Y at Z about 41. Worm is self-locking (also cures the sunrise/sunset flop). About 27:1, about 0.004 deg per 1/16 microstep. Tooth force about 70 N on a brass wheel (module 1.5, 8 mm wide). Encoder (AS5600) at the left shaft end inside the drum. Chain, sprocket, blocks, lugs all removed.
- Overall height about 354 mm (was 379). Mirror can lie flat on the plate at 90 deg.
- A sunk hinge instead needs a V notch of width 2 x depth x tan(tilt): 45 mm wide for 12 mm depth at 62 deg, and cannot lie flat. Rejected.
- Total concealment is impossible: the mirror has to emerge from the base, so the bar (or a notch) always shows.

## DONE 2026-11-02: CAD rebuilt around the hidden hinge (v2)
`cad/src/hinge_mirror.py` -> `cad/out/hinge-mirror/assembly/hinge-mirror-assembly.step` (v1 exposed version archived as `*_v1_exposed*`). Details in `docs/cad-brief.md`.
Changes from the concept drawing: the worm drive was dropped (a gear on the shaft rises above the top plate when the mirror tilts). Replaced by a crank arm on the shaft, a pin sliding in a vertical slot in a yoke on a lead screw nut, driven by a NEMA 17 along Y. Everything is below the plate. Tilt limited to +/-70 deg, height 360 mm.
Next: user explores in Fusion; open points are in the brief (idler for the azimuth belt, bar clamp detail, real mirror mass, brackets and fasteners).
