#!/usr/bin/env python3
"""Wall-mounted tip-tilt sun mirror, two NEMA 11 push-screws (CadQuery). Concept model, nothing built or tested.

Frame (mm, Fusion-friendly, Y up): X right, Y up, Z out of the wall towards the viewer. Origin on the wall, centre of
the housing. The mirror reflects the Sun to a fixed target, so its normal bisects the Sun and target directions.

Mechanism:
  - 60 mm round x 3 mirror glued on a printed carrier. The carrier sits on a steel ball (pivot) at the mirror centre.
  - Two NEMA 11 motors, each with a lead screw that pushes the carrier from behind through a steel ball on a flat
    magnet pad (no joint, no backlash, free to slide a little as the mirror tilts). The magnets also hold the carrier on.
  - The two push points sit low, left and right of centre, so both rods together = pitch, one against the other = yaw.
  - Screws are keyed by a D flat in a small plate on the motor face so they push instead of spinning.
  - Controller stack sits above the motors, behind the mirror.

Usage (from the repo root):
  python3 cad/src/wall_mirror_nema11.py [--pitch DEG --yaw DEG | --sun AZ EL] [--wall-bearing DEG] [--target X Y Z]
                                        [--check] [--day MM-DD --lat DEG --lon DEG] [--no-render]
Writes cad/out/earlier-concepts/wall-mirror/wall-mirror-nema11.step and renders to cad/media/previews/wall-mirror/.
"""
import argparse
import math
from pathlib import Path

import cadquery as cq

CAD = Path(__file__).resolve().parent.parent
OUT = CAD / "out" / "earlier-concepts" / "wall-mirror"
IMG = CAD / "media" / "previews" / "wall-mirror"

# ------------------------------------------------------------------ parameters (mm)
MIR = 60.0                                   # round glass, diameter
GLASS_T, CARR_T, CARR = 3.0, 6.0, 58.0       # glass, printed carrier thickness and side
PIV_Z = 66.0                                 # pivot ball centre height above the wall (carrier back face, neutral)
PIV_R, POST_R = 4.0, 2.0                     # pivot steel ball and its post
BALL_R = 3.0                                 # push balls
PUSH_X, PUSH_Y = 15.3, -16.8                 # push point positions in the carrier plane (left/right, low)
MAG_R, MAG_T = 5.0, 2.0                      # 10 x 2 magnet pads
HOUSE, WALL_T = 35.0, 2.0                    # housing half width (70 square), wall thickness
Z_FRONT = 81.0                               # front face of the bezel
BEZEL_T = 3.0
BACK_T = 3.0
DECK_Z0, DECK_Z1 = 10.0, 13.0                # printed motor deck
N11 = 28.2                                   # NEMA 11 face
N11_L = 31.5                                 # motor body length (single stack)
MOT_Z0, MOT_Z1 = DECK_Z1, DECK_Z1 + N11_L    # 13 .. 44.5
BOSS_R, BOSS_T = 11.0, 1.6
ROD_R, ROD_L, FLAT = 2.5, 44.0, 1.9          # screw, length, D flat plane x = 1.9
KEY_T = 2.0
TRAVEL = 13.0                                # +/- screw travel from neutral the geometry allows
LIM = 25.0                                   # mirror normal cone half angle from the wall normal, deg (Sun 50 deg off the wall normal)

STEEL, BLACK, GREY, PRINT, GLASS, MAGC, TEAL, GREEN = (
    "#b9bec4", "#3b3e43", "#7d8288", "#ece7dc", "#b4d3e8", "#b8423a", "#2f7f86", "#2e7d4f")


# ------------------------------------------------------------------ helpers
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def sph(r, x=0.0, y=0.0, z=0.0):
    return cq.Workplane("XY").sphere(r).translate((x, y, z))


def shp(w):
    return w.val() if hasattr(w, "val") else w


def nema11():
    """Local frame: flange face at z=0, body behind it, screw bore through."""
    h = N11 / 2
    m = box(-h, h, -h, h, -N11_L, 0).edges("|Z").chamfer(2.0)
    m = m.union(cylz(BOSS_R, 0, BOSS_T))
    return m.cut(cylz(2.7, -N11_L - 1, BOSS_T + 1))


def rod(z0, z1):
    r = cylz(ROD_R, z0, z1).intersect(box(-5, FLAT, -5, 5, z0 - 1, z1 + 1))
    return r


def key_plate():
    z0 = MOT_Z1 + BOSS_T
    p = box(-7, 7, -7, 7, z0, z0 + KEY_T)
    hole = cylz(2.6, z0 - 1, z0 + KEY_T + 1).intersect(box(-5, 2.0, -5, 5, z0 - 1, z0 + KEY_T + 1))
    return p.cut(hole)


def rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mv(A, v):
    return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]


def normal_of(pitch, yaw):
    return mv(mm(ry(yaw), rx(pitch)), [0, 0, 1])


def tilt_of(pitch, yaw):
    return math.degrees(math.acos(normal_of(pitch, yaw)[2]))


def py_from_cone(theta, phi):
    """Pitch/yaw for a normal tilted theta from the wall normal towards direction phi (0 = right, 90 = up)."""
    t, f = math.radians(theta), math.radians(phi)
    n = (math.sin(t) * math.cos(f), math.sin(t) * math.sin(f), math.cos(t))
    return math.degrees(-math.asin(n[1])), math.degrees(math.atan2(n[0], n[2]))


# ------------------------------------------------------------------ pointing maths
def wall_frame(bearing):
    b = math.radians(bearing)
    z = (math.sin(b), math.cos(b), 0.0)          # wall normal in ENU (east, north, up)
    y = (0.0, 0.0, 1.0)
    x = (-math.cos(b), math.sin(b), 0.0)
    return x, y, z


def sun_enu(az, el):
    a, e = math.radians(az), math.radians(el)
    return (math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))


def to_wall(v, bearing):
    x, y, z = wall_frame(bearing)
    return tuple(sum(v[i] * f[i] for i in range(3)) for f in (x, y, z))


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def pose_for_sun(az, el, bearing, target):
    """Mirror pitch/yaw (deg) so the Sun at (az, el) reflects to `target` (wall-frame direction). None if the Sun or
    target is behind the wall."""
    s = to_wall(sun_enu(az, el), bearing)
    t = unit(target)
    if s[2] <= 0.02 or t[2] <= 0.02:
        return None
    n = unit(tuple(s[i] + t[i] for i in range(3)))
    return math.degrees(-math.asin(n[1])), math.degrees(math.atan2(n[0], n[2])), s, t


def sun_position(lat, lon, month, day, hour_utc):
    """Low precision Sun az/el (deg). Good to about 0.5 deg, enough for a window summary."""
    n = sum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][:month - 1]) + day
    dec = math.radians(23.44) * math.sin(math.radians(360 / 365 * (n - 81)))
    b = math.radians(360 / 364 * (n - 81))
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)      # minutes
    solar = hour_utc + lon / 15 + eot / 60
    h = math.radians(15 * (solar - 12))
    la = math.radians(lat)
    el = math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(h))
    az = math.atan2(math.sin(h), math.cos(h) * math.sin(la) - math.tan(dec) * math.cos(la)) + math.pi
    return math.degrees(az) % 360, math.degrees(el)


# ------------------------------------------------------------------ parts
def static_parts():
    P = []
    P.append(("back_plate", box(-HOUSE, HOUSE, -HOUSE, HOUSE, 0, BACK_T)
              .cut(cylz(2.0, -1, BACK_T + 1, 28, 28)).cut(cylz(2.0, -1, BACK_T + 1, -28, 28))
              .cut(cylz(2.0, -1, BACK_T + 1, 28, -28)).cut(cylz(2.0, -1, BACK_T + 1, -28, -28)), BLACK))
    shell = box(-HOUSE, HOUSE, -HOUSE, HOUSE, BACK_T, Z_FRONT - BEZEL_T).cut(
        box(-HOUSE + WALL_T, HOUSE - WALL_T, -HOUSE + WALL_T, HOUSE - WALL_T, BACK_T - 1, Z_FRONT))
    P.append(("housing_walls", shell, BLACK))
    bez = box(-HOUSE, HOUSE, -HOUSE, HOUSE, Z_FRONT - BEZEL_T, Z_FRONT).cut(cylz(HOUSE - WALL_T, Z_FRONT - BEZEL_T - 1, Z_FRONT + 1))
    P.append(("bezel", bez, BLACK))
    deck = box(-HOUSE + WALL_T, HOUSE - WALL_T, -HOUSE + WALL_T, HOUSE - WALL_T, DECK_Z0, DECK_Z1)
    for sx in (-1, 1):
        deck = deck.cut(cylz(4.2, DECK_Z0 - 1, DECK_Z1 + 1, sx * PUSH_X, PUSH_Y))
    deck = deck.cut(cylz(3.0, DECK_Z0 - 1, DECK_Z1 + 1))
    P.append(("motor_deck", deck, GREY))
    P.append(("pivot_post_ball", cylz(POST_R, BACK_T, PIV_Z - PIV_R + 0.5).union(sph(PIV_R, 0, 0, PIV_Z)), STEEL))
    P.append(("controller_stack", box(-25, 25, 6, 28, DECK_Z1, DECK_Z1 + 16), GREEN))
    for i, sx in enumerate((-1, 1)):
        mx, my = sx * PUSH_X, PUSH_Y
        P.append((f"nema11_{'LR'[i]}", nema11().translate((mx, my, MOT_Z1)), TEAL))
        P.append((f"key_plate_{'LR'[i]}", key_plate().translate((mx, my, 0)), GREY))
    return P


def carrier_local():
    """Built in the carrier frame: origin at the pivot ball centre, +Z toward the viewer, back face at z = 0."""
    c = cylz(CARR / 2, 0, CARR_T)
    c = c.cut(sph(PIV_R + 0.1))
    c = c.cut(cylz(3.0, PIV_R + 0.1, PIV_R + 0.1 + 1.5))
    for sx in (-1, 1):
        c = c.cut(cylz(MAG_R, 0, MAG_T, sx * PUSH_X, PUSH_Y))
    parts = [("carrier", c, PRINT),
             ("mirror_glass", cylz(MIR / 2, CARR_T, CARR_T + GLASS_T), GLASS),
             ("pivot_magnet", cylz(3.0, PIV_R + 0.1, PIV_R + 0.1 + 1.5), MAGC)]
    for i, sx in enumerate((-1, 1)):
        parts.append((f"pad_magnet_{'LR'[i]}", cylz(MAG_R, 0, MAG_T, sx * PUSH_X, PUSH_Y), MAGC))
    return parts


def push_ball_z(pitch, yaw, sx):
    """Height of the push ball centre when it just touches the carrier back plane at the fixed screw axis."""
    n = normal_of(pitch, yaw)
    xi, yi = sx * PUSH_X, PUSH_Y
    return PIV_Z + (-BALL_R - n[0] * xi - n[1] * yi) / n[2]


def pose(pitch, yaw):
    parts = static_parts()
    R = mm(ry(yaw), rx(pitch))
    for nm, w, col in carrier_local():
        s = shp(w).rotate((0, 0, 0), (1, 0, 0), pitch).rotate((0, 0, 0), (0, 1, 0), yaw).translate((0, 0, PIV_Z))
        parts.append((nm, s, col))
    info = {}
    for i, sx in enumerate((-1, 1)):
        zc = push_ball_z(pitch, yaw, sx)
        xi, yi = sx * PUSH_X, PUSH_Y
        top = zc - 2.0
        parts.append((f"screw_ball_{'LR'[i]}", rod(top - ROD_L, top).translate((xi, yi, 0)).union(sph(BALL_R, xi, yi, zc)), STEEL))
        n = normal_of(pitch, yaw)
        contact = (xi + BALL_R * n[0], yi + BALL_R * n[1], zc + BALL_R * n[2])
        pad = mv(R, [xi, yi, 0])
        pad = (pad[0], pad[1], pad[2] + PIV_Z)
        info[f"{'LR'[i]}"] = dict(ext=zc - (PIV_Z - BALL_R), slip=math.dist(contact[:2], pad[:2]), bottom=top - ROD_L)
    return [(n, shp(s), c) for n, s, c in parts], info


# ------------------------------------------------------------------ checks and export
def cqc(h):
    h = h.lstrip("#")
    return cq.Color(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, 1.0)


def assemble(parts):
    a = cq.Assembly(name="wall_mirror_nema11")
    for nm, s, col in parts:
        a.add(s, name=nm, color=cqc(col))
    return a


def clashes(parts, tol=1.0):
    out = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _ in parts]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            a, b = bbs[i], bbs[j]
            if (a[2].xmax < b[2].xmin or b[2].xmax < a[2].xmin or a[2].ymax < b[2].ymin or b[2].ymax < a[2].ymin
                    or a[2].zmax < b[2].zmin or b[2].zmax < a[2].zmin):
                continue
            try:
                v = a[1].intersect(b[1]).Volume()
            except Exception:
                v = -1
            if v > tol:
                out.append((a[0], b[0], round(v, 1)))
    return out


def run_checks():
    print(f"Mirror normal within a {LIM:.0f} deg cone of the wall normal; screw travel allowed +/-{TRAVEL:.0f} mm from neutral")
    worst, rows = 0.0, []
    for theta in (0, LIM, LIM + 5):
        for phi in ((0,) if theta == 0 else range(0, 360, 45)):
            p, y = py_from_cone(theta, phi)
            parts, info = pose(p, y)
            c = clashes(parts)
            ext = [info['L']['ext'], info['R']['ext']]
            slip = max(info['L']['slip'], info['R']['slip'])
            bottom = min(info['L']['bottom'], info['R']['bottom'])
            bad = bool(c) or (theta <= LIM and (max(abs(e) for e in ext) > TRAVEL + 0.01 or slip > MAG_R - 1 or bottom < BACK_T + 1))
            if theta <= LIM:
                worst = max(worst, max(abs(e) for e in ext))
            print(f"tilt {theta:4.0f} dir {phi:3.0f}: pitch {p:+5.1f} yaw {y:+5.1f}  ext L {ext[0]:+5.1f} R {ext[1]:+5.1f}  "
                  f"tail low {bottom:5.1f}  pad slip {slip:3.1f}  clashes {c if c else 'none'}{'  <-- check' if bad else ''}")
    print(f"Largest screw movement from neutral inside the cone: {worst:.1f} mm")


def day_summary(month, day, lat, lon, bearing, target):
    inr, tot, rows = 0, 0, []
    for k in range(0, 24 * 6):
        h = k / 6
        az, el = sun_position(lat, lon, month, day, h)
        if el < 0:
            continue
        tot += 1
        r = pose_for_sun(az, el, bearing, target)
        ok = r is not None and tilt_of(r[0], r[1]) <= LIM
        inr += ok
        rows.append((h, az, el, r, ok))
    ok_h = [r[0] for r in rows if r[4]]
    print(f"{day:02d}/{month:02d}, lat {lat}, lon {lon}, wall faces {bearing:.0f} deg, target {tuple(round(c, 2) for c in unit(target))}")
    print(f"  daylight {tot/6:.1f} h (UTC); mirror within {LIM:.0f} deg of straight out for {inr/6:.1f} h"
          + (f", {min(ok_h):.1f} to {max(ok_h):.1f} UTC" if ok_h else ""))
    for h, az, el, r, ok in rows[::6]:
        pr = f"pitch {r[0]:+5.1f} yaw {r[1]:+5.1f}" if r else "Sun behind the wall"
        print(f"    {h:4.1f}h  az {az:5.1f} el {el:5.1f}  {pr}  {'ok' if ok else 'out of range'}")


# ------------------------------------------------------------------ rendering (VTK, offscreen)
def render(parts, path, view, focal=(0, -2, 42), size=(1500, 1100), hide=(), cut_x=None, cut_all=False, rays=None):
    """view = (azimuth deg around Y from +Z towards +X, elevation deg, distance mm)."""
    import vtk

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.96)
    ren.SetBackground2(0.86, 0.87, 0.89)
    ren.GradientBackgroundOn()
    for nm, s, col in parts:
        if any(h in nm for h in hide):
            continue
        if cut_x is not None and (cut_all or nm in ("housing_walls", "bezel", "back_plate", "motor_deck")):
            s = s.cut(shp(box(cut_x, 200, -200, 200, -10, 200)))
        v, t = s.tessellate(0.15, 0.25)
        if not t:
            continue
        pts, cells = vtk.vtkPoints(), vtk.vtkCellArray()
        for p in v:
            pts.InsertNextPoint(p.x, p.y, p.z)
        for a, b, c in t:
            cells.InsertNextCell(3)
            for k in (a, b, c):
                cells.InsertCellPoint(k)
        pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
        nrm = vtk.vtkPolyDataNormals(); nrm.SetInputData(pd); nrm.SetFeatureAngle(35); nrm.SplittingOn(); nrm.Update()
        mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(nrm.GetOutputPort())
        ac = vtk.vtkActor(); ac.SetMapper(mp)
        h = col.lstrip("#")
        ac.GetProperty().SetColor(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
        glass = nm == "mirror_glass"
        ac.GetProperty().SetSpecular(0.9 if glass else 0.25)
        ac.GetProperty().SetSpecularPower(80 if glass else 20)
        ac.GetProperty().SetDiffuse(0.85)
        ac.GetProperty().SetAmbient(0.18)
        ren.AddActor(ac)
    for (a, b, col, r) in (rays or []):
        ln = vtk.vtkLineSource(); ln.SetPoint1(*a); ln.SetPoint2(*b); ln.SetResolution(1)
        tb = vtk.vtkTubeFilter(); tb.SetInputConnection(ln.GetOutputPort()); tb.SetRadius(r); tb.SetNumberOfSides(16)
        mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(tb.GetOutputPort())
        ac = vtk.vtkActor(); ac.SetMapper(mp); ac.GetProperty().SetColor(*col); ac.GetProperty().SetAmbient(1.0)
        ren.AddActor(ac)
    cm = ren.GetActiveCamera()
    az, el, dist = (math.radians(view[0]), math.radians(view[1]), view[2])
    pos = (focal[0] + dist * math.cos(el) * math.sin(az), focal[1] + dist * math.sin(el), focal[2] + dist * math.cos(el) * math.cos(az))
    cm.SetFocalPoint(*focal); cm.SetPosition(*pos); cm.SetViewUp(0, 1, 0); cm.SetViewAngle(28)
    ren.ResetCameraClippingRange()
    for pos in ((250, 300, 400), (-300, 150, 250), (0, -250, 200)):
        L = vtk.vtkLight(); L.SetPosition(*pos); L.SetFocalPoint(*focal); L.SetIntensity(0.6 if pos[0] > 0 else 0.35)
        L.SetLightTypeToSceneLight(); ren.AddLight(L)
    ren.LightFollowCameraOff()
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(*size); win.SetMultiSamples(8)
    win.AddRenderer(ren); win.Render()
    f = vtk.vtkWindowToImageFilter(); f.SetInput(win); f.ReadFrontBufferOff(); f.Update()
    w = vtk.vtkPNGWriter(); w.SetFileName(str(path)); w.SetInputConnection(f.GetOutputPort()); w.Write()
    print("Wrote", path)


def ray_lines(sun_wall, target_wall, pitch, yaw, L=130.0):
    c = (0.0, 0.0, PIV_Z + CARR_T + GLASS_T)
    n = normal_of(pitch, yaw)
    c = (n[0] * (CARR_T + GLASS_T), n[1] * (CARR_T + GLASS_T), PIV_Z + n[2] * (CARR_T + GLASS_T))
    s = unit(sun_wall); t = unit(target_wall)
    return [((c[0] + s[0] * L, c[1] + s[1] * L, c[2] + s[2] * L), c, (1.0, 0.72, 0.15), 0.9),
            (c, (c[0] + t[0] * L, c[1] + t[1] * L, c[2] + t[2] * L), (1.0, 0.72, 0.15), 0.9)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pitch", type=float); ap.add_argument("--yaw", type=float)
    ap.add_argument("--sun", type=float, nargs=2, metavar=("AZ", "EL"), default=[200.0, 40.0])
    ap.add_argument("--wall-bearing", type=float, default=180.0, help="compass bearing the wall faces (180 = south)")
    ap.add_argument("--target", type=float, nargs=3, default=[0.0, 0.0, 1.0], help="target direction in wall frame (x right, y up, z out)")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--day", help="MM-DD: print when the mirror is within its range")
    ap.add_argument("--lat", type=float, default=51.5); ap.add_argument("--lon", type=float, default=0.0)
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()

    if a.day:
        mo, dy = (int(x) for x in a.day.split("-"))
        day_summary(mo, dy, a.lat, a.lon, a.wall_bearing, a.target)
        return
    if a.check:
        run_checks()
        return

    sun_w = tgt_w = None
    if a.pitch is not None or a.yaw is not None:
        pitch, yaw = a.pitch or 0.0, a.yaw or 0.0
    else:
        r = pose_for_sun(a.sun[0], a.sun[1], a.wall_bearing, a.target)
        if r is None:
            print("Sun is behind the wall: parked upright"); pitch = yaw = 0.0
        else:
            pitch, yaw, sun_w, tgt_w = r
            print(f"Sun az {a.sun[0]:.0f} el {a.sun[1]:.0f}, wall faces {a.wall_bearing:.0f}: pitch {pitch:+.1f}, yaw {yaw:+.1f} deg")
    parts, info = pose(pitch, yaw)
    for k in 'LR':
        print(f"  screw {k}: {info[k]['ext']:+.1f} mm from neutral, pad slip {info[k]['slip']:.1f} mm")
    OUT.mkdir(parents=True, exist_ok=True)
    assemble(parts).save(str(OUT / "wall-mirror-nema11.step"))
    print("Wrote", OUT / "wall-mirror-nema11.step")
    if a.no_render:
        return
    IMG.mkdir(parents=True, exist_ok=True)
    neutral, _ = pose(0, 0)
    rays = ray_lines(sun_w, tgt_w, pitch, yaw) if sun_w else None
    render(neutral, IMG / "wall-mirror-front.png", view=(32, 16, 330), focal=(0, 0, 38), size=(1300, 1100))
    render(parts, IMG / "wall-mirror-posed-front.png", view=(28, 14, 430), focal=(0, 0, 45), size=(1300, 1100), rays=rays)
    render(parts, IMG / "wall-mirror-posed-section.png", view=(90, 8, 235), focal=(0, -2, 42), size=(1500, 1000), cut_x=0.0, cut_all=True)
    render(neutral, IMG / "wall-mirror-neutral-section.png", view=(90, 8, 235), focal=(0, -2, 42), size=(1500, 1000), cut_x=0.0, cut_all=True)
    render(parts, IMG / "wall-mirror-mechanism.png", view=(24, 38, 250), focal=(0, -4, 44), size=(1500, 1000),
           hide=("housing_walls", "bezel", "controller_stack", "carrier", "mirror_glass", "magnet"))


if __name__ == "__main__":
    main()
