> **Status: stale (2026-11-03).** Draft BOM for the five-joint arm. The current parts list is `bom-v4.md`; this and `bom/archive/arm-v4/bom-uk-draft.csv` are kept for history.

# Draft UK bill of materials (2026-11-01)

File: `bom/archive/arm-v4/bom-uk-draft.csv`. Five joints, slip ring on the base, 24 V supply, ESP32 on the rotating stage.

**Draft total: about £301**, of which about £230 comes from UK web listings and about £71 is my estimate where I found no UK price. Likely range £250 to £320 (inference). This replaces the earlier £150 to £250 guess for four joints.

## How reliable are the prices
- Prices came from web search snippets on 2026-11-01. I did not open each shop page, so VAT treatment, stock and delivery are unchecked. Re-check before ordering.
- Not found in UK shops: NEMA 17 at other lengths, AS5600 modules, hall sensors, limit switches, bearings. Those lines are estimates.
- 123-3D prices for GT2 pulleys and belts look high; multi-packs elsewhere are probably cheaper (not verified), which could save about £30 to £40.
- Generic TMC2209 modules vary in quality; genuine branded ones may cost more.
- The 2 A rating is per slip-ring circuit. Use several circuits in parallel for the 24 V and ground feed.

## Not included
3D printer, tools and soldering kit, delivery charges, spare parts beyond those listed, mounting plate or table finish, and any paint or finishing.

## Design issue found while pricing
The slip ring sits on the base axis, so a magnetic encoder cannot go on the yaw axis. Use a hall sensor as a once-per-turn index and count steps for yaw (inference, to be tested).
