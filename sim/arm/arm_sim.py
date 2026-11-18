#!/usr/bin/env python3
"""Simulate the Sun-pointing arm over London for the solstices and an equinox.

Arm model (4 degrees of freedom):
  yaw       rotation about the vertical axis at the base
  shoulder, elbow, wrist   three pitch joints, all in one vertical plane
The pointer is a rigid stick of length POINTER on the end of the wrist.

Pointing only fixes the yaw and the pointer's tilt in the arm's plane. The
shoulder and elbow are free, so a posture rule chooses where the wrist sits.
Rule used here ("clearance"): the wrist stays a fixed distance out from the
shoulder axis and rises as the pointer tips downwards, so the pointer tip
never goes below TIP_MIN_Z above the table.

Two ways to reach the same direction exist: "branch A" (yaw = azimuth, pointer
tilt = elevation) and "branch B" (yaw = azimuth + 180, tilt = 180 - elevation,
the arm leaning back over its own base). This script tests both.

Usage (from the repo root):
    python3 sim/arm/arm_sim.py [output_dir]
Writes a summary to the terminal, joint-angle CSVs and a PNG of poses.
Sun position comes from sun-path/scripts/sun_path.py (NOAA low precision).
All lengths in millimetres, angles in degrees.
"""
import csv
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

# ---- arm geometry (draft numbers, change freely) ----
SHOULDER_Z = 60.0   # shoulder axis height above the table
L1 = 160.0          # shoulder to elbow
L2 = 160.0          # elbow to wrist
POINTER = 90.0      # wrist to pointer tip
WRIST_R = 200.0     # wrist distance out from the shoulder axis (posture rule)
TIP_MIN_Z = 25.0    # lowest allowed pointer tip height above the table
ELBOW_MIN_Z = 25.0  # lowest allowed elbow height above the table

DAYS = {
    "winter solstice": (2026, 12, 21),
    "spring equinox": (2026, 3, 20),
    "summer solstice": (2026, 6, 21),
}


def ik(branch, az, el):
    """Return yaw, shoulder, elbow, wrist angles (degrees) and the geometry.

    Angles are measured in the arm's vertical plane from horizontal-forward,
    positive upwards. The shoulder angle is absolute; the elbow and wrist are
    relative to the link before them.
    """
    if branch == "A":
        yaw, phi = az, el
    else:
        yaw, phi = (az + 180.0) % 360.0, 180.0 - el
    phi_r = np.radians(phi)
    # posture rule: wrist rises as the pointer tips down
    wz = TIP_MIN_Z + POINTER * max(0.0, -np.sin(phi_r)) + 10.0
    wz = max(wz, SHOULDER_Z)
    dz, dr = wz - SHOULDER_Z, WRIST_R
    d = np.hypot(dr, dz)
    if d > L1 + L2 or d < abs(L1 - L2):
        return None
    gamma = np.arccos((L1**2 + d**2 - L2**2) / (2 * L1 * d))
    a1 = np.arctan2(dz, dr) + gamma                 # elbow-up solution
    ex, ez = L1 * np.cos(a1), L1 * np.sin(a1)
    a2 = np.arctan2(dz - ez, dr - ex)
    shoulder = np.degrees(a1)
    elbow = np.degrees(a2 - a1)
    wrist = np.degrees(phi_r - a2)
    pts = np.array([[0, 0], [0, SHOULDER_Z],
                    [ex, SHOULDER_Z + ez], [dr, wz],
                    [dr + POINTER * np.cos(phi_r), wz + POINTER * np.sin(phi_r)]])
    return yaw, shoulder, elbow, wrist, pts


def wrap180(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0


def run_day(branch, ymd):
    rows = []
    for m in range(24 * 60):
        t = datetime(*ymd, m // 60, m % 60, tzinfo=timezone.utc)
        az, el = sun_position(t)
        sol = ik(branch, az, el)
        rows.append((m, az, el, sol))
    return rows


def summarise(name, branch, rows):
    ok = [r for r in rows if r[3] is not None]
    miss = len(rows) - len(ok)
    yaw = np.degrees(np.unwrap(np.radians([r[3][0] for r in ok])))
    sh = np.array([r[3][1] for r in ok])
    el_ = np.array([r[3][2] for r in ok])
    wr = np.array([r[3][3] for r in ok])
    elev = np.array([r[2] for r in rows])
    min_tip = min(r[3][4][4][1] for r in ok)
    min_elbow = min(r[3][4][2][1] for r in ok)
    min_wrist = min(r[3][4][3][1] for r in ok)
    per_min = lambda a: np.abs(np.diff(a)).max()
    print(f"{name:16s} branch {branch}: elevation {elev.min():6.1f} to {elev.max():5.1f}"
          f" | yaw travel {yaw.max()-yaw.min():6.1f}"
          f" | shoulder {sh.min():5.1f}..{sh.max():5.1f}"
          f" | elbow {el_.min():6.1f}..{el_.max():6.1f}"
          f" | wrist {wr.min():6.1f}..{wr.max():6.1f}"
          f" | unreachable minutes {miss}")
    print(f"{'':16s}          lowest tip {min_tip:5.1f} mm, elbow {min_elbow:5.1f} mm, wrist {min_wrist:5.1f} mm"
          f" | fastest joint step per minute: yaw {per_min(yaw):.2f}, shoulder {per_min(sh):.2f},"
          f" elbow {per_min(el_):.2f}, wrist {per_min(wr):.2f} deg")
    return yaw


def draw(out):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    hours = [0, 3, 6, 9, 12, 15, 18, 21]
    for ax, (name, ymd) in zip(axes[0], DAYS.items()):
        for h in hours:
            t = datetime(*ymd, h, 0, tzinfo=timezone.utc)
            az, el = sun_position(t)
            sol = ik("A", az, el)
            if sol is None:
                continue
            pts = sol[4]
            col = plt.cm.viridis(h / 24)
            ax.plot(pts[:, 0], pts[:, 1], "-o", color=col, lw=2, ms=3, label=f"{h:02d}:00")
        ax.axhline(0, color="k", lw=2)
        ax.set_title(f"{name}: side view of arm plane")
        ax.set_aspect("equal")
        ax.set_xlabel("out from shoulder axis (mm)")
        ax.set_ylabel("height above table (mm)")
        ax.set_xlim(-60, 360)
        ax.set_ylim(-20, 340)
    axes[0][0].legend(fontsize=7, ncol=2, loc="upper right")
    for ax, (name, ymd) in zip(axes[1], DAYS.items()):
        rows = run_day("A", ymd)
        ok = [r for r in rows if r[3] is not None]
        m = np.array([r[0] for r in ok]) / 60
        yaw = np.degrees(np.unwrap(np.radians([r[3][0] for r in ok])))
        ax.plot(m, yaw, label="yaw")
        ax.plot(m, [r[3][1] for r in ok], label="shoulder")
        ax.plot(m, [r[3][2] for r in ok], label="elbow")
        ax.plot(m, [r[3][3] for r in ok], label="wrist")
        ax.set_title(f"{name}: joint angles, branch A")
        ax.set_xlabel("hour (UTC)")
        ax.set_ylabel("degrees")
        ax.set_xlim(0, 24)
        ax.grid(alpha=0.3)
    axes[1][0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=110)


def main():
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "sim" / "arm" / "output"
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"Arm: L1 {L1}, L2 {L2}, pointer {POINTER}, wrist out {WRIST_R}, shoulder height {SHOULDER_Z} mm\n")
    for branch in ("A", "B"):
        for name, ymd in DAYS.items():
            rows = run_day(branch, ymd)
            summarise(name, branch, rows)
            if branch == "A":
                slug = name.replace(" ", "-")
                with open(outdir / f"joints-{slug}.csv", "w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["minute_utc", "azimuth_from_north", "elevation",
                                "yaw", "shoulder", "elbow", "wrist"])
                    for m, az, el, sol in rows:
                        if sol is not None:
                            w.writerow([m, f"{az:.3f}", f"{el:.3f}"] + [f"{v:.3f}" for v in sol[:4]])
        print()
    draw(outdir / "arm-poses.png")
    print(f"Wrote {outdir}")


if __name__ == "__main__":
    main()
