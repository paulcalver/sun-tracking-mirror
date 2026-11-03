#!/usr/bin/env python3
"""Labelled front and plan views of the test rig, to show how the parts link up.

Usage (from the repo root): python3 cad/src/rig_labelled_views.py
Writes cad/media/earlier-concepts/test-rig-labelled.png. Painter's-algorithm drawing, so small overlaps may look rough.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_joint_rig as R  # noqa: E402

COL = {"base_plate": "#d9d9d9", "bearing_block": "#4a6fa5", "motor_bracket": "#7fa3d1",
       "output_pulley_60T": "#f2b705", "lever_arm": "#2a9d8f", "encoder_bracket": "#8d6bb3",
       "ref_motor": "#555555", "ref_shaft_8mm": "#999999", "ref_pulley20": "#e08e00",
       "ref_magnet": "#d62828", "ref_belt": "#1b1b1b", "ref_bearing_rear": "#bbbbbb", "ref_bearing_front": "#bbbbbb"}


def collect():
    parts = {"base_plate": R.base_plate(), "bearing_block": R.bearing_block(),
             "motor_bracket": R.motor_bracket(), "output_pulley_60T": R.output_pulley(),
             "lever_arm": R.lever_arm(), "encoder_bracket": R.encoder_bracket()}
    parts.update(R.reference_parts())
    tris = []
    for name, wp in parts.items():
        v, t = R.tessellate(wp, 0.3)
        for tri in v[t]:
            tris.append((name, tri))
    return tris


def view(ax, tris, ix, iy, idepth, sign, title):
    items = []
    for name, tri in tris:
        depth = sign * tri[:, idepth].mean()
        items.append((depth, name, tri[:, [ix, iy]]))
    items.sort(key=lambda a: a[0])
    ax.add_collection(PolyCollection([i[2] for i in items], facecolors=[COL[i[1]] for i in items],
                                     edgecolors="none"))
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11)
    ax.set_xticks([]); ax.set_yticks([])


def note(ax, text, xy, xytext):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=9, ha="center",
                arrowprops=dict(arrowstyle="->", color="black", lw=0.8),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.6"))


def main():
    tris = collect()
    C, H = R.C, R.AXIS_Z
    fig, (a, b) = plt.subplots(1, 2, figsize=(15, 6.5))
    # front view: looking along the shaft from the lever end; X across, Z up (nearer = larger Y)
    view(a, tris, 0, 2, 1, 1, "FRONT VIEW: looking along the shaft")
    a.set_xlim(-160, 125); a.set_ylim(-12, 135)
    note(a, "lever arm (green)\nweights hang here", (-110, H), (-110, 105))
    note(a, "60-tooth pulley (yellow)\nsits behind the lever", (-8, H + 17), (-30, 118))
    note(a, "shaft end", (0, H), (-50, 85))
    note(a, "small pulley on\nthe motor shaft", (C, H), (C - 5, 118))
    note(a, "MOTOR (dark grey)\nbehind its bracket", (C + 12, H - 12), (C + 30, 105))
    note(a, "motor bracket\n(light blue)", (C + 28, H + 25), (C + 40, 80))
    note(a, "bearing block\n(dark blue)", (-15, H - 30), (-60, 10))
    note(a, "base plate", (-40, -3), (-85, -8))
    note(a, "belt (black): one loop round\nboth pulleys", (C / 2, H + 12), (C / 2 + 5, 84))
    # plan view
    view(b, tris, 0, 1, 2, 1, "PLAN VIEW: looking down from above")
    b.set_xlim(-160, 125); b.set_ylim(-65, 65)
    note(b, "belt (black) runs between\nthe two pulleys", (C / 2, 25.75), (C / 2 + 10, 55))
    note(b, "encoder bracket (purple)\nreads the magnet (red)\non the back of the shaft", (0, -38), (-70, -50))
    note(b, "lever arm", (-100, 45), (-100, 58))
    note(b, "motor body\n(grey)", (C, -10), (C + 28, -48))
    fig.suptitle("How the single-joint test rig links up: motor, belt, output shaft, lever and sensor", fontsize=12)
    fig.tight_layout()
    fig.savefig(Path(__file__).resolve().parent.parent / "media" / "test-rig" / "test-rig-labelled.png", dpi=110)


if __name__ == "__main__":
    main()
