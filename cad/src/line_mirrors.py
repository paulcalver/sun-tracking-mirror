#!/usr/bin/env python3
"""Wall-mounted line of 7 sun mirrors, two versions of the "out of sync" control (CadQuery). Concept model, nothing built.

Frame (mm): X along the row (right), Y up, Z out of the wall towards the viewer, origin on the wall at the middle of the row.

Rule that keeps the Sun's view clear: the whole enclosure is BEHIND a thin front plate (top at Z = 48). Each mirror stands on a
stem that passes through a ball joint in that plate, with its back face well above the plate even at full tilt. Nothing is in
front of any mirror face except the other mirrors. `--check` proves it with ray casting.

Mirror (x7): 50 mm round glass 3 mm on a 46 mm carrier. A rigid 30 mm stem runs from a ball tip behind the front plate, through
a 10 mm pivot ball in a bore in the front plate (free to slide in Z), to the carrier. Tip position = pivot - 30 * normal.
Both versions move the tips; the tip ball sits between two 2 mm "lip" plates, the pan bar (vertical slots, moves in X) and either
  PASSIVE : the tilt plate (slots at a different small angle for each mirror, moves in Y). Tip height = Y + slope_i * X, so the
            seven spots are in a straight line only at pan offset 0 and fan out as the Sun moves off the wall axis.
  WEDGE   : a wedge bar (seven ramps of different slope) carried on the tilt frame, slid in X by a third NEMA 11. Tip height =
            Y + slope_i * u, u = pan offset minus wedge slide. u = 0 is a straight line, any other u bends it.
Motors: NEMA 11 (28.2 x 28.2 x 34) screw actuators (X and wedge motors at the left end, Y motor hanging inside the strip at the right end), drawn as body + rod. Springs, magnets, guides and fasteners not modelled.

Usage (from the repo root):
  python3 cad/src/line_mirrors.py [--variant passive|wedge|both] [--check] [--no-render]
Writes cad/out/line-mirrors/*.step and renders to cad/media/previews/line-mirrors/.
"""
import argparse
import math
from pathlib import Path

import cadquery as cq

CAD = Path(__file__).resolve().parent.parent
OUT = CAD / "out" / "line-mirrors"
IMG = CAD / "media" / "previews" / "line-mirrors"

# ------------------------------------------------------------------ parameters (mm)
N, PITCH = 7, 70.0
XS = [(i - 3) * PITCH for i in range(N)]
MIR_R, CARR_R, GLASS_T, CARR_T, B_OFF = 25.0, 23.0, 3.0, 4.0, 22.0     # glass, carrier, carrier back face above the pivot
L, STEM_R, PIV_R, TIP_R = 30.0, 1.5, 5.0, 3.0                          # stem length pivot-tip, pivot ball, tip ball
Z_T = 16.0                                                              # tip plane (ball centre)
SLOT_W = 4.4
HALF_H = math.sqrt(TIP_R ** 2 - (SLOT_W / 2) ** 2)                      # ball sits 2.04 off each lip edge
LIP_T = 2.0
LIM = 25.0                                                              # mirror normal cone half angle (Sun 50 deg off the wall axis)
TRAV = L * math.sin(math.radians(LIM))                                  # plate travel for the cone, 12.7
Z_PL0, Z_PL1 = 41.0, 48.0                                               # front plate: the highest part of the enclosure
WALL, HX, HY = 3.0, 330.0, 48.0                                         # housing walls, half length, half height of the strip
XL, XR = -HX, HX                                                        # housing ends (the wave version is longer on the left)
N11, N11L = 28.2, 34.0
ZM = 17.1                                                               # motor axis height (body sits on the back plate)
M = [-0.045, 0.015, 0.06, 0.045, -0.015, -0.06, -0.045]                # passive: tip height per mm of pan
S = [-0.15, 0.05, 0.2, 0.15, -0.05, -0.2, -0.15]                       # wedge: tip height per mm of u
U_MAX = 5.0                                                             # wedge relative slide, +/- mm

HOUSE, FRONT, PLATE_A, PLATE_B, WEDGE, MOTOR, STEEL, STEM, CARR, GLASSC = (
    "#3b3e43", "#2b2d31", "#2f7f86", "#7a5ca8", "#c2552d", "#5b7fa6", "#b9bec4", "#8d939a", "#ece7dc", "#b4d3e8")


# ------------------------------------------------------------------ helpers
def shp(w):
    return w.val() if hasattr(w, "val") else w


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def sph(r, x, y, z):
    return cq.Workplane("XY").sphere(r).translate((x, y, z))


def between(a, b, r):
    v = cq.Vector(*b) - cq.Vector(*a)
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(r, v.Length, cq.Vector(*a), v))


def orient(shape, axis):
    """Rotate a shape built with its axis along +Z so that axis points along `axis`."""
    a = cq.Vector(0, 0, 1)
    b = cq.Vector(*axis).normalized()
    ax = a.cross(b)
    if ax.Length < 1e-9:
        return shape if a.dot(b) > 0 else shape.rotate((0, 0, 0), (1, 0, 0), 180)
    return shape.rotate((0, 0, 0), (ax.x, ax.y, ax.z), math.degrees(math.acos(a.dot(b))))


def nema11(face, axis):
    """Body behind the flange face (which sits at `face`), boss and rod pointing along `axis`; rod added separately."""
    h = N11 / 2
    m = box(-h, h, -h, h, -N11L, 0).edges("|Z").chamfer(2.0).union(cylz(11, 0, 1.6)).cut(cylz(2.6, -N11L - 1, 3))
    return orient(shp(m), axis).translate(face)


def rot_pitch_yaw(shape, pitch, yaw):
    return shape.rotate((0, 0, 0), (1, 0, 0), pitch).rotate((0, 0, 0), (0, 1, 0), yaw)


def pitch_yaw(n):
    return math.degrees(-math.asin(max(-1, min(1, n[1])))), math.degrees(math.atan2(n[0], n[2]))


def unit(v):
    m = math.sqrt(sum(c * c for c in v))
    return tuple(c / m for c in v)


def sun_dir(alpha, phi):
    """Sun direction in the wall frame: alpha from the wall normal, phi around it (0 = +X, 90 = up)."""
    a, f = math.radians(alpha), math.radians(phi)
    return (math.sin(a) * math.cos(f), math.sin(a) * math.sin(f), math.cos(a))


# ------------------------------------------------------------------ static parts
BASE_CFG = dict(Z_T=16.0, Z_PL0=41.0, Z_PL1=48.0, XL=-330.0, XR=330.0, ZM=17.1)
WAVE_CFG = dict(Z_T=27.2, Z_PL0=52.0, Z_PL1=60.0, XL=-412.0, XR=412.0, ZM=24.15)


def configure(variant):
    """The wave version has NEMA 17 motors, so its front plate is further out and the strip longer."""
    globals().update(WAVE_CFG if variant == "wave" else BASE_CFG)


def outline(z0, z1, shrink=0.0):
    """The enclosure strip: 660 x 96 mm in plan. Every motor sits inside it."""
    s = shrink
    return box(XL + s, XR - s, -HY + s, HY - s, z0, z1)


def static_parts(variant):
    P = []
    house = outline(0, Z_PL0).cut(outline(WALL, Z_PL0 + 1, WALL))
    P.append(("housing", house, HOUSE))
    front = outline(Z_PL0, Z_PL1)
    for x in XS:
        front = front.cut(cylz(PIV_R + 0.05, Z_PL0 - 1, Z_PL1 + 1, x, 0))
    P.append(("front_plate", front, FRONT))
    z0 = Z_T - TIP_R if variant == "wedge" else Z_T - HALF_H
    for sy in (1, -1):
        P.append((f"spacer_rail_{'top' if sy > 0 else 'bottom'}", box(-232, 232, 43 if sy > 0 else -45, 45 if sy > 0 else -43, z0, Z_T + HALF_H), HOUSE))
    if variant == "wedge":
        P.append(("back_flat_plate", box(-240, 240, -41, 41, Z_T - TIP_R - 1.5, Z_T - TIP_R), STEEL))
    return P


# ------------------------------------------------------------------ pose
def tips(variant, n_c, u):
    """Plate coordinates for a common normal n_c and wedge offset u. Returns X, Y, D (wedge slide) and each tip (x, y)."""
    X, Y = -L * n_c[0], -L * n_c[1]
    t = []
    for i, x in enumerate(XS):
        ty = Y + (M[i] * X if variant == "passive" else S[i] * u)
        t.append((x + X, ty))
    return X, Y, X - u, t


def lip_with_slots(x0, x1, y0, y1, z0, z1, slots, w=SLOT_W):
    """slots: list of (cx, cy, length, angle_deg) rounded slots cut through the plate."""
    p = box(x0, x1, y0, y1, z0, z1)
    for cx, cy, ln, ang in slots:
        s = (cq.Workplane("XY").workplane(offset=z0 - 1).center(cx, cy).slot2D(ln, w, ang).extrude(z1 - z0 + 2))
        p = p.cut(s)
    return p


def add_mirrors(parts, tp, X, Y, D):
    info = dict(X=X, Y=Y, D=D, normals=[], pivots=[], tips=tp)
    for i, x in enumerate(XS):
        nx, ny = (x - tp[i][0]) / L, (0 - tp[i][1]) / L
        nz2 = 1 - nx * nx - ny * ny
        if nz2 <= 0.05:
            raise ValueError("tilt too large")
        n = (nx, ny, math.sqrt(nz2))
        P_ = (x, 0.0, Z_T + L * n[2])
        T_ = (tp[i][0], tp[i][1], Z_T)
        info["normals"].append(n)
        info["pivots"].append(P_)
        p, y = pitch_yaw(n)
        loc = lambda w: rot_pitch_yaw(shp(w), p, y).translate(cq.Vector(*P_))
        back = tuple(P_[k] + n[k] * (B_OFF + 0.1) for k in range(3))
        stem = between(T_, back, STEM_R).union(sph(PIV_R, *P_)).union(sph(TIP_R, *T_))
        parts.append((f"stem_{i}", stem, STEM))
        parts.append((f"carrier_{i}", loc(cylz(CARR_R, B_OFF, B_OFF + CARR_T)), CARR))
        parts.append((f"glass_{i}", loc(cylz(MIR_R, B_OFF + CARR_T, B_OFF + CARR_T + GLASS_T)), GLASSC))
    return info


def pose(variant, n_c, u=0.0):
    """All parts for a common mirror normal n_c (unit, wall frame) and wedge offset u (mm; wave version: cam angle, deg)."""
    configure(variant)
    if variant == "wave":
        return pose_wave(n_c, u)
    X, Y, D, tp = tips(variant, n_c, u)
    parts = list(static_parts(variant))
    slot_len_y = 2 * (TRAV + 3.0) + SLOT_W
    slot_len_x = 2 * (TRAV + 3.0) + SLOT_W
    # pan bar (moves in X): vertical slots, lug at the left end for the X screw
    za = Z_T + HALF_H
    a = lip_with_slots(-240, 240, -28, 28, za, za + 0.8, [(x, 0, slot_len_y, 90) for x in XS])
    a = a.union(lip_with_slots(-240, 240, -28, 28, za + 0.8, za + LIP_T, [(x, 0, slot_len_y, 90) for x in XS], w=9.0))
    a = a.union(box(-245, -240, 20, 36, 14.0, za + LIP_T))
    parts.append(("pan_bar", shp(a).translate(cq.Vector(X, 0, 0)), PLATE_A))
    if variant == "passive":
        b = lip_with_slots(-240, 240, -28, 28, Z_T - HALF_H - LIP_T, Z_T - HALF_H,
                           [(x, 0, slot_len_x, math.degrees(math.atan(M[i]))) for i, x in enumerate(XS)])
        b = b.union(box(236, 296, -10, -4, Z_T - HALF_H - LIP_T, Z_T - HALF_H)).union(box(276, 296, -10, -4, Z_T - HALF_H - LIP_T, 20.2))
        parts.append(("tilt_plate", shp(b).translate(cq.Vector(0, Y, 0)), PLATE_B))
        tab_top, arm_x = -4.0 + Y, 286.0
    else:
        fr = box(-240, 300, -17, -14, Z_T - TIP_R + 0.05, Z_T + TIP_R - 1.05).union(box(286, 300, -17, -10, Z_T - TIP_R + 0.05, 20.2))
        parts.append(("tilt_frame", shp(fr).translate(cq.Vector(0, Y, 0)), PLATE_B))
        wb = box(-262, 264, -14, -12, Z_T - TIP_R + 0.1, Z_T + TIP_R - 1.1).union(box(-268, -262, -31, -5, Z_T - TIP_R + 0.1, Z_T + TIP_R - 1.1))
        for i, x in enumerate(XS):
            poly = [(x - 20, -3 - 20 * S[i]), (x + 20, -3 + 20 * S[i]), (x + 20, -12), (x - 20, -12)]
            wb = wb.union(cq.Workplane("XY").workplane(offset=Z_T - TIP_R + 0.1).polyline(poly).close().extrude(2 * TIP_R - 1.2))
        parts.append(("wedge_bar", shp(wb).translate(cq.Vector(D, Y, 0)), WEDGE))
        tab_top, arm_x = -10.0 + Y, 293.0
        # wedge motor at the left end, below the X motor, pushing the bar in +X (spring at the right end not modelled)
        parts.append(("wedge_motor", nema11((-288, -18, ZM), (1, 0, 0)), MOTOR))
        parts.append(("wedge_rod", between((-288, -18, ZM), (-268 + D, -18, ZM), 2.4), STEEL))
    # X motor (left) and rod to the lug; Y motor hangs from the top wall at the right end, its rod pushes the tab down
    parts.append(("x_motor", nema11((-288, 28, ZM), (1, 0, 0)), MOTOR))
    parts.append(("x_rod", between((-288, 28, ZM), (-245 + X, 28, ZM), 2.4), STEEL))
    parts.append(("y_motor", nema11((arm_x, 11, ZM), (0, -1, 0)), MOTOR))
    parts.append(("y_rod", between((arm_x, 11, ZM), (arm_x, tab_top, ZM), 2.4), STEEL))
    info = add_mirrors(parts, tp, X, Y, D)
    return [(n_, shp(s), c) for n_, s, c in parts], info


# ------------------------------------------------------------------ wave version: NEMA 17 belts, camshaft travelling wave
E_AMP, D_PHASE = 1.0, math.radians(60.0)                                # cam throw (mm of tip height) and phase step between mirrors
N17, N17L, ZAX = 42.3, 34.0, 24.15                                      # Pi Hut NEMA 17 42 x 34, motor axis height (body on the back plate)
XF, XN, XPL0 = -386.0, -330.0, 17.5                                     # X belt: motor pulley x, idler x, pulley y start (belt 6 wide)
YP, Y_A, Y_B = 300.0, -23.5, 30.5                                       # Y belt: x of both pulleys, motor pulley y, idler y
CAM_Y = -9.5                                                            # camshaft height relative to the tilt frame


def nema17(face, axis, shaft=24.0):
    h = N17 / 2
    m = box(-h, h, -h, h, -N17L, 0).edges("|Z").chamfer(3.0).union(cylz(11, 0, 2.0)).union(cylz(2.5, 0, shaft))
    return orient(shp(m), axis).translate(face)


def cyl_along(axis, r, a0, a1, c1, c2):
    """Cylinder along x, y or z from a0 to a1; (c1, c2) are the other two coordinates in x, y, z order."""
    p, d = {"x": ((a0, c1, c2), (1, 0, 0)), "y": ((c1, a0, c2), (0, 1, 0)), "z": ((c1, c2, a0), (0, 0, 1))}[axis]
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(r, a1 - a0, cq.Vector(*p), cq.Vector(*d)))


def pulley(axis, a0, a1, c1, c2, bore=0.0):
    p = cyl_along(axis, 6.4, a0 + 1, a1 - 1, c1, c2).union(cyl_along(axis, 8.0, a0, a0 + 1, c1, c2)).union(cyl_along(axis, 8.0, a1 - 1, a1, c1, c2))
    return p.cut(cyl_along(axis, bore, a0 - 1, a1 + 1, c1, c2)) if bore else p


def belt_xy(c, d, ang, z0, z1):
    o = cq.Workplane("XY").workplane(offset=z0).center(*c).slot2D(d + 15.6, 15.6, ang).extrude(z1 - z0)
    i = cq.Workplane("XY").workplane(offset=z0 - 1).center(*c).slot2D(d + 12.8, 12.8, ang).extrude(z1 - z0 + 2)
    return o.cut(i)


def pose_wave(n_c, theta):
    """theta = cam angle in degrees: mirror i tip height = Y + E_AMP * sin(theta + i * 60 deg), a wave running along the row."""
    X, Y = -L * n_c[0], -L * n_c[1]
    ph = [math.radians(theta) + i * D_PHASE for i in range(N)]
    tp = [(x + X, Y + E_AMP * math.sin(ph[i])) for i, x in enumerate(XS)]
    P = []
    P.append(("housing", outline(0, Z_PL0).cut(outline(WALL, Z_PL0 + 1, WALL)), HOUSE))
    front = outline(Z_PL0, Z_PL1)
    for x in XS:
        front = front.cut(cylz(PIV_R + 0.05, Z_PL0 - 1, Z_PL1 + 1, x, 0))
    P.append(("front_plate", front, FRONT))
    for sy in (1, -1):
        P.append((f"spacer_rail_{'top' if sy > 0 else 'bottom'}", box(-232, 232, 43 if sy > 0 else -45, 45 if sy > 0 else -43, Z_T - HALF_H, Z_T + HALF_H), HOUSE))
    # X drive (pan), left end: motor, pulley, idler on an axle from the top wall, belt in the XZ plane
    P.append(("x_motor", nema17((XF, 15.0, ZAX), (0, 1, 0)), MOTOR))
    P.append(("x_pulley", pulley("y", XPL0, XPL0 + 8, XF, ZAX, bore=2.55), STEEL))
    P.append(("x_idler", pulley("y", XPL0, XPL0 + 8, XN, ZAX).union(cyl_along("y", 2.5, XPL0 + 8, 45, XN, ZAX)), STEEL))
    xb = belt_xy(((XF + XN) / 2, ZAX), XN - XF, 0, 0, 6)
    P.append(("x_belt", shp(xb).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, XPL0 + 7, 0)), WEDGE))
    # Y drive (tilt), right end: motor standing on the back plate, pulley above it, idler on a post, belt in the XY plane
    P.append(("y_motor", nema17((YP, Y_A, 37.0), (0, 0, 1), shaft=12.0), MOTOR))
    P.append(("y_pulley", pulley("z", 39, 47, YP, Y_A, bore=2.55), STEEL))
    P.append(("y_idler", pulley("z", 39, 47, YP, Y_B).union(cyl_along("z", 2.5, 3, 39, YP, Y_B)), STEEL))
    P.append(("y_belt", belt_xy((YP, (Y_A + Y_B) / 2), Y_B - Y_A, 90, 40, 46), WEDGE))
    # pan bar (moves in X) with the arm and belt clamp at its left end
    za = Z_T + HALF_H
    sl = 2 * (TRAV + 3.0) + SLOT_W
    a = lip_with_slots(-240, 240, -28, 28, za, za + 0.8, [(x, 0, sl, 90) for x in XS])
    a = a.union(lip_with_slots(-240, 240, -28, 28, za + 0.8, za + LIP_T, [(x, 0, sl, 90) for x in XS], w=9.0))
    a = a.union(box(-362, -239, 27, 33, za, 33.0)).union(box(-362, -354, 18, 33, za, 30.45))
    P.append(("pan_bar", shp(a).translate(cq.Vector(X, 0, 0)), PLATE_A))
    # tilt frame (moves in Y): bar, cam plate and motor standoffs, right bearing, bracket and arm to the Y belt
    def mv(w):
        return shp(w).translate(cq.Vector(0, Y, 0))
    P.append(("tilt_bar", mv(box(-254, 270, -26, -22, 21, 26.5)), PLATE_B))
    P.append(("cam_plate", mv(box(-258, -254, -27, 8, 6, 42).cut(cyl_along("x", 2.55, -259, -253, CAM_Y, ZAX))), PLATE_B))
    posts = None
    for dy in (-15.5, 15.5):
        for dz in (-15.5, 15.5):
            c = cyl_along("x", 2.0, -278, -258, CAM_Y + dy, ZAX + dz)
            posts = c if posts is None else posts.union(c)
    P.append(("cam_posts", mv(posts), PLATE_B))
    P.append(("bearing_right", mv(box(238, 246, -22, -3, 21, 27.8).cut(cyl_along("x", 2.55, 237, 247, CAM_Y, ZAX))), PLATE_B))
    P.append(("tilt_bracket", mv(box(262, 270, -22, 7, 21, 46.5).union(box(262, 292, 0.5, 6.5, 39.5, 46.5))), PLATE_B))
    # camshaft with its coupler, and the cam motor on the frame
    cs = cyl_along("x", 2.5, -266, 246, CAM_Y, ZAX)
    for i, x in enumerate(XS):
        cs = cs.union(cyl_along("x", 3.5, x - 6, x + 6, CAM_Y + E_AMP * math.sin(ph[i]), ZAX + E_AMP * math.cos(ph[i])))
    cs = cs.union(cyl_along("x", 11, -276, -259, CAM_Y, ZAX).cut(cyl_along("x", 2.55, -277, -267.2, CAM_Y, ZAX)))
    P.append(("camshaft", mv(cs), STEEL))
    P.append(("cam_motor", nema17((-278, Y + CAM_Y, ZAX), (1, 0, 0), shaft=9.5), MOTOR))
    # tabs: slotted plates carried by the cams, one per mirror
    zb0, zb1 = Z_T - HALF_H - LIP_T, Z_T - HALF_H
    for i, x in enumerate(XS):
        t = lip_with_slots(x - 22, x + 22, -6, 6, zb0, zb1, [(x, 0, sl, 0)])
        P.append((f"tab_{i}", shp(t).translate(cq.Vector(0, Y + E_AMP * math.sin(ph[i]), 0)), PLATE_B))
    info = add_mirrors(P, tp, X, Y, X)
    return [(n_, shp(s_), c_) for n_, s_, c_ in P], info


# ------------------------------------------------------------------ checks
def clashes(parts, tol=1.0, skip=()):
    out = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _ in parts]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            a, b = bbs[i], bbs[j]
            if (a[2].xmax < b[2].xmin or b[2].xmax < a[2].xmin or a[2].ymax < b[2].ymin or b[2].ymax < a[2].ymin
                    or a[2].zmax < b[2].zmin or b[2].zmax < a[2].zmin):
                continue
            if any(sk in a[0] + b[0] for sk in skip):
                continue
            try:
                v = a[1].intersect(b[1]).Volume()
            except Exception:
                v = -1
            if v > tol:
                out.append((a[0], b[0], round(v, 1)))
    return out


def cone_normal(theta, phi):
    return sun_dir(theta, phi)


def ray_check(parts, info, sun):
    """For every mirror, cast rays from sample points on the glass towards the Sun (in) and along the reflected direction (out).
    Returns blocked fractions (enclosure, other mirrors) for in and out."""
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    from OCP.gp import gp_Lin, gp_Pnt, gp_Dir

    enc = [s for n, s, _ in parts if not any(k in n for k in ("glass", "carrier", "stem"))]
    comp = lambda lst: cq.Compound.makeCompound(lst)
    enc_i = IntCurvesFace_ShapeIntersector(); enc_i.Load(comp(enc).wrapped, 1e-3)
    res = {"enc_in": 0, "enc_out": 0, "mir_in": 0, "mir_out": 0, "n": 0}
    mir_parts = {i: [s for n, s, _ in parts if n.endswith(f"_{i}") and any(k in n for k in ("glass", "carrier", "stem"))] for i in range(N)}
    for i in range(N):
        others = [s for k, lst in mir_parts.items() if k != i for s in lst]
        oth = IntCurvesFace_ShapeIntersector(); oth.Load(comp(others).wrapped, 1e-3)
        n = info["normals"][i]
        p, y = pitch_yaw(n)
        P_ = info["pivots"][i]
        out = tuple(2 * sum(n[k] * sun[k] for k in range(3)) * n[j] - sun[j] for j in range(3))
        pts = [(0.0, 0.0)] + [(12 * math.cos(a * math.pi / 3), 12 * math.sin(a * math.pi / 3)) for a in range(6)] \
              + [(23.5 * math.cos(a * math.pi / 4), 23.5 * math.sin(a * math.pi / 4)) for a in range(8)]
        for (u_, v_) in pts:
            loc = cq.Vector(u_, v_, B_OFF + CARR_T + GLASS_T + 0.05)
            loc = cq.Vertex.makeVertex(loc.x, loc.y, loc.z)
            w = rot_pitch_yaw(loc, p, y).Center()
            o = (w.x + P_[0], w.y + P_[1], w.z + P_[2])
            for key, d in (("in", sun), ("out", out)):
                lin = gp_Lin(gp_Pnt(*o), gp_Dir(*d))
                enc_i.Perform(lin, 0.0, 1500.0)
                if enc_i.NbPnt() > 0:
                    res["enc_" + key] += 1
                oth.Perform(lin, 0.0, 1500.0)
                if oth.NbPnt() > 0:
                    res["mir_" + key] += 1
            res["n"] += 1
    return res


def run_checks(variants):
    for var in variants:
        print(f"\n=== {var} ===")
        cases = [(0, 0, 0.0)] + [(LIM, phi, 0.0) for phi in range(0, 360, 45)]
        if var == "wave":
            cases = [(0, 0, 0.0), (0, 0, 90.0), (0, 0, 180.0)] + [(LIM, phi, (phi * 2 + 30) % 360) for phi in range(0, 360, 45)]
        if var == "wedge":
            cases += [(0, 0, U_MAX), (LIM, 0, -U_MAX), (LIM, 90, U_MAX), (LIM, 225, U_MAX)]
        for th, phi, u in cases:
            n_c = cone_normal(th, phi)
            parts, info = pose(var, n_c, u)
            c = clashes(parts)
            maxtilt = max(math.degrees(math.acos(n[2])) for n in info["normals"])
            lowest = min(s.BoundingBox().zmin for nm, s, _ in parts if "glass" in nm or "carrier" in nm) - Z_PL1
            print(f"tilt {th:3.0f} dir {phi:3.0f} u {u:+4.1f}: X {info['X']:+5.1f} Y {info['Y']:+5.1f} D {info['D']:+5.1f}  "
                  f"max mirror tilt {maxtilt:4.1f}  glass/carrier above plate {lowest:+5.1f}  clashes {c if c else 'none'}")
        print("-- sun view (rays from 15 points per mirror, in = towards the Sun, out = reflected) --")
        for alpha in (25, 50, 65):
            tot = dict(enc_in=0, enc_out=0, mir_in=0, mir_out=0, n=0)
            for phi in range(0, 360, 45):
                s = sun_dir(alpha, phi)
                n_c = unit(tuple(s[k] + (0, 0, 1)[k] for k in range(3)))
                for u in ((0.0, U_MAX) if var == "wedge" else (0.0, 120.0) if var == "wave" else (0.0,)):
                    try:
                        parts, info = pose(var, n_c, u)
                    except ValueError:
                        continue
                    r = ray_check(parts, info, s)
                    for k in tot:
                        tot[k] += r[k]
            f = lambda k: 100.0 * tot[k] / max(1, tot["n"])
            print(f"Sun {alpha:2d} deg off the wall axis: enclosure blocks in {f('enc_in'):4.1f}% out {f('enc_out'):4.1f}%   "
                  f"other mirrors block in {f('mir_in'):4.1f}% out {f('mir_out'):4.1f}%   ({tot['n']} rays)")
        # spot lines at 3 m for a sun 40 deg to the right and 40 to the left
        for alpha, phi in ((40, 0), (0, 0), (40, 180)):
            s = sun_dir(alpha, phi); n_c = unit(tuple(s[k] + (0, 0, 1)[k] for k in range(3)))
            parts, info = pose(var, n_c, U_MAX if var == "wedge" else 90.0 if var == "wave" else 0.0)
            ys = []
            for i in range(N):
                n = info["normals"][i]
                out = tuple(2 * sum(n[k] * s[k] for k in range(3)) * n[j] - s[j] for j in range(3))
                z0 = info["pivots"][i][2] + n[2] * 30
                ys.append((XS[i] + out[0] * (3000 - z0) / out[2], out[1] * (3000 - z0) / out[2]))
            print(f"spots at 3 m, Sun {alpha} deg {'right' if phi == 0 else 'left'}: y(mm) = " + ", ".join(f"{b:+6.0f}" for a, b in ys))


# ------------------------------------------------------------------ export and render
def cqc(h):
    h = h.lstrip("#")
    return cq.Color(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, 1.0)


def save_step(parts, path):
    a = cq.Assembly(name=path.stem)
    for nm, s, col in parts:
        a.add(s, name=nm, color=cqc(col))
    a.save(str(path))
    print("Wrote", path)


def render(parts, path, view, focal, size=(1600, 900), hide=(), cut_x=None, rays=None):
    import vtk

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.96); ren.SetBackground2(0.86, 0.87, 0.89); ren.GradientBackgroundOn()
    for nm, s, col in parts:
        if any(h in nm for h in hide):
            continue
        if cut_x is not None:
            s = s.cut(shp(box(cut_x, 600, -300, 300, -10, 200)))
        v, t = s.tessellate(0.2, 0.3)
        if not t:
            continue
        pts, cells = vtk.vtkPoints(), vtk.vtkCellArray()
        for p in v:
            pts.InsertNextPoint(p.x, p.y, p.z)
        for a, b, c in t:
            cells.InsertNextCell(3)
            for k in (a, b, c):
                cells.InsertCellPoint(k)
        pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
        nm_ = vtk.vtkPolyDataNormals(); nm_.SetInputData(pd); nm_.SetFeatureAngle(35); nm_.SplittingOn(); nm_.Update()
        mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(nm_.GetOutputPort())
        ac = vtk.vtkActor(); ac.SetMapper(mp)
        h = col.lstrip("#")
        ac.GetProperty().SetColor(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
        gl = nm.startswith("glass")
        ac.GetProperty().SetSpecular(0.9 if gl else 0.25); ac.GetProperty().SetSpecularPower(80 if gl else 20)
        ac.GetProperty().SetDiffuse(0.85); ac.GetProperty().SetAmbient(0.2)
        ren.AddActor(ac)
    for (a, b, col, r) in (rays or []):
        ln = vtk.vtkLineSource(); ln.SetPoint1(*a); ln.SetPoint2(*b); ln.SetResolution(1)
        tb = vtk.vtkTubeFilter(); tb.SetInputConnection(ln.GetOutputPort()); tb.SetRadius(r); tb.SetNumberOfSides(12)
        mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(tb.GetOutputPort())
        ac = vtk.vtkActor(); ac.SetMapper(mp); ac.GetProperty().SetColor(*col); ac.GetProperty().SetAmbient(1.0)
        ren.AddActor(ac)
    cm = ren.GetActiveCamera()
    az, el, dist = math.radians(view[0]), math.radians(view[1]), view[2]
    pos = (focal[0] + dist * math.cos(el) * math.sin(az), focal[1] + dist * math.sin(el), focal[2] + dist * math.cos(el) * math.cos(az))
    cm.SetFocalPoint(*focal); cm.SetPosition(*pos); cm.SetViewUp(0, 1, 0); cm.SetViewAngle(28)
    ren.ResetCameraClippingRange()
    for p_, I in (((300, 400, 600), 0.6), ((-400, 200, 300), 0.35), ((0, -300, 300), 0.25)):
        Lt = vtk.vtkLight(); Lt.SetPosition(*p_); Lt.SetFocalPoint(*focal); Lt.SetIntensity(I); Lt.SetLightTypeToSceneLight(); ren.AddLight(Lt)
    ren.LightFollowCameraOff()
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(*size); win.SetMultiSamples(8)
    win.AddRenderer(ren); win.Render()
    f = vtk.vtkWindowToImageFilter(); f.SetInput(win); f.ReadFrontBufferOff(); f.Update()
    w = vtk.vtkPNGWriter(); w.SetFileName(str(path)); w.SetInputConnection(f.GetOutputPort()); w.Write()
    print("Wrote", path)


def out_rays(info, sun, length=900.0):
    r = []
    for i in range(N):
        n = info["normals"][i]
        o = tuple(info["pivots"][i][k] + n[k] * (B_OFF + CARR_T + GLASS_T) for k in range(3))
        d = tuple(2 * sum(n[k] * sun[k] for k in range(3)) * n[j] - sun[j] for j in range(3))
        r.append((o, tuple(o[k] + d[k] * length for k in range(3)), (1.0, 0.72, 0.15), 0.8))
    c = tuple(info["pivots"][3][k] + info["normals"][3][k] * (B_OFF + CARR_T + GLASS_T) for k in range(3))
    r.append((tuple(c[k] + sun[k] * 700 for k in range(3)), c, (1.0, 0.85, 0.2), 1.6))
    return r


def make(variant, render_on=True):
    s = sun_dir(40, 20)                                  # a morning-ish Sun, 40 deg off the wall axis
    n_c = unit(tuple(s[k] + (0, 0, 1)[k] for k in range(3)))
    u = U_MAX if variant == "wedge" else 60.0 if variant == "wave" else 0.0
    parts, info = pose(variant, n_c, u)
    OUT.mkdir(parents=True, exist_ok=True)
    save_step(parts, OUT / f"line-mirrors-{variant}.step")
    if not render_on:
        return
    IMG.mkdir(parents=True, exist_ok=True)
    flat, _ = pose(variant, (0, 0, 1), 0.0)
    pre = f"line-{variant}"
    fx, k = (-41.0, 1.22) if variant == "wave" else (0.0, 1.0)
    render(flat, IMG / f"{pre}-front.png", view=(32, 9, 1000 * k), focal=(fx - 20, -15, 50))
    render(parts, IMG / f"{pre}-posed-rays.png", view=(15, 14, 1450 * k), focal=(fx, 0, 60), rays=out_rays(info, s))
    render(parts, IMG / f"{pre}-mechanism.png", view=(12, 30, 880 * k), focal=(fx, -10, 18), hide=("glass", "carrier", "front_plate", "housing"), size=(1700, 900))
    render(parts, IMG / f"{pre}-inner.png", view=(8, 22, 830 * k), focal=(fx, -5, 18), hide=("glass", "carrier", "front_plate", "housing", "pan_bar"), size=(1700, 900))
    render(parts, IMG / f"{pre}-section.png", view=(90, 4, 330), focal=(0, -12, 48), cut_x=0.0, size=(1400, 1000))
    if variant == "wave":
        render(parts, IMG / f"{pre}-left-end.png", view=(20, 28, 330), focal=(-330, -5, 24), hide=("glass", "carrier", "front_plate", "housing"), size=(1500, 950))
        render(parts, IMG / f"{pre}-right-end.png", view=(-25, 28, 300), focal=(270, -5, 24), hide=("glass", "carrier", "front_plate", "housing"), size=(1500, 950))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=("passive", "wedge", "wave", "both", "all"), default="both")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    vs = ("passive", "wedge") if a.variant == "both" else ("passive", "wedge", "wave") if a.variant == "all" else (a.variant,)
    if a.check:
        run_checks(vs)
        return
    for v in vs:
        make(v, not a.no_render)


if __name__ == "__main__":
    main()
