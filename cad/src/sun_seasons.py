#!/usr/bin/env python3
"""One portrait video (1080 x 1920) with three stacked panels: the mirror tracking the Sun in London over 24 hours at the
summer solstice, equinox and winter solstice. Base and mirror only: no text, no Sun marker.

Rendered with VTK (real depth buffer, smooth shading, 8x multisampling), then encoded with ffmpeg as H.264, so it is much
cleaner than the matplotlib GIFs. Same Sun maths as sun_day.py (NOAA low-precision formulas, London, UK clock time).

Usage (from the repo root): python3 cad/src/sun_seasons.py [--which all|summer-solstice|equinox|winter-solstice] [--days 4] [--frames-per-day 288] [--fps 30]
Writes cad/media/animations/<square-mirror|round-mirror|hole-mirror>/hinge-mirror-<seasons or day name>[-round|-hole]-<days>days-1080x1920.mp4 (--png-frame N also writes that frame as a PNG, no video).
"""
import argparse
import math
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "sun-path" / "scripts"))
import hinge_mirror as m  # noqa: E402
import sun_path  # noqa: E402

W, H_PX = 1080, 1920
DATES = {"summer-solstice": "2026-06-21", "equinox": "2026-03-20", "winter-solstice": "2026-12-21"}   # top to bottom in the stacked version
DAY, TWILIGHT, NIGHT = np.array([0.86, 0.92, 0.96]), np.array([0.93, 0.62, 0.45]), np.array([0.07, 0.09, 0.19])
GLASS_HEX = "#a9bcc8"


def sky(el):
    """Background from the Sun's elevation: day above 6 deg, orange twilight, night below -12 deg."""
    if el >= 6:
        return DAY
    if el >= 0:
        return TWILIGHT + (DAY - TWILIGHT) * el / 6
    if el >= -12:
        return NIGHT + (TWILIGHT - NIGHT) * (el + 12) / 12
    return NIGHT


def track(date, n, days=1):
    """(drum azimuth, tilt, Sun elevation) for n frames per day over `days` consecutive local days."""
    y, mo, d = (int(v) for v in date.split("-"))
    off = 1 if 3 < mo < 10 else 0                                   # BST in summer
    out = []
    for i in range(n * days):
        minutes = 24 * 60 * i / n
        utc = datetime(y, mo, d, tzinfo=timezone.utc) + timedelta(minutes=minutes - 60 * off)
        bearing, el = sun_path.sun_position(utc)
        out.append(((-float(bearing)) % 360.0, max(-m.T_MAX, min(m.T_MAX, float(el))), float(el)))
    return out


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def polydata(shape):
    v, t = shape.tessellate(0.25, 0.12)
    pts = vtk.vtkPoints()
    for p in v:
        pts.InsertNextPoint(p.x, p.y, p.z)
    cells = vtk.vtkCellArray()
    for a, b, c in t:
        cells.InsertNextCell(3, (a, b, c))
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(cells)
    nrm = vtk.vtkPolyDataNormals()
    nrm.SetInputData(pd)
    nrm.SetFeatureAngle(35.0)                                        # smooth curved faces, keep sharp edges
    nrm.SplittingOn()
    nrm.ConsistencyOn()
    nrm.Update()
    return nrm.GetOutput()


CFG = {"elev": 17.0, "scale": None, "focus_z": 170.0, "beam": False}
HOLE_R = 10.0                                                       # 20 mm hole through the middle of the mirror
BASE_LO, BASE_HI = np.array([-150.0, -150.0, 0.0]), np.array([150.0, 150.0, m.PLATE_TOP])
TABLE_HALF = 450.0                                                  # table slab drawn 900 x 900 mm


def mirror_centre(az, tilt):
    """Centre of the mirror and its unit normal (towards the Sun) in world coordinates."""
    zc = (m.GLASS_Z0 + m.GLASS_TOP) / 2
    t, a = math.radians(tilt), math.radians(az)
    c, n = np.array([0.0, -zc * math.sin(t), zc * math.cos(t) + m.H]), np.array([0.0, math.cos(t), math.sin(t)])
    rz = lambda v: np.array([v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a), v[2]])
    return rz(c), rz(n)


def beam_hit(origin, u):
    """First surface the beam meets going from origin along u: the base (a box) or the table (z = 0). Returns (t, face normal)."""
    tmin, tmax, face = -1e9, 1e9, None
    for k in range(3):
        if abs(u[k]) < 1e-9:
            if origin[k] < BASE_LO[k] or origin[k] > BASE_HI[k]:
                tmax = -1
            continue
        t1, t2 = (BASE_LO[k] - origin[k]) / u[k], (BASE_HI[k] - origin[k]) / u[k]
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 > tmin:
            tmin, face = t1, k
        tmax = min(tmax, t2)
    if face is not None and 0 < tmin <= tmax:
        nrm = np.zeros(3); nrm[face] = -np.sign(u[face])
        return tmin, nrm
    return -origin[2] / u[2], np.array([0.0, 0.0, 1.0])          # table plane


def hull_xy(pts):
    """Convex hull (x, y) of 3D points, in order, as a list of points."""
    P = sorted({(round(float(p[0]), 6), round(float(p[1]), 6)) for p in pts})
    def half(seq):
        h = []
        for q in seq:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (q[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (q[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(q)
        return h
    lo, up = half(P), half(P[::-1])
    return [np.array([x, y, 0.0]) for x, y in lo[:-1] + up[:-1]]


def clip_square(poly, half):
    """Sutherland-Hodgman clip of a polygon (list of 3D points) to the table square."""
    out = list(poly)
    for axis in (0, 1):
        for sign in (1.0, -1.0):
            inp, out = out, []
            if not inp:
                break
            prev = inp[-1]
            for cur in inp:
                ic, ip = sign * cur[axis] <= half, sign * prev[axis] <= half
                if ic != ip:
                    out.append(prev + ((sign * half - prev[axis]) / (cur[axis] - prev[axis])) * (cur - prev))
                if ic:
                    out.append(cur)
                prev = cur
    return out


def set_poly(pd, pts):
    v = vtk.vtkPoints()
    for q in pts:
        v.InsertNextPoint(*q)
    cells = vtk.vtkCellArray()
    if len(pts) >= 3:
        cells.InsertNextCell(len(pts), list(range(len(pts))))
    pd.SetPoints(v); pd.SetPolys(cells); pd.Modified()


def local_to_world(p, az, tilt):
    t, a = math.radians(tilt), math.radians(az)
    q = np.array([p[0], p[1] * math.cos(t) - p[2] * math.sin(t), p[1] * math.sin(t) + p[2] * math.cos(t) + m.H])
    return np.array([q[0] * math.cos(a) - q[1] * math.sin(a), q[0] * math.sin(a) + q[1] * math.cos(a), q[2]])


def make_beam(ren):
    """Translucent shaft of sunlight plus a bright spot (and glow) where it lands. Returns the objects update_beam moves."""
    line = vtk.vtkLineSource()
    tube = vtk.vtkTubeFilter()
    tube.SetInputConnection(line.GetOutputPort()); tube.SetRadius(HOLE_R); tube.SetNumberOfSides(48); tube.CappingOff()
    sm = vtk.vtkPolyDataMapper(); sm.SetInputConnection(tube.GetOutputPort())
    shaft = vtk.vtkActor(); shaft.SetMapper(sm)
    shaft.GetProperty().SetColor(1.0, 0.92, 0.55); shaft.GetProperty().SetOpacity(0.32); shaft.GetProperty().LightingOff()
    n = 72
    spots = []
    for colour, opacity in (((1.0, 1.0, 1.0), 1.0),):                                  # the lit patch the hole lets through
        pts = vtk.vtkPoints(); pts.SetNumberOfPoints(n)
        cells = vtk.vtkCellArray(); cells.InsertNextCell(n, list(range(n)))
        pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
        mp = vtk.vtkPolyDataMapper(); mp.SetInputData(pd)
        ac = vtk.vtkActor(); ac.SetMapper(mp)
        ac.GetProperty().SetColor(*colour); ac.GetProperty().SetOpacity(opacity); ac.GetProperty().LightingOff()
        ren.AddActor(ac)
        spots.append((pd, ac))
    shadows = []
    for _ in range(2):                                               # base shadow, then mirror shadow on top of it
        pd = vtk.vtkPolyData()
        mp = vtk.vtkPolyDataMapper(); mp.SetInputData(pd)
        ac = vtk.vtkActor(); ac.SetMapper(mp); ac.GetProperty().LightingOff()
        ren.AddActor(ac)
        shadows.append((pd, ac))
    return line, shaft, spots, n, shadows


def update_beam(beam, table, az, tilt, el):
    line, shaft, spots, n, shadows = beam
    f = float(np.clip((el + 12.0) / 18.0, 0.18, 1.0))               # the table follows the daylight
    table.GetProperty().SetColor(0.97 * f, 0.97 * f, 0.97 * f)
    c, nrm = mirror_centre(az, tilt)
    if el <= 0.5:                                                    # Sun below the horizon: no light through the hole
        shaft.SetVisibility(0)
        for _, ac in spots:
            ac.SetVisibility(0)
        for _, ac in shadows:
            ac.SetVisibility(0)
        return
    u = -nrm                                                         # the light travels away from the Sun
    origin = c + 3.0 * u                                             # back face of the 6 mm mirror
    t, fn = beam_hit(origin, u)
    centre = origin + t * u
    cut = t                                                          # the shaft stops where it leaves the table, as it would run on past it
    for k in (0, 1):
        if abs(u[k]) > 1e-9:
            cut = min(cut, (math.copysign(TABLE_HALF, u[k]) - origin[k]) / u[k])
    shaft_end = origin + max(cut, 0.0) * u
    line.SetPoint1(*origin); line.SetPoint2(*shaft_end)
    shaft.SetVisibility(1)
    on_table = fn[2] == 1.0 and centre[2] < 1.0
    show = not (on_table and (abs(centre[0]) > TABLE_HALF or abs(centre[1]) > TABLE_HALF))
    v1 = np.cross(u, [0.0, 0.0, 1.0])
    v1 = v1 / np.linalg.norm(v1) if np.linalg.norm(v1) > 1e-6 else np.array([1.0, 0.0, 0.0])
    v2 = np.cross(u, v1)
    plane_c = fn @ centre
    shade = (0.62 * f, 0.62 * f, 0.64 * f)
    # shadows on the table: the base (hull of its corners slid along the light to z = 0) and the mirror plate
    def slide(p):
        return p + (-p[2] / u[2]) * u
    corners = [np.array([x, y, z]) for x in (-150.0, 150.0) for y in (-150.0, 150.0) for z in (0.0, m.PLATE_TOP)]
    base_poly = clip_square(hull_xy([slide(c_) for c_ in corners]), TABLE_HALF)
    plate = [slide(local_to_world((x, 0.0, z), az, tilt)) for x, z in ((-m.MIR_W / 2, m.GLASS_Z0), (m.MIR_W / 2, m.GLASS_Z0),
                                                                          (m.MIR_W / 2, m.GLASS_TOP), (-m.MIR_W / 2, m.GLASS_TOP))]
    plate_poly = clip_square(plate, TABLE_HALF)
    for (pd, ac), poly, z in zip(shadows, (base_poly, plate_poly), (0.1, 0.2)):
        set_poly(pd, [np.array([q[0], q[1], z]) for q in poly])
        ac.GetProperty().SetColor(*shade)
        ac.SetVisibility(1 if len(poly) >= 3 else 0)
    for (pd, ac), scale in zip(spots, (1.0,)):
        for k in range(n):
            th = 2 * math.pi * k / n
            q = origin + scale * HOLE_R * (math.cos(th) * v1 + math.sin(th) * v2)
            hit = q + ((plane_c - fn @ q) / (fn @ u)) * u + 0.4 * fn
            pd.GetPoints().SetPoint(k, *hit)
        pd.GetPoints().Modified(); pd.Modified()
        lit = 0.97 * f if fn[2] == 1.0 and centre[2] < 1.0 else 0.5 * f        # white table, or a lighter patch on the black base
        ac.GetProperty().SetColor(lit, lit, lit)
        ac.SetVisibility(1 if show else 0)


def build_panel(index, parts, count=3):
    """A renderer in the panel's viewport, actors grouped by how they move."""
    ren = vtk.vtkRenderer()
    ren.SetViewport(0, 1 - (index + 1) / count, 1, 1 - index / count)
    groups = {"base": [], "drum": [], "slider": [], "mirror": []}
    for group, nm, pd, col in parts:
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(pd)
        act = vtk.vtkActor()
        act.SetMapper(mapper)
        p = act.GetProperty()
        p.SetInterpolationToPhong()
        p.SetColor(*hex_rgb(col))
        if nm in ("mirror_glass_6mm", "mirror_round_disc"):
            p.SetSpecular(1.0); p.SetSpecularPower(120); p.SetAmbient(0.25); p.SetDiffuse(0.75)
        elif nm == "mirror_clear_panel":                        # clear glass or acrylic carrier: faint tint, bright edges
            p.SetSpecular(1.0); p.SetSpecularPower(150); p.SetOpacity(0.2); p.SetAmbient(0.4)
            edges = vtk.vtkFeatureEdges()
            edges.SetInputData(pd); edges.BoundaryEdgesOn(); edges.FeatureEdgesOn(); edges.SetFeatureAngle(40); edges.Update()
            em = vtk.vtkPolyDataMapper(); em.SetInputConnection(edges.GetOutputPort()); em.ScalarVisibilityOff()
            ea = vtk.vtkActor(); ea.SetMapper(em)
            ea.GetProperty().SetColor(0.93, 0.98, 1.0); ea.GetProperty().SetLineWidth(2.5); ea.GetProperty().LightingOff()
            ren.AddActor(ea); groups[group].append(ea)
        else:
            p.SetSpecular(0.25); p.SetSpecularPower(30)
        ren.AddActor(act)
        groups[group].append(act)
        if nm == "table_slab":
            groups["table"] = act
    kit = vtk.vtkLightKit()
    kit.SetKeyLightIntensity(0.9)
    kit.AddLightsToRenderer(ren)
    cam = ren.GetActiveCamera()
    cam.ParallelProjectionOn()
    focus = np.array([0.0, 0.0, CFG["focus_z"]])
    e, a = math.radians(CFG["elev"]), math.radians(232)               # seen from the south-west, so the mirror faces the camera around noon
    cam.SetFocalPoint(*focus)
    cam.SetPosition(*(focus + 1500 * np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])))
    cam.SetViewUp(0, 0, 1)
    cam.SetClippingRange(800, 2400)
    cam.SetParallelScale(CFG["scale"] or (225 if count == 3 else 430))                                        # half the panel height in mm
    ren.SetUseFXAA(True)
    if CFG["beam"]:
        groups["beam"] = make_beam(ren)
    return ren, groups


def place(groups, az, tilt):
    for act in groups["drum"]:
        t = vtk.vtkTransform(); t.RotateZ(az); act.SetUserTransform(t)
    for act in groups["slider"]:
        t = vtk.vtkTransform(); t.PostMultiply(); t.Translate(0, m.slider_y(tilt), 0); t.RotateZ(az); act.SetUserTransform(t)
    for act in groups["mirror"]:
        t = vtk.vtkTransform(); t.PostMultiply(); t.RotateX(tilt); t.Translate(0, 0, m.H); t.RotateZ(az); act.SetUserTransform(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=("all",) + tuple(DATES), default="all", help="all three stacked, or one day full frame")
    ap.add_argument("--mirror", choices=("square", "round", "hole"), default="square", help="round = 150 mm round mirror on a clear panel; hole = solid mirror with a 20 mm hole, a table, and the sunbeam through it (visual tests)")
    ap.add_argument("--days", type=int, default=4, help="consecutive days to follow")
    ap.add_argument("--frames-per-day", type=int, default=288)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--png-frame", type=int, default=None, help="write this one frame as a PNG and stop")
    ap.add_argument("--png-frames", default=None, help="comma separated frame numbers: write each as a PNG and stop")
    a = ap.parse_args()

    m.build()
    parts = []
    mirror_parts = list(m.mirror_parts)
    if a.mirror == "round":
        # visual alternative: a 150 mm round mirror centred on a clear 200 x 267 x 6 panel (physics not checked)
        zc = (m.GLASS_Z0 + m.GLASS_TOP) / 2
        mirror_parts = [p for p in mirror_parts if p[0] not in ("mirror_glass_6mm", "mirror_back_black_paint")]
        mirror_parts += [("mirror_clear_panel", m.box(-m.MIR_W / 2, m.MIR_W / 2, -m.GLASS_T / 2, m.GLASS_T / 2, m.GLASS_Z0, m.GLASS_TOP), "#cfe8f2"),
                         ("mirror_round_back_black", m.cyly(75.0, m.GLASS_T / 2, m.GLASS_T / 2 + 0.4, 0.0, zc), m.BLACK),
                         ("mirror_round_disc", m.cyly(75.0, m.GLASS_T / 2 + 0.4, m.GLASS_T / 2 + 3.0, 0.0, zc), GLASS_HEX)]
    extra_base = []
    if a.mirror == "hole":
        zc = (m.GLASS_Z0 + m.GLASS_TOP) / 2
        cutter = m._shape(m.cyly(HOLE_R, -6.0, 6.0, 0.0, zc))
        mirror_parts = [(n, m.cq.Workplane(obj=m._shape(w).cut(cutter)) if n in ("mirror_glass_6mm", "mirror_back_black_paint") else w, c)
                        for n, w, c in mirror_parts]
        extra_base = [("table_slab", m.box(-TABLE_HALF, TABLE_HALF, -TABLE_HALF, TABLE_HALF, -20.0, 0.0), "#f4f4f4")]
        CFG.update(elev=38.0, scale=330.0, focus_z=60.0, beam=True)
    for group, lst in (("base", list(m.base_parts) + extra_base), ("drum", m.drum_parts), ("slider", m.slider_parts), ("mirror", mirror_parts)):
        for nm, wp, col in lst:
            parts.append((group, nm, polydata(m._shape(wp)), GLASS_HEX if nm == "mirror_glass_6mm" else col))
    names = list(DATES) if a.which == "all" else [a.which]
    tracks = [track(DATES[n], a.frames_per_day, a.days) for n in names]
    if a.mirror == "hole" and len(names) == 1:
        CFG["scale"] = 640.0                                         # a lone portrait panel is narrower, so zoom out to keep the table in view
    total = a.frames_per_day * a.days

    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(W, H_PX)
    win.SetMultiSamples(8)
    panels = []
    for i in range(len(names)):
        ren, groups = build_panel(i, parts, len(names))
        win.AddRenderer(ren)
        panels.append((ren, groups))

    def draw(f):
        for (ren, groups), tr in zip(panels, tracks):
            az, tilt, el = tr[f]
            place(groups, az, tilt)
            if "beam" in groups:
                update_beam(groups["beam"], groups["table"], az, tilt, el)
            ren.SetBackground(*sky(el))
        win.Render()
        grab = vtk.vtkWindowToImageFilter()
        grab.SetInput(win); grab.SetInputBufferTypeToRGB(); grab.ReadFrontBufferOff(); grab.Update()
        img = grab.GetOutput()
        w, h, _ = img.GetDimensions()
        return np.flipud(vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, 3))

    out_dir = m.MEDIA / "animations"
    suffix = {"square": "", "round": "-round", "hole": "-hole"}[a.mirror]
    out_dir = out_dir / {"square": "square-mirror", "round": "round-mirror", "hole": "hole-mirror"}[a.mirror]
    out_dir.mkdir(parents=True, exist_ok=True)
    still = [a.png_frame] if a.png_frame is not None else [int(v) for v in a.png_frames.split(",")] if a.png_frames else []
    if still:
        from PIL import Image
        for f in still:
            name = out_dir / f"hinge-mirror-seasons{suffix}-frame{'' if len(still) == 1 else f'-{f}'}.png"
            Image.fromarray(draw(f)).save(name)
            print("Wrote", name)
        return
    tag = "seasons" if a.which == "all" else a.which
    out = out_dir / f"hinge-mirror-{tag}{suffix}-{a.days}days-1080x1920.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H_PX}",
                           "-r", str(a.fps), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for f in range(total):
        ff.stdin.write(np.ascontiguousarray(draw(f)).tobytes())
        if f % 100 == 0:
            print("frame", f + 1, "of", total, flush=True)
    ff.stdin.close()
    ff.wait()
    print("Wrote", out, f"{out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
