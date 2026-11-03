#!/usr/bin/env python3
"""To-scale concept drawing: PEDESTAL (vanity mirror) mount for the 200 mm Sun mirror.

Layout: round fixed base, one thin pole, a U shaped fork at the top, the mirror held in a bezel ring with
two pivot pins at its sides (like a dressing table mirror).
Drive: two concentric shafts, both motors in the fixed base, so no slip ring and no moving wires.
  hollow tube  = azimuth (turned by the azimuth motor through a bevel pair)
  inner rod    = tilt   (turned by the tilt motor through a bevel pair)
At the top a bevel pair turns the rod's rotation RELATIVE to the tube into a cross shaft along the
fork's bridge, a short steel chain on the outside of the right arm turns the right pivot pin (2:1).
Mirror tilt = 0.5 x (rod angle minus tube angle), so the controller moves the rod with the tube.

Draft sizes in mm, schematic positions inside the base. Nothing here has been tested.
Usage (from the repo root): python3 cad/src/pedestal_to_scale.py
Writes cad/media/earlier-concepts/pedestal-to-scale.png
"""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle

OUT = Path(__file__).resolve().parent.parent / "media" / "earlier-concepts" / "pedestal-to-scale.png"
BLUE, ORANGE, DARK = "#4a6fa5", "#e8a400", "#1a1a1a"
LIGHT, LIGHT_O, GREY = "#dbe6f4", "#f7e3a8", "#c9c9c9"
MIRROR_C = "#cfe3ee"

# ---------------- parameters (mm) ----------------
R_MIRROR, R_BEZEL = 100.0, 106.0          # 200 mm mirror, 6 mm bezel ring around it
BASE_D, BASE_H = 250.0, 70.0              # fixed round base
POLE_LEN = 100.0                          # visible pole between base top and the head block
TUBE_D, ROD_D = 17.0, 6.0                 # azimuth tube, tilt rod inside it
HEAD_W, HEAD_H = 34.0, 28.0               # head block that holds the bevel pair
ARM_X, ARM_D, BRIDGE_D = 115.0, 10.0, 12.0
Z_BR_BELOW, HEAD_BELOW = 124.0, 144.0     # bridge axis and tube top, measured below the pivot axis
PITCH, N_TOP, N_BOT = 6.35, 32, 16        # ANSI 25 chain, 32T on the pin, 16T on the cross shaft
Z_AX = BASE_H + POLE_LEN + HEAD_BELOW
Z_BR = Z_AX - Z_BR_BELOW
T_TOP = Z_AX - HEAD_BELOW
CH_X = ARM_X + ARM_D / 2 + 8.0            # chain plane, just outside the right arm
PCD = lambda n: PITCH / math.sin(math.pi / n)
R_TOP, R_BOT = PCD(N_TOP) / 2, PCD(N_BOT) / 2
C_DIST = Z_BR_BELOW


def rect(ax, x0, z0, w, h, fc, ec="black", lw=0.8, z=2, alpha=1.0):
    ax.add_patch(Rectangle((x0, z0), w, h, facecolor=fc, edgecolor=ec, lw=lw, zorder=z, alpha=alpha))


def poly(ax, pts, fc, z=3, lw=0.8):
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor="black", lw=lw, zorder=z))


def label(ax, text, xy, xytext, ha="left", fs=8.5):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, ha=ha, va="center", zorder=20,
                arrowprops=dict(arrowstyle="-", color="black", lw=0.7),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.6"))


def dim(ax, p0, p1, text, off=(0, 0), fs=8.5, rot=0):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="<->", color="#333333", lw=0.9), zorder=15)
    mx, mz = (p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1]
    ax.text(mx, mz, text, fontsize=fs, ha="center", va="center", rotation=rot, zorder=16,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))


def chain_lines(c1, r1, c2, r2):
    """External tangent lines between two pitch circles."""
    c1, c2 = np.array(c1, float), np.array(c2, float)
    d = np.linalg.norm(c2 - c1)
    u = (c2 - c1) / d
    phi = math.acos((r1 - r2) / d)
    out = []
    for s in (1, -1):
        c, sn = math.cos(s * phi), math.sin(s * phi)
        n = np.array([u[0] * c - u[1] * sn, u[0] * sn + u[1] * c])
        out.append((c1 + r1 * n, c2 + r2 * n))
    return out


def front(ax):
    ax.set_title("Front, face on (base shown cut away, schematic inside)", fontsize=11)
    ax.plot([-210, 210], [0, 0], color="#999999", lw=2)
    # ---------- base ----------
    rect(ax, -BASE_D / 2, 0, BASE_D, BASE_H, "#ececec", lw=1.6, z=1)
    rect(ax, -BASE_D / 2, BASE_H - 4, BASE_D, 4, "#b9b9b9", lw=1.0, z=1.2)
    rect(ax, -BASE_D / 2 + 3, 3, BASE_D - 6, 5, "#9a9a9a", lw=0.6, z=1.2)           # ballast plate
    ax.text(0, 5.5, "ballast", fontsize=6.5, ha="center", va="center", zorder=3, color="white")
    zaz, zti = 47.0, 25.0                                                          # motor axes
    # tilt rod and azimuth tube
    rect(ax, -ROD_D / 2, 10, ROD_D, (Z_BR - 6) - 10, ORANGE, z=3.2)
    for x0 in (-TUBE_D / 2, TUBE_D / 2 - 1.5):
        rect(ax, x0, 41, 1.5, T_TOP + HEAD_H - 41 - 6, BLUE, z=3)
    for z in (46, 62):                                                             # tube bearings
        for s in (-1, 1):
            rect(ax, 8.5 if s > 0 else -14.5, z, 6, 6, "#8d8d8d", z=2.5)
    for z in (11, 31):                                                             # rod bearings
        for s in (-1, 1):
            rect(ax, 3 if s > 0 else -6.5, z - 2, 3.5, 5, "#8d8d8d", z=2.5)
    # azimuth bevel gear on the tube, pinion, gearbox, motor (right)
    poly(ax, [(-25, zaz - 6), (25, zaz - 6), (25, zaz + 2), (10, zaz + 8), (-10, zaz + 8), (-25, zaz + 2)], "#9bb3d1")
    poly(ax, [(26, zaz - 4), (26, zaz + 4), (36, zaz + 7), (36, zaz - 7)], "#7f9cc4")
    rect(ax, 36, zaz - 21, 38, 42, "#c9d8ea")
    rect(ax, 74, zaz - 21, 34, 42, "#a9bedb")
    ax.text(55, zaz, "10:1\ngearbox", fontsize=6.5, ha="center", va="center", zorder=5)
    ax.text(91, zaz, "NEMA 17", fontsize=6.5, ha="center", va="center", zorder=5)
    # tilt bevel gear on the rod, pinion, gearbox, motor (left)
    poly(ax, [(-25, zti - 6), (25, zti - 6), (25, zti + 2), (10, zti + 8), (-10, zti + 8), (-25, zti + 2)], "#f4c542")
    poly(ax, [(-26, zti - 4), (-26, zti + 4), (-36, zti + 7), (-36, zti - 7)], "#e0a800")
    rect(ax, -74, zti - 21, 38, 42, LIGHT_O)
    rect(ax, -108, zti - 21, 34, 42, "#efc96a")
    ax.text(-55, zti, "10:1\ngearbox", fontsize=6.5, ha="center", va="center", zorder=5)
    ax.text(-91, zti, "NEMA 17", fontsize=6.5, ha="center", va="center", zorder=5)
    # ---------- head block, bevel pair, cross shaft ----------
    rect(ax, -HEAD_W / 2, T_TOP, HEAD_W, HEAD_H, LIGHT, lw=1.0, z=2.8)
    poly(ax, [(-9, Z_BR - 12), (9, Z_BR - 12), (2.5, Z_BR - 4.5), (-2.5, Z_BR - 4.5)], "#f4c542", z=4)
    poly(ax, [(9, Z_BR - 9), (9, Z_BR + 9), (3.5, Z_BR + 3), (3.5, Z_BR - 3)], "#f4c542", z=4)
    # ---------- fork: bridge and two arms ----------
    rect(ax, -ARM_X - ARM_D / 2, Z_BR - BRIDGE_D / 2, 2 * ARM_X + ARM_D, BRIDGE_D, LIGHT, lw=1.0, z=2.9)
    for s in (-1, 1):
        rect(ax, s * ARM_X - ARM_D / 2, Z_BR, ARM_D, Z_AX + 8 - Z_BR, LIGHT, lw=1.0, z=2.7)
    rect(ax, 3.5, Z_BR - 1.5, CH_X - 3.5, 3, ORANGE, z=5)                         # cross shaft
    # ---------- mirror in its bezel ----------
    ax.add_patch(Circle((0, Z_AX), R_BEZEL, facecolor=DARK, edgecolor="#8a8a8a", lw=2.0, zorder=6))
    ax.add_patch(Circle((0, Z_AX), R_MIRROR, facecolor=MIRROR_C, edgecolor="#666666", lw=0.8, zorder=6.5))
    ax.add_patch(Circle((-35, Z_AX + 38), 18, facecolor="white", edgecolor="none", alpha=0.45, zorder=7))
    rect(ax, -ARM_X - 6, Z_AX - 1.5, ARM_X + 6 - R_BEZEL + 10, 3, ORANGE, z=8)       # left pivot pin
    rect(ax, R_BEZEL - 10, Z_AX - 1.5, CH_X + 6 - R_BEZEL + 10, 3, ORANGE, z=8)      # right pivot pin (drive)
    ax.plot(0, Z_AX, "+", color="#555555", ms=8, zorder=9)
    # ---------- chain (a disc in the YZ plane, so edge on from the front) ----------
    rect(ax, CH_X - 3, Z_AX - R_TOP, 6, 2 * R_TOP, "#f4c542", z=8.5)
    rect(ax, CH_X - 3, Z_BR - R_BOT, 6, 2 * R_BOT, "#f4c542", z=8.5)
    rect(ax, CH_X - 1.2, Z_BR, 2.4, Z_AX - Z_BR, DARK, z=9, lw=0.3)
    # ---------- labels and dimensions ----------
    label(ax, f"mirror {2 * R_MIRROR:.0f} mm in a bezel ring\n(pivot pins at its sides)", (-60, Z_AX + 70), (-300, Z_AX + 90), ha="right")
    label(ax, "U shaped fork", (-ARM_X, Z_AX - 40), (-300, Z_AX + 20), ha="right")
    label(ax, "left pin (free)", (-ARM_X - 2, Z_AX), (-300, Z_AX - 20), ha="right")
    label(ax, f"32T sprocket on the right pin, 16T on\nthe cross shaft, steel chain ({N_TOP}:{N_BOT} = 2:1)\n(seen edge on from the front)", (CH_X + 3, Z_AX + 10), (150, Z_AX + 80))
    label(ax, "cross shaft in the bridge", (90, Z_BR), (150, Z_BR - 30))
    label(ax, "bevel pair in the head block", (0, Z_BR - 8), (-300, Z_BR - 20), ha="right")
    label(ax, f"hollow tube {TUBE_D:.0f} mm: azimuth\ninner rod {ROD_D:.0f} mm: tilt", (-8, T_TOP - 40), (-300, T_TOP - 60), ha="right")
    label(ax, "azimuth motor + gearbox,\nbevel gear on the tube", (95, zaz + 20), (150, 140))
    label(ax, "tilt motor + gearbox,\nbevel gear on the rod", (-95, zti - 20), (-300, 30), ha="right")
    dim(ax, (-225, 0), (-225, Z_AX + R_BEZEL), f"{Z_AX + R_BEZEL:.0f}", off=(-12, 0), rot=90)
    dim(ax, (-BASE_D / 2, -14), (BASE_D / 2, -14), f"base {BASE_D:.0f}", off=(0, -12))
    dim(ax, (250, 0), (250, BASE_H), f"{BASE_H:.0f}", off=(14, 0), rot=90)
    dim(ax, (-R_BEZEL, Z_AX + R_BEZEL + 14), (R_BEZEL, Z_AX + R_BEZEL + 14), f"{2 * R_BEZEL:.0f}", off=(0, 11))
    ax.set_xlim(-310, 290); ax.set_ylim(-35, Z_AX + R_BEZEL + 40); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def side(ax):
    ax.set_title("Side, looking along the pivot axis: mirror edge on", fontsize=11)
    ax.plot([-210, 210], [0, 0], color="#999999", lw=2)
    rect(ax, -BASE_D / 2, 0, BASE_D, BASE_H, "#ececec", lw=1.6)
    rect(ax, -BASE_D / 2, BASE_H - 4, BASE_D, 4, "#b9b9b9", lw=1.0)
    rect(ax, -TUBE_D / 2, BASE_H, TUBE_D, T_TOP - BASE_H, BLUE)
    rect(ax, -ROD_D / 2, BASE_H, ROD_D, T_TOP - BASE_H, ORANGE, z=2.5)
    rect(ax, -HEAD_W / 2, T_TOP, HEAD_W, HEAD_H, LIGHT, lw=1.0)
    ax.add_patch(Circle((0, Z_BR), BRIDGE_D / 2, facecolor=LIGHT, edgecolor="black", lw=1.0, zorder=3))
    rect(ax, -ARM_D / 2, Z_BR, ARM_D, Z_AX + 8 - Z_BR, LIGHT, lw=0.8, z=1.5, alpha=0.8)
    ax.add_patch(Circle((0, Z_AX), R_BEZEL, fill=False, edgecolor="#999999", lw=1.0, ls=":", zorder=1))
    ax.add_patch(Circle((0, Z_AX), R_TOP, facecolor="#f4c542", edgecolor="black", lw=0.8, alpha=0.5, zorder=1.2))
    ax.add_patch(Circle((0, Z_BR), R_BOT, facecolor="#f4c542", edgecolor="black", lw=0.8, alpha=0.5, zorder=1.2))
    for p, q in chain_lines((0, Z_AX), R_TOP, (0, Z_BR), R_BOT):
        ax.plot([p[0], q[0]], [p[1], q[1]], color=DARK, lw=1.6, zorder=1.3)
    ax.text(40, Z_BR + 25, "chain, outside the\nright arm", fontsize=7.5, va="center")
    for ang, a, lab in ((-62, 0.45, "night, winter"), (0, 0.65, "Sun on the horizon"), (62, 0.45, "noon, summer")):
        phi = math.radians(ang)
        nx, nz = math.cos(phi), math.sin(phi)
        tx, tz = -nz, nx
        ax.plot([-R_BEZEL * tx, R_BEZEL * tx], [Z_AX - R_BEZEL * tz, Z_AX + R_BEZEL * tz], color=DARK, lw=6, alpha=a,
                solid_capstyle="round", zorder=6)
        ax.annotate("", xy=(75 * nx, Z_AX + 75 * nz), xytext=(0, Z_AX),
                    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.6), zorder=7)
        ax.text(86 * nx + (4 if nx >= 0 else 0), Z_AX + 86 * nz, lab, fontsize=8, ha="left", va="center")
    ax.plot(0, Z_AX, "o", color=ORANGE, ms=6, zorder=9)
    ax.text(0, -52, "Orange arrows: the way the mirror faces (towards the Sun).\n"
                    "The pole is never in the way: the lowest edge of the swinging\n"
                    "mirror stays clear of the head block (about 10 mm).",
            fontsize=9, ha="center", va="top")
    ax.set_xlim(-170, 250); ax.set_ylim(-100, Z_AX + R_BEZEL + 40); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def plan(ax):
    ax.set_title("From above: footprint against the goal post version", fontsize=11)
    ax.add_patch(Circle((0, 0), 240, facecolor="#f0f0f0", edgecolor="#888888", lw=1.2, ls="--", zorder=1))
    ax.add_patch(Circle((0, 0), 200, facecolor="none", edgecolor="#aaaaaa", lw=1.0, ls=":", zorder=1))
    ax.add_patch(Circle((0, 0), BASE_D / 2, facecolor=LIGHT, edgecolor=BLUE, lw=2.0, zorder=2))
    ax.add_patch(Ellipse((0, 0), 2 * R_BEZEL, 2 * R_BEZEL * math.sin(math.radians(62)), facecolor="none",
                         edgecolor=DARK, lw=1.0, ls="--", zorder=3))
    ax.plot([-R_BEZEL, R_BEZEL], [0, 0], color=DARK, lw=4, zorder=4)
    ax.plot([-CH_X - 6, CH_X + 6], [0, 0], color=ORANGE, lw=1.5, zorder=5)
    ax.plot(0, 0, "o", color=BLUE, ms=6, zorder=6)
    ax.text(0, -285, f"Pedestal base {BASE_D:.0f} mm across (blue)\n"
                      "Goal post base about 480 mm (grey dashed), platform 400 (dotted)\n"
                      f"Floor area: pedestal is about {100 * (BASE_D / 480) ** 2:.0f}% of the goal post",
            fontsize=9, ha="center", va="top")
    ax.text(0, 160, "dashed ellipse: the mirror\nedge at full tilt (62 deg)", fontsize=8, ha="center")
    ax.set_xlim(-260, 260); ax.set_ylim(-340, 260); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])


def main():
    fig = plt.figure(figsize=(23, 10.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 0.95, 0.8])
    a, b, c = (fig.add_subplot(gs[0, i]) for i in range(3))
    front(a); side(b); plan(c)
    fig.suptitle("Pedestal (vanity mirror) mount, 200 mm mirror, to scale (mm). Draft: nothing built or tested.",
                 fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT, dpi=100)
    # numbers
    cl = 2 * C_DIST / PITCH + (N_TOP + N_BOT) / 2 + ((N_TOP - N_BOT) / (2 * math.pi)) ** 2 * PITCH / C_DIST
    links = math.ceil(cl / 2) * 2
    print(f"Pivot axis height {Z_AX:.0f} mm, overall height {Z_AX + R_BEZEL:.0f} mm, base {BASE_D:.0f} x {BASE_H:.0f} mm")
    print(f"Chain: {cl:.1f} pitches -> {links} links, about {links * PITCH:.0f} mm; pitch circles {2 * R_TOP:.1f} and {2 * R_BOT:.1f} mm")
    print(f"Lowest swing of the bezel above the head block: {(Z_AX - R_BEZEL) - (T_TOP + HEAD_H):.0f} mm")
    print("Footprint ratio vs goal post (480 base):", f"{(BASE_D / 480) ** 2:.2f}")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
