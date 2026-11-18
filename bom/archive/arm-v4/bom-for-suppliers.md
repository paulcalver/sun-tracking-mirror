# Parts to buy: plain list for a UK supplier search (2026-11-03)

Project: a small indoor motorised mirror sculpture (two stepper motors, a Raspberry Pi Pico, a turntable bearing, a lead screw). Hobby use, bought once. Please find UK suppliers (or ones that ship to the UK). For each line give: best supplier, exact product link, price including VAT, delivery cost, stock, and one cheaper or better alternative if there is a clear one. Flag anything that does not match the spec.

Items marked **HARD** have no UK supplier found yet.

## Motion and structure

| # | Item | Qty | Spec that must match | Notes |
|---|---|---|---|---|
| 1 | NEMA 17 stepper motor | 2 | 42 x 42 mm frame, body 34 mm (up to 40 mm is fine), 1.5 A or less per phase, 5 mm D shaft, shaft at least 22 mm long, bipolar 4 wire | Plain motors, no gearbox. Check the shaft length. Known: The Pi Hut, 11 pounds. |
| 2 | Lazy Susan turntable bearing, 9 inch | 1 | ID 114.3 mm, OD 228.6 mm, thickness about 8.3 mm, steel ball bearing | Need the **mounting hole pattern** (pitch circle diameters, hole size) if any listing gives it. Known: Bearing King, 10.61 pounds. |
| 3 | Slip ring with flange | 1 | 22 mm body, 12 wire, 2 A, flange about 44 mm, at least 300 rpm | Need body length and flange hole pattern if given. Known: The Pi Hut, 17.40 pounds. |
| 4 | **HARD** TR8x2 lead screw | 1 | 8 mm diameter, **2 mm lead, single start** (not the common T8x8 with 8 mm lead), 150 mm or longer (cut to length is fine) | Known source is Tinytronics in the Netherlands. Looking for a UK or EU seller that ships to the UK; 200 to 300 mm lengths are fine. |
| 5 | **HARD** TR8x2 nut | 1 | Brass or bronze nut for item 4, flanged or round, anti-backlash welcome | If none, a UK source for a 2 mm lead, 8 mm screw and nut as a set. |
| 6 | Flexible shaft coupler | 1 | 5 mm bore to 8 mm bore | Motor shaft to lead screw. |
| 7 | GT2 timing pulley | 1 | 20 teeth, 5 mm bore, **6 mm belt width**, aluminium, grub screws | Known: 123-3D, about 6.50 pounds. |
| 8 | **HARD** GT2 closed-loop timing belt | 1 | 6 mm wide, 2 mm pitch, **200 mm length (100 teeth)** | Also acceptable: any length from 188 to 208 mm (say which exist, the layout can adapt). |
| 9 | Ball bearing 685ZZ | 2 | 5 x 11 x 5 mm | A small pack is fine. |
| 10 | Ball bearing 688ZZ | 1 | 8 x 16 x 5 mm | A small pack is fine. |
| 11 | Steel rod, 5 mm | about 40 mm in total | Silver steel or stainless, 5 mm diameter | Cut into two short pieces. |
| 12 | Steel rod, 4 mm | 1 piece, 115 mm | Silver steel or stainless, 4 mm diameter | |
| 13 | Bolt M6 x 25 mm with nut | 1 | Stainless or steel | |
| 14 | Neodymium disc magnet | 2 | 5 mm diameter x 2 mm thick | A pack of 10 or more is fine. |

## Electronics

| # | Item | Qty | Spec that must match | Notes |
|---|---|---|---|---|
| 15 | Raspberry Pi Pico | 1 | RP2040, **no Wi-Fi** (plain Pico, not Pico W), with or without headers | |
| 16 | DS3231 real-time clock module | 1 | I2C, with CR2032 battery holder | The usual small blue module is fine. |
| 17 | TMC2209 stepper driver module | 2 | StepStick / A4988 footprint, V2 or V3 | With header pins. |
| 18 | DC-DC buck converter | 1 | Input 24 V, output 5 V, at least 1 A | Powers the Pico. |
| 19 | Digital Hall effect sensor module | 2 | 3.3 V compatible, digital output (A3144 or similar breakout) | Reads a small magnet for the home position. |
| 20 | GY-271 compass module | 1 | I2C magnetometer (HMC5883L or QMC5883L, either is fine) | |
| 21 | 24 V DC power supply | 1 | 24 V, 5 A (3 A minimum), mains in, UK plug, CE or UKCA marked | |
| 22 | Hook-up wire, connectors, screw terminal block | 1 set | About 22 to 26 AWG, a few colours; Dupont and JST connectors | |

## Fasteners and consumables (quantities approximate)

| # | Item | Qty | Notes |
|---|---|---|---|
| 23 | Brass heat-set inserts, M3 | about 40 | Short type, 4 to 5.7 mm long, for 3D printed PETG parts |
| 24 | Brass heat-set inserts, M2 | 4 to 10 | Short type, for mounting the Pico |
| 25 | Screws, M3 | about 40 | Mixed lengths: 6, 8, 12, 16 mm |
| 26 | Screws, M2 | 10 | 6 to 8 mm |
| 27 | Screws and nuts, M4 | 10 | 8 to 20 mm |
| 28 | Glass adhesive | 1 tube | For bonding mirror glass to a printed part: clear silicone or two-part epoxy |
| 29 | Ballast, about 1.5 kg | 1 | Steel washers or bolts; must fit in a 300 mm square box |

## Materials

| # | Item | Qty | Spec | Notes |
|---|---|---|---|---|
| 30 | Mirror glass | 1 | **6 mm** silvered float glass mirror, cut to 200 x 267 mm, **polished edges** (the edge stays exposed), no safety backing; **the back must be black** (ask for a black-painted back, or spray it matt black yourself over the silvering) | UK made-to-measure glass shop. Give a quote route or price calculator. Many have a minimum charge. |
| 31 | PETG filament (or ASA), 1 kg | 1 | 1.75 mm, black or dark grey | For a Bambu Lab P1S. |
| 32 | Sheet for laser cutting | about 0.4 m2 | 6 mm plywood or cast acrylic (black if possible), plus about 0.15 m2 of 3 mm | Only needed if my laser cutter lab does not stock it. |

## What I most need answered
1. UK sources for items 4, 5 and 8 (lead screw, nut, belt).
2. Mounting hole patterns for items 2 and 3.
3. The cheapest trustworthy UK basket for items 15 to 21 (for example The Pi Hut, Pimoroni, Cool Components, Kitronik, RS, Farnell).
4. Total basket cost per supplier.
