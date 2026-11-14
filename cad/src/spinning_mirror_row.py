#!/usr/bin/env python3
"""CAD assembly: row of 7 spinning mirror gimbals on a laser-cut plywood base with a goal-post top bar (CadQuery). Draft, nothing built or tested.

Reuses the single unit from spinning_mirror.py (60 mm mirror, free hinge, 2804-class brushless motor) and adds, per unit, a 3 mm top pin on the
ring that runs in a 683ZZ bearing in a printed block hung under a 20 x 20 aluminium bar. The bar passes through two end uprights and a centre
plate (6 mm plywood, laminated 2 thick at the ends). Each motor is independent and has its own random speed, nothing links the units.

World frame (mm): origin on the table at the centre of the base, Z up, X along the row. Units sit on Y = 0.
Base: 3 laminated 6 mm plywood layers (bottom, middle with ballast and cable windows, top) on four rubber feet, 720 x 140 mm.
Unit pitch 95 mm, 100 mm across the centre plate gap (22 mm clear between rings there, 17 mm elsewhere).
Hierarchy: frame (base layers, ballast, uprights, centre plate, bar), and per unit: fixed (boss, motor, top block, top bearing), spin (hub, ring, pin,
bearings), tilt (carrier, axle, mirrors, weight).

Usage (from the repo root):
  python3 cad/src/spinning_mirror_row.py [--up y|z] [--check] [--seed N]
Writes cad/out/spinning-mirror-row/ (assembly STEP, parts/<laser|print|purchase>/ with DXF for the laser parts), bom/bom-spinning-mirror-row.csv
and previews in cad/media/previews/spinning-mirror-row/.
"""
import argparse
import csv
import math
import random
from pathlib import Path

import cadquery as cq
import spinning_mirror as sm

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
OUTD = CAD / "out" / "spinning-mirror-row"
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / "spinning-mirror-row"
BOMF = CAD.parent / "bom" / "bom-spinning-mirror-row.csv"

box, cylz, cylx, cyly = sm.box, sm.cylz, sm.cylx, sm.cyly
ZC, R_OUT = sm.ZC, sm.R_OUT

# ------------------------------------------------------------------ parameters (mm)
N = 7
PITCH, PITCH_CENTRE, CENTRE_AFTER = 95.0, 100.0, 2          # pitch, and the wider pitch after unit index 2 (units 3 and 4)
_cum = [0.0]
for _i in range(1, N):
    _cum.append(_cum[-1] + (PITCH_CENTRE if _i - 1 == CENTRE_AFTER else PITCH))
XS = [c - _cum[-1] / 2 for c in _cum]                       # unit centres along X, row centred on 0
PLY = 6.0                                                    # plywood thickness (laser cutter max)
BASE_L, BASE_W = 720.0, 140.0
FEET_T = 2.0
Z_BOT, Z_MID, Z_TOP = FEET_T, FEET_T + PLY, FEET_T + 2 * PLY   # layer bottoms: 2, 8, 14
Z_BASE = FEET_T + 3 * PLY                                    # top of the base, 20
BOSS_R = 16.0                                                # printed motor boss, Z_BASE to sm.BOSS_Z1
X_UP = XS[-1] + R_OUT + 10.0 + PLY                           # upright centre, 10 mm outside the end rings (342.5)
UP_W = 70.0                                                  # upright width (Y)
BAR_W, BAR_T, BAR_L = 20.0, 1.5, 700.0                       # 20 x 20 x 1.5 aluminium box tube
TOP_PIN_L = 19.0
Z_PIN0, Z_PIN1 = ZC + R_OUT - 3, ZC + R_OUT + 16             # pin 136 to 155
Z_BLK0, BLK_H = ZC + R_OUT + 8, 12.0                         # top bearing block 147 to 159
Z_BAR0, Z_BAR1 = Z_BLK0 + BLK_H, Z_BLK0 + BLK_H + BAR_W      # bar 159 to 179
Z_BAR_C = (Z_BAR0 + Z_BAR1) / 2
UP_TOP = Z_BAR1 + 10.0
WIN = BAR_W + 0.2                                            # window for the bar
X_CENTRE = (XS[CENTRE_AFTER] + XS[CENTRE_AFTER + 1]) / 2     # centre plate between units 3 and 4
BALLAST_W, BALLAST_L = 38.0, 620.0                           # steel flat bar 38 x 6 x 620, two of them
WOOD, ALU_C = "#d2b48c", "#b8bec6"


# ------------------------------------------------------------------ laser parts (flat, thickness PLY)
def flat_rect(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, PLY, centered=False).translate((x0, y0, 0))


def cutter(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, PLY + 2, centered=False).translate((x0, y0, -1))


def layer_bottom():
    return flat_rect(-BASE_L / 2, BASE_L / 2, -BASE_W / 2, BASE_W / 2)


def layer_middle():
    w = layer_bottom()
    for y0, y1 in ((12.0, 52.0), (-52.0, -12.0)):
        w = w.cut(cutter(-BALLAST_L / 2 - 2, BALLAST_L / 2 + 2, y0, y1))
    return w.cut(cutter(-BASE_L / 2 - 1, XS[-1] + 45, -8, 8))    # cable channel, opens at the left end


def layer_top():
    w = layer_bottom()
    for x in XS:
        w = w.cut(cylz(7.0, -1, PLY + 1, x, 0))                                             # cable hole
        for k in range(4):
            a = math.radians(90 * k)
            w = w.cut(cylz(1.25, -1, PLY + 1, x + 12.5 * math.cos(a), 12.5 * math.sin(a)))   # pilot holes for the boss screws
    for xc, t in ((-X_UP, 2 * PLY), (X_UP, 2 * PLY), (X_CENTRE, PLY)):
        w = w.cut(cutter(xc - (t + 0.2) / 2, xc + (t + 0.2) / 2, -15.2, 15.2))     # tab slots
    return w


def upright_flat(tab=True, window=True):
    """Profile in (u = Y, v = Z world), thickness along local z."""
    pts = [(-15, Z_TOP), (15, Z_TOP), (15, Z_BASE), (UP_W / 2, Z_BASE), (UP_W / 2, UP_TOP), (-UP_W / 2, UP_TOP), (-UP_W / 2, Z_BASE), (-15, Z_BASE)]
    w = cq.Workplane("XY").polyline(pts).close().extrude(PLY)
    return w.cut(cq.Workplane("XY").center(0, Z_BAR_C).rect(WIN, WIN).extrude(PLY * 3).translate((0, 0, -PLY)))


def place_yz(flat, x_min):
    """Flat (u = Y, v = Z, t) to the world: thickness along +X starting at x_min."""
    s = flat.val() if hasattr(flat, "val") else flat
    s = s.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 90)
    return s.translate((x_min, 0, 0))


# ------------------------------------------------------------------ unit parts
UNIT = []          # (name, shape, colour, group, material, process)
SKIP = {"print_base_floor_plate", "print_base_puck", "rubber_feet_x4", "ballast_steel_washers"}


def build_unit():
    sm.build()
    UNIT.clear()
    ztop = ZC + R_OUT
    for nm, s, col, grp, mat in sm.PARTS_L:
        if nm in SKIP:
            continue
        if nm == "print_ring_with_foot":
            s = cq.Workplane(obj=s).union(cylz(4.5, ztop - 2, ztop + 5)).cut(cylz(1.5, ztop - 3, ztop + 6)).val()
            nm = "print_ring_with_foot_and_pin_boss"
        UNIT.append((nm, s, col, grp, mat))
    boss = cylz(BOSS_R, Z_BASE, sm.BOSS_Z1).cut(cylz(7.0, Z_BASE - 1, sm.BOSS_Z1 + 1))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        boss = boss.cut(cylz(2.1, sm.BOSS_Z1 - 5, sm.BOSS_Z1 + 1, sm.MOTOR_BASE_PCD / 2 * math.cos(a), sm.MOTOR_BASE_PCD / 2 * math.sin(a)))
        b = math.radians(90 * k)
        x, y = 12.5 * math.cos(b), 12.5 * math.sin(b)
        boss = boss.cut(cylz(1.6, Z_BASE - 1, sm.BOSS_Z1 + 1, x, y)).cut(cylz(3.0, sm.BOSS_Z1 - 3, sm.BOSS_Z1 + 1, x, y))
    UNIT.append(("print_motor_boss", boss.val(), sm.PRINT_C, "fixed", "print"))
    UNIT.append(("pin_3mm_steel_19", cylz(1.5, Z_PIN0, Z_PIN1).val(), sm.STEEL, "spin", "steel"))
    blk = box(-BAR_W / 2, BAR_W / 2, -BAR_W / 2, BAR_W / 2, Z_BLK0, Z_BLK0 + BLK_H)
    blk = blk.cut(cylz(3.55, Z_BLK0 - 1, Z_BLK0 + 3.1)).cut(cylz(2.0, Z_BLK0 + 3.0, Z_BLK0 + 10.0))
    for sx in (-1, 1):
        blk = blk.cut(cylz(1.65, Z_BLK0 + 3.5, Z_BLK0 + BLK_H + 1, sx * 7.0, 0))
    UNIT.append(("print_top_bearing_block", blk.val(), sm.PRINT_C, "fixed", "print"))
    brg = cylz(3.5, Z_BLK0, Z_BLK0 + 3.0).cut(cylz(1.5, Z_BLK0 - 1, Z_BLK0 + 4.0))
    UNIT.append(("bearing_683zz_top", brg.val(), sm.STEEL, "fixed", "steel"))


def pose_unit(i, az, tilt):
    out = []
    for nm, s, col, grp, mat in UNIT:
        if grp == "tilt":
            s = s.rotate((0, 0, ZC), (1, 0, ZC), tilt + 90)
        if grp in ("tilt", "spin"):
            s = s.rotate((0, 0, 0), (0, 0, 1), az)
        out.append((f"u{i + 1}_{nm}", s.translate((XS[i], 0, 0)), col, f"unit{i + 1}_{grp}", mat))
    return out


FRAME = []         # (name, shape, colour, group, material)


def build_frame():
    FRAME.clear()
    L = (layer_bottom(), layer_middle(), layer_top())
    for nm, w, z in (("laser_base_bottom_6mm", L[0], Z_BOT), ("laser_base_middle_6mm", L[1], Z_MID), ("laser_base_top_6mm", L[2], Z_TOP)):
        FRAME.append((nm, w.translate((0, 0, z)).val(), WOOD, "frame", "ply"))
    for k, y in enumerate((32.0, -32.0)):
        FRAME.append((f"ballast_steel_bar_{k + 1}", box(-BALLAST_L / 2, BALLAST_L / 2, y - BALLAST_W / 2, y + BALLAST_W / 2, Z_MID, Z_MID + PLY).val(), sm.STEEL, "frame", "steel"))
    for k, (x, y) in enumerate(((-BASE_L / 2 + 15, 55), (BASE_L / 2 - 15, 55), (-BASE_L / 2 + 15, -55), (BASE_L / 2 - 15, -55))):
        FRAME.append((f"rubber_foot_{k + 1}", cylz(6.0, 0, FEET_T, x, y).val(), sm.RUBBER, "frame", "rubber"))
    for k, xc in enumerate((-X_UP, X_UP)):
        for j in range(2):
            FRAME.append((f"laser_upright_{k + 1}_layer_{j + 1}_6mm", place_yz(upright_flat(), xc - PLY + j * PLY), WOOD, "frame", "ply"))
    FRAME.append(("laser_centre_plate_6mm", place_yz(upright_flat(), X_CENTRE - PLY / 2), WOOD, "frame", "ply"))
    bar = box(-BAR_L / 2, BAR_L / 2, -BAR_W / 2, BAR_W / 2, Z_BAR0, Z_BAR1).cut(
        box(-BAR_L / 2 - 1, BAR_L / 2 + 1, -BAR_W / 2 + BAR_T, BAR_W / 2 - BAR_T, Z_BAR0 + BAR_T, Z_BAR1 - BAR_T))
    for x in XS:
        for sx in (-1, 1):
            bar = bar.cut(cylz(3.0, Z_BAR0 - 1, Z_BAR1 + 1, x + sx * 7.0, 0))
    FRAME.append(("bar_alu_20x20x1.5_700", bar.val(), ALU_C, "frame", "alu"))


def all_parts(poses):
    out = list(FRAME)
    for i, (az, t) in enumerate(poses):
        out += pose_unit(i, az, t)
    return out


def cqc(h):
    return cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255)


def assemble(poses, yup):
    root = cq.Assembly(name="spinning_mirror_row")
    subs = {}
    for nm, s, col, grp, _ in all_parts(poses):
        if yup:
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        if grp not in subs:
            subs[grp] = cq.Assembly(name=grp)
        subs[grp].add(s, name=nm, color=cqc(col))
    for a in subs.values():
        root.add(a)
    return root


def clashes(parts, tol=1.0, only_with=None):
    found = []
    bbs = [(p[0], p[1], p[1].BoundingBox()) for p in parts]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            a, b = bbs[i], bbs[j]
            if only_with and not (a[0] in only_with or b[0] in only_with):
                continue
            if (a[2].xmax < b[2].xmin or b[2].xmax < a[2].xmin or a[2].ymax < b[2].ymin or b[2].ymax < a[2].ymin
                    or a[2].zmax < b[2].zmin or b[2].zmax < a[2].zmin):
                continue
            try:
                v = a[1].intersect(b[1]).Volume()
            except Exception:
                v = -1
            if v > tol:
                found.append((a[0], b[0], round(v, 1)))
    return found


def mass_g():
    rho = {"print": 1.25e-3, "steel": 7.85e-3, "brass": 8.5e-3, "acrylic": 1.19e-3, "ply": 0.65e-3, "alu": 2.7e-3, "rubber": 1.1e-3}
    m = {}
    for _, s, _, grp, mat in all_parts([(0, 0)] * N):
        m[grp[:4] == "unit" and "units" or "frame"] = m.get(grp[:4] == "unit" and "units" or "frame", 0) + s.Volume() * rho[mat]
    return m


def export_all(yup):
    for sub in ("laser", "print", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")) + list(d.glob("*.dxf")):
            old.unlink()

    def put(nm, s, proc):
        sh = s.rotate((0, 0, 0), (1, 0, 0), -90) if yup else s
        cq.exporters.export(cq.Workplane(obj=sh), str(PARTS / proc / f"{nm}.step"))
    for nm, s, _, _, _ in UNIT:
        put(nm, s, "print" if nm.startswith("print_") else "purchase")
    for nm, s, _, _, mat in FRAME:
        if nm.startswith(("bar_", "ballast", "rubber")):
            put(nm, s, "purchase")
        else:
            put(nm, s, "laser")
    d = PARTS / "laser"
    flat = {"laser_base_bottom_6mm": layer_bottom(), "laser_base_middle_6mm": layer_middle(), "laser_base_top_6mm": layer_top(),
            "laser_upright_layer_6mm_x4": upright_flat(), "laser_centre_plate_6mm": upright_flat()}
    for nm, w in flat.items():
        cq.exporters.exportDXF(cq.Workplane(obj=w.val() if hasattr(w, "val") else w).faces("<Z").val(), str(d / f"{nm}.dxf"))
    print("Wrote", len(UNIT) + len(FRAME), "part STEP files and", len(flat), "laser DXF outlines to", PARTS)


def write_bom():
    rows = [
        ("laser", f"Plywood 6 mm: base layers, {int(BASE_L)} x {int(BASE_W)} mm, bottom (plain), middle (ballast and cable windows), top (cable holes, slots)", 3, "own cutter, bed 1219 x 914"),
        ("laser", "Plywood 6 mm: end upright, 70 mm wide, with bar window and tab; cut 4 (2 laminated per end)", 4, "DXF laser_upright_layer_6mm_x4"),
        ("laser", "Plywood 6 mm: centre plate, same profile as the upright", 1, "DXF laser_centre_plate_6mm"),
        ("print", "PETG: ring with foot and pin boss (x7), carrier (x7), hub adapter (x7), top bearing block (x7)", 28, "Bambu P1S, 0.4 mm, 4 walls"),
        ("print", "PLA or PETG: motor boss (x7)", 7, "bolts to the top plate with M3 x 16 self-tapping screws"),
        ("buy", "Brushless gimbal motor 2804 class, about 100 KV (ASSUMED size, check)", 7, ""),
        ("buy", "Motor drivers, 3-phase, open-loop capable (SimpleFOC Mini or similar), 7 in total; two boards with enough PWM (21 outputs)", 7, "ESP32-S3 or RP2040 x2"),
        ("buy", "12 V supply, 5 A, fuse, power distribution", 1, ""),
        ("buy", "Bearing 683ZZ (3 x 7 x 3): 2 per ring hinge plus 1 per top block", 21, ""),
        ("buy", "Steel pin 3 mm x 19 mm (ring top)", 7, "press into the ring boss"),
        ("buy", "Steel rod 3 mm x 78 mm (hinge axle)", 7, ""),
        ("buy", "Acrylic mirror 2 mm, 60 mm discs (laser-cut), two per unit", 14, "one per unit if single-sided"),
        ("buy", "Brass slug 6 x 5 mm (swap for steel, aluminium or none)", 7, "tune the random behaviour"),
        ("buy", "Aluminium box tube 20 x 20 x 1.5, 700 mm", 1, "drill 2 x 6 mm holes per unit, M4 screws to the blocks"),
        ("buy", "Steel flat bar 38 x 6 mm, 620 mm (about 1.1 kg each)", 2, "ballast in the middle layer windows"),
        ("buy", "Rubber feet 12 mm", 4, ""),
        ("buy", "Fasteners: M3 x 16 self-tapping (28), M3 x 8 (28 motor, 14 hub to ring), M2.5 x 6 (28), M4 x 12 (14), M3 x 6 trim (28), M3 and M4 heat-set inserts, wood glue", 1, "set"),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


def render(parts, path, views, hide=(), box_=None, zoom=1.2, cut_y=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris, cols = [], []
    light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
    for nm, s, col, _, _ in parts:
        if any(h in nm for h in hide):
            continue
        if cut_y is not None:
            try:
                s = s.cut(box(-900, 900, cut_y, 300, -10, 400).val())
            except Exception:
                pass
        v, t = s.tessellate(0.6, 0.5)
        v = np.array([(p.x, p.y, p.z) for p in v])
        base = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        for a, b, c in t:
            tri = v[[a, b, c]]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            sh = 0.55 + 0.45 * abs(float(n @ light) / nn) if nn > 1e-9 else 0.8
            tris.append(tri); cols.append(np.clip(base * sh, 0, 1))
    x0, x1, y0, y1, z0, z1 = box_
    fig = plt.figure(figsize=(9 * len(views), 5.5))
    for k, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(1, len(views), k + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolors="none"))
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1)
        ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0), zoom=zoom); ax.set_axis_off(); ax.view_init(elev, azim)
        ax.set_title(title, fontsize=12)
    fig.subplots_adjust(0.0, 0.0, 1.0, 0.92, wspace=0.0)
    fig.savefig(path, dpi=100)
    plt.close(fig)


def random_poses(seed):
    rnd = random.Random(seed)
    return [(rnd.uniform(0, 360), rnd.uniform(0, 360)) for _ in range(N)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--up", choices=("y", "z"), default="y", help="up axis of the STEP files (y for Fusion)")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    ap.add_argument("--seed", type=int, default=3, help="random pose for the previews")
    a = ap.parse_args()
    build_unit()
    build_frame()

    print(f"Row of {N}: unit centres X = {', '.join(f'{x:.1f}' for x in XS)}; gaps between rings {PITCH - 2 * R_OUT:.0f} mm, {PITCH_CENTRE - 2 * R_OUT:.0f} mm at the centre plate (X {X_CENTRE:.1f})")
    print(f"Base {BASE_L:.0f} x {BASE_W:.0f} x {Z_BASE - FEET_T:.0f} mm on feet, uprights at X +/-{X_UP:.1f}, bar {BAR_L:.0f} mm long, centre {Z_BAR_C:.0f} mm above the table, uprights to {UP_TOP:.0f} mm")
    print(f"Pin {TOP_PIN_L:.0f} mm into a 683ZZ in the block; ring top boss to {ZC + R_OUT + 5:.0f} mm, block bottom {Z_BLK0:.0f} mm (3 mm axial float before the boss touches)")
    m = mass_g()
    print(f"Mass: frame about {m['frame'] / 1000:.1f} kg (of which steel ballast {2 * 38 * 6 * 620 * 7.85e-6:.1f} kg), 7 units about {m['units'] / 1000:.2f} kg")

    if a.check:
        names_unit = lambda parts: {p[0] for p in parts if "_spin" in p[3] or "_tilt" in p[3]}
        total = 0
        for seed in range(8):
            P = all_parts(random_poses(seed))
            bad = clashes(P, only_with=names_unit(P))
            bad = [b for b in bad if not (b[0].split("_", 1)[1].startswith(("axle", "bearing", "pin")) and b[1].split("_", 1)[1].startswith(("axle", "bearing", "pin")))]
            total += len(bad)
            if bad:
                print(f"seed {seed}: {len(bad)} clashes", bad[:8])
        print("total clashes over 8 random poses (moving parts against everything):", total)
        static = clashes(all_parts([(0, 0)] * N))
        print("static clashes at az 0, tilt 0:", len(static), static[:12])
        return

    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_all(a.up == "y")
    write_bom()
    P0 = random_poses(a.seed)
    assemble(P0, a.up == "y").save(str(OUTD / "spinning-mirror-row-assembly.step"))
    print("Wrote", OUTD / "spinning-mirror-row-assembly.step")
    P = all_parts(P0)
    bx = (-380, 380, -90, 90, 0, UP_TOP + 5)
    render(P, IMG / "row.png", [(12, -35, "Row of 7, 3/4 view"), (0, -90, "Front")], box_=bx, zoom=1.35)
    render(P, IMG / "row-plan.png", [(90, -90, "Plan"), (6, -90, "Front, mirrors in random poses")], box_=bx, zoom=1.35)
    render(P, IMG / "row-detail.png", [(14, -60, "Ends and centre plate"), (12, -125, "Back")],
           box_=(-380, -40, -90, 90, 0, UP_TOP + 5), zoom=1.1)
    render(P, IMG / "row-section.png", [(4, -90, "Section through the row (y > 0 cut away)")], box_=bx, zoom=1.35, cut_y=0.0)
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
