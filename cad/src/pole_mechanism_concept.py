#!/usr/bin/env python3
"""Concept drawing: concentric-shaft drive for a Sun-facing obsidian disc on a straight pole.

Two fixed motors in the base. The azimuth motor turns a hollow pole (tube). The tilt motor turns a thin
shaft that runs up inside the tube. At the top, a 90 degree mitre gear pair turns that shaft's rotation
into rotation of a cross shaft, a short belt carries it up the right arm of the Y fork, and it turns the
axle through the middle of the disc (vanity mirror style). Disc tilt follows the DIFFERENCE between the
inner shaft angle and the pole angle (see pole_drive_plan.py).

Schematic only: not to scale for mechanics, sizes are draft (disc 60 mm across, pole tube 30 mm).
Usage (from the repo root): python3 cad/src/pole_mechanism_concept.py
Writes cad/media/earlier-concepts/pole-mechanism-concept.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon, Rectangle, Wedge

OUT = Path(__file__).resolve().parent.parent / "media" / "earlier-concepts" / "pole-mechanism-concept.png"
BLUE, ORANGE, GREY, DARK = "#4a6fa5", "#e8a400", "#b8b8b8", "#1a1a1a"
LIGHT = "#dbe6f4"
Z0 = 240.0          # height of the tube top in the whole-sculpture panel
ZC = 92.0           # disc centre above the tube top
R_DISC, R_MOUTH, R_OUT = 30.0, 36.0, 48.0


def rect(ax, x0, z0, w, h, fc, ec="black", lw=0.8, alpha=1.0, z=2):
    ax.add_patch(Rectangle((x0, z0), w, h, facecolor=fc, edgecolor=ec, lw=lw, alpha=alpha, zorder=z))


def label(ax, text, xy, xytext, ha="left", fs=8.5):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, ha=ha, va="center", zorder=10,
                arrowprops=dict(arrowstyle="-", color="black", lw=0.7),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.6"))


def head(ax, z0, detail=False):
    """Draw the head: Y fork around the disc, mitre gears, cross shaft, belt, axle. z0 = tube top."""
    zc = z0 + ZC
    # Y fork: stem plus a half ring hugging the lower half of the disc, with arms up the sides
    stem = Polygon([(-15, z0), (15, z0), (15, z0 + 30), (R_OUT * 0.55, z0 + 38), (R_OUT * 0.55, z0 + 44),
                    (-R_OUT * 0.55, z0 + 44), (-R_OUT * 0.55, z0 + 38), (-15, z0 + 30)],
                   closed=True, facecolor=LIGHT, edgecolor="black", lw=0.8, zorder=2)
    ax.add_patch(stem)
    ax.add_patch(Wedge((0, zc), R_OUT, 180, 360, width=R_OUT - R_MOUTH, facecolor=LIGHT, edgecolor="black", lw=0.8, zorder=2))
    for s in (-1, 1):
        rect(ax, s * R_MOUTH if s > 0 else -R_OUT, zc, R_OUT - R_MOUTH, 12, LIGHT)
    # belt channel in the right arm: a lighter strip along the belt path
    ax.plot([20, 42], [z0 + 32, zc], color="#9bb3d1", lw=9, solid_capstyle="round", zorder=2.5, alpha=0.9)
    # tube top and inner shaft
    for s in (-1, 1):
        rect(ax, s * 13 - 2 if s > 0 else -15, z0 - 14, 4, 14, BLUE)
    rect(ax, -4, z0 - 14, 8, 14 + 24, ORANGE, z=3)
    # mitre gears (apex on the pole axis), 1:1
    ax.add_patch(Polygon([(-9, z0 + 23), (9, z0 + 23), (2.5, z0 + 29.5), (-2.5, z0 + 29.5)], closed=True,
                         facecolor=ORANGE, edgecolor="black", lw=0.8, zorder=4))
    ax.add_patch(Polygon([(9, z0 + 23), (9, z0 + 41), (3.5, z0 + 36.5), (3.5, z0 + 27.5)], closed=True,
                         facecolor="#f4c542", edgecolor="black", lw=0.8, zorder=4))
    # cross shaft and its pulley
    rect(ax, 9, z0 + 30.5, 11, 3, "#f4c542", z=4)
    rect(ax, 17, z0 + 24, 6, 16, "#f4c542", z=4)
    # belt up the arm to the axle pulley
    ax.plot([17.5, 38.5], [z0 + 32, zc - 0.5], color=DARK, lw=1.6, zorder=5)
    ax.plot([22.5, 45.5], [z0 + 32, zc - 0.5], color=DARK, lw=1.6, zorder=5)
    # disc (face on), bezel, axle through its centre
    ax.add_patch(Circle((0, zc), R_DISC, facecolor=DARK, edgecolor="#8a8a8a", lw=2.5, zorder=6))
    ax.add_patch(Circle((-9, zc + 9), 5, facecolor="#444444", edgecolor="none", alpha=0.6, zorder=7))   # sheen
    rect(ax, -R_OUT + 3, zc - 1.5, 2 * (R_OUT - 3), 3, ORANGE, z=8)
    rect(ax, R_MOUTH + 1, zc - 7, 8, 14, "#f4c542", z=8)       # axle pulley
    ax.plot(0, zc, "o", color="white", ms=3, zorder=9)


def main():
    fig = plt.figure(figsize=(22, 10.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[0.95, 0.85, 1.0])
    a, b, c = (fig.add_subplot(gs[0, i]) for i in range(3))

    # ---------- whole mechanism ----------
    a.set_title("Whole sculpture, cut away (not to scale)", fontsize=11)
    rect(a, -120, -6, 240, 6, "#dddddd", ec="#999999")
    a.add_patch(Rectangle((-85, 0), 170, 70, fill=False, edgecolor="black", lw=2, zorder=1))
    # tube
    for s in (-1, 1):
        rect(a, 11 if s > 0 else -15, 10, 4, Z0 - 10, BLUE)
    # bearings (tube in base)
    for z in (12, 52):
        for s in (-1, 1):
            rect(a, 15 if s > 0 else -21, z, 6, 7, GREY)
    # inner shaft and its bearings
    rect(a, -4, 2, 8, Z0 + 24 - 2, ORANGE, z=3)
    for z in (12, 225):
        for s in (-1, 1):
            rect(a, 4 if s > 0 else -11, z, 7, 7, GREY, z=3)
    # pulleys and belts, motors
    rect(a, -26, 26, 52, 6, BLUE, z=3)                                    # azimuth pulley on the tube
    rect(a, -18, 2, 36, 5, ORANGE, z=3)                                   # tilt pulley on the inner shaft
    rect(a, 45, 8, 38, 56, "#c9d8ea", ec="black")                         # azimuth motor + reduction
    rect(a, -83, 0, 32, 46, "#f6dfa0", ec="black")                        # tilt motor + reduction
    a.plot([26, 56], [29, 29], color=BLUE, lw=3)
    a.plot([-18, -62], [4.5, 4.5], color=ORANGE, lw=3)
    a.text(64, 36, "az\nmotor", ha="center", fontsize=8)
    a.text(-67, 22, "tilt\nmotor", ha="center", fontsize=8)
    head(a, Z0)
    # labels
    label(a, "1 azimuth motor + reduction", (64, 50), (60, 150))
    label(a, "2 tilt motor + reduction", (-67, 38), (-100, 110), ha="right")
    label(a, "3 hollow pole: turns once a day for azimuth", (13, 130), (35, 190))
    label(a, "4 inner shaft: turned by the tilt motor", (-1, 175), (-60, 205), ha="right")
    label(a, "5 main bearings", (18, 55), (60, 100))
    label(a, "6 mitre gears + cross shaft + belt\n(all inside the fork)", (10, Z0 + 30), (80, Z0 + 45))
    label(a, "7 obsidian disc on an axle through its centre", (30, Z0 + ZC + 15), (70, Z0 + 140))
    a.set_xlim(-185, 185); a.set_ylim(-12, Z0 + 150); a.set_aspect("equal")
    a.set_xticks([]); a.set_yticks([])

    # ---------- head detail, face on ----------
    b.set_title("Head, face on: Y fork with a half-circle mouth", fontsize=11)
    head(b, 0)
    label(b, "obsidian disc, 60 mm", (-15, ZC + 20), (-62, ZC + 62), ha="right")
    label(b, "axle through the disc's centre\n(turns the disc: tilt)", (-38, ZC), (-72, ZC - 25), ha="right")
    label(b, "Y fork: half-circle mouth\nwider than the disc", (-32, ZC - 30), (-72, ZC - 60), ha="right")
    label(b, "belt in the right arm turns the axle", (30, ZC - 25), (68, ZC - 38))
    label(b, "cross shaft + pulley", (20, 33), (66, 8))
    label(b, "mitre gear pair (90 degrees, 1:1)", (3, 28), (-62, 4), ha="right")
    label(b, "inner shaft (tilt)", (0, -8), (36, -20))
    label(b, "hollow pole (azimuth)", (-13, -8), (-62, -24), ha="right")
    b.set_xlim(-110, 110); b.set_ylim(-34, ZC + 82); b.set_aspect("equal")
    b.set_xticks([]); b.set_yticks([])

    # ---------- side view, edge on, showing the tilt sweep ----------
    c.set_title("Side view along the axle: the disc seen edge on", fontsize=11)
    zc = ZC
    rect(c, -15, 0, 30, 44, LIGHT)
    rect(c, -6, 44, 12, zc - 44, LIGHT)
    c.plot([0, 0], [-14, 0], color=BLUE, lw=4)
    for ang, alpha, lab in ((-62, 0.35, "night, winter"), (0, 0.55, "Sun on the horizon"), (62, 0.35, "noon, summer")):
        phi = np.radians(ang)
        # disc plane contains the axle; edge-on it is a line perpendicular to the Sun direction
        nx, nz = np.cos(phi), np.sin(phi)
        tx, tz = -nz, nx
        c.plot([-R_DISC * tx, R_DISC * tx], [zc - R_DISC * tz, zc + R_DISC * tz], color=DARK, lw=7, alpha=alpha + 0.3,
               solid_capstyle="round")
        c.annotate("", xy=(55 * nx, zc + 55 * nz), xytext=(0, zc), arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.6))
        c.text(66 * nx + (6 if nx >= 0 else 0), zc + 66 * nz, lab, fontsize=8, ha="left", va="center")
    c.plot(0, zc, "o", color=ORANGE, ms=6, zorder=9)
    c.text(10, -25, "Orange arrows: the way the disc faces (towards the Sun).\n"
                    "In London the disc swings about plus or minus 62 degrees.\n"
                    "The fork wraps the disc, so it could swing right round.",
           fontsize=9, ha="center", va="top")
    c.set_xlim(-110, 150); c.set_ylim(-75, zc + 80); c.set_aspect("equal")
    c.set_xticks([]); c.set_yticks([])

    fig.suptitle("Option C: two concentric shafts, everything electrical stays in the base", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT, dpi=110)
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
