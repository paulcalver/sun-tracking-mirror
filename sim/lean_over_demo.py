#!/usr/bin/env python3
"""Animate two ways to point a disc at the Sun over one day in London.

Left:  "nod" mount. Vertical pole turns for azimuth, the disc tilts up and down every day.
Right: "lean-over" mount (equatorial). The pole leans at the latitude (it points at the
       sky's centre of rotation), turns at a steady 15 degrees an hour, and the disc
       keeps one fixed angle to the pole during the day (it changes only slowly with the seasons).

Both discs face the Sun at every moment. Sun position: sun-path/scripts/sun_path.py.

Usage (from the repo root):
    python3 sim/lean_over_demo.py [YYYY-MM-DD] [output.gif]
Defaults to 2026-11-01 and sim/output/lean-over-vs-nod.gif. Times are UTC (GMT in winter).
Axes: x east, y north, z up. Simulation only; the sizes are schematic.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sun-path" / "scripts"))
from sun_path import LAT, sun_position  # noqa: E402

LAT_R = np.radians(LAT)
POLE = np.array([0.0, np.cos(LAT_R), np.sin(LAT_R)])     # axis pointing at the celestial pole
U = np.array([1.0, 0.0, 0.0])                            # perpendicular to POLE (east)
V = np.array([0.0, -np.sin(LAT_R), np.cos(LAT_R)])       # perpendicular to POLE and U
DISC_R = 0.055
STEP_MIN = 20


def sun_vec(az, el):
    a, e = np.radians(az), np.radians(el)
    return np.array([np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), np.sin(e)])


def disc_poly(centre, normal, n=40):
    ref = np.array([0.0, 0.0, 1.0]) if abs(normal[2]) < 0.95 else np.array([1.0, 0.0, 0.0])
    a = np.cross(normal, ref); a /= np.linalg.norm(a)
    b = np.cross(normal, a)
    t = np.linspace(0, 2 * np.pi, n)
    return np.array([centre + DISC_R * (np.cos(k) * a + np.sin(k) * b) for k in t])


def scene(ax, kind, s, title):
    ax.cla()
    # table and compass
    ax.add_collection3d(Poly3DCollection([[(-0.25, -0.25, 0), (0.25, -0.25, 0), (0.25, 0.25, 0), (-0.25, 0.25, 0)]],
                                         facecolor="#e6e6e6", edgecolor="#aaaaaa", alpha=0.9))
    ax.text(0, 0.29, 0, "N", ha="center", fontsize=9, color="#555555")
    ax.text(0.29, 0, 0, "E", ha="center", fontsize=9, color="#555555")
    ax.plot([0, 0], [0, 0.0], [0, 0.03], color="#444444", lw=8)     # base plinth
    if kind == "nod":
        top = np.array([0.0, 0.0, 0.22])
        ax.plot(*zip([0, 0, 0.03], top), color="#4a6fa5", lw=4)
        centre = top + np.array([0, 0, 0.0])
    else:
        top = np.array([0.0, 0.0, 0.03]) + 0.22 * POLE
        ax.plot(*zip([0, 0, 0.03], top), color="#4a6fa5", lw=4)
        # dotted axis extension to show where the pole points (the sky's centre of rotation)
        ext = top + 0.20 * POLE
        ax.plot(*zip(top, ext), color="#4a6fa5", lw=1, ls=":")
        ax.text(*(ext + 0.01), "pole points\nat the sky's\ncentre of rotation", fontsize=7, color="#4a6fa5")
        centre = top
    poly = disc_poly(centre, s)
    ax.add_collection3d(Poly3DCollection([poly], facecolor="#1a1a1a", edgecolor="#777777", alpha=1.0))
    end = centre + 0.16 * s
    ax.plot(*zip(centre, end), color="#e8a400", lw=1.6, ls="--")
    ax.scatter(*end, color="#e8a400", s=40)
    ax.set_xlim(-0.25, 0.25); ax.set_ylim(-0.25, 0.25); ax.set_zlim(0, 0.45)
    ax.set_box_aspect((1, 1, 0.9))
    ax.set_axis_off()
    ax.view_init(elev=18, azim=-62)
    ax.set_title(title, fontsize=11)


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-11-01"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "sim" / "output" / "lean-over-vs-nod.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    y, m, d = (int(v) for v in day.split("-"))
    minutes = np.arange(0, 24 * 60 + 1, STEP_MIN)
    sv, az_l, el_l = [], [], []
    for mm in minutes:
        t = datetime(y, m, d, 0, 0, tzinfo=timezone.utc) if mm == 0 else \
            datetime(y, m, d, (mm // 60) % 24, mm % 60, tzinfo=timezone.utc) if mm < 1440 else \
            datetime(y, m, d, 23, 59, tzinfo=timezone.utc)
        az, el = sun_position(t)
        sv.append(sun_vec(az, el)); az_l.append(az); el_l.append(el)
    sv = np.array(sv)
    # nod mount: base turn = azimuth (cumulative), tilt = elevation
    turn_nod = np.degrees(np.unwrap(np.radians(az_l))); turn_nod -= turn_nod[0]
    tilt_nod = np.array(el_l)
    # lean-over mount: base turn = angle of the Sun's direction around the pole, tilt = angle from the pole
    psi = np.unwrap(np.arctan2(sv @ V, sv @ U))
    turn_eq = np.degrees(psi - psi[0])
    turn_eq *= np.sign(turn_eq[-1])
    tilt_eq = np.degrees(np.arccos(np.clip(sv @ POLE, -1, 1)))
    # convention for the chart: 90 minus tilt-from-pole is the Sun's declination
    dec = 90 - tilt_eq.mean()

    fig = plt.figure(figsize=(12, 7.6), dpi=70)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.7, 1])
    ax1 = fig.add_subplot(gs[0, 0], projection="3d")
    ax2 = fig.add_subplot(gs[0, 1], projection="3d")
    c1 = fig.add_subplot(gs[1, 0])
    c2 = fig.add_subplot(gs[1, 1])
    hours = minutes / 60
    for c, turn, tilt, lab in ((c1, turn_nod, tilt_nod, "disc height above the horizon"),
                               (c2, turn_eq, tilt_eq, "disc angle from the pole")):
        c.plot(hours, turn, color="#4a6fa5", label="base: total turn so far")
        c.plot(hours, tilt, color="#e8a400", label=lab)
        c.set_xlim(0, 24); c.set_ylim(-80, 380); c.set_xlabel("hour (UTC)"); c.set_ylabel("degrees")
        c.grid(alpha=0.3); c.legend(fontsize=8, loc="upper left")
    c1.set_title("Nod mount: the disc moves up and down every day", fontsize=10)
    c2.set_title(f"Lean-over mount: steady base turn, disc angle barely changes (sun declination {dec:+.1f} deg)",
                 fontsize=9)
    dots = [c1.plot([], [], "o", color="#4a6fa5")[0], c1.plot([], [], "o", color="#e8a400")[0],
            c2.plot([], [], "o", color="#4a6fa5")[0], c2.plot([], [], "o", color="#e8a400")[0]]
    fig.suptitle(f"Two ways to keep an obsidian disc facing the Sun, London, {day}", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    frames = []
    for i, mm in enumerate(minutes):
        s = sv[i]
        scene(ax1, "nod", s, f"Nod mount   {int(mm // 60):02d}:{int(mm % 60):02d}   Sun height {el_l[i]:+.0f} deg")
        scene(ax2, "lean", s, f"Lean-over mount   pole leans {LAT:.1f} deg")
        for dot, (x, yv) in zip(dots, [(hours[i], turn_nod[i]), (hours[i], tilt_nod[i]),
                                       (hours[i], turn_eq[i]), (hours[i], tilt_eq[i])]):
            dot.set_data([x], [yv])
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3]))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=110, loop=0, optimize=True)
    frames[len(frames) // 4].save(out.with_suffix(".png"))
    print(f"Wrote {out} ({len(frames)} frames). Disc angle from pole: {tilt_eq.min():.2f} to {tilt_eq.max():.2f} deg;"
          f" disc height range {tilt_nod.min():.0f} to {tilt_nod.max():.0f} deg.")


if __name__ == "__main__":
    main()
