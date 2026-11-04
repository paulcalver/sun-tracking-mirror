#!/usr/bin/env python3
"""Line of 7 wall mirrors, travelling-wave (camshaft) version, FULL detail model (CadQuery). Concept model, nothing built.

Builds on line_mirrors.py (same mirror unit, same tip joint, same NEMA 17 belt drives) and adds everything that model left out:
the enclosure as separate laser-cut plates, the pan-bar guide rails, the tilt-frame comb (tab guide), guide pins, a Z-offset camshaft
with proper eccentric cams, shaft supports, springs, couplers, motor mounts, belt clamps, limit switches and the controller.
Every part carries a process (3D print / laser cut / buy) and a material; `--bom` writes the bill of materials from the model.

Frame (mm): X along the row (right), Y up, Z out of the wall, origin on the wall at the middle of the row.
Strip: 824 x 96 x 62. The mirror row is centred, so the strip ends are the same distance (177 mm) from the outer mirror edges.

Usage (repo root): python3 cad/src/line_wave_full.py [--check] [--render] [--bom] [--step]
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
CAM_R, SHAFT_R = 4.5, 2.0                    # cam disc radius, camshaft radius (4 mm)
CAM_Y = -(6.0 + CAM_R - 0.11)                # tab bottom edge at y=-6 touches the cam (contact is 0.11 mm below the cam top, see notes)
XF, XN, XPL0 = -386.0, -330.0, 10.5          # X belt: motor pulley x, idler x, pulley start in y
YP, Y_A, Y_B = 300.0, -23.5, 30.5            # Y belt: x of both pulleys, motor pulley y, idler y
PIN_L, PIN_R, PIN_Y = -244.0, 249.0, 13.5    # tilt-frame guide pins (x, y)
BLOCK_X = [XS[i] + 35.0 for i in range(N - 1)] + [242.0]   # camshaft support blocks

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


# ------------------------------------------------------------------ neutral geometry
def build_neutral():
    PARTS.clear()
    # ---------------- enclosure, laser cut (3 mm walls, 2 x 4 mm front)
    bp = box(XL, XR, -HY, HY, 0, WALL)
    for (x, y) in ((-390, 38), (-275, 40), (275, 40), (390, 38), (-390, -38), (390, -38)):
        bp = hole_cut(bp, x, y, 2.5, 0, WALL)
    reg("back_plate", bp, color=C_ENC)
    wt = box(XL, XR, HY - WALL, HY, WALL, ZP0)
    # idler axle slot in the top wall (tension the X belt): slot along x at z = ZAX, 3.2 wide, 10 long
    sl = box(XN - 3.4, XN + 3.4, HY - WALL - 1, HY + 1, ZAX - 1.6, ZAX + 1.6)
    sl = sl.union(cyl_along("y", 1.6, HY - WALL - 1, HY + 1, XN - 3.4, ZAX)).union(cyl_along("y", 1.6, HY - WALL - 1, HY + 1, XN + 3.4, ZAX))
    reg("wall_top", wt.cut(sl), color=C_ENC)
    reg("wall_bottom", box(XL, XR, -HY, -HY + WALL, WALL, ZP0), color=C_ENC)
    reg("end_left", box(XL, XL + WALL, -HY + WALL, HY - WALL, WALL, ZP0), color=C_ENC)
    er = box(XR - WALL, XR, -HY + WALL, HY - WALL, WALL, ZP0)
    reg("end_right", er.cut(cyl_along("x", 5.6, XR - WALL - 1, XR + 1, 0, 18)), color=C_ENC)
    for k, (z0, z1) in enumerate(((ZP0, ZP0 + 4), (ZP0 + 4, ZP1))):
        f = box(XL, XR, -HY, HY, z0, z1)
        for x in XS:
            f = hole_cut(f, x, 0, lm.PIV_R + 0.05, z0, z1)
        reg(f"front_plate_{k + 1}", f, color=C_ENC)

    # ---------------- pan group: bar (2 x 1 mm) with a tail to the X belt, clamp, guide rails
    def bar(z0, z1, w):
        b = box(-226, 226, -PB_Y, PB_Y, z0, z1).union(box(-362, -226, 25.0, 29.6, z0, z1))
        for x in XS:
            b = slot_cut(b, x, 0, SL, w, 90, z0, z1)
        return b
    reg("pan_bar_lip", bar(ZA, ZA + LIP, SLOT_W), "pan", C_LASER)
    reg("pan_bar_relief", bar(ZA + LIP, ZA + 2.0, 9.0), "pan", C_LASER)
    clamp = box(-362, -352, XPL0 + 0.2, XPL0 + 8.0, 29.35, 30.5).union(box(-362, -352, XPL0 + 8.0, 29.6, 29.35, 33.0))
    reg("x_belt_clamp", clamp, "pan", C_PRINT)
    reg("x_belt_clamp_cap", box(-362, -352, XPL0 + 0.2, XPL0 + 8.0, 31.95, 33.5), "pan", C_PRINT)
    for side, (ya, yb) in (("top", (27.0, 45.0)), ("bottom", (-45.0, -27.0))):
        for seg, (xa, xb) in (("a", (-220, 0)), ("b", (0, 220))):
            if side == "top":
                web = box(xa, xb, 30.4, 45.0, ZA - 2.3, ZA + 4.3)
                lo = box(xa, xb, 27.0, 30.4, ZA - 2.3, ZA - 0.3)
                up = box(xa, xb, 27.0, 30.4, ZA + 2.3, ZA + 4.3)
            else:
                web = box(xa, xb, -45.0, -30.4, ZA - 2.3, ZA + 4.3)
                lo = box(xa, xb, -30.4, -27.0, ZA - 2.3, ZA - 0.3)
                up = box(xa, xb, -30.4, -27.0, ZA + 2.3, ZA + 4.3)
            reg(f"pan_rail_{side}_{seg}", web.union(lo).union(up), color=C_PRINT)

    # ---------------- tilt group (frame coordinates, y relative to the tilt frame)
    comb = box(-254, 270, 13, 16, ZT0, ZB)
    edges = [-254.0] + sum(([XS[i] - 22.3, XS[i] + 22.3] for i in range(N)), []) + [270.0]
    for k in range(N + 1):
        a, b = edges[2 * k], edges[2 * k + 1]
        comb = comb.union(box(a, b, -4.0, 13, ZT0, ZB))
    comb = comb.union(box(-254, -234, 13, 31, ZT0, ZB)).union(box(240, 258, 13, 31, ZT0, ZB))
    for px in (PIN_L, PIN_R):
        comb = slot_cut(comb, px, PIN_Y, 2 * 13.4 + 4.2, 4.2, 90, ZT0, ZB)
    reg("tab_comb", comb, "tilt", C_LASER)
    reg("tilt_bar", box(-254, 270, -26, -22, 15, 26.5), "tilt", C_LASER)
    cp = box(-258, -254, -27, 8, 6, 42)
    cp = cp.cut(cyl_along("x", SHAFT_R + 0.1, -259, -253, CAM_Y, ZAX))
    reg("cam_plate", cp, "tilt", C_LASER)
    for k, (dy, dz) in enumerate(((-15.5, -15.5), (-15.5, 15.5), (15.5, -15.5), (15.5, 15.5))):
        reg(f"cam_motor_standoff_{k}", cyl_along("x", 2.5, -284, -258, CAM_Y + dy, ZAX + dz), "tilt", C_BUY)
    reg("cam_motor", lm.nema17((-284, CAM_Y, ZAX), (1, 0, 0), shaft=14.0), "tilt", C_BUY)
    reg("shaft_coupler", cyl_along("x", 5.0, -278, -258.2, CAM_Y, ZAX), "tilt", C_BUY)
    cs = cyl_along("x", SHAFT_R, -270, 246, CAM_Y, ZAX)
    reg("camshaft", cs, "tilt", C_BUY)
    reg("shaft_collar", cyl_along("x", 4.0, 246.1, 250.1, CAM_Y, ZAX).cut(cyl_along("x", SHAFT_R, 245, 251, CAM_Y, ZAX)), "tilt", C_BUY)
    for k, xc in enumerate(BLOCK_X):
        x0, x1 = (xc - 5, xc + 5) if k < N - 1 else (237.0, 246.0)
        blk = box(x0, x1, -22, CAM_Y + 4.9, ZAX - 4.0, ZAX + 4.0).cut(cyl_along("x", SHAFT_R + 0.1, x0 - 1, x1 + 1, CAM_Y, ZAX))
        reg(f"shaft_block_{k}", blk, "tilt", C_PRINT)
    reg("tilt_bracket", box(262, 270, -26, 7, 15, 46.5).union(box(262, 292, 0.5, 6.5, 39.5, 46.5)), "tilt", C_PRINT)
    for k, px in enumerate((PIN_L, PIN_R)):
        reg(f"guide_pin_{k}", cylz(4.0, WALL, ZT0 - 0.16, px, PIN_Y).union(cylz(2.0, ZT0 - 0.2, ZB + 0.2, px, PIN_Y)).union(cylz(3.8, ZB + 0.2, ZB + 2.4, px, PIN_Y)), "static", C_BUY)
    for i in range(N):
        t = box(XS[i] - 22, XS[i] + 22, -6, 6, ZT0, ZB)
        t = slot_cut(t, XS[i], 0, SL, SLOT_W, 0, ZT0, ZB)
        reg(f"tab_{i}", t, "tab", C_LASER)
        cam = cyl_along("x", CAM_R, XS[i] - 6, XS[i] + 6, CAM_Y, ZAX + E).cut(cyl_along("x", SHAFT_R + 0.05, XS[i] - 7, XS[i] + 7, CAM_Y, ZAX))
        reg(f"cam_{i}", cam, "cam", C_PRINT)

    # ---------------- fixed drives, supports and electronics
    reg("x_motor", lm.nema17((XF, 8.0, ZAX), (0, 1, 0)), color=C_BUY)
    reg("x_mount", box(-408, -364, 8.0, XPL0, 3.0, 45.3).cut(cyl_along("y", 11.2, 7, XPL0 + 1, XF, ZAX)).union(box(-408, -364, XPL0, 28.0, 3.0, 6.0)), color=C_PRINT)
    reg("x_pulley", lm.pulley("y", XPL0, XPL0 + 8, XF, ZAX, bore=2.55), color=C_BUY)
    reg("x_idler", lm.pulley("y", XPL0, XPL0 + 8, XN, ZAX).union(cyl_along("y", 1.5, XPL0 + 8, 45.0, XN, ZAX)), color=C_BUY)
    xb = lm.belt_xy(((XF + XN) / 2, ZAX), XN - XF, 0, 0, 6)
    reg("x_belt", shp(xb).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, XPL0 + 7, 0)), color="#222222")
    reg("y_motor", lm.nema17((YP, Y_A, 37.0), (0, 0, 1), shaft=12.0), color=C_BUY)
    ym = box(276.85, 323.15, Y_A - 21.15, Y_A + 21.15, 37.0, 39.0).cut(cylz(11.2, 36, 40, YP, Y_A))
    ym = ym.union(box(276.85, 278.85, Y_A - 21.15, Y_A + 21.15, 3.0, 39.0)).union(box(321.15, 323.15, Y_A - 21.15, Y_A + 21.15, 3.0, 39.0))
    reg("y_mount", ym, color=C_PRINT)
    reg("y_pulley", lm.pulley("z", 39, 47, YP, Y_A, bore=2.55), color=C_BUY)
    reg("y_idler", lm.pulley("z", 39, 47, YP, Y_B).union(cyl_along("z", 1.5, 3, 39, YP, Y_B)), color=C_BUY)
    reg("y_belt", lm.belt_xy((YP, (Y_A + Y_B) / 2), Y_B - Y_A, 90, 40, 46), color="#222222")
    reg("x_limit_switch", box(240.5, 246.5, -27, -21, 31.0, 35.0), color=C_BUY)
    reg("x_limit_post", box(241.5, 245.5, -45, -27, 28.6, 35.0), color=C_PRINT)
    reg("y_limit_switch", box(-155, -149, -45, -39.2, 16, 22), color=C_BUY)
    # controller at the right end: Pico board, three TMC2209 drivers, RTC, buck converter on a perfboard
    reg("pcb", box(326, 406, -30, 30, 6.0, 7.6), color="#2a6b3a")
    for k, (x, y) in enumerate(((332, -26), (332, 26), (404, -26), (404, 26))):
        reg(f"pcb_standoff_{k}", cylz(2.5, WALL, 6.0, x, y), color=C_BUY)
    reg("pico", box(330, 381, -10.5, 10.5, 7.6, 12.6), color="#1f4f2b")
    for k in range(3):
        reg(f"driver_{k}", box(386, 400, -26 + k * 17, -26 + k * 17 + 15, 7.6, 17.6), color="#7b2d8e")
    reg("buck_converter", box(334, 360, 14, 28, 7.6, 15.0), color="#b03030")
    reg("dc_jack", box(402, XR, -7, 7, 12, 24), color=C_BUY)


# ------------------------------------------------------------------ pose
def tab_dy(ph):
    """Height of the tab centre (frame coordinates) for cam angle ph: the tab's lower face rests on the cam circle."""
    zc = ZAX + E * math.cos(ph)
    dz = max(0.0, ZT0 - zc)
    return CAM_Y + E * math.sin(ph) + math.sqrt(CAM_R ** 2 - dz ** 2) + 6.0


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
        sp = lm.between((XS[i], y0, ZT0 + 1.0), (XS[i], y1, ZT0 + 1.0), 2.4)
        sp = sp.cut(lm.between((XS[i], y0 - 1, ZT0 + 1.0), (XS[i], y1 + 1, ZT0 + 1.0), 1.8))
        out.append((f"spring_{i}", shp(sp), "#c9a227"))
    tp = [(x + X, Y + tab_dy(ph[i])) for i, x in enumerate(XS)]
    tmp = []
    info = lm.add_mirrors(tmp, tp, X, Y, X)
    for nm, s, col in tmp:
        out.append((nm, shp(s), col))
    return out, info


# ------------------------------------------------------------------ checks
JOINED = [   # pairs that are screwed or glued together or deliberately overlap (matched by base name)
    ("tilt_bar", "cam_plate"), ("tilt_bar", "tilt_bracket"), ("tilt_bar", "shaft_block"), ("tab_comb", "cam_plate"), ("tab_comb", "tilt_bracket"),
    ("camshaft", "shaft_coupler"), ("camshaft", "cam_"), ("cam_motor", "shaft_coupler"), ("cam_motor", "cam_motor_standoff"),
    ("cam_plate", "cam_motor_standoff"), ("pan_bar_lip", "pan_bar_relief"), ("pan_bar_lip", "x_belt_clamp"), ("pan_bar_relief", "x_belt_clamp"),
    ("x_belt_clamp", "x_belt"), ("x_belt_clamp_cap", "x_belt"), ("x_belt", "x_pulley"), ("x_belt", "x_idler"), ("y_belt", "y_pulley"), ("y_belt", "y_idler"),
    ("y_belt", "tilt_bracket"), ("x_motor", "x_pulley"), ("y_motor", "y_pulley"), ("x_motor", "x_mount"), ("y_motor", "y_mount"),
    ("shaft_collar", "camshaft"), ("shaft_block", "camshaft"), ("shaft_block", "cam_plate"), ("pcb", "pcb_standoff"), ("pcb", "pico"),
    ("pcb", "driver"), ("pcb", "buck"), ("back_plate", "pcb_standoff"), ("back_plate", "guide_pin"), ("y_belt", "y_mount"),
    ("end_right", "dc_jack"), ("spring_", "tab_"), ("spring_", "tab_comb"), ("y_pulley", "y_mount"),
]
ENC = ("back_plate", "wall_top", "wall_bottom", "end_left", "end_right", "front_plate")


def base(n):
    m = re.match(r"^(.*)_(\d+)$", n)
    if m and m.group(1) in ("tab", "cam", "shaft_block", "cam_motor_standoff", "pcb_standoff", "driver", "guide_pin", "front_plate", "stem", "carrier", "glass", "spring"):
        return m.group(1)
    if n.startswith("pan_rail"):
        return "pan_rail"
    return n


def joined(a, b):
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
    for X, Y in ((c9, c9), (-c9, c9), (c9, -c9), (-c9, -c9), (TRAV, 0.0), (-TRAV, 0.0), (0.0, TRAV), (0.0, -TRAV), (14.3, 0.0), (0.0, -13.2), (0.0, 13.2)):
        for th in (0.0, 90.0):
            cases.append((n0, th, X, Y))
    bad = 0
    mintilt = 99.0
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
            print(f"  tilt {tilt:4.1f} X {info['X']:+5.1f} Y {info['Y']:+5.1f} cam {th:5.0f}: CLASH {c[:6]}")
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
    for key, (d, a, b) in sorted(seen.items(), key=lambda kv: kv[1][0]):
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
    print("== cam and belt numbers ==")
    wall = CAM_R - E - SHAFT_R
    zmax = ZAX + E + CAM_R
    print(f"  cam disc r {CAM_R}, shaft r {SHAFT_R}, throw {E}: minimum wall {wall:.2f} mm; highest cam point z {zmax:.2f}, pan bar underside z {ZA:.2f} (clearance {ZA - zmax:.2f})")
    ytop = []
    for deg in range(0, 360, 10):
        phi = math.radians(deg)
        zc = ZAX + E * math.cos(phi)
        dzz = max(0.0, ZT0 - zc)                          # z of the tab's lower face above the cam axis
        ytop.append(E * math.sin(phi) + math.sqrt(CAM_R ** 2 - dzz ** 2))
    amp = (max(ytop) - min(ytop)) / 2
    print(f"  tab motion amplitude with the {ZT0 - ZAX:.2f} mm z offset: +/-{amp:.2f} mm (nominal +/-{E:.2f})")
    xl = 2 * (XN - XF) + math.pi * 12.73
    yl = 2 * (Y_B - Y_A) + math.pi * 12.73
    print(f"  X belt loop {xl:.0f} mm, Y belt loop {yl:.0f} mm (cut GT2 belt, joined in the clamp, buy 1 m)")
    print(f"  mirror torque on the tip: {0.83 * 0.030 * 9.81:.2f} N with 30 g of mirror; tab spring set to about 1.2 N")


# ------------------------------------------------------------------ BOM data
PRINT_BED = (256, 256, 256)
INFO = {   # base -> (process, material, description, note)
    "back_plate": ("laser", "3 mm black acrylic (or birch ply)", "Back plate 824 x 96", "mounting holes 6 x 5 mm"),
    "wall_top": ("laser", "3 mm black acrylic (or birch ply)", "Top wall 824 x 49", "idler slot"),
    "wall_bottom": ("laser", "3 mm black acrylic (or birch ply)", "Bottom wall 824 x 49", ""),
    "end_left": ("laser", "3 mm black acrylic (or birch ply)", "End wall 90 x 49", ""),
    "end_right": ("laser", "3 mm black acrylic (or birch ply)", "End wall 90 x 49", "11 mm hole for the DC jack"),
    "front_plate": ("laser", "4 mm black acrylic", "Front plate layer 824 x 96, 7 x 10.1 mm holes", "2 layers glued, 8 mm total"),
    "pan_bar_lip": ("laser", "0.5 mm stainless shim", "Pan bar lip layer with 4.4 mm slots", "tail included, 588 x 60 mm"),
    "pan_bar_relief": ("laser", "1.5 mm acrylic", "Pan bar relief layer with 9 mm slots", "glue to the lip layer"),
    "tab_comb": ("laser", "2 mm acrylic", "Tab comb (guides tabs, carries pin slots)", "fits a 600 x 300 bed"),
    "pan_rail": ("print", "PETG", "Pan bar guide rail, 220 mm long, C section", "top and bottom, 2 halves each"),
    "tilt_bar": ("laser", "4 mm acrylic", "Tilt bar 524 x 11.5", ""),
    "cam_plate": ("laser", "4 mm acrylic", "Cam plate (left end of the tilt frame)", ""),
    "tab": ("laser", "2 mm POM or acrylic", "Tab with 4.4 mm slot", "line contact with the ball"),
    "x_belt_clamp": ("print", "PETG", "X belt clamp block with riser", ""),
    "x_belt_clamp_cap": ("print", "PETG", "X belt clamp cap", ""),
    "shaft_block": ("print", "PETG", "Camshaft support block, 4.2 mm bore", "6 between mirrors + 1 at the right end"),
    "tilt_bracket": ("print", "PETG", "Tilt bracket with belt clamp arm", ""),
    "x_mount": ("print", "PETG", "X motor mount (plate and foot)", ""),
    "y_mount": ("print", "PETG", "Y motor mount (bridge)", ""),
    "x_limit_post": ("print", "PETG", "X limit switch post", ""),
    "cam": ("print", "nylon or resin (PETG ok)", "Eccentric cam disc 9 mm, 4 mm bore offset 1 mm", "glue to the shaft"),
    "cam_motor": ("buy", "NEMA 17 42 x 34", "NEMA 17 stepper, 42 x 34 mm, 1.5-2 A max", "3 off in total (X, Y, cam)"),
    "x_motor": ("buy", "NEMA 17 42 x 34", "NEMA 17 stepper, 42 x 34 mm", ""),
    "y_motor": ("buy", "NEMA 17 42 x 34", "NEMA 17 stepper, 42 x 34 mm", ""),
    "camshaft": ("buy", "4 mm silver steel / ground rod", "Camshaft 4 mm x 520 mm", "cut from a 1 m rod"),
    "glass": ("buy", "3 mm glass mirror, 50 mm round", "Mirror disc 50 mm", "7 off; acrylic mirror ok for a trial"),
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


BUY = [   # purchased items with no modelled solid, or counted separately: (qty, item, spec, est GBP total, note)
    (3, "NEMA 17 stepper 42 x 34 mm, 5 mm D shaft, 1.5-2 A", "X pan, Y tilt, camshaft", 33, "Pi Hut about 11 GBP each ex VAT (seen earlier)"),
    (3, "TMC2209 stepper driver module", "UART, silent (stealthChop)", 15, "3-7 GBP each, many UK sellers"),
    (1, "Raspberry Pi Pico (RP2040)", "controller", 5, "Pi Hut stocks"),
    (1, "RTC module DS3231", "I2C, keeps time without WiFi", 4, "alternative: GPS module for location-free time"),
    (1, "12 V 2 A DC adapter + panel DC jack 5.5/2.1", "UK plug", 10, ""),
    (1, "Buck converter 12 V to 5 V", "for the Pico and RTC", 3, ""),
    (3, "GT2 20T pulley, 6 mm belt, 5 mm bore", "X motor, Y motor and spares", 8, "5 packs about 8.6 GBP at Desertcart UK"),
    (2, "GT2 20T idler pulley with bearing, 3 mm bore, 6 mm belt", "X and Y idlers", 5, ""),
    (1, "GT2 6 mm belt, 1 m", "cut and clamp, 160 mm per axis", 3, "Pi Hut sells 5 m reels about 9-10 GBP"),
    (1, "Flexible shaft coupler 5 mm to 4 mm, 20 mm long", "motor to camshaft", 3, "the model uses a 10 mm diameter, 20 mm long coupler"),
    (1, "Camshaft rod 4 mm x 520 mm (silver steel or ground)", "cut from a 1 m rod", 4, ""),
    (2, "Shaft collar 4 mm bore, 8 mm OD", "axial stop at the right end (spare)", 2, ""),
    (7, "Mirror disc 50 mm round, 3 mm glass", "front-surface not needed; flat float glass mirror", 14, "craft glass cutters; acrylic mirror for a trial"),
    (7, "Steel ball 10 mm, drilled 2 mm through (or drill yourself)", "pivot ball", 6, "G10 or better; brass ok"),
    (7, "Steel ball 6 mm", "tip ball, epoxied to the rod end", 3, "G10 or better"),
    (7, "Stem rod 2 mm x 52 mm (silver steel or stainless)", "stem, epoxied through the pivot ball", 4, ""),
    (7, "Compression spring 5 mm OD, 0.5 mm wire, 10 mm free, about 0.4 N/mm", "tab preload", 4, "gives about 1.2 N pushing each tab onto its cam"),
    (2, "Micro limit switch with lever (or hall sensor)", "X and Y home", 3, ""),
    (2, "M4 x 25 button head screw + M4 nut", "tilt-frame guide pins", 1, "with the printed standoff; nut in a hex pocket"),
    (1, "M3 screws, nuts and standoffs assortment", "about 60 M3 x 8-16 mm screws, 40 nuts, 4 x M3 x 26 standoffs, 2 x M3 x 36 post", 8, "T-slot nuts for the laser-cut box joints"),
    (1, "Wall fixings", "6 x 4 mm screws and plugs (wall dependent)", 3, ""),
    (1, "Cable, connectors", "motor cables (JST-XH or 4-pin), wire, heat shrink", 8, "tilt frame cable (cam motor) needs a flexing loop"),
    (1, "Epoxy, thread lock, PTFE tape", "", 8, ""),
]


def write_bom(path):
    rows = part_summary()
    order = {"laser": 0, "print": 1, "buy": 2}
    lines = []
    meta = lambda b: INFO.get(b)
    out = ["# Wave version (full detail): parts split and bill of materials", "",
           "Generated by `python3 cad/src/line_wave_full.py --bom` from the model. Prices are rough UK estimates, ex-shipping, unchecked except where a note says so.", ""]
    for title, proc in (("Laser cut", "laser"), ("3D printed", "print")):
        out += [f"## {title}", "", "| Qty | Part | Material | Size (mm, bounding box) | Note |", "|---|---|---|---|---|"]
        for b, inst in rows.items():
            m = meta(b)
            if not m or m[0] != proc:
                continue
            dims = " x ".join(f"{v:g}" for v in inst[0][1])
            out.append(f"| {len(inst)} | {m[2]} | {m[1]} | {dims} | {m[3]} |")
        if proc == "print":
            out.append("| 7 | Mirror carrier 46 mm disc, 4 mm | PLA/PETG | 46 x 46 x 4 | glass bonded on |")
        out.append("")
    out += ["## Purchased (not individually modelled, or counted here)", "", "| Qty | Item | Use | Est. GBP | Note |", "|---|---|---|---|---|"]
    tot = 0
    for q, item, use, price, note in BUY:
        tot += price
        out.append(f"| {q} | {item} | {use} | {price} | {note} |")
    out += ["", f"Purchased total about {tot} GBP (estimate).", ""]
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
        write_bom(lm.CAD.parent / "docs" / "line-mirrors-wave-bom.md")
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
    hide_front = ("glass", "carrier", "front_plate", "end_", "wall_top", "wall_bottom")
    lm.render(parts, IMG / f"{pre}-mechanism.png", view=(6, 40, 1000), focal=(0, -8, 24), hide=hide_front, size=(1900, 800))
    lm.render(parts, IMG / f"{pre}-left-end.png", view=(22, 30, 360), focal=(-320, 0, 24), hide=hide_front, size=(1600, 950))
    lm.render(parts, IMG / f"{pre}-right-end.png", view=(-28, 30, 330), focal=(300, 0, 24), hide=hide_front, size=(1600, 950))
    lm.render(parts, IMG / f"{pre}-row-inside.png", view=(8, 40, 520), focal=(-100, 0, 24), hide=hide_front + ("pan_bar", "pan_rail"), size=(1800, 900))
    lm.render(parts, IMG / f"{pre}-section.png", view=(90, 4, 330), focal=(0, -12, 48), cut_x=0.0, size=(1400, 1000))


if __name__ == "__main__":
    main()
