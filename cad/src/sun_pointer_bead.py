#!/usr/bin/env python3
"""Sun pointer: the bead at the tip of a horizontal wall pole, polar (equatorial) gimbal. CadQuery concept model, nothing built.

A light rod hinged at the viewer point T points at the Sun. Spin about the polar axis once a day (stepper + worm), tilt by the
declination (stepper + worm sector on the rod hub). Power crosses the spinning joint through a slip ring. The bead hangs on a ball
joint at the end of a horizontal arm, so latitude and wall bearing are set once at install by turning the ball in its socket.

Local frame (axis frame): origin at the hinge T, +Z along the polar axis (towards the pole), +X = noon direction q0 (the Sun at
equinox noon), +Y = east. World frame (as in docs/sun-ring-concept.html): x east, y up, z south, T at the origin, the wall at z = -ARM.
World = x_l * q0 + y_l * east + z_l * p, with p = (0, sin lat, -cos lat), q0 = (0, cos lat, sin lat).

Rod angles: spin theta = -H (hour angle from noon), tilt about the hinge pin (local Y) by -dec so the rod swings toward the pole for
positive declination. The tip is then at T + PLEN * sun direction (checked in `--check`).

Usage (repo root): python3 cad/src/sun_pointer_bead.py [--check] [--render] [--step] [--lat 51.5] [--day 355] [--hour 9.5]
"""
import argparse
import math
import sys
from pathlib import Path

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import line_mirrors as lm  # noqa: E402
from line_mirrors import box, cyl_along, cylz, shp, sph  # noqa: E402

CAD = Path(__file__).resolve().parent.parent
OUT = CAD / "out" / "sun-pointer"
IMG = CAD / "media" / "previews" / "sun-pointer"
D2R = math.pi / 180

# ------------------------------------------------------------------ parameters (mm)
R_REAL = 300.0                     # size of R (the ring radius in the tool)
PLEN = 1.3 * R_REAL                # pointer length from the hinge to the tip bead centre = 390
ARM = 1.65 * R_REAL                # wall to T, horizontal
HR, HW = 46.0, 2.5                 # housing radius and wall
Z_FRONT, Z_REAR = 30.0, 123.0      # housing front face, rear cap start
BALL_Z, BALL_R = 170.0, 18.0       # ball centre on the polar axis (local), ball radius
SHAFT_OD, SHAFT_ID = 8.0, 6.0      # polar shaft tube
SPIN_C, GEAR_R, PIN_R = 28.0, 22.0, 6.0   # spin reduction: pinion on the 28BYJ-48 shaft, gear on the polar shaft (about 7:1 on top of the motor's 64:1)
WHEEL_R = 15.5                           # tilt worm sector radius (module 0.5, 60T) and tilt worm centre distance below

C_PRINT, C_BUY, C_METAL, C_ROD, C_TIP, C_WALL = "#e08a3c", "#9aa0a8", "#c8ccd2", "#26282b", "#f5b301", "#d8d4cc"

PARTS = {}                          # name -> dict(shape, grp, color); shapes in the LOCAL frame, grp: static / spin / tilt / world


def reg(name, shape, grp, color):
    PARTS[name] = dict(shape=shp(shape), grp=grp, color=color)


def rot_y(s, deg):
    return s.rotate((0, 0, 0), (0, 1, 0), deg)


def rot_z(s, deg):
    return s.rotate((0, 0, 0), (0, 0, 1), deg)


def pie_xz(r, a0, a1, y0, y1):
    """Sector in the XZ plane (angles from +X towards +Z), thickness y0..y1."""
    pts = [(0.0, 0.0)] + [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in [a0 + (a1 - a0) * k / 12 for k in range(13)]]
    w = cq.Workplane("XY").polyline(pts).close().extrude(y1 - y0).translate((0, 0, -(y1 - y0) / 2))
    return shp(w).rotate((0, 0, 0), (1, 0, 0), 90).translate(cq.Vector(0, (y0 + y1) / 2, 0))


def build():
    PARTS.clear()
    # ---------------- static (bead housing, drive, ball)
    hf = cylz(HR, Z_FRONT, Z_REAR).cut(cylz(HR - HW, Z_FRONT + 8, Z_REAR + 1))
    hf = hf.cut(cylz(8.0, Z_FRONT - 1, Z_FRONT + 5)).cut(cylz(5.0, Z_FRONT - 1, Z_FRONT + 9))
    reg("housing_front", hf, "static", C_PRINT)
    rc = cylz(HR, Z_REAR, Z_REAR + 8).union(cylz(14.0, Z_REAR + 8, 158.0)).cut(cylz(8.0, Z_REAR - 1, Z_REAR + 5)).cut(cylz(5.0, Z_REAR - 1, Z_REAR + 9))
    rc = rc.cut(cylz(6.2, Z_REAR + 8, 160.0))
    reg("rear_cap_neck", rc, "static", C_PRINT)
    for nm, z0 in (("bearing_front", Z_FRONT), ("bearing_rear", Z_REAR)):
        reg(nm, cylz(8.0, z0, z0 + 5).cut(cylz(4.0, z0 - 1, z0 + 6)), "static", C_BUY)
    reg("slip_ring", cylz(5.5, Z_REAR + 8, 154.0), "static", C_BUY)
    ball = sph(BALL_R, 0, 0, BALL_Z).cut(cylz(6.0, 150.0, BALL_Z))
    reg("ball", ball, "static", C_METAL)
    # spin drive: 28BYJ-48 with its axis parallel to the polar shaft, pinion meshing with a gear on the shaft; bracket to the housing wall
    zw = 75.0
    reg("spin_motor", cylz(14.0, zw + 3.0, zw + 22.0, 0.0, -SPIN_C), "static", C_BUY)
    reg("spin_pinion", cylz(PIN_R + 0.5, zw - 2.5, zw + 2.5, 0.0, -SPIN_C).union(cylz(2.5, zw - 2.5, zw + 3.5, 0.0, -SPIN_C)), "static", C_METAL)
    reg("spin_motor_mount", box(-22.0, 22.0, -HR + HW - 0.5, -SPIN_C + 16.0, zw + 22.0, zw + 26.0), "static", C_PRINT)
    reg("hall_post", box(-3.0, 3.0, 13.0, HR - HW + 0.5, zw + 5.5, zw + 12.0), "static", C_PRINT)
    reg("hall_sensor", box(-2.0, 2.0, 9.0, 13.0, zw + 5.5, zw + 8.5), "static", C_BUY)
    # ---------------- spinning assembly
    reg("polar_shaft", cylz(SHAFT_OD / 2, 14.0, Z_REAR + 8).cut(cylz(SHAFT_ID / 2, 13.0, Z_REAR + 9)), "spin", C_METAL)
    wh = cylz(GEAR_R + 0.5, zw - 2.5, zw + 2.5).union(cylz(7.0, zw + 2.5, zw + 8.0)).cut(cylz(4.0, zw - 3, zw + 9))
    reg("spin_wheel", wh, "spin", C_PRINT)
    reg("magnet", cylz(2.0, zw + 2.5, zw + 4.5, 0.0, 11.0), "spin", C_BUY)
    fork = box(-36.0, 16.0, -12.0, 12.0, 14.0, 20.0)
    fork = fork.union(box(-24.0, 16.0, 8.0, 12.0, -14.0, 14.0)).union(box(-24.0, 16.0, -12.0, -8.0, -14.0, 14.0)).union(box(-36.0, -15.0, -14.0, 14.0, -14.0, -11.0))
    fork = fork.cut(cylz(4.0, 13.0, 21.0)).cut(cyl_along("z", 3.6, -15.0, 21.0, -19.5, 0.0)).cut(cyl_along("y", 1.6, -13.0, 13.0, 0.0, 0.0))
    reg("fork", fork, "spin", C_PRINT)
    reg("dec_motor", cylz(14.0, -34.0, -14.0, -19.5, 0.0), "spin", C_BUY)
    reg("dec_worm", cylz(4.5, -9.0, 9.0, -19.5, 0.0).union(cylz(2.5, -14.0, 11.0, -19.5, 0.0)), "spin", C_METAL)
    reg("hinge_pin", cyl_along("y", 1.5, -12.0, 12.0, 0.0, 0.0), "spin", C_METAL)
    # ---------------- tilting group: hub with the worm sector, carbon rod, fibre, LED, tip bead
    hub = cyl_along("y", 8.0, -7.0, 7.0, 0.0, 0.0).union(pie_xz(WHEEL_R, 180 - 27, 180 + 27, -3.5, 3.5)).union(box(6.0, 24.0, -5.0, 5.0, -5.0, 5.0))
    hub = hub.cut(cyl_along("y", 1.6, -8.0, 8.0, 0.0, 0.0)).cut(cyl_along("x", 1.55, 10.0, 25.0, 0.0, 0.0))
    reg("rod_hub", hub, "tilt", C_PRINT)
    reg("rod", cyl_along("x", 1.5, 12.0, PLEN, 0.0, 0.0), "tilt", C_ROD)
    reg("fibre", cyl_along("x", 0.8, 20.0, PLEN, 0.0, -2.4), "tilt", "#f6d98a")
    reg("led", box(8.0, 14.0, -3.0, 3.0, -8.0, -5.0), "tilt", C_TIP)
    reg("tip_bead", sph(5.0, PLEN, 0.0, 0.0), "tilt", C_TIP)


def basis(lat):
    phi = lat * D2R
    q0 = (0.0, math.cos(phi), math.sin(phi))
    p = (0.0, math.sin(phi), -math.cos(phi))
    return q0, (1.0, 0.0, 0.0), p


def world_loc(lat):
    """Location that maps the local frame (X = q0, Y = east, Z = polar axis) into the world."""
    q0, _, p = basis(lat)
    return cq.Location(cq.Plane(origin=(0, 0, 0), xDir=q0, normal=p))


def sun_dir(H_deg, dec_deg, lat):
    """Unit Sun direction in world (x east, y up, z south), same formulas as the tool."""
    H, dl, phi = H_deg * D2R, dec_deg * D2R, lat * D2R
    E = -math.cos(dl) * math.sin(H)
    N = math.sin(dl) * math.cos(phi) - math.cos(dl) * math.cos(H) * math.sin(phi)
    U = math.sin(dl) * math.sin(phi) + math.cos(dl) * math.cos(H) * math.cos(phi)
    return (E, U, -N)


def decl(day):
    return -23.44 * math.cos(2 * math.pi * (day + 10) / 365)


def pose(H_deg, dec_deg, lat=51.5, world=True):
    """All parts for hour angle H (deg from noon) and declination. Returns [(name, shape, colour)]; world=False keeps the local frame."""
    if not PARTS:
        build()
    M = world_loc(lat)
    out = []
    for nm, d in PARTS.items():
        s = d["shape"]
        if d["grp"] == "tilt":
            s = rot_y(s, -dec_deg)
        if d["grp"] in ("tilt", "spin"):
            s = rot_z(s, -H_deg)
        if world:
            s = s.moved(M)
        out.append((nm, s, d["color"]))
    if world:
        out.extend(world_parts(lat))
    return out


def world_parts(lat):
    """Arm, ball socket, wall plate: built directly in world coordinates."""
    _, _, p = basis(lat)
    B = tuple(BALL_Z * c for c in p)                     # ball centre in world
    out = []
    sock = sph(BALL_R + 7.0, *B).cut(sph(BALL_R + 0.2, *B))
    cone = cq.Workplane("XY").add(cq.Solid.makeCone(0.0, math.tan(math.radians(40)) * 70.0, 70.0, cq.Vector(*B), cq.Vector(-p[0], -p[1], -p[2])))
    sock = sock.cut(cone)
    sock = sock.union(cyl_along("z", 10.0, B[2] - (BALL_R + 7.0) - 20.0, B[2] - (BALL_R + 4.0), B[0], B[1]))
    out.append(("ball_socket", shp(sock), C_PRINT))
    for k, sx in enumerate((-1, 1)):
        out.append((f"socket_grub_{k}", shp(cyl_along("x", 2.0, min(sx * 14.0, sx * (BALL_R + 17.0)), max(sx * 14.0, sx * (BALL_R + 17.0)), B[1], B[2])), C_METAL))
    z0 = -ARM
    tube = cyl_along("z", 10.0, z0 + 6.0, B[2] - (BALL_R + 7.0) - 20.0, B[0], B[1]).cut(cyl_along("z", 8.0, z0, B[2] - (BALL_R + 7.0) - 21.0, B[0], B[1]))
    out.append(("arm_tube", shp(tube), C_METAL))
    out.append(("arm_flange", shp(cyl_along("z", 38.0, z0, z0 + 6.0, B[0], B[1])), C_PRINT))
    for k, (dx, dy) in enumerate(((22, 22), (-22, 22), (22, -22), (-22, -22))):
        out.append((f"flange_screw_{k}", shp(cyl_along("z", 2.5, z0 - 8.0, z0 + 6.0, dx, B[1] + dy).union(cyl_along("z", 4.5, z0 + 6.0, z0 + 9.0, dx, B[1] + dy))), "#8d939a"))
    out.append(("wall_plate", shp(box(-260, 260, -300, 320, z0 - 14.0, z0)), C_WALL))
    return out


# ------------------------------------------------------------------ checks
ALLOW = [("polar_shaft", "bearing_"), ("polar_shaft", "spin_wheel"), ("polar_shaft", "fork"), ("spin_wheel", "spin_pinion"), ("spin_wheel", "magnet"),
         ("dec_worm", "rod_hub"), ("dec_worm", "fork"), ("dec_motor", "fork"), ("hinge_pin", "fork"), ("hinge_pin", "rod_hub"),
         ("rod_hub", "rod"), ("rod_hub", "led"), ("rod", "fibre"), ("rod", "tip_bead"), ("fibre", "tip_bead"), ("fibre", "rod_hub"),
         ("slip_ring", "rear_cap_neck"), ("slip_ring", "ball"), ("rear_cap_neck", "ball"), ("rear_cap_neck", "bearing_rear"), ("housing_front", "bearing_front"),
         ("spin_motor", "spin_pinion"), ("spin_motor", "spin_motor_mount"), ("spin_motor_mount", "housing_front"), ("hall_post", "housing_front"),
         ("hall_post", "hall_sensor"), ("ball", "ball_socket"), ("ball_socket", "arm_tube"), ("arm_tube", "arm_flange"), ("arm_flange", "wall_plate"),
         ("arm_flange", "flange_screw"), ("flange_screw", "wall_plate"), ("socket_grub", "ball_socket"), ("socket_grub", "ball"), ("housing_front", "rear_cap_neck"),
         ("polar_shaft", "slip_ring")]


def allowed(a, b):
    return any((a.startswith(u) and b.startswith(v)) or (a.startswith(v) and b.startswith(u)) for u, v in ALLOW)


def clashes(parts, tol=0.5):
    out = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _ in parts]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            a, b = bbs[i], bbs[j]
            if (a[2].xmax < b[2].xmin or b[2].xmax < a[2].xmin or a[2].ymax < b[2].ymin or b[2].ymax < a[2].ymin or a[2].zmax < b[2].zmin or b[2].zmax < a[2].zmin):
                continue
            if allowed(a[0], b[0]):
                continue
            try:
                v = a[1].intersect(b[1]).Volume()
            except Exception:
                v = -1
            if v > tol:
                out.append((a[0], b[0], round(v, 2)))
    return out


def run_checks(lat):
    build()
    print(f"== tip against the Sun formulas (lat {lat}) ==")
    worst = 0.0
    for day, hour in ((172, 12.0), (355, 9.5), (80, 15.0), (172, 4.0), (355, 0.0), (266, 18.5)):
        dec, H = decl(day), (hour - 12) * 15
        parts = pose(H, dec, lat)
        tip = next(s for n, s, _ in parts if n == "tip_bead").Center()
        s = sun_dir(H, dec, lat)
        want = tuple(PLEN * c for c in s)
        err = math.dist((tip.x, tip.y, tip.z), want)
        worst = max(worst, err)
        print(f"  day {day:3d} {hour:5.1f} h: dec {dec:+6.2f}, tip ({tip.x:+7.1f},{tip.y:+7.1f},{tip.z:+7.1f}) vs ({want[0]:+7.1f},{want[1]:+7.1f},{want[2]:+7.1f}): {err:.2f} mm")
    print(f"  worst tip error {worst:.3f} mm")
    print("== clash sweep (all parts, spin 0..330, tilt at both limits and the middle) ==")
    agg, n = {}, 0
    for dec in (-23.44, -12.0, 0.0, 12.0, 23.44):
        for H in range(0, 360, 30):
            n += 1
            for a, b, v in clashes(pose(float(H), dec, lat)):
                agg[(a, b)] = max(v, agg.get((a, b), 0))
    for (a, b), v in sorted(agg.items(), key=lambda kv: -kv[1]):
        print(f"  CLASH {a} / {b}: up to {v} mm3")
    print(f"  poses {n}, clashing pairs {len(agg)}")
    # clearances of the swinging rod and the nearest static parts
    print("== clearances at the tilt limits ==")
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    for dec in (-23.44, 23.44):
        mind = {}
        for H in range(0, 360, 30):
            parts = {nm: s for nm, s, _ in pose(float(H), dec, lat)}
            for rot in ("rod", "rod_hub", "tip_bead", "fork", "dec_motor"):
                for stat in ("housing_front", "ball_socket", "arm_tube", "wall_plate"):
                    d = BRepExtrema_DistShapeShape(parts[rot].wrapped, parts[stat].wrapped); d.Perform()
                    mind[(rot, stat)] = min(mind.get((rot, stat), 1e9), d.Value())
        worst = sorted((v, k) for k, v in mind.items())[:5]
        print(f"  tilt {dec:+.1f}: closest " + ", ".join(f"{v:.1f} mm {k[0]}/{k[1]}" for v, k in worst))


def cut_housing(parts, names=("housing_front", "rear_cap_neck", "spin_motor_mount", "hall_post")):
    """Cut the east half of the named parts away (local frame only) so the inside shows."""
    cutter = shp(box(-200, 200, 0, 200, -100, 300))
    return [(n, s.cut(cutter), c) if n in names else (n, s, c) for n, s, c in parts]


def render_all(lat, day, hour):
    IMG.mkdir(parents=True, exist_ok=True)
    dec, H = decl(day), (hour - 12) * 15
    world = pose(H, dec, lat)
    lm.render(world, IMG / "pointer-world.png", view=(-35, 14, 1800), focal=(0, 40, -150), size=(1800, 900))
    lm.render(world, IMG / "pointer-bead-world.png", view=(-40, 22, 520), focal=(0, 60, -40), size=(1700, 1000))
    loc = pose(H, dec, lat, world=False)
    keep = [x for x in loc if x[0] not in ("fibre",)]
    lm.render(cut_housing(keep), IMG / "pointer-local-cutaway.png", view=(-48, 22, 330), focal=(0, 0, 70), size=(1700, 1000))
    lm.render(cut_housing(keep, ("fork", "rod_hub", "polar_shaft")), IMG / "pointer-local-fork.png", view=(-35, 58, 150), focal=(-8, 0, 0), hide=("housing", "rear_cap", "rod", "tip_bead", "fibre", "spin", "polar", "bearing", "slip", "ball", "magnet", "hall"), size=(1500, 1000))
    lm.render(cut_housing(pose(H, 23.44, lat, world=False)), IMG / "pointer-local-tilt-max.png", view=(-40, 20, 420), focal=(40, 0, 40), size=(1700, 900))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, default=51.5)
    ap.add_argument("--day", type=int, default=355)
    ap.add_argument("--hour", type=float, default=9.5)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--step", action="store_true")
    a = ap.parse_args()
    if a.check:
        run_checks(a.lat)
        return
    if a.render:
        build()
        render_all(a.lat, a.day, a.hour)
    if a.step or not a.render:
        build()
        OUT.mkdir(parents=True, exist_ok=True)
        lm.save_step(pose((a.hour - 12) * 15, decl(a.day), a.lat), OUT / "sun-pointer-bead.step")


if __name__ == "__main__":
    main()
