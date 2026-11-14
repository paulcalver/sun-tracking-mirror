#!/usr/bin/env python3
"""Trace the pointing-hand silhouette from cad/src/assets/finger-source.jpg for the finger pointer plates.

Writes cad/src/assets/finger-outline.json: the closed outline in mm in the plate frame, plus numbers used by
finger_pointer.py. Plate frame (seen from the front): +X is the pointing direction (the index finger axis), +Z is the
thumb side, origin at the pivot (area centroid of the silhouette, so the plate is balanced about the axle).
Also writes the engraving artwork (light areas inside the outline, for black acrylic: the laser frosts the light areas
and leaves the ink black) as a PNG at 8 px per mm in the plate frame.

The source is a vintage engraving of unchecked licence: check it before publishing the artwork.
Usage (repo root): python3 cad/src/trace_finger.py
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
SRC = HERE / "assets" / "finger-source.jpg"
OUT = HERE / "assets" / "finger-outline.json"
HAND_LEN = 120.0                                            # mm, cuff to fingertip along the finger axis
PX_PER_MM = 8.0                                             # engraving artwork resolution


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def rdp(pts, eps):
    """Ramer-Douglas-Peucker on a closed polyline (list of (x, y)): split at the two points farthest apart."""
    pts = np.asarray(pts)
    i0 = int(np.argmin(pts[:, 0]))
    j0 = int(np.argmax(np.linalg.norm(pts - pts[i0], axis=1)))
    a, b = sorted((i0, j0))
    parts = [pts[a:b + 1], np.vstack([pts[b:], pts[:a + 1]])]

    def simp(p):
        if len(p) < 3:
            return p
        s, e = p[0], p[-1]
        d = e - s
        n = np.hypot(*d)
        q = p - s
        dist = np.abs(d[0] * q[:, 1] - d[1] * q[:, 0]) / n if n > 1e-9 else np.linalg.norm(q, axis=1)
        k = int(np.argmax(dist))
        if dist[k] > eps:
            return np.vstack([simp(p[:k + 1])[:-1], simp(p[k:])])
        return np.vstack([s, e])

    return np.vstack([simp(parts[0])[:-1], simp(parts[1])[:-1]])


def main():
    import contourpy
    gray = np.array(Image.open(SRC).convert("L")).astype(float)
    h, w = gray.shape
    ink = gray < 150
    pad = 24
    # silhouette = everything the outside background cannot reach once the ink outline is thickened to seal small gaps
    SEAL = 9                                                  # px: gaps up to 2 x SEAL in the outline are closed (the finger edge is dashed)
    bar = ndi.binary_dilation(np.pad(ink, pad), structure=disk(SEAL))
    lab, n = ndi.label(~bar)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    m = ~np.isin(lab, list(border))
    m = ndi.binary_opening(ndi.binary_erosion(m, structure=disk(SEAL - 1)), structure=disk(3))   # undo the seal
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(sizes)))
    m = m[pad:-pad, pad:-pad]

    # finger axis: centre line of the index finger over its lower part
    ys = np.where(m.any(axis=1))[0]
    ytip = ys.max()
    rows = np.arange(int(ytip - 120), int(ytip - 30))
    cx = []
    for y in rows:
        xs = np.where(m[y])[0]
        cx.append(0.5 * (xs.min() + xs.max()))
    b, a = np.polyfit(rows, cx, 1)
    d = np.array([b, 1.0]); d /= np.linalg.norm(d)         # pointing direction in image coords (x right, y down)
    nrm = np.array([d[1], -d[0]])                           # thumb side
    yy, xx = np.nonzero(m)
    cen = np.array([xx.mean(), yy.mean()])

    gen = contourpy.contour_generator(z=m.astype(float))
    line = max(gen.lines(0.5), key=len)
    px = ndi.gaussian_filter1d(line[:, 0], 2.5, mode="wrap")
    py = ndi.gaussian_filter1d(line[:, 1], 2.5, mode="wrap")
    poly = rdp(np.column_stack([px, py]), 0.6)

    def to_plate(p, s):
        v = (np.asarray(p, float) - cen)
        return np.column_stack([(v @ d) * s, (v @ nrm) * s])

    prj = (np.column_stack([px, py]) - cen) @ d
    s = HAND_LEN / (prj.max() - prj.min())                  # mm per px
    pl = to_plate(poly, s)
    area_mm2 = m.sum() * s * s
    # finger axis offset from the pivot, measured on the plate (line through the finger centre, direction d)
    ax_pt = np.array([a + b * ytip, ytip])
    off = float((ax_pt - cen) @ nrm) * s
    info = {
        "mm_per_px": s, "hand_len_mm": HAND_LEN, "tip_mm": float(prj.max() * s), "cuff_mm": float(prj.min() * s),
        "finger_axis_offset_mm": off, "area_mm2": float(area_mm2), "axis_tilt_deg": math.degrees(math.atan(b)),
        "outline": [[round(float(x), 3), round(float(z), 3)] for x, z in pl],
    }
    OUT.write_text(json.dumps(info))
    print(f"outline {len(pl)} points, scale {s:.4f} mm/px, area {area_mm2:.0f} mm2, tip {info['tip_mm']:.1f} cuff {info['cuff_mm']:.1f},"
          f" finger axis {off:+.1f} mm from the pivot, tilt {info['axis_tilt_deg']:.1f} deg")
    print(f"extent X {pl[:, 0].min():.1f}..{pl[:, 0].max():.1f}, Z {pl[:, 1].min():.1f}..{pl[:, 1].max():.1f}")
    r_in = min(np.min(np.hypot(*(pl - 0).T)), 1e9)
    print(f"nearest outline point to the pivot {r_in:.1f} mm (palm covers a disc this big around the pivot)")

    # engraving artwork in the plate frame, 8 px per mm
    xmin, xmax = math.floor(pl[:, 0].min()) - 1, math.ceil(pl[:, 0].max()) + 1
    zmin, zmax = math.floor(pl[:, 1].min()) - 1, math.ceil(pl[:, 1].max()) + 1
    W, H = int((xmax - xmin) * PX_PER_MM), int((zmax - zmin) * PX_PER_MM)
    gx, gz = np.meshgrid(xmin + (np.arange(W) + 0.5) / PX_PER_MM, zmax - (np.arange(H) + 0.5) / PX_PER_MM)
    # plate (X, Z) -> image coords: p = cen + (X d + Z nrm) / s
    ipx = cen[0] + (gx * d[0] + gz * nrm[0]) / s
    ipy = cen[1] + (gx * d[1] + gz * nrm[1]) / s
    val = ndi.map_coordinates(gray, [ipy, ipx], order=1, mode="constant", cval=255)
    sil = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sil).polygon([((x - xmin) * PX_PER_MM, (zmax - z) * PX_PER_MM) for x, z in pl], fill=255)
    inside = np.array(sil) > 0
    inside = ndi.binary_erosion(inside, structure=disk(3))   # keep the engraving 0.4 mm off the cut edge
    laser = inside & (val > 150)                             # frost the light areas, leave the ink black
    art = np.where(laser, 0, 255).astype(np.uint8)
    dpi = PX_PER_MM * 25.4
    Image.fromarray(art).save(HERE / "assets" / "finger-engrave-front.png", dpi=(dpi, dpi))
    print(f"engraving PNG {W} x {H} px at {dpi:.0f} dpi ({(xmax - xmin)} x {(zmax - zmin)} mm), origin (pivot) at x={-xmin * PX_PER_MM:.0f} px, y={zmax * PX_PER_MM:.0f} px")

    # overlay check picture
    ov = Image.open(SRC).convert("RGB")
    dr = ImageDraw.Draw(ov)
    dr.line([tuple(p) for p in poly] + [tuple(poly[0])], fill=(255, 0, 0), width=2)
    dr.ellipse([cen[0] - 5, cen[1] - 5, cen[0] + 5, cen[1] + 5], outline=(0, 0, 255), width=2)
    dr.line([(a + b * 300, 300), (a + b * 640, 640)], fill=(0, 160, 0), width=1)
    ov.save(HERE / "assets" / "finger-trace-check.png")


if __name__ == "__main__":
    main()
