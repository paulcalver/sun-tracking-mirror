#!/usr/bin/env python3
"""CAD assembly: row of 7 spinning mirror gimbals (or --units 1: the single test rig, same top support) on a laser-cut plywood base with a goal-post top bar (CadQuery). Draft, nothing built or tested.

Reuses the single unit from spinning_mirror.py (60 mm mirror, free hinge, 2804-class brushless motor) and adds, per unit, a 3 mm top pin on the
ring that runs in a 683ZZ bearing in a small printed block clamped under a 10 mm carbon tube. The tube is carried by two 8 mm steel rod posts
(captive M8 nuts in the base) and passes through two 3 mm plywood blades, one in each of the gaps between units 2|3 and 5|6, so the row is
symmetrical (2 | 3 | 2) and the structure above and beside the mirrors is as thin as practical. Each motor is independent, own random speed.

World frame (mm): origin on the table at the centre of the base, Z up, X along the row. Units sit on Y = 0.
Base: 3 laminated 6 mm plywood layers (bottom, middle with ballast and cable windows, top) on four rubber feet, 720 x 140 mm.
Unit pitch 95 mm, uniform (17 mm clear between rings), blades 3 mm thick in the gaps 2|3 and 5|6.
Hierarchy: frame (base layers, ballast, rod posts, end clamps, blades, tube), and per unit: fixed (boss, motor, top block, top bearing), spin (hub, ring, pin,
bearings), tilt (carrier, axle, mirrors, weight).

Usage (from the repo root):
  python3 cad/src/spinning_mirror_row.py [--units N] [--up y|z] [--check] [--seed N]    (--units 1 writes out/spinning-mirror-test/)
Writes cad/out/spinning-mirror-row/ (assembly STEP, parts/<laser|print|purchase>/ with DXF for the laser parts), bom/bom-spinning-mirror-row.csv
and previews in cad/media/previews/spinning-mirror-row/.
"""
import argparse
import csv
import math
import random
import sys
from pathlib import Path

import cadquery as cq
import spinning_mirror as sm

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
# number of units: --units N on the command line (7 = the long row, 3 = the trio, 1 = the single test rig); read here because the layout is computed at import
N = int(sys.argv[sys.argv.index("--units") + 1]) if "--units" in sys.argv else 7
TAG = {1: "spinning-mirror-test", 3: "spinning-mirror-trio"}.get(N, "spinning-mirror-row")
OUTD = CAD / "out" / TAG
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / TAG
BOMF = CAD.parent / "bom" / f"bom-{TAG}.csv"

box, cylz, cylx, cyly = sm.box, sm.cylz, sm.cylx, sm.cyly
ZC, R_OUT = sm.ZC, sm.R_OUT

# ------------------------------------------------------------------ parameters (mm)
PITCH = 2 * R_OUT + 17.0                                      # 17 mm clear between rings (115 mm)
XS = [(i - (N - 1) / 2) * PITCH for i in range(N)]            # unit centres along X, row centred on 0 (symmetrical)
PLY = 6.0                                                    # plywood thickness (laser cutter max)
BOX_W = 150.0                                                # plywood box outer width (the electronics bay under the deck)
FEET_T = 2.0
Z_BOT, Z_MID, Z_TOP = FEET_T, FEET_T + PLY, FEET_T + 2 * PLY   # layer bottoms: 2, 8, 14
Z_BASE = FEET_T + 3 * PLY                                    # top of the base, 20
BOSS_R = 16.0                                                # printed motor boss, Z_BASE to sm.BOSS_Z1
DECK_Z1 = sm.HUB_Z1                                          # plywood deck, top level with the top of the hub adapter
DECK_Z0 = DECK_Z1 - PLY                                      # 1 mm above the rotor bell
TAB_W = 24.0                                                 # finger tabs on the box walls
CTRL_XY = (PITCH / 2, -50.0)                                 # controller board envelope (placeholder) in the box

X_POST = XS[-1] + R_OUT + 25.0                               # steel rod post, 25 mm outside the end rings (349)
ROD_D, NUT_AF = 8.0, 13.0                                    # 8 mm steel rod, M8 thin nut (13 mm across flats) captive in the middle layer
TUBE_D, TUBE_ID = 10.0, 8.0                                  # 10 x 8 carbon tube
BAR_L = 2 * (X_POST + 1.0)                                   # tube ends 1 mm past each rod axis
BOX_L = max(260.0, math.ceil(2 * (X_POST + 17.0) / 10) * 10) - 8.0     # plywood box outer length (412 for the trio)
WALL_X, WALL_Y = BOX_L / 2, BOX_W / 2                        # outer faces of the box walls
HOOD_GAP, ACR_T, HTAB = 8.0, 5.0, 20.0                       # air gap round the box, acrylic thickness, hood tab width
HOOD_IN_X, HOOD_IN_Y = WALL_X + HOOD_GAP, WALL_Y + HOOD_GAP  # hood inner faces
HOOD_OUT_X, HOOD_OUT_Y = HOOD_IN_X + ACR_T, HOOD_IN_Y + ACR_T
RIM, LEDGE = 6.0, 36.0                                       # base rim outside the hood, control ledge in front
BASE_L = 2 * (HOOD_OUT_X + RIM)                              # 450 for the trio
BASE_Y1 = HOOD_OUT_Y + RIM
BASE_Y0 = -(HOOD_OUT_Y + RIM + LEDGE)
BASE_W = BASE_Y1 - BASE_Y0
BALLAST_L = min(BASE_L - 40.0, 1000.0)                       # steel flat bar length
POD_L, POD_W, POD_H = 70.0, 30.0, 24.0                       # printed control pod on the ledge
POD_X, POD_Y = 0.0, BASE_Y0 + LEDGE / 2
POD_HOLES = [(POD_X + sx * 31.0, POD_Y + sy * 11.5) for sx in (-1, 1) for sy in (-1, 1)]    # M3 from below into inserts in the pod
FRONT_CABLE_X = -20.0                                        # pod wires: notch in the hood bottom edge and hole in the front panel
BLADE_T, BLADE_W = 3.0, 26.0                                 # 3 mm plywood blades in the gaps 2|3 and 5|6
BLADE_X = [(XS[1] + XS[2]) / 2, (XS[4] + XS[5]) / 2] if N == 7 else []   # blades only for the full row
TOP_PIN_L = 16.0
Z_PIN0, Z_PIN1 = ZC + R_OUT - 3, ZC + R_OUT + 13             # pin 136 to 152
Z_BLK0 = ZC + R_OUT + 8                                      # top bearing block bottom, 147
Z_TC = Z_BLK0 + 13.0                                         # tube centre line; 2.7 mm of plastic between the pin hole and the tube saddle
Z_END0 = Z_TC - 28.0                                         # end clamp block bottom (130)
Z_POST1 = Z_TC - 10.0                                        # rod post top, 4.5 mm of plastic below the tube saddle
BLADE_TOP = Z_TC + 14.0
CLAMP_Y, SCREW_Y = 11.5, 8.0                                 # clamp block half width, M3 screw offset from the tube axis
CLAMP_GAP, CAP_T = 0.3, 8.5                                  # block top 0.3 below, cap bottom 0.3 above the tube centre line (closes onto the tube); cap height above the centre line
HOOD_TOP_IN = math.ceil(Z_TC + CAP_T + 14.5)                 # inner top of the hood, 14.5 mm over the tube clamps
REED_X, MAG_Z = BOX_L / 4, 30.0                              # reed switch on the back wall, magnet on the hood
BALLAST_W = 38.0                                             # steel flat bar 38 x 6, two of them, under the box in the middle layer
WOOD, ALU_C = "#d2b48c", "#b8bec6"


# ------------------------------------------------------------------ laser parts (flat, thickness PLY)
def flat_rect(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, PLY, centered=False).translate((x0, y0, 0))


def cutter(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, PLY + 2, centered=False).translate((x0, y0, -1))


def layer_bottom(holes=False):
    w = flat_rect(-BASE_L / 2, BASE_L / 2, BASE_Y0, BASE_Y1)
    if holes:                                                                                # M2 motor screws, heads counterbored from below
        for x in XS:
            for (hx, hy) in sm.MOTOR_BOTTOM_HOLES:
                w = w.cut(cylz(1.2, -1, PLY + 1, x + hx, hy))
    for (hx, hy) in POD_HOLES:                                                               # M3 screws for the control pod
        w = w.cut(cylz(1.7, -1, PLY + 1, hx, hy))
    return w


def layer_middle():
    w = layer_bottom()
    for y0, y1 in ((20.0, 60.0), (-60.0, -20.0)):                                            # windows for the steel flat bar
        w = w.cut(cutter(-BALLAST_L / 2 - 2, BALLAST_L / 2 + 2, y0, y1))
    for sx in (-1, 1):                                                                       # hex pockets for the M8 thin nuts
        w = w.cut(cq.Workplane("XY").workplane(offset=-1).center(sx * X_POST, 0).polygon(6, NUT_AF / math.cos(math.radians(30)) + 0.3).extrude(PLY + 2))
    return w


def tab_centres(length, pitch=80.0):
    n = max(2, round(length / pitch))
    return [-length / 2 + (i + 0.5) * length / n for i in range(n)]


def wall_slots(w, front=True, back=True, ends=True):
    """Slots for the wall tabs in a layer (top layer for the bottom tabs, deck for the top tabs)."""
    t = PLY + 0.2
    if front:
        for c in tab_centres(BOX_L):
            w = w.cut(cutter(c - TAB_W / 2 - 0.1, c + TAB_W / 2 + 0.1, -WALL_Y - 0.1, -WALL_Y + t - 0.1))
    if back:
        for c in tab_centres(BOX_L):
            w = w.cut(cutter(c - TAB_W / 2 - 0.1, c + TAB_W / 2 + 0.1, WALL_Y - t + 0.1, WALL_Y + 0.1))
    if ends:
        for sx in (-1, 1):
            x0, x1 = (-WALL_X - 0.1, -WALL_X + t - 0.1) if sx < 0 else (WALL_X - t + 0.1, WALL_X + 0.1)
            for c in tab_centres(2 * (WALL_Y - PLY)):
                w = w.cut(cutter(x0, x1, c - TAB_W / 2 - 0.1, c + TAB_W / 2 + 0.1))
    return w


# ------------------------------------------------------------------ acrylic hood (5 mm clear, laser cut, finger joints)
HOOD_H = HOOD_TOP_IN - Z_BASE


def acr_box(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, ACR_T, centered=False).translate((x0, y0, 0))


def acr_cut(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, ACR_T + 2, centered=False).translate((x0, y0, -1))


def hood_tab_centres(length):
    return tab_centres(length, pitch=90.0)


def hood_floor_slots(w):
    """Slots in the top base layer for the bottom tabs of the four hood walls."""
    t = ACR_T + 0.2
    for c in hood_tab_centres(2 * HOOD_OUT_X):
        for y0 in (-HOOD_OUT_Y - 0.1, HOOD_IN_Y - 0.1):
            w = w.cut(cutter(c - HTAB / 2 - 0.1, c + HTAB / 2 + 0.1, y0, y0 + t))
    for c in hood_tab_centres(2 * HOOD_IN_Y):
        for x0 in (-HOOD_OUT_X - 0.1, HOOD_IN_X - 0.1):
            w = w.cut(cutter(x0, x0 + t, c - HTAB / 2 - 0.1, c + HTAB / 2 + 0.1))
    return w


def hood_wall_flat(length, inner=None, outer=None, long_wall=True):
    """Front/back wall (long) or end wall: profile in (u along the wall, v = Z), thickness ACR_T. Plain edges: the corners and the top are
    butt joints, solvent-welded. Only the bottom tabs remain (into the base top layer), which hold all four walls square while welding."""
    w = acr_box(-length / 2, length / 2, Z_BASE, HOOD_TOP_IN)
    for c in hood_tab_centres(length):
        w = w.union(acr_box(c - HTAB / 2, c + HTAB / 2, Z_TOP, Z_BASE))
    return w


def hood_front_back(front=True):
    w = hood_wall_flat(2 * HOOD_OUT_X)
    for k in range(6):                                                                       # vents just above the deck, 6 mm wide
        u = -150.0 + 60.0 * k
        w = w.cut(acr_cut(u - 20, u + 20, DECK_Z1 + 2, DECK_Z1 + 8))
    if front:
        w = w.cut(acr_cut(FRONT_CABLE_X - 7, FRONT_CABLE_X + 7, Z_BASE - 1, Z_BASE + 6))     # notch for the control pod wires
    return w


def hood_end():
    return hood_wall_flat(2 * HOOD_IN_Y)                                                    # fits between the front and back walls


def hood_top():
    w = acr_box(-HOOD_OUT_X, HOOD_OUT_X, -HOOD_OUT_Y, HOOD_OUT_Y)
    for k in range(6):                                                                       # top vents, 6 x 40 mm, two rows
        u = -150.0 + 60.0 * k
        for y in (-30.0, 30.0):
            w = w.cut(acr_cut(u - 20, u + 20, y - 3, y + 3))
    return w


def place_acr_xz(flat, y_shift):
    s = flat.val() if hasattr(flat, "val") else flat
    return s.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y_shift, 0))


def layer_top():
    w = layer_bottom(holes=True)
    for sx in (-1, 1):
        w = w.cut(cylz(ROD_D / 2 + 0.1, -1, PLY + 1, sx * X_POST, 0))                         # rod post holes
    for xb in BLADE_X:
        w = w.cut(cutter(xb - (BLADE_T + 0.2) / 2, xb + (BLADE_T + 0.2) / 2, -10.2, 10.2))   # blade tab slots
    return hood_floor_slots(wall_slots(w))                                                   # bottom tabs of the four plywood walls and the hood


def deck_flat():
    w = flat_rect(-WALL_X, WALL_X, -WALL_Y, WALL_Y)
    for x in XS:
        w = w.cut(cylz(19.0, -1, PLY + 1, x, 0))                                             # 38 mm holes round the 35 mm hubs
    for sx in (-1, 1):
        w = w.cut(cylz(ROD_D / 2 + 0.1, -1, PLY + 1, sx * X_POST, 0))                         # rod posts pass through
    for xb in BLADE_X:
        w = w.cut(cutter(xb - (BLADE_T + 0.2) / 2, xb + (BLADE_T + 0.2) / 2, -BLADE_W / 2 - 0.2, BLADE_W / 2 + 0.2))
    for x in (-BOX_L / 4, 0.0, BOX_L / 4):                                                 # M3 wood screws into the top edge of the front panel
        w = w.cut(cylz(1.7, -1, PLY + 1, x, -WALL_Y + PLY / 2))
    return wall_slots(w, front=False)                                                        # top tabs of the back and end walls


def wall_flat(length, bottom=True, top=True, cuts=()):
    """Wall profile in (u along the wall, v = Z world), thickness PLY along local z; tabs at the bottom (into the base) and top (into the deck)."""
    w = box(-length / 2, length / 2, Z_BASE, DECK_Z0, 0, PLY)
    for c in tab_centres(length):
        if bottom:
            w = w.union(box(c - TAB_W / 2, c + TAB_W / 2, Z_TOP, Z_BASE, 0, PLY))
        if top:
            w = w.union(box(c - TAB_W / 2, c + TAB_W / 2, DECK_Z0, DECK_Z1, 0, PLY))
    for (cu, cv, kind, size) in cuts:
        w = w.cut(cq.Workplane("XY").workplane(offset=-1).center(cu, cv).circle(size / 2).extrude(PLY + 2) if kind == "round"
                  else cq.Workplane("XY").workplane(offset=-1).center(cu, cv).rect(*size).extrude(PLY + 2))
    return w


WALL_LEN_X = BOX_L                                           # front and back walls span the full box
WALL_LEN_Y = 2 * (WALL_Y - PLY)                              # end walls fit between them
FRONT_CUT = [(FRONT_CABLE_X, 30.0, "round", 10.0)]           # wires from the control pod to the controller
BACK_CUT = [(REED_X, MAG_Z, "round", 4.0)]                   # reed switch leads


def place_xz(flat, y_shift):
    """Flat (u = X, v = Z, t) to the world: thickness along -Y, outer face at y_shift."""
    s = flat.val() if hasattr(flat, "val") else flat
    return s.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y_shift, 0))


def blade_flat():
    """Blade profile in (u = Y, v = Z world), thickness BLADE_T along local z."""
    pts = [(-10, Z_TOP), (10, Z_TOP), (10, Z_BASE), (BLADE_W / 2, Z_BASE), (BLADE_W / 2, BLADE_TOP), (-BLADE_W / 2, BLADE_TOP), (-BLADE_W / 2, Z_BASE), (-10, Z_BASE)]
    w = cq.Workplane("XY").polyline(pts).close().extrude(BLADE_T)
    return w.cut(cq.Workplane("XY").workplane(offset=-1).center(0, Z_TC).circle(TUBE_D / 2 + 0.1).extrude(BLADE_T + 2))


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
    boss = cylz(BOSS_R, Z_BASE, sm.BOSS_Z1).cut(cylz(sm.CABLE_R, Z_BASE - 1, sm.BOSS_Z1 + 1))
    for (x, y) in sm.MOTOR_BOTTOM_HOLES:                     # the four M2 screws from the underside pass through here into the motor
        boss = boss.cut(cylz(1.2, Z_BASE - 1, sm.BOSS_Z1 + 1, x, y))
    boss = boss.cut(box(-3.5, 3.5, 0, BOSS_R + 1, Z_BASE - 0.5, Z_BASE + 6.0))              # slot: the motor leads leave sideways into the box, toward the driver
    UNIT.append(("print_motor_boss", boss.val(), sm.PRINT_C, "fixed", "print"))
    drv = box(-15, 15, -12.5, 12.5, Z_BASE + 3, Z_BASE + 15).translate((0, 50, 0))
    UNIT.append(("placeholder_driver_board_30x25x12", drv.val(), "#2e6f4e", "fixed", "print_ph"))
    UNIT.append(("pin_3mm_steel_16", cylz(1.5, Z_PIN0, Z_PIN1).val(), sm.STEEL, "spin", "steel"))
    blk = box(-6.0, 6.0, -CLAMP_Y, CLAMP_Y, Z_BLK0, Z_TC - CLAMP_GAP)
    blk = blk.cut(cylx(TUBE_D / 2, -10, 10, 0, Z_TC))                                      # saddle for the tube
    blk = blk.cut(cylz(3.55, Z_BLK0 - 1, Z_BLK0 + 3.1)).cut(cylz(2.0, Z_BLK0 + 3.0, Z_BLK0 + 5.3))
    for sy in (-1, 1):
        blk = blk.cut(cylz(1.3, Z_TC - 8.0, Z_TC + 1, 0, sy * SCREW_Y))
    UNIT.append(("print_top_block", blk.val(), sm.PRINT_C, "fixed", "print"))
    UNIT.append(("print_top_cap", clamp_cap(0.0).val(), sm.PRINT_C, "fixed", "print"))
    brg = cylz(3.5, Z_BLK0, Z_BLK0 + 3.0).cut(cylz(1.5, Z_BLK0 - 1, Z_BLK0 + 4.0))
    UNIT.append(("bearing_683zz_top", brg.val(), sm.STEEL, "fixed", "steel"))


def clamp_cap(x, half_x=6.0):
    cap = box(x - half_x, x + half_x, -CLAMP_Y, CLAMP_Y, Z_TC + CLAMP_GAP, Z_TC + CAP_T).cut(cylx(TUBE_D / 2, x - 20, x + 20, 0, Z_TC))
    for sy in (-1, 1):
        cap = cap.cut(cylz(1.65, Z_TC - 1, Z_TC + CAP_T + 1, x, sy * SCREW_Y))
    return cap


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
    L = (layer_bottom(holes=True), layer_middle(), layer_top())
    for nm, w, z in (("laser_base_bottom_6mm", L[0], Z_BOT), ("laser_base_middle_6mm", L[1], Z_MID), ("laser_base_top_6mm", L[2], Z_TOP)):
        FRAME.append((nm, w.translate((0, 0, z)).val(), WOOD, "frame", "ply"))
    for k, y in enumerate((40.0, -40.0)):
        FRAME.append((f"ballast_steel_bar_{k + 1}", box(-BALLAST_L / 2, BALLAST_L / 2, y - BALLAST_W / 2, y + BALLAST_W / 2, Z_MID, Z_MID + PLY).val(), sm.STEEL, "frame", "steel"))
    for k, (x, y) in enumerate(((-BASE_L / 2 + 15, BASE_Y1 - 15), (BASE_L / 2 - 15, BASE_Y1 - 15), (-BASE_L / 2 + 15, BASE_Y0 + 15), (BASE_L / 2 - 15, BASE_Y0 + 15))):
        FRAME.append((f"rubber_foot_{k + 1}", cylz(6.0, 0, FEET_T, x, y).val(), sm.RUBBER, "frame", "rubber"))
    FRAME.append(("laser_deck_6mm", deck_flat().translate((0, 0, DECK_Z0)).val(), WOOD, "frame", "ply"))
    FRAME.append(("laser_front_panel_6mm", place_xz(wall_flat(WALL_LEN_X, bottom=True, top=False, cuts=FRONT_CUT), -(WALL_Y - PLY)), WOOD, "frame", "ply"))
    FRAME.append(("laser_back_wall_6mm", place_xz(wall_flat(WALL_LEN_X, cuts=BACK_CUT), WALL_Y), WOOD, "frame", "ply"))
    FRAME.append(("laser_end_wall_left_6mm", place_yz(wall_flat(WALL_LEN_Y), -WALL_X), WOOD, "frame", "ply"))
    FRAME.append(("laser_end_wall_right_6mm", place_yz(wall_flat(WALL_LEN_Y), WALL_X - PLY), WOOD, "frame", "ply"))
    # ---- control pod on the front ledge, outside the hood
    pod = box(POD_X - POD_L / 2, POD_X + POD_L / 2, POD_Y - POD_W / 2, POD_Y + POD_W / 2, Z_BASE, Z_BASE + POD_H)
    pod = pod.cut(box(POD_X - 26, POD_X + 26, POD_Y - 8, POD_Y + 8, Z_BASE - 1, Z_BASE + POD_H - 5))
    pod = pod.cut(cylz(3.75, Z_BASE + POD_H - 6, Z_BASE + POD_H + 1, POD_X - 18, POD_Y))                  # potentiometer bushing
    pod = pod.cut(cylx(5.5, POD_X - POD_L / 2 - 1, POD_X - 24, POD_Y, Z_BASE + 12))                          # DC barrel jack, 11 mm
    pod = pod.cut(box(POD_X + 24, POD_X + POD_L / 2 + 1, POD_Y - 4.75, POD_Y + 4.75, Z_BASE + 10.1, Z_BASE + 13.9))   # USB-C socket
    pod = pod.cut(box(POD_X - 24, POD_X - 12, POD_Y + 7, POD_Y + POD_W / 2 + 1, Z_BASE - 1, Z_BASE + 7))   # wires leave toward the hood
    for (hx, hy) in POD_HOLES:
        pod = pod.cut(cylz(2.1, Z_BASE - 1, Z_BASE + 6, hx, hy))                                           # M3 heat-set inserts
    FRAME.append(("print_control_pod", pod.val(), sm.PRINT_C, "frame", "print"))
    px = POD_X - 18
    FRAME.append(("pot_10k_with_knob", cylz(8.0, Z_BASE + POD_H - 18, Z_BASE + POD_H - 5, px, POD_Y).union(cylz(10.0, Z_BASE + POD_H, Z_BASE + POD_H + 15, px, POD_Y)).val(), "#2b2b2b", "frame", "print_ph"))
    # ---- acrylic hood and the interlock
    FRAME.append(("laser_hood_front_5mm", place_acr_xz(hood_front_back(front=True), -HOOD_IN_Y), "#e6f3f9", "frame", "acrylic"))
    FRAME.append(("laser_hood_back_5mm", place_acr_xz(hood_front_back(front=False), HOOD_OUT_Y), "#e6f3f9", "frame", "acrylic"))
    FRAME.append(("laser_hood_end_left_5mm", place_yz(hood_end(), -HOOD_OUT_X), "#e6f3f9", "frame", "acrylic"))
    FRAME.append(("laser_hood_end_right_5mm", place_yz(hood_end(), HOOD_IN_X), "#e6f3f9", "frame", "acrylic"))
    FRAME.append(("laser_hood_top_5mm", hood_top().translate((0, 0, HOOD_TOP_IN)).val(), "#e6f3f9", "frame", "acrylic"))
    FRAME.append(("reed_switch_3x16", cylx(1.5, REED_X - 8, REED_X + 8, WALL_Y + 1.5, MAG_Z).val(), "#b0c4de", "frame", "steel"))
    FRAME.append(("magnet_6x3_on_hood", cq.Workplane("XZ").workplane(offset=-HOOD_IN_Y).center(REED_X, MAG_Z).circle(3.0).extrude(3.0).val(), "#c0392b", "frame", "steel"))
    cx, cy = CTRL_XY
    FRAME.append(("placeholder_controller_esp32_55x28x14", box(cx - 27.5, cx + 27.5, cy - 14, cy + 14, Z_BASE + 3, Z_BASE + 17).val(), "#2e6f4e", "frame", "print_ph"))
    for k, sx in enumerate((-1, 1)):
        x = sx * X_POST
        FRAME.append((f"rod_post_8mm_steel_{k + 1}", cylz(ROD_D / 2, Z_MID, Z_POST1, x, 0).val(), sm.STEEL, "frame", "steel"))
        end = box(x - 7.0, x + 7.0, -CLAMP_Y, CLAMP_Y, Z_END0, Z_TC - CLAMP_GAP).cut(cylx(TUBE_D / 2, x - 20, x + 20, 0, Z_TC))
        end = end.cut(cylz(ROD_D / 2 + 0.05, Z_END0 - 1, Z_POST1 + 0.5, x, 0))
        for sy in (-1, 1):
            end = end.cut(cylz(1.3, Z_TC - 8.0, Z_TC + 1, x, sy * SCREW_Y))
        FRAME.append((f"print_end_clamp_{k + 1}", end.val(), sm.PRINT_C, "frame", "print"))
        FRAME.append((f"print_end_cap_{k + 1}", clamp_cap(x, 7.0).val(), sm.PRINT_C, "frame", "print"))
        FRAME.append((f"nut_m8_thin_{k + 1}", cq.Workplane("XY").workplane(offset=Z_MID).center(x, 0).polygon(6, NUT_AF / math.cos(math.radians(30))).extrude(4.0).cut(cylz(ROD_D / 2, Z_MID - 1, Z_MID + 5, x, 0)).val(), sm.STEEL, "frame", "steel"))
    for k, xb in enumerate(BLADE_X):
        FRAME.append((f"laser_blade_{k + 1}_3mm", place_yz(blade_flat(), xb - BLADE_T / 2), WOOD, "frame", "ply"))
    tube = cylx(TUBE_D / 2, -BAR_L / 2, BAR_L / 2, 0, Z_TC).cut(cylx(TUBE_ID / 2, -BAR_L / 2 - 1, BAR_L / 2 + 1, 0, Z_TC))
    FRAME.append((f"tube_carbon_10x8_{int(BAR_L)}", tube.val(), "#2b2b2e", "frame", "cf"))


def all_parts(poses):
    out = list(FRAME)
    for i, (az, t) in enumerate(poses):
        out += pose_unit(i, az, t)
    return out


def cqc(h, a=1.0):
    return cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255, a)


def assemble(poses, yup, hood=True, only_hood=False):
    root = cq.Assembly(name="spinning_mirror_row")
    subs = {}
    for nm, s, col, grp, _ in all_parts(poses):
        if (not hood and nm.startswith("laser_hood")) or (only_hood and not nm.startswith("laser_hood")):
            continue
        if yup:
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        if grp not in subs:
            subs[grp] = cq.Assembly(name=grp)
        subs[grp].add(s, name=nm, color=cqc(col, 0.25 if nm.startswith("laser_hood") else 1.0))
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
    rho = {"print": 1.25e-3, "steel": 7.85e-3, "brass": 8.5e-3, "acrylic": 1.19e-3, "ply": 0.65e-3, "alu": 2.7e-3, "rubber": 1.1e-3, "cf": 1.6e-3, "motor": 2.45e-3, "print_ph": 0.3e-3}
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
        if nm.startswith(("tube_", "ballast", "rubber", "rod_", "nut_", "placeholder_", "pot_", "reed_", "magnet_")):
            put(nm, s, "purchase")
        elif nm.startswith("print_"):
            put(nm, s, "print")
        else:
            put(nm, s, "laser")
    d = PARTS / "laser"
    flat = {"laser_base_bottom_6mm": layer_bottom(holes=True), "laser_base_middle_6mm": layer_middle(), "laser_base_top_6mm": layer_top(),
            "laser_deck_6mm": deck_flat(), "laser_front_panel_6mm": wall_flat(WALL_LEN_X, top=False, cuts=FRONT_CUT), "laser_back_wall_6mm": wall_flat(WALL_LEN_X, cuts=BACK_CUT),
            "laser_end_wall_6mm_x2": wall_flat(WALL_LEN_Y),
            "laser_hood_front_5mm": hood_front_back(front=True), "laser_hood_back_5mm": hood_front_back(front=False), "laser_hood_end_5mm_x2": hood_end(),
            "laser_hood_top_5mm": hood_top()}
    if BLADE_X:
        flat["laser_blade_3mm_x2"] = blade_flat()
    for nm, w in flat.items():
        cq.exporters.exportDXF(cq.Workplane(obj=w.val() if hasattr(w, "val") else w).faces("<Z").val(), str(d / f"{nm}.dxf"))
    print("Wrote", len(UNIT) + len(FRAME), "part STEP files and", len(flat), "laser DXF outlines to", PARTS)


def write_bom():
    nb = len(BLADE_X)
    rows = [("laser", f"Plywood 6 mm: base layers, {int(BASE_L)} x {int(BASE_W)} mm, bottom (motor screw holes), middle (ballast windows, nut pockets), top (wall slots, motor holes)", 3, "own cutter, bed 1219 x 914"),
            ("laser", f"Plywood 6 mm: deck {int(2 * WALL_X)} x {int(2 * WALL_Y)} mm, level with the top of the hub adapters (hub holes, post holes, front screw holes)", 1, "DXF laser_deck_6mm"),
            ("laser", "Plywood 6 mm: box walls, back (glued, 4 mm reed lead hole), two ends (glued, same profile), front panel (removable, 3 screws through the deck, 10 mm hole for the pod wires)", 4, "DXF laser_*_wall / panel"),
            ("laser", f"Clear cast acrylic 5 mm: hood, {2 * HOOD_OUT_X:.0f} x {2 * HOOD_OUT_Y:.0f} x {HOOD_TOP_IN - Z_BASE:.0f} mm tall; top, front, back, two ends (finger joints, vents 6 mm wide, notch for the pod wires). Solvent-weld the corners, leave the bottom tabs loose", 5, "CO2 laser (to be confirmed) or order cut; DXF laser_hood_*"),
            ("buy", "Solvent cement for acrylic (e.g. Weld-On 4 or dichloromethane type), adhesive foam strip 3 mm for the hood seat", 1, "")]
    if nb:
        rows.append(("laser", "Plywood 3 mm: blade, 26 mm wide with a tube hole and a tab into the top layer; in the gaps 2|3 and 5|6", nb, "DXF laser_blade_3mm_x2; own cutter, 3 mm ply"))
    rows += [
        ("print", f"PETG: ring with foot and pin boss, carrier, hub adapter, top block, top cap (x{N} each)", 5 * N, "Bambu P1S, 0.4 mm, 4 walls"),
        ("print", "PETG: end clamp block (x2) and end cap (x2) for the tube and rod posts", 4, "M3 x 16 screws, M3 grub screw for the rod"),
        ("print", f"PETG or ASA, matt black: motor boss (x{N})", N, "clamped between the base and the motor by the M2 screws"),
        ("print", "PETG or ASA, matt black: control pod on the front ledge (dial, DC jack, USB-C), 4 M3 x 25 screws from below into heat-set inserts", 1, "all printed parts: matt black, PETG or ASA in the sun, not PLA"),
        ("buy", "iPower GM2804-100T gimbal motor with AS5048A encoder, 12 V (35 x 26 mm, hollow shaft 6.5 mm)", N, "STEP in cad/src/assets"),
        ("buy", f"Motor driver, 3-phase, open-loop capable (SimpleFOC Mini or similar), plus a microcontroller with {3 * N} PWM outputs (ESP32 or RP2040{', two boards' if N > 5 else ''})", N, "random-walk speed per motor"),
        ("buy", f"12 V supply, {max(2, N)} A, fuse, 5.5 x 2.1 mm DC barrel jack (11 mm hole) in the control pod", 1, ""),
        ("buy", "USB-C panel-mount socket or short USB-C extension (9.5 x 3.8 mm slot) in the control pod, wired to the controller for programming", 1, ""),
        ("buy", "10k rotary potentiometer, 7 mm bushing (hole 7.5 mm), knob about 20 mm, for the jitter amount, in the control pod", 1, "wires to the controller"),
        ("buy", "Reed switch (glass, 3 x 16 mm) on the plywood back wall and a 6 x 3 mm neodymium magnet on the hood: the controller stops the motors when the hood lifts", 2, "interlock"),
        ("buy", "Standoffs M3 x 3 mm and screws for the driver and controller boards (envelopes in the model are placeholders: 30 x 25 x 12 and 55 x 28 x 14)", N + 1, "check real board sizes"),
        ("buy", "Bearing 683ZZ (3 x 7 x 3): 2 per ring hinge plus 1 per top block", 3 * N, ""),
        ("buy", "Steel pin 3 mm x 16 mm (ring top)", N, "press into the ring boss"),
        ("buy", f"Steel rod 3 mm x {int(2 * sm.R_OUT)} mm (hinge axle)", N, ""),
        ("buy", "Acrylic mirror 2 mm, 80 mm discs (laser-cut), two per unit", 2 * N, "one per unit if single-sided"),
        ("buy", "Brass slug 6 x 5 mm (swap for steel, aluminium or none)", N, "tune the random behaviour"),
        ("buy", f"Carbon fibre tube 10 x 8 mm, {int(BAR_L)} mm", 1, "clamped, no drilling; check the stiffness on a sample"),
        ("buy", "Steel rod 8 mm (silver steel), about 150 mm, threaded M8 for the lower 14 mm", 2, "end posts, screw into the captive nuts"),
        ("buy", "M8 thin nut, 4 mm (DIN 439)", 2, "captive in the middle layer"),
        ("buy", f"Steel flat bar 38 x 6 mm, {int(BALLAST_L)} mm (about {38 * 6 * BALLAST_L * 7.85e-6:.2f} kg each)", 2, "ballast in the middle layer windows"),
        ("buy", "Rubber feet 12 mm", 4, ""),
        ("buy", f"Fasteners: M2 x 30 ({4 * N}, up from under the base into each motor), M2 x 6 countersunk ({4 * N}, hub to bell), M3 x 16 ({2 * N} ring to hub, 8 clamps), M3 x 6 trim ({4 * N}), M3 grub (2), M3 heat-set inserts ({2 * N}), M3 x 20 wood screws (3, front panel), wood glue", 1, "set"),
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
        alpha = 0.10 if nm.startswith("laser_hood") else 1.0
        gain = 2.4 if col == sm.PRINT_C else 1.0                                              # matt black prints, brightened in previews only
        for a, b, c in t:
            tri = v[[a, b, c]]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            sh = 0.55 + 0.45 * abs(float(n @ light) / nn) if nn > 1e-9 else 0.8
            tris.append(tri); cols.append(list(np.clip(base * sh * gain, 0, 1)) + [alpha])
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
    ap.add_argument("--units", type=int, default=7, help="number of units, 7 (the row) or 1 (single test rig)")
    ap.add_argument("--seed", type=int, default=3, help="random pose for the previews")
    a = ap.parse_args()
    build_unit()
    build_frame()

    print(f"{'Row' if N > 1 else 'Single test rig'} of {N}: unit centres X = {', '.join(f'{x:.1f}' for x in XS)}; gaps between rings {PITCH - 2 * R_OUT:.0f} mm, blades at X {', '.join(f'{x:.1f}' for x in BLADE_X) or 'none'}")
    print(f"Base {BASE_L:.0f} x {BASE_W:.0f} x {Z_BASE - FEET_T:.0f} mm on feet, rod posts at X +/-{X_POST:.1f}, tube {BAR_L:.0f} mm long, centre {Z_TC:.0f} mm above the table, blades to {BLADE_TOP:.0f} mm")
    print(f"Deck {DECK_Z0:.2f} to {DECK_Z1:.2f} mm (top level with the hub tops), {DECK_Z0 - (sm.MOTOR_Z0 + sm.MOTOR_ZTOP - sm.MOTOR_ZBOT):.2f} mm above the bell, hub holes {19 * 2:.0f} mm for 35 mm hubs; box interior {DECK_Z0 - Z_BASE:.1f} mm tall, {2 * (WALL_X - PLY):.0f} x {2 * (WALL_Y - PLY):.0f} mm; ring bottom {ZC - R_OUT:.1f} mm, {ZC - R_OUT - DECK_Z1:.1f} mm over the deck")
    hood_kg = sum(sh.Volume() for nm, sh, *_ in FRAME if nm.startswith("laser_hood")) * 1.19e-6
    print(f"Hood: 5 mm acrylic, {2 * HOOD_OUT_X:.0f} x {2 * HOOD_OUT_Y:.0f} mm outside, inner top {HOOD_TOP_IN} mm above the table ({HOOD_TOP_IN - Z_BASE:.0f} mm tall from the base top), {HOOD_GAP:.0f} mm gap round the plywood box, about {hood_kg:.1f} kg; base {BASE_L:.0f} x {BASE_W:.0f} mm with a {LEDGE:.0f} mm front ledge for the control pod")
    print(f"Pin {TOP_PIN_L:.0f} mm into a 683ZZ in the block; ring top boss to {ZC + R_OUT + 5:.0f} mm, block bottom {Z_BLK0:.0f} mm (3 mm axial float before the boss touches)")
    m = mass_g()
    print(f"Mass: frame about {m['frame'] / 1000:.1f} kg (of which steel ballast {2 * 38 * 6 * BALLAST_L * 7.85e-6:.2f} kg), {N} unit{'s' if N > 1 else ''} about {m['units'] / 1000:.2f} kg")

    if a.check:
        multi = [(nm, len(s.Solids())) for nm, s, *_ in UNIT + FRAME if nm.startswith(("print_", "laser_")) and len(s.Solids()) != 1]
        print("printed or cut parts that are not a single solid:", multi or "none")
        names_unit = lambda parts: {p[0] for p in parts if "_spin" in p[3] or "_tilt" in p[3]}
        total = 0
        for seed in range(8):
            P = all_parts(random_poses(seed))
            bad = clashes(P, only_with=names_unit(P))
            bad = [b for b in bad if not (b[0].split("_", 1)[1].startswith(("axle", "bearing", "pin")) and b[1].split("_", 1)[1].startswith(("axle", "bearing", "pin")))]
            bad = [b for b in bad if not ("motor_gm2804" in b[0] and "motor_gm2804" in b[1])]
            total += len(bad)
            if bad:
                print(f"seed {seed}: {len(bad)} clashes", bad[:8])
        print("total clashes over 8 random poses (moving parts against everything):", total)
        static = [b for b in clashes(all_parts([(0, 0)] * N)) if not ("motor_gm2804" in b[0] and "motor_gm2804" in b[1])]
        print("static clashes at az 0, tilt 0:", len(static), static[:12])
        return

    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_all(a.up == "y")
    write_bom()
    P0 = random_poses(a.seed)
    assemble(P0, a.up == "y").save(str(OUTD / f"{TAG}-assembly.step"))
    assemble(P0, a.up == "y", hood=False).save(str(OUTD / f"{TAG}-assembly-no-hood.step"))       # for Fusion: the hood as a separate, hideable file
    assemble(P0, a.up == "y", only_hood=True).save(str(OUTD / f"{TAG}-hood.step"))
    print("Wrote", OUTD / f"{TAG}-assembly.step")
    P = all_parts(P0)
    hx = BASE_L / 2 + 10
    bx = (-hx, hx, BASE_Y0 - 10, BASE_Y1 + 10, 0, HOOD_TOP_IN + 15)
    z = 1.35 if N > 1 else 1.0
    what = f"{'Row of ' + str(N) if N > 1 else 'Single test rig'}"
    render(P, IMG / "row.png", [(14, -35, f"{what}, hood on (clear)"), (0, -90, "Front")], box_=bx, zoom=z)
    render(P, IMG / "row-open.png", [(14, -35, f"{what}, hood off"), (0, -90, "Front, hood off")], box_=bx, zoom=z, hide=("laser_hood",))
    render(P, IMG / "row-plan.png", [(90, -90, "Plan, hood on"), (90, -90, "Plan, hood off")][:1], box_=bx, zoom=z)
    render(P, IMG / "row-detail.png", [(18, -60, "Left end, hood off"), (16, -125, "Back, hood off")],
           box_=(-hx, -40 if N > 1 else hx, BASE_Y0 - 10, BASE_Y1 + 10, 0, HOOD_TOP_IN + 15), zoom=1.1 if N > 1 else 1.0, hide=("laser_hood",))
    render(P, IMG / "row-pod.png", [(25, -20, "Control ledge and pod, front")], box_=(-120, 120, BASE_Y0 - 5, BASE_Y0 + 120, 0, 120), zoom=1.2)
    render(P, IMG / "row-section.png", [(4, -90, "Section (y > 0 cut away), hood hidden")], box_=bx, zoom=z, cut_y=0.0, hide=("laser_hood",))
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
