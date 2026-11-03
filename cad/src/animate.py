#!/usr/bin/env python3
"""Animation of the v4 hinged mirror working: the mirror tilts through +/-70 deg, then the drum turns a full circle.

Left panel: the finished sculpture. Right panel: cutaway (cover, lid and glass hidden) so the lead screw, yoke, crank arm and
belt drive can be seen moving. Parts are tessellated once, then moved with numpy each frame (same transforms as posed()).

Usage (from the repo root): python3 cad/src/animate.py [--frames N]
Writes cad/media/animations/gif-drafts/hinge-mirror-animation.gif. Rough painter's-algorithm drawing, so small overlaps may look rough.
"""
import argparse
import io
import math
import sys
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hinge_mirror as m  # noqa: E402

OUT = m.MEDIA / "animations" / "gif-drafts" / "hinge-mirror-animation.gif"
HIDE_CUT = ("drum_top_plate", "drum_arm_relief", "base_top_frame", "base_wall", "mirror_glass", "mirror_back")


def subdivide(tris, max_edge):
    """Split big triangles so the painter's sort treats floors and plates sensibly."""
    out = []
    stack = list(tris)
    while stack:
        t = stack.pop()
        e = [np.linalg.norm(t[i] - t[(i + 1) % 3]) for i in range(3)]
        k = int(np.argmax(e))
        if e[k] <= max_edge:
            out.append(t)
            continue
        a, b, c = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
        mid = (a + b) / 2
        stack += [np.array([a, mid, c]), np.array([mid, b, c])]
    return np.array(out)


def colour(hexs):
    return np.array([int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def load():
    parts = []  # (name, group, triangles Nx3x3, base colour)
    for group, lst in (("base", m.base_parts), ("drum", m.drum_parts), ("slider", m.slider_parts), ("mirror", m.mirror_parts)):
        for nm, wp, col in lst:
            v, t = m._shape(wp).tessellate(0.8, 0.5)
            v = np.array([(p.x, p.y, p.z) for p in v])
            tris = v[np.array(t)]
            if nm.startswith("mirror_back"):
                tris = tris - np.array([0, 0.6, 0])      # drawing only: keeps the thin paint layer in front of the glass when seen from behind
            parts.append((nm, group, subdivide(tris, 45.0), colour(col)))
    return parts


def rz(v, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return v @ np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])


def rx(v, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return v @ np.array([[1, 0, 0], [0, c, s], [0, -s, c]])


def pose(group, tris, az, tilt):
    if group == "base":
        return tris
    if group == "mirror":
        tris = rx(tris, tilt) + np.array([0, 0, m.H])
    elif group == "slider":
        tris = tris + np.array([0, m.slider_y(tilt), 0])
    return rz(tris, az)


def frame_image(parts, az, tilt, label=None, sun_dir=None, bg=None, single=False, size=None, px=None):
    light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
    size = size or ((6.4, 6.4) if single else (10.0, 5.6))
    fig = plt.figure(figsize=size, dpi=(px / size[0] if px else 80), facecolor=bg if bg is not None else "white")
    fg = "black" if bg is None or np.mean(bg) > 0.5 else "white"
    views = (((), (16, 52), "Finished sculpture", 230, 420, 1.1), (HIDE_CUT, (32, 48), "Cutaway: cover, lid and glass hidden", 160, 110, 1.5))
    if single:
        views = ((views[0][0], views[0][1], "", 215, 400, 1.3),)
    for k, (hide, (elev, azim), title, r, zm, zoom) in enumerate(views):
        ax = fig.add_subplot(1, len(views), k + 1, projection="3d")
        tris, cols = [], []
        for nm, group, t0, base in parts:
            if any(h in nm for h in hide):
                continue
            t = pose(group, t0, az, tilt)
            n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
            nn = np.linalg.norm(n, axis=1)
            sh = 0.55 + 0.45 * np.abs(n @ light / np.where(nn > 1e-9, nn, 1))
            tris.append(t)
            cols.append(np.clip(base[None, :] * sh[:, None], 0, 1))
        ax.add_collection3d(Poly3DCollection(np.concatenate(tris), facecolors=np.concatenate(cols), edgecolors=np.concatenate(cols), linewidths=0.4))
        ax.set_xlim(-r, r); ax.set_ylim(-r, r); ax.set_zlim(0, zm)
        ax.set_box_aspect((1, 1, zm / (2 * r)), zoom=zoom); ax.set_axis_off(); ax.view_init(elev, azim)
        ax.set_title(title, fontsize=11, color=fg)
        ax.set_facecolor(bg if bg is not None else "white")
        if sun_dir is not None and k == 0:
            c = rz(rx(np.array([[0.0, 0.0, m.GLASS_Z0 + 133.0]]), tilt) + np.array([0, 0, m.H]), az)[0]
            e = c + 150.0 * np.asarray(sun_dir)
            ax.plot([c[0], e[0]], [c[1], e[1]], [c[2], e[2]], color="#f5b700", lw=1.5)
            ax.scatter([e[0]], [e[1]], [e[2]], s=120, color="#f5b700", edgecolors="#c98a00")
    fig.suptitle(label or f"Mirror tilt {tilt:+.0f} deg    drum azimuth {az:.0f} deg", fontsize=(9 if single else 12), y=0.97, color=fg)
    fig.subplots_adjust(0.0, 0.0, 1.0, 0.92, wspace=0.0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("P", palette=Image.ADAPTIVE, colors=128)


def timeline(n):
    """(az, tilt) per frame: tilt sweep 0 -> +70 -> -70 -> 0, then the drum turns a full circle at 40 deg tilt."""
    a, b = int(n * 0.45), n - int(n * 0.45)
    seq = [(0.0, m.T_MAX * math.sin(2 * math.pi * i / a)) for i in range(a)]
    ramp = max(3, b // 8)
    for i in range(b):
        r = min(1.0, (i + 1) / ramp, (b - i) / ramp)
        seq.append((360.0 * i / b, 40.0 * r))
    return seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=64)
    a = ap.parse_args()
    m.build()
    parts = load()
    imgs = []
    for i, (az, tilt) in enumerate(timeline(a.frames)):
        imgs.append(frame_image(parts, az, tilt))
        if i % 8 == 0:
            print("frame", i + 1, "of", a.frames, flush=True)
    imgs[0].save(OUT, save_all=True, append_images=imgs[1:], duration=90, loop=0, optimize=True)
    print("Wrote", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
