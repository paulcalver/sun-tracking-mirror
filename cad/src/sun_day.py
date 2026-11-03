#!/usr/bin/env python3
"""Animation of the mirror following the Sun through one day in London, looped.

The mirror faces the Sun directly, so tilt = Sun elevation and the drum azimuth follows the Sun's compass bearing (+Y in
the model is north; the model turns anti-clockwise for +azimuth, so drum azimuth = -bearing). Below the horizon the mirror
keeps tracking, tilting down and the background goes dark (the +/-70 deg range covers it: -15 deg at the midnight low in June, -62 deg in December).
Sun position: NOAA low-precision formulas from sun-path/scripts/sun_path.py (London). Times shown are UK clock time.

Usage (from the repo root): python3 cad/src/sun_day.py [--date 2026-06-21] [--frames 72]
Writes cad/media/animations/gif-drafts/hinge-mirror-sun-<date>.gif (or -sculpture.gif with --single)
"""
import argparse
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "sun-path" / "scripts"))
import animate as an  # noqa: E402
import sun_path  # noqa: E402

m = an.m
DAY, TWILIGHT, NIGHT = np.array([0.86, 0.92, 0.96]), np.array([0.93, 0.62, 0.45]), np.array([0.07, 0.09, 0.19])


def sky(el):
    """Background colour from the Sun's elevation: day above 6 deg, orange twilight around the horizon, night below -12."""
    if el >= 6:
        return tuple(DAY)
    if el >= 0:
        return tuple(TWILIGHT + (DAY - TWILIGHT) * el / 6)
    if el >= -12:
        return tuple(NIGHT + (TWILIGHT - NIGHT) * (el + 12) / 12)
    return tuple(NIGHT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-06-21", help="day to follow (21 June 2026 is the summer solstice)")
    ap.add_argument("--single", action="store_true", help="finished sculpture only, no cutaway panel")
    ap.add_argument("--px", type=int, default=0, help="output width in pixels (square with --single); default 800 wide, or 512 with --single")
    ap.add_argument("--frames", type=int, default=72, help="frames across 24 hours")
    a = ap.parse_args()
    y, mo, d = (int(v) for v in a.date.split("-"))
    uk_offset = 1 if 3 < mo < 10 else 0                                  # BST in summer (good enough for solstice dates)
    m.build()
    parts = an.load()
    imgs = []
    for i in range(a.frames):
        minutes = 24 * 60 * i / a.frames
        utc = datetime(y, mo, d, tzinfo=timezone.utc) + timedelta(minutes=minutes - 60 * uk_offset)
        bearing, el = sun_path.sun_position(utc)
        tilt = max(-m.T_MAX, min(m.T_MAX, float(el)))
        az = (-float(bearing)) % 360.0
        b, e = math.radians(bearing), math.radians(el)
        sun_dir = (math.sin(b) * math.cos(e), math.cos(b) * math.cos(e), math.sin(e))
        hh, mm = divmod(int(minutes), 60)
        label = (f"London, {a.date}   {hh:02d}:{mm:02d}   Sun elevation {el:+.0f} deg, bearing {bearing:.0f} deg"
                 + ("   NIGHT" if el < -6 else "   twilight" if el < 6 else "   day"))
        # drum azimuth must be continuous across the 0/360 wrap: image only, no motion limit needed
        imgs.append(an.frame_image(parts, az, tilt, label=label, sun_dir=sun_dir, bg=sky(float(el)), single=a.single, px=a.px or None))
        if i % 8 == 0:
            print("frame", i + 1, "of", a.frames, flush=True)
    out = m.MEDIA / "animations" / "gif-drafts" / f"hinge-mirror-sun-{a.date}{'-sculpture' if a.single else ''}{f'-{a.px}' if a.px else ''}.gif"
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=110, loop=0, optimize=True)
    print("Wrote", out, f"{out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
