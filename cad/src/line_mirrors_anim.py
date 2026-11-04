#!/usr/bin/env python3
"""MP4 animation of the wave version (line of 7 mirrors, camshaft travelling wave) as a viewer sees it.

Left: the strip on a wall, seen from the front, 1.5 m away. The Sun crosses the sky in front of the wall (a compressed day), the common
pan/tilt keeps the reflected beams on a fixed target, and the camshaft turns so a wave runs along the row. The glass is shaded by the
real mirror normals (no reflection of the room is rendered).
Right: where the seven reflected beams land on a wall 3 m in front, with fading trails, so the sine wave is visible.

Usage (repo root): python3 cad/src/line_mirrors_anim.py [--seconds 16] [--fps 30] [--out path.mp4] [--frames-only N]
"""
import argparse
import math
import subprocess
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import line_mirrors as lm  # noqa: E402

lm.configure("wave")
W, H = 1920, 1080
LW = 1300                                    # width of the 3D panel
TARGET_Z = 3000.0
FONT = "/System/Library/Fonts/Helvetica.ttc"


def polydata(shape):
    v, t = lm.shp(shape).tessellate(0.15, 0.3)
    pts, cells = vtk.vtkPoints(), vtk.vtkCellArray()
    for p in v:
        pts.InsertNextPoint(p.x, p.y, p.z)
    for a, b, c in t:
        cells.InsertNextCell(3)
        for k in (a, b, c):
            cells.InsertCellPoint(k)
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
    nm = vtk.vtkPolyDataNormals(); nm.SetInputData(pd); nm.SetFeatureAngle(35); nm.SplittingOn(); nm.Update()
    return nm.GetOutput()


def actor(pd, col, spec=0.25, power=20, tf=None):
    mp = vtk.vtkPolyDataMapper(); mp.SetInputData(pd)
    ac = vtk.vtkActor(); ac.SetMapper(mp)
    h = col.lstrip("#")
    p = ac.GetProperty()
    p.SetColor(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    p.SetSpecular(spec); p.SetSpecularPower(power); p.SetDiffuse(0.85); p.SetAmbient(0.22)
    if tf is not None:
        ac.SetUserTransform(tf)
    return ac


def build_scene():
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.80, 0.79, 0.77)
    # plaster wall behind the strip
    wall = vtk.vtkPlaneSource(); wall.SetOrigin(-1500, -900, -0.5); wall.SetPoint1(1500, -900, -0.5); wall.SetPoint2(-1500, 900, -0.5)
    wm = vtk.vtkPolyDataMapper(); wm.SetInputConnection(wall.GetOutputPort())
    wa = vtk.vtkActor(); wa.SetMapper(wm); wa.GetProperty().SetColor(0.90, 0.88, 0.84); wa.GetProperty().SetAmbient(0.3); wa.GetProperty().SetDiffuse(0.7)
    ren.AddActor(wa)
    # static visible parts: housing shell and front plate
    parts, _ = lm.pose_wave((0, 0, 1), 0.0)
    for nm, s, col in parts:
        if nm in ("housing", "front_plate"):
            ren.AddActor(actor(polydata(s), "#4a4d52" if nm == "housing" else "#2b2d31", 0.35, 30))
    # one local mirror group (pivot at the origin, normal +Z), moved per frame by a transform
    tfs, glass_actors = [], []
    carrier = polydata(lm.cylz(lm.CARR_R, lm.B_OFF, lm.B_OFF + lm.CARR_T))
    glass = polydata(lm.cylz(lm.MIR_R, lm.B_OFF + lm.CARR_T, lm.B_OFF + lm.CARR_T + lm.GLASS_T))
    stem = polydata(lm.between((0, 0, -lm.L), (0, 0, lm.B_OFF + 0.1), lm.STEM_R).union(lm.sph(lm.PIV_R, 0, 0, 0)).union(lm.sph(lm.TIP_R, 0, 0, -lm.L)))
    for _ in range(lm.N):
        tf = vtk.vtkTransform(); tfs.append(tf)
        ren.AddActor(actor(carrier, lm.CARR, 0.2, 20, tf))
        ren.AddActor(actor(stem, lm.STEM, 0.5, 40, tf))
        g = actor(glass, "#cfe3f1", 1.0, 120, tf)
        g.GetProperty().SetDiffuse(0.55)
        glass_actors.append(g)
        ren.AddActor(g)
    for pos, inten in (((500, 700, 900), 0.8), ((-600, 300, 500), 0.4), ((0, -400, 600), 0.25)):
        lt = vtk.vtkLight(); lt.SetPosition(*pos); lt.SetFocalPoint(0, 0, 0); lt.SetIntensity(inten); lt.SetLightTypeToSceneLight(); ren.AddLight(lt)
    ren.LightFollowCameraOff()
    cm = ren.GetActiveCamera()
    cm.SetFocalPoint(0, 0, 45); cm.SetPosition(0, 0, TARGET_Z)
    cm.SetViewUp(0, 1, 0); cm.SetViewAngle(15)
    ren.ResetCameraClippingRange()
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(LW, H); win.SetMultiSamples(8); win.AddRenderer(ren)
    f = vtk.vtkWindowToImageFilter(); f.SetInput(win); f.ReadFrontBufferOff()
    return win, f, tfs, glass_actors, cm


def scene_state(t):
    """t in 0..1: the Sun's position, the cam angle. Returns Sun vector, common normal, cam angle in degrees."""
    ax = 38.0 * math.cos(math.pi * t)                       # sweeps from 38 deg on one side to 38 on the other (a day, compressed)
    ey = 14.0 + 10.0 * math.sin(math.pi * t)                 # climbs and falls
    a, e = math.radians(ax), math.radians(ey)
    sun = (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))
    n_c = lm.unit(tuple(sun[k] + (0, 0, 1)[k] for k in range(3)))
    return sun, n_c, 360.0 * 2.5 * t, ax, ey


def mirror_state(n_c, theta):
    X, Y = -lm.L * n_c[0], -lm.L * n_c[1]
    out = []
    for i, x in enumerate(lm.XS):
        ph = math.radians(theta) + i * lm.D_PHASE
        tp = (x + X, Y + lm.E_AMP * math.sin(ph))
        nx, ny = (x - tp[0]) / lm.L, -tp[1] / lm.L
        n = (nx, ny, math.sqrt(1 - nx * nx - ny * ny))
        out.append((n, (x, 0.0, lm.Z_T + lm.L * n[2])))
    return out


def spot(n, piv, sun):
    d = tuple(2 * sum(n[k] * sun[k] for k in range(3)) * n[j] - sun[j] for j in range(3))
    o = tuple(piv[k] + n[k] * (lm.B_OFF + lm.CARR_T + lm.GLASS_T) for k in range(3))
    s = (TARGET_Z - o[2]) / d[2]
    return o[0] + d[0] * s, o[1] + d[1] * s


def panel(trail, spots, sun_ax, sun_ey, theta, xe, big, small):
    """Right panel: the target wall with beams and trails, plus a sun gauge."""
    pw = W - LW
    img = Image.new("RGB", (pw, H), (24, 25, 29))
    d = ImageDraw.Draw(img)
    d.text((24, 20), "Reflected beams on a wall 3 m in front", font=big, fill=(235, 235, 232))
    d.text((24, 52), "each dot = one mirror's spot of sunlight; ring = the viewer's eye", font=small, fill=(150, 152, 158))
    sc = 0.46                                                # px per mm
    cx, cy = pw / 2, 330
    d.rectangle((cx - 640 * sc, cy - 330 * sc * 1.0, cx + 640 * sc, cy + 330 * sc * 1.0), fill=(47, 48, 53), outline=(70, 72, 78))
    d.line((cx - 640 * sc, cy, cx + 640 * sc, cy), fill=(64, 66, 72))
    glow = Image.new("RGB", (pw, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    # trails: fading, each mirror its own colour step so the wave reads
    for age, frame in enumerate(reversed(trail)):
        a = max(0.0, 1.0 - age / len(trail))
        for i, (sx, sy) in enumerate(frame):
            r = 3 + 6 * a
            px, py = cx + sx * sc, cy - sy * sc
            g.ellipse((px - r, py - r, px + r, py + r), fill=(int(150 * a * a), int(105 * a * a), int(25 * a * a)))
    for (sx, sy) in spots:
        px, py = cx + sx * sc, cy - sy * sc
        g.ellipse((px - 20, py - 20, px + 20, py + 20), fill=(255, 205, 90))
    soft = glow.filter(ImageFilter.GaussianBlur(7))
    arr = np.clip(np.asarray(img, dtype=np.int16) + np.asarray(soft, dtype=np.int16) + np.asarray(glow, dtype=np.int16) // 3, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)
    pts = [(cx + sx * sc, cy - sy * sc) for sx, sy in spots]
    d.line(pts, fill=(255, 235, 170), width=2)
    for p in pts:
        d.ellipse((p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), fill=(255, 250, 225))
    ex = cx + xe * sc
    d.ellipse((ex - 9, cy - 9, ex + 9, cy + 9), outline=(120, 200, 255), width=3)
    d.text((ex - 22, cy - 34), "viewer", font=small, fill=(120, 200, 255))
    d.text((24, 520), "Camshaft angle", font=small, fill=(150, 152, 158))
    d.text((24, 545), f"{theta % 360:5.0f} deg   ({theta / 360:.1f} turns)", font=big, fill=(235, 235, 232))
    # sun gauge: top-down azimuth bar and elevation
    d.text((24, 620), "Sun (compressed day)", font=small, fill=(150, 152, 158))
    gx0, gx1, gy = 24, pw - 24, 690
    d.line((gx0, gy, gx1, gy), fill=(90, 92, 98), width=2)
    sx = (gx0 + gx1) / 2 + (gx1 - gx0) / 2 * (sun_ax / 50.0)
    d.ellipse((sx - 12, gy - 12, sx + 12, gy + 12), fill=(255, 205, 70))
    d.text((gx0, gy + 20), "left of wall axis", font=small, fill=(110, 112, 118))
    d.text((gx1 - 120, gy + 20), "right", font=small, fill=(110, 112, 118))
    d.text((24, 750), f"Sun {sun_ax:+.0f} deg sideways, {sun_ey:.0f} deg up", font=small, fill=(200, 200, 196))
    d.text((24, 790), "Mirrors share one tilt that follows the Sun,", font=small, fill=(150, 152, 158))
    d.text((24, 812), "so the whole line stays on this wall.", font=small, fill=(150, 152, 158))
    d.text((24, 840), "The camshaft adds a slow sine on top:", font=small, fill=(150, 152, 158))
    d.text((24, 862), "the wave runs along the row and back.", font=small, fill=(150, 152, 158))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=16.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "media" / "animations" / "line-wave-viewer.mp4"))
    ap.add_argument("--frames-only", type=int, default=0, help="write this many PNG test frames instead of the mp4")
    a = ap.parse_args()
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    win, filt, tfs, glass_actors, cm = build_scene()
    big, small = ImageFont.truetype(FONT, 28), ImageFont.truetype(FONT, 20)
    total = int(a.seconds * a.fps)
    ff = None
    if not a.frames_only:
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(a.fps), "-i", "-",
                               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    trail = []
    marks = [int(total * k / max(1, a.frames_only)) for k in range(a.frames_only)] if a.frames_only else None
    for f in range(total):
        t = f / (total - 1)
        sun, n_c, theta, ax, ey = scene_state(t)
        ms = mirror_state(n_c, theta)
        for tf, (n, piv) in zip(tfs, ms):
            p, y = lm.pitch_yaw(n)
            tf.Identity(); tf.Translate(*piv); tf.RotateY(y); tf.RotateX(p)
        xe = -280.0 + 560.0 * t                              # the viewer walks slowly along the wall, eye on the row's height
        cm.SetPosition(xe, 0, TARGET_Z); cm.SetFocalPoint(0, 0, 45); cm.SetClippingRange(1000, 5000)
        spots = [spot(n, piv, sun) for n, piv in ms]
        for g, (sx, sy) in zip(glass_actors, spots):
            fl = math.exp(-(((sx - xe) ** 2 + sy ** 2) / 38.0 ** 2))
            pr = g.GetProperty()
            pr.SetColor(0.55 + 0.45 * fl, 0.66 + 0.34 * fl, 0.75 + 0.18 * fl)
            pr.SetAmbient(0.25 + 0.75 * fl); pr.SetDiffuse(0.55 + 0.1 * fl)
        win.Render(); filt.Modified(); filt.Update()
        vimg = filt.GetOutput()
        arr = np.flip(np.frombuffer(bytes(vtk.util.numpy_support.vtk_to_numpy(vimg.GetPointData().GetScalars())), dtype=np.uint8).reshape(H, LW, -1)[:, :, :3], axis=0)
        trail.append(spots)
        trail = trail[-22:]
        right = panel(trail, spots, ax, ey, theta, xe, big, small)
        frame = np.concatenate([arr, np.asarray(right)], axis=1)
        im = Image.fromarray(frame)
        ImageDraw.Draw(im).text((24, 20), "Line of 7 mirrors, wave version: what a viewer sees", font=big, fill=(30, 30, 32))
        ImageDraw.Draw(im).text((24, 54), "The viewer stands 3 m out and walks along the wall. A mirror flashes when its beam sweeps over the eye.", font=small, fill=(70, 70, 74))
        if ff:
            ff.stdin.write(im.tobytes())
        elif f in marks:
            p = out.parent / f"test-frame-{f:04d}.png"; im.save(p); print("Wrote", p)
        if f % 60 == 0:
            print(f"frame {f}/{total}", flush=True)
    if ff:
        ff.stdin.close(); ff.wait(); print("Wrote", out)


if __name__ == "__main__":
    import vtk.util.numpy_support  # noqa: F401
    main()
