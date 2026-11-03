#!/usr/bin/env python3
"""To-scale concept drawing: goal-post mount for a 20 cm (200 mm) mirror.

A round platform turns for azimuth. Two uprights (the goal post) stand on it either side of the mirror. A
separate horizontal axle runs through the mirror's centre and turns in bearings at the top of the uprights.
A 60-tooth pulley on the axle, between the mirror edge and one upright, is driven by a belt that runs down
inside that (hollow) upright to a 20-tooth pulley on a NEMA 17 + 10:1 gearbox (StepperOnline MG17 class) lying
in the rotating drum under the platform. A slip ring under the hub feeds the rotating parts. The azimuth motor
is fixed in the base and drives the hub through a second belt.

Known dimensions: mirror 200 mm (owner), NEMA 17 42.3 x 42.3 x 34 mm, MG17-G10 gearbox 42 x 42 x 40 mm with an
8 mm output shaft 21.5 mm long, GT2 pulley pitch diameters (20T 12.7 mm, 60T 38.2 mm). Everything else (platform,
drum, base, uprights, bearing ring size, belt lengths, slip ring length) is a draft sizing for a concept only.
No strength, stiffness or clearance analysis has been done.

Usage (from the repo root): python3 cad/src/goalpost_to_scale.py
Writes cad/media/earlier-concepts/goalpost-to-scale.png
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

MIN = "--minimal" in sys.argv           # thin rods for uprights, exposed metal chain (implies the slim base)
OUTSIDE = "--outside" in sys.argv         # with --airy: sprocket and chain outside the right-hand rod
FLUSH = "--flush" in sys.argv           # base top level with the platform top
AIRY = "--airy" in sys.argv             # with --minimal: more space round the mirror, smoother chain (32T / 16T)
SMALLTOP = "--smalltop" in sys.argv     # with --minimal: small sprocket on the exposed axle end, bigger one with the motor
SLIM = "--slim" in sys.argv or MIN or AIRY
MIN = MIN or AIRY
OUT = Path(__file__).resolve().parent.parent / "media" / "earlier-concepts" / ("goalpost-to-scale-airy-outside-flush.png" if (AIRY and OUTSIDE and FLUSH) else "goalpost-to-scale-airy.png" if AIRY else "goalpost-to-scale-smalltop.png" if (MIN and SMALLTOP) else "goalpost-to-scale-minimal.png" if MIN else "goalpost-to-scale-slim.png" if SLIM else "goalpost-to-scale.png")
STEEL, STEEL_E = "#cfd6dc", "#6b7780"
BLUE, ORANGE, DARK, GREY, PURPLE = "#4a6fa5", "#e8a400", "#3a3a3a", "#b8b8b8", "#6a4f9c"
LIGHT = "#dbe6f4"

# ---- draft layout (mm) ----
R_DISC = 100.0
BASE_R, BASE_H = 180.0, 100.0           # fixed base: 360 mm across
BEAR_R = 130.0                          # turntable bearing ring radius (260 mm across, to be sized)
DRUM_R, DRUM_Z0, DRUM_Z1 = 175.0, 106.0, 150.0
PLAT_Z0, PLAT_Z1, PLAT_R = 150.0, 158.0, 170.0
UP_X0, UP_X1, UP_D = 110.0, 150.0, 20.0  # upright inner and outer faces (x), depth (y)
ZC = PLAT_Z1 + R_DISC + 40.0            # axle height
UP_TOP = ZC + 30.0
BELT_X = 118.0                          # belt plane (x), between mirror edge and upright outer face
PD20, PD60 = 20 * 2 / np.pi, 60 * 2 / np.pi
ZM = 128.0                              # tilt motor axis height (centre of the drum)
MOT_L, MOT_W, GB_L = 34.0, 42.3, 40.0
if SLIM:
    # both motors lie on their sides in the same 42 mm band (z 17 to 59). The tilt motor is in the rotating drum; the
    # azimuth motor is fixed outside the drum, under the platform's overhang, with a small bevel pinion meshing a crown
    # gear ring fixed to the platform's underside. Platform underside is at z 60.
    BASE_R, BASE_H = 185.0, 60.0
    BEAR_R = 115.0
    DRUM_R, DRUM_Z0, DRUM_Z1 = 128.0, 14.0, 60.0
    PLAT_Z0, PLAT_Z1, PLAT_R = 60.0, 68.0, 170.0
    BELT_X = 114.0
    ZM = 38.0
    ZC = PLAT_Z1 + R_DISC + 40.0
    UP_TOP = ZC + 30.0
if MIN:
    # thin round rods for the uprights; the axle turns in bronze bushings in the rod tops; a stainless roller chain
    # (ANSI 25, 6.35 mm pitch) runs OUTSIDE the right rod from a 36-tooth sprocket on the axle end down to a 12-tooth
    # sprocket on the tilt gearbox shaft (3:1), through a slot in the platform.
    ROD_D, ROD_X = 10.0, 109.0
    ROD_TOP = ZC + 14.0
    BELT_X = 120.0
    DRUM_R = 132.0
    PLAT_R = 160.0
    CHAIN_P = 6.35
    N_TOP, N_BOT = (10, 20) if SMALLTOP else (36, 12)      # axle sprocket, motor sprocket (teeth)
    CHAIN_INSIDE = False
    if AIRY:
        # owner wants the mirror to float clear: 50 mm each side to the rods, 100 mm above the platform, bigger
        # sprockets for smoothness. The chain then runs in the gap between the mirror and the right-hand rod.
        GAP_SIDE, GAP_BELOW = 50.0, 100.0
        ROD_X = R_DISC + GAP_SIDE + ROD_D / 2
        ZC = PLAT_Z1 + R_DISC + GAP_BELOW
        UP_TOP = ZC + 30.0
        ROD_TOP = ZC + 14.0
        N_TOP, N_BOT = 32, 16
        CHAIN_INSIDE = True
        BELT_X = ROD_X - 16.0
        DRUM_R, BEAR_R, PLAT_R, BASE_R = 156.0, 140.0, 180.0, 212.0
    CROWN_R = 166.0 if AIRY else 142.0   # crown gear mesh radius
    PD_TOP = CHAIN_P / np.sin(np.pi / N_TOP)
    PD_BOT = CHAIN_P / np.sin(np.pi / N_BOT)
    if AIRY and OUTSIDE:
        CHAIN_INSIDE = False
        BELT_X = ROD_X + ROD_D / 2 + 8.0              # outside the right-hand rod
        DRUM_R = BELT_X + 14.0                         # drum must contain the gearbox shaft and sprocket
        CROWN_R = DRUM_R + 10.0
        PLAT_R = CROWN_R + 8.0
        BASE_R = CROWN_R + 6.0 + MOT_L + 8.0
        BEAR_R = ROD_X
    if FLUSH:
        BASE_H = PLAT_Z1                               # fixed base top level with the platform top


def rect(ax, x0, y0, w, h, fc, ec="black", lw=0.8, z=2, alpha=1.0, ls="-"):
    ax.add_patch(Rectangle((x0, y0), w, h, facecolor=fc, edgecolor=ec, lw=lw, zorder=z, alpha=alpha, ls=ls))


def note(ax, text, xy, xytext, ha="left", fs=8.5):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, ha=ha, va="center", zorder=20,
                arrowprops=dict(arrowstyle="-", color="black", lw=0.7),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.6"))


def dim(ax, p0, p1, text, off=(0, 0), fs=9, rot=0):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.1), zorder=15)
    ax.text((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1], text, color="#c0392b", fontsize=fs,
            ha="center", va="center", rotation=rot, zorder=16,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))


def num(ax, n, x, y):
    ax.text(x, y, str(n), fontsize=9, ha="center", va="center", zorder=25, color="white", fontweight="bold",
            bbox=dict(boxstyle="circle,pad=0.25", fc="#c0392b", ec="none"))


def scale_bar(ax, x, y, length=100):
    ax.plot([x, x + length], [y, y], color="black", lw=3, zorder=20)
    ax.text(x + length / 2, y + 8, f"{length} mm", ha="center", fontsize=8.5)


def belt_length(c, r1, r2):
    phi = np.arcsin((r2 - r1) / c)
    return 2 * c * np.cos(phi) + (np.pi + 2 * phi) * r2 + (np.pi - 2 * phi) * r1


def belt_poly(ax, zc_big, zc_small, r_big, r_small, thick=1.4, alpha=1.0, z=9):
    """Belt loop between a big and a small pulley stacked vertically (centres on x = 0 in this view)."""
    tip = -0.38
    for rb, rs, fc in ((r_big + tip + thick, r_small + tip + thick, DARK),):
        c = zc_big - zc_small
        phi = np.arcsin((rb - rs) / c)
        pts = [(rb * np.cos(phi), zc_big - rb * np.sin(phi)), (rs * np.cos(phi), zc_small - rs * np.sin(phi))]
        for sgn in (1, -1):
            ax.plot([sgn * pts[0][0], sgn * pts[1][0]], [pts[0][1], pts[1][1]], color=DARK, lw=2.2, zorder=z, alpha=alpha)
        for (cz, r) in ((zc_big, rb), (zc_small, rs)):
            ax.add_patch(Circle((0, cz), r, fill=False, edgecolor=DARK, lw=2.2, zorder=z, alpha=alpha))


def front(ax):
    ax.set_title("Front view (looking along the axle's side), to scale", fontsize=11)
    rect(ax, -250, -22, 500, 22, "#d8b48c", ec="#8b6b4a")                                    # table
    rect(ax, -BASE_R, 0, 2 * BASE_R, BASE_H, "#d6d6d6", lw=1.5)                              # fixed base
    if not SLIM:
        rect(ax, -DRUM_R, DRUM_Z0, 2 * DRUM_R, DRUM_Z1 - DRUM_Z0, "#e6e6e6", lw=1.5)
    rect(ax, -PLAT_R, PLAT_Z0, 2 * PLAT_R, PLAT_Z1 - PLAT_Z0, "#bfc7d1", lw=1.5, z=3)        # platform
    for s in (-1, 1):                                                                        # uprights
        x0 = UP_X0 if s > 0 else -UP_X1
        rect(ax, x0, PLAT_Z1, UP_X1 - UP_X0, UP_TOP - PLAT_Z1, LIGHT, lw=1.2, z=4)
    ax.add_patch(Circle((0, ZC), R_DISC, facecolor=STEEL, edgecolor=STEEL_E, lw=2.5, zorder=6))
    ax.add_patch(Circle((-30, ZC + 35), 48, facecolor="white", edgecolor="none", alpha=0.35, zorder=7))
    rect(ax, -158, ZC - 4, 316, 8, DARK, z=8)                                                # axle
    rect(ax, BELT_X - 4, ZC - PD60 / 2, 8, PD60, ORANGE, z=9)                                # axle pulley
    ax.plot([BELT_X, BELT_X], [ZM, ZC], color=DARK, lw=1.5, ls=":", zorder=10)               # hidden belt
    ax.plot(0, ZC, "o", color="black", ms=4, zorder=11)
    dim(ax, (-R_DISC, ZC + R_DISC + 22), (R_DISC, ZC + R_DISC + 22), "mirror 200 mm", off=(0, 12))
    dim(ax, (-215, 0), (-215, ZC + R_DISC), f"{ZC + R_DISC:.0f} mm overall", off=(-20, 0), rot=90)
    dim(ax, (-196, 0), (-196, ZC), f"axle {ZC:.0f}", off=(-16, 0), rot=90, fs=8)
    dim(ax, (-PLAT_R, PLAT_Z0 - 6), (PLAT_R, PLAT_Z0 - 6), "platform 340 mm", off=(0, -10), fs=8)
    dim(ax, (-UP_X0, UP_TOP + 18), (UP_X0, UP_TOP + 18), "uprights 220 mm apart (inner faces)", off=(0, 10), fs=8)
    note(ax, "belt hidden inside the\nright upright (dotted)", (BELT_X + 2, ZC - 60), (235, ZC - 5))
    note(ax, "axle through the mirror's centre,\nturning in bearings in the uprights", (-140, ZC + 4), (-250, ZC + 70), ha="left")
    note(ax, "rotating platform (azimuth)", (120, PLAT_Z1 - 4), (205, 120), ha="left")
    note(ax, "fixed base: azimuth motor,\nslip ring, ballast", (150, 30), (205, 50))
    scale_bar(ax, 100, -50, 100)
    ax.set_xlim(-255, 330); ax.set_ylim(-60, ZC + R_DISC + 50); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def side(ax):
    c = ZC - ZM
    L = belt_length(c, PD20 / 2, PD60 / 2)
    ax.set_title("Side view along the axle, to scale", fontsize=11)
    rect(ax, -250, -22, 500, 22, "#d8b48c", ec="#8b6b4a")
    rect(ax, -BASE_R, 0, 2 * BASE_R, BASE_H, "#d6d6d6", lw=1.5)
    if not SLIM:
        rect(ax, -DRUM_R, DRUM_Z0, 2 * DRUM_R, DRUM_Z1 - DRUM_Z0, "#e6e6e6", lw=1.5)
    rect(ax, -PLAT_R, PLAT_Z0, 2 * PLAT_R, PLAT_Z1 - PLAT_Z0, "#bfc7d1", lw=1.5, z=3)
    rect(ax, -MOT_W / 2, ZM - MOT_W / 2, MOT_W, MOT_W, DARK, z=4)                           # motor + gearbox end on
    rect(ax, -UP_D / 2, PLAT_Z1, UP_D, UP_TOP - PLAT_Z1, LIGHT, lw=1.2, z=5, alpha=0.35)     # see-through upright
    ang = np.radians(35)                                                                      # disc edge-on, tilted
    for a, al in ((ang, 1.0), (-np.radians(40), 0.35)):
        ax.plot([-R_DISC * np.sin(a), R_DISC * np.sin(a)], [ZC - R_DISC * np.cos(a), ZC + R_DISC * np.cos(a)],
                color=STEEL_E, lw=8, alpha=al, solid_capstyle="butt", zorder=6)
    belt_poly(ax, ZC, ZM, PD60 / 2, PD20 / 2)
    ax.add_patch(Circle((0, ZC), PD60 / 2 - 1, facecolor=ORANGE, edgecolor="black", lw=0.8, zorder=10, alpha=0.8))
    ax.add_patch(Circle((0, ZM), PD20 / 2 - 0.5, facecolor=ORANGE, edgecolor="black", lw=0.8, zorder=10))
    ax.plot(0, ZC, "o", color="black", ms=4, zorder=12)
    dim(ax, (60, ZM), (60, ZC), f"belt centres {c:.0f} mm", off=(26, 0), rot=90, fs=8)
    note(ax, f"belt loop about {L:.0f} mm (20T to 60T, 3:1)", (3, (ZC + ZM) / 2), (95, 205), fs=8)
    note(ax, "motor + gearbox lying along the axle\n(seen end on, 42 x 42 mm)", (MOT_W / 2 - 2, ZM + 12), (92, 130), fs=8)
    note(ax, "mirror seen edge on, two tilts\n(it can turn all the way round)", (R_DISC * np.sin(ang) * 0.8, ZC + R_DISC * np.cos(ang) * 0.8),
         (-170, ZC + 70), ha="right", fs=8)
    note(ax, "upright (shown see-through)", (UP_D / 2, UP_TOP - 25), (-125, UP_TOP + 20), ha="right", fs=8)
    scale_bar(ax, -240, -50, 100)
    ax.set_xlim(-250, 250); ax.set_ylim(-60, ZC + R_DISC + 50); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    print(f"Tilt belt: centres {c:.0f} mm, loop length about {L:.0f} mm")


def base(ax):
    ax.set_title("Base cutaway, to scale", fontsize=11)
    rect(ax, -BASE_R, 0, 2 * BASE_R, BASE_H, "#ececec", lw=1.5, z=1)
    rect(ax, -170, 0, 340, 12, "#8a8a8a", z=1)                                               # ballast
    rect(ax, -DRUM_R, DRUM_Z0, 2 * DRUM_R, DRUM_Z1 - DRUM_Z0, "#f4f4f4", lw=1.5, z=1)        # drum
    rect(ax, -PLAT_R, PLAT_Z0, 2 * PLAT_R, PLAT_Z1 - PLAT_Z0, "#bfc7d1", lw=1.5, z=3)
    for s in (-1, 1):
        rect(ax, s * BEAR_R - 7 if s > 0 else -BEAR_R - 7, BASE_H, 14, 6, GREY, z=3)         # turntable bearing ring
        x0 = UP_X0 if s > 0 else -UP_X1
        rect(ax, x0, PLAT_Z1, UP_X1 - UP_X0, 20, LIGHT, lw=1.0, z=4)                          # upright feet
    # hub, slip ring, hub pulley
    rect(ax, -11, 12, 22, 34, PURPLE, z=3)                                                    # slip ring (length draft)
    rect(ax, -15, 46, 30, DRUM_Z0 - 46 + 2, BLUE, z=3)                                        # hub shaft
    rect(ax, -28.6, 86, 57.2, 7, BLUE, z=4)                                                   # hub pulley (90T class)
    ax.plot([0, 0], [46, DRUM_Z1 - 6], color=PURPLE, lw=1.5, ls=":", zorder=6)               # wires up the hub
    # azimuth motor + gearbox, vertical, fixed
    xa = 95.0
    rect(ax, xa - MOT_W / 2, 8, MOT_W, MOT_L, DARK, z=3)
    rect(ax, xa - MOT_W / 2, 8 + MOT_L, MOT_W, GB_L, ORANGE, z=3)
    rect(ax, xa - 6.4, 8 + MOT_L + GB_L, 12.7, 8, BLUE, z=4)                                   # 20T pulley
    ax.plot([28.6, xa - 6.4], [89.5, 89.5], color=DARK, lw=2.2, zorder=5)
    # tilt motor + gearbox lying along x in the drum, pulley at x = BELT_X
    xf = BELT_X - 10.0                                                                         # gearbox front face
    rect(ax, xf - GB_L, ZM - MOT_W / 2, GB_L, MOT_W, ORANGE, z=3)
    rect(ax, xf - GB_L - MOT_L, ZM - MOT_W / 2, MOT_L, MOT_W, DARK, z=3)
    rect(ax, xf, ZM - 4, 21.5, 8, "#9a9a9a", z=4)                                              # output shaft
    rect(ax, BELT_X - 4, ZM - PD20 / 2, 8, PD20, BLUE, z=5)                                    # 20T pulley
    ax.plot([BELT_X, BELT_X], [ZM + 8, PLAT_Z1 + 20], color=DARK, lw=2.2, zorder=6)           # belt up
    rect(ax, BELT_X - 6, PLAT_Z0, 12, 8, "white", ec="none", z=3.5)                           # slot in the platform
    # controller on the drum
    rect(ax, -150, 112, 80, 34, "#8fbf8f", z=3)
    ax.text(-110, 129, "controller\nand drivers", ha="center", va="center", fontsize=8, zorder=5)
    # labels
    num(ax, 1, 150, 154); num(ax, 2, -165, 128); num(ax, 3, xf - GB_L / 2, ZM); num(ax, 4, -110, 150)
    num(ax, 5, BELT_X + 14, 175); num(ax, 6, 22, 28); num(ax, 7, xa, 30); num(ax, 8, 55, 98)
    num(ax, 9, BEAR_R + 9, BASE_H + 3); num(ax, 10, -150, 6)
    legend = ("1  platform, turns for azimuth (340 mm)\n"
              "2  rotating drum under it (holds the tilt drive)\n"
              "3  tilt NEMA 17 + 10:1 gearbox, lying along the axle\n"
              "4  controller and drivers ride on the drum\n"
              "5  belt up to the axle, hidden in the right upright\n"
              "6  slip ring: stator fixed, rotor turns with the hub\n"
              "7  azimuth NEMA 17 + gearbox, vertical, fixed\n"
              "8  belt from the motor to the hub pulley\n"
              "9  turntable bearing ring (about 260 mm, to be sized)\n"
              "10 ballast plate")
    ax.text(-190, -12, legend, fontsize=8, va="top", ha="left", linespacing=1.45,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.6"))
    scale_bar(ax, 80, -40, 100)
    ax.set_xlim(-195, 215); ax.set_ylim(-175, 200); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def base_slim(ax):
    ax.set_title("Base cutaway: both motors on their sides in one 42 mm band, to scale", fontsize=11)
    rect(ax, -BASE_R, 0, 2 * BASE_R, BASE_H, "#ececec", lw=1.5, z=1)                           # fixed skirt (cut away)
    rect(ax, -BASE_R + 6, 0, 2 * BASE_R - 12, 8, "#8a8a8a", z=2)                               # base plate and ballast
    rect(ax, -PLAT_R, PLAT_Z0, 2 * PLAT_R, PLAT_Z1 - PLAT_Z0, "#bfc7d1", lw=1.5, z=3)          # platform
    rect(ax, -DRUM_R, DRUM_Z0, 2 * DRUM_R, 3, "#9a9a9a", z=3)                                  # drum floor
    for s_ in (-1, 1):
        rect(ax, s_ * (DRUM_R) - (3 if s_ > 0 else -0), DRUM_Z0, 3, DRUM_Z1 - DRUM_Z0, "#9a9a9a", z=3)   # drum wall
        rect(ax, s_ * BEAR_R - 7, 8, 14, 6, GREY, z=3)                                          # turntable bearing ring
        rect(ax, s_ * 138 - 6 if s_ > 0 else -138 - 6, 48, 12, 12, ORANGE, z=4)                  # crown gear ring (teeth down)
        x0 = UP_X0 if s_ > 0 else -UP_X1
        rect(ax, x0, PLAT_Z1, UP_X1 - UP_X0, 20, LIGHT, lw=1.0, z=4)                             # upright feet
    # slip ring in the centre: stator fixed to the plate, rotor stub up to the platform
    rect(ax, -11, 8, 22, 34, PURPLE, z=3)
    rect(ax, -4, 42, 8, 18, BLUE, z=3)
    # tilt motor + gearbox lying along the axle in the rotating drum
    xf = BELT_X - 10.0
    rect(ax, xf - GB_L, ZM - MOT_W / 2, GB_L, MOT_W, ORANGE, z=3)
    rect(ax, xf - GB_L - MOT_L, ZM - MOT_W / 2, MOT_L, MOT_W, DARK, z=3)
    rect(ax, xf, ZM - 4, 21.5, 8, "#9a9a9a", z=4)
    rect(ax, BELT_X - 4, ZM - PD20 / 2, 8, PD20, BLUE, z=5)
    ax.plot([BELT_X, BELT_X], [ZM + 8, PLAT_Z1 + 20], color=DARK, lw=2.2, zorder=6)
    rect(ax, BELT_X - 6, PLAT_Z0, 12, 8, "white", ec="none", z=3.5)
    # azimuth motor lying radially outside the drum, under the platform overhang, bevel pinion meshing the crown ring
    rect(ax, 138 + 6, 8, MOT_L + 4, 9, "#9a9a9a", z=3)                                         # mount block
    rect(ax, 144, ZM - MOT_W / 2, MOT_L, MOT_W, DARK, z=3)                                      # azimuth NEMA 17 (no gearbox)
    rect(ax, 130, 28, 14, 20, "#f4c542", z=5)                                                   # bevel pinion (20 mm)
    # controller on the drum
    rect(ax, -118, 20, 76, 36, "#8fbf8f", z=3)
    ax.text(-80, 38, "controller\nand drivers", ha="center", va="center", fontsize=8, zorder=5)
    num(ax, 1, -120, 64); num(ax, 2, -140, 38); num(ax, 3, xf - GB_L / 2, ZM); num(ax, 4, -80, 62)
    num(ax, 5, BELT_X + 12, 90); num(ax, 6, 22, 24); num(ax, 7, 161, ZM); num(ax, 8, 138, 70)
    num(ax, 9, BEAR_R + 12, 11); num(ax, 10, -150, 4)
    legend = ("1  platform, turns for azimuth (340 mm)\n"
              "2  rotating drum (holds the tilt drive and controller)\n"
              "3  tilt NEMA 17 + 10:1 gearbox, lying along the axle\n"
              "4  controller and drivers ride on the drum\n"
              "5  belt up to the axle, hidden in the right upright\n"
              "6  slip ring: stator fixed, rotor turns with the platform\n"
              "7  azimuth NEMA 17 lying radially, fixed, bevel pinion (20 mm)\n"
              "8  crown gear ring on the platform underside (teeth down,\n"
              "    about 14:1; print in segments)\n"
              "9  turntable bearing ring (about 230 mm, to be sized)\n"
              "10 base plate and ballast")
    ax.text(-195, -12, legend, fontsize=8, va="top", ha="left", linespacing=1.45,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.6"))
    scale_bar(ax, 80, -40, 100)
    ax.set_xlim(-200, 215); ax.set_ylim(-185, 110); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


SILVER, SILVER_E = "#c8d0d8", "#7d8791"


def chain_poly(ax, zc_big, zc_small, r_big, r_small, z=9):
    c = zc_big - zc_small
    phi = np.arcsin((r_big - r_small) / c)
    for sgn in (1, -1):
        x0, z0 = sgn * r_big * np.cos(phi), zc_big - r_big * np.sin(phi)
        x1, z1 = sgn * r_small * np.cos(phi), zc_small - r_small * np.sin(phi)
        ax.plot([x0, x1], [z0, z1], color=SILVER_E, lw=3.2, zorder=z)
        ax.plot([x0, x1], [z0, z1], color="white", lw=1.4, ls=(0, (1.2, 2.4)), zorder=z + 0.1)   # hints the links
    for (cz, r) in ((zc_big, r_big), (zc_small, r_small)):
        ax.add_patch(Circle((0, cz), r, facecolor=SILVER, edgecolor=SILVER_E, lw=2.5, zorder=z - 0.5, alpha=0.9))
        ax.add_patch(Circle((0, cz), r * 0.25, facecolor="#9aa4ad", edgecolor="black", lw=0.8, zorder=z + 0.2))


def front_min(ax):
    ax.set_title("Front view, minimal goal post and exposed chain, to scale", fontsize=11)
    rect(ax, -250, -22, 500, 22, "#d8b48c", ec="#8b6b4a")
    rect(ax, -BASE_R, 0, 2 * BASE_R, BASE_H, "#d6d6d6", lw=1.5)
    rect(ax, -PLAT_R, PLAT_Z0, 2 * PLAT_R, PLAT_Z1 - PLAT_Z0, "#bfc7d1", lw=1.5, z=3)
    for s_ in (-1, 1):
        rect(ax, s_ * ROD_X - ROD_D / 2, PLAT_Z1, ROD_D, ROD_TOP - PLAT_Z1, SILVER, ec=SILVER_E, lw=1.2, z=4)   # rods
        rect(ax, s_ * ROD_X - 8, ZC - 8, 16, 16, "#b58a4a", z=5)                                              # bronze bushing block
    ax.add_patch(Circle((0, ZC), R_DISC, facecolor=STEEL, edgecolor=STEEL_E, lw=2.5, zorder=6))
    ax.add_patch(Circle((-30, ZC + 35), 48, facecolor="white", edgecolor="none", alpha=0.35, zorder=7))
    rect(ax, -(ROD_X + 12), ZC - 4, ROD_X + 12 + max(BELT_X + 8, ROD_X + 12), 8, DARK, z=8)                                   # axle
    rect(ax, BELT_X - 4, ZC - PD_TOP / 2, 8, PD_TOP, SILVER, ec=SILVER_E, z=9)                                    # sprocket edge on
    ax.plot([BELT_X, BELT_X], [PLAT_Z1, ZC - PD_TOP / 2], color=SILVER_E, lw=3.2, zorder=9)                      # exposed chain
    ax.plot([BELT_X, BELT_X], [PLAT_Z1, ZC - PD_TOP / 2], color="white", lw=1.4, ls=(0, (1.2, 2.4)), zorder=9.1)
    ax.plot([BELT_X, BELT_X], [ZM, PLAT_Z1], color=DARK, lw=1.2, ls=":", zorder=3.6)                            # inside the base
    ax.plot(0, ZC, "o", color="black", ms=4, zorder=11)
    dim(ax, (-R_DISC, ZC + R_DISC + 22), (R_DISC, ZC + R_DISC + 22), "mirror 200 mm", off=(0, 12))
    dim(ax, (-215, 0), (-215, ZC + R_DISC), f"{ZC + R_DISC:.0f} mm overall", off=(-20, 0), rot=90)
    dim(ax, (-196, 0), (-196, ZC), f"axle {ZC:.0f}", off=(-16, 0), rot=90, fs=8)
    dim(ax, (-PLAT_R, PLAT_Z0 - 6), (PLAT_R, PLAT_Z0 - 6), f"platform {2 * PLAT_R:.0f} mm", off=(0, -10), fs=8)
    dim(ax, (-ROD_X, ROD_TOP + 22), (ROD_X, ROD_TOP + 22), f"rods {2 * ROD_X:.0f} mm apart (centres)", off=(0, 10), fs=8)
    note(ax, "stainless roller chain, exposed,\n" + ("runs between the mirror and the right rod" if CHAIN_INSIDE else "runs outside the right-hand rod"), (BELT_X + 1, ZC - 70), (215, ZC - 40))
    note(ax, "10 mm rods; the axle turns in bronze\nbushings in the rod tops", (-ROD_X, ZC + 8), (-250, ZC + 70), ha="left")
    note(ax, f"{N_TOP}-tooth sprocket on the axle end", (BELT_X, ZC + 10), (150, ZC + 70), ha="left")
    note(ax, "rotating platform (azimuth)", (140, PLAT_Z1 - 4), (205, 120), ha="left")
    note(ax, "fixed base: azimuth motor,\nslip ring, ballast", (150, 30), (205, 50))
    scale_bar(ax, 100, -50, 100)
    ax.set_xlim(-255, 330); ax.set_ylim(-60, ZC + R_DISC + 50); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def side_min(ax):
    c = ZC - ZM
    L = belt_length(c, min(PD_BOT, PD_TOP) / 2, max(PD_BOT, PD_TOP) / 2)
    links = int(round(L / CHAIN_P / 2) * 2)
    ax.set_title("Side view along the axle, to scale", fontsize=11)
    rect(ax, -250, -22, 500, 22, "#d8b48c", ec="#8b6b4a")
    rect(ax, -BASE_R, 0, 2 * BASE_R, BASE_H, "#d6d6d6", lw=1.5)
    rect(ax, -PLAT_R, PLAT_Z0, 2 * PLAT_R, PLAT_Z1 - PLAT_Z0, "#bfc7d1", lw=1.5, z=3)
    rect(ax, -MOT_W / 2, ZM - MOT_W / 2, MOT_W, MOT_W, DARK, z=4)
    rect(ax, -ROD_D / 2, PLAT_Z1, ROD_D, ROD_TOP - PLAT_Z1, SILVER, ec=SILVER_E, lw=1.2, z=5)
    ang = np.radians(35)
    for a, al in ((ang, 1.0), (-np.radians(40), 0.35)):
        ax.plot([-R_DISC * np.sin(a), R_DISC * np.sin(a)], [ZC - R_DISC * np.cos(a), ZC + R_DISC * np.cos(a)],
                color=STEEL_E, lw=8, alpha=al, solid_capstyle="butt", zorder=6)
    chain_poly(ax, ZC, ZM, PD_TOP / 2, PD_BOT / 2)
    ax.plot(0, ZC, "o", color="black", ms=4, zorder=12)
    dim(ax, (95, ZM), (95, ZC), f"sprocket centres {c:.0f} mm", off=(30, 0), rot=90, fs=8)
    note(ax, f"chain about {L:.0f} mm ({links} links of 6.35 mm),\n{N_BOT}T motor sprocket to {N_TOP}T axle sprocket", (22, (ZC + ZM) / 2), (115, 215), fs=8)
    note(ax, "motor + gearbox lying along the axle\n(seen end on, 42 x 42 mm)", (MOT_W / 2 - 2, ZM + 12), (92, 130), fs=8)
    note(ax, "mirror seen edge on, two tilts", (R_DISC * np.sin(ang) * 0.8, ZC + R_DISC * np.cos(ang) * 0.8),
         (-120, ZC + 70), ha="right", fs=8)
    note(ax, "10 mm rod", (ROD_D / 2, ROD_TOP - 15), (-70, ROD_TOP + 10), ha="right", fs=8)
    scale_bar(ax, -240, -50, 100)
    ax.set_xlim(-250, 250); ax.set_ylim(-60, ZC + R_DISC + 50); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    t_g = 0.255 * 10 * 0.9                      # N.m at the gearbox output at stall (theoretical)
    f_chain = t_g / (PD_BOT / 2 / 1000)
    print(f"Chain: centres {c:.0f} mm, length about {L:.0f} mm, about {links} links; axle sprocket {N_TOP}T ({PD_TOP:.1f} mm), "
          f"motor sprocket {N_BOT}T ({PD_BOT:.1f} mm)")
    print(f"Overall ratio motor to axle {10 * N_TOP / N_BOT:.1f}:1 (with the 10:1 gearbox); stall chain pull about {f_chain:.0f} N; "
          f"axle torque about {f_chain * PD_TOP / 2 / 1000:.2f} N.m; microstep at the axle about {360 / (3200 * 10 * N_TOP / N_BOT):.4f} deg")


def base_min(ax):
    ax.set_title("Base cutaway: both motors on their sides in one 42 mm band, to scale", fontsize=11)
    rect(ax, -BASE_R, 0, 2 * BASE_R, BASE_H, "#ececec", lw=1.5, z=1)
    rect(ax, -BASE_R + 6, 0, 2 * BASE_R - 12, 8, "#8a8a8a", z=2)
    rect(ax, -PLAT_R, PLAT_Z0, 2 * PLAT_R, PLAT_Z1 - PLAT_Z0, "#bfc7d1", lw=1.5, z=3)
    rect(ax, -DRUM_R, DRUM_Z0, 2 * DRUM_R, 3, "#9a9a9a", z=3)
    for s_ in (-1, 1):
        rect(ax, s_ * DRUM_R - (3 if s_ > 0 else 0), DRUM_Z0, 3, DRUM_Z1 - DRUM_Z0, "#9a9a9a", z=3)
        rect(ax, s_ * BEAR_R - 7, 8, 14, 6, GREY, z=3)
        rect(ax, s_ * CROWN_R - 6, 48, 12, 12, ORANGE, z=4)                                      # crown gear ring
        rect(ax, s_ * ROD_X - ROD_D / 2, PLAT_Z1, ROD_D, 20, SILVER, ec=SILVER_E, z=4)             # rod feet
    rect(ax, -11, 8, 22, 34, PURPLE, z=3)
    rect(ax, -4, 42, 8, 18, BLUE, z=3)
    xf = BELT_X - 10.0
    rect(ax, xf - GB_L, ZM - MOT_W / 2, GB_L, MOT_W, ORANGE, z=3)
    rect(ax, xf - GB_L - MOT_L, ZM - MOT_W / 2, MOT_L, MOT_W, DARK, z=3)
    rect(ax, xf, ZM - 4, 21.5, 8, "#9a9a9a", z=4)
    rect(ax, BELT_X - 4, ZM - PD_BOT / 2, 8, PD_BOT, SILVER, ec=SILVER_E, z=5)                        # 12T sprocket
    ax.plot([BELT_X, BELT_X], [ZM + PD_BOT / 2, PLAT_Z1 + 40], color=SILVER_E, lw=3, zorder=6)
    rect(ax, BELT_X - 7, PLAT_Z0, 14, 8, "white", ec="none", z=3.5)                              # slot in the platform
    rect(ax, CROWN_R + 6, 8, MOT_L + 4, 9, "#9a9a9a", z=3)                                        # mount block
    rect(ax, CROWN_R + 6, ZM - MOT_W / 2, MOT_L, MOT_W, DARK, z=3)                                # azimuth NEMA 17
    rect(ax, CROWN_R - 6, 28, 12, 20, "#f4c542", z=5)                                             # pinion
    rect(ax, -118, 20, 76, 36, "#8fbf8f", z=3)
    ax.text(-80, 38, "controller\nand drivers", ha="center", va="center", fontsize=8, zorder=5)
    num(ax, 1, -125, 64); num(ax, 2, -140, 38); num(ax, 3, xf - GB_L / 2, ZM); num(ax, 4, -80, 62)
    num(ax, 5, BELT_X + 12, 92); num(ax, 6, 22, 24); num(ax, 7, CROWN_R + 22, ZM); num(ax, 8, CROWN_R, 70)
    num(ax, 9, BEAR_R + 12, 11); num(ax, 10, -150, 4)
    legend = (f"1  platform, turns for azimuth ({2 * PLAT_R:.0f} mm)\n"
              "2  rotating drum (holds the tilt drive and controller)\n"
              "3  tilt NEMA 17 + 10:1 gearbox, lying along the axle\n"
              "4  controller and drivers ride on the drum\n"
              "5  chain up through a slot to the axle sprocket (exposed)\n"
              "6  slip ring: stator fixed, rotor turns with the platform\n"
              "7  azimuth NEMA 17 lying radially, fixed, pinion (20 mm)\n"
              f"8  crown gear ring on the platform underside, about {CROWN_R / 10:.1f}:1\n"
              "    (teeth down; print in segments)\n"
              "9  turntable bearing ring (about 230 mm, to be sized)\n"
              "10 base plate and ballast")
    ax.text(-max(195, BASE_R + 10), -12, legend, fontsize=8, va="top", ha="left", linespacing=1.45,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.6"))
    scale_bar(ax, 80, -40, 100)
    ax.set_xlim(-max(200, BASE_R + 18), max(215, BASE_R + 20)); ax.set_ylim(-185, 110); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def main():
    fig = plt.figure(figsize=(22, 10.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 0.9, 0.95])
    (front_min if MIN else front)(fig.add_subplot(gs[0, 0]))
    (side_min if MIN else side)(fig.add_subplot(gs[0, 1]))
    (base_min if MIN else base_slim if SLIM else base)(fig.add_subplot(gs[0, 2]))
    fig.suptitle("Goal-post mount, 20 cm mirror, " + ("minimal rods and an exposed metal chain, slim base" if MIN else "slim base, both motors on their sides at one level" if SLIM else "tilt motor in the rotating base") + " (concept, to scale)", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT, dpi=100)
    if MIN:
        span = 2 * ROD_X
        F = 0.5 * 9.81                      # 0.5 kg mirror assembly (assumed)
        for d in (8.0, 10.0):
            I = np.pi * d ** 4 / 64
            print(f"Axle {d:.0f} mm steel over {span:.0f} mm between rod centres: sag at the middle with a 0.5 kg mirror about "
                  f"{F * span ** 3 / (48 * 2e5 * I):.3f} mm; twist per N.m over 150 mm about {np.degrees(1000 * 150 / (8e4 * np.pi * d ** 4 / 32)):.2f} deg")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
