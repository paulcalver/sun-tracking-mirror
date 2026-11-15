# Spinning mirror, 150 mm test rig on a NEMA 17 (2026-11-15)

Draft CAD, nothing printed or tested. Script: `cad/src/spinning_mirror_150_nema17.py` (`--check` for clashes). Same concept as the GM2804 versions (free hinge, jittering motor speed, option D on the concept page), scaled up and driven by a stepper.

## Why a NEMA 17
- A 150 mm mirror and its ring need about 3.4e-4 to 4.8e-4 kg m2 about the spin axis (solid-print figures, so real parts are 20 to 30 % lighter). 100 rad/s2 needs about 0.05 N m and 300 rad/s2 about 0.14 N m.
- The GM2804 gives 0.025 to 0.034 N m and the GM3506 is out of stock. The motor chosen is The Pi Hut NEMA 17 42/60 (in stock): 1.68 A, 1.65 ohm, 6.2 mH, 6.5 kg cm (0.64 N m) holding, rotor inertia 102 g cm2 (1.0e-5 kg m2, small next to the load), 0.5 kg, detent 280 g cm. Its listed 5.1 V rated voltage does not match 1.68 A x 1.65 ohm (2.8 V); ignore it, the driver sets the current.
- Torque at speed (my estimate, not measured): at 24 V the current can just follow a 300 rpm step rate (about 3800 A/s needed against 24 V / 6.2 mH = 3900 A/s, less back-EMF of about 8 V), so expect roughly 0.3 to 0.4 N m at 300 rpm and the full value below 150 rpm. That is 2 to 3 times the 0.14 N m needed for 300 rad/s2. On 12 V the useful range is about half. The 34 mm (about 0.28 N m) and 40 mm (about 0.45 N m) versions were considered and are weaker.
- Heat: 2 x 1.68 A squared x 1.65 ohm is about 9 W at full current, and the motor is enclosed. Run the driver at 1.2 to 1.5 A (about 5 W, still about 0.45 N m holding) and the pedestal walls have vent slots.
- Loads: ring weight 1.7 N against 10 N axial limit; radial limit 28 N, shaft play 0.08 mm axial.
- Speed is what matters, not position, so it runs open loop on step and direction. A stalled or slipped step only slows the ring.
- The flash: the reflected beam turns at twice the mirror rate, so at 3 m a 100 rpm spin gives a flash of about 3 ms and 300 rpm about 1 ms. Plan on 60 to 300 rpm with the jitter; higher speed makes each flash shorter, not brighter.

## Layout
- Pedestal 150 x 150 mm, top at 74 mm (14 mm plus the motor body). The motor hangs under the 6 mm top plate with its shaft up (four M3 screws from above, heads counterbored), the pilot boss in the plate hole. Open-bottom shell, print it upside down; a 3 mm lid with four countersunk M3 into inserts in corner posts; about 350 g of steel washers in a ring around the motor (the motor is 0.5 kg itself); wire notch in the front wall and three vent slots in each side wall.
- Hub 35 mm x 15 mm clamps the 5 mm D shaft with two M3 grub screws (one on the flat) into heat-set inserts. The ring foot nests 2.5 mm into a pocket in the hub top and is held by two M3 x 16 from inside the ring.
- Ring 158 / 169 mm, 12 mm wide, boss face 1.5 mm from the mirror rim, 4 mm axle on two 684ZZ. Carrier has a rim, cross bars and an inner support ring so the thin discs stay flatter. Two 150 mm acrylic discs, 1.5 mm, one each side. Brass slug 8 x 5 at 54 mm.
- Ring centre 182.5 mm above the table, top of the ring 267 mm. Spinning load 176 g, whole rig about 1.5 kg with the motor.
- Change `MIR_R` in the script to rescale ring, axle and weight pad (`MIR_R = 50` gives a 100 mm version on the same motor).

## Checks run
- 24 tilt angles: 0 clashes. Static pose: 0 clashes. Every printed part is a single solid.

## Open
- No top support on this rig. A 5 mm shaft carries a 170 mm ring about 115 mm above the motor face; if it wobbles, add a top pin and bar like the trio.
- Whether 1.5 mm acrylic stays flat at 150 mm; buy a sample first.
- Stepper step-resonance and hum with jittering speed; limit acceleration in firmware and check around the resonance rpm.
- Shaft length (assumed 24 mm, not in the listing), flat length and front-face thread depth: the model is a generic NEMA 17 body at the listed 60 mm, not a vendor STEP. Check the hub bore and the M3 x 8 screw length.
- Wire order on the connector may not match the driver (the listing warns); check coil pairs with a multimeter.
- Print the ring in PETG or ASA at 4 walls; tolerances on the bearing pockets (9.1 mm).
