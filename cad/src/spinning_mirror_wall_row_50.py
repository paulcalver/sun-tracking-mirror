#!/usr/bin/env python3
"""CAD assembly: wall-mounted piece of 3 rows of eight 50 mm spinning mirrors, one NEMA 17 per row (CadQuery). Draft, nothing built or tested.

One 2020 aluminium extrusion per row runs along the wall, tied back to three vertical 2020 uprights standing in the gaps between units. Each unit is a printed bearing block that bolts into the top T-slot
(two M5 T-nuts) so it can slide along the rail to set its belt tension. The 5 mm spindle runs in two 625ZZ bearings in the block and carries a
double-head GT2 pulley (two toothed bands, 28 mm long) and, above it, a ring with a free hinge (3 mm axle on two 683ZZ bearings) holding a 50 mm x 1 mm
glass mirror on each face of a printed carrier. The pulley's lower band drives the belt on one side and its upper band the belt on the other, so eight short
closed 200 mm GT2 loops chain each row and every spindle turns the same way. The NEMA 17 hangs below a small printed bracket at the end of the rail,
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
N = 8                                          # mirrors per row
ROWS = 3                                       # rows, one NEMA 17 each
ROW_PITCH = 200.0                              # vertical distance between rails (ring top is 150 above its rail bottom)
PITCH = 80.0                                   # centre distance, set by a 200 mm GT2 loop on 20-tooth pulleys (pitch dia 12.73)
Y_R = 45.0                                     # spindle line and rail centre, out from the wall
RAIL_TOP = 20.0                                # 2020 extrusion, Z 0..20
XS = [i * PITCH for i in range(N)]
X_MOTOR = -PITCH
RAIL_X0, RAIL_L = -56.0, 680.0
RAIL_X1 = RAIL_X0 + RAIL_L
UPRIGHT_X = (40.0, 360.0, 600.0)               # vertical 2020 uprights in the gaps between units (and one past the last unit)
UPRIGHT_Y0, UPRIGHT_Y1 = 5.0, 25.0             # 20 mm deep, 5 mm off the wall; the ring sweep stays 6 mm clear of it
UPRIGHT_Z0 = 0.0
UPRIGHT_Z1 = (ROWS - 1) * ROW_PITCH + 40.0      # 440
TIE_Y1 = 58.0                                  # rail tie reaches from the upright face (25) to 3 mm past the rail front (55)
WALL_PLATE_Z = (60.0, 360.0)                   # two printed wall plates per upright

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

# electronics box, hung under the rail by two M5 screws into slide-in T-nuts in the bottom slot; the lid carries a 7 x 9 cm perfboard
EB_X0, EB_X1, EB_Y0, EB_Y1 = -46.0, 78.0, 6.0, 84.0        # 124 x 78 outside, clear of the wall plates and the uprights (the box top touches the upright ends)
EB_TOP_T, EB_WALL, EB_LID_T = 6.0, 3.0, 3.0
EB_Z_LID = -44.0                                           # lid bottom; box top flush against the rail bottom at Z = 0
EB_ZIN0, EB_ZIN1 = EB_Z_LID + EB_LID_T, -EB_TOP_T          # interior floor (lid top) -41, ceiling -6
EB_POST = 7.0                                              # lid-screw corner posts
EB_MOUNT_X = (-14.0, 52.0)                                 # M5 holes, heads recessed in the top plate
BOARD_L, BOARD_W, BOARD_T, BOARD_CX = 90.0, 70.0, 1.6, 13.0
BOARD_POST_H = 7.0
BOARD_HOLES = [(BOARD_CX + sx * 41.0, Y_R + sy * 31.0) for sx in (-1, 1) for sy in (-1, 1)]    # 82 x 62 mm hole spacing
EB_CORNERS = [(x, y) for x in (EB_X0 + EB_WALL + EB_POST / 2, EB_X1 - EB_WALL - EB_POST / 2) for y in (EB_Y0 + EB_WALL + EB_POST / 2, EB_Y1 - EB_WALL - EB_POST / 2)]
EB_CUT_Z = (EB_ZIN0 + EB_ZIN1) / 2                         # connector height, -23.5

RHO = dict(u.RHO, glass=2.5e-3, alu=2.7e-3, belt=1.1e-3, ph=0.3e-3)

UNIT = []
ROW = []                                       # one row of frame parts (rail, ties, bracket, motor, belts) at Z = 0
ELEC = []                                      # the single electronics box
FRAME = []                                     # everything that does not move, all rows


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
    add(UNIT, "washers_m5_2mm_stack", cylz(6.25, BLK_Z1, Z_P0).cut(cylz(2.65, BLK_Z1 - 1, Z_P0 + 1)), STEEL, "spin", "steel")      # two 12.5 x 5.3 x 1 mm panel washers
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


# ------------------------------------------------------------------ the frame: rail, ties, uprights, motor end, belts
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


def upright2020(xc, z0, z1):
    """Vertical 2020 extrusion centred at x = xc, y = 15 (simplified T-slot profile, slot opening 6.2, cavity 11 x 6.1 deep)."""
    yc = (UPRIGHT_Y0 + UPRIGHT_Y1) / 2
    r = box(xc - 10, xc + 10, yc - 10, yc + 10, z0, z1).cut(cylz(2.1, z0 - 1, z1 + 1, xc, yc))
    for sy in (-1, 1):
        yf = yc + sy * 10.0
        ya, yb = sorted((yf - sy * 1.8, yf + sy * 1.0))
        yg, yh = sorted((yf - sy * 6.1, yf - sy * 1.8))
        r = r.cut(box(xc - 3.1, xc + 3.1, ya, yb, z0 - 1, z1 + 1)).cut(box(xc - 5.5, xc + 5.5, yg, yh, z0 - 1, z1 + 1))
    for sx in (-1, 1):
        xf = xc + sx * 10.0
        xa, xb = sorted((xf - sx * 1.8, xf + sx * 1.0))
        xg, xh = sorted((xf - sx * 6.1, xf - sx * 1.8))
        r = r.cut(box(xa, xb, yc - 3.1, yc + 3.1, z0 - 1, z1 + 1)).cut(box(xg, xh, yc - 5.5, yc + 5.5, z0 - 1, z1 + 1))
    return r


def rail_tie(xu):
    """Printed block on top of a rail in the gap between two units: two M5 x 12 down into the rail's top-slot T-nuts, one M5 x 35 along Y
    into a T-nut in the upright's front slot (heads recessed)."""
    t = box(xu - 13, xu + 13, UPRIGHT_Y1, TIE_Y1, RAIL_TOP, RAIL_TOP + 10)
    for dx in (-6.0, 6.0):
        t = t.cut(cylz(2.75, RAIL_TOP - 1, RAIL_TOP + 11, xu + dx, Y_R)).cut(cylz(5.0, RAIL_TOP + 7.2, RAIL_TOP + 11, xu + dx, Y_R))
    t = t.cut(cyly(2.75, UPRIGHT_Y1 - 1, TIE_Y1 + 1, xu, RAIL_TOP + 4.0)).cut(cyly(5.0, TIE_Y1 - 3.0, TIE_Y1 + 1, xu, RAIL_TOP + 4.0))
    return t


def wall_plate(xu, zc):
    """Printed plate between the wall and an upright: one M5 x 12 from the wall side into a T-nut in the upright's back slot, two M4 wall screws either side."""
    w = box(xu - 28, xu + 28, 0.0, 5.0, zc - 20, zc + 20)
    w = w.cut(cyly(2.75, -1, 6, xu, zc)).cut(cyly(5.0, -1, 3.0, xu, zc))
    for dx in (-22.0, 22.0):
        w = w.cut(cyly(2.25, -1, 6, xu + dx, zc)).cut(cyly(4.5, 3.0, 6, xu + dx, zc))
    return w


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


def electronics_box():
    w = EB_WALL
    b = box(EB_X0, EB_X1, EB_Y0, EB_Y1, EB_ZIN0, 0.0)
    b = b.cut(box(EB_X0 + w, EB_X1 - w, EB_Y0 + w, EB_Y1 - w, EB_ZIN0 - 1, EB_ZIN1))
    for (x, y) in EB_CORNERS:                                                    # corner posts, M3 heat-set insert in the lower end
        b = b.union(box(x - EB_POST / 2, x + EB_POST / 2, y - EB_POST / 2, y + EB_POST / 2, EB_ZIN0, EB_ZIN1 + 1))
        b = b.cut(cylz(INSERT_D / 2, EB_ZIN0 - 1, EB_ZIN0 + 8.0, x, y))
    for x in EB_MOUNT_X:                                                         # M5 up into the T-nuts in the rail's bottom slot, head recessed
        b = b.cut(cylz(2.75, EB_ZIN1 - 1, 1.0, x, Y_R)).cut(cylz(5.0, EB_ZIN1 - 1, EB_ZIN1 + 3.5, x, Y_R))
    b = b.cut(cylx(6.0, EB_X1 - w - 1, EB_X1 + 1, Y_R - 18, EB_CUT_Z))            # DC barrel jack, 12 mm
    b = b.cut(box(EB_X1 - w - 1, EB_X1 + 1, Y_R + 18 - 5.5, Y_R + 18 + 5.5, EB_CUT_Z - 2.3, EB_CUT_Z + 2.3))   # USB-C panel socket, 11 x 4.6
    for dy in (-20.0, 0.0, 20.0):                                                # three motor leads with their plugs, 14 mm holes
        b = b.cut(cylx(7.0, EB_X0 - 1, EB_X0 + w + 1, Y_R + dy, EB_CUT_Z))
    return b


def electronics_lid():
    lid = box(EB_X0, EB_X1, EB_Y0, EB_Y1, EB_Z_LID, EB_ZIN0)
    for (x, y) in EB_CORNERS:
        lid = lid.cut(cylz(1.7, EB_Z_LID - 1, EB_ZIN0 + 1, x, y)).cut(cylz(3.2, EB_Z_LID - 1, EB_Z_LID + 1.5, x, y))
    for (x, y) in BOARD_HOLES:                                                   # perfboard posts with M3 heat-set inserts
        lid = lid.union(cylz(3.5, EB_ZIN0, EB_ZIN0 + BOARD_POST_H, x, y)).cut(cylz(INSERT_D / 2, EB_ZIN0 + 0.5, EB_ZIN0 + BOARD_POST_H + 1, x, y))
    for x in (-10.0, 0.0, 10.0, 20.0, 30.0, 40.0):                                # vent slots
        lid = lid.cut(box(x - 1.5, x + 1.5, Y_R - 20, Y_R + 20, EB_Z_LID - 1, EB_ZIN0 + 1))
    return lid


def build_frame():
    ROW.clear()
    ELEC.clear()
    add(ROW, f"rail_2020_aluminium_{int(RAIL_L)}mm", rail(), ALU, "frame", "alu")
    for k, x in enumerate(UPRIGHT_X):
        add(ROW, f"print_rail_tie_{k + 1}", rail_tie(x), PRINT_C, "frame", "print")
    add(ROW, "print_motor_bracket", motor_bracket(), PRINT_C, "frame", "print")
    mz1 = WEB_Z0
    body = box(X_MOTOR - u.N_W / 2, X_MOTOR + u.N_W / 2, Y_R - u.N_W / 2, Y_R + u.N_W / 2, mz1 - u.N_L, mz1).edges("|Z").chamfer(u.N_CH)
    body = body.union(cylz(u.N_PILOT_R, mz1, mz1 + u.N_PILOT_H, X_MOTOR, Y_R))
    add(ROW, "motor_nema17_60mm_body", body, MOTOR_C, "frame", "stator")
    tip = mz1 + u.N_SHAFT_L
    shaft = cylz(u.N_SHAFT_R, mz1 + u.N_PILOT_H, tip, X_MOTOR, Y_R).cut(box(X_MOTOR - 5, X_MOTOR + 5, Y_R + u.N_FLAT_Y, Y_R + 5, tip - u.N_FLAT_L, tip + 1))
    add(ROW, "motor_nema17_shaft_5mm_D", shaft, STEEL, "frame", "steel")
    z = Z_P0
    mp = cylz(P_R_FL, z, z + P_FL, X_MOTOR, Y_R).union(cylz(P_R_TEETH, z + P_FL, z + P_FL + 7.0, X_MOTOR, Y_R)).union(cylz(P_R_BOSS, z + P_FL + 7.0, tip, X_MOTOR, Y_R))
    mp = mp.cut(cylz(u.N_SHAFT_R, z - 1, tip + 1, X_MOTOR, Y_R))
    add(ROW, "pulley_gt2_20t_single_head_5mm", mp, ALU, "frame", "alu")
    xs = [X_MOTOR] + XS
    for k in range(N):
        add(ROW, f"belt_gt2_6mm_200_loop_{k + 1}", belt(xs[k], xs[k + 1], Z_BAND_LO if k % 2 == 0 else Z_BAND_HI), BELT_C, "frame", "belt")


    for k, x in enumerate(UPRIGHT_X):
        add(ELEC, f"upright_2020_aluminium_{int(UPRIGHT_Z1 - UPRIGHT_Z0)}mm_{k + 1}", upright2020(x, UPRIGHT_Z0, UPRIGHT_Z1), ALU, "frame", "alu")
        for j, zc in enumerate(WALL_PLATE_Z):
            add(ELEC, f"print_wall_plate_{k + 1}{'ab'[j]}", wall_plate(x, zc), PRINT_C, "frame", "print")
    add(ELEC, "print_electronics_box", electronics_box(), PRINT_C, "frame", "print")
    add(ELEC, "print_electronics_lid", electronics_lid(), PRINT_C, "frame", "print")
    zb = EB_ZIN0 + BOARD_POST_H
    add(ELEC, "placeholder_perfboard_70x90", box(BOARD_CX - BOARD_L / 2, BOARD_CX + BOARD_L / 2, Y_R - BOARD_W / 2, Y_R + BOARD_W / 2, zb, zb + BOARD_T), "#2e6f4e", "frame", "ph")
    add(ELEC, "placeholder_esp32_55x28x22", box(BOARD_CX - 42, BOARD_CX + 13, Y_R - 33, Y_R - 5, zb + BOARD_T, zb + BOARD_T + 22), "#2e6f4e", "frame", "ph")
    for k in range(3):                                                           # one TMC2209 per row
        x0 = BOARD_CX - 44 + k * 28.0
        add(ELEC, f"placeholder_tmc2209_25x20x16_{k + 1}", box(x0, x0 + 25, Y_R + 5, Y_R + 25, zb + BOARD_T, zb + BOARD_T + 16), "#2e6f4e", "frame", "ph")


def build():
    build_unit()
    build_frame()
    FRAME.clear()
    for r in range(ROWS):
        for nm, sh, col, grp, mat in ROW:
            FRAME.append((f"r{r + 1}_{nm}", sh.translate((0, 0, r * ROW_PITCH)), col, f"row{r + 1}_{grp}", mat))
    FRAME.extend(ELEC)


def pose_unit(i, az, tilt, r=0):
    out = []
    for nm, s, col, grp, mat in UNIT:
        if grp == "tilt":
            s = s.rotate((0, 0, ZC), (1, 0, ZC), tilt + 90)          # carrier is modelled flat; +90 puts tilt 0 in the ring plane
        if grp in ("tilt", "spin"):
            s = s.rotate((0, 0, 0), (0, 0, 1), az)
        out.append((f"r{r + 1}u{i + 1}_{nm}", s.translate((XS[i], Y_R, r * ROW_PITCH)), col, f"r{r + 1}unit{i + 1}_{grp}", mat))
    return out


def all_parts(poses):
    out = list(FRAME)
    for k, (az, t) in enumerate(poses):
        out += pose_unit(k % N, az, t, k // N)
    return out


def poses_same_angle(seed):
    rnd = random.Random(seed)
    return [(0.0, rnd.uniform(0, 360)) for _ in range(N * ROWS)]            # all rings at the same angle, the tumble differs


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
    elif nm in ("print_motor_bracket", "print_electronics_box"):
        s = s.rotate((0, 0, 0), (1, 0, 0), 180)                     # upside down, the flat top on the bed
    elif nm.startswith("print_wall_plate"):
        s = s.rotate((0, 0, 0), (1, 0, 0), 90)                      # flat on the bed
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
    for nm, s, *_ in ROW + ELEC:
        if (nm.startswith("print_rail_tie_") and not nm.endswith("_1")) or (nm.startswith("print_wall_plate_") and not nm.endswith("1a")) \
                or (nm.startswith("upright_2020") and not nm.endswith("_1")):
            continue                                                  # the ties, plates and uprights are identical
        if nm.startswith("belt_gt2") and not nm.endswith("_1"):
            continue
        if nm.startswith("placeholder_tmc2209") and not nm.endswith("_1"):
            continue
        dx = UPRIGHT_X[0] if nm in ("print_rail_tie_1", "print_wall_plate_1a") or nm.startswith("upright_2020") else 0.0
        put(nm.replace("print_rail_tie_1", "print_rail_tie").replace("print_wall_plate_1a", "print_wall_plate").replace("belt_gt2_6mm_200_loop_1", "belt_gt2_6mm_200_loop")
            .replace("upright_2020_aluminium_440mm_1", "upright_2020_aluminium_440mm"), s.translate((-dx, 0, 0)))
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
    U, R = N * ROWS, ROWS                                      # units, rows
    UPR = len(UPRIGHT_X)
    TIES, PLATES = UPR * R, 2 * UPR                            # rail ties, wall plates
    rows = [
        ("print", "Ring with foot: PETG or ASA, matt black, print flat with the +Y face up, 4 walls", U, "ream the two 7.05 mm bearing pockets and the 5.1 mm spindle bore"),
        ("print", "Mirror carrier: print flat, 4 walls", U, ""),
        ("print", "Spindle bearing block: print upright, 4 walls", U, "ream the two 16 mm pockets so a 625ZZ presses in"),
        ("print", "Motor bracket: print upside down on its flat top face", R, "one per row"),
        ("print", "Rail tie: print as modelled; sits on a rail in a gap between units and bolts to an upright", TIES, f"{UPR} per rail"),
        ("print", "Wall plate: print flat; goes between the wall and an upright", PLATES, "2 per upright"),
        ("print", "Electronics box: print upside down on the flat top plate; 124 x 78 x 44 mm, hangs under the bottom rail", 1, "inside 118 x 72 x 35 mm"),
        ("print", "Electronics box lid: print flat; carries the perfboard posts", 1, ""),
        ("buy", f"Aluminium extrusion 2020 (T-slot, 6 mm slot, 20 x 20 mm), cut to {int(RAIL_L)} mm", R, "one rail per row; deburr the ends"),
        ("buy", f"Aluminium extrusion 2020 (T-slot, 6 mm slot, 20 x 20 mm), cut to {int(UPRIGHT_Z1 - UPRIGHT_Z0)} mm", UPR, "vertical uprights behind the rails, 5 mm off the wall; deburr the ends"),
        ("buy", "NEMA 17 stepper 42/60 (The Pi Hut, 60 mm body): 1.68 A, 0.64 N m holding, 5 mm D shaft, 0.5 kg", R, "one per row; check the shaft length (24 mm assumed) and the front-face thread depth"),
        ("buy", "Adafruit TMC2209 stepper driver breakout (DigiKey 1528-6121-ND); set the current about 1.2 to 1.5 A", R + 1, "one per row plus a spare"),
        ("buy", "Aluminium SMT heat sink 6.35 x 6.35 x 3.8 mm (0.25 x 0.25 x 0.15 in), 10 pack, stuck on each TMC2209 chip", R + 1, "one per driver; check it fits the chip"),
        ("buy", "ESP32 dev board (38-pin); three step/dir outputs from the RMT or timers, acceleration limited", 1, "serial or OSC control from Max is possible"),
        ("buy", "24 V 5 A DC supply, 5.5 x 2.1 mm plug", 1, "3 motors at 1.2 to 1.5 A"),
        ("buy", "Inline fuse holder with 5 A blade fuses", 1, "fuse in the 24 V lead"),
        ("buy", "Electrolytic capacitor 100 uF, 35 V or higher", R + 1, "one across each driver's + and GND terminals, plus a spare"),
        ("buy", "Lever connectors 5-way (Wago 221-415) for 24 V and GND distribution", 2, ""),
        ("buy", "4-pin 2.54 mm motor extension cable: 1 m (x2) for rows 2 and 3, 0.5 m (x1) for row 1", 3, "the motor leads are short; run extensions up the wall"),
        ("buy", "Wire 22 AWG silicone red/black and 26 AWG logic, ferrules, heat shrink, cable ties", 1, "set"),
        ("buy", "Perfboard 70 x 90 mm, mounting holes 82 x 62 mm, with female header sockets for the ESP32 and drivers", 1, "check the hole spacing of your board"),
        ("buy", "Female DC power adapter, 2.1 mm jack to screw terminal block (The Pi Hut)", 1, "no panel flange: it sits behind the 12 mm hole in the right-hand wall, so glue or clip it in; check the socket diameter"),
        ("buy", "USB-C panel-mount extension cable (11 x 4.6 mm slot)", 1, "right-hand end wall of the box"),
        ("buy", "Rubber grommet for a 14 mm hole", R, "one per motor lead, left-hand wall of the box"),
        ("buy", "GT2 20T 5 mm bore double-head pulley for 6 mm belt (Technobots 6001-071)", U + 2, "two toothed bands, set screw in the centre boss, about 28 mm long (check on arrival); 2 spare"),
        ("buy", "GT2 20T 5 mm bore single pulley for 6 mm belt (Technobots 6001-002)", R + 1, "motor pulleys plus a spare"),
        ("buy", "GT2 6 mm closed belt, 200 mm (Technobots 6001-376)", U + 2, f"{N} loops per row; 2 spare"),
        ("buy", "Bearing 625ZZ (5 x 16 x 5), spindles", 2 * U + 4, "2 per unit plus 4 spare"),
        ("buy", "Bearing 683ZZ (3 x 7 x 3), mirror hinges", 2 * U + 4, "2 per unit plus 4 spare"),
        ("buy", f"Stainless rod 5 mm x 300 mm (AOOSU, pack of 4), each cut into 4 spindles of 67 mm", -(-U // 4), "flat ground for the grub screws; drawn rod can run oversize, test-fit a bearing"),
        ("buy", f"Stainless rod 3 mm x 1 m, cut into {U} hinge axles of 66 mm", 2, "glue into the carrier"),
        ("buy", "Glass mirror 50 mm round, 1 mm thick, seamed edges, rear silvered", 2 * U + 4, "2 per unit plus 4 spare; mount with mirror-safe tape or neutral silicone"),
        ("buy", "M5 slide-in T-nut for a 6 mm slot (20 series, zinc plated)", 2 * U + 2 * R + 3 * TIES + PLATES + 2 + 4, "2 per unit, 2 per motor bracket, 3 per rail tie (2 in the rail, 1 in the upright front slot), 1 per wall plate (upright back slot), 2 for the box, spares; load them into the slot from the rail end before building"),
        ("buy", "M5 x 25 button head screw, stainless", 2 * U + 2 * R + 6, "2 per unit (block into the T-nuts) plus 2 per motor bracket, spares"),
        ("buy", "M5 x 35 screw, stainless", TIES + 1, "1 per rail tie, along Y into the upright front-slot T-nut; 1 spare"),
        ("buy", "M5 x 12 button head screw, stainless", 2 * TIES + PLATES + 2 + 4, "2 per rail tie (into the rail), 1 per wall plate (into the upright), 2 for the electronics box, spares"),
        ("buy", "M5 panel/slot washer 12.5 x 5.3 x 1 mm, stainless", 2 * U + 2, "2 per spindle as a 2 mm spacer on the inner race of the upper bearing; spares; 12.5 mm just clears the bearing's outer-race shoulder (about 13 mm), so check it does not rub"),
        ("buy", "M3 x 6 socket cap head screw, stainless", 4 * R + 2, "4 per motor into the front face; check the thread depth first"),
        ("buy", "M3 x 5 cup-point grub screw, stainless", U + 2, "1 per ring foot, clamps the ring to the spindle; thread-lock"),
        ("buy", "M3 x 8 pan head screw, stainless", 6, "4 hold the electronics box lid; 2 spare"),
        ("buy", "M3 x 6 pan head screw, stainless", 6, "4 hold the perfboard to the lid posts; 2 spare"),
        ("buy", "M4 x 40 wall screw with plug to suit your wall", 2 * PLATES + 2, "2 per wall plate; choose the plug for the wall type"),
        ("buy", "Heat-set insert M3 x 5.7", U + 8 + 4, "1 per ring foot, 4 box corners, 4 perfboard posts, spares"),
        ("buy", "Thread-locking compound (medium)", 1, "grub screws and pulley set screws"),
        ("buy", "Cyanoacrylate glue or retaining compound", 1, "glue the hinge axles into the carriers"),
        ("buy", "Double-sided foam mounting tape 1 mm and neutral-cure silicone", 1, "mirrors onto the carriers"),
    ]
    VAT = 1.2
    # (substring of the item, unit price per piece ex VAT, quantity bought, supplier). Technobots and the extrusion shop show ex VAT; Amazon UK shows
    # inc VAT, so those are divided by 1.2. Pack prices: 625ZZ 20 for 8.59, 683ZZ 10 for 6.59, 5 mm rods 4 for 5.99.
    prices = [
        ("NEMA 17 stepper 42/60", 54.00 / VAT / 3, 3, "The Pi Hut (3 for 54.00 inc VAT, divided by 1.2)"),
        ("Adafruit TMC2209", 6.69, 7, "DigiKey UK 1528-6121-ND (ex VAT)"),
        ("Aluminium SMT heat sink", 4.80 / VAT / 10, 10, "The Pi Hut (10-pack 4.80 inc VAT)"),
        ("Female DC power adapter", 4.50 / VAT / 3, 3, "The Pi Hut (3 for 4.50 inc VAT)"),
        ("GT2 6 mm closed belt", 1.34, 26, "Technobots 6001-376"),
        ("double-head pulley", 1.47, 26, "Technobots 6001-071"),
        ("GT2 20T 5 mm bore single pulley", 1.48, 4, "Technobots 6001-002"),
        ("Bearing 625ZZ", 8.59 / VAT / 20, 60, "Amazon UK, sourcing map 20-pack x 3"),
        ("Bearing 683ZZ", 6.59 / VAT / 10, 50, "Amazon UK, sourcing map 10-pack x 5"),
        ("Stainless rod 5 mm", 5.99 / VAT / 4, 8, "Amazon UK, AOOSU 4-pack x 2"),
        ("cut to 680 mm", 22.27 / 3, 3, "extrusion shop, AEP-TV-2020-B-CTS cut to 680"),
        ("Glass mirror 50 mm round", 3.99 / VAT / 25, 75, "eBay, 25 for 3.99 (assumed inc VAT) x 3 packs"),
        ("M5 slide-in T-nut", 46.12 / 100, 100, "extrusion shop, SIN-20-M5"),
        ("M5 x 25 button head", 9.35 / 60, 60, "extrusion shop, BHB-M5-25"),
        ("M5 x 35 screw", 6.06 / 10, 10, "extrusion shop, BHB-M5-35"),
        ("M5 x 12 button head", 1.49 / 10, 10, "extrusion shop, BHB-M5-12"),
        ("M5 panel/slot washer", 10.80 / 50, 50, "extrusion shop, PSW-M5"),
    ]
    out, total = [], 0.0
    for pr, item, qty, note in rows:
        hit = next((x for x in prices if x[0] in item), None)
        if hit:
            _, unit, bought, sup = hit
            cost = round(unit * bought, 2)
            total += cost
            if bought < qty:
                note += f"; basket covers {bought} of {qty}, order {qty - bought} more"
            out.append((pr, item, qty, f"{unit:.3f}", bought, f"{cost:.2f}", sup, note))
        else:
            out.append((pr, item, qty, "", "", "", "", note))
    out.append(("shipping", "Technobots UK shipping, zone 1 (ex VAT, from the cart)", "", "", "", "5.95", "Technobots", "other shops' delivery not included"))
    total += 5.95
    out.append(("total", "Priced lines above, ex VAT, with Technobots shipping", "", "", "", f"{total:.2f}", "", "lines with no price are not in this total"))
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty_needed", "unit_ex_vat_gbp", "qty_bought", "cost_ex_vat_gbp", "supplier", "note"])
        w.writerows(out)
    print("Wrote", BOMF, f"(priced lines total {total:.2f} GBP ex VAT)")


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
    print(f"{ROWS} rows of {N} units, rows {ROW_PITCH:.0f} mm apart; each row: {N} units at {PITCH:.0f} mm pitch, spindle line {Y_R:.0f} mm from the wall, rail {RAIL_L:.0f} mm; ring swept diameter {2 * R_OUT:.0f} mm, {PITCH - 2 * R_OUT:.0f} mm between rings, "
          f"{Y_R - R_OUT:.0f} mm to the wall")
    print(f"Heights above the rail bottom: pulley {Z_P0:.0f}..{Z_P0 + P_LEN:.0f}, belts at {Z_BAND_LO:.0f} and {Z_BAND_HI:.0f}, ring centre {ZC:.1f}, ring top {ZC + R_OUT:.1f}")
    print(f"One unit: turning mass {unit_mass_g(('spin', 'tilt')):.0f} g (mirror group {unit_mass_g(('tilt',)):.0f} g), spin inertia {i_lo:.2e} to {i_hi:.2e} kg m2; "
          f"row incl. rotor {row_lo:.2e} to {row_hi:.2e} kg m2; torque for 100 rad/s2 {row_hi * 100:.3f} N m, for 300 rad/s2 {row_hi * 300:.3f} N m (before friction)")
    print(f"Mass: frame and motors about {frame_mass_g() / 1000:.2f} kg, {N * ROWS} units about {N * ROWS * unit_mass_g(('fixed', 'spin', 'tilt')) / 1000:.2f} kg; wall piece about {(ROWS * ROW_PITCH + 150) / 1000:.2f} m tall, {(RAIL_X1 - X_MOTOR + 60) / 1000:.2f} m wide")
    if a.check:
        multi = [(nm, len(s.Solids())) for nm, s, *_ in UNIT + ROW + ELEC if nm.startswith("print_") and len(s.Solids()) != 1]
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
        total_az = 0
        for seed in range(2):
            rnd = random.Random(100 + seed)
            P = all_parts([(rnd.uniform(0, 360), rnd.uniform(0, 360)) for _ in range(N * ROWS)])
            bad = [b for b in sm.clashes(P, only_with=moving(P)) if ok(b)]
            total_az += len(bad)
            if bad:
                print(f"random ring angles, seed {seed}: {len(bad)} clashes", bad[:8])
        print("total clashes over 2 poses with random ring angles too:", total_az)
        P = [(f"{n}", s, c, g, m) for n, s, c, g, m in all_parts([(0, 0)] * (N * ROWS))]
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
    top = (ROWS - 1) * ROW_PITCH + 190
    bx = (-130, RAIL_X1 + 40, 0, 160, -30, top)
    sm.render(P, IMG / "overview.png", [(14, 62, "3 rows of eight 50 mm mirrors, one NEMA 17 per row")], box_=(-130, RAIL_X1 + 40, 0, 140, -60, top), zoom=1.55)
    sm.render(P, IMG / "front.png", [(0, 90, "View from the room (X runs right to left)")], box_=bx, zoom=1.7)
    sm.render(P, IMG / "motor-end.png", [(18, 40, "Motor end of the bottom row: bracket, NEMA 17, first units")], box_=(-120, 200, 0, 100, -30, 190), zoom=1.2, only=("r1", "electronics"))
    sm.render(P, IMG / "unit-section.png", [(4, 90, "Section through the bottom row (y > 45 cut away)")], box_=(-120, 200, 0, 100, -30, 190), zoom=1.2, cut_y=Y_R, only=("r1",))
    only = ("r1_rail", "electronics", "placeholder", "r1_motor_", "r1_print_motor", "r1_print_wall")
    sm.render(P, IMG / "electronics-box.png", [(-28, 35, "Electronics box under the bottom rail (from below)")], box_=(-120, 110, 0, 100, -60, 45), zoom=1.15, only=only)
    sm.render(P, IMG / "electronics-box-open.png", [(-38, 28, "Lid removed: perfboard on the lid posts")], box_=(-120, 110, 0, 100, -60, 45), zoom=1.15,
              only=only, hide=("electronics_lid",))
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
