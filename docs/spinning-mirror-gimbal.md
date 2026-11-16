# Spinning mirror gimbal, single unit (updated 2026-11-14)

> Primary route from 2026-11-15: 150 mm mirrors on NEMA 17 steppers, see `spinning-mirror-150-nema17.md`. This brushless GM2804 version is the alternative.

Draft CAD, nothing printed or tested. Model: `cad/src/spinning_mirror.py` (the unit; `--check` sweeps the mirror tilt for clashes) and, for the rigs with the top support, `cad/src/spinning_mirror_row.py`. Concept and the four drive options: `spinning-mirror-gimbal-concept.html` (this is option D).

## Idea
An 80 mm round mirror on a free horizontal hinge inside a ring. One brushless gimbal motor spins the ring about the vertical axis with a randomly jittering speed, and nothing drives the hinge. At steady speed the mirror would settle flat; with the speed wobbling it swings and tumbles at random.

## Motor (real, from the vendor STEP in `cad/src/assets/ipower-gm2804-as5048a.step`)
iPower GM2804 with AS5048A encoder: 35 mm diameter, 26.15 mm tall (stator housing 13.4 mm below, rotor bell 12.75 mm above), 6.5 mm hollow shaft through the stator. The stator is fixed, the bell turns with the ring.
- Bottom face: 4 blind holes 2.4 x 3.5 mm on a 15.8 mm circle (not evenly spaced). In the CAD, M2 screws come up from the underside through the base and boss.
- Bell top: 4 holes on a 26 mm circle (countersunk, 2.4 mm) take the hub with M2 screws, and 4 more on a 19 mm circle. Whether any of them are threaded is not stated, so check the part.
- Specs from the maker: 9 ohm, 1600 to 1770 rpm no load at 10 V, 250 to 350 g cm at 0.8 A, 42 g.

## Parts (all values are parameters at the top of the script)
| Part | Process | Notes |
|---|---|---|
| Base puck 110 mm, floor plate | print | Single-unit variant only. Underside pocket for about 150 g of steel, cable notch |
| Hub adapter 35 mm x 6 | print | 4 x M2 into the bell top, 2 x M3 heat-set inserts that take the ring screws |
| Ring with foot, 88 / 98 mm, 10 wide | print, PETG, flat | Axle bosses with 683ZZ pockets opening to the inside; 4 balance screw holes; two M3 x 16 from inside the ring into the hub |
| Mirror carrier | print | 80 mm rim, two 6 mm bars (axle and cross), weight pad at 29 mm, 3 mm bore |
| 2 x 683ZZ, 3 mm axle (98 mm), 2 x 80 mm acrylic mirror 2 mm, brass slug 6 x 5 | buy | |

Assembly order: screw the ring to the hub from inside the ring, press the bearings in from inside, place the carrier, slide the 3 mm axle through and glue it to the carrier. Carrier hubs trap the axle between the bearings (0.2 mm end float).

## Numbers
- Ring centre 116 mm above the table, ring top 165 mm. Mirror to ring clearance 3.7 mm worst case (checked at 24 tilt angles, no clashes); boss face to mirror rim 1.5 mm.
- Spinning load on the motor 80 g (hub, ring, bell, bearings 39 g; carrier, mirrors, weight 40 g). Inertia about the spin axis 4.5e-5 (mirror in the ring plane) to 6.0e-5 kg m2 (flat), including the bell.
- At the vendor's 0.0245 N m (low end of the load test) that is about 400 to 540 rad/s2, so a 100 rpm change takes roughly 20 to 26 ms before back-EMF derating. Plan on half that torque at several hundred rpm.

## Open
- Which motor holes are threaded.
- Print tolerances on the bearing pockets (7.1 mm) and the 4 mm clearance hole for the axle.
- Hinge friction with real bearings, and whether the tumbling matches the page's model.
- Balance: trim with the four ring screws; set the weight slug (brass, steel, aluminium or none).
- Motor rotor inertia is in the numbers only as the CAD volume of the bell (density set so the motor weighs 42 g); the real rotor mass distribution may differ.
