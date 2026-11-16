#!/usr/bin/env python3
"""First-pass CAD assembly: hinged flat mirror on a turning drum (CadQuery). Draft, nothing built or tested.

World frame (mm): origin at the centre of the base on the table, Z up, X along the hinge axis, +Y towards the
Sun side of the mirror at 'upright'. Hierarchy (maps to Fusion components, no joints yet):
  base_fixed        steel floor plate, cup wall, bearing ring, hub pulley, slip ring, sensors
  drum_rotating     floor, wall, top plate, azimuth motor + belt, tilt motor + chain, controller, hinge blocks
    mirror_tilting  frame, glass, backing, hinge shaft, lugs, 32T sprocket (origin on the hinge axis, X axis = revolute)

Drives:
  azimuth: NEMA 17 (no gearbox) stands in the drum, shaft down, 16T GT2 pulley, belt around a FIXED 160T hub
           pulley (planetary belt, 10:1, smooth, no backlash). Power only crosses the slip ring.
  tilt:    NEMA 17 + 10:1 gearbox lies along X, 16T ANSI 25 sprocket, 42 link chain to a 32T sprocket on the
           hinge shaft (2:1, 20:1 overall). Chain sits outside the right hand hinge block.
Teeth are NOT modelled (pulleys and sprockets are root cylinders). Bought parts are marked in grey.

Usage (from the repo root):
  python3 cad/src/hinge_mirror_v1_exposed.py [--tilt DEG] [--az DEG] [--check]
Writes cad/out/hinge-mirror/assembly/hinge-mirror-v1-exposed-assembly.step, .glb and hinge-mirror-v1-exposed-preview.png (suffix added if posed).
"""
import argparse
import math
from pathlib import Path

import cadquery as cq

CAD = Path(__file__).resolve().parent.parent
ASM = CAD / "out" / "hinge-mirror" / "archive"
PARTS = CAD / "out" / "hinge-mirror" / "archive" / "hinge-mirror-v1-parts"
IMG = CAD / "media" / "earlier-concepts"

# ------------------------------------------------------------------ parameters (mm)
MIR_W, MIR_H, GLASS_T, BACK_T = 200.0, 267.0, 4.0, 4.0     # 3:4 mirror on a rigid backing
FRAME_W, FRAME_H, FRAME_D = MIR_W + 8, MIR_H + 8, 10.0
FRAME_Z0 = 8.0                                              # frame bottom edge above the hinge axis

CUP_R, WALL_T = 131.0, 4.0                                  # fixed cup (outer radius)
FLOOR_T = 6.0                                               # steel floor plate = ballast (about 2.5 kg)
CUP_TOP, BRG_T, DRUM_FLOOR_T = 14.0, 3.0, 3.0
DRUM_R, DRUM_WALL_T, PLATE_T = 126.0, 2.0, 7.0
FLOOR_TOP = CUP_TOP + BRG_T + DRUM_FLOOR_T                  # 20: top of drum floor
BAND = 42.0                                                 # motor height band inside the drum
PLATE_Z0 = FLOOR_TOP + BAND                                 # 62
PLATE_TOP = PLATE_Z0 + PLATE_T                              # 69
Z_M = FLOOR_TOP + BAND / 2                                  # tilt motor axis, 41

P25 = 6.35                                                  # ANSI 25 pitch
N_H, N_M = 32, 16
PCD = lambda n: P25 / math.sin(math.pi / n)
R_H, R_M = PCD(N_H) / 2, PCD(N_M) / 2                       # pitch radii 32.4, 16.3
LINKS = 42
_k = LINKS - (N_H + N_M) / 2
C_DIST = P25 / 4 * (_k + math.sqrt(_k * _k - 8 * ((N_H - N_M) / (2 * math.pi)) ** 2))
H = Z_M + C_DIST                                            # hinge axis height (about 95)

BLOCK_X0, BLOCK_X1, BLOCK_W = 106.0, 114.0, 8.0
SPR_X0, SPR_X1 = 115.0, 122.0                               # sprocket plane, outside right block
SHAFT_R, SHAFT_X0, SHAFT_X1 = 4.0, -116.0, 124.0

GT_P = 2.0                                                  # GT2 pitch
HUB_T, MOT_T = 160, 16
HUB_R = (HUB_T * GT_P / math.pi - 0.76) / 2                 # outside radius of root cylinder
MOTP_R = (MOT_T * GT_P / math.pi - 0.76) / 2
AZ_D = 90.0                                                 # azimuth motor distance from the axis (on -Y)
BELT_Z0, BELT_W = 7.0, 6.0

GREY, DARKG, STEEL = "#9a9a9a", "#4d4d4d", "#c4c8cc"
ORANGE, BLUE, BRASS, GLASS, RED, GREEN = "#e8a400", "#4a6fa5", "#b5893a", "#cfe3ee", "#c0392b", "#2e8b57"
FRAMEC, BLACK = "#8a6d2f", "#222222"


# ------------------------------------------------------------------ helpers
def _shape(wp):
    v = wp.val() if hasattr(wp, "val") else wp
    return v


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def cylx(r, x0, x1, y=0.0, z=0.0):
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)


def ring(ro, ri, z0, z1):
    return cylz(ro, z0, z1).cut(cylz(ri, z0 - 1, z1 + 1))


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


def hull(plane_fn, c1, r1, c2, r2, depth):
    t = tangents(c1, r1, c2, r2)
    quad = [t[0][0], t[0][1], t[1][1], t[1][0]]
    s = plane_fn().polyline(quad).close().extrude(depth)
    s = s.union(plane_fn().center(*c1).circle(r1).extrude(depth))
    return s.union(plane_fn().center(*c2).circle(r2).extrude(depth))


def loop(plane_fn, c1, r1, c2, r2, depth, thick):
    return hull(plane_fn, c1, r1 + thick, c2, r2 + thick, depth).cut(hull(plane_fn, c1, r1, c2, r2, depth))


def nema17(body=34.0, gearbox=0.0, shaft=24.0, shaft_r=2.5):
    """Local frame: flange face at z=0, body behind it (z from -body to 0), optional square gearbox in front."""
    m = box(-21, 21, -21, 21, -body, 0).edges("|Z").chamfer(3)
    m = m.union(cylz(11, 0, 2))
    if gearbox:
        g = box(-21, 21, -21, 21, 0, gearbox).edges("|Z").chamfer(3)
        m = m.union(g).union(cylz(11, gearbox, gearbox + 1))
        return m.union(cylz(4, gearbox, gearbox + shaft))
    return m.union(cylz(shaft_r, 0, shaft))


# ------------------------------------------------------------------ parts
base_parts, drum_parts, mirror_parts = [], [], []


def add(lst, name, wp, colour):
    lst.append((name, wp, colour))


def build():
    # ============ fixed base ============
    add(base_parts, "base_floor_plate_steel_6mm", cylz(CUP_R, 0, FLOOR_T), DARKG)
    add(base_parts, "base_cup_wall", ring(CUP_R, CUP_R - WALL_T, FLOOR_T, CUP_TOP), BLACK)
    add(base_parts, "turntable_bearing_ring", ring(125.0, 119.0, CUP_TOP, CUP_TOP + BRG_T), GREY)
    hub = cylz(HUB_R, BELT_Z0, BELT_Z0 + BELT_W).union(cylz(16, FLOOR_T, BELT_Z0)).cut(cylz(11.05, 0, 30))
    add(base_parts, "hub_pulley_160T_fixed", hub, ORANGE)
    add(base_parts, "slip_ring_22mm", cylz(11.0, FLOOR_T, 38.0), GREY)
    add(base_parts, "az_home_sensor", box(-4, 4, -113.5, -110.5, FLOOR_T, 13.6), GREEN)

    # ============ rotating drum ============
    floor = cylz(DRUM_R, CUP_TOP + BRG_T, FLOOR_TOP).cut(cylz(12.0, 0, 40)).cut(cylz(11.5, 0, 40, 0, -AZ_D))
    add(drum_parts, "drum_floor", floor, STEEL)
    add(drum_parts, "drum_wall", ring(DRUM_R, DRUM_R - DRUM_WALL_T, FLOOR_TOP, PLATE_Z0), STEEL)
    plate = cylz(DRUM_R, PLATE_Z0, PLATE_TOP).cut(box(SPR_X0 - 1, 123.0, -31, 31, PLATE_Z0 - 1, PLATE_TOP + 1))
    add(drum_parts, "drum_top_plate", plate, STEEL)

    # azimuth: motor stands on the floor, shaft down through it, pulley in the belt band
    az = nema17(body=34.0, shaft=14.0).rotate((0, 0, 0), (0, 1, 0), 180).translate((0, -AZ_D, FLOOR_TOP))
    add(drum_parts, "az_motor_NEMA17_34mm", az, GREY)
    pul = (cylz(MOTP_R, BELT_Z0, BELT_Z0 + BELT_W, 0, -AZ_D).union(cylz(7, BELT_Z0 - 1, BELT_Z0, 0, -AZ_D))
           .union(cylz(7, BELT_Z0 + BELT_W, BELT_Z0 + BELT_W + 1, 0, -AZ_D)).cut(cylz(2.5, 0, 30, 0, -AZ_D)))
    add(drum_parts, "az_motor_pulley_16T", pul, ORANGE)
    belt = loop(lambda: cq.Workplane("XY", origin=(0, 0, BELT_Z0)), (0, 0), HUB_R + 0.05, (0, -AZ_D), MOTP_R + 0.05,
                BELT_W, 1.5)
    add(drum_parts, "az_belt_GT2_6mm", belt, BLACK)
    add(drum_parts, "az_home_magnet", cylz(2.5, CUP_TOP + BRG_T - 2.0, CUP_TOP + BRG_T, 0, -112.0), RED)

    # tilt: motor + 10:1 gearbox along X, output face at X=114, 16T sprocket outside the right block
    tm = nema17(body=34.0, gearbox=40.0, shaft=9.0).rotate((0, 0, 0), (0, 1, 0), 90).translate((114.0 - 40.0, 0, Z_M))
    add(drum_parts, "tilt_motor_NEMA17_gearbox_10to1", tm, GREY)
    spm = cylx(R_M - 3.0, SPR_X0, SPR_X1, 0, Z_M).cut(cylx(4.0, SPR_X0 - 1, SPR_X1 + 1, 0, Z_M))
    add(drum_parts, "tilt_sprocket_16T", spm, ORANGE)
    xc = (SPR_X0 + SPR_X1) / 2
    chain = loop(lambda: cq.Workplane("YZ", origin=(xc - 2.0, 0, 0)), (0, Z_M), R_M - 3.0, (0, H), R_H - 3.0, 4.0, 6.0)
    add(drum_parts, f"tilt_chain_ANSI25_{LINKS}links", chain, BLACK)

    for s, nm in ((-1, "left"), (1, "right")):
        x0, x1 = (BLOCK_X0, BLOCK_X1) if s > 0 else (-BLOCK_X1, -BLOCK_X0)
        blk = box(x0, x1, -10, 10, PLATE_TOP, H + 10).cut(cylx(SHAFT_R + 0.1, x0 - 1, x1 + 1, 0, H))
        add(drum_parts, f"hinge_block_{nm}", blk, BRASS)
    add(drum_parts, "encoder_AS5600_pcb", box(-121.0, -119.4, -11.5, 11.5, H - 11.5, H + 11.5), GREEN)
    add(drum_parts, "encoder_post", box(-121.0, -119.4, -4, 4, PLATE_TOP, H - 11.5), GREY)

    # controller on stand-offs, +Y side of the drum
    add(drum_parts, "controller_plate", box(-50, 50, 45, 108, 28, 30), GREEN)
    for i, (x, y) in enumerate(((-45, 50), (45, 50), (-45, 103), (45, 103))):
        add(drum_parts, f"standoff_{i + 1}", cylz(3, FLOOR_TOP, 28, x, y), GREY)
    add(drum_parts, "esp32_devkit", box(-47.5, 3.5, 76, 104, 30, 42), BLUE)
    add(drum_parts, "buck_converter", box(-43.5, -0.5, 49.5, 70.5, 30, 44), BLUE)
    add(drum_parts, "driver_TMC2209_az", box(18, 38, 50, 66, 30, 41), BLUE)
    add(drum_parts, "driver_TMC2209_tilt", box(18, 38, 82, 98, 30, 41), BLUE)

    # ============ tilting mirror (origin on the hinge axis, X = axis) ============
    fz0, fz1 = FRAME_Z0, FRAME_Z0 + FRAME_H
    zc = (fz0 + fz1) / 2
    frame = (box(-FRAME_W / 2, FRAME_W / 2, -5, 5, fz0, fz1)
             .cut(box(-97, 97, -6, 6, zc - 130.5, zc + 130.5))
             .cut(box(-100.2, 100.2, -6, 3, zc - MIR_H / 2 - 0.2, zc + MIR_H / 2 + 0.2)))
    add(mirror_parts, "mirror_frame", frame, FRAMEC)
    add(mirror_parts, "mirror_glass_4mm", box(-MIR_W / 2, MIR_W / 2, -1, 3, zc - MIR_H / 2, zc + MIR_H / 2), GLASS)
    add(mirror_parts, "mirror_backing_4mm", box(-MIR_W / 2, MIR_W / 2, -5, -1, zc - MIR_H / 2, zc + MIR_H / 2), DARKG)
    for s, nm in ((-1, "left"), (1, "right")):
        x0, x1 = (60.0, 80.0) if s > 0 else (-80.0, -60.0)
        lug = box(x0, x1, -8, 8, -8, FRAME_Z0).cut(cylx(SHAFT_R, x0 - 1, x1 + 1, 0, 0))
        add(mirror_parts, f"hinge_lug_{nm}", lug, BRASS)
    add(mirror_parts, "hinge_shaft_8mm", cylx(SHAFT_R, SHAFT_X0, SHAFT_X1), STEEL)
    sph = cylx(R_H - 3.0, SPR_X0, SPR_X1).cut(cylx(SHAFT_R, SPR_X0 - 1, SPR_X1 + 1))
    add(mirror_parts, "hinge_sprocket_32T", sph, ORANGE)
    add(mirror_parts, "encoder_magnet", cylx(3.0, SHAFT_X0 - 2.5, SHAFT_X0), RED)


# ------------------------------------------------------------------ posing, export, checks
def posed(az, tilt):
    """Return list of (name, shape, colour) in the world frame for the given pose."""
    out = []
    for nm, wp, col in base_parts:
        out.append((nm, _shape(wp), col))
    for nm, wp, col in drum_parts:
        out.append((nm, _shape(wp).rotate((0, 0, 0), (0, 0, 1), az), col))
    for nm, wp, col in mirror_parts:
        s = _shape(wp).rotate((0, 0, 0), (1, 0, 0), tilt).translate((0, 0, H)).rotate((0, 0, 0), (0, 0, 1), az)
        out.append((nm, s, col))
    return out


def cqc(hexs):
    h = hexs.lstrip("#")
    return cq.Color(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, 1.0)


def assemble(az, tilt):
    root = cq.Assembly(name="sun_mirror_hinge")
    base = cq.Assembly(name="base_fixed")
    for nm, wp, col in base_parts:
        base.add(wp, name=nm, color=cqc(col))
    root.add(base, name="base_fixed")
    drum = cq.Assembly(name="drum_rotating")
    for nm, wp, col in drum_parts:
        drum.add(wp, name=nm, color=cqc(col))
    mir = cq.Assembly(name="mirror_tilting")
    for nm, wp, col in mirror_parts:
        mir.add(wp, name=nm, color=cqc(col))
    drum.add(mir, name="mirror_tilting", loc=cq.Location(cq.Vector(0, 0, H), cq.Vector(1, 0, 0), tilt))
    root.add(drum, name="drum_rotating", loc=cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), az))
    return root


def clashes(parts, tol=2.0, skip=()):
    found = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _ in parts]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            a, b = bbs[i], bbs[j]
            if (a[2].xmax < b[2].xmin or b[2].xmax < a[2].xmin or a[2].ymax < b[2].ymin or b[2].ymax < a[2].ymin
                    or a[2].zmax < b[2].zmin or b[2].zmax < a[2].zmin):
                continue
            if (a[0], b[0]) in skip or (b[0], a[0]) in skip:
                continue
            try:
                v = a[1].intersect(b[1]).Volume()
            except Exception:
                v = -1
            if v > tol:
                found.append((a[0], b[0], v))
    return found


def render(parts, path, views, hide=()):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris, cols = [], []
    light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
    for nm, s, col in parts:
        if any(h in nm for h in hide):
            continue
        v, t = s.tessellate(0.6, 0.4)
        v = np.array([(p.x, p.y, p.z) for p in v])
        base = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        for a, b, c in t:
            tri = v[[a, b, c]]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            sh = 0.55 + 0.45 * abs(float(n @ light) / nn) if nn > 1e-9 else 0.8
            tris.append(tri); cols.append(np.clip(base * sh, 0, 1))
    fig = plt.figure(figsize=(8 * len(views), 8.5))
    for k, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(1, len(views), k + 1, projection="3d")
        pc = Poly3DCollection(tris, facecolors=cols, edgecolors="none")
        ax.add_collection3d(pc)
        r = 230
        ax.set_xlim(-r, r); ax.set_ylim(-r, r); ax.set_zlim(0, 2 * r)
        ax.set_box_aspect((1, 1, 1), zoom=1.45); ax.set_axis_off(); ax.view_init(elev, azim)
        ax.set_title(title, fontsize=12)
    fig.subplots_adjust(0.0, 0.0, 1.0, 0.94, wspace=0.0)
    fig.savefig(path, dpi=100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tilt", type=float, default=0.0, help="mirror normal elevation, deg (0 upright, +leans back)")
    ap.add_argument("--az", type=float, default=0.0, help="drum azimuth, deg")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    a = ap.parse_args()
    build()

    print(f"Hinge axis height H = {H:.1f} mm, chain centre distance {C_DIST:.1f} mm ({LINKS} links, {LINKS * P25:.0f} mm)")
    print(f"Pitch radii: 32T {R_H:.1f}, 16T {R_M:.1f}; plate top {PLATE_TOP:.0f}; overall height upright {H + FRAME_Z0 + FRAME_H:.0f} mm")
    hub_pitch, mot_pitch = HUB_T * GT_P / math.pi / 2, MOT_T * GT_P / math.pi / 2
    al = math.asin((hub_pitch - mot_pitch) / AZ_D)
    bl = 2 * math.sqrt(AZ_D ** 2 - (hub_pitch - mot_pitch) ** 2) + hub_pitch * (math.pi + 2 * al) + mot_pitch * (math.pi - 2 * al)
    print(f"Azimuth belt: about {bl:.0f} mm ({bl / GT_P:.0f} teeth), wrap on the 16T pulley {math.degrees(math.pi - 2 * al):.0f} deg, ratio {HUB_T / MOT_T:.0f}:1,"
          f" {360 / (200 * 16 * HUB_T / MOT_T):.4f} deg per 1/16 microstep")
    m_kg, d = 1.0, (FRAME_Z0 + (FRAME_H + FRAME_Z0)) / 2 / 1000
    tq = m_kg * 9.81 * d
    print(f"Gravity torque on the hinge with the mirror flat (1.0 kg assumed, CoG {d * 1000:.0f} mm out): {tq:.2f} N.m;"
          f" chain pull {tq / (R_H / 1000):.0f} N; torque at the gearbox {tq / 2:.2f} N.m")
    print(f"Stall chain pull at full motor current (about 4 N.m at the gearbox): {4.0 / (R_M / 1000):.0f} N. Limit the driver current and add a guard.")

    if a.check:
        for tilt in (0, 62, -62, 90, -90):
            p = posed(0, tilt)
            fixed = [x for x in p if x[0] in {n for n, _, _ in base_parts + drum_parts}]
            mov = [x for x in p if x[0] in {n for n, _, _ in mirror_parts}]
            skip = {("hinge_shaft_8mm", "encoder_AS5600_pcb")}
            bad = clashes(mov + fixed, skip=skip)
            bad = [b for b in bad if not (b[0] in {n for n, _, _ in mirror_parts} and b[1] in {n for n, _, _ in mirror_parts})]
            print(f"tilt {tilt:+d}: {len(bad)} mirror/base clashes", bad[:6])
        bad = clashes(posed(0, 0), tol=2.0)
        print("All-pairs clashes at upright:", len(bad))
        for b in bad:
            print("  ", b)
        return

    tag = "" if (a.tilt == 0 and a.az == 0) else f"-tilt{a.tilt:.0f}-az{a.az:.0f}"
    asm = assemble(a.az, a.tilt)
    asm.save(str(ASM / f"hinge-mirror-v1-exposed-assembly{tag}.step"))
    asm.save(str(ASM / f"hinge-mirror-v1-exposed-assembly{tag}.glb"))
    print("Wrote", ASM / f"hinge-mirror-v1-exposed-assembly{tag}.step")
    views = [(16, 52, "Upright (Sun on the horizon), seen from the front"), (16, 52, f"Tilted {a.tilt or 55:.0f} deg, drum turned 30 deg"),
             (90, -90, "Inside the drum from above (lid and mirror hidden)")]
    p0 = posed(a.az, a.tilt)
    p1 = posed(30.0, a.tilt or 55.0)
    import matplotlib
    matplotlib.use("Agg")
    render(p0, IMG / f"hinge-mirror-v1-exposed-preview{tag}.png", views[:1], hide=())
    render(p1, IMG / "hinge-mirror-v1-exposed-preview-tilted.png", views[1:2], hide=())
    render(posed(0, 0), IMG / "hinge-mirror-v1-exposed-preview-inside.png", views[2:], hide=("drum_top_plate", "mirror_", "hinge_", "tilt_chain", "encoder_", "drum_wall"))
    print("Wrote previews")


if __name__ == "__main__":
    main()
