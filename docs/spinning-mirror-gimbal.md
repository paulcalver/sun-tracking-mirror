# Spinning mirror gimbal (2026-11-14)

Draft CAD, nothing printed or tested. Model: `cad/src/spinning_mirror.py` (`--check` runs a tilt sweep for clashes). Concept and the four drive options: `spinning-mirror-gimbal-concept.html` (this is option D).

## Idea
A 60 mm round mirror on a free horizontal hinge inside a ring. One brushless gimbal motor spins the ring about the vertical axis with a randomly jittering speed, and nothing drives the hinge. At steady speed the mirror would settle flat; with the speed wobbling it swings and tumbles at random (see the page, option D, for the model).

## Parts (all values are parameters at the top of the script)
| Part | Process | Notes |
|---|---|---|
| Base puck 110 mm, floor plate | print | Underside pocket takes about 150 g of steel washers, cable notch at the rim, 4 inserts for the floor plate |
| Hub adapter 34 mm | print | Screws to the bell top (4 x M2.5) and takes the ring foot (2 x M3) |
| Ring with foot, 68 / 78 mm | print, PETG, flat | Axle bosses with 683ZZ pockets opening to the inside; 4 balance screw holes |
| Mirror carrier | print | 60 mm rim, 6 mm bar, weight pad at 22 mm; 3 mm bore for the axle |
| Gimbal motor 2804 | buy | Bell size and bolt circles are ASSUMED, check the datasheet |
| 2 x 683ZZ, 3 mm axle, 2 x 60 mm acrylic mirror, brass slug 6 x 5 | buy | |

Assembly order: press the bearings into the ring from inside, place the carrier in the ring, slide the 3 mm axle through bearing, carrier and second bearing, glue it to the carrier. The carrier hubs trap the axle between the bearings (0.2 mm end float).

## Numbers
Ring centre 100 mm above the table, ring top 139 mm. Spinning load on the motor about 43 g (carrier group 25 g), base about 450 g with ballast. Mirror to ring clearance 3.7 mm worst case (checked at 24 tilt angles, no clashes); ring boss face to mirror rim 1.5 mm.

## Open
- Motor dimensions and bolt circles (assumed).
- Print tolerances on the bearing pockets (7.1 mm) and the 4.0 mm clearance hole for the axle.
- Hinge friction with real bearings, and whether the random tumbling matches the page's model.
- Balance: trim with the four ring screws; set the weight slug (brass, steel, aluminium or none).
