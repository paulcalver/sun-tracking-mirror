#!/usr/bin/env python3
"""Line of 7 wall mirrors, travelling wave, PRINT-IN-PLACE version (CadQuery). Concept model, nothing built or printed.

Same brief as line_wave_full.py (7 x 50 mm mirrors, 70 mm pitch, +/-25 deg cone, pan + tilt + wave = 3 steppers), new mechanism:
every motion is a rotation, and each mirror is one print-in-place gimbal cartridge with captive joints.

Cartridge (one print, x7): pedestal (screwed to the back plate) + pan frame + carrier.
  - Pan frame: a vertical 8 mm journal through the pedestal block, with the pan crank printed above the block and the fork printed
    below it, so it can never come out. The journal runs in a diamond (square, turned 45 deg) bore.
  - Carrier: an axle captive between the fork cheeks on two 5 mm trunnions (diamond bores again), a spigot forward through the
    front plate to the mirror disc, and a 3 mm steel tail pin pointing down and back.
  - No springs: the mirror is front-heavy, so gravity seats every journal in a corner of its diamond bore and presses the tail
    against its cam. Play in the printed joints does not reach the mirror angle.
Pan: all seven cranks and a crank on a vertical NEMA 17 are joined by one tie bar (parallelogram, 1:1, no slides).
Tilt: a cradle shaft, directly on a NEMA 17, carries four arms; the arms carry the camshaft. Turning the cradle swings the cams.
Wave: seven eccentric drums on the camshaft (60 deg steps), turned by a 28BYJ-48 riding on the end arm. Each tail rests on a drum.

Frame (mm): X along the row (right), Y up, Z out of the wall, origin on the wall at the middle of the row.

Usage (repo root): python3 cad/src/line_wave_pip.py [--check] [--sun] [--render] [--step] [--print]
"""
import argparse
import math
import sys
from pathlib import Path

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import line_mirrors as lm  # noqa: E402
from line_mirrors import box, cyl_along, cylz, shp, sph  # noqa: E402

# ------------------------------------------------------------------ parameters (mm, deg): edit and re-run
N, PITCH, XS = lm.N, lm.PITCH, lm.XS
LIM = lm.LIM                                  # mirror cone half angle, 25
WAVE_E = 0.75                                 # cam eccentricity (wave throw at the tail)
DPH = 60.0                                    # wave phase step between neighbouring mirrors
ZP = 40.0                                     # pivot plane (pan axis and tilt axis cross here) above the wall
PL0, PL1 = ZP + 9.5, ZP + 12.5                # front plate (3 mm)
B_OFF, CARR_T, GLASS_T = 28.0, 3.0, 3.0       # mirror disc back face in front of the pivot, disc, glass
WALL, HY, XL, XR = 3.0, 48.0, -365.0, 365.0   # strip 730 x 96 x 52.5
JR, TR = 4.0, 2.5                             # pan journal and tilt trunnion radius
CLR = 0.25                                    # print-in-place clearance on each side of a journal
RP = 16.0                                     # pan crank radius
TH0 = 30.3                                    # tail angle from straight down, towards the wall, at zero tilt
TAIL_R, TAIL_L = 1.5, 35.0                    # 3 mm steel pin
SOCKET_L = 10.0                               # printed boss the pin presses into
DRUM_R, DRUM_L = 5.0, 20.0                    # cam drum
SY, SZ = -2.0, 24.15                          # cradle shaft (y, z): on the axis of a NEMA 17 sitting on the back plate
ARM, PSI0, PSI_MAX = 16.5, -167.0, 47.0       # cradle arm length, arm direction at mid travel (from +y towards +z), travel
ARMS_X = (-232.0, -105.0, 105.0, 232.0)
BLOCKS_X = (-175.0, -35.0, 35.0, 175.0)       # cradle shaft bearing blocks
XPM, ZPM = -290.0, 24.15                      # pan motor axis (vertical)
XTM = 266.0                                   # tilt motor face

C_LASER, C_PRINT, C_BUY, C_ENC, C_PIP = "#5aa0c8", "#e08a3c", "#9aa0a8", "#33363b", "#d9692b"
C_FORK, C_CARR = "#f0b24a", "#ece7dc"

lm.configure("wave")
lm.Z_PL0, lm.Z_PL1, lm.XL, lm.XR, lm.B_OFF, lm.CARR_T, lm.GLASS_T = PL0, PL1, XL, XR, B_OFF, CARR_T, GLASS_T
OUT, IMG = lm.OUT, lm.IMG


# ------------------------------------------------------------------ kinematics
def cam_centre(psi):
    a = math.radians(PSI0 + psi)
    return SY + ARM * math.cos(a), SZ + ARM * math.sin(a)


def tail_angle(cy, cz):
    """Tail angle (projected on the Y-Z plane) when the tail rests on a drum centred at (cy, cz); also the lever length."""
    vy, vz = cy, cz - ZP
    d = math.hypot(vy, vz)
    rho = DRUM_R + TAIL_R
    return math.degrees(math.atan2(-vz, -vy) - math.asin(rho / d)), math.sqrt(d * d - rho * rho)


def psi_for(theta_eff):
    lo, hi = -PSI_MAX, PSI_MAX
    f = lambda p: tail_angle(*cam_centre(p))[0] - theta_eff
    if f(lo) * f(hi) > 0:
        raise ValueError("tilt out of the cradle range")
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def solve(n_c, cam_deg):
    """Common normal n_c -> pan angle, cradle angle, and each mirror's tilt and normal with the wave added."""
    p = math.atan2(n_c[0], n_c[2])
    t = math.asin(max(-1, min(1, n_c[1])))
    eff = lambda th: math.degrees(math.atan(math.tan(math.radians(th)) * math.cos(p)))
    psi = psi_for(eff(TH0 - math.degrees(t)))
    cy, cz = cam_centre(psi)
    out = []
    for i in range(N):
        ph = math.radians(cam_deg + i * DPH)
        dy, dz = cy + WAVE_E * math.cos(ph), cz + WAVE_E * math.sin(ph)
        te, s = tail_angle(dy, dz)
        th = math.degrees(math.atan(math.tan(math.radians(te)) / math.cos(p)))
        ti = math.radians(TH0 - th)
        out.append(dict(t=ti, n=(math.sin(p) * math.cos(ti), math.sin(ti), math.cos(p) * math.cos(ti)), drum=(dy, dz), lever=s))
    return p, psi, out


# ------------------------------------------------------------------ parts
def diamond(axis, w, a0, a1, c1, c2):
    """Square bore of side w turned 45 deg, along x or y: a journal sits in one corner (two line contacts)."""
    if axis == "x":
        return shp(box(a0, a1, -w / 2, w / 2, -w / 2, w / 2)).rotate((0, 0, 0), (1, 0, 0), 45).translate((0, c1, c2))
    return shp(box(-w / 2, w / 2, a0, a1, -w / 2, w / 2)).rotate((0, 0, 0), (0, 1, 0), 45).translate((c1, 0, c2))


def pedestal():
    """Fixed part of the cartridge, pivot at the origin: block with the pan bore, column to the back plate, foot."""
    p = box(-8, 8, 9, 21, -ZP + 3, 8).union(box(-17, 17, 9, 21, -ZP + 3, -ZP + 8))
    return shp(p).cut(diamond("y", 2 * (JR + CLR), 8, 22, 0, 0))


def fork():
    """Pan frame: crank and pin above the pedestal block, journal through it, fork below it."""
    f = cyl_along("y", JR, 8.6, 21.5, 0, 0)
    f = f.union(box(-4.5, 4.5, 21.5, 24.5, -RP - 4.5, 4.5)).union(cyl_along("y", 2.0, 24.5, 30.5, 0, -RP))
    f = f.union(box(-10.5, 10.5, 6.0, 8.6, -4.2, 4.2))
    for sx in (1, -1):
        f = f.union(box(sx * 7.5, sx * 10.5, -4.2, 6.0, -4.2, 4.2) if sx > 0 else box(-10.5, -7.5, -4.2, 6.0, -4.2, 4.2))
    return shp(f).cut(diamond("x", 2 * (TR + CLR), -11, 11, 0, 0))


def carrier_core():
    """Axle with trunnions, spigot with the trim ball."""
    c = cyl_along("x", 3.5, -7.0, 7.0, 0, 0).union(cyl_along("x", TR, -10.5, 10.5, 0, 0))
    c = c.union(cylz(3.0, 0, 24.0)).union(sph(4.5, 0, 0, 24.0))
    a = math.radians(TH0)
    d = (0.0, -math.cos(a), -math.sin(a))
    pt = lambda k: tuple(k * v for v in d)
    c = c.union(lm.between((0, 0, 0), pt(SOCKET_L), 3.2))                 # boss for the tail pin
    return shp(c).cut(shp(lm.between(pt(2.0), pt(SOCKET_L + 1), TAIL_R)))


def tail():
    a = math.radians(TH0)
    d = (0.0, -math.cos(a), -math.sin(a))
    return shp(lm.between(tuple(2.0 * k for k in d), tuple(TAIL_L * k for k in d), TAIL_R))


def disc():
    """Mirror disc with a split socket on the trim ball (one M2 clamp screw, not drawn)."""
    d = cylz(lm.CARR_R, B_OFF, B_OFF + CARR_T).union(cylz(8.0, 19.5, B_OFF))
    return shp(d).cut(shp(sph(4.55, 0, 0, 24.0))).cut(shp(cylz(4.0, 19, 24.0)))


def arm(x, ang):
    a = box(x - 3, x + 3, 0, ARM, -5, 5).union(cyl_along("x", 6.0, x - 3, x + 3, 0, 0)).union(cyl_along("x", 5.5, x - 3, x + 3, ARM, 0))
    a = a.cut(cyl_along("x", 2.5, x - 4, x + 4, 0, 0)).cut(cyl_along("x", 2.6, x - 4, x + 4, ARM, 0))
    return shp(a).rotate((0, 0, 0), (1, 0, 0), ang).translate((0, SY, SZ))


def static_parts():
    P = []
    P.append(("back_plate", lm.outline(0, WALL), C_ENC))
    walls = lm.outline(WALL, PL0).cut(lm.outline(WALL - 1, PL0 + 1, WALL))
    P.append(("walls", walls, C_ENC))
    front = lm.outline(PL0, PL1)
    for x in XS:
        front = front.cut(cylz(11.0, PL0 - 1, PL1 + 1, x, 0))
    P.append(("front_plate", front, C_LASER))
    ped = pedestal()
    for i, x in enumerate(XS):
        P.append((f"pedestal_{i}x", ped.translate((x, 0, ZP)), C_PRINT))
    for k, x in enumerate(BLOCKS_X):
        b = box(x - 4, x + 4, SY - 4.5, SY + 4.5, WALL, SZ + 5.5).cut(cyl_along("x", 2.55, x - 5, x + 5, SY, SZ))
        P.append((f"cradle_block_{k}x", b, C_PRINT))
    # tilt motor on the cradle shaft axis, coupler; pan motor standing at the left
    P.append(("tilt_motor", lm.nema17((XTM, SY, SZ), (-1, 0, 0), shaft=10.0), C_BUY))
    P.append(("tilt_motor_mount", box(XTM - 3, XTM, SY - 24, SY + 24, WALL, 46.0).cut(cyl_along("x", 11.5, XTM - 4, XTM + 1, SY, SZ)), C_PRINT))
    P.append(("pan_motor", lm.nema17((XPM, 0.3, ZPM), (0, 1, 0), shaft=24.0), C_BUY))
    P.append(("pan_motor_mount", box(XPM - 25, XPM + 25, 0.3, 3.3, WALL, 46.0).cut(cyl_along("y", 11.5, 0, 4, XPM, ZPM)), C_PRINT))
    # electronics bay at the right end
    P.append(("pcb", box(308, 358, -32, 32, 7, 8.6), "#2e6b3a"))
    P.append(("pico", box(312, 333, -26, 25, 8.6, 12), "#3d8f52"))
    for k in range(3):
        P.append((f"driver_{k}x", box(338, 353, -28 + k * 20, -12 + k * 20, 8.6, 20), "#7a3fa0"))
    P.append(("dc_jack", box(348, 362, 34, 44, 8, 19), C_BUY))
    return [(n_, shp(s_), c_) for n_, s_, c_ in P]


STATIC = None
PARTS0 = None


def pose(n_c, cam_deg=0.0):
    global STATIC, PARTS0
    if STATIC is None:
        STATIC = static_parts()
        PARTS0 = dict(fork=fork(), core=carrier_core(), tail=tail(), disc=disc(),
                      glass=shp(cylz(lm.MIR_R, B_OFF + CARR_T, B_OFF + CARR_T + GLASS_T)))
    p, psi, mir = solve(n_c, cam_deg)
    pd = math.degrees(p)
    P = list(STATIC)
    info = dict(X=pd, Y=psi, D=cam_deg, normals=[], pivots=[], levers=[m["lever"] for m in mir], tilts=[math.degrees(m["t"]) for m in mir])
    for i, x in enumerate(XS):
        O = cq.Vector(x, 0, ZP)
        td = -math.degrees(mir[i]["t"])
        mv = lambda s: lm.rot_pitch_yaw(s, td, pd).translate(O)
        P.append((f"fork_{i}x", PARTS0["fork"].rotate((0, 0, 0), (0, 1, 0), pd).translate(O), C_FORK))
        P.append((f"stem_{i}", mv(PARTS0["core"]), C_PIP))
        P.append((f"tailpin_{i}x", mv(PARTS0["tail"]), C_BUY))
        P.append((f"carrier_{i}", mv(PARTS0["disc"]), C_CARR))
        P.append((f"glass_{i}", mv(PARTS0["glass"]), lm.GLASSC))
        info["normals"].append(mir[i]["n"])
        info["pivots"].append((x, 0.0, ZP))
    # pan tie bar: rests on the crank plates, one hole per pin, dog-leg to the motor crank pin
    dx, dz = -RP * math.sin(p), RP * (1 - math.cos(p))
    zb = ZP - RP
    bar = box(XPM - 7, XS[-1] + 8, 24.6, 27.6, zb - 5, zb + 5).union(box(XPM - 7, XPM + 7, 24.6, 27.6, ZPM - RP - 4.5, zb + 5))
    for x in XS:
        bar = bar.cut(cyl_along("y", 2.05, 24, 28, x, zb))
    bar = bar.cut(cyl_along("y", 2.05, 24, 28, XPM, ZPM - RP))
    P.append(("pan_tie_bar", shp(bar).translate((dx, 0, dz)), C_LASER))
    mc = cyl_along("y", 7.0, 5.0, 24.5, 0, 0).union(box(-4.5, 4.5, 21.5, 24.5, -RP - 4.5, 0)).union(cyl_along("y", 2.0, 24.5, 30.5, 0, -RP))
    mc = mc.cut(cyl_along("y", 2.5, 4, 24.4, 0, 0))
    P.append(("pan_motor_crank", shp(mc).rotate((0, 0, 0), (0, 1, 0), pd).translate((XPM, 0, ZPM)), C_PRINT))
    # cradle: shaft on the tilt motor, four arms, camshaft with drums, cam motor on the left arm
    ang = PSI0 + psi
    cy, cz = cam_centre(psi)
    cr = cyl_along("x", 2.5, -237.5, XTM - 13, SY, SZ).union(cyl_along("x", 9.5, XTM - 24, XTM - 4, SY, SZ).cut(cyl_along("x", 2.5, XTM - 13, XTM - 3, SY, SZ)))
    P.append(("cradle_shaft", cr, C_BUY))
    for k, x in enumerate(ARMS_X):
        P.append((f"cradle_arm_{k}x", arm(x, ang), C_PRINT))
    cs = cyl_along("x", 2.5, -240, 238, cy, cz).union(cyl_along("x", 4.0, -240, -236.5, cy, cz))
    P.append(("camshaft", cs, C_BUY))
    for i, x in enumerate(XS):
        dy_, dz_ = mir[i]["drum"]
        d = cyl_along("x", DRUM_R, x - DRUM_L / 2, x + DRUM_L / 2, dy_, dz_).cut(cyl_along("x", 2.5, x - 11, x + 11, cy, cz))
        P.append((f"cam_drum_{i}x", d, C_PRINT))
    b = math.radians(ang - 148.0)
    my, mz = cy + 8.0 * math.cos(b), cz + 8.0 * math.sin(b)
    P.append(("cam_motor_28byj", cyl_along("x", 14.0, -260, -241, my, mz), C_BUY))
    P.append(("cam_motor_plate", shp(cyl_along("x", 15.0, -241, -238, 0, 0).cut(cyl_along("x", 4.5, -242, -237, -8 * math.cos(b), -8 * math.sin(b)))).translate((0, my, mz)), C_PRINT))
    return [(n_, shp(s_), c_) for n_, s_, c_ in P], info


def common_normal(sun):
    return lm.unit(tuple(sun[k] + (0, 0, 1)[k] for k in range(3)))


# ------------------------------------------------------------------ checks
SKIP = ("back_platewalls", "wallsfront_plate")


def run_check():
    cases = [(0, 0, c) for c in (0, 90, 180, 270)]
    cases += [(LIM, phi, (phi * 2 + 30) % 360) for phi in range(0, 360, 45)]
    cases += [(LIM, phi, (phi + 200) % 360) for phi in range(0, 360, 45)]
    cases += [(12, phi, 45) for phi in range(0, 360, 90)]
    bad = 0
    for th, phi, cam in cases:
        parts, info = pose(lm.sun_dir(th, phi), cam)
        c = [x for x in lm.clashes(parts, tol=0.5) if x[0] + x[1] not in SKIP]
        low = min(s.BoundingBox().zmin for nm, s, _ in parts if nm.startswith(("glass", "carrier"))) - PL1
        bad += len(c)
        print(f"cone {th:2.0f} dir {phi:3.0f} cam {cam:3.0f}: pan {info['X']:+6.1f} cradle {info['Y']:+6.1f}  tilts {min(info['tilts']):+5.1f}..{max(info['tilts']):+5.1f}  "
              f"lever {min(info['levers']):4.1f}..{max(info['levers']):4.1f}  disc above plate {low:+5.1f}  clashes {c if c else 'none'}")
    print(f"{len(cases)} poses, {len(parts)} parts, clashing pairs: {bad}")
    print("-- wave size through the tilt range (mirror tilt swing, spot swing at 3 m) --")
    for td in (-25, -12, 0, 12, 25):
        n = (0.0, math.sin(math.radians(td)), math.cos(math.radians(td)))
        ts = [solve(n, c)[2][0]["t"] for c in range(0, 360, 10)]
        sw = math.degrees(max(ts) - min(ts)) / 2
        print(f"tilt {td:+3d}: cradle {solve(n, 0)[1]:+6.1f} deg, lever {solve(n, 0)[2][0]['lever']:4.1f} mm, wave +/-{sw:4.2f} deg, spot +/-{3000 * math.tan(math.radians(2 * sw)):4.0f} mm")


def run_sun():
    for alpha in (25, 50, 65):
        tot = dict(enc_in=0, enc_out=0, mir_in=0, mir_out=0, n=0)
        for phi in range(0, 360, 45):
            s = lm.sun_dir(alpha, phi)
            for cam in (0.0, 120.0):
                try:
                    parts, info = pose(common_normal(s), cam)
                except ValueError:
                    continue
                r = lm.ray_check(parts, info, s)
                for k in tot:
                    tot[k] += r[k]
        f = lambda k: 100.0 * tot[k] / max(1, tot["n"])
        print(f"Sun {alpha:2d} deg off the wall axis: enclosure blocks in {f('enc_in'):4.1f}% out {f('enc_out'):4.1f}%   "
              f"other mirrors block in {f('mir_in'):4.1f}% out {f('mir_out'):4.1f}%   ({tot['n']} rays)")


# ------------------------------------------------------------------ outputs
def make(step, render):
    s = lm.sun_dir(40, 20)
    parts, info = pose(common_normal(s), 60.0)
    OUT.mkdir(parents=True, exist_ok=True)
    if step:
        lm.save_step(parts, OUT / "line-mirrors-wave-pip.step")
    if not render:
        return
    IMG.mkdir(parents=True, exist_ok=True)
    flat, _ = pose((0, 0, 1), 0.0)
    cover = ("front_plate", "walls")
    lm.render(flat, IMG / "pip-front.png", view=(32, 9, 1150), focal=(-20, -15, 50))
    lm.render(parts, IMG / "pip-posed-rays.png", view=(15, 14, 1650), focal=(0, 0, 60), rays=lm.out_rays(info, s))
    lm.render(parts, IMG / "pip-mechanism.png", view=(12, 30, 1000), focal=(0, -10, 18), hide=cover + ("glass", "carrier"), size=(1900, 800))
    lm.render(parts, IMG / "pip-cartridge.png", view=(-38, 22, 200), focal=(0, 0, 32), hide=cover + ("_0", "_1", "_2", "_4", "_5", "_6"), size=(1400, 1000))
    lm.render(parts, IMG / "pip-cartridge-back.png", view=(205, 18, 210), focal=(0, 0, 28), hide=cover + ("back_plate", "pcb"), size=(1400, 1000))
    lm.render(parts, IMG / "pip-section.png", view=(90, 4, 330), focal=(0, 0, 40), cut_x=0.0, size=(1400, 1000))
    lm.render(parts, IMG / "pip-left-end.png", view=(20, 28, 360), focal=(-255, 0, 24), hide=cover + ("glass", "carrier"), size=(1500, 950))
    lm.render(parts, IMG / "pip-right-end.png", view=(-25, 28, 360), focal=(270, 0, 24), hide=cover + ("glass", "carrier"), size=(1500, 950))


def make_print():
    """Print-ready files for one test cartridge: three bodies in one file, joints captive, crank side down on the bed."""
    d = OUT / "print"
    d.mkdir(parents=True, exist_ok=True)
    bodies = [pedestal(), fork(), carrier_core()]
    cart = cq.Compound.makeCompound(bodies).rotate((0, 0, 0), (1, 0, 0), -90)       # +Y (crank) down
    cart = cart.translate((0, 0, -cart.BoundingBox().zmin))
    md = disc().rotate((0, 0, 0), (1, 0, 0), 180)                                  # mirror face down
    md = md.translate((0, 0, -md.BoundingBox().zmin))
    for nm, sh in (("pip-cartridge-test", cart), ("pip-mirror-disc", md)):
        cq.exporters.export(cq.Workplane("XY").add(sh), str(d / f"{nm}.step"))
        cq.exporters.export(cq.Workplane("XY").add(sh), str(d / f"{nm}.stl"), tolerance=0.01, angularTolerance=0.1)
        bb = sh.BoundingBox()
        print(f"Wrote {d / nm}.step/.stl  {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")


def main():
    ap = argparse.ArgumentParser()
    for f in ("--check", "--sun", "--render", "--step", "--print"):
        ap.add_argument(f, action="store_true")
    a = ap.parse_args()
    if a.check:
        run_check()
    if a.sun:
        run_sun()
    if a.render or a.step:
        make(a.step, a.render)
    if a.print:
        make_print()


if __name__ == "__main__":
    main()
