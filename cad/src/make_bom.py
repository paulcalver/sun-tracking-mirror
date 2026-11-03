#!/usr/bin/env python3
"""Bill of materials for the v4 hinged mirror, split into laser cutting / 3D printing / purchase.

Part sizes and print volumes come from the CadQuery model (hinge_mirror.py), so they follow the CAD. Purchased items and
prices are listed here by hand (see docs/parts-sourcing.md for the sources and their status).

Usage (from the repo root): python3 cad/src/make_bom.py
Writes bom/bom-v4.csv and docs/bom-v4.md.
"""
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hinge_mirror as m  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PETG_G_CM3 = 1.27

m.build()
allparts = {nm: _w for lst in (m.base_parts, m.drum_parts, m.slider_parts, m.mirror_parts) for nm, _w, _c in lst}


def bbox(nm):
    b = m._shape(allparts[nm]).BoundingBox()
    return b.xlen, b.ylen, b.zlen


def vol_cm3(nm):
    return m._shape(allparts[nm]).Volume() / 1000.0


def dims(nm):
    x, y, z = sorted(bbox(nm), reverse=True)
    return f"{x:.0f} x {y:.0f} x {z:.0f}"


# ---------------------------------------------------------------- laser cutting (6 mm max, ply or acrylic, no metal)
wall_h = m.PLATE_Z0
laser = [
    ("Base floor (sits loose inside the cover, on the table)", 1, "6 mm ply or acrylic", f"{2 * m.FLOOR_HALF:.0f} x {2 * m.FLOOR_HALF:.0f} x 6", f"Engrave (top face, {m.ENG:.0f} mm deep): six bearing post pockets, DXF base_floor_plate_6mm_engrave. Bolt holes for the bearing and slip ring still to be added. Felt pads underneath"),
    ("Cover wall, long, front", 1, "3 mm ply or acrylic, black", f"{2 * m.WW:.0f} x {wall_h + m.ENG:.1f} x 3", f"Plain rectangle; the top {m.ENG:.0f} mm sits in the groove under the frame. DXF wall_panel_long_front. Felt strip on the bottom edge"),
    ("Cover wall, long, back", 1, "3 mm ply or acrylic, black", f"{2 * m.WW:.0f} x {wall_h + m.ENG:.1f} x 3", f"As the front, with a {m.WALL_NOTCH:.0f} mm cable notch in the bottom edge. DXF wall_panel_long_back_notch"),
    ("Cover wall, short (left, right)", 2, "3 mm ply or acrylic, black", f"{2 * (m.WW - m.WALL_T):.0f} x {wall_h + m.ENG:.1f} x 3", "Fits between the long panels; corners butt and are glued. DXF wall_panel_short"),
    ("Cover top frame", 1, "6 mm ply or acrylic, black", f"{2 * m.BASE_HALF:.0f} x {2 * m.BASE_HALF:.0f} x 6", f"Round hole {2 * m.HOLE_R:.0f} dia round the turntable. Engrave the wall groove in the underside (file is mirrored: turn the sheet over about Y), then cut. Walls glue in, inset {m.WALL_INSET:.0f} mm; the whole cover stands on the table"),
    ("Drum floor", 1, "6 mm ply or acrylic", f"{2 * m.DRUM_R:.0f} dia x 6", f"Holes: 24 dia centre (slip ring), 23 dia motor boss. Engrave (top face, {m.ENG:.0f} mm deep): pockets for the pillars, controller tray legs, compass post, Hall column and the two tilt blocks. Mount holes for the bearing and motors to be added"),
    ("Drum top plate (lid)", 1, "6 mm black acrylic or ply", f"{2 * m.DRUM_R:.0f} dia x 6", f"Slot 242 x 19.2 and a 16.4 x 90.4 rectangular hole for the printed relief insert. Engrave the six pillar pockets in the underside (mirrored file, sheet turned over about Y)"),
]
# ---------------------------------------------------------------- 3D printing (P1S, 256 x 256 x 256, PETG or ASA)
groups = [
    ("Fixed 80T GT2 hub pulley (teeth need a test print)", ["hub_pulley_GT2_80T_fixed"], 1, ""),
    ("Hinge bar, 18 mm half round with glass slit", ["hinge_bar_18mm"], 1, "Print flat; may twist about 1 deg (see cad-brief); consider a stiffening rod"),
    ("Hinge end housing", ["hinge_end_housing_left", "hinge_end_housing_right"], 2, "Left and right are mirror images"),
    ("Crank arm", ["crank_arm_40mm"], 1, "5 x 2 mm magnet pocket"),
    ("Tilt yoke block", ["tilt_yoke_block"], 1, "Slot open at the top; sliding fits to tune"),
    ("Arm relief insert (fills the plate hole)", ["drum_arm_relief_insert"], 1, "Print black; glued flush in the top plate"),
    ("Screw end block", ["tilt_screw_end_block"], 1, "Holds the 688 bearing and the guide rod"),
    ("Guide rod support block", ["tilt_guide_support_block"], 1, ""),
    ("Hall sensor column", ["tilt_home_hall_column"], 1, ""),
    ("Bearing post (under the lazy Susan)", [f"bearing_post_{i}" for i in range(1, 7)], 6, f"{m.ENG:.0f} mm tenon on the bottom glues into a floor pocket; bolt holes to match the real bearing"),
    ("Drum pillar (floor to lid)", [f"drum_pillar_{i}" for i in range(1, 7)], 6, f"{m.ENG:.0f} mm tenon each end glues into a pocket in the drum floor and the top plate"),
    ("Floor locator (centres the floor in the cover)", ["floor_locator_1", "floor_locator_2", "floor_locator_3", "floor_locator_4"], 4, "14 x 14 x 8 corner block, glued on the floor 0.2 mm from the walls"),
    ("Controller tray (plate with four legs)", ["controller_tray"], 1, "4 x M3 heat-set inserts in the leg bottoms, 4 x M2 inserts for the Pico; clock, drivers and buck mounting to be set once the modules are in hand"),
    ("Compass post", ["compass_post"], 1, ""),
]
printed = []
solid_g = 0.0
for label, names, qty, note in groups:
    v = sum(vol_cm3(n) for n in names)
    solid_g += v * PETG_G_CM3
    printed.append((label, qty, "PETG or ASA", dims(names[0]), note))

# ---------------------------------------------------------------- purchase (unit_gbp None = not looked up yet)
# (item, qty, spec, unit_gbp, confidence, source or note)
buy = [
    ("NEMA 17 stepper 42 x 34 mm, 1.5 A", 2, "2.6 kg.cm, D shaft (length to check, model assumes 24 mm)", 11.00, "sourced 2026-11-03", "Pi Hut, in stock: https://thepihut.com/products/nema-17-stepper-motor-42mm-x-34mm"),
    ("Lazy Susan bearing, 9 inch", 1, "ID 114.3, OD 228.6, 8.33 thick, bolt pattern unknown", 10.61, "sourced 2026-11-03", "Bearing King, in stock: https://bearing-king.co.uk/products/9-inch-lazy-susan-turntable-bearing-round"),
    ("Slip ring with flange, 22 mm, 12 wire, 2 A", 1, "44 mm flange, 6 inch wires, 300 rpm", 17.40, "sourced 2026-11-03", "Pi Hut, in stock: https://thepihut.com/products/slip-ring-with-flange-22mm-diameter-12-wires-max-240v-2a"),
    ("GT2 pulley 20T, 5 mm bore, 6 mm belt", 1, "aluminium, two grub screws", 6.50, "earlier BOM, not rechecked", "123-3D"),
    ("GT2 closed belt loop 6 mm, 200 mm (100 teeth)", 1, "stock size", 3.50, "estimate", "UK shop not confirmed; 380 and 400 mm sizes were found, 200 mm is a standard length"),
    ("TR8x2 lead screw, 2 mm lead, about 150 mm cut or 300 mm", 1, "single start, 8 mm", None, "no UK source", "Tinytronics (Netherlands): https://www.tinytronics.nl/en/mechanics-and-actuators/parts/lead-screws"),
    ("TR8x2 brass nut", 1, "2 mm lead", None, "no UK source", "Tinytronics: https://www.tinytronics.nl/en/mechanics-and-actuators/parts/lead-screws/tr8x2-leadscrew-nut"),
    ("Shaft coupler 5 to 8 mm", 1, "", 2.00, "estimate", "not researched"),
    ("Bearing 685ZZ (5 x 11 x 5)", 2, "hinge stubs", 2.00, "sourced, low confidence", "eBay UK listing, 2 for 3.99 pounds; RS sells only bulk packs"),
    ("Bearing 688ZZ (8 x 16 x 5)", 1, "screw end", 1.00, "estimate", "https://uk.rs-online.com/web/p/ball-bearings/0644241"),
    ("Steel rod 5 mm, about 20 mm pieces", 2, "hinge stubs", 1.00, "estimate", ""),
    ("Steel rod 4 mm, 114 mm", 1, "guide rod", 1.00, "estimate", ""),
    ("M6 bolt, 25 mm, with nut", 1, "crank pin", 0.50, "estimate", ""),
    ("Magnet 5 x 2 mm", 2, "tilt home (arm) and azimuth home (drum floor)", 1.00, "estimate", ""),
    ("Hall sensor board (digital)", 2, "tilt home and azimuth home", 2.00, "estimate", "e.g. A3144 or similar breakout"),
    ("Raspberry Pi Pico (RP2040, no radio)", 1, "", 4.00, "estimate", ""),
    ("DS3231 real-time clock module", 1, "with coin cell", 3.00, "estimate", ""),
    ("TMC2209 stepper driver (StepStick)", 2, "", 4.45, "earlier BOM, not rechecked", "Kunkune"),
    ("Buck converter (24 V to 5 V)", 1, "", 2.00, "estimate", ""),
    ("GY-271 compass module (I2C)", 1, "chip varies (HMC5883L or QMC5883L clones)", 3.00, "estimate", "test in place; coarse check only"),
    ("24 V 5 A power supply", 1, "", 18.88, "earlier BOM, not rechecked", "eBay UK"),
    ("Mirror glass, 6 mm silvered, polished edge", 1, "200 x 267 mm, cut to size, back painted matt black", 31.00, "from a listing, size not confirmed", "UK made to measure (Mirrorworld, BuyGlass has a minimum charge, eBay from about 31 pounds)"),
    ("PETG or ASA filament, 1 kg", 1, "", 15.30, "earlier BOM", "The Pi Hut"),
    ("Ply or acrylic sheet, 6 mm, about 0.4 m2 plus 3 mm and 2 mm offcuts", 1, "for the laser parts", None, "not looked up", "check what the lab stocks"),
    ("Fasteners, heat-set inserts, glue, wire, connectors", 1, "not modelled yet: M3 and M4 screws, M3 inserts, glass adhesive", 15.00, "estimate", ""),
    ("Ballast about 1.5 kg", 1, "e.g. steel washers or bolts, not modelled", None, "not looked up", "free space in the base corners"),
]

# ---------------------------------------------------------------- write CSV
out_csv = ROOT / "bom" / "bom-v4.csv"
with open(out_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["process", "item", "qty", "material_or_spec", "size_mm", "unit_gbp", "total_gbp", "confidence", "source_or_note"])
    for item, qty, mat, size, note in laser:
        w.writerow(["laser cutting", item, qty, mat, size, "", "", "", note])
    for item, qty, mat, size, note in printed:
        w.writerow(["3D printing", item, qty, mat, size, "", "", "", note])
    for item, qty, spec, price, conf, src in buy:
        w.writerow(["purchase", item, qty, spec, "", "" if price is None else f"{price:.2f}", "" if price is None else f"{price * qty:.2f}", conf, src])

# ---------------------------------------------------------------- write markdown
priced = [(q * p, c) for _, q, _, p, c, _ in buy if p is not None]
sourced = sum(t for t, c in priced if c.startswith("sourced") or c.startswith("earlier") or c.startswith("from a listing"))
est = sum(t for t, c in priced if not (c.startswith("sourced") or c.startswith("earlier") or c.startswith("from a listing")))
unpriced = [i for i, _, _, p, _, _ in buy if p is None]
fit = max(max(bbox(n)) for _, names, _, _ in groups for n in names)
lines = [
    "# Bill of materials, v4 hinged mirror (2026-11-03)",
    "",
    "Generated from the CAD by `cad/src/make_bom.py`; also as `bom/bom-v4.csv`. Replaces the stale `bom-uk-draft.csv`. Sizes in mm. Prices in pounds incl. VAT where the shop gave them; see `parts-sourcing.md` for sources.",
    "",
    "## Laser cutting (cutter bed 1219 x 914, max 6 mm, ply or acrylic, no metal)",
    "",
    "| Part | Qty | Material | Size | Notes |",
    "|---|---|---|---|---|",
]
lines += [f"| {i} | {q} | {mt} | {sz} | {nt} |" for i, q, mt, sz, nt in laser]
lines += [
    "",
    "## 3D printing (Bambu P1S, 256 x 256 x 256, PETG or ASA, not PLA)",
    "",
    "| Part | Qty | Material | Largest size | Notes |",
    "|---|---|---|---|---|",
]
lines += [f"| {i} | {q} | {mt} | {sz} | {nt} |" for i, q, mt, sz, nt in printed]
lines += [
    "",
    f"Biggest printed part is {fit:.0f} mm (the hinge bar), so everything fits the bed. Solid volume of all printed parts is about {solid_g:.0f} g in PETG at 100 percent; plan on roughly half that at normal infill. One 1 kg spool should be plenty.",
    "",
    "## Purchase",
    "",
    "| Item | Qty | Spec | Unit | Total | Confidence | Source or note |",
    "|---|---|---|---|---|---|---|",
]
for item, qty, spec, price, conf, src in buy:
    u = "n/a" if price is None else f"{price:.2f}"
    t = "n/a" if price is None else f"{price * qty:.2f}"
    lines.append(f"| {item} | {qty} | {spec} | {u} | {t} | {conf} | {src} |")
lines += [
    "",
    f"Priced lines add up to about {sourced + est:.0f} pounds: {sourced:.0f} from listings or the earlier BOM, {est:.0f} estimated. Not priced yet: {'; '.join(unpriced)}.",
    "Prices of 2026-11-03 or earlier, not rechecked at order time. Nothing is ordered.",
]
(ROOT / "docs" / "bom-v4.md").write_text("\n".join(lines) + "\n")
print("Wrote", out_csv, "and docs/bom-v4.md")
print(f"printed solid mass about {solid_g:.0f} g, largest printed dimension {fit:.0f} mm, priced about {sourced + est:.0f} pounds")
