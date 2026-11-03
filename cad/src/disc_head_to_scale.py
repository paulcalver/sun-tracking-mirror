#!/usr/bin/env python3
"""To-scale drawing: 12 inch polished stainless disc, Y fork, NEMA 17 + HDP30 tilt drive, base with slip ring.

Three panels, all in millimetres with scale bars:
  left   whole sculpture, face on (disc vertical)
  top    section through the tilt drive, looking down along the axle's perpendicular
  bottom section through the base: slip ring, bearings, azimuth NEMA 17 + HDP30, belt

Dimensions: HDP30 from its STEP files (outer 53.8 mm, stack 29.4 mm: interface plate z -5.0 to output spline z 24.4);
NEMA 17 42.3 x 42.3 x 34 mm; 6806 bearing 30x42x7; disc 304.8 mm. The fork, base, belt, slip ring length and all
housings are my draft sizes. Concept only: no strength or clearance analysis.

Usage (from the repo root): python3 cad/src/disc_head_to_scale.py
Writes cad/media/earlier-concepts/disc-head-to-scale.png
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle, Wedge

FIT = "--fit0349" in sys.argv          # The Pi Hut / DFRobot FIT0349: NEMA 17 with 5.18:1 planetary gearbox
GEARED = "--geared" in sys.argv or FIT
OUT = Path(__file__).resolve().parent.parent / "media" / "earlier-concepts" / ("disc-head-to-scale-fit0349.png" if FIT else "disc-head-to-scale-geared.png" if GEARED else "disc-head-to-scale.png")
DRIVE = "FIT0349 geared NEMA 17" if FIT else "NEMA 14 + planetary gearbox" if GEARED else "NEMA 17 + HDP30"
STEEL, STEEL_E = "#cfd6dc", "#6b7780"
BLUE, ORANGE, DARK, GREY = "#4a6fa5", "#e8a400", "#3a3a3a", "#b8b8b8"
LIGHT = "#dbe6f4"

R_DISC = 304.8 / 2
R_MOUTH = R_DISC + 8
R_OUT = R_MOUTH + 15
BASE_H = 110.0
POLE_TOP = BASE_H + 120.0
STEM_TOP = POLE_TOP + 30.0
ZC = STEM_TOP + R_OUT                       # disc centre height above the table
HDP_T, HDP_D = 29.4, 53.8                    # from the STEP bounding boxes
MOTOR_L, MOTOR_W = 34.0, 42.3
HOUSING_D = 64.0
if GEARED:
    # ready-made geared NEMA 14: 35 mm flange, 26 mm gearbox stack (5:1 listing), 28 mm motor body (14HS11 class)
    HDP_T, HDP_D = 26.0, 35.0
    MOTOR_L, MOTOR_W = 28.0, 35.0
    HOUSING_D = 50.0
if FIT:
    # from the FIT0349 datasheet drawing: 42 mm square motor 40 mm long, 36 mm round gearbox (page says 27 mm long), 8 mm D shaft
    HDP_T, HDP_D = 27.0, 36.0
    MOTOR_L, MOTOR_W = 40.0, 42.0
    HOUSING_D = 62.0


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


def scale_bar(ax, x, y, length=100):
    ax.plot([x, x + length], [y, y], color="black", lw=3, zorder=20)
    ax.text(x + length / 2, y + 8, f"{length} mm", ha="center", fontsize=8.5)


def whole(ax):
    ax.set_title("Whole sculpture, face on, to scale", fontsize=11)
    rect(ax, -270, -25, 540, 25, "#d8b48c", ec="#8b6b4a")                                   # table top
    rect(ax, -110, 0, 220, BASE_H, "#d6d6d6", lw=1.5)                                       # base housing
    rect(ax, -15, BASE_H, 30, POLE_TOP - BASE_H, BLUE)                                      # pole
    rect(ax, -22, POLE_TOP, 44, ZC - R_OUT - POLE_TOP, LIGHT)                               # stem
    ax.add_patch(Wedge((0, ZC), R_OUT, 180, 360, width=R_OUT - R_MOUTH, facecolor=LIGHT, edgecolor="black", lw=0.8, zorder=2))
    for x0 in (-R_OUT, R_MOUTH):
        rect(ax, x0, ZC, R_OUT - R_MOUTH, 25, LIGHT)                                        # arms
    ax.add_patch(Circle((0, ZC), R_DISC, facecolor=STEEL, edgecolor=STEEL_E, lw=2.5, zorder=5))
    ax.add_patch(Circle((-45, ZC + 50), 70, facecolor="white", edgecolor="none", alpha=0.35, zorder=6))
    rect(ax, -R_OUT - 15, ZC - 4, 2 * R_OUT + 30, 8, DARK, z=7)                             # axle
    # tilt drive housing on the right arm
    x0 = R_OUT
    rect(ax, x0, ZC - HOUSING_D / 2, HDP_T + MOTOR_L + 5, HOUSING_D, "#f1f1f1", z=4, ls="--")
    rect(ax, x0, ZC - HDP_D / 2, HDP_T, HDP_D, ORANGE, z=5)
    rect(ax, x0 + HDP_T, ZC - MOTOR_W / 2, MOTOR_L, MOTOR_W, DARK, z=5)
    rect(ax, -R_OUT - 15, ZC - 15, 15, 30, LIGHT, z=4)                                      # left bearing boss
    ax.plot(0, ZC, "o", color="black", ms=4, zorder=9)
    # dimensions
    dim(ax, (-R_DISC, ZC + R_DISC + 25), (R_DISC, ZC + R_DISC + 25), "12 in = 304.8 mm", off=(0, 14))
    dim(ax, (-250, 0), (-250, ZC + R_DISC), f"{ZC + R_DISC:.0f} mm overall", off=(-22, 0), rot=90)
    dim(ax, (-232, 0), (-232, ZC), f"centre {ZC:.0f}", off=(-18, 0), rot=90, fs=8)
    dim(ax, (-110, 12), (110, 12), "base 220 mm", off=(0, 8), fs=8)
    note(ax, "polished stainless sheet on\na stiff backing, flat", (60, ZC - 60), (150, ZC - 175))
    note(ax, "Y fork: half-circle mouth,\nwider than the disc", (-120, ZC - 125), (-110, 205))
    note(ax, f"tilt drive: {DRIVE}\n(in line with the axle)", (R_OUT + 45, ZC - 30), (R_OUT + 25, ZC - 120))
    note(ax, "hollow pole (30 mm tube)\nwires and slip ring inside", (15, 170), (80, 190))
    note(ax, f"base: azimuth {DRIVE},\nslip ring, heavy ballast", (80, 55), (150, 90))
    scale_bar(ax, 160, -60)
    ax.set_xlim(-275, 330); ax.set_ylim(-70, ZC + R_DISC + 60); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def drive_section(ax):
    ax.set_title("Tilt drive in the right arm, top-down section, to scale", fontsize=11)
    x0 = R_OUT                       # outer face of the fork arm
    rect(ax, 120, -3, x0 - 120, 6, STEEL, ec=STEEL_E)                                       # disc edge-on (thickness 6)
    rect(ax, x0 - 15, -HOUSING_D / 2, 15, HOUSING_D, LIGHT)                                 # arm boss
    rect(ax, 120, -4, x0 - 120 + 7, 8, DARK, z=5)                                           # axle to coupling
    for xb in (x0 - 13, x0 - 6):                                                            # two bearings
        rect(ax, xb, 4, 5, 8, GREY); rect(ax, xb, -12, 5, 8, GREY)
    rect(ax, x0 + 0, -12, 7, 24, "#9a9a9a", z=4)                                            # coupling
    if GEARED:
        rect(ax, x0 + 0, -HDP_D / 2, HDP_T, HDP_D, ORANGE, z=3)                                  # planetary gearbox
        rect(ax, x0 - 2, -2.5, 12, 5, DARK, z=6)                                                  # 5 mm output shaft (assumed)
    else:
        # HDP30 (positions from the STEP files; output face at the arm)
        rect(ax, x0 + 5.5, -HDP_D / 2, 24.4 - 5.0 + 0.0, HDP_D, ORANGE, z=3)                      # circular spline base + preloader
        rect(ax, x0 + 0, -19.3, 20.0, 38.6, "#f4c542", z=4)                                       # output spline
        rect(ax, x0 + HDP_T - 5.0, -HDP_D / 2, 5.0, HDP_D, "#c9c9c9", z=4)                        # interface plate
        rect(ax, x0 + 5, -11.6, 12.2, 23.2, "#8a5a00", z=5)                                       # wave generator
        rect(ax, x0 + 7, -2.5, 28, 5, DARK, z=6)                                                  # motor shaft
    rect(ax, x0 + HDP_T, -MOTOR_W / 2, MOTOR_L, MOTOR_W, DARK, z=3)                         # NEMA 17
    rect(ax, x0 + HDP_T + MOTOR_L, -MOTOR_W / 2 - 2, 5, MOTOR_W + 4, "#c9c9c9", z=3)        # rear cap
    rect(ax, x0, -HOUSING_D / 2, HDP_T + MOTOR_L + 5, HOUSING_D, "none", ls="--", lw=1.2, z=8)
    ax.text(x0 - 22, -42, "to disc centre", fontsize=8, ha="center")
    ax.annotate("", xy=(124, -38), xytext=(150, -38), arrowprops=dict(arrowstyle="->"))

    def num(n, x, y):
        ax.text(x, y, str(n), fontsize=9, ha="center", va="center", zorder=25, color="white", fontweight="bold",
                bbox=dict(boxstyle="circle,pad=0.25", fc="#c0392b", ec="none"))

    num(1, 140, 12); num(2, x0 - 30, 6); num(3, x0 + 3.5, 25); num(4, x0 + HDP_T * 0.6, HDP_D / 2 + 7); num(5, x0 + HDP_T + MOTOR_L / 2, 0)
    num(6, x0 + HDP_T + MOTOR_L + 2.5, HOUSING_D / 2 + 4)
    dim(ax, (x0, 52), (x0 + HDP_T + MOTOR_L + 5, 52), f"housing {HDP_T + MOTOR_L + 5:.0f} mm long", off=(0, 8), fs=8)
    if FIT:
        legend = ("1  disc edge-on (6 mm: sheet + backing)\n"
                  "2  8 mm axle on two bearings in the arm\n"
                  "3  coupling: gearbox 8 mm D shaft to the axle\n"
                  "4  planetary gearbox 5.18:1: 36 mm across, 27 mm long (page)\n"
                  "5  NEMA 17 motor: 42 x 42 mm, 40 mm long (datasheet)\n"
                  "6  housing: 62 mm across, shown dashed\n"
                  "   (a light torsion spring on the axle would take up backlash)")
    elif GEARED:
        legend = ("1  disc edge-on (6 mm: sheet + backing)\n"
                  "2  8 mm axle on two bearings in the arm\n"
                  "3  coupling: gearbox output shaft to the axle\n"
                  "4  planetary gearbox: 35 mm flange, 26 mm long (NEMA 14, 5:1 listing)\n"
                  "5  NEMA 14 motor: 35 x 35 mm, 28 mm body (14HS11 class)\n"
                  "6  housing: 50 mm across, shown dashed\n"
                  "   (a light torsion spring on the axle would take up backlash)")
    else:
        legend = ("1  disc edge-on (6 mm: sheet + backing)\n"
                  "2  8 mm axle on two bearings in the arm\n"
                  "3  coupling: HDP30 output bolts to the axle\n"
                  "4  HDP30: 53.8 mm across, 29.4 mm thick (from its STEP files)\n"
                  "5  NEMA 17: 42.3 x 42.3 x 34 mm\n"
                  "6  housing: 64 mm across, shown dashed")
    ax.text(114, -76, legend, fontsize=8.5, va="top", ha="left", linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.6"))
    scale_bar(ax, 114, -168, 50)
    ax.set_xlim(112, x0 + 105); ax.set_ylim(-178, 80); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def base_section(ax):
    ax.set_title("Base, side section, to scale", fontsize=11)
    rect(ax, -110, 12, 220, BASE_H - 12, "#ececec", lw=1.5, z=1)
    rect(ax, -105, 0, 210, 12, "#8a8a8a", z=1)                                              # ballast plate
    ax.text(0, 5, "ballast", ha="center", color="white", fontsize=8)
    rect(ax, -11, 14, 22, 30, "#6a4f9c")                                                    # slip ring (approx)
    ax.plot([0, 0], [44, 125], color="#6a4f9c", lw=1.5, ls=":", zorder=6)
    for z0 in (50, 98):                                                                      # 6806 bearings
        rect(ax, -21, z0, 6, 7, GREY); rect(ax, 15, z0, 6, 7, GREY)
    rect(ax, -15, 44, 4, 81, BLUE); rect(ax, 11, 44, 4, 81, BLUE)                             # pole tube
    rect(ax, -30, 76, 60, 8, BLUE, z=3)                                                       # pole pulley
    xm = 75                                                                                  # azimuth stack
    rect(ax, xm - MOTOR_W / 2, 14, MOTOR_W, MOTOR_L, DARK)
    rect(ax, xm - HDP_D / 2, 14 + MOTOR_L, HDP_D, HDP_T, ORANGE)
    rect(ax, xm - 15, 14 + MOTOR_L + HDP_T, 30, 8, BLUE, z=3)                                 # output pulley
    ax.plot([-30, xm - 15], [80, 80], color=BLUE, lw=2, zorder=4)
    ax.plot([30, xm + 15], [80, 80], color=BLUE, lw=2, zorder=4)
    note(ax, "slip ring (about 22 mm;\nlength to be confirmed)", (0, 30), (-70, 40), ha="right", fs=8)
    note(ax, "two 6806 bearings\n(30 x 42 x 7)", (18, 101), (-70, 100), ha="right", fs=8)
    note(ax, f"belt and azimuth {DRIVE}\n(output pulley level with the pole's)", (xm + 25, 70), (155, 118), ha="right", fs=8)
    note(ax, "wires up the hollow pole", (0, 115), (-62, 118), ha="right", fs=8)
    dim(ax, (-110, 124), (110, 124), "220 mm", off=(0, 6), fs=8)
    scale_bar(ax, -105, -22, 100)
    ax.set_xlim(-125, 160); ax.set_ylim(-32, 140); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def main():
    fig = plt.figure(figsize=(22, 11.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[0.9, 1.1], height_ratios=[1.15, 0.85])
    whole(fig.add_subplot(gs[:, 0]))
    drive_section(fig.add_subplot(gs[0, 1]))
    base_section(fig.add_subplot(gs[1, 1]))
    fig.suptitle(f"12 inch polished stainless disc, tilt motor in the fork ({DRIVE}), all to scale", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT, dpi=100)
    print("Wrote", OUT, f"| disc centre {ZC:.0f} mm, overall height {ZC + R_DISC:.0f} mm")


if __name__ == "__main__":
    main()
