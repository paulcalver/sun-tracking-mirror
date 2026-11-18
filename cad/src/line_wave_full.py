#!/usr/bin/env python3
"""Line of 7 wall mirrors, travelling-wave (camshaft) version, FULL detail model (CadQuery). Concept model, nothing built.

Builds on line_mirrors.py (same mirror unit and tip joint) and draws every part with the way it is held: laser-cut enclosure and
plates, 3D-printed blocks and mounts, metal stock, bought parts, screws and nuts. `--bom` writes the bill of materials from the model.

Review 2 (2026-11-04) changed the tilt axis: the tilt frame is built on a 20 x 10 aluminium bar and is driven in Y at BOTH ends by
two vertical belts on a cross shaft (one NEMA 17). The cam motor is a 28BYJ-48 geared stepper on a printed end block. Tabs are
pushed against the tip balls by printed flexure pads, so the ball sandwich has no play.

Frame (mm): X along the row (right), Y up, Z out of the wall, origin on the wall at the middle of the row.
Strip: 824 x 96 x 62. The mirror row is centred, so the strip ends are the same distance (177 mm) from the outer mirror edges.

Usage (repo root): python3 cad/src/line_wave_full.py [--check] [--sun] [--render] [--bom] [--step]
"""
import argparse
import math
import re
import sys
from pathlib import Path

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import line_mirrors as lm  # noqa: E402
from line_mirrors import box, cyl_along, cylz, shp, sph  # noqa: E402

lm.configure("wave")
# this model is 2 mm taller than the first wave model: the Z offset keeps the cams under the pan bar with room to spare
lm.Z_T, lm.Z_PL0, lm.Z_PL1 = 29.2, 54.0, 62.0
lm.XL, lm.XR = -412.0, 412.0
lm.STEM_R = 1.0                              # 2 mm stem rod: a 3 mm rod tilted 25 deg in the pan direction cannot pass the 4.4 mm slot

OUT = lm.OUT
IMG = lm.IMG
XS, N, L = lm.XS, lm.N, lm.L
ZT, ZP0, ZP1 = lm.Z_T, lm.Z_PL0, lm.Z_PL1
XL, XR, HY, WALL = lm.XL, lm.XR, lm.HY, lm.WALL
HALF_H, TRAV, SLOT_W = lm.HALF_H, lm.TRAV, lm.SLOT_W
ZAX = 24.15                                  # motor axis height (NEMA 17 body sits on the back plate)
ZB = ZT - HALF_H                             # top face of the lower lip (tab layer); ball sits ZB..ZB+2*HALF_H
ZA = ZT + HALF_H                             # underside of the upper lip (pan bar)
ZT0 = ZB - 2.0                               # tab layer bottom
SL = 2 * (TRAV + 3.0) + SLOT_W               # ball slot length 36.8
PB_Y = 30.0                                  # pan bar half height
LIP = 0.5                                    # pan bar contact lip (steel shim); the 1.5 mm relief layer above it has 9 mm slots
E = lm.E_AMP                                 # cam throw 1.0
DPH = lm.D_PHASE
ZAC = ZAX + 0.5                              # camshaft axis: 0.5 mm higher than a motor sitting on the back plate
CAM_R, SHAFT_R = 5.0, 2.5                    # cam disc radius; camshaft is a 5 mm D shaft (cams keyed on the flat)
XF, XN, XPL0 = -386.0, -330.0, 10.5          # X belt: motor pulley x, idler x, pulley start in y
PIN_L, PIN_R, PIN_Y = -242.0, 249.0, 13.5    # tilt-frame X guide pins (x, y)
BAR_Y, BAR_Z = (-28.0, -18.0), (3.5, 23.5)   # tilt-frame backbone: 20 x 10 aluminium flat bar (frame coordinates)
BAR_X = (-254.0, 262.0)
YS_Y, YS_Z, YB_Y = 36.5, 45.0, -36.5         # Y drive: cross shaft (y, z) at the top, bottom idlers at y = YB_Y
LOOP_L, LOOP_R = (-254.0, -246.0), (262.0, 270.0)   # x of the left and right Y pulleys (belt runs 1 mm inside)
YM_FACE = 307.0                              # Y motor face (motor axis along x at y 0, z ZAX)
TP_X = (311.0, 319.0)                        # transfer pulleys (Y motor to cross shaft)
XS_BEAR = (-263.0, -120.0, 120.0, 254.0, 327.0)     # cross-shaft bearing blocks (centres)
BLK = [(XS[i] + 35.0 - 5, XS[i] + 35.0 + 5, XS[i] + 35.0 - 10, XS[i] + 35.0 + 10) for i in range(N - 1)]
BLK = [(-236.0, -226.0, -236.0, -226.0)] + BLK + [(237.0, 246.0, 233.0, 243.0)]   # camshaft blocks: x0, x1 and retainer support x0, x1
BYJ_C = None                                 # 28BYJ-48 body centre (set below once CAM_Y is known)


def _tab_raw(ph):
    zc = ZAC + E * math.cos(ph)
    dz = max(0.0, ZT0 - zc)
    return E * math.sin(ph) + math.sqrt(CAM_R ** 2 - dz ** 2) + 6.0


CAM_Y = -sum(_tab_raw(math.radians(k)) for k in range(360)) / 360.0    # tab bottom edge rests on the cam; mean tab height 0
BLK_TOP = CAM_Y + 2.6 + 2.0
BYJ_C = (CAM_Y + 3.59, ZAC - 7.15)          # body offset 8 mm from the shaft, low and toward +y so it sits 0.5 above the back plate
_v = (0.894, 0.449)
BYJ_EARS = [(BYJ_C[0] + s_ * 17.5 * _v[0], BYJ_C[1] + s_ * 17.5 * _v[1]) for s_ in (1, -1)]

# process colours
C_LASER, C_PRINT, C_BUY, C_ENC = "#5aa0c8", "#e08a3c", "#9aa0a8", "#33363b"
C_GLASS, C_CARR = lm.GLASSC, lm.CARR

PARTS = {}        # name -> dict(shape, group, color)


def reg(name, shape, group="static", color=C_BUY):
    PARTS[name] = dict(shape=shp(shape), group=group, color=color)


def slot_cut(p, cx, cy, ln, w, ang, z0, z1):
    return p.cut(cq.Workplane("XY").workplane(offset=z0 - 1).center(cx, cy).slot2D(ln, w, ang).extrude(z1 - z0 + 2))


def hole_cut(p, cx, cy, r, z0, z1):
    return p.cut(cylz(r, z0 - 1, z1 + 1, cx, cy))


# ------------------------------------------------------------------ fasteners
FAST = []         # dicts(name, spec, kind) for the BOM
ALLOW = {}        # screw/nut name -> set of part names it may overlap (the parts it joins)
HEAD = {2: (1.9, 1.5), 3: (2.75, 2.0), 4: (3.8, 2.2)}      # pan / button head radius, height by thread size
CSK = {2: (2.0, 1.2), 3: (3.0, 1.7), 4: (4.0, 2.2)}


def _pt(p, d, t):
    return tuple(p[k] + d[k] * t for k in range(3))


def _cyl(p, d, length, r):
    return lm.between(p, _pt(p, d, length), r)


def _hex(c, d, thick, across):
    """Hex prism centred on c, axis d, thickness thick, across-flats `across`."""
    h = cq.Workplane("XY").polygon(6, across / math.cos(math.radians(30))).extrude(thick).translate((0, 0, -thick / 2))
    return lm.orient(shp(h), d).translate(cq.Vector(*c))


def _cut(name, solid):
    PARTS[name]["shape"] = PARTS[name]["shape"].cut(shp(solid))


def screw(name, head_pos, d, length, size=3, head="pan", clear=(), tap=(), allow=(), group=None):
    """Screw with its head underside (or flush face for csk) at head_pos, shank along d for `length`.
    clear: parts it passes through (clearance hole), tap: parts it threads into (pilot hole), allow: extra parts it may touch."""
    r = size / 2.0
    hr, hh = (CSK if head == "csk" else HEAD)[size]
    shank = _cyl(head_pos, d, length, r)
    if head == "csk":
        hd = _cyl(head_pos, d, hh, hr)
    else:
        hd = _cyl(_pt(head_pos, d, -hh), d, hh, hr)
    s = shank.union(hd)
    grp = group or next((PARTS[p]["group"] for p in list(clear) + list(tap) if PARTS[p]["group"] != "static"), "static")
    reg("screw_" + name, s, grp, "#c8ccd2")
    for i, p in enumerate(clear):
        _cut(p, _cyl(_pt(head_pos, d, -0.05), d, length + 0.1, r + 0.2))
        if head == "csk" and i == 0:
            _cut(p, _cyl(_pt(head_pos, d, -0.05), d, hh + 0.05, hr + 0.15))
    for p in tap:
        _cut(p, _cyl(_pt(head_pos, d, 0), d, length, r - 0.3))
    ALLOW["screw_" + name] = set(clear) | set(tap) | set(allow)
    FAST.append(dict(name=name, spec=f"M{size} x {length:g} {'countersunk' if head == 'csk' else 'button/pan head'}"))


def nut(name, centre, d_open, part, size=3):
    """Hex nut sitting in a pocket in `part`; the pocket opens along d_open."""
    thick, across = {2: (1.6, 4.0), 3: (2.4, 5.5), 4: (3.2, 7.0)}[size]
    reg("nut_" + name, _hex(centre, d_open, thick, across), PARTS[part]["group"], "#8d939a")
    _cut(part, _hex(_pt(centre, d_open, 6.0), d_open, 12.0 + thick, across + 0.35))
    ALLOW["nut_" + name] = {part}
    FAST.append(dict(name=name, spec=f"M{size} nut"))


# ------------------------------------------------------------------ neutral geometry
def belt_yz(c, d, ang, x0, x1):
    """GT2 belt loop in a YZ plane: c = (y, z) centre, d = pulley centre distance, ang = loop angle from +y (deg), x0..x1 belt width."""
    return shp(lm.belt_xy(c, d, ang, x0, x1)).rotate((0, 0, 0), (1, 1, 1), 120)


def build_neutral():
    PARTS.clear(); FAST.clear(); ALLOW.clear()
    # ---------------- enclosure: laser cut, cemented; printed posts carry the 10 front-plate screws
    bp = box(XL, XR, -HY, HY, 0, WALL)
    for (x, y) in ((-390, 38), (390, 38), (-390, -38), (390, -38), (-275, -40), (300, -40)):
        bp = hole_cut(bp, x, y, 2.5, 0, WALL)
    reg("back_plate", bp, color=C_ENC)
    reg("wall_top", box(XL, XR, HY - WALL, HY, WALL, ZP0).cut(cyl_along("y", 1.7, HY - WALL - 1, HY + 1, XN, ZAX)), color=C_ENC)
    reg("wall_bottom", box(XL, XR, -HY, -HY + WALL, WALL, ZP0), color=C_ENC)
    reg("end_left", box(XL, XL + WALL, -HY + WALL, HY - WALL, WALL, ZP0), color=C_ENC)
    reg("end_right", box(XR - WALL, XR, -HY + WALL, HY - WALL, WALL, ZP0).cut(cyl_along("x", 5.6, XR - WALL - 1, XR + 1, 0, 18)), color=C_ENC)
    for k, (z0, z1) in enumerate(((ZP0, ZP0 + 4), (ZP0 + 4, ZP1))):
        f = box(XL, XR, -HY, HY, z0, z1)
        for x in XS:
            f = hole_cut(f, x, 0, lm.PIV_R + 0.05, z0, z1)
        reg(f"front_plate_{k + 1}", f, color=C_ENC)
    for i, x in enumerate((-405.0, -340.0, 0.0, 340.0, 405.0)):
        mid = x == 0.0
        for tag, (y0, y1) in (("t", (40.0 if mid else 37.0, 45.0)), ("b", (-45.0, -41.6 if mid else -39.8))):
            reg(f"corner_post_{i}{tag}", box(x - 4, x + 4, y0, y1, WALL, ZP0), color=C_PRINT)
            screw(f"front_{i}{tag}", (x, (y0 + y1) / 2, ZP1), (0, 0, -1), 12, 3, "csk", clear=("front_plate_2", "front_plate_1"), tap=(f"corner_post_{i}{tag}",))

    # ---------------- pan group: bar (0.5 mm PET lip + 1.5 mm acrylic relief) with a tail to the X belt; it is pushed against the rail caps by the balls
    def bar(z0, z1, w):
        b = box(-226, 226, -PB_Y, PB_Y, z0, z1).union(box(-362, -226, 25.0, 29.6, z0, z1))
        for x in XS:
            b = slot_cut(b, x, 0, SL, w, 90, z0, z1)
        return b
    reg("pan_bar_lip", bar(ZA, ZA + LIP, SLOT_W), "pan", C_LASER)
    reg("pan_bar_relief", bar(ZA + LIP, ZA + 2.0, 9.0), "pan", C_LASER)
    reg("x_belt_clamp", box(-364, -350, XPL0 + 0.5, XPL0 + 8.0, 24.0, 30.5).union(box(-364, -350, XPL0 + 8.0, 29.6, 24.0, ZA)), "pan", C_PRINT)
    reg("x_belt_clamp_cap", box(-364, -350, XPL0 + 0.5, XPL0 + 8.0, 31.95, 33.45), "pan", C_PRINT)
    for side in ("top", "bottom"):
        sg = 1 if side == "top" else -1
        for seg, (xa, xb) in (("a", (-220, -5)), ("b", (5, 220))):
            y_in, y_out = (30.4, 45.0) if sg > 0 else (-45.0, -30.4)
            ylo, yhi = (27.0, 30.4) if sg > 0 else (-30.4, -27.0)
            web = box(xa, xb, y_in, y_out, ZA - 0.5, ZA + 4.05)
            up = box(xa, xb, ylo, yhi, ZA + 2.05, ZA + 4.05)          # cap: the balls push the bar against it; it slides on PTFE tape (0.05 mm)
            reg(f"pan_rail_{side}_{seg}", web.union(up), color=C_PRINT)
            wall = "wall_top" if sg > 0 else "wall_bottom"
            for j, xx in enumerate((xa + 20, (xa + xb) / 2, xb - 20)):
                screw(f"rail_{side}_{seg}{j}", (xx, 48.0 * sg, ZA + 1.0), (0, -sg, 0), 10.0, 3, "csk", clear=(wall,), tap=(f"pan_rail_{side}_{seg}",))
    for xx in (-360.5, -353.5):
        screw(f"tail_{int(-xx)}", (xx, 27.3, ZA + 2.0), (0, 0, -1), 6.0, 3, "csk", clear=("pan_bar_relief", "pan_bar_lip"), tap=("x_belt_clamp",))
        screw(f"cap_{int(-xx)}", (xx, 14.5, 33.45), (0, 0, -1), 9.0, 3, "pan", clear=("x_belt_clamp_cap",), tap=("x_belt_clamp",), allow=("x_belt",))
    for k, (x, y) in enumerate(((-105, 24), (-105, -24), (105, 24), (105, -24))):
        screw(f"lip_{k}", (x, y, ZA), (0, 0, 1), 3.6, 2, "pan", clear=("pan_bar_lip", "pan_bar_relief"), allow=(f"nut_lip_{k}",))
        reg(f"nut_lip_{k}", _hex((x, y, ZA + 2.0 + 0.8), (0, 0, 1), 1.6, 4.0), "pan", "#8d939a")
        ALLOW[f"nut_lip_{k}"] = {f"screw_lip_{k}"}
        FAST.append(dict(name=f"niplip{k}", spec="M2 nut"))

    # ---------------- tilt frame (frame coordinates, y relative to the frame): aluminium backbone, printed end block and bracket,
    # camshaft blocks, comb (guides the tabs), retainer pieces with flexure pads (push the tabs onto the balls)
    reg("tilt_backbone", box(BAR_X[0], BAR_X[1], BAR_Y[0], BAR_Y[1], BAR_Z[0], BAR_Z[1]), "tilt", "#a9b0b8")
    comb = box(-254, 262, 13, 16, ZT0, ZB)
    edges = [-254.0] + sum(([XS[i] - 22.3, XS[i] + 22.3] for i in range(N)), []) + [262.0]
    for k in range(N + 1):
        comb = comb.union(box(edges[2 * k], edges[2 * k + 1], -4.0, 13, ZT0, ZB))
    comb = comb.union(box(-254, -234, 13, 31, ZT0, ZB)).union(box(240, 258, 13, 31, ZT0, ZB))
    comb = comb.union(box(-258, -254, -1.0, 5.0, ZT0, ZB)).union(box(262, 266, -1.0, 5.0, ZT0, ZB))      # tabs into the end block and bracket
    for x in XS:
        comb = comb.union(box(x - 0.9, x + 0.9, 10.5, 13.0, ZT0, ZB))                                      # spring locating tongue
    for px in (PIN_L, PIN_R):
        comb = slot_cut(comb, px, PIN_Y, 2 * 13.4 + 4.2, 4.2, 90, ZT0, ZB)
    reg("tab_comb", comb, "tilt", C_LASER)
    # left end block (printed): holds the 28BYJ-48, the backbone end, the comb tab and the left Y belt clamp
    ce = box(-258, -254, -28, 8, BAR_Z[0], 37.2).union(cyl_along("x", 3.5, -258, -254, *BYJ_EARS[0])).union(box(-254, -246, -8, 1, 33.0, 37.2))
    ce = ce.cut(cyl_along("x", 4.8, -259, -253, CAM_Y, ZAC)).cut(cyl_along("x", 5.5, -257, -253, CAM_Y, ZAC))
    ce = ce.cut(box(-258.5, -253.5, -1.05, 5.05, ZT0 - 0.05, ZB + 0.05))
    reg("cam_end", ce, "tilt", C_PRINT)
    br = box(262, 270, -28, 7, BAR_Z[0], 36.4).union(box(262, 270, -3, 5, 36.4, 37.2))
    br = br.cut(box(261.9, 267.7, -1.05, 5.05, ZT0 - 0.05, ZB + 0.05))      # comb tab pocket 1.7 mm longer: the acrylic comb can grow
    reg("tilt_bracket", br, "tilt", C_PRINT)
    for j, (yy, zz) in enumerate(((-20.5, 19.5), (-25.5, 15.5))):
        screw(f"bar_l{j}", (-258.0, yy, zz), (1, 0, 0), 10.0, 3, "csk", clear=("cam_end",), tap=("tilt_backbone",))
        screw(f"bar_r{j}", (270.0, yy, zz), (-1, 0, 0), 14.0, 3, "csk", clear=("tilt_bracket",), tap=("tilt_backbone",))
    # Y belt clamps: jaw under the back run of each vertical belt, cap above, 2 M2 through the belt
    reg("y_clamp_cap_l", box(-254, -246, -8, 1, 38.6, 40.6), "tilt", C_PRINT)
    reg("y_clamp_cap_r", box(262, 270, -3, 5, 38.6, 40.6), "tilt", C_PRINT)
    for j, yy in enumerate((-6.0, -1.0)):
        screw(f"yclamp_l{j}", (-250.0, yy, 40.6), (0, 0, -1), 6.0, 2, "pan", clear=("y_clamp_cap_l",), tap=("cam_end",), allow=("y_belt_l",))
    for j, yy in enumerate((-1.5, 3.5)):
        screw(f"yclamp_r{j}", (266.0, yy, 40.6), (0, 0, -1), 6.0, 2, "pan", clear=("y_clamp_cap_r",), tap=("tilt_bracket",), allow=("y_belt_r",))
    # cam motor: 28BYJ-48 (geared, 5 mm shaft with flats), ears screwed to the end block
    byj = cyl_along("x", 14.0, -277, -259, *BYJ_C)
    for ey, ez in BYJ_EARS:
        byj = byj.union(cyl_along("x", 3.5, -259, -258, ey, ez))
    byj = byj.union(cyl_along("x", 4.5, -258, -256.5, CAM_Y, ZAC)).union(cyl_along("x", 2.5, -256.5, -249, CAM_Y, ZAC))
    reg("cam_motor", byj, "tilt", C_BUY)
    for j, (ey, ez) in enumerate(BYJ_EARS):
        screw(f"byj_{j}", (-259.0, ey, ez), (1, 0, 0), 5.0, 3, "pan", tap=("cam_end",), allow=("cam_motor",))
    reg("shaft_coupler", cyl_along("x", 5.0, -257, -237, CAM_Y, ZAC), "tilt", C_BUY)
    reg("camshaft", cyl_along("x", SHAFT_R, -246, 246, CAM_Y, ZAC), "tilt", "#b9bec4")
    reg("shaft_collar", cyl_along("x", 4.0, 246.1, 250.1, CAM_Y, ZAC).cut(cyl_along("x", SHAFT_R, 245, 251, CAM_Y, ZAC)), "tilt", C_BUY)
    for k, (x0, x1, e0, e1) in enumerate(BLK):
        if k == 0:      # left: no bearing (the motor shaft carries the end); a low post under tab 0 that only supports the retainer
            blk = box(x0, x1, BAR_Y[1], -8.0, 18.0, 22.0).union(box(e0, e1, -8.0, 4.5, 18.0, ZT0 - 2.5))
        else:
            blk = box(x0, x1, BAR_Y[1], BLK_TOP, 18.0, ZAC + 4.0).union(box(e0, e1, -8.0, 4.5, 18.0, ZT0 - 2.5))
            blk = blk.cut(cyl_along("x", SHAFT_R + 0.1, x0 - 1, x1 + 1, CAM_Y, ZAC))
        reg(f"shaft_block_{k}", blk, "tilt", C_PRINT)
        xm = (x0 + x1) / 2
        for j, xx in enumerate((xm - 3.4, xm + 3.4) if x1 - x0 >= 10 else (xm,)):
            screw(f"block_{k}{j}", (xx, BAR_Y[0], 20.5), (0, 1, 0), 14, 3, "pan", clear=("tilt_backbone",), tap=(f"shaft_block_{k}",))
    # retainer pieces (printed, one per tab): cemented under the comb teeth, resting on the block extensions; two flexure tongues
    # per tab end in pads that push the tab towards the pan bar (print the pads 0.3 mm proud for about 0.5 N per tab)
    for i, x in enumerate(XS):
        x0, x1 = max(x - 32, -236.0), min(x + 32, 242.0)
        r = box(x0, x1, -4, 4.5, ZT0 - 2.5, ZT0 - 1.0)
        if x0 < x - 22.6:
            r = r.union(box(x0, x - 22.6, -4, 4.5, ZT0 - 1.0, ZT0))
        r = r.union(box(x + 22.6, x1, -4, 4.5, ZT0 - 1.0, ZT0))
        for sgn in (-1, 1):
            a, b = sorted((x + sgn * 13, x + sgn * 26))
            for y0, y1 in ((2.5, 3.5), (-3.5, -2.5)):
                r = r.cut(box(a, b, y0, y1, ZT0 - 2.6, ZT0 - 0.99))
            ta, tb = sorted((x + sgn * 13, x + sgn * 14))
            r = r.cut(box(ta, tb, -3.5, 3.5, ZT0 - 2.6, ZT0 - 0.99))
            pa, pb = sorted((x + sgn * 14, x + sgn * 17))
            r = r.union(box(pa, pb, -2.5, 2.5, ZT0 - 1.0, ZT0))
        reg(f"retainer_{i}", r, "tilt", C_PRINT)
        lx = -234.3 if i == 0 else x - 29
        rx = x + 29
        for j, (sx, blk_i) in enumerate(((lx, i), (rx, i + 1))):
            screw(f"ret_{i}{j}", (sx, 0.25, ZB), (0, 0, -1), 8.0, 2, "pan", clear=("tab_comb", f"retainer_{i}"), tap=(f"shaft_block_{blk_i}",))
    # X guide pins: flanged printed standoff, two M3 screws from behind, M4 button head screw and trapped nut
    for k, px in enumerate((PIN_L, PIN_R)):
        so = cylz(10.0, WALL, WALL + 3.0, px, PIN_Y).union(cylz(4.0, WALL + 3.0, ZT0 - 0.16, px, PIN_Y)).cut(cylz(2.1, WALL - 1, ZT0, px, PIN_Y))
        reg(f"pin_standoff_{k}", so, "static", C_PRINT)
        nut(f"pin_{k}", (px, PIN_Y, WALL + 1.6), (0, 0, -1), f"pin_standoff_{k}", 4)
        screw(f"pin_{k}", (px, PIN_Y, ZB + 0.2), (0, 0, -1), 24.0, 4, "pan", clear=(f"pin_standoff_{k}",), allow=(f"nut_pin_{k}",))
        for j, dx in enumerate((-7.0, 7.0)):
            nut(f"pinf_{k}{j}", (px + dx, PIN_Y, WALL + 1.4), (0, 0, 1), f"pin_standoff_{k}", 3)
            screw(f"pinf_{k}{j}", (px + dx, PIN_Y, 0.0), (0, 0, 1), 6.0, 3, "csk", clear=("back_plate",), tap=(f"pin_standoff_{k}",), allow=(f"nut_pinf_{k}{j}",))
    # tabs (laser, 2 mm POM) with a spring tongue; cams printed with a D bore, each one turned 60 degrees on the flat
    for i, x in enumerate(XS):
        t = box(x - 22, x + 22, -6, 6, ZT0, ZB).union(box(x - 0.9, x + 0.9, 6.0, 8.5, ZT0, ZB))
        reg(f"tab_{i}", slot_cut(t, x, 0, SL, SLOT_W, 0, ZT0, ZB), "tab", C_LASER)
        cam = cyl_along("x", CAM_R, x - 6, x + 6, CAM_Y, ZAC + E).cut(cyl_along("x", SHAFT_R + 0.05, x - 7, x + 7, CAM_Y, ZAC))
        reg(f"cam_{i}", cam, "cam", C_PRINT)
    # PTFE skid strips on the back plate: the frame is pushed towards the wall by the tab preload and slides on them
    reg("ptfe_strip", box(-258, 270, -41.5, -4.0, WALL, WALL + 0.5).union(box(-258, -254, -4.0, 22.0, WALL, WALL + 0.5)).union(box(262, 270, -4.0, 22.0, WALL, WALL + 0.5)), color="#f2f2f2")

    # ---------------- X drive (left end)
    reg("x_motor", lm.nema17((XF, 8.0, ZAX), (0, 1, 0)), color=C_BUY)
    xm = box(-408, -364, 8.0, XPL0, 3.0, 45.3).cut(cyl_along("y", 11.2, 7, XPL0 + 1, XF, ZAX)).union(box(-408, -364, XPL0, 28.0, 3.0, 6.0))
    reg("x_mount", xm, color=C_PRINT)
    for j, (dx, dz) in enumerate(((-15.5, -15.5), (-15.5, 15.5), (15.5, -15.5), (15.5, 15.5))):
        screw(f"xmotor_{j}", (XF + dx, XPL0, ZAX + dz), (0, -1, 0), 8, 3, "pan", clear=("x_mount",), tap=("x_motor",))
    for j, x in enumerate((-400.0, -372.0)):
        nut(f"xmount_{j}", (x, 18.0, 4.8), (0, 0, 1), "x_mount", 3)
        screw(f"xmount_{j}", (x, 18.0, 0.0), (0, 0, 1), 6.0, 3, "csk", clear=("back_plate",), tap=("x_mount",), allow=(f"nut_xmount_{j}",))
    reg("x_pulley", lm.pulley("y", XPL0, XPL0 + 8, XF, ZAX, bore=2.55), color=C_BUY)
    reg("x_idler", lm.pulley("y", XPL0, XPL0 + 8, XN, ZAX, bore=1.55), color=C_BUY)
    reg("x_idler_sleeve", cyl_along("y", 2.4, XPL0 + 8, 45.0, XN, ZAX).cut(cyl_along("y", 1.55, XPL0 + 7, 46, XN, ZAX)), color=C_BUY)
    reg("x_idler_nut", _hex((XN, XPL0 - 1.3, ZAX), (0, 1, 0), 2.4, 5.5), color="#8d939a")
    screw("xidler", (XN, HY, ZAX), (0, -1, 0), 40.0, 3, "pan", clear=("wall_top", "x_idler_sleeve", "x_idler"), allow=("x_idler_nut",))
    ALLOW["x_idler_nut"] = {"screw_xidler"}
    FAST.append(dict(name="xidlernut", spec="M3 nut"))
    xb = lm.belt_xy(((XF + XN) / 2, ZAX), XN - XF, 0, 0, 6)
    reg("x_belt", shp(xb).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, XPL0 + 7, 0)), color="#222222")

    # ---------------- Y drive: NEMA 17 at the right end turns a cross shaft along the top; a vertical belt at each end of the frame
    reg("y_motor", lm.nema17((YM_FACE, 0.0, ZAX), (1, 0, 0)), color=C_BUY)
    ym = box(YM_FACE, YM_FACE + 2.5, -23, 23, 3.0, 46.0).cut(cyl_along("x", 11.2, YM_FACE - 1, YM_FACE + 3.5, 0.0, ZAX))
    ym = ym.union(box(YM_FACE + 2.5, 333.0, -23, 23, 3.0, 6.0))
    reg("y_mount", ym, color=C_PRINT)
    for j, (dy, dz) in enumerate(((-15.5, -15.5), (-15.5, 15.5), (15.5, -15.5), (15.5, 15.5))):
        screw(f"ymotor_{j}", (YM_FACE + 2.5, dy, ZAX + dz), (-1, 0, 0), 8, 3, "pan", clear=("y_mount",), tap=("y_motor",))
    for j, yy in enumerate((-15.0, 15.0)):
        nut(f"ymount_{j}", (325.0, yy, 4.8), (0, 0, 1), "y_mount", 3)
        screw(f"ymount_{j}", (325.0, yy, 0.0), (0, 0, 1), 6.0, 3, "csk", clear=("back_plate",), tap=("y_mount",), allow=(f"nut_ymount_{j}",))
    reg("y_pulley_m", lm.pulley("x", TP_X[0], TP_X[1], 0.0, ZAX, bore=2.55), color=C_BUY)
    reg("y_pulley_t", lm.pulley("x", TP_X[0], TP_X[1], YS_Y, YS_Z, bore=2.55), color=C_BUY)
    reg("y_belt_t", belt_yz((YS_Y / 2, (ZAX + YS_Z) / 2), math.hypot(YS_Y, YS_Z - ZAX), math.degrees(math.atan2(YS_Z - ZAX, YS_Y)), TP_X[0] + 1, TP_X[1] - 1), color="#222222")
    reg("cross_shaft", cyl_along("x", 2.5, -270.0, 334.0, YS_Y, YS_Z), color="#b9bec4")
    for nm_, (a_, b_) in (("l", LOOP_L), ("r", LOOP_R)):
        reg(f"y_pulley_{nm_}", lm.pulley("x", a_, b_, YS_Y, YS_Z, bore=2.55), color=C_BUY)
        reg(f"y_idler_{nm_}", lm.pulley("x", a_, b_, YB_Y, YS_Z, bore=1.55), color=C_BUY)
        reg(f"y_belt_{nm_}", belt_yz((0.0, YS_Z), YS_Y - YB_Y, 0.0, a_ + 1, b_ - 1), color="#222222")
    for k, xc in enumerate(XS_BEAR):
        blk = box(xc - 7, xc + 7, 28.0, 45.0, 37.0, 53.0).cut(cyl_along("x", 2.7, xc - 8, xc + 8, YS_Y, YS_Z)).cut(cyl_along("x", 5.6, xc - 2.6, xc + 2.6, YS_Y, YS_Z))
        reg(f"xs_block_{k}", blk, color=C_PRINT)
        reg(f"xs_bearing_{k}", cyl_along("x", 5.5, xc - 2.5, xc + 2.5, YS_Y, YS_Z).cut(cyl_along("x", 2.5, xc - 3, xc + 3, YS_Y, YS_Z)), color=C_BUY)
        for j, dx in enumerate((-5.0, 5.0)):
            screw(f"xsb_{k}{j}", (xc + dx, HY, YS_Z), (0, -1, 0), 8.0, 3, "csk", clear=("wall_top",), tap=(f"xs_block_{k}",))
    for nm_, (sx0, sx1), head_x, d_ in (("l", (-246.0, -240.0), -240.0, -1), ("r", (270.0, 276.0), 276.0, -1)):
        reg(f"y_idler_sup_{nm_}", box(sx0, sx1, -45.0, -28.0, 37.0, 53.0), color=C_PRINT)
        nx = -255.2 if nm_ == "l" else 260.8
        reg(f"y_idler_nut_{nm_}", _hex((nx, YB_Y, YS_Z), (1, 0, 0), 2.4, 5.5), color="#8d939a")
        screw(f"yidler_{nm_}", (head_x, YB_Y, YS_Z), (d_, 0, 0), 16.0, 3, "pan", clear=(f"y_idler_sup_{nm_}", f"y_idler_{nm_}"), allow=(f"y_idler_nut_{nm_}",))
        ALLOW[f"y_idler_nut_{nm_}"] = {f"screw_yidler_{nm_}"}
        FAST.append(dict(name=f"yidlernut{nm_}", spec="M3 nut"))
        for j, zz in enumerate((40.0, 50.0)):
            screw(f"yidlersup_{nm_}{j}", ((sx0 + sx1) / 2, -HY, zz), (0, 1, 0), 10.0, 3, "csk", clear=("wall_bottom",), tap=(f"y_idler_sup_{nm_}",))

    # ---------------- limit switches
    reg("x_limit_switch", box(240.5, 246.5, -27, -21, 31.0, 35.0), color=C_BUY)
    reg("x_limit_post", box(241.5, 245.5, -45, -27, 29.0, 35.0), color=C_PRINT)
    screw("xlimit_post", (243.5, -48.0, 32.0), (0, 1, 0), 10.0, 3, "csk", clear=("wall_bottom",), tap=("x_limit_post",))
    screw("xlimit_sw", (243.5, -21.0, 33.0), (0, -1, 0), 8.0, 2, "pan", clear=("x_limit_switch",), tap=("x_limit_post",))
    reg("y_limit_switch", box(225, 231, 29.4, 35.4, 23.5, 28.5), color=C_BUY)        # top: the comb bridge trips it at Y = +13.4
    reg("y_limit_post", box(226, 230, 35.4, 45.0, 23.5, 28.5), color=C_PRINT)
    screw("ylimit_post", (228.0, HY, 26.0), (0, -1, 0), 10.0, 3, "csk", clear=("wall_top",), tap=("y_limit_post",))

    # ---------------- controller on a perfboard at the right end, on 5 mm standoffs
    reg("pcb", box(340, 406, -30, 30, 8.0, 9.6), color="#2a6b3a")
    for k, (x, y) in enumerate(((343, -27), (343, 27), (403, -27), (403, 27))):
        reg(f"pcb_standoff_{k}", cylz(2.8, WALL, 8.0, x, y), color=C_BUY)
        screw(f"pcbtop_{k}", (x, y, 9.6), (0, 0, -1), 4.0, 3, "pan", clear=("pcb",), tap=(f"pcb_standoff_{k}",))
        screw(f"pcbback_{k}", (x, y, 0.0), (0, 0, 1), 5.0, 3, "csk", clear=("back_plate",), tap=(f"pcb_standoff_{k}",))
    reg("pico", box(347, 398, 2, 23, 9.6, 14.6), color="#1f4f2b")
    for k in range(3):
        reg(f"driver_{k}", box(348 + k * 15, 361 + k * 15, -24, -9, 9.6, 19.6), color="#7b2d8e")
    reg("buck_converter", box(393, 405, -22, -8, 9.6, 17.0), color="#b03030")
    reg("dc_jack", box(402, XR, -7, 7, 12, 24), color=C_BUY)


# ------------------------------------------------------------------ pose
def tab_dy(ph):
    """Height of the tab centre (frame coordinates) for cam angle ph: the tab's lower face rests on the cam circle."""
    return CAM_Y + _tab_raw(ph)


def add_mirrors(tp, X, Y):
    """Seven mirrors: carrier with a hub for the rod, glass, stem (2 mm rod, 10 mm pivot ball, 6 mm tip ball)."""
    info = dict(X=X, Y=Y, D=X, normals=[], pivots=[], tips=tp)
    out = []
    for i, x in enumerate(XS):
        nx, ny = (x - tp[i][0]) / L, -tp[i][1] / L
        n = (nx, ny, math.sqrt(1 - nx * nx - ny * ny))
        P_ = (x, 0.0, ZT + L * n[2])
        T_ = (tp[i][0], tp[i][1], ZT)
        info["normals"].append(n); info["pivots"].append(P_)
        pa, ya = lm.pitch_yaw(n)
        loc = lambda w: lm.rot_pitch_yaw(shp(w), pa, ya).translate(cq.Vector(*P_))
        back = tuple(P_[k] + n[k] * (lm.B_OFF + 2.0) for k in range(3))
        stem = lm.between(T_, back, lm.STEM_R).union(sph(lm.PIV_R, *P_)).union(sph(lm.TIP_R, *T_))
        out.append((f"stem_{i}", shp(stem), "#8d939a"))
        carrier = cylz(lm.CARR_R, lm.B_OFF, lm.B_OFF + lm.CARR_T).union(cylz(4.0, lm.B_OFF - 6.0, lm.B_OFF))
        out.append((f"carrier_{i}", loc(carrier), C_CARR))
        out.append((f"glass_{i}", loc(cylz(lm.MIR_R, lm.B_OFF + lm.CARR_T, lm.B_OFF + lm.CARR_T + lm.GLASS_T)), C_GLASS))
        grub = cq.Workplane("XY").add(cq.Solid.makeCylinder(1.0, 3.0, cq.Vector(1.0, 0, lm.B_OFF - 3.0), cq.Vector(1, 0, 0)))
        out.append((f"carrier_grub_{i}", loc(grub), "#555555"))      # M2 grub: the carrier comes off the rod, so the front plate can be lifted
    return info, out


def pose(n_c, theta, X=None, Y=None):
    """n_c: common mirror normal (unit). theta: camshaft angle (deg). X, Y override the pan and tilt offsets (limit tests)."""
    if not PARTS:
        build_neutral()
    X0, Y0 = -L * n_c[0], -L * n_c[1]
    X = X0 if X is None else X
    Y = Y0 if Y is None else Y
    ph = [math.radians(theta) + i * DPH for i in range(N)]
    out = []
    for name, d in PARTS.items():
        g, s = d["group"], d["shape"]
        if g == "pan":
            s = s.translate(cq.Vector(X, 0, 0))
        elif g == "tilt":
            s = s.translate(cq.Vector(0, Y, 0))
        elif g == "tab":
            i = int(name.split("_")[1]); s = s.translate(cq.Vector(0, Y + tab_dy(ph[i]), 0))
        elif g == "cam":
            i = int(name.split("_")[1]); s = s.translate(cq.Vector(0, Y + E * math.sin(ph[i]), E * (math.cos(ph[i]) - 1)))
        out.append((name, s, d["color"]))
    for i in range(N):                               # springs push each tab down onto its cam
        y0 = Y + tab_dy(ph[i]) + 6.0
        y1 = Y + 13.0
        sp = lm.between((XS[i], y0, ZT0 + 1.0), (XS[i], y1, ZT0 + 1.0), 2.3)       # 4.6 OD x 0.6 wire, sits over the two tongues
        sp = sp.cut(lm.between((XS[i], y0 - 1, ZT0 + 1.0), (XS[i], y1 + 1, ZT0 + 1.0), 1.7))
        out.append((f"spring_{i}", shp(sp), "#c9a227"))
    tp = [(x + X, Y + tab_dy(ph[i])) for i, x in enumerate(XS)]
    info, mp = add_mirrors(tp, X, Y)
    out.extend(mp)
    return out, info


# ------------------------------------------------------------------ checks
JOINED = [   # pairs that are screwed, glued, clamped or deliberately touching (matched by name prefix)
    ("tilt_backbone", "cam_end"), ("tilt_backbone", "tilt_bracket"), ("tilt_backbone", "shaft_block"), ("shaft_block", "retainer"),
    ("tab_comb", "retainer"), ("tab_comb", "cam_end"), ("tab_comb", "tilt_bracket"), ("camshaft", "shaft_coupler"), ("camshaft", "cam_"),
    ("cam_motor", "shaft_coupler"), ("cam_motor", "cam_end"), ("shaft_collar", "camshaft"), ("shaft_block", "camshaft"),
    ("pan_bar_lip", "pan_bar_relief"), ("pan_bar_lip", "x_belt_clamp"), ("pan_bar_relief", "x_belt_clamp"),
    ("x_belt_clamp", "x_belt"), ("x_belt_clamp_cap", "x_belt"), ("x_belt", "x_pulley"), ("x_belt", "x_idler"), ("x_motor", "x_pulley"), ("x_motor", "x_mount"),
    ("y_motor", "y_mount"), ("y_motor", "y_pulley_m"), ("y_belt_t", "y_pulley_t"), ("y_belt_t", "y_pulley_m"),
    ("y_belt_l", "y_pulley_l"), ("y_belt_l", "y_idler_l"), ("y_belt_r", "y_pulley_r"), ("y_belt_r", "y_idler_r"),
    ("cross_shaft", "y_pulley"), ("cross_shaft", "xs_bearing"), ("cross_shaft", "xs_block"), ("xs_bearing", "xs_block"),
    ("y_belt_l", "cam_end"), ("y_belt_l", "y_clamp_cap_l"), ("y_belt_r", "tilt_bracket"), ("y_belt_r", "y_clamp_cap_r"),
    ("pcb", "pcb_standoff"), ("pcb", "pico"), ("pcb", "driver"), ("pcb", "buck"), ("back_plate", "pcb_standoff"), ("end_right", "dc_jack"),
    ("spring_", "tab_"), ("spring_", "tab_comb"), ("ptfe_strip", "tilt_backbone"), ("ptfe_strip", "cam_end"), ("ptfe_strip", "tilt_bracket"), ("ptfe_strip", "back_plate"),
]
ENC = ("back_plate", "wall_top", "wall_bottom", "end_left", "end_right", "front_plate")


def base(n):
    m = re.match(r"^(.*)_(\d+)$", n)
    if m and m.group(1) in ("tab", "cam", "shaft_block", "retainer", "pcb_standoff", "driver", "pin_standoff", "front_plate", "stem", "carrier", "glass",
                            "spring", "xs_block", "xs_bearing", "carrier_grub"):
        return m.group(1)
    for pre in ("pan_rail", "corner_post", "y_idler_sup", "y_clamp_cap", "y_pulley", "y_idler", "y_belt"):
        if n.startswith(pre):
            return pre
    return n


def joined(a, b):
    for n, o in ((a, b), (b, a)):
        if n in ALLOW and o in ALLOW[n]:
            return True
    ma, mb = re.match(r"^(stem|carrier|carrier_grub|glass)_(\d+)$", a), re.match(r"^(stem|carrier|carrier_grub|glass)_(\d+)$", b)
    if ma and mb and ma.group(2) == mb.group(2):
        return True
    for u, v in JOINED:
        if (a.startswith(u) and b.startswith(v)) or (a.startswith(v) and b.startswith(u)):
            return True
    return False


def same_mirror(a, b):
    ia = a.rsplit("_", 1)[-1] if a.split("_")[0] in ("stem", "carrier", "glass", "tab", "cam", "spring") else None
    ib = b.rsplit("_", 1)[-1] if b.split("_")[0] in ("stem", "carrier", "glass", "tab", "cam", "spring") else None
    return ia is not None and ia == ib


def clashes(parts, tol=0.5):
    out = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _ in parts]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            a, b = bbs[i], bbs[j]
            if (a[2].xmax < b[2].xmin or b[2].xmax < a[2].xmin or a[2].ymax < b[2].ymin or b[2].ymax < a[2].ymin
                    or a[2].zmax < b[2].zmin or b[2].zmax < a[2].zmin):
                continue
            if joined(a[0], b[0]):
                continue
            # a mirror's own stem passes through its tab slot and pan-bar slot, the pivot ball sits in the front plate: these are touches, so test them too
            try:
                v = a[1].intersect(b[1]).Volume()
            except Exception:
                v = -1
            if v > tol:
                out.append((a[0], b[0], round(v, 2)))
    return out


def gap(a, b):
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value()


def run_checks():
    n0 = (0, 0, 1)
    print("== clash sweep (all parts, 50 poses) ==")
    cases = [(n0, 0.0, None, None)]
    for th in (0, 60, 120, 180, 240, 300):
        cases.append((n0, th, None, None))
    for phi in range(0, 360, 45):
        n_c = lm.unit(tuple(lm.sun_dir(25 * 2, phi)[k] + (0, 0, 1)[k] for k in range(3)))   # sun 50 deg off axis -> cone 25 deg
        for th in (phi * 2 % 360, (phi * 2 + 150) % 360):
            cases.append((n_c, float(th), None, None))
    # travel extremes: pan and tilt at their stops, with the cam at its worst angles
    c9 = TRAV / math.sqrt(2)
    for X, Y in ((c9, c9), (-c9, c9), (c9, -c9), (-c9, -c9), (TRAV, 0.0), (-TRAV, 0.0), (0.0, TRAV), (0.0, -TRAV), (14.3, 0.0), (0.0, 13.4)):
        for th in (0.0, 90.0):
            cases.append((n0, th, X, Y))
    bad = 0
    agg = {}
    for n_c, th, X, Y in cases:
        try:
            parts, info = pose(n_c, th, X, Y)
        except ValueError as e:
            print("  skipped (tilt too large):", e)
            continue
        c = clashes(parts)
        tilt = max(math.degrees(math.acos(n[2])) for n in info["normals"])
        if c:
            bad += 1
            for a_, b_, v_ in c:
                k_ = (a_, b_)
                agg[k_] = (max(v_, agg.get(k_, (0, 0))[0]), agg.get(k_, (0, 0))[1] + 1)
    for (a_, b_), (v_, n_) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
        print(f"  CLASH {a_} / {b_}: up to {v_} mm3 in {n_} poses")
    print(f"  poses {len(cases)}, with clashes: {bad}")
    return bad


def sun_view():
    print("== sun view (rays from 15 points per mirror) ==")
    wrapper = []
    for alpha in (25, 50, 65):
        tot = dict(enc_in=0, enc_out=0, mir_in=0, mir_out=0, n=0)
        for phi in range(0, 360, 45):
            s = lm.sun_dir(alpha, phi)
            n_c = lm.unit(tuple(s[k] + (0, 0, 1)[k] for k in range(3)))
            for th in (0.0, 120.0):
                try:
                    parts, info = pose(n_c, th)
                except ValueError:
                    continue
                r = lm.ray_check(parts, info, s)
                for k in tot:
                    tot[k] += r[k]
        f = lambda k: 100.0 * tot[k] / max(1, tot["n"])
        print(f"  sun {alpha:2d} deg: enclosure blocks in {f('enc_in'):4.1f}% out {f('enc_out'):4.1f}%   other mirrors in {f('mir_in'):4.1f}% out {f('mir_out'):4.1f}%   ({tot['n']} rays)")


def near_scan(parts, thr=0.6):
    """All pairs of loose parts whose boxes are within thr mm: exact distance. Returns sorted (distance, a, b)."""
    out = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _ in parts]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            a, b = bbs[i], bbs[j]
            if (a[2].xmax + thr < b[2].xmin or b[2].xmax + thr < a[2].xmin or a[2].ymax + thr < b[2].ymin or b[2].ymax + thr < a[2].ymin
                    or a[2].zmax + thr < b[2].zmin or b[2].zmax + thr < a[2].zmin):
                continue
            if joined(a[0], b[0]) or same_mirror(a[0], b[0]):
                continue
            d = gap(a[1], b[1])
            if d < thr:
                out.append((round(d, 2), a[0], b[0]))
    return sorted(out)


def tight_spots():
    print("== near-contact scan: every pair of loose parts closer than 0.6 mm (neutral and four corner poses, cam 0 and 90) ==")
    seen = {}
    for X, Y in ((0.0, 0.0), (TRAV * 0.7, TRAV * 0.7), (-TRAV * 0.7, TRAV * 0.7), (TRAV * 0.7, -TRAV * 0.7), (-TRAV * 0.7, -TRAV * 0.7)):
        for th in (0.0, 90.0):
            parts, _ = pose((0, 0, 1), th, X, Y)
            for d, a, b in near_scan(parts):
                key = (a.rstrip("0123456789_") or a, b.rstrip("0123456789_") or b)
                if key not in seen or d < seen[key][0]:
                    seen[key] = (d, a, b)
    zero = [k for k, v in seen.items() if v[0] == 0.0]
    print(f"  {len(zero)} pairs touch exactly (stacked plates, glued parts, screws in their holes)")
    for key, (d, a, b) in sorted(seen.items(), key=lambda kv: kv[1][0]):
        if d > 0.0:
            print(f"  {d:4.2f} mm  {a} / {b}")


def gaps():
    print("== minimum gaps between neighbours, neutral pose and worst poses ==")
    pairs = [("pan_bar_lip", "pan_rail_top_a"), ("pan_bar_lip", "pan_rail_bottom_a"), ("pan_bar_relief", "pan_rail_top_a"), ("cam_motor", "x_idler"),
             ("cam_motor", "pan_bar_lip"), ("tab_comb", "pan_bar_lip"), ("camshaft", "pan_bar_lip"), ("shaft_block_0", "pan_rail_bottom_a"),
             ("cam_3", "pan_bar_lip"), ("cam_3", "stem_3"), ("tilt_bracket", "pan_bar_lip"), ("tilt_bracket", "y_mount"), ("y_motor", "wall_bottom"),
             ("x_motor", "end_left"), ("x_belt_clamp", "cam_motor"), ("tab_comb", "guide_pin_0"), ("x_limit_post", "shaft_block_6"), ("spring_3", "stem_3")]
    for X, Y, label in ((0.0, 0.0, "neutral"), (TRAV, TRAV, "X+ Y+"), (-TRAV, -TRAV, "X- Y-"), (TRAV, -TRAV, "X+ Y-"), (-TRAV, TRAV, "X- Y+")):
        parts, info = pose((0, 0, 1), 0.0, X, Y)
        d = {n: s for n, s, _ in parts}
        row = []
        for a, b in pairs:
            if a in d and b in d:
                row.append((round(gap(d[a], d[b]), 2), a, b))
        row.sort()
        print(f"  [{label}] tightest: " + ", ".join(f"{g}mm {a}/{b}" for g, a, b in row[:5]))


def cam_checks():
    print("== numbers ==")
    wall = CAM_R - E - SHAFT_R
    zmax = ZAC + E + CAM_R
    print(f"  cam disc r {CAM_R}, 5 mm D shaft, throw {E}: minimum wall {wall:.2f} mm; highest cam point z {zmax:.2f}, pan bar underside z {ZA:.2f} (clearance {ZA - zmax:.2f})")
    ys = [tab_dy(math.radians(k)) for k in range(360)]
    print(f"  tab motion {min(ys):+.2f} to {max(ys):+.2f} mm (nominal +/-{E:.2f}); cam top to retainer {(-4.0) - (CAM_Y + E + CAM_R):.2f} mm")
    # tilt frame: 20 x 10 aluminium bar, 10 mm deep in Y; supported in Y by a belt at each end
    E_al, I = 70000.0, 20.0 * 10.0 ** 3 / 12.0
    L_ = BAR_X[1] - BAR_X[0]
    w = (0.20 + 0.28) * 9.81 / L_            # frame parts about 200 g plus the bar about 280 g, N/mm
    sag = 5 * w * L_ ** 4 / (384 * E_al * I)
    print(f"  tilt frame: bar EI {E_al * I:.2e} N mm2, self-weight sag between the two belts {sag:.3f} mm (constant, calibrates out)")
    acr = 3000.0 * (2.0 * 3.0 ** 3 / 12 + 11.5 * 4.0 ** 3 / 12)
    print(f"  (the old acrylic frame: EI {acr:.2e}, same load {5 * w * L_ ** 4 / (384 * acr):.1f} mm, and with one belt it was a cantilever)")
    load = (0.48 + 0.06) * 9.81 + 0.15 * 3.5          # frame weight + PTFE friction from the tab preload
    print(f"  Y load {load:.1f} N at 6.37 mm pulley radius: {load * 6.37 / 10:.1f} N cm on the Y motor (42 x 40, 40 N cm holding)")
    xl = 2 * (XN - XF) + math.pi * 12.73
    yl = 2 * (YS_Y - YB_Y) + math.pi * 12.73
    tl = 2 * math.hypot(YS_Y, YS_Z - ZAX) + math.pi * 12.73
    print(f"  belts: X {xl:.0f} mm, Y left and right {yl:.0f} mm each, transfer {tl:.0f} mm (cut GT2, joined in the clamps)")
    print(f"  mirror torque on the tip: {0.83 * 0.030 * 9.81:.2f} N; tab spring about 1.2 N; ball preload about 0.5 N per tab from the flexure pads")
    a70 = 70e-6 * 210 * 30
    print(f"  thermal, end mirror at 30 K: steel lip vs acrylic front {(70e-6 - 12e-6) * 210 * 30:.2f} mm, PET lip vs acrylic {(70e-6 - 60e-6) * 210 * 30:.2f} mm")


# ------------------------------------------------------------------ BOM data
PRINT_BED = (256, 256, 256)
INFO = {   # base -> (process, material, description, note)
    "back_plate": ("laser", "3 mm acrylic (light colour) or birch ply", "Back plate 824 x 96", "6 wall-fixing holes"),
    "wall_top": ("laser", "3 mm acrylic or birch ply", "Top wall 824 x 51", "holes for idler bolt, rail, bearing-block and switch-post screws"),
    "wall_bottom": ("laser", "3 mm acrylic or birch ply", "Bottom wall 824 x 51", "holes for rail, idler-support and switch-post screws"),
    "end_left": ("laser", "3 mm acrylic or birch ply", "End wall 90 x 51", ""),
    "end_right": ("laser", "3 mm acrylic or birch ply", "End wall 90 x 51", "11 mm hole for the DC jack"),
    "front_plate": ("laser", "4 mm acrylic", "Front plate layer 824 x 96, 7 x 10.1 mm holes", "2 layers cemented, 8 mm; 10 countersunk screws"),
    "pan_bar_lip": ("laser", "0.5 mm PET (Mylar stencil sheet)", "Pan bar lip with 4.4 mm slots", "PET expands like acrylic; cement to the relief layer"),
    "pan_bar_relief": ("laser", "1.5 mm acrylic", "Pan bar relief layer with 9 mm slots", "588 x 60 incl. tail"),
    "tab_comb": ("laser", "2 mm acrylic", "Tab comb: guides the tabs, spring tongues, pin slots", "fixed at the left, slides in the right bracket"),
    "tab": ("laser", "2 mm POM (acetal)", "Tab with 4.4 mm slot and spring tongue", "ball runs on the slot edges"),
    "x_belt_clamp": ("print", "PETG", "X belt clamp block with riser", ""),
    "x_belt_clamp_cap": ("print", "PETG", "X belt clamp cap", ""),
    "pan_rail": ("print", "PETG", "Pan bar rail (web and cap), 215 mm", "PTFE tape on the cap underside"),
    "cam_end": ("print", "PETG", "Tilt-frame left end block: cam motor, backbone end, comb tab, left Y belt jaw", ""),
    "tilt_bracket": ("print", "PETG", "Tilt-frame right bracket: backbone end, comb pocket, right Y belt jaw", ""),
    "y_clamp_cap": ("print", "PETG", "Y belt clamp cap", "2 M2 through the belt"),
    "shaft_block": ("print", "PETG", "Camshaft block with retainer support (first one is a support only)", "2 M3 from under the backbone"),
    "retainer": ("print", "PETG", "Tab retainer with 2 flexure pads", "pads printed 0.3 mm proud; cemented under the comb, 2 M2"),
    "cam": ("print", "PETG or nylon", "Eccentric cam 10 mm, 5 mm D bore, 1 mm throw", "print cam i with the bore turned i x 60 deg"),
    "corner_post": ("print", "PETG", "Front plate post", "cemented to back plate and wall"),
    "pin_standoff": ("print", "PETG", "Guide pin standoff with 20 mm flange", "M4 nut trapped under it"),
    "x_mount": ("print", "PETG", "X motor mount (plate and foot)", ""),
    "y_mount": ("print", "PETG", "Y motor mount (plate and foot)", ""),
    "xs_block": ("print", "PETG", "Cross-shaft bearing block (685ZZ)", "2 M3 through the top wall"),
    "y_idler_sup": ("print", "PETG", "Y bottom idler support", "2 M3 through the bottom wall"),
    "x_limit_post": ("print", "PETG", "X limit switch post", ""),
    "y_limit_post": ("print", "PETG", "Y limit switch post (top)", "switch cemented on"),
    "tilt_backbone": ("metal", "aluminium flat bar 20 x 10", "Tilt-frame backbone 516 mm", "M3 tapped: 2 in each end, 2 per block from below (clearance)"),
    "camshaft": ("metal", "5 mm D shaft (or 5 mm silver steel with a filed flat)", "Camshaft 492 mm", ""),
    "cross_shaft": ("metal", "5 mm silver steel", "Y cross shaft 604 mm", "floats axially in the bearings"),
    "ptfe_strip": ("buy", "0.5 mm adhesive PTFE sheet", "Skid strip under the tilt frame", ""),
}


def part_summary():
    """Group the parts for the BOM: returns rows (base, qty, bbox dims)."""
    if not PARTS:
        build_neutral()
    rows = {}
    for n, d in PARTS.items():
        b = base(n)
        bb = d["shape"].BoundingBox()
        dims = tuple(round(v, 1) for v in sorted((bb.xlen, bb.ylen, bb.zlen), reverse=True))
        rows.setdefault(b, []).append((n, dims))
    return rows


BUY = [   # purchased items: (qty, item, use, est GBP total, note)
    (1, "NEMA 17 stepper 42 x 34 mm, 5 mm D shaft", "X pan", 11, "Pi Hut about 11 GBP ex VAT (seen earlier)"),
    (1, "NEMA 17 stepper 42 x 40 mm, 1.68 A, about 40 N cm", "Y tilt (lifts a 0.5 kg frame)", 12, "Pi Hut about 12 GBP ex VAT (seen earlier)"),
    (1, "28BYJ-48 5 V geared stepper", "camshaft (slow, light, on the moving frame)", 3, "cut the red-wire trace to run it bipolar from a TMC2209, or use its ULN2003 board"),
    (3, "TMC2209 stepper driver module", "silent (stealthChop)", 15, "3-7 GBP each, many UK sellers"),
    (1, "Raspberry Pi Pico (RP2040)", "controller", 5, ""),
    (1, "RTC module DS3231", "keeps time without WiFi", 4, "or a GPS module"),
    (1, "12 V 2 A DC adapter + panel DC jack 5.5/2.1", "UK plug", 10, ""),
    (1, "Buck converter 12 V to 5 V", "Pico, RTC, 28BYJ", 3, ""),
    (5, "GT2 20T pulley, 6 mm belt, 5 mm bore", "X motor, Y motor, cross shaft x 3", 9, "packs of 5 about 8.6 GBP (Desertcart UK)"),
    (3, "GT2 20T idler with bearing, 3 mm bore", "X idler, Y bottom idlers", 6, ""),
    (1, "GT2 6 mm belt, 2 m", "X 160, Y 2 x 200, transfer 130 mm", 4, "Pi Hut 5 m reel about 9-10 GBP"),
    (5, "685ZZ bearing 5 x 11 x 5", "cross shaft", 4, ""),
    (1, "Rigid coupler 5 to 5 mm, 10 x 20", "28BYJ shaft to camshaft", 3, ""),
    (1, "Shaft collar 5 mm", "camshaft right end", 1, ""),
    (1, "Aluminium flat bar 20 x 10, 600 mm", "tilt backbone (cut 516)", 6, "drill and tap M3"),
    (1, "5 mm silver steel 1 m (or D shaft)", "camshaft 492 + cross shaft 604 (2 lengths)", 6, ""),
    (1, "PET (Mylar) sheet 0.5 mm", "pan bar lip", 4, "stencil sheet, laser cuts"),
    (1, "Adhesive PTFE sheet 0.5 mm + PTFE tape", "frame skids, rail caps", 8, ""),
    (7, "Mirror disc 50 mm round, 3 mm glass", "mirrors", 14, "acrylic mirror for a trial"),
    (7, "Steel ball 10 mm, drilled 2 mm through", "pivot ball (fix on the rod with a 30 mm jig)", 6, ""),
    (7, "Steel ball 6 mm", "tip ball, epoxied to the rod end", 3, ""),
    (7, "Stem rod 2 mm x 52 mm, silver steel", "stem", 4, ""),
    (7, "Compression spring 4.6 OD, 0.6 wire, 10 mm free, about 0.4 N/mm", "tab onto cam, about 1.2 N", 4, "slides over the tab and comb tongues"),
    (2, "Micro limit switch with lever", "X and Y home", 3, ""),
    (1, "Brass tube 5 mm OD, 3.2 mm ID", "X idler sleeve (26.5 mm)", 2, ""),
    (1, "Fasteners in the table below", "counted from the model", 15, "stainless"),
    (1, "Grub screws M3 x 4 (about 12), M2 x 3 (7)", "coupler, collar, pulleys, carrier hubs (M2)", 3, "pulley and coupler grubs not drawn"),
    (1, "Acrylic cement and thin CA glue, epoxy", "enclosure, posts, comb/retainer, glass, balls", 12, ""),
    (1, "Wall fixings", "6 x 4 mm screws and plugs", 3, ""),
    (1, "Cable, connectors, cable chain or loop", "motor cables; the cam motor rides on the frame", 8, ""),
]


def write_bom(path):
    rows = part_summary()
    order = {"laser": 0, "print": 1, "buy": 2}
    lines = []
    meta = lambda b: INFO.get(b)
    out = ["# Wave version (full detail): parts split and bill of materials", "",
           "Generated by `python3 cad/src/line_wave_full.py --bom` from the model. Prices are rough UK estimates, ex-shipping, unchecked except where a note says so.", ""]
    for title, proc in (("Laser cut", "laser"), ("3D printed", "print"), ("Metal stock (cut, drill, tap)", "metal")):
        out += [f"## {title}", "", "| Qty | Part | Material | Size (mm, bounding box) | Note |", "|---|---|---|---|---|"]
        for b, inst in rows.items():
            m = meta(b)
            if not m or m[0] != proc:
                continue
            dims = " x ".join(f"{v:g}" for v in inst[0][1])
            out.append(f"| {len(inst)} | {m[2]} | {m[1]} | {dims} | {m[3]} |")
        if proc == "print":
            out.append("| 7 | Mirror carrier 46 mm disc with 8 mm hub, M2 grub | PETG or ASA (PLA softens in sun) | 46 x 46 x 10 | glass cemented on |")
        out.append("")
    out += ["## Purchased (not individually modelled, or counted here)", "", "| Qty | Item | Use | Est. GBP | Note |", "|---|---|---|---|---|"]
    tot = 0
    for q, item, use, price, note in BUY:
        tot += price
        out.append(f"| {q} | {item} | {use} | {price} | {note} |")
    out += ["", f"Purchased total about {tot} GBP (estimate).", ""]
    from collections import Counter
    c = Counter(f["spec"] for f in FAST)
    out += ["## Fasteners counted from the model", "", "| Qty | Fastener |", "|---|---|"]
    for spec, q in sorted(c.items()):
        out.append(f"| {q} | {spec} |")
    out += ["", "Comb tabs sit in pockets in the printed end block and bracket (the right pocket is long so the acrylic comb can grow). Enclosure joints are butt joints with acrylic cement plus the corner posts; the front plate comes off with its 10 countersunk screws once the 7 carriers are slid off their rods.", ""]
    path.write_text("\n".join(out))
    print("Wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--step", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--bom", action="store_true")
    ap.add_argument("--sun", action="store_true", help="include the slow sun-view ray check with --check")
    a = ap.parse_args()
    build_neutral()
    if a.bom:
        write_bom(lm.CAD.parent / "bom" / "archive" / "line-mirrors" / "line-mirrors-wave-bom.md")
        return
    if a.sun and not a.check:
        sun_view()
        return
    if a.check:
        run_checks(); cam_checks(); tight_spots()
        if a.sun:
            sun_view()
        return
    s = lm.sun_dir(40, 20)
    n_c = lm.unit(tuple(s[k] + (0, 0, 1)[k] for k in range(3)))
    parts, info = pose(n_c, 60.0)
    if a.step or not a.render:
        OUT.mkdir(parents=True, exist_ok=True)
        lm.save_step(parts, OUT / "line-mirrors-wave-full.step")
    if a.render:
        IMG.mkdir(parents=True, exist_ok=True)
        flat, _ = pose((0, 0, 1), 0.0)
        render_all(flat, parts, info, s)


def render_all(flat, parts, info, s):
    pre = "full"
    fx = 0.0
    lm.render(flat, IMG / f"{pre}-front.png", view=(25, 8, 1500), focal=(0, -10, 40), size=(1800, 700))
    lm.render(parts, IMG / f"{pre}-posed-rays.png", view=(15, 14, 1700), focal=(0, 0, 60), rays=lm.out_rays(info, s), size=(1800, 800))
    hide_front = ("glass", "carrier", "front_plate", "end_left", "end_right", "wall_top", "wall_bottom", "screw_front", "screw_rail", "screw_xsb", "screw_yidlersup", "screw_ylimit", "screw_xlimit_post")
    lm.render(parts, IMG / f"{pre}-mechanism.png", view=(6, 40, 1000), focal=(0, -8, 24), hide=hide_front, size=(1900, 800))
    lm.render(parts, IMG / f"{pre}-left-end.png", view=(22, 30, 360), focal=(-320, 0, 24), hide=hide_front, size=(1600, 950))
    lm.render(parts, IMG / f"{pre}-right-end.png", view=(-28, 30, 330), focal=(300, 0, 24), hide=hide_front, size=(1600, 950))
    lm.render(parts, IMG / f"{pre}-row-inside.png", view=(8, 40, 520), focal=(-100, 0, 24), hide=hide_front + ("pan_bar", "pan_rail", "screw_lip", "nut_lip"), size=(1800, 900))
    lm.render(parts, IMG / f"{pre}-tab-detail.png", view=(25, 35, 170), focal=(-140, 0, 25), hide=hide_front + ("pan_bar", "pan_rail", "screw_lip", "nut_lip", "cross_shaft", "xs_", "y_"), size=(1600, 1000))
    lm.render(parts, IMG / f"{pre}-tilt-frame.png", view=(10, 30, 1000), focal=(0, -8, 20), hide=hide_front + ("pan_bar", "pan_rail", "screw_lip", "nut_lip", "back_plate", "ptfe", "corner_post", "pin_", "screw_pin", "nut_pin", "x_", "screw_x", "nut_x", "pcb", "pico", "driver", "buck", "dc_jack", "screw_pcb", "stem", "y_limit", "screw_tail", "screw_cap"), size=(1900, 800))
    lm.render(parts, IMG / f"{pre}-section.png", view=(90, 4, 330), focal=(0, -12, 48), cut_x=0.0, size=(1400, 1000))


if __name__ == "__main__":
    main()
