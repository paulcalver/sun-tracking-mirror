#!/usr/bin/env python3
"""CAD assembly: wall-mounted row of ten 50 mm spinning mirrors on one NEMA 17 (CadQuery). Draft, nothing built or tested.

One 2020 aluminium extrusion runs along the wall on three printed standoffs. Each unit is a printed bearing block that bolts into the top T-slot
(two M5 T-nuts) so it can slide along the rail to set its belt tension. The 5 mm spindle runs in two 625ZZ bearings in the block and carries a
double-head GT2 pulley (two toothed bands, 28 mm long) and, above it, a ring with a free hinge (3 mm axle on two 683ZZ bearings) holding a 50 mm x 1 mm
glass mirror on each face of a printed carrier. The pulley's lower band drives the belt on one side and its upper band the belt on the other, so ten short
closed 200 mm GT2 loops chain the row and every spindle turns the same way. The NEMA 17 hangs below a small printed bracket at the end of the rail,
shaft up, and drives the first loop through a single GT2 pulley. All rings are fitted at the same angle; only the tumble differs.

World frame (mm): wall plane at Y = 0, the viewer on +Y, X along the row, Z up with the rail bottom at Z = 0. Spindle line at Y = 45.
Usage (from the repo root):
  python3 cad/src/spinning_mirror_wall_row_50.py [--check] [--up y|z] [--seed N]
Writes cad/out/spinning-mirror/spinning-mirror-wall-row-50/ (assembly STEP, parts/<print|print_ready|purchase>/),
bom/bom-spinning-mirror-wall-row-50.csv and previews in cad/media/previews/spinning-mirror-wall-row-50/.
"""
import argparse
import csv
import math
import random
import sys
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spinning_mirror as sm                       # noqa: E402  (helpers)
import spinning_mirror_150_nema17 as u             # noqa: E402  (STEP writer, NEMA 17 numbers)

CAD = HERE.parent
TAG = "spinning-mirror-wall-row-50"
OUTD = CAD / "out" / "spinning-mirror" / TAG
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / TAG
BOMF = CAD.parent / "bom" / f"bom-{TAG}.csv"

box, cylz, cylx, cyly = sm.box, sm.cylz, sm.cylx, sm.cyly
PRINT_C, STEEL, MIRROR, MOTOR_C = sm.PRINT_C, sm.STEEL, sm.MIRROR, sm.MOTOR_C
ALU, BELT_C, WALL_C = "#a9b0b8", "#3a3a3a", "#e8e4dc"

# ------------------------------------------------------------------ parameters (mm)
N = 10                                         # mirrors in the row
PITCH = 80.0                                   # centre distance, set by a 200 mm GT2 loop on 20-tooth pulleys (pitch dia 12.73)
Y_R = 45.0                                     # spindle line and rail centre, out from the wall
RAIL_TOP = 20.0                                # 2020 extrusion, Z 0..20
XS = [i * PITCH for i in range(N)]
X_MOTOR = -PITCH
RAIL_X0, RAIL_L = -56.0, 850.0
RAIL_X1 = RAIL_X0 + RAIL_L
STANDOFF_X = (40.0, 400.0, 765.0)

# spindle block and bearings (625ZZ: 5 x 16 x 5)
BRG_S = (5.0, 16.0, 5.0)
BLK_X, BLK_Y, BLK_H = 20.0, 15.0, 22.0         # half length along the rail, half width, height
BLK_Z1 = RAIL_TOP + BLK_H                      # 42
TNUT_X = 15.5                                  # M5 T-nut holes at +-15.5
SPACER = 2.0                                   # two M5 washers between the upper bearing and the pulley
Z_P0 = BLK_Z1 + SPACER                         # pulley bottom, 44

# double-head GT2 20T pulley (assumed from the photo and listings: 28 mm long, 5 mm bore, grub screw in the centre boss)
P_FL, P_BAND, P_BOSS = 1.0, 8.0, 10.0
P_R_FL, P_R_TEETH, P_R_BOSS = 8.0, 6.0, 7.0
P_LEN = 2 * P_FL + 2 * P_BAND + P_BOSS         # 28
Z_BAND_LO = Z_P0 + P_FL + P_BAND / 2           # lower belt centre, 49
Z_BAND_HI = Z_P0 + P_FL + P_BAND + P_BOSS + P_BAND / 2   # upper belt centre, 67
BELT_W, BELT_T = 6.0, 1.38

# spin, ring and hinge
FOOT_Z0, FOOT_H, FOOT_X = Z_P0 + P_LEN + 0.5, 12.0, 9.0    # ring foot 0.5 mm over the pulley
SPIN_D, SPIN_BORE_R = 5.0, 2.55
R_IN, R_OUT, RING_W = 29.0, 33.0, 9.0
BRG = u.BRG                                    # 683ZZ 3 x 7 x 3
BOSS_D, BOSS_X0 = 11.0, 26.5
HUB_D, AXLE_D = 4.0, 3.0
MIR_R, MIR_T = 25.0, 1.0                       # 50 mm glass, 1 mm
CAR_T, RIM_W, BAR_W = 4.0, 2.5, 5.0                  # carrier 4 mm so the 3 mm axle and the 4 mm hubs stay inside it
ZC = FOOT_Z0 + FOOT_H + R_OUT                  # ring and mirror centre height
SPIN_TIP = FOOT_Z0 + FOOT_H + 2.5 - 0.5        # rod tip, 0.5 mm short of the end of the bore
INSERT_D = u.INSERT_D

# NEMA 17 on the bracket
WEB_Z0, WEB_Z1 = 36.0, BLK_Z1                  # web 6 mm, top flush with the bearing block tops, motor front face under it
BR_X0, BR_X1 = -106.0, -28.0                   # bracket extent along the rail
BR_THICK_X0 = RAIL_X0                          # the 22 mm thick part sits on the rail from here to BR_X1
BR_TNUT = (-50.0, -34.0)

RHO = dict(u.RHO, glass=2.5e-3, alu=2.7e-3, belt=1.1e-3)

UNIT = []
FRAME = []


def add(lst, name, wp, colour, grp, mat):
    lst.append((name, sm._shape(wp), colour, grp, mat))


def cone(r0, r1, z0, z1, x=0.0, y=0.0):
    return cq.Workplane(obj=cq.Solid.makeCone(r0, r1, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1)))


# ------------------------------------------------------------------ one unit, spindle at X = Y = 0 (local)
def build_unit():
    UNIT.clear()
    blk = box(-BLK_X, BLK_X, -BLK_Y, BLK_Y, RAIL_TOP, BLK_Z1).edges("|Z").chamfer(4.0)
    blk = blk.cut(cylz(BRG_S[1] / 2 + 0.05, RAIL_TOP - 1, RAIL_TOP + BRG_S[2]))                       # lower bearing pocket, opens onto the rail
    blk = blk.cut(cone(BRG_S[1] / 2 + 0.05, 3.0, RAIL_TOP + BRG_S[2], RAIL_TOP + BRG_S[2] + 5.05))    # 45 degree ceiling, so it prints without a bridge
    blk = blk.cut(cylz(3.0, RAIL_TOP - 1, BLK_Z1 + 1))                                                 # rod clearance
    blk = blk.cut(cylz(BRG_S[1] / 2 + 0.05, BLK_Z1 - BRG_S[2], BLK_Z1 + 1))                           # upper bearing pocket, opens upward
    for sx in (-1, 1):                                                                                 # M5 through the block into the T-nuts
        blk = blk.cut(cylz(2.75, RAIL_TOP - 1, BLK_Z1 + 1, sx * TNUT_X, 0)).cut(cylz(5.0, BLK_Z1 - 3.0, BLK_Z1 + 1, sx * TNUT_X, 0))
    add(UNIT, "print_spindle_block", blk, PRINT_C, "fixed", "print")
    for nm, z0 in (("bearing_625zz_a", RAIL_TOP), ("bearing_625zz_b", BLK_Z1 - BRG_S[2])):
        add(UNIT, nm, cylz(BRG_S[1] / 2, z0, z0 + BRG_S[2]).cut(cylz(BRG_S[0] / 2, z0 - 1, z0 + BRG_S[2] + 1)), STEEL, "fixed", "steel")

    add(UNIT, "spindle_5mm_steel_rod", cylz(SPIN_D / 2, RAIL_TOP, SPIN_TIP), STEEL, "spin", "steel")
    add(UNIT, "washers_m5_2mm_stack", cylz(4.5, BLK_Z1, Z_P0).cut(cylz(SPIN_D / 2, BLK_Z1 - 1, Z_P0 + 1)), STEEL, "spin", "steel")
    z = Z_P0
    pul = cylz(P_R_FL, z, z + P_FL)
    z += P_FL
    pul = pul.union(cylz(P_R_TEETH, z, z + P_BAND))
    z += P_BAND
    pul = pul.union(cylz(P_R_BOSS, z, z + P_BOSS))
    z += P_BOSS
    pul = pul.union(cylz(P_R_TEETH, z, z + P_BAND))
    z += P_BAND
    pul = pul.union(cylz(P_R_FL, z, z + P_FL)).cut(cylz(SPIN_D / 2, Z_P0 - 1, Z_P0 + P_LEN + 1))
    add(UNIT, "pulley_gt2_20t_double_head_5mm", pul, ALU, "spin", "alu")

    ring = cyly(R_OUT, -RING_W / 2, RING_W / 2, 0, ZC).cut(cyly(R_IN, -RING_W, RING_W, 0, ZC))
    for sx in (-1, 1):
        x0, x1 = (BOSS_X0, R_OUT) if sx > 0 else (-R_OUT, -BOSS_X0)
        ring = ring.union(cylx(BOSS_D / 2, x0, x1, 0, ZC))
        pk0, pk1 = (BOSS_X0 - 1, BOSS_X0 + BRG[2] + 0.1) if sx > 0 else (-BOSS_X0 - BRG[2] - 0.1, -BOSS_X0 + 1)
        ring = ring.cut(cylx(BRG[1] / 2 + 0.05, pk0, pk1, 0, ZC))                  # bearing pocket opens to the inside
        ring = ring.cut(cylx(1.7, 0, R_OUT + 1, 0, ZC) if sx > 0 else cylx(1.7, -R_OUT - 1, 0, 0, ZC))   # axle clearance
    foot_top = ZC - R_OUT + 2
    ring = ring.union(box(-FOOT_X, FOOT_X, -RING_W / 2, RING_W / 2, FOOT_Z0, foot_top))
    ring = ring.cut(cylz(SPIN_BORE_R, FOOT_Z0 - 1, FOOT_Z0 + FOOT_H + 2.5))         # spindle bore, ends 2.5 mm into the ring wall
    ring = ring.cut(cylx(INSERT_D / 2, 0, FOOT_X + 1, 0, FOOT_Z0 + 6.0))            # M3 heat-set insert for the grub screw, from +X
    ring = ring.intersect(box(-R_OUT - 5, R_OUT + 5, -RING_W / 2, RING_W / 2, 0, ZC + R_OUT + 5))   # bosses flush with the faces: prints flat
    add(UNIT, "print_ring_with_foot", ring, PRINT_C, "spin", "print")
    for nm, sx in (("bearing_683zz_a", 1), ("bearing_683zz_b", -1)):
        x0 = BOSS_X0 if sx > 0 else -BOSS_X0 - BRG[2]
        add(UNIT, nm, cylx(BRG[1] / 2, x0, x0 + BRG[2], 0, ZC).cut(cylx(BRG[0] / 2, x0 - 1, x0 + BRG[2] + 1, 0, ZC)), STEEL, "spin", "steel")

    rim = cylz(MIR_R, ZC - CAR_T / 2, ZC + CAR_T / 2).cut(cylz(MIR_R - RIM_W, ZC - CAR_T, ZC + CAR_T))
    bar = box(-MIR_R + 1, MIR_R - 1, -BAR_W / 2, BAR_W / 2, ZC - CAR_T / 2, ZC + CAR_T / 2)
    bar2 = box(-BAR_W / 2, BAR_W / 2, -MIR_R + 1, MIR_R - 1, ZC - CAR_T / 2, ZC + CAR_T / 2)
    car = rim.union(bar).union(bar2)
    hub_len = BOSS_X0 - 0.1
    car = car.union(cylx(HUB_D / 2, MIR_R - 1, hub_len, 0, ZC)).union(cylx(HUB_D / 2, -hub_len, -MIR_R + 1, 0, ZC))
    car = car.cut(cylx(AXLE_D / 2, -hub_len - 1, hub_len + 1, 0, ZC))
    add(UNIT, "print_mirror_carrier", car, PRINT_C, "tilt", "print")
    add(UNIT, "axle_3mm_steel_rod", cylx(AXLE_D / 2, -R_OUT, R_OUT, 0, ZC), STEEL, "tilt", "steel")
    add(UNIT, "mirror_front_glass_50", cylz(MIR_R, ZC + CAR_T / 2, ZC + CAR_T / 2 + MIR_T), MIRROR, "tilt", "glass")
    add(UNIT, "mirror_back_glass_50", cylz(MIR_R, ZC - CAR_T / 2 - MIR_T, ZC - CAR_T / 2), MIRROR, "tilt", "glass")


# ------------------------------------------------------------------ the frame: rail, standoffs, motor end, belts
def rail():
    x0, x1 = RAIL_X0, RAIL_X1
    r = box(x0, x1, Y_R - 10, Y_R + 10, 0, RAIL_TOP)
    r = r.cut(cylx(2.1, x0 - 1, x1 + 1, Y_R, 10.0))
    r = r.cut(box(x0 - 1, x1 + 1, Y_R - 3.1, Y_R + 3.1, RAIL_TOP - 1.8, RAIL_TOP + 1)).cut(box(x0 - 1, x1 + 1, Y_R - 5.5, Y_R + 5.5, RAIL_TOP - 6.1, RAIL_TOP - 1.8))
    r = r.cut(box(x0 - 1, x1 + 1, Y_R - 3.1, Y_R + 3.1, -1, 1.8)).cut(box(x0 - 1, x1 + 1, Y_R - 5.5, Y_R + 5.5, 1.8, 6.1))
    for sy in (-1, 1):                                                           # wall-side and viewer-side slots
        yf = Y_R + sy * 10.0
        ya, yb = sorted((yf - sy * 1.8, yf + sy * 1.0))
        yc, yd = sorted((yf - sy * 6.1, yf - sy * 1.8))
        r = r.cut(box(x0 - 1, x1 + 1, ya, yb, 10 - 3.1, 10 + 3.1)).cut(box(x0 - 1, x1 + 1, yc, yd, 10 - 5.5, 10 + 5.5))
    return r


def standoff():
    s = box(-10, 10, 5, Y_R - 10, 0, RAIL_TOP).union(box(-15, 15, 0, 5, 10 - 25, 10 + 25))                   # arm to the rail back, wall flange
    s = s.cut(cyly(2.75, -1, Y_R - 10 + 1, 0, 10)).cut(cyly(5.0, -1, 10, 0, 10))                          # M5 into a back-slot T-nut, head recessed
    for sz in (-1, 1):
        s = s.cut(cyly(2.25, -1, 6, 0, 10 + sz * 18))                                                       # wall screws M4
    return s


def motor_bracket():
    web = box(BR_X0, BR_X1, Y_R - 24, Y_R + 24, WEB_Z0, WEB_Z1)
    thick = box(BR_THICK_X0, BR_X1, Y_R - 20, Y_R + 20, RAIL_TOP, BLK_Z1)
    b = web.union(thick)
    b = b.cut(cylz(u.N_PILOT_R + 0.15, WEB_Z0 - 1, WEB_Z1 + 1, X_MOTOR, Y_R))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = X_MOTOR + sx * u.N_HOLE_PITCH / 2, Y_R + sy * u.N_HOLE_PITCH / 2
            b = b.cut(cylz(1.7, WEB_Z0 - 1, WEB_Z1 + 1, x, y)).cut(cylz(3.2, WEB_Z1 - 3.0, WEB_Z1 + 1, x, y))
    for x in BR_TNUT:
        b = b.cut(cylz(2.75, RAIL_TOP - 1, BLK_Z1 + 1, x, Y_R)).cut(cylz(5.0, BLK_Z1 - 3.0, BLK_Z1 + 1, x, Y_R))
    return b


def belt(xa, xb, zc):
    c = xb - xa
    ro, ri = P_R_TEETH + BELT_T, P_R_TEETH
    wp = cq.Workplane("XY").workplane(offset=zc - BELT_W / 2).center((xa + xb) / 2, Y_R)
    outer = wp.slot2D(c + 2 * ro, 2 * ro).extrude(BELT_W)
    inner = cq.Workplane("XY").workplane(offset=zc - BELT_W / 2 - 1).center((xa + xb) / 2, Y_R).slot2D(c + 2 * ri, 2 * ri).extrude(BELT_W + 2)
    return outer.cut(inner)


def build_frame():
    FRAME.clear()
    add(FRAME, "rail_2020_aluminium_850mm", rail(), ALU, "frame", "alu")
    for k, x in enumerate(STANDOFF_X):
        add(FRAME, f"print_wall_standoff_{k + 1}", standoff().translate((x, 0, 0)), PRINT_C, "frame", "print")
    add(FRAME, "print_motor_bracket", motor_bracket(), PRINT_C, "frame", "print")
    mz1 = WEB_Z0
    body = box(X_MOTOR - u.N_W / 2, X_MOTOR + u.N_W / 2, Y_R - u.N_W / 2, Y_R + u.N_W / 2, mz1 - u.N_L, mz1).edges("|Z").chamfer(u.N_CH)
    body = body.union(cylz(u.N_PILOT_R, mz1, mz1 + u.N_PILOT_H, X_MOTOR, Y_R))
    add(FRAME, "motor_nema17_60mm_body", body, MOTOR_C, "frame", "stator")
    tip = mz1 + u.N_SHAFT_L
    shaft = cylz(u.N_SHAFT_R, mz1 + u.N_PILOT_H, tip, X_MOTOR, Y_R).cut(box(X_MOTOR - 5, X_MOTOR + 5, Y_R + u.N_FLAT_Y, Y_R + 5, tip - u.N_FLAT_L, tip + 1))
    add(FRAME, "motor_nema17_shaft_5mm_D", shaft, STEEL, "frame", "steel")
    z = Z_P0
    mp = cylz(P_R_FL, z, z + P_FL, X_MOTOR, Y_R).union(cylz(P_R_TEETH, z + P_FL, z + P_FL + 7.0, X_MOTOR, Y_R)).union(cylz(P_R_BOSS, z + P_FL + 7.0, tip, X_MOTOR, Y_R))
    mp = mp.cut(cylz(u.N_SHAFT_R, z - 1, tip + 1, X_MOTOR, Y_R))
    add(FRAME, "pulley_gt2_20t_single_head_5mm", mp, ALU, "frame", "alu")
    xs = [X_MOTOR] + XS
    for k in range(N):
        add(FRAME, f"belt_gt2_6mm_200_loop_{k + 1}", belt(xs[k], xs[k + 1], Z_BAND_LO if k % 2 == 0 else Z_BAND_HI), BELT_C, "frame", "belt")


def build():
    build_unit()
    build_frame()


def pose_unit(i, az, tilt):
    out = []
    for nm, s, col, grp, mat in UNIT:
        if grp == "tilt":
            s = s.rotate((0, 0, ZC), (1, 0, ZC), tilt + 90)          # carrier is modelled flat; +90 puts tilt 0 in the ring plane
        if grp in ("tilt", "spin"):
            s = s.rotate((0, 0, 0), (0, 0, 1), az)
        out.append((f"u{i + 1}_{nm}", s.translate((XS[i], Y_R, 0)), col, f"unit{i + 1}_{grp}", mat))
    return out


def all_parts(poses):
    out = list(FRAME)
    for i, (az, t) in enumerate(poses):
        out += pose_unit(i, az, t)
    return out


def poses_same_angle(seed):
    rnd = random.Random(seed)
    return [(0.0, rnd.uniform(0, 360)) for _ in range(N)]            # all rings at the same angle, the tumble differs


def inertia_unit(tilt):
    """Spin-axis inertia (kg m2) of one unit's turning parts about its own spindle, mirror at the given tilt."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    tot = 0.0
    for nm, s, _, grp, mat in UNIT:
        if grp not in ("spin", "tilt"):
            continue
        if grp == "tilt":
            s = s.rotate((0, 0, ZC), (1, 0, ZC), tilt + 90)
        p = GProp_GProps()
        BRepGProp.VolumeProperties_s(s.wrapped, p)
        c = p.CentreOfMass()
        tot += p.MatrixOfInertia().Value(3, 3) * RHO[mat] + p.Mass() * RHO[mat] * (c.X() ** 2 + c.Y() ** 2)
    return tot * 1e-9


def unit_mass_g(grps):
    return sum(s.Volume() * RHO[m] for _, s, _, g, m in UNIT if g in grps)


def frame_mass_g():
    return sum(s.Volume() * RHO[m] for _, s, _, _, m in FRAME)


# ------------------------------------------------------------------ export
def print_oriented(nm, s):
    if nm == "print_ring_with_foot":
        s = s.rotate((0, 0, 0), (1, 0, 0), 90)                      # flat, +Y face up
    elif nm == "print_motor_bracket":
        s = s.rotate((0, 0, 0), (1, 0, 0), 180)                     # upside down, the flat top on the bed
    elif nm.startswith("print_wall_standoff"):
        s = s.rotate((0, 0, 0), (1, 0, 0), 90)                      # flange on the bed
    bb = s.BoundingBox()
    return s.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def export_all(yup):
    for sub in ("print", "print_ready", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")):
            old.unlink()

    def put(nm, s):
        sh = s.rotate((0, 0, 0), (1, 0, 0), -90) if yup else s
        u.write_step(nm, sh, PARTS / ("print" if nm.startswith("print_") else "purchase") / f"{nm}.step")
        if nm.startswith("print_"):
            u.write_step(nm, print_oriented(nm, s), PARTS / "print_ready" / f"{nm}.step")
    for nm, s, *_ in UNIT:
        put(nm, s)
    for nm, s, *_ in FRAME:
        if nm.startswith("print_wall_standoff_") and not nm.endswith("_1"):
            continue                                                  # the three standoffs are identical
        if nm.startswith("belt_gt2") and not nm.endswith("_1"):
            continue
        put(nm.replace("print_wall_standoff_1", "print_wall_standoff").replace("belt_gt2_6mm_200_loop_1", "belt_gt2_6mm_200_loop"),
            s.translate((-STANDOFF_X[0], 0, 0)) if nm == "print_wall_standoff_1" else s)
    print("Wrote part STEP files to", PARTS)


def assemble(poses, yup):
    root = cq.Assembly(name="spinning_mirror_wall_row_50")
    subs = {}
    for nm, s, col, grp, _ in all_parts(poses):
        if yup:
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        subs.setdefault(grp, cq.Assembly(name=grp)).add(s, name=nm, color=sm.cqc(col))
    for a in subs.values():
        root.add(a)
    return root


def write_bom():
    rows = [
        ("print", f"PETG or ASA, matt black: ring with foot, mirror carrier, spindle bearing block (x{N} each); print the ring flat, +Y up", 3 * N, "Bambu P1S, 0.4 mm, 0.2 mm layers, 4 walls; ream the bearing pockets and the 5 mm bore"),
        ("print", "PETG or ASA: motor bracket (print upside down) and wall standoff (flange on the bed)", 1 + len(STANDOFF_X), "bracket x1, standoff x3"),
        ("buy", "Aluminium extrusion 2020 (T-slot, 6 mm slot), cut to 850 mm", 1, "the rail; deburr the ends"),
        ("buy", "NEMA 17 stepper 42/60 (The Pi Hut, 60 mm body): 1.68 A, 0.64 N m holding, 5 mm D shaft, 0.5 kg", 1, "check the shaft length (24 mm assumed) and the front-face thread depth"),
        ("buy", "Adafruit TMC2209 stepper driver breakout with heatsink; set the current about 1.2 to 1.5 A", 2, "one spare; see the 150 mm wiring doc"),
        ("buy", "ESP32 dev board, one random-walk speed setpoint shared by the row, acceleration limited; step pulses from the RMT or a timer", 1, "serial or OSC control from Max is possible"),
        ("buy", "24 V 3 A supply, DC jack, inline fuse, 100 uF 35 V capacitor, wiring", 1, "same as the single 150 mm rig"),
        ("buy", "GT2 20T 5 mm bore double-head pulley for 6 mm belt (Technobots 6001-071)", N, "two toothed bands, set screw in the centre boss; length about 28 mm, check on arrival"),
        ("buy", "GT2 20T 5 mm bore single pulley for 6 mm belt (Technobots 6001-002)", 2, "motor pulley plus a spare"),
        ("buy", "GT2 6 mm closed belt, 200 mm (Technobots 6001-376)", N, "ten links, one per unit; stock 10"),
        ("buy", "Bearing 625ZZ (5 x 16 x 5), spindles", 2 * N + 2, "2 per unit plus 2 spare"),
        ("buy", "Bearing 683ZZ (3 x 7 x 3), mirror hinges", 2 * N + 2, "2 per unit plus 2 spare"),
        ("buy", "Stainless rod 5 mm x 67 mm cut from 1 m (spindle), flat ground for the grub screws", N, "drawn rod can run oversize: test-fit a bearing"),
        ("buy", "Stainless rod 3 mm x 66 mm cut from 1 m (hinge axle), glue into the carrier", N, ""),
        ("buy", "Glass mirror 50 mm round, 1 mm, seamed edges, rear silvered", 2 * N + 2, "2 per unit plus 2 spare; mirror-safe tape or neutral silicone"),
        ("buy", "M5 drop-in T-nut for a 6 mm slot", 2 * N + 2 + len(STANDOFF_X) + 4, "2 per unit, 2 for the bracket, 1 per standoff, a few spare"),
        ("buy", f"Screws: M5 x 25 button head ({2 * N + 2}, block and bracket), M5 x 35 ({len(STANDOFF_X)}, standoffs), M5 washer 1 mm ({2 * N * 2}, spindle spacers, 2 per unit), M3 x 6 cap ({4}, motor), M3 x 5 grub ({N}, ring foot), M4 x 40 wall screws with plugs ({2 * len(STANDOFF_X)})", 1, "set; thread-lock the grub and set screws"),
        ("buy", "Heat-set inserts M3 x 5.7", N + 2, "one per ring foot, 2 spare"),
        ("buy", "Thread-locking compound (medium), CA glue, 1 mm foam mounting tape, neutral-cure silicone, wall plugs for the wall type", 1, "set"),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--up", choices=("y", "z"), default="y")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    build()
    i_lo, i_hi = inertia_unit(0), inertia_unit(90)
    rotor = u.N_ROTOR_I
    row_lo, row_hi = N * i_lo + rotor, N * i_hi + rotor
    print(f"Row: {N} units at {PITCH:.0f} mm pitch, spindle line {Y_R:.0f} mm from the wall, rail {RAIL_L:.0f} mm; ring swept diameter {2 * R_OUT:.0f} mm, {PITCH - 2 * R_OUT:.0f} mm between rings, "
          f"{Y_R - R_OUT:.0f} mm to the wall")
    print(f"Heights above the rail bottom: pulley {Z_P0:.0f}..{Z_P0 + P_LEN:.0f}, belts at {Z_BAND_LO:.0f} and {Z_BAND_HI:.0f}, ring centre {ZC:.1f}, ring top {ZC + R_OUT:.1f}")
    print(f"One unit: turning mass {unit_mass_g(('spin', 'tilt')):.0f} g (mirror group {unit_mass_g(('tilt',)):.0f} g), spin inertia {i_lo:.2e} to {i_hi:.2e} kg m2; "
          f"row incl. rotor {row_lo:.2e} to {row_hi:.2e} kg m2; torque for 100 rad/s2 {row_hi * 100:.3f} N m, for 300 rad/s2 {row_hi * 300:.3f} N m (before friction)")
    print(f"Mass: frame about {frame_mass_g() / 1000:.2f} kg, {N} units about {N * unit_mass_g(('fixed', 'spin', 'tilt')) / 1000:.2f} kg")
    if a.check:
        multi = [(nm, len(s.Solids())) for nm, s, *_ in UNIT + FRAME if nm.startswith("print_") and len(s.Solids()) != 1]
        print("printed parts that are not a single solid:", multi or "none")
        ok = lambda b: not (b[0].split("_", 1)[1].startswith(("axle", "bearing")) and b[1].split("_", 1)[1].startswith(("axle", "bearing")))
        moving = lambda P: {p[0] for p in P if "_spin" in p[3] or "_tilt" in p[3]}
        total = 0
        for seed in range(3):
            P = all_parts(poses_same_angle(seed))
            bad = [b for b in sm.clashes(P, only_with=moving(P)) if ok(b)]
            total += len(bad)
            if bad:
                print(f"seed {seed}: {len(bad)} clashes", bad[:8])
        print("total clashes over 3 random tumble poses, moving parts against everything:", total)
        P = [(f"{n}", s, c, g, m) for n, s, c, g, m in all_parts([(0, 0)] * N)]
        static = sm.clashes(P)
        print("static clashes at az 0, tilt 0 (all parts):", len(static), static[:12])
        return

    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_all(a.up == "y")
    write_bom()
    P0 = poses_same_angle(a.seed)
    assemble(P0, a.up == "y").save(str(OUTD / f"{TAG}-assembly.step"))
    print("Wrote", OUTD / f"{TAG}-assembly.step")
    P = all_parts(P0)
    bx = (-130, 830, 0, 160, -30, 190)
    sm.render(P, IMG / "overview.png", [(16, 62, "Ten 50 mm mirrors on one NEMA 17, wall mounted")], box_=(-130, 830, 0, 120, -30, 190), zoom=1.6)
    sm.render(P, IMG / "front.png", [(0, 90, "View from the room (X runs right to left)")], box_=bx, zoom=1.7)
    sm.render(P, IMG / "plan.png", [(90, -90, "Plan")], box_=(-130, 830, 0, 100, -30, 190), zoom=1.7)
    sm.render(P, IMG / "motor-end.png", [(18, 40, "Motor end: bracket, NEMA 17, first two units")], box_=(-120, 200, 0, 100, -30, 190), zoom=1.2)
    sm.render(P, IMG / "unit-section.png", [(4, 90, "Section through the spindles (y > 45 cut away)")], box_=(-120, 200, 0, 100, -30, 190), zoom=1.2, cut_y=Y_R)
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
