#!/usr/bin/env python3
"""What the two motors must do each day for the concentric-shaft (option C) mount, London.

Pole angle = Sun azimuth (cumulative turn). Disc tilt = Sun elevation.
Because the disc's tilt is the DIFFERENCE between the inner shaft and the pole (1:1 mitre gears and belt),
the inner shaft must turn by  pole angle + tilt.  Net: both motors turn about 360 degrees a day.

Usage (from the repo root): python3 sim/arm/pole_drive_plan.py
Writes sim/arm/output/pole-drive-plan.png and prints speeds. Sun: sun-path/scripts/sun_path.py.
Sign and ratio conventions are my assumptions; they flip or scale with the real gearing.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sun-path" / "scripts"))
from sun_path import sun_position  # noqa: E402

DAYS = {"winter solstice": (2026, 12, 21), "spring equinox": (2026, 3, 20), "summer solstice": (2026, 6, 21)}
BLUE, ORANGE, GREY = "#4a6fa5", "#e8a400", "#777777"


def day(ymd):
    az, el = [], []
    for m in range(0, 24 * 60 + 1):
        t = datetime(*ymd, 23, 59, tzinfo=timezone.utc) if m == 1440 else datetime(*ymd, m // 60, m % 60, tzinfo=timezone.utc)
        a, e = sun_position(t)
        az.append(a); el.append(e)
    pole = np.degrees(np.unwrap(np.radians(az))); pole -= pole[0]
    tilt = np.array(el)
    inner = pole + tilt
    return np.arange(len(az)) / 60, pole, tilt, inner


def main():
    out = ROOT / "sim" / "arm" / "output"
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    for ax, (name, ymd) in zip(axes, DAYS.items()):
        h, pole, tilt, inner = day(ymd)
        ax.plot(h, pole, color=BLUE, lw=2, label="azimuth motor (pole turn so far)")
        ax.plot(h, inner, color=ORANGE, lw=2, label="tilt motor (inner shaft turn so far)")
        ax.plot(h, tilt, color=GREY, lw=2, ls="--", label="disc tilt = inner minus pole")
        ax.set_title(name); ax.set_xlabel("hour (UTC)"); ax.set_xlim(0, 24); ax.grid(alpha=0.3)
        sp, si = np.abs(np.diff(pole)).max(), np.abs(np.diff(inner)).max()
        print(f"{name:16s} pole net {pole[-1]:6.1f} deg, inner net {inner[-1]-inner[0]:6.1f} deg, "
              f"fastest pole {sp:.2f} deg/min, fastest inner {si:.2f} deg/min, tilt {tilt.min():.0f} to {tilt.max():.0f} deg")
    axes[0].set_ylabel("degrees"); axes[0].legend(fontsize=8, loc="upper left")
    fig.suptitle("Both motors turn about 360 degrees a day; the disc tilt is the gap between them", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out / "pole-drive-plan.png", dpi=110)


if __name__ == "__main__":
    main()
