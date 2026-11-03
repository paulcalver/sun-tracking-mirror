#!/usr/bin/env python3
"""To-scale concept drawing: HINGED FLAT MIRROR on a turntable base (easel / laptop lid style).

A rectangular mirror stands on the base and hinges along its bottom edge. The hinge shaft sits on top of a
rotating drum, centred on the azimuth axis. The drum turns for azimuth (slip ring carries power, controller
rides on the drum). A NEMA 17 + 10:1 gearbox lies along the hinge inside the drum and drives the hinge
shaft through a short GT2 belt (16T to 32T, 2:1, 20:1 overall). No fork, chain, axle through the mirror, or
concentric shafts. Mirror normal elevation 'el': 0 = standing upright, +90 = lying back flat, -90 = lying
forward flat, face down.

Draft sizes in mm. The azimuth drive and slip ring are not drawn in detail (see the notes).
Usage (from the repo root): python3 cad/src/hinge_to_scale.py
Writes cad/media/earlier-concepts/hinge-to-scale.png
"""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon, Rectangle

from pedestal_to_scale import BLUE, DARK, GREY, LIGHT, LIGHT_O, MIRROR_C, ORANGE, chain_lines, dim, label, poly, rect

OUT = Path(__file__).resolve().parent.parent / "media" / "earlier-concepts" / "hinge-to-scale.png"

BASE_D, FIX_H, BASE_H = 250.0, 14.0, 66.0     # fixed ring 14 tall, turning drum up to 66
HINGE_Z = BASE_H + 6.0                        # hinge shaft axis
MIR_W, MIR_H, MIR_T = 200.0, 200.0, 8.0       # mirror plate (glass or sheet on a rigid backing)
MOT_Z = 38.0                                  # tilt motor axis
R16, R32 = 10.2 / 2, 20.4 / 2                 # GT2 pulley pitch radii (2 mm pitch)
TOP = HINGE_Z + MIR_H + 4


def mirror_poly(ax, el, alpha=1.0, fc=MIRROR_C, z=6):
    """Mirror seen edge on from the side. Hinge at (0, HINGE_Z). el = elevation of the mirror normal."""
    p = math.radians(el)
    n = np.array([math.cos(p), math.sin(p)])
    t = np.array([-math.sin(p), math.cos(p)])
    h = np.array([0.0, HINGE_Z])
    pts = [h - n * MIR_T / 2, h + t * MIR_H - n * MIR_T / 2, h + t * MIR_H + n * MIR_T / 2, h + n * MIR_T / 2]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=DARK, lw=1.0, alpha=alpha, zorder=z))
    return h + t * MIR_H / 2, n


def side(ax):
    ax.set_title("Side, looking along the hinge: the mirror swings like a laptop lid", fontsize=11)
    ax.plot([-330, 330], [0, 0], color="#999999", lw=2)
    rect(ax, -BASE_D / 2, 0, BASE_D, FIX_H, "#d8d8d8", lw=1.4)
    rect(ax, -BASE_D / 2, FIX_H, BASE_D, BASE_H - FIX_H, "#ececec", lw=1.4)
    rect(ax, -BASE_D / 2, BASE_H - 7, BASE_D, 7, "#b9b9b9", lw=1.0, z=2.5)
    rect(ax, -21, FIX_H + 3, 42, 42, "none", ec="#777777", lw=0.9, z=3)       # tilt motor, end on
    ax.add_patch(Circle((0, MOT_Z), 18, facecolor="none", edgecolor="#777777", lw=0.9, ls="--", zorder=3))
    ax.add_patch(Circle((0, MOT_Z), R16, facecolor="#f4c542", edgecolor="black", lw=0.8, zorder=4))
    ax.add_patch(Circle((0, HINGE_Z), R32, facecolor="#f4c542", edgecolor="black", lw=0.8, zorder=4))
    for p, q in chain_lines((0, HINGE_Z), R32, (0, MOT_Z), R16):
        ax.plot([p[0], q[0]], [p[1], q[1]], color=DARK, lw=1.4, zorder=4.5)
    ax.add_patch(Circle((0, HINGE_Z), MIR_H, fill=False, edgecolor="#999999", lw=1.0, ls=":", zorder=1))
    for el in (-90, 90):
        mirror_poly(ax, el, alpha=0.15, z=5)
    for el, lab in ((-62, "Sun below the horizon:\nfaces down, leans forward"), (0, "Sun on the horizon"),
                    (62, "Sun high (summer noon):\nleans right back")):
        c, n = mirror_poly(ax, el, alpha=0.9)
        a0 = c + n * 8
        ax.annotate("", xy=a0 + n * 70, xytext=a0, arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.8), zorder=8)
        e = a0 + n * 78
        if el > 30:
            ax.text(e[0] - 8, e[1] + 22, lab, fontsize=8, ha="right", va="center")
        else:
            ax.text(e[0] + 8, e[1], lab, fontsize=8, ha="left", va="center")
    ax.plot(0, HINGE_Z, "o", color=ORANGE, ms=6, zorder=9)
    label(ax, "hinge shaft on top of the drum,\non the azimuth axis", (0, HINGE_Z), (-285, 70), ha="right")
    label(ax, "tilt motor lies along the hinge (end on here),\n16T pulley, GT2 belt to a 32T pulley on the hinge", (-6, MOT_Z), (-285, 15), ha="right")
    label(ax, "turntable bearing", (125, FIX_H), (200, -30))
    dim(ax, (-300, 0), (-300, TOP), f"{TOP:.0f}", off=(-14, 0), rot=90)
    reach = MIR_H * math.sin(math.radians(62))
    dim(ax, (0, 4), (-reach, 4), f"{reach:.0f}", off=(0, -11))
    ax.text(0, -60, "Orange arrows: the way the mirror faces (towards the Sun). The mirror always stays above the hinge line,\n"
                    "so it never hits the base. The weight of the mirror always pulls one way except at upright, where it flips.",
            fontsize=8.5, ha="center", va="top")
    ax.set_xlim(-330, 340); ax.set_ylim(-120, TOP + 70); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def front(ax):
    ax.set_title("Front at upright, base cut away (schematic inside)", fontsize=11)
    ax.plot([-200, 200], [0, 0], color="#999999", lw=2)
    rect(ax, -BASE_D / 2, 0, BASE_D, FIX_H, "#d8d8d8", lw=1.4)
    rect(ax, -BASE_D / 2, FIX_H, BASE_D, BASE_H - FIX_H, "#ececec", lw=1.4)
    rect(ax, -BASE_D / 2, BASE_H - 7, BASE_D, 7, "#b9b9b9", lw=1.0, z=2.5)
    # tilt motor lying along X: motor 34 long, gearbox 40 long, output at the right
    rect(ax, 22, MOT_Z - 21, 34, 42, "#efc96a", z=3)
    rect(ax, 56, MOT_Z - 21, 40, 42, LIGHT_O, z=3)
    ax.text(39, MOT_Z, "NEMA 17", fontsize=6.5, ha="center", va="center", rotation=90, zorder=5)
    ax.text(76, MOT_Z, "10:1\ngearbox", fontsize=6.5, ha="center", va="center", zorder=5)
    rect(ax, 96, MOT_Z - 1.5, 8, 3, ORANGE, z=4)
    rect(ax, 96, MOT_Z - R16, 7, 2 * R16, "#f4c542", z=4)
    rect(ax, 96, HINGE_Z - R32, 7, 2 * R32, "#f4c542", z=4)
    rect(ax, 98.8, MOT_Z, 1.4, HINGE_Z - MOT_Z, DARK, z=4.5, lw=0.2)
    # azimuth motor, end on, dashed (lies along the viewing direction)
    rect(ax, -63, FIX_H + 3, 42, 42, "none", ec="#777777", lw=0.9, z=3)
    ax.text(-42, FIX_H + 24, "azimuth\nmotor\n(lies front\nto back)", fontsize=6.5, ha="center", va="center", zorder=5)
    # hinge shaft, bearing blocks
    rect(ax, -120, HINGE_Z - 4, 240, 8, ORANGE, z=7)
    for s in (-1, 1):
        rect(ax, s * 113 - 5, BASE_H, 10, 16, GREY, z=6)
    # mirror (upright)
    rect(ax, -MIR_W / 2, HINGE_Z, MIR_W, MIR_H, MIRROR_C, ec=DARK, lw=2.0, z=6)
    rect(ax, -MIR_W / 2 + 4, HINGE_Z + 4, MIR_W - 8, MIR_H - 8, "none", ec="#888888", lw=0.6, z=6.5)
    ax.add_patch(Circle((-45, HINGE_Z + 150), 18, facecolor="white", edgecolor="none", alpha=0.45, zorder=7))
    label(ax, f"{MIR_W:.0f} x {MIR_H:.0f} mm mirror on a rigid backing,\nframed (draft size)", (60, HINGE_Z + 150), (140, HINGE_Z + 175))
    label(ax, "hinge shaft in two bearing blocks", (-113, HINGE_Z + 6), (-170, HINGE_Z + 60), ha="right")
    label(ax, "belt, edge on", (99, 55), (150, 20))
    dim(ax, (-BASE_D / 2, -14), (BASE_D / 2, -14), f"base {BASE_D:.0f}", off=(0, -12))
    dim(ax, (-MIR_W / 2, TOP + 14), (MIR_W / 2, TOP + 14), f"{MIR_W:.0f}", off=(0, 11))
    ax.set_xlim(-230, 235); ax.set_ylim(-40, TOP + 40); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def plan(ax):
    ax.set_title("From above: the sweep as the base turns", fontsize=11)
    flat = math.hypot(MIR_W / 2, MIR_H)
    r62 = math.hypot(MIR_W / 2, MIR_H * math.sin(math.radians(62)))
    ax.add_patch(Circle((0, 0), 240, facecolor="#f0f0f0", edgecolor="#888888", lw=1.0, ls="--", zorder=1))
    ax.add_patch(Circle((0, 0), flat, facecolor="#fbeccb", edgecolor=ORANGE, lw=1.0, ls=":", zorder=1.2))
    ax.add_patch(Circle((0, 0), r62, facecolor="none", edgecolor=ORANGE, lw=1.4, zorder=1.3))
    ax.add_patch(Circle((0, 0), BASE_D / 2, facecolor=LIGHT, edgecolor=BLUE, lw=2.0, zorder=2))
    for sgn in (-1, 1):
        ax.add_patch(Rectangle((-MIR_W / 2, 0), MIR_W, sgn * MIR_H * math.sin(math.radians(62)), facecolor=MIRROR_C,
                               edgecolor=DARK, lw=0.8, alpha=0.6, zorder=3))
    ax.plot([-118, 118], [0, 0], color=ORANGE, lw=2.5, zorder=5)
    ax.text(0, -270, f"Base {BASE_D:.0f} (blue). Orange: reach of the mirror corners as the base turns,\n"
                      f"{2 * r62:.0f} across at 62 deg tilt, {2 * flat:.0f} across if it lies flat.\n"
                      "Grey dashed: the goal post base (about 480).",
            fontsize=9, ha="center", va="top")
    ax.set_xlim(-260, 260); ax.set_ylim(-340, 260); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def main():
    fig = plt.figure(figsize=(22, 8.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[670, 465, 520])
    a, b, c = (fig.add_subplot(gs[0, i]) for i in range(3))
    side(a); front(b); plan(c)
    fig.suptitle("Hinged flat mirror on a turntable, to scale (mm). Draft: nothing built or tested.", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT, dpi=100)
    torque = 0.7 * 9.81 * (MIR_H / 2) / 1000
    print(f"Overall height upright {TOP:.0f} mm, base {BASE_D:.0f} x {BASE_H:.0f} mm, hinge axis {HINGE_Z:.0f} mm")
    print(f"Corner reach: {math.hypot(MIR_W / 2, MIR_H * math.sin(math.radians(62))):.0f} mm at 62 deg, "
          f"{math.hypot(MIR_W / 2, MIR_H):.0f} mm flat")
    print(f"Gravity torque on the hinge when flat, assuming 0.7 kg: {torque:.2f} N.m (at the gearbox: {torque / 2:.2f})")
    print(f"Tilt resolution: {360 / (200 * 16 * 20):.4f} deg per microstep (20:1 overall)")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
