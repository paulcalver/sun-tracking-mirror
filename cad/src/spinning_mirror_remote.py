#!/usr/bin/env python3
"""CAD: desk remote controller for the spinning mirrors (CadQuery). Draft, nothing printed or tested.

A sloped desk wedge, 120 x 76 mm in plan, 22 mm high at the front and 42 mm at the back, with a 15 degree control panel:
two 16 mm panel pots (SPEED and JITTER) with 36 mm knobs, a 12 mm STOP/GO push button between them and a 5 mm SEND LED above it.
Inside: a Seeed XIAO ESP32-S3 at the back with its USB-C port in the back wall (charging and programming), a 3.7 V LiPo
(503450 class, 50 x 34 x 5 mm) in a pocket under the left pot, and a slide switch in the back wall that breaks the battery lead.
Radio is ESP-NOW (firmware/remote_dial/remote_dial.ino); no cable to the sculpture.

Two printed parts, both supportless:
  print_remote_tray   open sloped top, vertical walls; print as modelled (floor on the bed). Four corner posts take M3 heat-set inserts.
  print_remote_panel  3.4 mm plate with the holes, engraved labels and a dot scale round each knob; print with the outer face on the bed
                      (the print_ready STEP is already turned over). Four M3 x 10 countersunk screws into the posts.

World frame (mm): origin at the centre of the tray floor, X across, Y front (-) to back (+), Z up. The user sits at -Y.

Usage (from the repo root):
  python3 cad/src/spinning_mirror_remote.py [--check]
Writes cad/out/spinning-mirror/spinning-mirror-remote/ (assembly STEP, parts/<print|print_ready|purchase>/) and previews in
cad/media/previews/spinning-mirror-remote/.
"""
import argparse
import math
import sys
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spinning_mirror as sm                       # noqa: E402  (helpers, preview renderer, clash test)

CAD = HERE.parent
TAG = "spinning-mirror-remote"
OUTD = CAD / "out" / "spinning-mirror" / TAG
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / TAG

box, cylz = sm.box, sm.cylz
PRINT_C, STEEL = sm.PRINT_C, sm.STEEL

# ------------------------------------------------------------------ parameters (mm)
W, D = 120.0, 76.0                       # outer size in plan
WALL, FLOOR = 2.4, 2.4
TILT = 15.0                              # panel slope, degrees
HF = 22.0                                # outer wall height at the front edge, up to the panel underside
PT = 3.4                                 # panel thickness
T = math.radians(TILT)
ZC = HF + (D / 2) * math.tan(T)          # panel underside height above the floor at y = 0 (32.2)
HB = HF + D * math.tan(T)                # at the back edge (42.4)

POST_IN = 5.6                            # post axis distance from the outer faces
POST_R, INS_D, INS_DEPTH = 3.75, 4.1, 6.0    # post radius, M3 heat-set insert hole (4.0 to 4.2), depth
SCREW_D, SCREW_HEAD = 3.4, 6.4           # M3 countersunk screw: clearance hole, head diameter

POT_X, POT_V = 30.0, 6.0                 # pot axes at x = +/-30, v along the panel from its centre
POT_HOLE = 7.4                           # 16 mm Alpha-type pot, M7 bushing, 6 mm shaft
KNOB_D, KNOB_H = 36.0, 17.0
BTN_V, BTN_D = -4.0, 12.2                # 12 mm panel push button
LED_V, LED_D = 17.0, 5.2                 # 5 mm LED pressed in
TICKS, TICK_R, TICK_D, TICK_DEPTH = 11, 21.5, 1.4, 0.5   # dot scale over 270 degrees round each knob
TEXT_DEPTH = 0.5

# inside the tray
USB_W, USB_H = 13.0, 7.2                 # back wall cutout for a USB-C plug with its overmould
XIAO_L, XIAO_W = 21.0, 17.8
RAIL_H = 3.0                             # board sits 3 mm above the floor so the BAT pads underneath have room
XIAO_Y1 = D / 2 - WALL - 0.3             # USB end of the board, just off the back wall
BAT_L, BAT_W, BAT_T = 50.0, 34.0, 5.0    # 503450 LiPo
BAT_X0, BAT_Y0 = -48.2, -33.0            # inner corner of the pocket (battery long side along Y), under the left pot
BAT_WALL, BAT_WH = 1.5, 4.5
SW_X, SW_Z, SW_W, SW_H = 40.0, 11.0, 9.2, 4.0     # slide switch cutout in the back wall
FOOT_D, FOOT_DEPTH = 10.4, 0.8           # recesses for stick-on rubber feet


# ------------------------------------------------------------------ helpers
def to_world(shape):
    """Panel-local (x across, v up the slope, w out of the panel; origin on the panel underside at y = 0) to world."""
    s = shape.val() if hasattr(shape, "val") else shape
    return s.rotate((0, 0, 0), (1, 0, 0), TILT).translate((0, 0, ZC))


def lbox(x0, x1, v0, v1, w0, w1):
    return box(x0, x1, v0, v1, w0, w1)


def lcyl(r, w0, w1, x, v):
    return cylz(r, w0, w1, x, v)


def prism_outer(z1=120.0):
    return box(-W / 2, W / 2, -D / 2, D / 2, 0, z1)


POSTS = [(sx * (W / 2 - POST_IN), sy * (D / 2 - POST_IN) / math.cos(T)) for sx in (-1, 1) for sy in (-1, 1)]    # (x, v)


# ------------------------------------------------------------------ parts
def build_tray():
    prof = [(-D / 2, 0), (D / 2, 0), (D / 2, HB), (-D / 2, HF)]
    body = cq.Workplane("YZ").polyline(prof).close().extrude(W / 2, both=True)
    body = body.cut(box(-W / 2 + WALL, W / 2 - WALL, -D / 2 + WALL, D / 2 - WALL, FLOOR, 120))
    # corner posts along the panel normal, from the panel plane down to the floor
    posts = None
    for x, v in POSTS:
        c = to_world(lcyl(POST_R, -50, 0, x, v))
        posts = cq.Workplane(obj=c) if posts is None else posts.union(cq.Workplane(obj=c))
    body = body.union(posts).intersect(prism_outer())
    for x, v in POSTS:
        body = body.cut(cq.Workplane(obj=to_world(lcyl(INS_D / 2, -INS_DEPTH, 0.5, x, v))))
    # battery pocket (four low walls round the cell, open at the top)
    bx0, bx1 = BAT_X0, BAT_X0 + BAT_W + 2.5
    by0, by1 = BAT_Y0, BAT_Y0 + BAT_L + 1.5
    ring = box(bx0 - BAT_WALL, bx1 + BAT_WALL, by0 - BAT_WALL, by1 + BAT_WALL, FLOOR - 0.1, FLOOR + BAT_WH).cut(box(bx0, bx1, by0, by1, FLOOR - 0.2, FLOOR + BAT_WH + 1))
    body = body.union(ring)
    # XIAO ESP32-S3: two edge rails under the board, a stop at the front end; the USB-C shell points at the back wall
    y0 = XIAO_Y1 - XIAO_L
    for sx in (-1, 1):
        lo, hi = sorted((sx * (XIAO_W / 2 - 1.5), sx * (XIAO_W / 2 + 2.4)))
        body = body.union(box(lo, hi, y0 + 7.0, XIAO_Y1 - 1.0, FLOOR - 0.1, FLOOR + RAIL_H))
        lo2, hi2 = sorted((sx * (XIAO_W / 2 + 0.3), sx * (XIAO_W / 2 + 2.4)))
        body = body.union(box(lo2, hi2, y0 + 7.0, XIAO_Y1 - 1.0, FLOOR + RAIL_H, FLOOR + RAIL_H + 2.6))     # side guides, no overhang
    body = body.union(box(-4.0, 4.0, y0 - 2.0, y0 - 0.3, FLOOR - 0.1, FLOOR + RAIL_H + 1.2))
    # cutouts in the back wall: USB-C and the battery slide switch
    zu = FLOOR + RAIL_H + 1.2 + 1.6
    body = body.cut(box(-USB_W / 2, USB_W / 2, D / 2 - WALL - 0.5, D / 2 + 1, zu - USB_H / 2, zu + USB_H / 2))
    body = body.cut(box(SW_X - SW_W / 2, SW_X + SW_W / 2, D / 2 - WALL - 0.5, D / 2 + 1, SW_Z - SW_H / 2, SW_Z + SW_H / 2))
    # stick-on rubber feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(cylz(FOOT_D / 2, -0.1, FOOT_DEPTH, sx * (W / 2 - 14), sy * (D / 2 - 14)))
    return body.val()


def build_panel():
    half_v = (D / 2) / math.cos(T) + 1.5
    slab = lbox(-W / 2, W / 2, -half_v, half_v, 0, PT)
    for sx in (-1, 1):
        slab = slab.cut(lcyl(POT_HOLE / 2, -1, PT + 1, sx * POT_X, POT_V))
    slab = slab.cut(lcyl(BTN_D / 2, -1, PT + 1, 0, BTN_V))
    slab = slab.cut(lcyl(LED_D / 2, -1, PT + 1, 0, LED_V))
    for x, v in POSTS:
        slab = slab.cut(cylz(SCREW_D / 2, -1, PT + 1, x, v))
        slab = slab.cut(cq.Workplane(obj=cq.Solid.makeCone(SCREW_D / 2, SCREW_HEAD / 2, (SCREW_HEAD - SCREW_D) / 2, cq.Vector(x, v, PT - (SCREW_HEAD - SCREW_D) / 2), cq.Vector(0, 0, 1))))
        slab = slab.cut(cylz(SCREW_HEAD / 2, PT, PT + 1, x, v))
    # dot scale round each knob, 11 dots over 270 degrees from the lower left, through straight up, to the lower right
    for sx in (-1, 1):
        for i in range(TICKS):
            a = math.radians(-135 + 270 * i / (TICKS - 1))
            slab = slab.cut(cylz(TICK_D / 2, PT - TICK_DEPTH, PT + 1, sx * POT_X + TICK_R * math.sin(a), POT_V + TICK_R * math.cos(a)))
    # engraved labels (skipped quietly if the build has no font)
    labels = [("SPEED", -POT_X, -26.0, 6.0), ("JITTER", POT_X, -26.0, 6.0), ("STOP / GO", 0.0, BTN_V - 11.0, 3.6), ("SEND", 0.0, LED_V + 7.0, 3.0)]
    for txt, x, v, size in labels:
        try:
            t = cq.Workplane("XY").workplane(offset=PT).center(x, v).text(txt, size, -TEXT_DEPTH, combine=False, halign="center", valign="center", kind="bold")
            slab = slab.cut(t)
        except Exception as e:
            print("label skipped:", txt, e)
    shape = to_world(slab).intersect(prism_outer().val())
    return shape


def purchased():
    """(name, shape, colour) of the bought parts, placed for the clash test and the previews."""
    out = []
    for sx, nm in ((-1, "speed"), (1, "jitter")):
        x = sx * POT_X
        out.append((f"pot_{nm}", to_world(lcyl(8.0, -19.4, -0.4, x, POT_V).union(lcyl(3.5, -0.4, 6.6, x, POT_V)).union(lcyl(3.0, 6.6, 21.6, x, POT_V))), STEEL))
        out.append((f"nut_{nm}", to_world(lcyl(5.0, PT, PT + 2.0, x, POT_V).cut(lcyl(3.6, PT - 1, PT + 3, x, POT_V))), "#a9b0b8"))
        out.append((f"knob_{nm}", to_world(lcyl(KNOB_D / 2, 7.2, 7.2 + KNOB_H, x, POT_V).cut(lcyl(3.0, 7.0, 21.7, x, POT_V))), "#d9dde1"))
    out.append(("button", to_world(lcyl(5.9, -25.0, PT + 0.5, 0, BTN_V).union(lcyl(7.0, PT, PT + 3.0, 0, BTN_V))), "#c9a24a"))
    out.append(("led", to_world(lcyl(2.5, -8.0, PT + 0.5, 0, LED_V)), "#e03a2a"))
    y0 = XIAO_Y1 - XIAO_L
    xiao = box(-XIAO_W / 2, XIAO_W / 2, y0, XIAO_Y1, FLOOR + RAIL_H, FLOOR + RAIL_H + 1.2).union(box(-4.5, 4.5, y0 + 13.0, XIAO_Y1 + 0.8, FLOOR + RAIL_H + 1.2, FLOOR + RAIL_H + 4.4))
    out.append(("xiao_esp32s3", xiao, "#2a6fd6"))
    out.append(("lipo_503450", box(BAT_X0 + 1.25, BAT_X0 + 1.25 + BAT_W, BAT_Y0 + 0.75, BAT_Y0 + 0.75 + BAT_L, FLOOR, FLOOR + BAT_T), "#c8b04a"))
    out.append(("slide_switch", box(SW_X - 4.2, SW_X + 4.2, D / 2 - WALL - 5.0, D / 2 - WALL, SW_Z - 1.7, SW_Z + 1.7), "#444444"))
    return out


def all_parts():
    P = [("print_remote_tray", build_tray(), PRINT_C, "fixed", "print"), ("print_remote_panel", build_panel(), "#3b6ea5", "fixed", "print")]
    for nm, s, col in purchased():
        P.append((nm, s.val() if hasattr(s, "val") else s, col, "fixed", "purchase"))
    return P


def export_all(P):
    for sub in ("print", "print_ready", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")):
            old.unlink()
    for nm, s, *_ in P:
        if nm.startswith("print_"):
            cq.exporters.export(cq.Workplane(obj=s), str(PARTS / "print" / f"{nm}.step"))
            if nm.endswith("panel"):          # outer face on the bed: undo the slope, flip over, sit on Z = 0
                flat = s.translate((0, 0, -ZC)).rotate((0, 0, 0), (1, 0, 0), -TILT).rotate((0, 0, 0), (1, 0, 0), 180)
                flat = flat.translate((0, 0, -flat.BoundingBox().zmin))
                cq.exporters.export(cq.Workplane(obj=flat), str(PARTS / "print_ready" / f"{nm}.step"))
            else:
                cq.exporters.export(cq.Workplane(obj=s), str(PARTS / "print_ready" / f"{nm}.step"))
        else:
            cq.exporters.export(cq.Workplane(obj=s), str(PARTS / "purchase" / f"{nm}.step"))
    print("Wrote", len(P), "part STEP files to", PARTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    P = all_parts()
    tray, panel = P[0][1], P[1][1]
    bt = tray.BoundingBox()
    print(f"Tray {bt.xlen:.0f} x {bt.ylen:.0f} x {bt.zlen:.1f} mm; panel {panel.BoundingBox().xlen:.0f} mm wide, {TILT:g} degrees, underside {HF:.1f} mm high at the front, {HB:.1f} mm at the back")
    print(f"Mass about {tray.Volume() * sm.RHO['print'] + panel.Volume() * sm.RHO['print']:.0f} g printed (solid-volume figure, a real print with 3 walls is about 60 percent of it)")
    if a.check:
        multi = [(n, len(s.Solids())) for n, s, *_ in P if n.startswith("print_") and len(s.Solids()) != 1]
        print("printed parts that are not a single solid:", multi or "none")
        bad = sm.clashes(P)
        print("clashes between any two parts:", len(bad), bad)
        # fit checks: everything bought lies inside the tray's outer prism and below the panel plane
        pr = prism_outer().val()
        outside = []
        for n, s, *_ in P:
            if n.startswith("print_"):
                continue
            if n in ("pot_speed", "pot_jitter", "button", "led", "nut_speed", "nut_jitter", "knob_speed", "knob_jitter"):
                continue
            if abs(s.intersect(pr).Volume() - s.Volume()) > 0.5:
                outside.append(n)
        print("inside parts outside the tray outline:", outside or "none")
        # pots, button and LED must stay clear of the floor (the battery and XIAO are covered by the clash test)
        floor_hits = [n for n, s, *_ in P if n in ("pot_speed", "pot_jitter", "button", "led") and s.BoundingBox().zmin < FLOOR + 2.0]
        print("panel parts closer than 2 mm to the floor:", floor_hits or "none")
        return
    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_all(P)
    asm = cq.Assembly(name="remote")
    for nm, s, col, *_ in P:
        asm.add(s, name=nm, color=sm.cqc(col))
    asm.save(str(OUTD / f"{TAG}-assembly.step"))
    print("Wrote", OUTD / f"{TAG}-assembly.step")
    bb = (-90, 90, -70, 70, 0, 60)
    sm.render(P, IMG / "overview.png", [(28, -62, "Desk remote: SPEED, JITTER, STOP/GO and a SEND LED")], box_=(-70, 70, -55, 55, -8, 62), zoom=1.7)
    sm.render(P, IMG / "inside.png", [(55, -70, "Panel and knobs lifted off: XIAO, battery pocket, posts")], box_=(-70, 70, -50, 50, -4, 48), zoom=1.7, hide=("panel", "knob", "nut", "pot_", "button", "led"))
    sm.render(P, IMG / "back.png", [(18, 150, "Back: USB-C (charge and program) and the battery slide switch")], box_=(-70, 70, -50, 50, -4, 48), zoom=1.7)
    sm.render(P, IMG / "panel.png", [(70, -90, "Panel plate, outer face: labels and dot scales")], box_=(-70, 70, -50, 50, -4, 60), zoom=1.7, only=("panel",))
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
