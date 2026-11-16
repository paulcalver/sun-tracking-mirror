#!/usr/bin/env python3
"""CAD assembly v2: hinged flat mirror with a hidden hinge and drive (CadQuery). Draft, nothing built or tested.

World frame (mm): origin at the centre of the base on the table, Z up, X along the hinge axis, +Y towards the
Sun side of the mirror when upright. The hinge axis sits level with the top of the base (Z = 69).
Hierarchy (maps to Fusion components, no joints yet):
  base_fixed        300 x 300 square plinth (steel floor plate, wall, top frame with a round hole), bearing ring,
                    fixed 160T hub pulley, slip ring, sensor
  drum_rotating     turns about Z, top plate flush in the frame hole: floor, wall, top plate, motors, belt, controller, bar end housings
    tilt_slider     yoke block + nut that slide along the lead screw (Y)
    mirror_tilting  origin on the hinge axis, revolute about X: bar, shaft stubs, raw 6 mm glass, crank arm and pin

What shows on the outside: the raw glass, an 18 mm half round bar (9 mm proud) and two end housings of the same
radius, on a flat top. Everything else is inside the plinth. The bar stays proud because the glass leaves it at up to
70 deg either way; a bar buried below the surface would need a slot that widens by depth x tan(tilt).

Drives:
  azimuth: NEMA 17 (34 mm) stands in the drum, 16T GT2 pulley, belt around a FIXED 160T hub pulley (10:1).
  tilt:    NEMA 17 (34 mm) lies along Y, T8x2 lead screw (via coupler), nut in a yoke block with a vertical slot,
           a crank arm (40 mm) on the hinge shaft carries a pin that slides in the slot (scotch yoke).
           Nut travel Y = 40 sin(tilt). Design range +/-70 deg (two sided: the Sun can be below the horizon).
  encoder: AS5600 style board + magnet at the left end of the hinge, inside the left housing.
Teeth: GT2 pulleys are toothed; the lead screw has no thread; belt is a plain loop.

Usage (from the repo root):
  python3 cad/src/hinge_mirror.py [--tilt DEG] [--az DEG] [--up y|z] [--check]
Writes cad/out/hinge-mirror/assembly/hinge-mirror-assembly.step, one STEP per part in
cad/out/hinge-mirror/parts/<laser|print|purchase>/, and previews in cad/media/previews/ (suffix if posed).
"""
import argparse
import math
from pathlib import Path

import cadquery as cq

CAD = Path(__file__).resolve().parent.parent
ASM = CAD / "out" / "hinge-mirror" / "assembly"
PARTS = CAD / "out" / "hinge-mirror" / "parts"
MEDIA = CAD / "media"
IMG = MEDIA / "previews"

# ------------------------------------------------------------------ parameters (mm)
MIR_W, MIR_H, GLASS_T = 200.0, 267.0, 6.0                   # raw mirror glass, no frame, no backing
BASE_HALF, WALL_T, FLOOR_T = 150.0, 3.0, 6.0                # square plinth 300 x 300, laser cut (6 mm max)
WALL_INSET = 3.0                                             # walls stand 3 mm in from the floor and frame edge (shadow gap)
WALL_NOTCH = 12.0                                            # cable notch in the bottom edge of the back wall
WW = BASE_HALF - WALL_INSET                                  # wall panel outer face at +/-147
ENG, CLR = 2.0, 0.1                                          # engraved locating pockets: 2 mm deep, 0.1 mm clearance per side (glue gap)
BRG_ID, BRG_OD, BRG_T = 114.3, 228.6, 8.33                  # 9 inch lazy Susan (Bearing King), holes not published
BELT_Z0, BELT_W = 9.0, 6.0                                  # belt band, under the bearing and above the slip ring flange
BRG_Z0 = BELT_Z0 + BELT_W + 2.0                             # bearing sits on printed posts above the belt
BRG_TOP = BRG_Z0 + BRG_T
DRUM_FLOOR_T, DRUM_R, PLATE_T = 6.0, 126.0, 6.0             # laser cut 6 mm floor and top plate
HOLE_R = DRUM_R + 1.5                                       # round hole in the square top frame (1.5 mm gap, room for the cover to sit +/-0.5 off centre)
FLOOR_HALF = BASE_HALF - 2 * WALL_INSET - WALL_T - 0.5       # base floor 287 square, loose inside the cover (cavity 288)
FLOOR_TOP = BRG_TOP + DRUM_FLOOR_T
PLATE_Z0 = FLOOR_TOP + 43.0                                 # 42 for the NEMA 17 on its side, 1 clearance
PLATE_TOP = PLATE_Z0 + PLATE_T                              # = hinge axis height
H = PLATE_TOP
BAR_R, BAR_X = 9.0, 105.5                                   # rotating bar, axis level with the surface
SLOT_HALF = BAR_R + 0.6                                     # plate slot half width
SLIT_HALF, SLIT_Z0 = 3.2, -4.0                              # slit in the bar that holds the glass tongue
GLASS_Z0 = SLIT_Z0 + 0.2                                    # tongue bottom, in the slit
GLASS_TOP = BAR_R + MIR_H                                   # visible mirror = 267 above the top of the bar
HOUS_X0, HOUS_X1 = 106.0, 120.0                             # fixed end housings (same radius as the bar)
SHAFT_R, BRG_R = 2.5, 5.5                                   # 5 mm stubs in 685 bearings (5 x 11 x 5)
L_ARM, T_MAX = 40.0, 70.0
ARM_X0, ARM_X1 = 25.8, 33.8
PIN_R = 3.0
SCREW_X, SCREW_Z = 47.0, H - 28.0
YOKE_X0, YOKE_X1, YOKE_HY = 34.0, 54.0, 9.0                 # yoke block bounds (Y half length 9)
YOKE_Z0, YOKE_Z1 = H - 47.0, H - 7.6
CTRL_Z = FLOOR_TOP + 8.0                                    # controller plate height
GUIDE_Z = H - 41.0                                          # anti-rotation guide rod, parallel to the screw, below it

GT_P = 2.0
HUB_T, MOT_T, BELT_LEN = 80, 20, 200.0                      # printed fixed 80T hub, 20T motor pulley, stock 200 mm loop
HUB_R = (HUB_T * GT_P / math.pi - 0.76) / 2
MOTP_R = (MOT_T * GT_P / math.pi - 0.76) / 2


def belt_len(c):
    hp, mp = HUB_T * GT_P / math.pi / 2, MOT_T * GT_P / math.pi / 2
    al = math.asin((hp - mp) / c)
    return 2 * math.sqrt(c * c - (hp - mp) ** 2) + hp * (math.pi + 2 * al) + mp * (math.pi - 2 * al)


def _centre_for(length):
    lo, hi = 30.0, 120.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if belt_len(mid) < length else (lo, mid)
    return (lo + hi) / 2


AZ_D = _centre_for(BELT_LEN)                                # about 45 mm: the belt stays inside the bearing bore

GREY, DARKG, STEEL = "#9a9a9a", "#4d4d4d", "#c4c8cc"
ORANGE, BLUE, BRASS, GLASS, RED, GREEN = "#e8a400", "#4a6fa5", "#b5893a", "#cfe3ee", "#c0392b", "#2e8b57"
FRAMEC, BLACK, PLY = "#8a6d2f", "#222222", "#c9a46a"


# ------------------------------------------------------------------ helpers
def _shape(wp):
    return wp.val() if hasattr(wp, "val") else wp


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def cylx(r, x0, x1, y=0.0, z=0.0):
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)


def cyly(r, y0, y1, x=0.0, z=0.0):
    """Cylinder along +Y from y0 to y1 at (x, z)."""
    return (cq.Workplane("XZ").workplane(offset=-y1).center(x, z).circle(r).extrude(y1 - y0))


def ring(ro, ri, z0, z1):
    return cylz(ro, z0, z1).cut(cylz(ri, z0 - 1, z1 + 1))


def toothed_disc(n, r_tip, r_root, z0, z1, cx=0.0, cy=0.0):
    pts = []
    for i in range(n):
        a0 = 2 * math.pi * i / n
        for frac, r in ((0.0, r_root), (0.2, r_tip), (0.55, r_tip), (0.75, r_root)):
            a = a0 + frac * 2 * math.pi / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0)


def tangents(c1, r1, c2, r2):
    d = math.dist(c1, c2)
    ux, uy = (c2[0] - c1[0]) / d, (c2[1] - c1[1]) / d
    phi = math.acos((r1 - r2) / d)
    out = []
    for s in (1, -1):
        c, sn = math.cos(s * phi), math.sin(s * phi)
        n = (ux * c - uy * sn, ux * sn + uy * c)
        out.append(((c1[0] + r1 * n[0], c1[1] + r1 * n[1]), (c2[0] + r2 * n[0], c2[1] + r2 * n[1])))
    return out


def hull(plane_fn, c1, r1, c2, r2, depth):
    t = tangents(c1, r1, c2, r2)
    quad = [t[0][0], t[0][1], t[1][1], t[1][0]]
    s = plane_fn().polyline(quad).close().extrude(depth)
    s = s.union(plane_fn().center(*c1).circle(r1).extrude(depth))
    return s.union(plane_fn().center(*c2).circle(r2).extrude(depth))


def loop(plane_fn, c1, r1, c2, r2, depth, thick):
    return hull(plane_fn, c1, r1 + thick, c2, r2 + thick, depth).cut(hull(plane_fn, c1, r1, c2, r2, depth))


def nema17(body=34.0, shaft=24.0, shaft_r=2.5):
    """Local frame: flange face at z=0, body behind (z from -body to 0), shaft +z."""
    m = box(-21, 21, -21, 21, -body, 0).edges("|Z").chamfer(3)
    return m.union(cylz(11, 0, 2)).union(cylz(shaft_r, 0, shaft))


# ------------------------------------------------------------------ parts
base_parts, drum_parts, slider_parts, mirror_parts = [], [], [], []


def add(lst, name, wp, colour):
    lst.append((name, wp, colour))


ENGRAVE, BLANK = {}, {}                                     # plate name -> engraved pocket solids / the plate before pocketing


def _entry(nm):
    for lst in (base_parts, drum_parts, slider_parts, mirror_parts):
        for i, (n, _, _) in enumerate(lst):
            if n == nm:
                return lst, i
    raise KeyError(nm)


def seat(part_nm, plate_nm, z_face, part_above):
    """Glue-seat a printed or cut part into an engraved pocket in a laser plate: the part gains a ENG mm tenon with its own
    footprint (holes kept), the plate loses a pocket of the footprint plus CLR all round. part_above: the part stands on the
    plate's top face (pocket in the top); otherwise it hangs under the plate (pocket in the underside)."""
    lst, i = _entry(part_nm)
    nm, wp, col = lst[i]
    shp = _shape(wp)
    zs = (z_face, z_face + 0.4) if part_above else (z_face - 0.4, z_face)
    slab = shp.intersect(_shape(box(-400, 400, -400, 400, *zs)))
    vec = cq.Vector(0, 0, -ENG if part_above else ENG)
    tenon = pocket = None
    for f in cq.Workplane(obj=slab).faces("<Z" if part_above else ">Z").vals():
        t = cq.Solid.extrudeLinear(f, vec)
        pf = cq.Face.makeFromWires(f.outerWire().offset2D(CLR)[0])
        pk = cq.Solid.extrudeLinear(pf, vec)
        tenon = t if tenon is None else tenon.fuse(t)
        pocket = pk if pocket is None else pocket.fuse(pk)
    lst[i] = (nm, cq.Workplane(obj=shp.fuse(tenon).clean()), col)
    plst, pi = _entry(plate_nm)
    pn, pw, pc = plst[pi]
    BLANK.setdefault(plate_nm, (pw, part_above))
    plst[pi] = (pn, cq.Workplane(obj=_shape(pw).cut(pocket).clean()), pc)
    old = ENGRAVE.get(plate_nm)
    ENGRAVE[plate_nm] = (pocket if old is None else old[0].fuse(pocket), part_above)


def seat_all():
    for nm in [f"bearing_post_{i}" for i in range(1, 7)]:
        seat(nm, "base_floor_plate_6mm", FLOOR_T, True)
    for w in ("front", "back", "right", "left"):
        seat(f"base_wall_{w}_3mm", "base_top_frame", PLATE_Z0, False)
    for nm in ([f"drum_pillar_{i}" for i in range(1, 7)] + ["controller_tray", "compass_post", "tilt_home_hall_column",
                                                            "tilt_screw_end_block", "tilt_guide_support_block"]):
        seat(nm, "drum_floor_6mm", FLOOR_TOP, True)
    for i in range(1, 7):
        seat(f"drum_pillar_{i}", "drum_top_plate_6mm", PLATE_Z0, False)


def build():
    # ============ fixed base (laser cut 6 mm ply or acrylic, printed posts and hub) ============
    B = BASE_HALF
    # the walls hang from the top frame as a cover that stands on the table; the floor sits loose inside it
    add(base_parts, "base_floor_plate_6mm", box(-FLOOR_HALF, FLOOR_HALF, -FLOOR_HALF, FLOOR_HALF, 0, FLOOR_T), BLACK)
    W3, Wi = WW - WALL_T, WW - WALL_T                           # front and back panels run full width, left and right fit between
    add(base_parts, "base_wall_front_3mm", box(-WW, WW, -WW, -W3, 0, PLATE_Z0), BLACK)
    add(base_parts, "base_wall_back_3mm", box(-WW, WW, W3, WW, 0, PLATE_Z0).cut(box(-WALL_NOTCH / 2, WALL_NOTCH / 2, W3 - 1, WW + 1, -1, 6.0)), BLACK)
    add(base_parts, "base_wall_right_3mm", box(W3, WW, -Wi, Wi, 0, PLATE_Z0), BLACK)
    add(base_parts, "base_wall_left_3mm", box(-WW, -W3, -Wi, Wi, 0, PLATE_Z0), BLACK)
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):    # corner blocks glued on the floor: they centre it in the cover (0.2 mm each side)
        x0, x1 = sorted((sx * (WW - WALL_T - 0.2), sx * (WW - WALL_T - 14.2)))
        y0, y1 = sorted((sy * (WW - WALL_T - 0.2), sy * (WW - WALL_T - 14.2)))
        add(base_parts, f"floor_locator_{i + 1}", box(x0, x1, y0, y1, FLOOR_T, FLOOR_T + 8.0), ORANGE)
    add(base_parts, "base_top_frame", box(-B, B, -B, B, PLATE_Z0, PLATE_TOP).cut(cylz(HOLE_R, PLATE_Z0 - 1, PLATE_TOP + 1)), BLACK)
    add(base_parts, "turntable_bearing_9in_lazy_susan", ring(BRG_OD / 2, BRG_ID / 2, BRG_Z0, BRG_TOP), GREY)
    for i in range(6):                                          # printed posts under the bearing (bolt holes to be matched to the real part)
        a_ = math.radians(60 * i)
        add(base_parts, f"bearing_post_{i + 1}", cylz(4.0, FLOOR_T, BRG_Z0, 86.0 * math.cos(a_), 86.0 * math.sin(a_)), ORANGE)
    hub = (toothed_disc(HUB_T, HUB_R, HUB_R - 0.75, BELT_Z0, BELT_Z0 + BELT_W)
           .union(cylz(HUB_R + 1.2, BELT_Z0 - 1.0, BELT_Z0)).union(cylz(HUB_R + 1.2, BELT_Z0 + BELT_W, BELT_Z0 + BELT_W + 1.0))
           .cut(cylz(11.05, 0, 40)))
    add(base_parts, "hub_pulley_GT2_80T_fixed", hub, ORANGE)
    add(base_parts, "slip_ring_22mm_flange44", cylz(11.0, FLOOR_T, FLOOR_T + 26.5).union(cylz(22.0, FLOOR_T, FLOOR_T + 2.0)), GREY)
    add(base_parts, "az_home_sensor", box(-4, 4, -121.5, -118.5, FLOOR_T, 19.0), GREEN)

    # ============ rotating drum ============
    floor = cylz(DRUM_R, BRG_TOP, FLOOR_TOP).cut(cylz(12.0, 0, 60)).cut(cylz(11.5, 0, 60, 0, -AZ_D))
    add(drum_parts, "drum_floor_6mm", floor, PLY)
    for i, (x, y) in enumerate(((79, 79), (-79, 79), (-79, -79), (79, -79), (0, 115), (0, -115))):
        add(drum_parts, f"drum_pillar_{i + 1}", cylz(4.0, FLOOR_TOP, PLATE_Z0, x, y), ORANGE)
    # top plate: one 6 mm laser-cut sheet with a rectangular hole across the slot, filled flush by a printed insert that has the
    # sloped relief for the crank arm on its underside (a laser cutter cannot cut a slope, and a stepped relief would show)
    slot = box(-121.0, 121.0, -SLOT_HALF, SLOT_HALF, PLATE_Z0 - 1, PLATE_TOP + 1)
    pocket = box(21.8, 38.2, -45.2, 45.2, PLATE_Z0 - 1, PLATE_TOP + 1)
    wedge = (cq.Workplane("YZ", origin=(24.0, 0, 0)).polyline([(-SLOT_HALF, H + 0.01), (SLOT_HALF, H + 0.01), (37.6, H - 7.5), (-37.6, H - 7.5)]).close()
             .extrude(12.0))
    add(drum_parts, "drum_top_plate_6mm", cylz(DRUM_R, PLATE_Z0, PLATE_TOP).cut(slot).cut(pocket), BLACK)
    add(drum_parts, "drum_arm_relief_insert", box(22.0, 38.0, -45.0, 45.0, PLATE_Z0, PLATE_TOP).cut(slot).cut(wedge), BLACK)

    # azimuth: motor stands on the floor inside the bearing bore, shaft down through the floor, pulley in the belt band
    az = nema17(body=34.0, shaft=24.0).rotate((0, 0, 0), (0, 1, 0), 180).translate((0, -AZ_D, FLOOR_TOP))
    add(drum_parts, "az_motor_NEMA17_34mm", az, GREY)
    pul = (toothed_disc(MOT_T, MOTP_R, MOTP_R - 0.75, BELT_Z0, BELT_Z0 + BELT_W, 0, -AZ_D)
           .union(cylz(7, BELT_Z0 - 1, BELT_Z0, 0, -AZ_D)).union(cylz(7, BELT_Z0 + BELT_W, BELT_Z0 + BELT_W + 1, 0, -AZ_D))
           .cut(cylz(2.5, 0, 40, 0, -AZ_D)))
    add(drum_parts, "az_motor_pulley_GT2_20T", pul, ORANGE)
    belt = loop(lambda: cq.Workplane("XY", origin=(0, 0, BELT_Z0)), (0, 0), HUB_R + 0.05, (0, -AZ_D), MOTP_R + 0.05, BELT_W, 1.5)
    add(drum_parts, "az_belt_GT2_6mm_200", belt, BLACK)
    add(drum_parts, "az_home_magnet", cylz(2.5, BRG_TOP - 2.0, BRG_TOP, 0, -120.0), RED)

    # tilt: NEMA 17 lies along Y, flange face at Y=66, body Y 66..100, coupler, lead screw, far bearing
    tm = nema17(body=34.0, shaft=10.0).rotate((0, 0, 0), (1, 0, 0), 90).translate((SCREW_X, 66.0, SCREW_Z))
    add(drum_parts, "tilt_motor_NEMA17_34mm", tm, GREY)
    coup = cyly(7.0, 48.0, 64.0, SCREW_X, SCREW_Z).cut(cyly(2.5, 56.0, 65.0, SCREW_X, SCREW_Z)).cut(cyly(4.0, 47.0, 56.0, SCREW_X, SCREW_Z))
    add(drum_parts, "tilt_coupler_5to8", coup, ORANGE)
    add(drum_parts, "tilt_leadscrew_TR8x2", cyly(4.0, -55.0, 56.0, SCREW_X, SCREW_Z), STEEL)
    fb = (box(SCREW_X - 10, SCREW_X + 10, -60.0, -52.0, FLOOR_TOP, SCREW_Z + 10).cut(cyly(8.05, -61, -55.0, SCREW_X, SCREW_Z))
          .cut(cyly(4.4, -61, -50, SCREW_X, SCREW_Z)).cut(cyly(2.05, -61, -50, SCREW_X, GUIDE_Z)))
    add(drum_parts, "tilt_screw_end_block", fb, ORANGE)
    # anti-rotation guide: 4 mm steel rod through the yoke, parallel to the screw, held by the end block and a support block
    add(drum_parts, "tilt_guide_rod_4mm", cyly(2.0, -58.0, 56.0, SCREW_X, GUIDE_Z), STEEL)
    gs = box(SCREW_X - 4, SCREW_X + 4, 50.0, 58.0, FLOOR_TOP, GUIDE_Z + 4.0).cut(cyly(2.05, 49, 59, SCREW_X, GUIDE_Z))
    add(drum_parts, "tilt_guide_support_block", gs, ORANGE)
    brg = cyly(8.0, -60.0, -55.0, SCREW_X, SCREW_Z).cut(cyly(4.0, -61, -54, SCREW_X, SCREW_Z))
    add(drum_parts, "tilt_screw_bearing_688", brg, STEEL)
    # tilt home: Hall sensor on a printed column beside the crank arm, magnet in the arm
    add(drum_parts, "tilt_home_hall_column", box(ARM_X0 - 6.5, ARM_X0 - 2.5, -3, 3, FLOOR_TOP, H - 31.0), ORANGE)
    add(drum_parts, "tilt_home_hall_sensor", box(ARM_X0 - 5.5, ARM_X0 - 1.5, -5, 5, H - 31.0, H - 21.0), GREEN)

    # hinge end housings (printed, fixed to the plate), same radius as the bar, feet under the plate
    for s, nm in ((-1, "left"), (1, "right")):
        x0, x1 = (HOUS_X0, HOUS_X1) if s > 0 else (-HOUS_X1, -HOUS_X0)
        h = cylx(BAR_R, x0, x1, 0, H).union(box(x0, x1, -16, 16, PLATE_Z0 - 3.0, PLATE_Z0, ))
        if s > 0:
            h = h.cut(cylx(BRG_R + 0.05, x0 - 1, x0 + 5, 0, H)).cut(cylx(SHAFT_R + 0.4, x0, x1 - 2, 0, H))
        else:
            h = h.cut(cylx(BRG_R + 0.05, x1 - 5, x1 + 1, 0, H)).cut(cylx(SHAFT_R + 0.4, x0 + 1.6, x1, 0, H))
        add(drum_parts, f"hinge_end_housing_{nm}", h, BLACK)
    add(drum_parts, "bearing_685_right", cylx(BRG_R, HOUS_X0, HOUS_X0 + 5, 0, H).cut(cylx(SHAFT_R, HOUS_X0 - 1, HOUS_X0 + 6, 0, H)), STEEL)
    add(drum_parts, "bearing_685_left", cylx(BRG_R, -HOUS_X0 - 5, -HOUS_X0, 0, H).cut(cylx(SHAFT_R, -HOUS_X0 - 6, -HOUS_X0 + 1, 0, H)), STEEL)

    # controller tray (printed): plate with four legs; M3 heat-set inserts in the leg bottoms take screws up through the
    # drum floor, M2 inserts in the plate take the Pico (holes 47 x 11.4 apart, from the datasheet as I remember it)
    CTRL_T = 4.0
    tray = box(-102, -24, -30, 58, CTRL_Z, CTRL_Z + CTRL_T)
    for x, y in ((-98, -26), (-28, -26), (-98, 54), (-28, 54)):
        tray = tray.union(cylz(4, FLOOR_TOP, CTRL_Z + 0.5, x, y)).cut(cylz(2.1, FLOOR_TOP - 1, FLOOR_TOP + 6, x, y))
    for x, y in ((-96, 32.8), (-96, 44.2), (-49, 32.8), (-49, 44.2)):
        tray = tray.cut(cylz(1.6, CTRL_Z + CTRL_T - 3.0, CTRL_Z + CTRL_T + 1, x, y))
    add(drum_parts, "controller_tray", tray, ORANGE)
    t = CTRL_Z + CTRL_T
    add(drum_parts, "pico_rp2040", box(-98, -47, 28, 49, t, t + 4), BLUE)
    add(drum_parts, "rtc_DS3231_module", box(-98, -60, 1, 23, t, t + 10), BLUE)
    add(drum_parts, "buck_converter", box(-96, -53, -26, -5, t, t + 14), BLUE)
    add(drum_parts, "driver_TMC2209_az", box(-46, -26, 24, 40, t, t + 11), BLUE)
    add(drum_parts, "driver_TMC2209_tilt", box(-46, -26, -8, 8, t, t + 11), BLUE)
    # compass away from the motors (test in place), on a printed post
    add(drum_parts, "compass_post", cylz(3.0, FLOOR_TOP, FLOOR_TOP + 10.0, 93.0, -33.0), ORANGE)
    add(drum_parts, "compass_GY271_module", box(86, 100, -39.5, -26.5, FLOOR_TOP + 10.0, FLOOR_TOP + 12.6), BLUE)

    # ============ tilt slider (moves along Y with the nut) ============
    yoke = (box(YOKE_X0, YOKE_X1, -YOKE_HY, YOKE_HY, YOKE_Z0, YOKE_Z1)
            .cut(box(YOKE_X0 - 1, 39.5, -3.3, 3.3, H - 43.3, YOKE_Z1 + 1))     # slot open at the top so the lid lifts off
            .cut(cyly(5.6, -YOKE_HY - 1, YOKE_HY + 1, SCREW_X, SCREW_Z))
            .cut(cyly(2.2, -YOKE_HY - 1, YOKE_HY + 1, SCREW_X, GUIDE_Z)))      # rod hole stops the yoke spinning with the screw
    add(slider_parts, "tilt_yoke_block", yoke, ORANGE)
    nut = cyly(5.5, -7.0, 7.0, SCREW_X, SCREW_Z).cut(cyly(4.0, -8, 8, SCREW_X, SCREW_Z))
    add(slider_parts, "tilt_nut_TR8x2_brass", nut, BRASS)

    # ============ tilting mirror (origin on the hinge axis, X = axis) ============
    # raw glass, centred on the axis plane; the bottom of the glass sits in a slit in the bar (bonded and clamped)
    # the back (away from the Sun) carries a 0.2 mm black paint layer, inside the 6 mm
    add(mirror_parts, "mirror_glass_6mm", box(-MIR_W / 2, MIR_W / 2, -GLASS_T / 2 + 0.2, GLASS_T / 2, GLASS_Z0, GLASS_TOP), GLASS)
    add(mirror_parts, "mirror_back_black_paint", box(-MIR_W / 2, MIR_W / 2, -GLASS_T / 2, -GLASS_T / 2 + 0.2, GLASS_Z0, GLASS_TOP), BLACK)
    bar = (cylx(BAR_R, -BAR_X, BAR_X)
           .cut(cylx(SHAFT_R, -BAR_X - 1, -100.0)).cut(cylx(SHAFT_R, 100.0, BAR_X + 1))     # stub bores at the ends only
           .cut(box(-101, 101, -SLIT_HALF, SLIT_HALF, SLIT_Z0, BAR_R + 1))
           .cut(box(22, 58, -BAR_R - 1, BAR_R + 1, -BAR_R - 1, -6.5)))                       # flat for the crank arm, clear of the yoke
    add(mirror_parts, "hinge_bar_18mm", bar, BLACK)
    add(mirror_parts, "hinge_stub_left", cylx(SHAFT_R, -114.0, -100.0), STEEL)
    add(mirror_parts, "hinge_stub_right", cylx(SHAFT_R, 100.0, 117.5), STEEL)
    # crank arm is a plate bolted to the flat under the bar (fasteners not modelled), with a pocket for the home magnet
    arm = (box(ARM_X0, ARM_X1, -3, 3, -L_ARM - 6, -6.5).cut(cylx(PIN_R, ARM_X0 - 1, ARM_X1 + 1, 0, -L_ARM))
           .cut(cylx(2.5, ARM_X0 - 1, ARM_X0 + 2, 0, -26.0)))
    add(mirror_parts, "crank_arm_40mm", arm, ORANGE)
    add(mirror_parts, "crank_pin_6mm", cylx(PIN_R, ARM_X0, 39.3, 0, -L_ARM), STEEL)
    add(mirror_parts, "tilt_home_magnet_5x2", cylx(2.5, ARM_X0, ARM_X0 + 2, 0, -26.0), RED)
    seat_all()


# ------------------------------------------------------------------ posing, export, checks
def slider_y(tilt):
    return L_ARM * math.sin(math.radians(tilt))


def posed(az, tilt):
    out = []
    for nm, wp, col in base_parts:
        out.append((nm, _shape(wp), col))
    for nm, wp, col in drum_parts:
        out.append((nm, _shape(wp).rotate((0, 0, 0), (0, 0, 1), az), col))
    for nm, wp, col in slider_parts:
        out.append((nm, _shape(wp).translate((0, slider_y(tilt), 0)).rotate((0, 0, 0), (0, 0, 1), az), col))
    for nm, wp, col in mirror_parts:
        s = _shape(wp).rotate((0, 0, 0), (1, 0, 0), tilt).translate((0, 0, H)).rotate((0, 0, 0), (0, 0, 1), az)
        out.append((nm, s, col))
    return out


def cqc(hexs):
    h = hexs.lstrip("#")
    return cq.Color(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, 1.0)


def assemble(az, tilt, yup=False):
    """Model frame is Z up (base on Z = 0). yup=True turns the whole assembly so +Y is up, as Fusion expects by default
    (the base then sits flat on the XZ plane, the mirror faces +Z when upright)."""
    root = cq.Assembly(name="sun_mirror_hinge_v2", loc=cq.Location(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90) if yup else None)
    base = cq.Assembly(name="base_fixed")
    for nm, wp, col in base_parts:
        base.add(wp, name=nm, color=cqc(col))
    root.add(base, name="base_fixed")
    drum = cq.Assembly(name="drum_rotating")
    for nm, wp, col in drum_parts:
        drum.add(wp, name=nm, color=cqc(col))
    sl = cq.Assembly(name="tilt_slider")
    for nm, wp, col in slider_parts:
        sl.add(wp, name=nm, color=cqc(col))
    drum.add(sl, name="tilt_slider", loc=cq.Location(cq.Vector(0, slider_y(tilt), 0)))
    mir = cq.Assembly(name="mirror_tilting")
    for nm, wp, col in mirror_parts:
        mir.add(wp, name=nm, color=cqc(col))
    drum.add(mir, name="mirror_tilting", loc=cq.Location(cq.Vector(0, 0, H), cq.Vector(1, 0, 0), tilt))
    root.add(drum, name="drum_rotating", loc=cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), az))
    return root


def clashes(parts, tol=2.0, only_with=None):
    found = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _ in parts]
    for i in range(len(bbs)):
        for j in range(i + 1, len(bbs)):
            a, b = bbs[i], bbs[j]
            if only_with and not (a[0] in only_with or b[0] in only_with):
                continue
            if (a[2].xmax < b[2].xmin or b[2].xmax < a[2].xmin or a[2].ymax < b[2].ymin or b[2].ymax < a[2].ymin
                    or a[2].zmax < b[2].zmin or b[2].zmax < a[2].zmin):
                continue
            try:
                v = a[1].intersect(b[1]).Volume()
            except Exception:
                v = -1
            if v > tol:
                found.append((a[0], b[0], round(v, 1)))
    return found


LASER = {"base_floor_plate_6mm", "base_wall_front_3mm", "base_wall_back_3mm", "base_wall_left_3mm", "base_wall_right_3mm",
         "base_top_frame", "drum_floor_6mm", "drum_top_plate_6mm"}
PRINT = ("hub_pulley", "hinge_bar", "hinge_end_housing", "crank_arm", "tilt_yoke_block", "drum_arm_relief_insert",
         "tilt_screw_end_block", "tilt_guide_support_block", "tilt_home_hall_column", "bearing_post_", "drum_pillar_",
         "controller_tray", "compass_post", "floor_locator_")


def process_of(nm):
    """Folder a part belongs in: laser, print or purchase (reference model of a bought part)."""
    if nm in LASER:
        return "laser"
    return "print" if nm.startswith(PRINT) else "purchase"


def export_parts(yup=False):
    """One STEP per part in out/hinge-mirror/parts/<laser|print|purchase>/, matching the BOM. Purchase files are reference shapes for
    fit checks only. Parts keep their assembly-frame coordinates (mirror_tilting parts are in the hinge axis frame)."""
    for sub in ("laser", "print", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.step"):
            old.unlink()                                            # drop parts that no longer exist
    n = 0
    for lst in (base_parts, drum_parts, slider_parts, mirror_parts):
        for nm, wp, _ in lst:
            if yup:
                wp = _shape(wp).rotate((0, 0, 0), (1, 0, 0), -90)
            cq.exporters.export(wp, str(PARTS / process_of(nm) / f"{nm}.step"))
            n += 1
    print("Wrote", n, "part STEP files to", PARTS)
    export_dxf()


def export_dxf():
    """Flat outlines of the laser parts in out/hinge-mirror/parts/laser/*.dxf (mm): <name>.dxf is the cut, <name>_engrave.dxf the shallow
    locating pockets (ENG mm deep). Plates with pockets in the underside (top frame, drum top plate) have their engrave file
    mirrored in X: engrave with the sheet turned over about the Y axis, then turn it back and cut."""
    d = PARTS / "laser"
    for old in d.glob("*.dxf"):
        old.unlink()
    hw = PLATE_Z0 + ENG
    cut = {"wall_panel_long_front_3mm": box(0, 2 * WW, 0, hw, 0, WALL_T),
           "wall_panel_long_back_notch_3mm": box(0, 2 * WW, 0, hw, 0, WALL_T).cut(box(WW - WALL_NOTCH / 2, WW + WALL_NOTCH / 2, -1, 6.0, -1, WALL_T + 1)),
           "wall_panel_short_3mm_x2": box(0, 2 * (WW - WALL_T), 0, hw, 0, WALL_T)}
    for nm in ("base_floor_plate_6mm", "base_top_frame", "drum_floor_6mm", "drum_top_plate_6mm"):
        cut[nm] = BLANK[nm][0] if nm in BLANK else dict((n, w) for lst in (base_parts, drum_parts) for n, w, _ in lst)[nm]
    for nm, w in cut.items():
        cq.exporters.exportDXF(cq.Workplane(obj=_shape(w)).faces("<Z").val(), str(d / f"{nm}.dxf"))
    for nm, (pk, above) in ENGRAVE.items():
        fs = cq.Workplane(obj=pk.clean()).faces(">Z" if above else "<Z").vals()
        if not above:
            fs = [f.mirror("YZ") for f in fs]
        cq.exporters.exportDXF(fs, str(d / f"{nm}_engrave.dxf"))
    print("Wrote", len(cut), "cut and", len(ENGRAVE), "engrave DXF outlines to", d)


def render(parts, path, views, hide=(), r=215, zmax=None, zoom=1.45):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris, cols = [], []
    light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
    for nm, s, col in parts:
        if any(h in nm for h in hide):
            continue
        v, t = s.tessellate(0.6, 0.4)
        v = np.array([(p.x, p.y, p.z) for p in v])
        base = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        for a, b, c in t:
            tri = v[[a, b, c]]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            sh = 0.55 + 0.45 * abs(float(n @ light) / nn) if nn > 1e-9 else 0.8
            tris.append(tri); cols.append(np.clip(base * sh, 0, 1))
    fig = plt.figure(figsize=(8 * len(views), 8.5))
    for k, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(1, len(views), k + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolors="none"))
        zm = zmax or 2 * r
        ax.set_xlim(-r, r); ax.set_ylim(-r, r); ax.set_zlim(0, zm)
        ax.set_box_aspect((1, 1, zm / (2 * r)), zoom=zoom); ax.set_axis_off(); ax.view_init(elev, azim)
        ax.set_title(title, fontsize=12)
    fig.subplots_adjust(0.0, 0.0, 1.0, 0.94, wspace=0.0)
    fig.savefig(path, dpi=100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tilt", type=float, default=0.0, help="mirror normal elevation, deg (0 upright, + leans back)")
    ap.add_argument("--az", type=float, default=0.0, help="drum azimuth, deg")
    ap.add_argument("--up", choices=("y", "z"), default="y", help="up axis of the STEP files: y for Fusion (default), z for the script frame")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    a = ap.parse_args()
    build()

    top = H + GLASS_TOP
    print(f"Hinge axis height {H:.0f} mm (level with the top of the base), overall height upright {top:.0f} mm")
    hub_pitch, mot_pitch = HUB_T * GT_P / math.pi / 2, MOT_T * GT_P / math.pi / 2
    al = math.asin((hub_pitch - mot_pitch) / AZ_D)
    bl = 2 * math.sqrt(AZ_D ** 2 - (hub_pitch - mot_pitch) ** 2) + hub_pitch * (math.pi + 2 * al) + mot_pitch * (math.pi - 2 * al)
    print(f"Azimuth belt about {bl:.0f} mm ({bl / GT_P:.0f} teeth), wrap on 20T {math.degrees(math.pi - 2 * al):.0f} deg,"
          f" {HUB_T / MOT_T:.0f}:1, {360 / (200 * 16 * HUB_T / MOT_T):.4f} deg per 1/16 microstep")
    glass_kg = MIR_W * (GLASS_TOP - GLASS_Z0) * GLASS_T * 2.5e-6
    m_kg, d = glass_kg, (GLASS_Z0 + GLASS_TOP) / 2 / 1000
    tq = m_kg * 9.81 * d
    f70 = tq * math.tan(math.radians(T_MAX)) / (L_ARM / 1000)
    print(f"Gravity torque on the hinge, mirror flat ({m_kg:.2f} kg glass, CoG {d * 1000:.0f} mm out): {tq:.2f} N.m")
    print(f"Lead screw force at {T_MAX:.0f} deg: {f70:.0f} N; motor torque needed about {f70 * 0.002 / (2 * math.pi * 0.4):.2f} N.m (NEMA 17 34 mm about 0.255 holding)")
    print(f"Nut travel +/-{slider_y(T_MAX):.1f} mm; tilt step at upright {math.degrees(2.0 / (200 * 16) / L_ARM):.4f} deg per 1/16 microstep")
    print(f"Stall force at the nut (motor holding torque 0.255 N.m): about {0.255 * 2 * math.pi * 0.4 / 0.002:.0f} N. Limit the driver current, fit end stops.")

    if a.check:
        movers = {n for n, _, _ in mirror_parts} | {n for n, _, _ in slider_parts}
        for tilt in (0, 30, -30, 62, -62, 70, -70):
            p = posed(0, tilt)
            bad = clashes(p, only_with=movers)
            bad = [b for b in bad if not (b[0] in {n for n, _, _ in mirror_parts} and b[1] in {n for n, _, _ in mirror_parts})] if tilt else bad
            print(f"tilt {tilt:+d}: {len(bad)} clashes", bad[:8])
        return

    tag = "" if (a.tilt == 0 and a.az == 0) else f"-tilt{a.tilt:.0f}-az{a.az:.0f}"
    ASM.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_parts(a.up == "y")
    assemble(a.az, a.tilt, a.up == "y").save(str(ASM / f"hinge-mirror-assembly{tag}.step"))
    print("Wrote", ASM / f"hinge-mirror-assembly{tag}.step")
    render(posed(a.az, a.tilt), IMG / f"hinge-mirror-preview{tag}.png", [(16, 52, "Upright, seen from the front: mirror, bar, drum")])
    render(posed(30.0, a.tilt or 55.0), IMG / "hinge-mirror-preview-tilted.png", [(16, 52, f"Tilted {a.tilt or 55:.0f} deg, drum turned 30 deg")])
    hide = ("drum_top_plate", "drum_arm_relief", "base_top_frame", "base_wall", "mirror_", "hinge_", "bearing_685_", "crank_")
    render(posed(0, 0), IMG / "hinge-mirror-preview-inside.png",
           [(90, -90, "Inside the drum from above (lid and mirror hidden)")], hide=hide, r=140, zmax=120, zoom=1.6)
    render(posed(0, 45), IMG / "hinge-mirror-preview-tiltdrive.png",
           [(24, 30, "Tilt drive, wall and plate hidden, 45 deg")], hide=("drum_top_plate", "drum_arm_relief", "base_top_frame", "base_wall", "mirror_glass"), r=140, zmax=120, zoom=1.6)
    print("Wrote previews")


if __name__ == "__main__":
    main()
