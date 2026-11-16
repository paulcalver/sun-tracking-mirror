#!/usr/bin/env python3
"""CAD assembly: finger pointer, a 120 mm flat pointing hand that shows where the Sun is (CadQuery). Draft, nothing built or tested.

World frame (mm): origin on the table at the centre of the 170 mm plinth, Z up. The tube and rod axis is the Z axis.
At az = 0 the hand points along +X, so the pivot axle runs along Y. el = 0 is horizontal, + is up (range +/-90).
Hierarchy (maps to Fusion components, no joints):
  base_fixed          170 mm square black plinth (laser cut), bearing housing, two steppers standing side by side, rod bottom
                      bearing, controller tray, compass, Hall sensors
  azimuth_rotating    turns about Z: 12 x 2 aluminium tube, 60T pulley, collar, head (printed shell, 2 x 686 bearings)
  rod_rotating        6 mm steel rod inside the tube, 60T pulley, mitre gear A. Turns az + el about Z.
  axle_rotating       turns about the pivot axle (Y): 6 mm axle, mitre gear B, hub ring, the hand plate

Drive: each stepper has a 20T GT2 pulley and a stock 200 mm loop to a 60T printed pulley (3:1).
  azimuth:   belt to the tube pulley.
  elevation: belt to the rod pulley; the rod turns the axle through a 1:1 mitre pair (rod gear A, axle gear B).
  hand elevation = rod angle - tube angle (firmware); no slip ring, both axes turn without limit.
One 3 mm black acrylic hand plate sits in front of the exposed gear pair, so the palm hides the gears from the front.
The pivot is the area centroid of the hand, so the plate is balanced about the axle; the finger axis is offset from it,
which does not matter for a distant target such as the Sun.

Usage (from the repo root):
  python3 cad/src/finger_pointer.py [--az DEG] [--el DEG] [--up y|z] [--check]
Needs cad/src/assets/finger-outline.json (python3 cad/src/trace_finger.py). Writes cad/out/earlier-concepts/finger-pointer/ (assembly STEP,
parts/<laser|print|purchase>/ with DXF and engraving PNGs), bom/bom-finger-pointer.csv and previews in
cad/media/previews/finger-pointer/.
"""
import argparse
import csv
import json
import math
import shutil
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
OUTD = CAD / "out" / "earlier-concepts" / "finger-pointer"
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / "finger-pointer"
BOMF = CAD.parent / "bom" / "bom-finger-pointer.csv"
ART = HERE / "assets"

# ------------------------------------------------------------------ parameters (mm)
BASE_HALF, WALL_T, WALL_INSET = 85.0, 3.0, 3.0              # 170 mm square plinth, 3 mm walls 3 mm in from the edge
FLOOR_T, FRAME_T, TOP_Z = 6.0, 6.0, 80.3                    # laser 6 mm floor and top frame; plinth top
FRAME_Z0 = TOP_Z - FRAME_T
WW = BASE_HALF - WALL_INSET                                 # wall outer face
CAV = WW - WALL_T                                           # cavity half width (79)
FLOOR_HALF = CAV - 0.5
NOTCH = 12.0                                                # cable notch in the back wall
SHAFT_EXPOSED = 177.0                                       # shaft above the plinth (was 118, raised 50 percent)
ZP = TOP_Z + SHAFT_EXPOSED                                  # pivot height, 257.3

GT_P, T_BIG, T_SMALL, BELT_LEN = 2.0, 60, 20, 200.0
MOT_BODY, MOT_X = 34.0, 50.0                                # NEMA 17 (34 mm) standing; motor centres at +/-50 in X
EL_Z0, EL_Z1 = 42.0, 49.0                                   # elevation belt teeth zone
AZ_Z0, AZ_Z1 = 52.0, 59.0                                   # azimuth belt teeth zone

TUBE_OD, TUBE_ID, TUBE_Z0 = 12.0, 8.0, 50.0
ROD_D, ROD_Z0 = 6.0, 22.5
HOUS_R, HOUS_Z0, FL_R = 12.0, 62.0, 18.0                    # bearing housing (6701 x 2: 12 x 18 x 4)
B6701_T, B_UP_Z0, B_LO_Z0 = 4.0, TOP_Z - 4.0, 62.0

# mitre pair (RS PRO POM, 20T, module 1, 6 mm bore): reference cones, apex at the pivot
BEVEL_T = 20
R_PITCH = BEVEL_T * 1.0 / 2
D_TOE, D_HEEL, D_HUB = 6.5, 10.7, 14.7                      # axial distance from the apex (cone half angle 45 deg)
Z_CAP_TOP = ZP - 15.2                                       # top of the printed cap on the tube; gear A sits 0.5 mm above it
CAP_R, CAP_ROOF, CAP_DEPTH = 9.0, 3.0, 10.0                 # cap over the tube end, rod bushing in its roof
BRK_Y = (-21.2, -15.2)                                      # bracket arm that carries the axle bearing, just beyond gear B's hub end (gears sit inside the L)
B686 = (6.0, 13.0, 5.0)                                     # one 6 x 13 x 5 axle bearing in the bracket plate
B686_Y = (-20.2, -15.2)
PLATE_T, HUB_T = 3.0, 3.0
HUB_FRONT_Y = (-24.7, -21.7)
FRONT_Y = (-27.7, -24.7)                                    # the single hand plate
AXLE_Y = (-28.2, -D_TOE)                                    # ends flush with gear B's toe

OUTLINE = json.loads((ART / "finger-outline.json").read_text())
HAND_PTS = [tuple(p) for p in OUTLINE["outline"]]

PRINT_C, LASER_C, STEEL, ALU, BLUE, GREEN, RED, POM, BELT = ("#e8a400", "#222222", "#c4c8cc", "#a9b0b8", "#4a6fa5", "#2e8b57",
                                                              "#c0392b", "#e8e6df", "#333333")


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


def ringz(ro, ri, z0, z1, x=0.0, y=0.0):
    return cylz(ro, z0, z1, x, y).cut(cylz(ri, z0 - 1, z1 + 1, x, y))


def ringy(ro, ri, y0, y1, x=0.0, z=0.0):
    return cyly(ro, y0, y1, x, z).cut(cyly(ri, y0 - 1, y1 + 1, x, z))


def toothed_disc(n, r_tip, r_root, z0, z1, cx=0.0, cy=0.0):
    pts = []
    for i in range(n):
        a0 = 2 * math.pi * i / n
        for frac, r in ((0.0, r_root), (0.2, r_tip), (0.55, r_tip), (0.75, r_root)):
            a = a0 + frac * 2 * math.pi / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0)


def pitch_r(n):
    return n * GT_P / (2 * math.pi)


def outer_r(n):
    return (n * GT_P / math.pi - 0.76) / 2


def belt_len(c, r1, r2):
    al = math.asin((r1 - r2) / c)
    return 2 * math.sqrt(c * c - (r1 - r2) ** 2) + r1 * (math.pi + 2 * al) + r2 * (math.pi - 2 * al)


def centre_for(length, r1, r2):
    lo, hi = r1 + r2 + 1, 200.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if belt_len(mid, r1, r2) < length else (lo, mid)
    return (lo + hi) / 2


def tangents(c1, r1, c2, r2):
    d = math.dist(c1, c2)
    ux, uy = (c2[0] - c1[0]) / d, (c2[1] - c1[1]) / d
    phi = math.acos((r1 - r2) / d)
    out = []
    for s in (1, -1):
        c, sn = math.cos(s * phi), math.sin(s * phi)
        n = (ux * c - uy * sn, ux * sn + uy * c)
        out.append(((c1[0] + r1 * n[0], c1[1] + r1 * n[1]), (c2[0] + r2 * n[0], c2[1] + r2 * n[1])))
    return out


def belt_solid(c1, r1, c2, r2, z0, z1, thick=0.8):
    """Closed belt loop, plain band z0..z1 whose inside runs on the pulley tip radii r1, r2 (teeth sit in the belt)."""
    def hull(a, b):
        t = tangents(c1, a, c2, b)
        w = cq.Workplane("XY").workplane(offset=z0)
        s = w.polyline([t[0][0], t[0][1], t[1][1], t[1][0]]).close().extrude(z1 - z0)
        s = s.union(cq.Workplane("XY").workplane(offset=z0).center(*c1).circle(a).extrude(z1 - z0))
        return s.union(cq.Workplane("XY").workplane(offset=z0).center(*c2).circle(b).extrude(z1 - z0))
    return hull(r1 + thick, r2 + thick).cut(hull(r1, r2))


def nema17(body=MOT_BODY, shaft=24.0, shaft_r=2.5):
    """Local frame: flange face at z=0, body behind (z from -body to 0), shaft +z."""
    m = box(-21, 21, -21, 21, -body, 0).edges("|Z").chamfer(3)
    return m.union(cylz(11, 0, 2)).union(cylz(shaft_r, 0, shaft))


def pulley20(z_teeth0, z_teeth1, z_hub0):
    r_o = outer_r(T_SMALL)
    body = toothed_disc(T_SMALL, r_o, r_o - 0.7, z_teeth0, z_teeth1)
    if z_hub0 < z_teeth0:
        body = body.union(cylz(8.0, z_hub0, z_teeth0))
    body = body.union(cylz(8.0, z_teeth1, z_teeth1 + 1.0))
    return body.cut(cylz(2.5, min(z_hub0, z_teeth0) - 1, z_teeth1 + 2))


# ------------------------------------------------------------------ geometry derived from the belts
R_BIG, R_SMALL = pitch_r(T_BIG), pitch_r(T_SMALL)
C_BELT = centre_for(BELT_LEN, R_BIG, R_SMALL)
MOT_Y = -math.sqrt(C_BELT ** 2 - MOT_X ** 2)
EL_XY, AZ_XY = (-MOT_X, MOT_Y), (MOT_X, MOT_Y)
MOT_Z0 = FLOOR_T
MOT_TOP = MOT_Z0 + MOT_BODY

# ------------------------------------------------------------------ parts: (name, solid, colour, group)
PARTS_L = []


def add(name, wp, colour, grp="fixed"):
    PARTS_L.append((name, _shape(wp), colour, grp))


def build():
    PARTS_L.clear()
    # ---- laser cut plinth, black acrylic
    add("base_floor_plate_6mm", box(-FLOOR_HALF, FLOOR_HALF, -FLOOR_HALF, FLOOR_HALF, 0, FLOOR_T), LASER_C)
    wf = box(-WW, WW, -WW, -CAV, 0, FRAME_Z0)
    wb = box(-WW, WW, CAV, WW, 0, FRAME_Z0).cut(box(-NOTCH / 2, NOTCH / 2, CAV - 1, WW + 1, -1, 6))
    add("base_wall_front_3mm", wf, LASER_C)
    add("base_wall_back_3mm", wb, LASER_C)
    add("base_wall_left_3mm", box(-WW, -CAV, -CAV, CAV, 0, FRAME_Z0), LASER_C)
    add("base_wall_right_3mm", box(CAV, WW, -CAV, CAV, 0, FRAME_Z0), LASER_C)
    add("base_top_frame_6mm", box(-BASE_HALF, BASE_HALF, -BASE_HALF, BASE_HALF, FRAME_Z0, TOP_Z).cut(cylz(HOUS_R + 0.2, FRAME_Z0 - 1, TOP_Z + 1)), LASER_C)

    # ---- bearing housing (printed): 2 x 6701, hall pin for the azimuth sensor
    hou = cylz(HOUS_R, HOUS_Z0, TOP_Z).union(cylz(FL_R, FRAME_Z0 - FRAME_T + 2.0 - 0.0, FRAME_Z0))
    hou = hou.union(cylz(2.5, 62.6, FRAME_Z0, 0, 15))
    hou = hou.cut(cylz(9.05, B_UP_Z0, TOP_Z + 1)).cut(cylz(7.5, B_LO_Z0 + B6701_T, B_UP_Z0 + 0.01)).cut(cylz(9.05, HOUS_Z0 - 1, B_LO_Z0 + B6701_T))
    add("bearing_housing", hou, PRINT_C)
    add("bearing_6701_upper", ringz(9.0, 6.0, B_UP_Z0, TOP_Z), STEEL)
    add("bearing_6701_lower", ringz(9.0, 6.0, B_LO_Z0, B_LO_Z0 + B6701_T), STEEL)

    # ---- steppers standing side by side, in printed cradles
    for tag, (mx, my) in (("el", EL_XY), ("az", AZ_XY)):
        mot = nema17().translate((mx, my, MOT_TOP))
        add(f"stepper_{tag}_NEMA17_34mm", mot, BLUE)
        cr = box(mx - 23.2, mx + 23.2, my - 23.2, my + 23.2, MOT_Z0, MOT_Z0 + 22).cut(box(mx - 21.2, mx + 21.2, my - 21.2, my + 21.2, MOT_Z0 - 1, MOT_Z0 + 23))
        cr = cr.union(box(mx - 27, mx + 27, my - 27, my + 27, MOT_Z0, MOT_Z0 + 3).cut(box(mx - 21.2, mx + 21.2, my - 21.2, my + 21.2, MOT_Z0 - 1, MOT_Z0 + 4)))
        add(f"motor_cradle_{tag}", cr, PRINT_C)
    add("motor_pulley_el_20T", pulley20(EL_Z0, EL_Z1, EL_Z0).translate((EL_XY[0], EL_XY[1], 0)), STEEL)
    add("motor_pulley_az_20T", pulley20(AZ_Z0, AZ_Z1, AZ_Z0 - 3.0).translate((AZ_XY[0], AZ_XY[1], 0)), STEEL)

    # ---- belts
    add("belt_el_GT2_6mm_200", belt_solid((0, 0), outer_r(T_BIG) + 0.02, EL_XY, outer_r(T_SMALL) + 0.02, EL_Z0 + 0.5, EL_Z1 - 0.5), BELT)
    add("belt_az_GT2_6mm_200", belt_solid((0, 0), outer_r(T_BIG) + 0.02, AZ_XY, outer_r(T_SMALL) + 0.02, AZ_Z0 + 0.5, AZ_Z1 - 0.5), BELT)

    # ---- rod bottom bearing bracket (printed) with a 626 (6 x 19 x 6)
    br = box(-12, 12, -12, 12, FLOOR_T, 28).cut(cylz(9.55, 22.0, 29))
    add("rod_bearing_bracket", br, PRINT_C)
    add("bearing_626_rod", ringz(9.5, 3.0, 22.0, 28.0), STEEL)

    # ---- sensors and electronics, fixed
    add("hall_post_el", cylz(2.5, FLOOR_T, 39.0, 0, 15), PRINT_C)
    add("hall_board_el", box(-4, 4, 12.5, 19, 39.0, 40.6), GREEN)
    add("hall_board_az", box(-4, 4, 12.5, 19, 61.0, 62.6), GREEN)
    leg = [box(x - 2, x + 2, y - 2, y + 2, FLOOR_T, 8.0) for x in (-36, 36) for y in (31, 61)]
    tray = box(-40, 40, 28, 64, 8.0, 11.0)
    for lg in leg:
        tray = tray.union(lg)
    add("controller_tray", tray, PRINT_C)
    add("board_pico", box(-38, 13, 31, 52, 11.0, 12.6), GREEN)
    add("board_tmc2209_el", box(18, 38, 31, 46, 11.0, 12.6), GREEN)
    add("board_tmc2209_az", box(18, 38, 49, 64, 11.0, 12.6), GREEN)
    add("board_buck", box(-38, -16, 54, 63, 11.0, 14.0), GREEN)
    add("board_ds3231", box(-12, 8, 54, 63, 11.0, 12.6), GREEN)
    add("compass_post", cylz(3.0, FLOOR_T, 20.0, 0, 70).union(box(-8, 8, 62, 78, 18.0, 20.0)), PRINT_C)
    add("board_compass_GY271", box(-7, 7, 63, 77, 20.0, 21.6), GREEN)

    # ---- azimuth: tube, collar, 60T pulley with magnet
    tube_top = Z_CAP_TOP - CAP_ROOF - 0.1
    add("tube_12x2_alu", ringz(TUBE_OD / 2, TUBE_ID / 2, TUBE_Z0, tube_top), ALU, "az")
    add("tube_collar", ringz(7.0, TUBE_OD / 2, TOP_Z, TOP_Z + 4.0), PRINT_C, "az")
    r_o = outer_r(T_BIG)
    tp = toothed_disc(T_BIG, r_o, r_o - 0.75, AZ_Z0, AZ_Z1).union(cylz(12.0, TUBE_Z0, AZ_Z1 + 2.0))
    tp = tp.cut(cylz(TUBE_OD / 2, TUBE_Z0 - 1, AZ_Z1 + 3)).cut(cylz(2.55, AZ_Z1 - 2.0, AZ_Z1 + 1, 0, 15))
    add("tube_pulley_60T", tp, PRINT_C, "az")
    add("magnet_az_5x2", cylz(2.5, AZ_Z1 - 2.0, AZ_Z1, 0, 15), RED, "az")

    # ---- elevation: rod, rod pulley with magnet, gear A
    add("rod_6mm_silver_steel", cylz(ROD_D / 2, ROD_Z0, ZP - D_TOE), STEEL, "rod")
    rp = toothed_disc(T_BIG, r_o, r_o - 0.75, EL_Z0, EL_Z1).union(cylz(8.0, EL_Z0 - 2.0, EL_Z1 + 0.5))
    rp = rp.cut(cylz(ROD_D / 2, EL_Z0 - 3, EL_Z1 + 3)).cut(cylz(2.55, EL_Z0, EL_Z0 + 2.0, 0, 15))
    add("rod_pulley_60T", rp, PRINT_C, "rod")
    add("magnet_el_5x2", cylz(2.5, EL_Z0, EL_Z0 + 2.0, 0, 15), RED, "rod")
    cone_a = cq.Solid.makeCone(D_TOE, D_HEEL, D_HEEL - D_TOE, cq.Vector(0, 0, ZP - D_TOE), cq.Vector(0, 0, -1))
    ga = cq.Workplane(obj=cone_a).union(cylz(6.0, ZP - D_HUB, ZP - D_HEEL)).cut(cylz(ROD_D / 2, ZP - D_HUB - 1, ZP - D_TOE + 1))
    add("mitre_gear_A_rod_20T", ga, POM, "rod")

    # ---- head (printed, one part): cap on the tube end with a rod bushing, and a bracket arm that carries the axle bearing.
    # Both gears stay exposed. The arm stands just in front of gear A so the mesh is open.
    cap = cylz(CAP_R, Z_CAP_TOP - CAP_ROOF - CAP_DEPTH, Z_CAP_TOP)
    foot = box(-5, 5, BRK_Y[0], -6, Z_CAP_TOP - CAP_ROOF, Z_CAP_TOP)
    plate = box(-8, 8, BRK_Y[0], BRK_Y[1], Z_CAP_TOP - CAP_ROOF, ZP).union(cyly(8.0, BRK_Y[0], BRK_Y[1], 0, ZP))
    brk = cap.union(foot).union(plate)
    brk = brk.cut(cylz(TUBE_OD / 2 + 0.1, Z_CAP_TOP - CAP_ROOF - CAP_DEPTH - 1, Z_CAP_TOP - CAP_ROOF))
    brk = brk.cut(cylz(3.15, Z_CAP_TOP - CAP_ROOF - 1, Z_CAP_TOP + 1))
    brk = brk.cut(cyly(B686[1] / 2 + 0.05, B686_Y[0], BRK_Y[1] + 0.1, 0, ZP)).cut(cyly(4.0, BRK_Y[0] - 1, B686_Y[0] + 0.1, 0, ZP))
    add("head_bracket", brk, PRINT_C, "az")
    add("bearing_686_axle", ringy(B686[1] / 2, B686[0] / 2, B686_Y[0], B686_Y[1], 0, ZP), STEEL, "az")

    # ---- axle, gear B, hub rings, hand plates
    add("axle_6mm_silver_steel", cyly(3.0, AXLE_Y[0], AXLE_Y[1], 0, ZP), STEEL, "axle")
    cone_b = cq.Solid.makeCone(D_TOE, D_HEEL, D_HEEL - D_TOE, cq.Vector(0, -D_TOE, ZP), cq.Vector(0, -1, 0))
    gb = cq.Workplane(obj=cone_b).union(cyly(6.0, -D_HUB, -D_HEEL, 0, ZP)).cut(cyly(3.0, -D_HUB - 1, 0, 0, ZP))
    add("mitre_gear_B_axle_20T", gb, POM, "axle")
    add("hand_hub_ring_front", ringy(8.0, 3.0, HUB_FRONT_Y[0], HUB_FRONT_Y[1], 0, ZP), PRINT_C, "axle")
    add("hand_plate_front_3mm", plate_solid(*FRONT_Y), LASER_C, "axle")


def plate_solid(y0, y1):
    wp = cq.Workplane("XZ").workplane(offset=-y1).polyline(HAND_PTS).close().extrude(y1 - y0).translate((0, 0, ZP))
    return wp.cut(cyly(3.1, y0 - 1, y1 + 1, 0, ZP))


def posed(az=0.0, el=0.0):
    out = []
    for nm, s, col, grp in PARTS_L:
        if grp == "rod":
            s = s.rotate((0, 0, 0), (0, 0, 1), az + el)
        elif grp == "axle":
            s = s.rotate((0, 0, ZP), (0, 1, ZP), -el).rotate((0, 0, 0), (0, 0, 1), az)
        elif grp == "az":
            s = s.rotate((0, 0, 0), (0, 0, 1), az)
        out.append((nm, s, col, grp))
    return out


def cqc(h):
    return cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255)


def assemble(az, el, yup):
    root = cq.Assembly(name="finger_pointer")
    subs = {"fixed": "base_fixed", "az": "azimuth_rotating", "rod": "rod_rotating", "axle": "axle_rotating"}
    sa = {g: cq.Assembly(name=n) for g, n in subs.items()}
    for nm, s, col, grp in posed(az, el):
        if yup:
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        sa[grp].add(s, name=nm, color=cqc(col))
    for g, a in sa.items():
        root.add(a, name=subs[g])
    return root


def clashes(parts, tol=2.0, only_with=None):
    found = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _, _ in parts]
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


LASER = {"base_floor_plate_6mm", "base_wall_front_3mm", "base_wall_back_3mm", "base_wall_left_3mm", "base_wall_right_3mm",
         "base_top_frame_6mm", "hand_plate_front_3mm"}
PRINT = ("bearing_housing", "motor_cradle_", "rod_bearing_bracket", "hall_post_el", "controller_tray", "compass_post",
         "tube_collar", "tube_pulley_60T", "rod_pulley_60T", "head_bracket", "hand_hub_ring_")


def process_of(nm):
    if nm in LASER:
        return "laser"
    return "print" if nm.startswith(PRINT) else "purchase"


def hand_flat():
    w = cq.Workplane("XY").polyline(HAND_PTS).close().extrude(PLATE_T)
    return w.cut(cq.Workplane("XY").circle(3.1).extrude(PLATE_T))


def export_parts(yup):
    for sub in ("laser", "print", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")) + list(d.glob("*.dxf")) + list(d.glob("*.png")):
            old.unlink()
    n = 0
    for nm, s, _, _ in PARTS_L:
        sh = s.rotate((0, 0, 0), (1, 0, 0), -90) if yup else s
        cq.exporters.export(cq.Workplane(obj=sh), str(PARTS / process_of(nm) / f"{nm}.step"))
        n += 1
    print("Wrote", n, "part STEP files to", PARTS)
    d = PARTS / "laser"
    flat = {"base_floor_plate_6mm": box(-FLOOR_HALF, FLOOR_HALF, -FLOOR_HALF, FLOOR_HALF, 0, FLOOR_T),
            "base_top_frame_6mm": box(-BASE_HALF, BASE_HALF, -BASE_HALF, BASE_HALF, 0, FRAME_T).cut(cylz(HOUS_R + 0.2, -1, FRAME_T + 1)),
            "wall_panel_long_front_3mm": box(0, 2 * WW, 0, FRAME_Z0, 0, WALL_T),
            "wall_panel_long_back_notch_3mm": box(0, 2 * WW, 0, FRAME_Z0, 0, WALL_T).cut(box(WW - NOTCH / 2, WW + NOTCH / 2, -1, 6.0, -1, WALL_T + 1)),
            "wall_panel_short_3mm_x2": box(0, 2 * CAV, 0, FRAME_Z0, 0, WALL_T),
            "hand_plate_front": hand_flat()}
    for nm, w in flat.items():
        cq.exporters.exportDXF(cq.Workplane(obj=_shape(w)).faces("<Z").val(), str(d / f"{nm}.dxf"))
    shutil.copy(ART / "finger-engrave-front.png", d / "finger-engrave-front.png")
    print("Wrote", len(flat), "cut DXF outlines and the engraving PNG to", d)


def write_bom():
    rows = [
        ("laser", "Black acrylic 6 mm: floor plate 151 mm square, top frame 170 mm with a 24.4 mm hole", 2, "own cutter, 6 mm max"),
        ("laser", "Black acrylic 3 mm: 2 long wall panels (164 x 74.3), 2 short (158 x 74.3), one with a 12 mm cable notch", 4, "own cutter"),
        ("laser", "Black acrylic 3 mm: hand plate (cut DXF, engrave the front PNG: light areas frosted)", 1, "own cutter"),
        ("print", "PETG-CF: housing, cradles x2, rod bracket, tray, compass post, Hall post, collar, 2 pulleys, head bracket, hub ring", 13, "Bambu P1S, hardened nozzle"),
        ("buy", "NEMA 17 stepper 42 x 34 mm", 2, "Pi Hut 42 x 34, in earlier BOM"),
        ("buy", "GT2 pulley 20T, 6 mm belt, 5 mm bore", 2, "123-3D"),
        ("buy", "GT2 closed belt 6 mm, 200 mm (100 teeth)", 2, "123-3D 200 mm in stock"),
        ("buy", "Aluminium tube 12 x 2 mm, about 189 mm cut", 1, "Aluminium Warehouse"),
        ("buy", "Silver steel rod 6 mm, one 333 mm bar cut into the rod (about 228 mm) and the axle (about 21.7 mm)", 1, "Tesco marketplace, Bolts.co.uk"),
        ("buy", "Bearing 6701 (12 x 18 x 4)", 2, "Simply Bearings, Henderson"),
        ("buy", "Bearing 686ZZ (6 x 13 x 5)", 1, "standard"),
        ("buy", "Bearing 626ZZ (6 x 19 x 6)", 1, "standard"),
        ("buy", "RS PRO POM mitre gear 20T, module 1, 6 mm bore (521-6058)", 2, "RS, about 5.83 each"),
        ("buy", "Torsion spring on the axle to take up bevel backlash (not modelled)", 1, "to be designed"),
        ("buy", "Pico, DS3231, 2 x TMC2209, buck converter, GY-271 compass, 2 x Hall board, 2 x 5 x 2 magnets, M3 and M2 fasteners, heat-set inserts", 1, "as the mirror BOM"),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


def render(parts, path, views, hide=(), box=None, zoom=1.2, only=()):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris, cols = [], []
    light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
    for nm, s, col, _ in parts:
        if any(h in nm for h in hide) or (only and not any(o in nm for o in only)):
            continue
        v, t = s.tessellate(0.5, 0.4)
        v = np.array([(p.x, p.y, p.z) for p in v])
        base = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        for a, b, c in t:
            tri = v[[a, b, c]]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            sh = 0.55 + 0.45 * abs(float(n @ light) / nn) if nn > 1e-9 else 0.8
            tris.append(tri); cols.append(np.clip(base * sh, 0, 1))
    x0, x1, y0, y1, z0, z1 = box or (-130, 130, -130, 130, 0, ZP + 100)
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
    ap.add_argument("--az", type=float, default=0.0, help="azimuth, deg (0 points along +X)")
    ap.add_argument("--el", type=float, default=0.0, help="hand elevation, deg (+ up, range +/-90)")
    ap.add_argument("--up", choices=("y", "z"), default="y", help="up axis of the STEP files (y for Fusion)")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    a = ap.parse_args()
    build()

    top = ZP + OUTLINE["tip_mm"]
    print(f"Plinth {2 * BASE_HALF:.0f} mm square, top at {TOP_Z} mm, pivot {ZP:.1f} mm above the table, overall about {ZP + max(OUTLINE['tip_mm'], -OUTLINE['cuff_mm']):.0f} mm")
    print(f"Belt: 60T/20T, 200 mm loop gives {C_BELT:.1f} mm centres; steppers at X +/-{MOT_X:.0f}, Y {MOT_Y:.1f} (side by side), motor edge {MOT_X + 21:.0f} of {CAV} cavity half width")
    print(f"3:1 each axis: {1.8 / 16 / 3:.4f} deg per 1/16 microstep at the tube and at the rod; mitre pair 1:1 so the hand moves {1.8 / 16 / 3:.4f} deg per microstep")
    print(f"Hand: {OUTLINE['hand_len_mm']:.0f} mm, area {OUTLINE['area_mm2']:.0f} mm2, pivot at the centroid, finger axis {OUTLINE['finger_axis_offset_mm']:+.1f} mm from the pivot; lowest tip at el -90 is {ZP - OUTLINE['tip_mm']:.0f} mm up")
    print(f"Head: exposed gears, one printed bracket (cap on the tube, arm with the 686); gear envelope {2 * D_HEEL:.1f} mm across, axle length {AXLE_Y[1] - AXLE_Y[0]:.1f} mm; hand plate at Y {FRONT_Y[0]} to {FRONT_Y[1]}")

    if a.check:
        movers = {n for n, _, _, g in PARTS_L if g in ("axle", "rod")}
        total = 0
        for el in (0, 30, -30, 60, -60, 90, -90):
            for az in (0, 60, 135, 250):
                bad = clashes(posed(az, el), only_with=movers)
                total += len(bad)
                if bad:
                    print(f"az {az} el {el:+d}: {len(bad)} clashes", bad[:6])
        print("total clashes in the moving checks:", total)
        static = clashes(posed(0, 0))
        print("static clashes at az 0, el 0:", len(static), static[:12])
        return

    tag = "" if (a.az == 0 and a.el == 0) else f"-az{a.az:.0f}-el{a.el:.0f}"
    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_parts(a.up == "y")
    write_bom()
    assemble(a.az, a.el, a.up == "y").save(str(OUTD / f"finger-pointer-assembly{tag}.step"))
    print("Wrote", OUTD / f"finger-pointer-assembly{tag}.step")
    P = posed(a.az, a.el)
    render(P, IMG / f"finger-pointer{tag}.png", [(14, -58, "Finger pointer, 3/4 view"), (0, -90, "Front")])
    render(posed(40, 35), IMG / "finger-pointer-posed.png", [(14, -58, "Az 40, el +35"), (8, -130, "From behind")])
    hide = ("base_top_frame", "base_wall", "hand_", "head_", "tube_", "bearing_housing", "mitre", "axle", "bearing_686", "rod_6mm", "collar")
    render(P, IMG / "finger-pointer-inside.png", [(90, -90, "Plan, plinth top and walls hidden")], hide=hide, box=(-90, 90, -90, 90, 0, 100), zoom=1.7)
    render(posed(0, 25), IMG / "finger-pointer-head.png", [(10, -60, "Head, plate on"), (0, -90, "Front")],
           box=(-55, 55, -45, 45, ZP - 60, ZP + 45), zoom=1.7, hide=("base_", "stepper", "belt", "motor_"))
    plates = ("hand_plate",)
    render(posed(0, 25), IMG / "finger-pointer-head-open.png", [(10, -60, "Head with the plate hidden"), (10, -140, "From the back, plate hidden")],
           box=(-45, 45, -35, 35, ZP - 50, ZP + 35), zoom=1.7, hide=("base_", "stepper", "belt", "motor_") + plates)
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
