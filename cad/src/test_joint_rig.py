#!/usr/bin/env python3
"""Parametric CAD for the single-joint test rig (belt reduction variant), CadQuery.

A NEMA 17 drives a 20-tooth pulley, a GT2 belt, and a 60-tooth printed pulley on an
8 mm output shaft held by two 608 bearings. A lever arm on the shaft carries weights,
so gravity loads the joint like the arm's shoulder will. A magnet on the back of the
shaft is read by an AS5600 board so we can see the true output angle.

Usage (from the repo root):
    python3 cad/src/test_joint_rig.py
Writes STL and STEP files to cad/out/hinge-mirror/archive/test-rig, an assembly (STEP and GLB, named and coloured
parts) and a preview PNG to cad/.

Coordinates: shaft axis along Y at the origin, X toward the motor, Z up, top of base plate at Z = 0.
All dimensions in mm. Drafted from standard part dimensions (NEMA 17 face 42.3 mm, 31 mm hole
spacing, 22 mm boss; 608 bearing 8x22x7; GT2 pitch 2 mm). Not yet printed or test-fitted:
check bearing, pulley, magnet and AS5600 board sizes against the parts you actually buy.
"""
from pathlib import Path

import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

CAD = Path(__file__).resolve().parent.parent
OUT = CAD / "out" / "hinge-mirror" / "archive"
STL = CAD / "out" / "hinge-mirror" / "archive" / "test-rig"
IMG = CAD / "media" / "test-rig"

# ---- parameters ----
AXIS_Z = 45.0                 # shaft height above the base plate
N_MOTOR, N_OUT = 20, 60       # pulley teeth (3:1 reduction)
PITCH = 2.0                   # GT2
PD_M, PD_O = N_MOTOR * PITCH / np.pi, N_OUT * PITCH / np.pi
BELT_LEN = 200.0              # closed loop, mm (a 200 mm size exists in the UK listings)
# centre distance from belt length, solved numerically below
TOL = 0.2                     # printing clearance

BASE_X0, BASE_X1, BASE_Y0, BASE_Y1, BASE_T = -50.0, 118.0, -60.0, 60.0, 6.0


def centre_distance():
    r1, r2 = PD_M / 2, PD_O / 2
    lo, hi = abs(r2 - r1) + 1, 200.0
    for _ in range(80):
        c = (lo + hi) / 2
        a = np.arcsin((r2 - r1) / c)
        length = 2 * c * np.cos(a) + (np.pi + 2 * a) * r2 + (np.pi - 2 * a) * r1
        lo, hi = (c, hi) if length < BELT_LEN else (lo, c)
    return (lo + hi) / 2


C = centre_distance()


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_y(r, y0, y1, x, z):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def cyl_z(r, z0, z1, x, y):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1)))


def slot_z(x, y, length, width, z0, z1):
    """Slot with its length along X."""
    r = width / 2
    s = box(x - length / 2, x + length / 2, y - r, y + r, z0, z1)
    return s.union(cyl_z(r, z0, z1, x - length / 2, y)).union(cyl_z(r, z0, z1, x + length / 2, y))


def base_plate():
    p = box(BASE_X0, BASE_X1, BASE_Y0, BASE_Y1, -BASE_T, 0)
    for x in (BASE_X0 + 8, BASE_X1 - 8):
        for y in (BASE_Y0 + 8, BASE_Y1 - 8):
            p = p.cut(cyl_z(2.3, -BASE_T - 1, 1, x, y))        # M4 clamp holes
    for y in (18.0, 30.0):                                      # tension slots for the motor bracket
        p = p.cut(slot_z(C, y, 16.0, 4.6, -BASE_T - 1, 1))
    for x in (-25.0, 25.0):                                     # bearing block bolts
        for y in (-12.0, 12.0):
            p = p.cut(cyl_z(2.3, -BASE_T - 1, 1, x, y))
    return p


def bearing_block():
    b = box(-29, 29, -18, 18, 0, 5).union(box(-20, 20, -18, 18, 0, AXIS_Z + 18))
    for x in (-25.0, 25.0):
        for y in (-12.0, 12.0):
            b = b.cut(cyl_z(2.3, -1, 6, x, y))
    b = b.cut(cyl_y(4.6, -19, 19, 0, AXIS_Z))                    # shaft clearance
    b = b.cut(cyl_y(11.0 + TOL / 2 + 0.05, -19, -18 + 7.2, 0, AXIS_Z))   # 608 pocket, rear
    b = b.cut(cyl_y(11.0 + TOL / 2 + 0.05, 18 - 7.2, 19, 0, AXIS_Z))     # 608 pocket, front
    # two screw holes to attach the encoder bracket on the rear face
    for x in (-12.0, 12.0):
        b = b.cut(cyl_y(1.5, -19, -10, x, AXIS_Z + 12))
    return b


def motor_bracket():
    yf = 8.0                                                     # motor face plane
    m = box(C - 29.5, C + 29.5, yf, yf + 6, 0, AXIS_Z + 25)      # vertical plate
    m = m.union(box(C - 29.5, C + 29.5, yf, yf + 36, 0, 5))      # foot with slots
    m = m.union(box(C - 29.5, C - 24, yf, yf + 36, 0, 24))           # low rib on the belt side (belt passes above it)
    m = m.union(box(C + 24, C + 29.5, yf, yf + 36, 0, AXIS_Z + 25))     # tall rib on the far side
    m = m.cut(cyl_y(11.3, yf - 1, yf + 7, C, AXIS_Z))            # 22 mm pilot boss
    for dx in (-15.5, 15.5):
        for dz in (-15.5, 15.5):
            m = m.cut(cyl_y(1.7, yf - 1, yf + 7, C + dx, AXIS_Z + dz))   # M3 motor holes
    for y in (18.0, 30.0):
        m = m.cut(slot_z(C, y, 16.0, 4.6, -1, 6))                # same slots as the plate, for bolts
    return m


def gt2_profile(n, y0, y1, cx, cz):
    """Approximate GT2 toothed profile (rounded trapezoids), extruded along Y. Tune on first print."""
    pd = n * PITCH / np.pi
    r_tip = pd / 2 - 0.38
    r_root = r_tip - 0.75
    pts = []
    steps = 12
    for i in range(n * steps):
        t = (i % steps) / steps
        # tooth: flat tip for 40 percent, ramps for 10 percent each, root for 40 percent
        if t < 0.4:
            r = r_tip
        elif t < 0.5:
            r = r_tip - (t - 0.4) / 0.1 * 0.75
        elif t < 0.9:
            r = r_root
        else:
            r = r_root + (t - 0.9) / 0.1 * 0.75
        th = 2 * np.pi * i / (n * steps)
        pts.append((cx + r * np.cos(th), cz + r * np.sin(th)))
    return cq.Workplane("XZ", origin=(0, y1, 0)).polyline(pts).close().extrude(y1 - y0)


def output_pulley():
    y0, y1 = 22.0, 29.5
    p = gt2_profile(N_OUT, y0, y1, 0, AXIS_Z)
    r_fl = PD_O / 2 + 1.5
    p = p.union(cyl_y(r_fl, y0 - 1.2, y0, 0, AXIS_Z)).union(cyl_y(r_fl, y1, y1 + 1.2, 0, AXIS_Z))
    p = p.union(cyl_y(9.0, y1 + 1.2, y1 + 10.2, 0, AXIS_Z))     # hub
    p = p.cut(cyl_y(4.0 + TOL / 2, y0 - 2, y1 + 11, 0, AXIS_Z))  # 8 mm bore
    # M3 grub screw from the top, nut pocket opening to the +X side so the nut can be slid in
    yh = y1 + 5.7
    p = p.cut(cyl_z(1.6, AXIS_Z, AXIS_Z + 10, 0, yh))
    p = p.cut(box(0, 10, yh - 2.9, yh + 2.9, AXIS_Z + 5.0, AXIS_Z + 7.6))
    return p


def lever_arm():
    y0, y1 = 42.0, 52.0
    a = cyl_y(10.0, y0, y1, 0, AXIS_Z)                           # hub
    a = a.union(box(-150, 0, y0 + 2, y0 + 8, AXIS_Z - 6, AXIS_Z + 6))   # arm toward -X
    a = a.cut(cyl_y(4.0 + TOL / 2, y0 - 1, y1 + 1, 0, AXIS_Z))
    ym = (y0 + y1) / 2
    a = a.cut(cyl_z(1.6, AXIS_Z, AXIS_Z + 12, 0, ym))                    # grub screw from the top
    a = a.cut(box(0, 11, ym - 2.9, ym + 2.9, AXIS_Z + 5.0, AXIS_Z + 7.6))  # nut pocket, open to +X
    for r in (30, 50, 75, 100, 125, 145):                        # weight holes, mm from the axis
        a = a.cut(cyl_y(2.2, y0, y1, -r, AXIS_Z))
    return a


def encoder_bracket():
    # two arms from the rear face of the bearing block, cross plate with a pocket for the AS5600 board
    yb, yt = -18.0, -41.0
    e = box(-16, 16, yt, yt + 5, AXIS_Z - 16, AXIS_Z + 16)       # cross plate
    for x in (-12.0, 12.0):
        e = e.union(box(x - 3, x + 3, yt, yb, AXIS_Z + 9, AXIS_Z + 15))   # arms
        e = e.cut(cyl_y(1.7, yt - 1, yb + 1, x, AXIS_Z + 12))
    e = e.cut(box(-11.8, 11.8, yt + 3.0, yt + 5.1, AXIS_Z - 11.8, AXIS_Z + 11.8))   # 23.6 mm board pocket
    e = e.cut(cyl_y(8.0, yt - 1, yt + 6, 0, AXIS_Z))             # sensor window
    return e


def belt(y0=22.75, y1=28.75, thickness=1.4):
    """Closed GT2 belt loop around both pulleys (simple band, no teeth drawn)."""
    r_big, r_small = PD_O / 2, PD_M / 2

    def hull(rb, rs):
        phi = np.arcsin((rb - rs) / C)
        nu = (np.sin(phi), np.cos(phi))
        nl = (np.sin(phi), -np.cos(phi))
        pts = [(rb * nu[0], AXIS_Z + rb * nu[1]), (C + rs * nu[0], AXIS_Z + rs * nu[1]),
               (C + rs * nl[0], AXIS_Z + rs * nl[1]), (rb * nl[0], AXIS_Z + rb * nl[1])]
        prism = cq.Workplane("XZ", origin=(0, y1, 0)).polyline(pts).close().extrude(y1 - y0)
        return cyl_y(rb, y0, y1, 0, AXIS_Z).union(cyl_y(rs, y0, y1, C, AXIS_Z)).union(prism)

    tip = -0.38      # belt sits on the tooth tips of the pulleys
    return hull(r_big + tip + thickness, r_small + tip + thickness).cut(
        hull(r_big + tip, r_small + tip))


def reference_parts():
    """Bought parts, drawn only so the preview shows how it fits together."""
    ref = {}
    yf = 8.0
    ref["ref_motor"] = box(C - 21.15, C + 21.15, yf - 34, yf, AXIS_Z - 21.15, AXIS_Z + 21.15) \
        .union(cyl_y(2.5, yf, yf + 24, C, AXIS_Z))
    ref["ref_shaft_8mm"] = cyl_y(4.0, -31.0, 54.0, 0, AXIS_Z)
    ref["ref_pulley20"] = cyl_y(PD_M / 2 - 0.4, 22.0, 29.5, C, AXIS_Z)
    ref["ref_belt"] = belt()
    ref["ref_magnet"] = cyl_y(3.0, -33.5, -31.0, 0, AXIS_Z)
    ref["ref_bearing_rear"] = cyl_y(11.0, -18.0, -11.0, 0, AXIS_Z).cut(cyl_y(4.0, -19, -10, 0, AXIS_Z))
    ref["ref_bearing_front"] = cyl_y(11.0, 11.0, 18.0, 0, AXIS_Z).cut(cyl_y(4.0, 10, 19, 0, AXIS_Z))
    return ref


def tessellate(wp, tol=0.4):
    verts, tris = wp.val().tessellate(tol)
    v = np.array([(p.x, p.y, p.z) for p in verts])
    return v, np.array(tris)


def preview(parts, refs, path):
    colours = {"base_plate": "#c9c9c9", "bearing_block": "#4a6fa5", "motor_bracket": "#4a6fa5",
               "output_pulley_60T": "#e8a400", "lever_arm": "#2a9d8f", "encoder_bracket": "#8d6bb3"}
    fig = plt.figure(figsize=(13, 6))
    for k, (elev, azim, title) in enumerate([(25, -50, "Assembly (bought parts in grey, belt dark)"),
                                              (89, -90, "Plan view")]):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        for name, wp in list(parts.items()) + list(refs.items()):
            v, t = tessellate(wp)
            col = colours.get(name, "#555555")
            alpha = 0.95 if name in colours else 0.35
            ax.add_collection3d(Poly3DCollection(v[t], facecolor=col, edgecolor="none", alpha=alpha))
        ax.set_xlim(-150, 120); ax.set_ylim(-60, 60); ax.set_zlim(-6, 130)
        ax.set_box_aspect((270, 120, 136))
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title)
        ax.set_xlabel("X"); ax.set_ylabel("Y")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def build_assembly(parts, refs):
    """Named, coloured assembly: printed parts in colour, bought parts in grey."""
    colours = {"base_plate": (0.78, 0.78, 0.78), "bearing_block": (0.29, 0.44, 0.65),
               "motor_bracket": (0.29, 0.44, 0.65), "output_pulley_60T": (0.91, 0.64, 0.0),
               "lever_arm": (0.16, 0.62, 0.56), "encoder_bracket": (0.55, 0.42, 0.70)}
    asm = cq.Assembly(name="test_joint_rig")
    for name, wp in parts.items():
        asm.add(wp, name=name, color=cq.Color(*colours.get(name, (0.5, 0.5, 0.5))))
    for name, wp in refs.items():
        col = (0.08, 0.08, 0.08) if name == "ref_belt" else (0.35, 0.35, 0.38)
        asm.add(wp, name=name, color=cq.Color(*col))
    return asm


def main():
    STL.mkdir(parents=True, exist_ok=True)
    parts = {
        "base_plate": base_plate(),
        "bearing_block": bearing_block(),
        "motor_bracket": motor_bracket(),
        "output_pulley_60T": output_pulley(),
        "lever_arm": lever_arm(),
        "encoder_bracket": encoder_bracket(),
    }
    for name, wp in parts.items():
        cq.exporters.export(wp, str(STL / f"rig_{name}.stl"))
        cq.exporters.export(wp, str(STL / f"rig_{name}.step"))
    refs = reference_parts()
    asm = build_assembly(parts, refs)
    OUT.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    asm.save(str(OUT / "test_joint_rig_assembly.step"))
    asm.save(str(OUT / "test_joint_rig_assembly.glb"))
    preview(parts, refs, IMG / "test-rig-preview.png")
    print(f"Pulley pitch diameters: motor {PD_M:.2f} mm, output {PD_O:.2f} mm, ratio {N_OUT / N_MOTOR:.1f}:1")
    phi = np.arcsin((PD_O - PD_M) / 2 / C)
    pitch_len = 2 * C * np.cos(phi) + (np.pi + 2 * phi) * PD_O / 2 + (np.pi - 2 * phi) * PD_M / 2
    print(f"Belt pitch length check: {pitch_len:.1f} mm ({pitch_len / PITCH:.0f} teeth)")
    print(f"Centre distance for a {BELT_LEN:.0f} mm belt: {C:.1f} mm (motor slots allow plus or minus 8 mm)")
    print("Wrote", ", ".join(f"rig_{n}.stl" for n in parts))


if __name__ == "__main__":
    main()
