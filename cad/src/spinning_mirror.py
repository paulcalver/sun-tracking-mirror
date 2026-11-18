#!/usr/bin/env python3
"""CAD assembly: spinning mirror gimbal, an 80 mm round mirror on a free hinge inside a ring, the ring on a brushless motor (CadQuery).
Draft, nothing built or tested. See docs/spinning-mirror-gimbal.md and sim/spinning-mirror/spinning-mirror-gimbal-concept.html (option D).

World frame (mm): origin on the table at the centre of the base, Z up. The ring spins about Z. Its plane is XZ and the mirror hinge axle
runs along X through the ring centre at Z = ZC. tilt = 0 puts the mirror in the ring plane; the mirror turns about X.
Hierarchy (maps to Fusion components, no joints):
  base_fixed   110 mm printed puck with a steel ballast pocket, floor plate, rubber feet, brushless gimbal motor
  ring_spin    turns about Z: hub adapter on the motor bell, ring with bearing bosses, two 683ZZ bearings
  mirror_tilt  free to turn about X: printed carrier (rim, bar, weight pad), 3 mm axle, two 2 mm acrylic mirror discs, brass weight slug

Nothing drives the hinge. The single motor jitters its speed at random and the mirror tumbles (concept page, option D). The eccentric
weight slug is swappable (brass 1.2 g, steel, aluminium, or none).
Motor: the real iPower GM2804 with AS5048A encoder, imported from cad/src/assets/ipower-gm2804-as5048a.step (35 mm, 26.15 mm tall: stator
housing below, 12.75 mm rotor bell above). Its stator is fixed, the bell turns with the ring. Mounting taken from the STEP: 4 blind holes
(2.4 mm, 3.5 deep, on a 15.8 mm circle, not evenly spaced) in the bottom face, 4 holes on a 26 mm circle at the bell top, and a 6.5 mm hollow
shaft through the stator that the wires can use. Whether those holes are threaded is not stated; check the part.

Usage (from the repo root):
  python3 cad/src/spinning_mirror.py [--az DEG] [--tilt DEG] [--up y|z] [--check]
Writes cad/out/spinning-mirror/archive/spinning-mirror/ (assembly STEP, parts/<print|purchase>/), bom/bom-spinning-mirror.csv and previews in
cad/media/previews/spinning-mirror/.
"""
import argparse
import csv
import math
import shutil
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
ART = HERE / "assets"
OUTD = CAD / "out" / "spinning-mirror" / "archive" / "spinning-mirror"
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / "spinning-mirror"
BOMF = CAD.parent / "bom" / "bom-spinning-mirror.csv"

# ------------------------------------------------------------------ parameters (mm)
BASE_R = 55.0                                   # puck radius (110 mm across)
FEET_T, PLATE_T, PUCK_Z0, PUCK_Z1 = 2.0, 3.0, 5.0, 21.0     # rubber feet 0..2, floor plate 2..5, puck shell 5..21
POCKET_R, POCKET_Z1 = 48.0, 15.0                # ballast and cable pocket in the underside of the puck
BALLAST_R0, BALLAST_R1, BALLAST_T = 30.0, 46.0, 5.0         # steel washers or nuts glued in, about 150 g
BOSS_R, BOSS_Z1 = 15.0, 29.0                    # motor boss on top of the puck
CABLE_R = 5.5                                   # central cable hole, 11 mm (the motor has a 6.5 mm hollow shaft)
NOTCH_W, NOTCH_Z0, NOTCH_Z1 = 8.0, 10.5, 14.5   # cable notch through the puck wall, above the ballast
INSERT_R, INSERT_D = 51.5, 4.2                  # M3 heat-set inserts that hold the floor plate (4 at 45 deg steps)

MOTOR_STEP = ART / "ipower-gm2804-as5048a.step"
MOTOR_D = 35.0
MOTOR_ZBOT, MOTOR_ZTOP = -13.4, 12.75           # in the STEP frame: bottom of the stator housing, top of the bell
MOTOR_H = MOTOR_ZTOP - MOTOR_ZBOT               # 26.15
MOTOR_BOTTOM_HOLES = [(5.09, 6.05), (-3.87, 6.89), (-5.09, -6.05), (3.87, -6.89)]    # blind 2.4 x 3.5 in the stator bottom face
MOTOR_TOP_HOLES = [(9.19, 9.19), (-9.19, 9.19), (-9.19, -9.19), (9.19, -9.19)]       # bell top, on a 26 mm circle, countersunk 2.4
MOTOR_Z0 = BOSS_Z1                              # bottom of the motor sits on the boss
HUB_T, HUB_R = 7.0, 17.5                        # hub adapter disc on the bell (7 mm so its top is level with a 6 mm deck 1 mm above the bell)
FOOT_SCREW_D = 3.4
HUB_Z0 = MOTOR_Z0 + MOTOR_H
HUB_Z1 = HUB_Z0 + HUB_T

R_IN, R_OUT, RING_W = 44.0, 49.0, 10.0          # ring inside and outside radius, width along Y
FOOT_H = 6.0
FOOT_X, FOOT_SCREW_X = 8.0, 5.0                 # foot half width, M3 pair at x = +/-5
ZC = HUB_Z1 + FOOT_H + R_OUT                    # ring and mirror centre height (about 116 mm)

MIR_R, MIR_T = 40.0, 2.0                        # 80 mm acrylic mirror discs, 2 mm
CAR_T, RIM_W, BAR_W = 5.0, 3.0, 6.0             # carrier thickness, rim width, bar width
PAD_Y, PAD_R, SLUG_D, SLUG_T = 29.0, 8.0, 6.0, 5.0         # weight pad off-axis by 29 mm, brass slug 6 x 5
AXLE_D, AXLE_L = 3.0, 2 * R_OUT                 # 3 mm axle, flush with the outer faces of the bosses
BOSS_D, BOSS_X0 = 12.0, 41.5                    # axle bosses on the ring, inner face at x = 41.5 (1.5 mm from the mirror rim)
BRG = (3.0, 7.0, 3.0)                           # 683ZZ: bore, outer diameter, width
HUB_D = 4.0                                     # carrier hub that touches the inner race

PRINT_C, STEEL, ALU, BRASS, MIRROR, MOTOR_C, RUBBER = ("#262626", "#c4c8cc", "#a9b0b8", "#c9a24a", "#cfe3ee", "#2f3338", "#222222")
RHO = {"print": 1.25e-3, "steel": 7.85e-3, "brass": 8.5e-3, "acrylic": 1.19e-3, "motor": 2.45e-3}   # g per mm3 (motor: 42.3 g over the STEP volume)


# ------------------------------------------------------------------ helpers
def _shape(wp):
    return wp.val() if hasattr(wp, "val") else wp


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def cyly(r, y0, y1, x=0.0, z=0.0):
    """Cylinder along +Y from y0 to y1 at (x, z)."""
    return cq.Workplane("XZ").workplane(offset=-y1).center(x, z).circle(r).extrude(y1 - y0)


def cylx(r, x0, x1, y=0.0, z=0.0):
    """Cylinder along +X from x0 to x1 at (y, z)."""
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)


PARTS_L = []


def motor_parts():
    """(stator, rotor) of the imported motor, placed with the bottom of the stator at MOTOR_Z0."""
    sol = cq.importers.importStep(str(MOTOR_STEP)).solids().vals()
    stator = [x for x in sol if x.BoundingBox().zmin < -1][0]
    rotor = [x for x in sol if x.BoundingBox().zmin >= -1]
    dz = MOTOR_Z0 - MOTOR_ZBOT
    return stator.translate((0, 0, dz)), cq.Compound.makeCompound([r.translate((0, 0, dz)) for r in rotor])


def add(name, wp, colour, grp, mat):
    PARTS_L.append((name, _shape(wp), colour, grp, mat))


def build():
    PARTS_L.clear()
    # ---- base
    plate = cylz(BASE_R, FEET_T, FEET_T + PLATE_T)
    puck = cylz(BASE_R, PUCK_Z0, PUCK_Z1).cut(cylz(POCKET_R, PUCK_Z0 - 1, POCKET_Z1))
    puck = puck.union(cylz(BOSS_R, PUCK_Z1 - 1, BOSS_Z1))
    puck = puck.cut(cylz(CABLE_R, POCKET_Z1 - 1, BOSS_Z1 + 1))
    puck = puck.cut(box(POCKET_R - 1, BASE_R + 1, -NOTCH_W / 2, NOTCH_W / 2, NOTCH_Z0, NOTCH_Z1))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, y = INSERT_R * math.cos(a), INSERT_R * math.sin(a)
        puck = puck.cut(cylz(INSERT_D / 2, PUCK_Z0 - 1, PUCK_Z0 + 6, x, y))
        plate = plate.cut(cylz(1.6, FEET_T - 1, FEET_T + PLATE_T + 1, x, y))
    for (x, y) in MOTOR_BOTTOM_HOLES:                        # M2 screws come up from the underside into the stator bottom
        puck = puck.cut(cylz(1.2, PUCK_Z0 - 1, BOSS_Z1 + 1, x, y))
        plate = plate.cut(cylz(1.2, FEET_T - 1, FEET_T + PLATE_T + 1, x, y))
    add("print_base_floor_plate", plate, PRINT_C, "fixed", "print")
    add("print_base_puck", puck, PRINT_C, "fixed", "print")
    feet = None
    for k in range(4):
        a = math.radians(90 * k)
        f = cylz(5.0, 0, FEET_T, 40 * math.cos(a), 40 * math.sin(a))
        feet = f if feet is None else feet.union(f)
    add("rubber_feet_x4", feet, RUBBER, "fixed", "print")
    add("ballast_steel_washers", cylz(BALLAST_R1, PUCK_Z0, PUCK_Z0 + BALLAST_T).cut(cylz(BALLAST_R0, PUCK_Z0 - 1, PUCK_Z0 + BALLAST_T + 1)),
        STEEL, "fixed", "steel")
    stator, rotor = motor_parts()
    add("motor_gm2804_stator", stator, MOTOR_C, "fixed", "motor")
    add("motor_gm2804_rotor_bell", rotor, "#3a3f45", "spin", "motor")

    # ---- hub adapter and ring (ring_spin)
    hub = cylz(HUB_R, HUB_Z0, HUB_Z1)
    for (x, y) in MOTOR_TOP_HOLES:                           # M2 down into the bell top, heads counterbored from above
        hub = hub.cut(cylz(1.2, HUB_Z0 - 1, HUB_Z1 + 1, x, y)).cut(cylz(2.1, HUB_Z1 - 1.6, HUB_Z1 + 1, x, y))
    for sx in (-1, 1):                                       # M3 heat-set inserts that take the screws from inside the ring
        hub = hub.cut(cylz(INSERT_D / 2, HUB_Z1 - 5.5, HUB_Z1 + 1, sx * FOOT_SCREW_X, 0))
    add("print_hub_adapter", hub, PRINT_C, "spin", "print")

    ring = cyly(R_OUT, -RING_W / 2, RING_W / 2, 0, ZC).cut(cyly(R_IN, -RING_W, RING_W, 0, ZC))
    for sx in (-1, 1):
        x0, x1 = (BOSS_X0, R_OUT) if sx > 0 else (-R_OUT, -BOSS_X0)
        ring = ring.union(cylx(BOSS_D / 2, x0, x1, 0, ZC))
        pk0, pk1 = (BOSS_X0 - 1, BOSS_X0 + BRG[2] + 0.1) if sx > 0 else (-BOSS_X0 - BRG[2] - 0.1, -BOSS_X0 + 1)
        ring = ring.cut(cylx(BRG[1] / 2 + 0.05, pk0, pk1, 0, ZC))              # bearing pocket opens to the inside
        ring = ring.cut(cylx(2.0, 0, sx * (R_OUT + 1), 0, ZC) if sx > 0 else cylx(2.0, -R_OUT - 1, 0, 0, ZC))   # clearance hole for the axle
    for k in range(4):                                       # balance screw holes, M3 self-tapping, in the +Y face
        a = math.radians(45 + 90 * k)
        ring = ring.cut(cyly(1.3, RING_W / 2 - 6, RING_W / 2 + 1, (R_IN + R_OUT) / 2 * math.cos(a), ZC + (R_IN + R_OUT) / 2 * math.sin(a)))
    foot_top = ZC - R_OUT + 2
    foot = box(-FOOT_X, FOOT_X, -RING_W / 2, RING_W / 2, HUB_Z1, foot_top)
    ring = ring.union(foot)
    z_in = ZC - R_IN
    for sx in (-1, 1):                                       # M3 x 16 from inside the ring, down through the ring bottom and foot into the hub
        ring = ring.cut(cylz(FOOT_SCREW_D / 2, HUB_Z1 - 1, z_in + 1, sx * FOOT_SCREW_X, 0)).cut(cylz(3.2, z_in - 2.5, z_in + 1, sx * FOOT_SCREW_X, 0))
    add("print_ring_with_foot", ring, PRINT_C, "spin", "print")
    for nm, sx in (("bearing_683zz_a", 1), ("bearing_683zz_b", -1)):
        x0 = BOSS_X0 if sx > 0 else -BOSS_X0 - BRG[2]
        b = cylx(BRG[1] / 2, x0, x0 + BRG[2], 0, ZC).cut(cylx(BRG[0] / 2, x0 - 1, x0 + BRG[2] + 1, 0, ZC))
        add(nm, b, STEEL, "spin", "steel")

    # ---- mirror_tilt
    rim = cylz(MIR_R, ZC - CAR_T / 2, ZC + CAR_T / 2).cut(cylz(MIR_R - RIM_W, ZC - CAR_T, ZC + CAR_T))
    bar = box(-MIR_R + 1, MIR_R - 1, -BAR_W / 2, BAR_W / 2, ZC - CAR_T / 2, ZC + CAR_T / 2)
    pad = cylz(PAD_R, ZC - CAR_T / 2, ZC + CAR_T / 2, 0, PAD_Y)
    bar2 = box(-BAR_W / 2, BAR_W / 2, -MIR_R + 1, MIR_R - 1, ZC - CAR_T / 2, ZC + CAR_T / 2)      # cross bar supports the mirror quadrants
    car = rim.union(bar).union(bar2).union(pad)
    car = car.cut(cylz(SLUG_D / 2, ZC - CAR_T, ZC + CAR_T, 0, PAD_Y))
    hub_len = BOSS_X0 - 0.1
    car = car.union(cylx(HUB_D / 2, MIR_R - 1, hub_len, 0, ZC)).union(cylx(HUB_D / 2, -hub_len, -MIR_R + 1, 0, ZC))
    car = car.cut(cylx(AXLE_D / 2, -hub_len - 1, hub_len + 1, 0, ZC))
    add("print_mirror_carrier", car, PRINT_C, "tilt", "print")
    add(f"axle_3mm_steel_rod", cylx(AXLE_D / 2, -AXLE_L / 2, AXLE_L / 2, 0, ZC), STEEL, "tilt", "steel")
    add(f"mirror_front_acrylic_{int(2 * MIR_R)}", cylz(MIR_R, ZC + CAR_T / 2, ZC + CAR_T / 2 + MIR_T), MIRROR, "tilt", "acrylic")
    add(f"mirror_back_acrylic_{int(2 * MIR_R)}", cylz(MIR_R, ZC - CAR_T / 2 - MIR_T, ZC - CAR_T / 2), MIRROR, "tilt", "acrylic")
    add("weight_slug_brass_6x5", cylz(SLUG_D / 2, ZC - SLUG_T / 2, ZC + SLUG_T / 2, 0, PAD_Y), BRASS, "tilt", "brass")


def posed(az=0.0, tilt=0.0):
    out = []
    for nm, s, col, grp, mat in PARTS_L:
        if grp == "tilt":
            s = s.rotate((0, 0, ZC), (1, 0, ZC), tilt + 90)      # carrier is modelled flat; +90 puts tilt 0 in the ring plane
        if grp in ("tilt", "spin"):
            s = s.rotate((0, 0, 0), (0, 0, 1), az)
        out.append((nm, s, col, grp, mat))
    return out


def cqc(h):
    return cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255)


def assemble(az, tilt, yup):
    root = cq.Assembly(name="spinning_mirror")
    subs = {"fixed": "base_fixed", "spin": "ring_spin", "tilt": "mirror_tilt"}
    sa = {g: cq.Assembly(name=n) for g, n in subs.items()}
    for nm, s, col, grp, _ in posed(az, tilt):
        if yup:
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        sa[grp].add(s, name=nm, color=cqc(col))
    for g, a in sa.items():
        root.add(a, name=subs[g])
    return root


def clashes(parts, tol=1.0, only_with=None):
    found = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _, _, _ in parts]
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


def mass_g(grp=None, mats=None):
    return sum(s.Volume() * RHO[m] for _, s, _, g, m in PARTS_L if (grp is None or g in grp) and (mats is None or m in mats))


def process_of(nm):
    return "print" if nm.startswith("print_") else "purchase"


def export_parts(yup):
    for sub in ("print", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")):
            old.unlink()
    for nm, s, _, _, _ in PARTS_L:
        sh = s.rotate((0, 0, 0), (1, 0, 0), -90) if yup else s
        cq.exporters.export(cq.Workplane(obj=sh), str(PARTS / process_of(nm) / f"{nm}.step"))
    print("Wrote", len(PARTS_L), "part STEP files to", PARTS)


def write_bom():
    rows = [
        ("print", "PETG: ring with foot, mirror carrier, hub adapter (balance and weight sensitive, print the ring flat)", 3, "Bambu P1S, 0.4 mm, 0.16 to 0.2 mm layers, 4 walls"),
        ("print", "PLA or PETG: base puck and floor plate", 2, "Bambu P1S"),
        ("buy", "iPower GM2804-100T gimbal motor with AS5048A encoder, 12 V", 1, "35 x 26 mm, hollow shaft 6.5 mm"),
        ("buy", "Motor driver SimpleFOC Mini (or similar 3-phase gimbal driver) and an ESP32 dev board", 1, "controller, random-walk speed setpoint"),
        ("buy", "Magnetic encoder AS5600 or AS5048 (optional, closed-loop speed and logging)", 1, "open-loop speed mode works without it"),
        ("buy", "12 V supply, 2 A, and a barrel jack or screw terminal", 1, ""),
        ("buy", "Bearing 683ZZ (3 x 7 x 3 mm)", 2, "choose low-drag, light grease or none"),
        ("buy", "Stainless or silver-steel rod 3 mm, 78 mm long", 1, "glue to the carrier with CA or retaining compound"),
        ("buy", "Acrylic mirror 2 mm, 80 mm discs (laser-cut or hole-sawn), one or two", 2, "cut from sheet; one-sided is fine, two give both faces"),
        ("buy", "Brass slug 6 x 5 mm (swap for steel or aluminium, or leave out)", 1, "eccentric weight, about 1.2 g"),
        ("buy", "Steel washers or M8 nuts as ballast, about 150 g", 1, "glue into the base pocket"),
        ("buy", "Heat-set inserts M3 x 5 (4 floor plate, 4 motor, 2 ring foot)", 10, ""),
        ("buy", "Screws: M3 x 8 (floor plate x4, motor x4, hub to ring foot x2), M2.5 x 6 (bell to hub x4), M3 x 6 (ring balance trim x4)", 1, "set"),
        ("buy", "Rubber feet 10 mm", 4, "stick-on"),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


def render(parts, path, views, hide=(), box_=None, zoom=1.2, only=(), cut_y=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris, cols = [], []
    light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
    for nm, s, col, _, _ in parts:
        if any(h in nm for h in hide) or (only and not any(o in nm for o in only)):
            continue
        if cut_y is not None:
            try:
                s = s.cut(box(-300, 300, cut_y, 300, -10, 400).val())
            except Exception:
                pass
        v, t = s.tessellate(0.25, 0.3)
        v = np.array([(p.x, p.y, p.z) for p in v])
        base = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        for a, b, c in t:
            tri = v[[a, b, c]]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            sh = 0.55 + 0.45 * abs(float(n @ light) / nn) if nn > 1e-9 else 0.8
            tris.append(tri); cols.append(np.clip(base * sh * (2.4 if col == PRINT_C else 1.0), 0, 1))   # matt black prints, brightened in previews only
    x0, x1, y0, y1, z0, z1 = box_ or (-80, 80, -80, 80, 0, ZC + 60)
    fig = plt.figure(figsize=(7 * len(views), 8.5))
    for k, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(1, len(views), k + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolors="none"))
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1)
        ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0), zoom=zoom); ax.set_axis_off(); ax.view_init(elev, azim)
        ax.set_title(title, fontsize=12)
    fig.subplots_adjust(0.0, 0.0, 1.0, 0.94, wspace=0.0)
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--az", type=float, default=0.0, help="ring angle about Z, deg")
    ap.add_argument("--tilt", type=float, default=0.0, help="mirror angle about the hinge, deg (0 = in the ring plane)")
    ap.add_argument("--up", choices=("y", "z"), default="y", help="up axis of the STEP files (y for Fusion)")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    a = ap.parse_args()
    build()

    spin_m = mass_g(("spin", "tilt"))
    print(f"Overall: {2 * BASE_R:.0f} mm base, ring centre {ZC:.0f} mm above the table, top of the ring {ZC + R_OUT:.0f} mm")
    print(f"Mirror {2 * MIR_R:.0f} mm, ring {2 * R_IN:.0f} inside / {2 * R_OUT:.0f} outside, clearance to the carrier {R_IN - math.hypot(MIR_R, CAR_T / 2 + MIR_T):.1f} mm at its worst, "
          f"ring boss face to mirror rim {BOSS_X0 - MIR_R:.1f} mm")
    print(f"Mass: spinning load on the motor {spin_m:.0f} g (ring, hub, carrier, mirrors, weight), mirror group {mass_g(('tilt',)):.0f} g, "
          f"base about {mass_g(('fixed',)):.0f} g with ballast")
    print(f"Weight slug {mass_g(mats=('brass',)):.1f} g at {PAD_Y:.0f} mm from the axle")

    if a.check:
        tilt_set = [p for p in PARTS_L if p[3] == "tilt"]
        names = {p[0] for p in tilt_set}
        total = 0
        for t in range(0, 360, 15):
            bad = clashes(posed(0, t), only_with=names)
            bad = [b for b in bad if not (b[0].startswith(("axle", "bearing")) and b[1].startswith(("axle", "bearing")))]
            total += len(bad)
            if bad:
                print(f"tilt {t}: {len(bad)} clashes", bad[:6])
        print("total clashes in the tilt sweep (carrier, mirrors, weight, axle against the rest):", total)
        static = clashes(posed(0, 0))
        print("static clashes at az 0, tilt 0:", len(static), static[:12])
        return

    tag = "" if (a.az == 0 and a.tilt == 0) else f"-az{a.az:.0f}-tilt{a.tilt:.0f}"
    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_parts(a.up == "y")
    write_bom()
    assemble(a.az, a.tilt, a.up == "y").save(str(OUTD / f"spinning-mirror-assembly{tag}.step"))
    print("Wrote", OUTD / f"spinning-mirror-assembly{tag}.step")
    render(posed(a.az, a.tilt), IMG / f"spinning-mirror{tag}.png", [(14, -50, "Spinning mirror, 3/4 view"), (0, -90, "Front, mirror in the ring plane")],
           box_=(-65, 65, -65, 65, 0, ZC + 50), zoom=1.1)
    render(posed(30, 55), IMG / "spinning-mirror-tilted.png", [(16, -40, "Ring at 30 deg, mirror tilted 55 deg"), (70, -40, "From above")],
           box_=(-65, 65, -65, 65, 0, ZC + 50), zoom=1.1)
    render(posed(0, 0), IMG / "spinning-mirror-section.png", [(10, -90, "Section through the shaft (y > 0 cut away)")],
           box_=(-65, 65, -65, 65, 0, ZC + 50), zoom=1.2, cut_y=0.0)
    render(posed(0, 40), IMG / "spinning-mirror-hinge.png", [(12, -50, "Hinge close-up"), (0, -90, "Hinge, front")],
           box_=(-48, 48, -30, 30, ZC - 48, ZC + 48), zoom=1.5, hide=("base", "motor", "ballast", "rubber", "hub"))
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
