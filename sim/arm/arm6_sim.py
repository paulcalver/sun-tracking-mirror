#!/usr/bin/env python3
"""Six-joint, UR-style arm pointing at the Sun over London, with an expressive posture.

Kinematics: standard Denavit-Hartenberg chain with UR-like proportions (draft
numbers, approximate, scaled down by SCALE; not the manufacturer's data). Joints
1 to 3 are the base yaw and two pitch joints, joints 4 to 6 are the wrist.
The pointer is a stick along the last joint's axis (the tool axis).

Task: the tool axis must lie along the Sun direction (2 constraints). The other
freedom is spent on a slow, visible posture: the base, shoulder and elbow swing
gently through preferred angles while the wrist head keeps the pointer on the
Sun. The solver also
keeps every joint inside a limit, keeps links above the table, avoids links
touching each other, and avoids the wrist singularity (joint 5 near 0 or 180).

Usage (from the repo root):
    python3 sim/arm/arm6_sim.py [output_dir] [--five]
--five locks joint 6 (the roll about the pointer, which does not affect aim).
Sun position: sun-path/scripts/sun_path.py (NOAA low precision, London).
Lengths in metres, angles in degrees unless noted. Results are simulation only.
"""
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sun-path" / "scripts"))
from sun_path import sun_position  # noqa: E402

# ---- geometry (draft) ----
SCALE = 0.65
D1, A2, A3, D4, D5, D6 = np.array(
    [0.15185, -0.24355, -0.2132, 0.13105, 0.08535, 0.0921]) * SCALE
ALPHA = np.radians([90, 0, 0, 90, -90, 0])
DH_D = [D1, 0, 0, D4, D5, D6]
DH_A = [0, A2, A3, 0, 0, 0]
POINTER = 0.07          # flange to pointer tip, along the tool axis
TABLE_MARGIN = 0.02     # keep every link point at least this far above the table
LINK_GAP = 0.05         # keep non-neighbouring links at least this far apart
JOINT_LIMIT = np.radians([540.0, 175.0, 175.0, 175.0, 175.0, 175.0])  # base yaw may turn endlessly (slip ring); the rest are cable-limited
SIN_Q5_MIN = 0.25       # stay clear of the wrist singularity

# ---- posture: preferred angles for joints 1 to 3 (degrees), slow swings ----
HOME = np.radians([0.0, -80.0, -90.0])
SWING = np.radians([45.0, 25.0, 30.0])      # swing amplitude of base, shoulder, elbow
SWING_PERIOD_MIN = np.array([72.0, 40.0, 60.0])   # minutes per cycle, one per joint
SWING_PHASE = np.radians([0.0, 90.0, 200.0])
ROLL_PERIOD_MIN = 90.0  # decorative roll of joint 6 (six-joint mode only)

DAYS = {
    "winter solstice": (2026, 12, 21),
    "spring equinox": (2026, 3, 20),
    "summer solstice": (2026, 6, 21),
}


def fk(q):
    """Frame origins p[0..6] (p[6] = flange) and the tool frame T."""
    T = np.eye(4)
    pts = [T[:3, 3].copy()]
    for i in range(6):
        ct, st = np.cos(q[i]), np.sin(q[i])
        ca, sa = np.cos(ALPHA[i]), np.sin(ALPHA[i])
        A = np.array([[ct, -st * ca, st * sa, DH_A[i] * ct],
                      [st, ct * ca, -ct * sa, DH_A[i] * st],
                      [0, sa, ca, DH_D[i]],
                      [0, 0, 0, 1.0]])
        T = T @ A
        pts.append(T[:3, 3].copy())
    return np.array(pts), T


def skeleton(q):
    """Points along the arm: base, shoulder, elbow, wrist 1..3, flange, tip."""
    p, T = fk(q)
    tip = p[6] + POINTER * T[:3, 2]
    return np.array([p[0], p[1], p[2], p[3], p[4], p[5], p[6], tip]), T


def seg_dist(a0, a1, b0, b1):
    """Minimum distance between two line segments (small, numerically sampled)."""
    u = np.linspace(0, 1, 6)[:, None]
    A = a0 + u * (a1 - a0)
    B = b0 + u * (b1 - b0)
    return np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1)).min()


# pairs of segments (by skeleton point index) that must not come close
PAIRS = [((0, 1), (3, 4)), ((0, 1), (4, 5)), ((0, 1), (6, 7)), ((1, 2), (4, 5)),
         ((1, 2), (6, 7)), ((2, 3), (6, 7)), ((0, 2), (5, 7))]


def clearances(q):
    sk, T = skeleton(q)
    # sample along each link so a mid-link dip below the table is caught
    mids = (sk[:-1] + sk[1:]) / 2
    zmin = min(sk[1:, 2].min(), mids[1:, 2].min())
    gaps = [seg_dist(sk[a], sk[b], sk[c], sk[d]) for (a, b), (c, d) in PAIRS]
    return zmin, min(gaps)


def sun_vector(az, el):
    a, e = np.radians(az), np.radians(el)
    return np.array([np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), np.sin(e)])  # x east, y north, z up


def target_pose(minute, heading):
    """Preferred angles of joints 1 to 3 at this minute. The base yaw prefers to face
    the Sun's compass heading (so the wrist need not pan), swung by up to SWING[0]."""
    pref = HOME + SWING * np.sin(2 * np.pi * minute / SWING_PERIOD_MIN + SWING_PHASE)
    pref[0] += heading
    return pref


def target_roll(minute, five):
    # decorative roll about the pointer: swings back and forth inside the joint limit
    return 0.0 if five else np.radians(150.0) * np.sin(2 * np.pi * minute / ROLL_PERIOD_MIN)


def residual(x, s, pose_target, prev, five, roll):
    q = np.concatenate([x, [0.0]]) if five else x
    sk, T = skeleton(q)
    z = T[:3, 2]
    r = list((z - s) * 300.0)                      # aim (dominant)
    r += list(wrapdiffs(x[:3], pose_target) * 2.0)  # posture preference
    mids = (sk[:-1] + sk[1:]) / 2
    low = np.concatenate([sk[1:, 2], mids[1:, 2]])
    r += list(np.maximum(0.0, TABLE_MARGIN - low) * 200.0)
    r.append(max(0.0, SIN_Q5_MIN - abs(np.sin(q[4]))) * 40.0)
    for (a, b), (c, d) in PAIRS:
        r.append(max(0.0, LINK_GAP - seg_dist(sk[a], sk[b], sk[c], sk[d])) * 100.0)
    if prev is not None:
        r += list((x - prev) * 1.5)                # prefer smooth motion
    if not five:
        r.append(wrapdiff(x[5], roll) * 0.3)
    return np.array(r)


def wrapdiffs(a, b):
    return (a - b + np.pi) % (2 * np.pi) - np.pi


def wrapdiff(a, b):
    return (a - b + np.pi) % (2 * np.pi) - np.pi


def solve(s, pose_target, x0, prev, five, roll):
    lim = (JOINT_LIMIT - 1e-6)[:len(x0)]
    x0 = np.clip(x0, -lim, lim)
    res = least_squares(residual, x0, args=(s, pose_target, prev, five, roll),
                        bounds=(-lim, lim), method="trf", xtol=1e-10, ftol=1e-10, max_nfev=100)
    return res.x


def start_pose(s, pose_target, five, seed=0):
    """Multi-start search for a good first pose."""
    rng = np.random.default_rng(seed)
    best, best_cost = None, 1e9
    n = 5 if five else 6
    for _ in range(150):
        x0 = rng.uniform(-2.8, 2.8, n)
        x = solve(s, pose_target, x0, None, five, 0.0)
        c = (residual(x, s, pose_target, None, five, 0.0) ** 2).sum()
        if c < best_cost:
            best, best_cost = x, c
    return best


def run_day(ymd, five, step=2):
    xs, rows = [], []
    prev = None
    for m in range(0, 24 * 60 + 1, step):
        t = datetime(*ymd, (m // 60) % 24, m % 60, tzinfo=timezone.utc) if m < 24 * 60 else \
            datetime(*ymd, 23, 59, tzinfo=timezone.utc)
        az, el = sun_position(t)
        s = sun_vector(az, el)
        tgt = target_pose(m, np.arctan2(s[1], s[0]))
        roll = target_roll(m, five)
        if prev is None:
            x = start_pose(s, tgt, five)
            x = solve(s, tgt, x, None, five, roll)
        else:
            x = solve(s, tgt, prev, prev, five, roll)
        q = np.concatenate([x, [0.0]]) if five else x
        sk, T = skeleton(q)
        aim_err = np.degrees(np.arccos(np.clip(T[:3, 2] @ s, -1, 1)))
        zmin, gap = clearances(q)
        rows.append(dict(minute=m, az=az, el=el, q=np.degrees(q), aim_err=aim_err,
                         tip_err=np.degrees(np.abs(wrapdiffs(x[:3], tgt)).max()), zmin=zmin, gap=gap,
                         sin5=abs(np.sin(q[4])), sk=sk))
        prev = x
    return rows


def summarise(name, rows, five):
    q = np.array([r["q"] for r in rows])
    unwrapped = np.degrees(np.unwrap(np.radians(q), axis=0))
    step = rows[1]["minute"] - rows[0]["minute"]
    speed = np.abs(np.diff(unwrapped, axis=0)).max(axis=0) / step
    print(f"{name:16s} aim error max {max(r['aim_err'] for r in rows):.3f} deg"
          f" | posture off preference max {max(r['tip_err'] for r in rows):.0f} deg"
          f" | lowest point {1000*min(r['zmin'] for r in rows):.0f} mm"
          f" | closest links {1000*min(r['gap'] for r in rows):.0f} mm"
          f" | min |sin q5| {min(r['sin5'] for r in rows):.2f}")
    print(f"{'':16s} joint range (deg) " + "  ".join(
        f"J{i+1} {q[:, i].min():5.0f}..{q[:, i].max():4.0f}" for i in range(6)))
    print(f"{'':16s} net change over the day " + "  ".join(
        f"J{i+1} {unwrapped[-1, i]-unwrapped[0, i]:6.1f}" for i in range(6)))
    print(f"{'':16s} fastest joint (deg per minute) " + "  ".join(
        f"J{i+1} {speed[i]:.2f}" for i in range(6)))


def pose_figure(rows_by_day, out):
    fig = plt.figure(figsize=(15, 9))
    for k, (name, rows) in enumerate(rows_by_day.items()):
        ax = fig.add_subplot(2, 3, k + 1, projection="3d")
        for idx in range(0, len(rows), len(rows) // 6):
            r = rows[idx]
            sk = r["sk"]
            ax.plot(sk[:7, 0], sk[:7, 1], sk[:7, 2], "-o", ms=3, lw=2,
                    color=plt.cm.viridis(idx / len(rows)))
            ax.plot(sk[6:8, 0], sk[6:8, 1], sk[6:8, 2], "-", lw=4, color="orange")
        ax.set_title(f"{name}: poses every ~4 h")
        ax.set_xlim(-0.35, 0.35); ax.set_ylim(-0.35, 0.35); ax.set_zlim(0, 0.5)
        ax.set_box_aspect((1, 1, 0.7))
        ax2 = fig.add_subplot(2, 3, k + 4)
        m = np.array([r["minute"] for r in rows]) / 60
        q = np.degrees(np.unwrap(np.radians([r["q"] for r in rows]), axis=0))
        for i in range(6):
            ax2.plot(m, q[:, i], label=f"J{i+1}")
        ax2.set_xlabel("hour (UTC)"); ax2.set_ylabel("degrees"); ax2.grid(alpha=0.3)
        ax2.set_title(f"{name}: joint angles")
        if k == 0:
            ax2.legend(fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(out, dpi=100)
    plt.close(fig)


def animate(rows, out, frames=96):
    from PIL import Image
    imgs = []
    idxs = np.linspace(0, len(rows) - 1, frames).astype(int)
    for i in idxs:
        r = rows[i]
        sk = r["sk"]
        s = sun_vector(r["az"], r["el"])
        fig = plt.figure(figsize=(6, 6), dpi=80)
        ax = fig.add_subplot(111, projection="3d")
        gx, gy = np.meshgrid([-0.35, 0.35], [-0.35, 0.35])
        ax.plot_surface(gx, gy, 0 * gx, color="#dddddd", alpha=0.6)
        ax.plot(sk[:7, 0], sk[:7, 1], sk[:7, 2], "-o", color="#4a6fa5", lw=5, ms=6)
        ax.plot(sk[6:8, 0], sk[6:8, 1], sk[6:8, 2], "-", color="#e8a400", lw=6)
        tip = sk[7]
        ax.plot([tip[0], tip[0] + 0.5 * s[0]], [tip[1], tip[1] + 0.5 * s[1]],
                [tip[2], tip[2] + 0.5 * s[2]], ":", color="#e8a400", lw=1.5)
        ax.set_xlim(-0.35, 0.35); ax.set_ylim(-0.35, 0.35); ax.set_zlim(0, 0.6)
        ax.set_box_aspect((1, 1, 0.85))
        ax.set_title(f"{int(r['minute']//60):02d}:{int(r['minute']%60):02d} UTC  "
                     f"Sun az {r['az']:.0f} el {r['el']:.0f}", fontsize=10)
        ax.view_init(elev=18, azim=-60)
        fig.canvas.draw()
        imgs.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3]))
        plt.close(fig)
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=90, loop=0, optimize=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    five = "--five" in sys.argv
    outdir = Path(args[0]) if args else ROOT / "sim" / "arm" / ("output6-five" if five else "output6")
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"{'5' if five else '6'}-joint run. Scale {SCALE}; reach about {1000*(abs(A2)+abs(A3)):.0f} mm"
          f" (shoulder {1000*D1:.0f} mm high). Posture swings {np.degrees(SWING)} deg, periods {SWING_PERIOD_MIN} min.\n")
    rows_by_day = {}
    for name, ymd in DAYS.items():
        rows = run_day(ymd, five)
        rows_by_day[name] = rows
        summarise(name, rows, five)
        slug = name.replace(" ", "-")
        with open(outdir / f"joints-{slug}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["minute_utc", "azimuth_from_north", "elevation"] + [f"q{i+1}_deg" for i in range(6)])
            for r in rows:
                w.writerow([r["minute"], f"{r['az']:.3f}", f"{r['el']:.3f}"] + [f"{v:.3f}" for v in r["q"]])
        print()
    pose_figure(rows_by_day, outdir / "poses.png")
    animate(rows_by_day["winter solstice"], outdir / "winter-solstice.gif")
    print(f"Wrote {outdir}")


if __name__ == "__main__":
    main()
