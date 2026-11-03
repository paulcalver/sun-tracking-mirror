#!/usr/bin/env python3
"""Concept drawing: hiding the hinge. Compares the first-pass exposed hinge with a 'barrel hinge' set flush
into the drum top, with the whole drive (sector worm wheel, worm, motor, encoder) inside the drum.

Side section (looking along the hinge) at three tilts, a front view of what is visible, and the notch width
needed if the hinge is sunk below the surface instead. Draft sizes in mm, not CAD.
Usage (from the repo root): python3 cad/src/hidden_hinge_concept.py
Writes cad/media/earlier-concepts/hidden-hinge-concept.png
"""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle, Wedge

OUT = Path(__file__).resolve().parent.parent / "media" / "earlier-concepts" / "hidden-hinge-concept.png"
DARK, ORANGE, BLUE, BRASS, STEEL = "#1a1a1a", "#e8a400", "#4a6fa5", "#b5893a", "#c4c8cc"
PLATE_TOP, PLATE_T, FLOOR = 69.0, 7.0, 20.0
BAR_R = 12.0
MIR_H = 267.0


def rect(ax, x0, z0, w, h, fc, ec="black", lw=0.8, z=2, ls="-", alpha=1.0):
    ax.add_patch(Rectangle((x0, z0), w, h, facecolor=fc, edgecolor=ec, lw=lw, zorder=z, ls=ls, alpha=alpha))


def mirror(ax, el, alpha=1.0, fc="#cfe3ee", z=6):
    p = math.radians(el)
    n = (math.cos(p), math.sin(p))
    t = (-math.sin(p), math.cos(p))
    h = (0.0, PLATE_TOP)
    r0, r1, th = BAR_R - 2, BAR_R + MIR_H, 8
    pts = [(h[0] + t[0] * r0 - n[0] * th / 2, h[1] + t[1] * r0 - n[1] * th / 2),
           (h[0] + t[0] * r1 - n[0] * th / 2, h[1] + t[1] * r1 - n[1] * th / 2),
           (h[0] + t[0] * r1 + n[0] * th / 2, h[1] + t[1] * r1 + n[1] * th / 2),
           (h[0] + t[0] * r0 + n[0] * th / 2, h[1] + t[1] * r0 + n[1] * th / 2)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=DARK, lw=1.0, alpha=alpha, zorder=z))


def side(ax):
    ax.set_title("A. Barrel hinge flush in the drum top: side section", fontsize=11)
    # drum section: floor, wall, top plate with a half round groove for the bar
    rect(ax, -130, 0, 260, FLOOR, "#d8d8d8", lw=1.4)
    rect(ax, -130, FLOOR, 260, PLATE_TOP - PLATE_T - FLOOR, "#f4f4f4", lw=1.0, z=1)
    ax.add_patch(Rectangle((-130, PLATE_TOP - PLATE_T), 260, PLATE_T, facecolor="#b9b9b9", edgecolor="black", lw=1.2, zorder=2))
    ax.add_patch(Wedge((0, PLATE_TOP), BAR_R + 0.6, 180, 360, facecolor="white", edgecolor="black", lw=0.8, zorder=3))
    ax.add_patch(Circle((0, PLATE_TOP), BAR_R, facecolor=BRASS, edgecolor="black", lw=1.0, zorder=4))
    # hidden drive, drawn dashed because it sits at the right hand end (in front of this section)
    ax.add_patch(Wedge((0, PLATE_TOP), 26, 195, 345, facecolor="none", edgecolor=ORANGE, lw=1.6, ls="--", zorder=5))
    ax.add_patch(Circle((0, PLATE_TOP - 34), 7, facecolor="none", edgecolor=ORANGE, lw=1.6, ls="--", zorder=5))
    rect(ax, 8, PLATE_TOP - 34 - 21, 84, 42, "none", ec=BLUE, lw=1.4, z=5, ls="--")
    ax.text(50, PLATE_TOP - 34, "tilt motor\nlies along Y", fontsize=8, ha="center", va="center", color=BLUE)
    ax.annotate("sector worm wheel (only below\nthe hinge line) and worm,\nboth under the top plate", xy=(-14, PLATE_TOP - 26), xytext=(-130, 150),
                fontsize=8.5, ha="left", arrowprops=dict(arrowstyle="-", color="black", lw=0.7),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.6"), zorder=20)
    for el, a in ((-90, 0.18), (90, 0.18)):
        mirror(ax, el, alpha=a, z=5)
    for el in (-62, 0, 62):
        mirror(ax, el, alpha=0.9)
    ax.plot([-130, 130], [PLATE_TOP, PLATE_TOP], color="#555555", lw=0.6, ls=":", zorder=1)
    ax.text(0, -22, "Mirror swings from the bar. At 90 degrees it lies flat on the top plate.\n"
                    "Visible: a half round bar and the mirror. Nothing else.",
            fontsize=9, ha="center", va="top")
    ax.set_xlim(-140, 300); ax.set_ylim(-60, PLATE_TOP + BAR_R + MIR_H + 30); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def front(ax):
    ax.set_title("What you would see from the front", fontsize=11)
    rect(ax, -131, 0, 262, PLATE_TOP, "#ececec", lw=1.4)
    rect(ax, -131, 0, 262, 14, "#4d4d4d", lw=1.0, z=2.5)
    rect(ax, -118, PLATE_TOP - 1, 236, BAR_R + 1, BRASS, lw=1.0, z=4)          # half round bar, end housings included
    for s in (-1, 1):
        rect(ax, s * 106 - (0 if s > 0 else 12) + (0 if s < 0 else 0), PLATE_TOP - 1, 12, BAR_R + 1, "#8f6c28", lw=1.0, z=4.5)
    rect(ax, -104, PLATE_TOP + BAR_R - 2, 208, 275, "#cfe3ee", ec="#8a6d2f", lw=3.0, z=5)
    ax.annotate("fixed end housings\n(bearings inside)", xy=(112, PLATE_TOP + 6), xytext=(150, 130), fontsize=8.5,
                arrowprops=dict(arrowstyle="-", color="black", lw=0.7), bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.6"), zorder=20)
    ax.annotate("bar turns with the mirror", xy=(40, PLATE_TOP + 6), xytext=(150, 190), fontsize=8.5,
                arrowprops=dict(arrowstyle="-", color="black", lw=0.7), bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.6"), zorder=20)
    ax.annotate("encoder inside the left end,\ndrive inside the right end", xy=(-112, PLATE_TOP - 20), xytext=(-250, 120), fontsize=8.5,
                arrowprops=dict(arrowstyle="-", color="black", lw=0.7), bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.6"), zorder=20)
    ax.set_xlim(-290, 290); ax.set_ylim(-20, PLATE_TOP + BAR_R + 290); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def notch(ax):
    ax.set_title("B. Hinge sunk below the surface: notch width", fontsize=11)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    rows = [("Depth", "Width at 62 deg", "Width at 70 deg")]
    for d in (0, 6, 12, 20):
        rows.append((f"{d} mm", f"{2 * d * math.tan(math.radians(62)):.0f} mm", f"{2 * d * math.tan(math.radians(70)):.0f} mm"))
    for i, r in enumerate(rows):
        for j, t in enumerate(r):
            ax.text(0.0 + j * 3.4, 9 - i * 1.1, t, fontsize=8.5, fontweight="bold" if i == 0 else None, va="center")
    ax.text(0.2, 3.4, "A sunk hinge needs a V shaped notch, because the mirror plane\n"
                      "passes through the hinge line at every tilt. It also cannot lie flat.\n"
                      "A flush bar (depth 0) needs no notch.", fontsize=9.5, va="top")


def main():
    fig = plt.figure(figsize=(21, 9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 0.95, 0.55])
    a, b, c = (fig.add_subplot(gs[0, i]) for i in range(3))
    side(a); front(b); notch(c)
    fig.suptitle("Hiding the hinge: barrel hinge flush with the drum top (draft, to scale in mm, not CAD)", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT, dpi=100)
    print("Wrote", OUT)
    print(f"Overall height with the axis at the top plate: {PLATE_TOP + BAR_R + MIR_H + 8 - 2:.0f} mm (first pass was 379)")


if __name__ == "__main__":
    main()
