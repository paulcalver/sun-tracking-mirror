#!/usr/bin/env python3
"""CAD assembly: spinning mirror test rig, 150 mm round mirror on a free hinge inside a ring, the ring on a NEMA 17 stepper (CadQuery).
Draft, nothing built or tested. Single unit, no top support, no box or hood. See docs/spinning-mirror-150-nema17.md.

Same idea as spinning_mirror.py (concept page, option D): one motor spins the ring about the vertical axis with a randomly jittering speed,
nothing drives the hinge, and the mirror tumbles. Differences: a 150 mm mirror (1.5 mm acrylic, two discs back to back), a NEMA 17 stepper
(The Pi Hut 42/60: 42.3 mm square, 60 mm body, 5 mm D shaft) instead of the GM2804, a 4 mm axle on 684ZZ bearings, and a printed square pedestal in which the
motor hangs below the top plate with its shaft up. A stepper is run open loop (step/dir), so only the speed matters, not the position.

World frame (mm): origin on the table at the centre of the base, Z up. The ring spins about Z. Its plane is XZ and the hinge axle runs along X
through the ring centre at Z = ZC. tilt = 0 puts the mirror in the ring plane. Change MIR_R to rescale the ring, axle and weight pad
(MIR_R = 50 gives a 100 mm version on the same motor).
Hierarchy: base_fixed (pedestal, lid, ballast, motor), ring_spin (shaft, hub, ring, bearings), mirror_tilt (carrier, axle, mirrors, slug).

Usage (from the repo root):
  python3 cad/src/spinning_mirror_150_nema17.py [--az DEG] [--tilt DEG] [--up y|z] [--check]
Writes cad/out/spinning-mirror/spinning-mirror-150-nema17/ (assembly STEP, parts/<print|purchase>/), bom/bom-spinning-mirror-150-nema17.csv and previews in
cad/media/previews/spinning-mirror-150-nema17/.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spinning_mirror as sm                     # noqa: E402  (shared helpers: box, cylx/y/z, clashes, render, colours)

box, cylx, cyly, cylz, cqc = sm.box, sm.cylx, sm.cyly, sm.cylz, sm.cqc
PRINT_C, STEEL, BRASS, MIRROR, MOTOR_C, RUBBER = sm.PRINT_C, sm.STEEL, sm.BRASS, sm.MIRROR, sm.MOTOR_C, sm.RUBBER

CAD = HERE.parent
TAG = "spinning-mirror-150-nema17"
OUTD = CAD / "out" / "spinning-mirror" / TAG
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / TAG
BOMF = CAD.parent / "bom" / f"bom-{TAG}.csv"

# ------------------------------------------------------------------ parameters (mm)
# NEMA 17, The Pi Hut 42/60 (datasheet: 1.68 A, 1.65 ohm, 6.2 mH, 6.5 kg cm, 102 g cm2, 0.5 kg); face and hole dimensions are the usual NEMA 17 ones
N_W, N_L, N_CH = 42.3, 60.0, 3.0                # square face, body length (The Pi Hut 42/60), vertical edge chamfer
N_HOLE_PITCH, N_HOLE_D, N_HOLE_DEPTH = 31.0, 3.0, 4.5     # M3 tapped holes in the front face
N_PILOT_R, N_PILOT_H = 11.0, 2.0                # 22 mm pilot boss, 2 mm high
N_SHAFT_R, N_SHAFT_L = 2.5, 24.0                # 5 mm shaft, 24 mm out of the front face
N_FLAT_Y, N_FLAT_L = 2.0, 15.0                  # D flat on the +Y side, 15 mm long from the tip
N_ROTOR_I = 1.02e-5                             # kg m2, 102 g cm2 from the 42/60 datasheet

# base: open-bottom printed pedestal (print it upside down, top plate on the bed) plus a lid
BASE_H = 14.0 + N_L                             # top of the pedestal plate above the table (74 for the 60 mm motor)
BASE_HALF = 75.0                                # 150 x 150 mm footprint
WALL, PLATE_T = 4.0, 6.0
LID_Z0, LID_T = 2.0, 3.0                        # lid 2..5, rubber feet 0..2
POST_IN, POST_Z1, POST_RUN = 57.0, 24.0, 14.0   # corner posts 57..71 for the lid inserts: a full 45 degree wedge from the wall corner at z 24 down to z 10, no flat face
LID_SCREW = 62.0                                # lid screws at (+/-62, +/-62), M3 countersunk into heat-set inserts in the posts
INSERT_D = 4.2
BALLAST_R0, BALLAST_R1, BALLAST_T = 32.0, 58.0, 6.0      # steel washers or plates in a ring around the motor, about 350 g (the motor itself is 0.5 kg)
MOTOR_Z1 = BASE_H - PLATE_T                     # front face of the motor, against the underside of the plate (48)
MOTOR_Z0 = MOTOR_Z1 - N_L                       # 8
SHAFT_Z1 = MOTOR_Z1 + N_SHAFT_L                 # 72

HUB_R, HUB_T = 17.5, 15.0
HUB_Z0 = BASE_H + 3.0                           # 3 mm above the plate
HUB_Z1 = HUB_Z0 + HUB_T                         # 72, flush with the shaft tip
BORE_R = 2.55
FOOT_H, FOOT_X, FOOT_SCREW_X, FOOT_NEST = 6.0, 12.0, 8.0, 4.5     # the foot nests 4.5 mm into a pocket in the hub top

MIR_R, MIR_T = 75.0, 1.5                        # 150 mm acrylic discs, 1.5 mm
CAR_T, RIM_W, BAR_W = 6.0, 3.5, 8.0             # carrier thickness (6 mm leaves a 1 mm wall round the axle bore), rim width, bar width
SUP_R = round(0.5 * MIR_R)                      # inner support ring that keeps the thin discs flat
PAD_Y, PAD_R, SLUG_D, SLUG_T = round(0.72 * MIR_R), 9.0, 8.0, 5.0      # weight pad off axis, brass slug 8 x 5 (centred in the 6 mm carrier, 0.5 mm recessed each side)
R_IN = MIR_R + 4.0                              # 3.9 mm clearance to the carrier at its worst
R_OUT, RING_W = R_IN + 5.5, 12.0
ZC = HUB_Z1 + FOOT_H + R_OUT                    # ring and mirror centre height
AXLE_D, AXLE_L = 4.0, 2 * R_OUT                 # 4 mm axle, flush with the outer boss faces
BOSS_D, BOSS_X0 = 14.0, R_IN - 2.5              # axle bosses on the ring, inner face 1.5 mm from the mirror rim
BRG = (4.0, 9.0, 4.0)                           # 684ZZ: bore, outer diameter, width
HUB_D = 5.4                                     # carrier hub next to the inner race (5.4 leaves a wall round the 4.15 bore)
BORE_D = AXLE_D + 0.15                          # carrier axle bore: 0.15 mm of slip because printed holes shrink; glue the rod in
FOOT_SCREW_D = 3.4

RHO = {"print": 1.25e-3, "steel": 7.85e-3, "brass": 8.5e-3, "acrylic": 1.19e-3, "stator": 4.7e-3}      # g per mm3 (stator: 0.5 kg motor)

PARTS_L = []


def add(name, wp, colour, grp, mat):
    PARTS_L.append((name, sm._shape(wp), colour, grp, mat))


def build():
    PARTS_L.clear()
    # ---- pedestal shell (open at the bottom), z 2 .. BASE_H
    z0 = LID_Z0
    shell = box(-BASE_HALF, BASE_HALF, -BASE_HALF, BASE_HALF, z0, BASE_H).cut(
        box(-BASE_HALF + WALL, BASE_HALF - WALL, -BASE_HALF + WALL, BASE_HALF - WALL, z0 - 1, BASE_H - PLATE_T))
    inner = BASE_HALF - WALL
    for sx in (-1, 1):
        for sy in (-1, 1):                                   # corner posts for the lid inserts
            x0, x1 = (POST_IN, inner) if sx > 0 else (-inner, -POST_IN)
            y0, y1 = (POST_IN, inner) if sy > 0 else (-inner, -POST_IN)
            post = box(x0, x1, y0, y1, LID_Z0 + LID_T, POST_Z1)
            zw, e = POST_Z1 - POST_RUN, 0.01
            wx = [(sx * POST_IN, zw), (sx * POST_IN, POST_Z1 + e), (sx * (POST_IN + POST_RUN), POST_Z1 + e)]
            wy = [(sy * POST_IN, zw), (sy * POST_IN, POST_Z1 + e), (sy * (POST_IN + POST_RUN), POST_Z1 + e)]
            # 45 degree wedge on the two inward faces, running the full width of the post: the pedestal prints upside down, so the post grows
            # from a line in the wall corner (z 24) and every layer is supported at 45 degrees or better, no flat face and no support material
            post = post.cut(cq.Workplane("XZ").workplane(offset=-y1 - 1).polyline(wx).close().extrude(y1 - y0 + 2))
            post = post.cut(cq.Workplane("YZ").workplane(offset=x0 - 1).polyline(wy).close().extrude(x1 - x0 + 2))
            shell = shell.union(post)
            shell = shell.cut(cylz(INSERT_D / 2, LID_Z0 + LID_T - 1, LID_Z0 + LID_T + 6, sx * LID_SCREW, sy * LID_SCREW))
    shell = shell.cut(cylz(N_PILOT_R + 0.15, BASE_H - PLATE_T - 1, BASE_H + 1))            # pilot and shaft opening
    for sx in (-1, 1):
        for sy in (-1, 1):                                   # motor screws from above, heads counterbored
            x, y = sx * N_HOLE_PITCH / 2, sy * N_HOLE_PITCH / 2
            shell = shell.cut(cylz(1.7, BASE_H - PLATE_T - 1, BASE_H + 1, x, y)).cut(cylz(3.2, BASE_H - 3.0, BASE_H + 1, x, y))
    shell = shell.cut(cq.Workplane("XZ").workplane(offset=BASE_HALF - WALL - 1).polyline(
        [(-6, LID_Z0 - 1), (6, LID_Z0 - 1), (6, 11), (0, 17), (-6, 11)]).close().extrude(WALL + 2))   # wire notch in the front wall, open to the lid side and pointed at the top, so it prints without a bridge
    for sx in (-1, 1):                                       # vent slots in the side walls, the motor is enclosed and runs warm
        for yv in (-24, 0, 24):
            shell = shell.cut(cq.Workplane("YZ").workplane(offset=sx * (BASE_HALF - WALL / 2) - 3).polyline(
                [(yv, 24), (yv + 2.5, 26.5), (yv + 2.5, 56), (yv - 2.5, 56), (yv - 2.5, 26.5)]).close().extrude(6))   # pointed at the lid end, no bridge
    lid = box(-inner + 0.2, inner - 0.2, -inner + 0.2, inner - 0.2, LID_Z0, LID_Z0 + LID_T)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.cut(cylz(1.7, LID_Z0 - 1, LID_Z0 + LID_T + 1, sx * LID_SCREW, sy * LID_SCREW))
    lid = lid.cut(box(-7, 7, -inner - 1, -inner + 3, LID_Z0 - 1, LID_Z0 + LID_T + 1))      # wire slot, same place as the wall notch
    add("print_base_pedestal", shell, PRINT_C, "fixed", "print")
    add("print_base_lid", lid, PRINT_C, "fixed", "print")
    feet = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = cylz(4.5, 0, LID_Z0, sx * 68.5, sy * 68.5)
            feet = f if feet is None else feet.union(f)
    add("rubber_feet_x4", feet, RUBBER, "fixed", "print")
    add("ballast_steel_washers", cylz(BALLAST_R1, LID_Z0 + LID_T, LID_Z0 + LID_T + BALLAST_T).cut(
        cylz(BALLAST_R0, LID_Z0, LID_Z0 + LID_T + BALLAST_T + 1)), STEEL, "fixed", "steel")

    # ---- NEMA 17: body hangs below the plate, shaft up through it
    body = box(-N_W / 2, N_W / 2, -N_W / 2, N_W / 2, MOTOR_Z0, MOTOR_Z1).edges("|Z").chamfer(N_CH)
    body = body.union(cylz(N_PILOT_R, MOTOR_Z1, MOTOR_Z1 + N_PILOT_H))
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(cylz(N_HOLE_D / 2, MOTOR_Z1 - N_HOLE_DEPTH, MOTOR_Z1 + 1, sx * N_HOLE_PITCH / 2, sy * N_HOLE_PITCH / 2))
    add("motor_nema17_60mm_body", body, MOTOR_C, "fixed", "stator")
    shaft = cylz(N_SHAFT_R, MOTOR_Z1 + N_PILOT_H, SHAFT_Z1).cut(box(-5, 5, N_FLAT_Y, 5, SHAFT_Z1 - N_FLAT_L, SHAFT_Z1 + 1))
    add("motor_nema17_shaft_5mm_D", shaft, STEEL, "spin", "steel")

    # ---- hub (clamps the shaft with two grub screws) and ring
    hub = cylz(HUB_R, HUB_Z0, HUB_Z1).cut(cylz(BORE_R, HUB_Z0 - 1, HUB_Z1 + 1))
    zg = HUB_Z0 + 5.0
    for sgn in (1, -1):                                      # grub screws along +-Y: the +Y one bites the flat. M3 heat-set insert, M3 x 5 set screw
        hub = hub.cut(cyly(1.3, 0, sgn * (HUB_R + 1), 0, zg) if sgn > 0 else cyly(1.3, -HUB_R - 1, 0, 0, zg))
        hub = hub.cut(cyly(INSERT_D / 2, 6.0, HUB_R + 1, 0, zg) if sgn > 0 else cyly(INSERT_D / 2, -HUB_R - 1, -6.0, 0, zg))
    hub = hub.cut(box(-FOOT_X - 0.15, FOOT_X + 0.15, -RING_W / 2 - 0.15, RING_W / 2 + 0.15, HUB_Z1 - FOOT_NEST, HUB_Z1 + 1))   # pocket for the ring foot
    for sx in (-1, 1):
        hub = hub.cut(cylz(INSERT_D / 2, HUB_Z1 - 11.0, HUB_Z1 + 1, sx * FOOT_SCREW_X, 0))
    add("print_hub_adapter", hub, PRINT_C, "spin", "print")

    ring = cyly(R_OUT, -RING_W / 2, RING_W / 2, 0, ZC).cut(cyly(R_IN, -RING_W, RING_W, 0, ZC))
    for sx in (-1, 1):
        x0, x1 = (BOSS_X0, R_OUT) if sx > 0 else (-R_OUT, -BOSS_X0)
        ring = ring.union(cylx(BOSS_D / 2, x0, x1, 0, ZC))
        pk0, pk1 = (BOSS_X0 - 1, BOSS_X0 + BRG[2] + 0.1) if sx > 0 else (-BOSS_X0 - BRG[2] - 0.1, -BOSS_X0 + 1)
        ring = ring.cut(cylx(BRG[1] / 2 + 0.05, pk0, pk1, 0, ZC))              # bearing pocket opens to the inside
        ring = ring.cut(cylx(2.5, 0, R_OUT + 1, 0, ZC) if sx > 0 else cylx(2.5, -R_OUT - 1, 0, 0, ZC))        # axle clearance hole
    for k in range(4):                                       # balance screw holes, M3 self-tapping, in the +Y face
        a = math.radians(45 + 90 * k)
        ring = ring.cut(cyly(1.3, RING_W / 2 - 6, RING_W / 2 + 1, (R_IN + R_OUT) / 2 * math.cos(a), ZC + (R_IN + R_OUT) / 2 * math.sin(a)))
    foot_top = ZC - R_OUT + 2
    ring = ring.union(box(-FOOT_X, FOOT_X, -RING_W / 2, RING_W / 2, HUB_Z1 - FOOT_NEST, foot_top))
    ring = ring.cut(cylz(BORE_R + 0.2, HUB_Z1 - FOOT_NEST - 1, HUB_Z1 + 0.5))      # relief for the shaft tip
    z_in = ZC - R_IN
    for sx in (-1, 1):                                       # M3 x 18 from inside the ring, down through the ring bottom and foot into the hub inserts
        ring = ring.cut(cylz(FOOT_SCREW_D / 2, HUB_Z1 - FOOT_NEST - 1, z_in + 1, sx * FOOT_SCREW_X, 0)).cut(
            cylz(3.2, z_in - 2.5, z_in + 1, sx * FOOT_SCREW_X, 0))
    ring = ring.intersect(box(-R_OUT - 5, R_OUT + 5, -RING_W / 2, RING_W / 2, 0, ZC + R_OUT + 5))      # trim the bosses flush with the ring faces, so it lies flat on the bed and prints without a tilt
    add("print_ring_with_foot", ring, PRINT_C, "spin", "print")
    for nm, sx in (("bearing_684zz_a", 1), ("bearing_684zz_b", -1)):
        x0 = BOSS_X0 if sx > 0 else -BOSS_X0 - BRG[2]
        b = cylx(BRG[1] / 2, x0, x0 + BRG[2], 0, ZC).cut(cylx(BRG[0] / 2, x0 - 1, x0 + BRG[2] + 1, 0, ZC))
        add(nm, b, STEEL, "spin", "steel")

    # ---- mirror_tilt
    rim = cylz(MIR_R, ZC - CAR_T / 2, ZC + CAR_T / 2).cut(cylz(MIR_R - RIM_W, ZC - CAR_T, ZC + CAR_T))
    sup = cylz(SUP_R + 1.75, ZC - CAR_T / 2, ZC + CAR_T / 2).cut(cylz(SUP_R - 1.75, ZC - CAR_T, ZC + CAR_T))
    bar = box(-MIR_R + 1, MIR_R - 1, -BAR_W / 2, BAR_W / 2, ZC - CAR_T / 2, ZC + CAR_T / 2)
    bar2 = box(-BAR_W / 2, BAR_W / 2, -MIR_R + 1, MIR_R - 1, ZC - CAR_T / 2, ZC + CAR_T / 2)
    pad = cylz(PAD_R, ZC - CAR_T / 2, ZC + CAR_T / 2, 0, PAD_Y)
    car = rim.union(sup).union(bar).union(bar2).union(pad)
    car = car.cut(cylz(SLUG_D / 2, ZC - CAR_T, ZC + CAR_T, 0, PAD_Y))
    hub_len = BOSS_X0 - 0.1
    car = car.union(cylx(HUB_D / 2, MIR_R - 1, hub_len, 0, ZC)).union(cylx(HUB_D / 2, -hub_len, -MIR_R + 1, 0, ZC))
    car = car.cut(cylx(BORE_D / 2, -hub_len - 1, hub_len + 1, 0, ZC))
    r_b = BORE_D / 2                                                                 # flat-topped teardrop roof through the carrier body so the sideways bore does not sag when printed flat
    pts = [(-r_b * 0.7071, ZC + r_b * 0.7071), (-0.48, ZC + 2.45), (0.48, ZC + 2.45), (r_b * 0.7071, ZC + r_b * 0.7071)]
    car = car.cut(cq.Workplane("YZ").workplane(offset=-MIR_R - 1).polyline(pts).close().extrude(2 * MIR_R + 2))
    add("print_mirror_carrier", car, PRINT_C, "tilt", "print")
    add("axle_4mm_steel_rod", cylx(AXLE_D / 2, -AXLE_L / 2, AXLE_L / 2, 0, ZC), STEEL, "tilt", "steel")
    add(f"mirror_front_acrylic_{int(2 * MIR_R)}", cylz(MIR_R, ZC + CAR_T / 2, ZC + CAR_T / 2 + MIR_T), MIRROR, "tilt", "acrylic")
    add(f"mirror_back_acrylic_{int(2 * MIR_R)}", cylz(MIR_R, ZC - CAR_T / 2 - MIR_T, ZC - CAR_T / 2), MIRROR, "tilt", "acrylic")
    add("weight_slug_brass_8x5", cylz(SLUG_D / 2, ZC - SLUG_T / 2, ZC + SLUG_T / 2, 0, PAD_Y), BRASS, "tilt", "brass")


def posed(az=0.0, tilt=0.0):
    out = []
    for nm, s, col, grp, mat in PARTS_L:
        if grp == "tilt":
            s = s.rotate((0, 0, ZC), (1, 0, ZC), tilt + 90)
        if grp in ("tilt", "spin"):
            s = s.rotate((0, 0, 0), (0, 0, 1), az)
        out.append((nm, s, col, grp, mat))
    return out


def assemble(az, tilt, yup):
    root = cq.Assembly(name="spinning_mirror_150_nema17")
    subs = {"fixed": "base_fixed", "spin": "ring_spin", "tilt": "mirror_tilt"}
    sa = {g: cq.Assembly(name=n) for g, n in subs.items()}
    for nm, s, col, grp, _ in posed(az, tilt):
        if yup:
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        sa[grp].add(s, name=nm, color=cqc(col))
    for g, a in sa.items():
        root.add(a, name=subs[g])
    return root


def mass_g(grp=None, mats=None):
    return sum(s.Volume() * RHO[m] for _, s, _, g, m in PARTS_L if (grp is None or g in grp) and (mats is None or m in mats))


def inertia_z(tilt):
    """Moment of inertia about the spin axis (kg m2) of everything that turns, at the given mirror tilt, plus the stepper rotor."""
    try:
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps
    except Exception:
        return None
    tot = 0.0
    for nm, s, _, grp, mat in posed(0, tilt):
        if grp not in ("spin", "tilt"):
            continue
        p = GProp_GProps()
        BRepGProp.VolumeProperties_s(s.wrapped, p)
        m = p.Mass() * RHO[mat]
        c = p.CentreOfMass()
        tot += p.MatrixOfInertia().Value(3, 3) * RHO[mat] + m * (c.X() ** 2 + c.Y() ** 2)
    return tot * 1e-9 + N_ROTOR_I


def process_of(nm):
    return "print" if nm.startswith("print_") else "purchase"


def write_step(name, shape, path):
    """Write one part as a STEP file with a single product named after the part, so slicers (Bambu Studio, Orca) list the object
    by name instead of 'Open CASCADE STEP translator 7.9'. The solid is wrapped in a compound so no extra 'SOLID' product is written."""
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPCAFControl import STEPCAFControl_Writer
    from OCP.STEPControl import STEPControl_AsIs
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFApp import XCAFApp_Application
    from OCP.XCAFDoc import XCAFDoc_DocumentTool
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    XCAFApp_Application.GetApplication_s().NewDocument(TCollection_ExtendedString("MDTV-XCAF"), doc)
    lab = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()).AddShape(cq.Compound.makeCompound([shape]).wrapped, False)
    TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
    w = STEPCAFControl_Writer()
    w.SetNameMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    if w.Write(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"could not write {path}")


def print_oriented(name, shape):
    """The part in its printing orientation, Z up, centred on the origin, lowest point at z = 0 (see docs/spinning-mirror-150-nema17-build.md).
    Ring: flat with the +Y face up. Pedestal: upside down. Hub, carrier and lid: as modelled (upright or flat)."""
    if name == "print_ring_with_foot":
        shape = shape.rotate((0, 0, 0), (1, 0, 0), 90)
    elif name == "print_base_pedestal":
        shape = shape.rotate((0, 0, 0), (1, 0, 0), 180)
    bb = shape.BoundingBox()
    return shape.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def export_parts(yup):
    for sub in ("print", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")):
            old.unlink()
    ready = PARTS / "print_ready"
    ready.mkdir(parents=True, exist_ok=True)
    for old in list(ready.glob("*.step")):
        old.unlink()
    for nm, s, _, _, _ in PARTS_L:
        sh = s.rotate((0, 0, 0), (1, 0, 0), -90) if yup else s
        write_step(nm, sh, PARTS / process_of(nm) / f"{nm}.step")
        if nm.startswith("print_"):
            write_step(nm, print_oriented(nm, s), ready / f"{nm}.step")
    print("Wrote", len(PARTS_L), "part STEP files to", PARTS)


def write_bom():
    rows = [
        ("print", "Ring with foot: PETG or ASA, matt black, print flat (circular face on the bed, 169 x 178 mm), 4 walls, 0.2 mm; about 45 g", 1, "ream the two 9.1 mm bearing pockets and 5 mm axle holes after printing"),
        ("print", "Mirror carrier: print flat, 4 walls; about 27 g", 1, "keep it flat, a warped carrier will rub the ring"),
        ("print", "Hub adapter: print upright, 4 walls, 100 % infill for the clamp; about 16 g", 1, ""),
        ("print", "Base pedestal: print upside down (top plate on the bed), 4 walls, 20 to 25 % gyroid; about 365 g solid", 1, "150 x 150 x 72 mm; small bridges over the motor screw counterbores"),
        ("print", "Base lid: 4 walls; about 75 g", 1, ""),
        ("buy", "NEMA 17 stepper 42/60 (The Pi Hut, 60 mm body): 1.68 A, 1.65 ohm, 6.2 mH, 0.64 N m holding, 5 mm D shaft, 0.5 kg", 1, "check the shaft length (24 mm assumed) and the front-face thread depth"),
        ("buy", "Adafruit TMC2209 stepper driver breakout, with headers", 2, "one spare; 5 to 29 V motor supply, 2 A max; set about 1.2 to 1.5 A"),
        ("buy", "Heatsink for the TMC2209 (Adafruit 1493 or 1515, or a stick-on stepper-driver heatsink)", 2, "check clearance over the chip"),
        ("buy", "ESP32 dev board (38-pin or QT Py ESP32-S3)", 1, "step pulses from the RMT or a hardware timer; powered from USB for the first test"),
        ("buy", "24 V 3 A DC supply, 5.5 x 2.1 mm plug", 1, "24 V gives the torque at several hundred rpm"),
        ("buy", "DC barrel jack breakout with screw terminals, inline fuse holder and 3 A fuses", 1, "fuse in the 24 V lead"),
        ("buy", "Electrolytic capacitor 100 uF, 35 V or higher", 2, "across the driver's + and GND screw terminals, one spare"),
        ("buy", "Breadboard or perfboard, jumper wires, 22 AWG wire red/black, ferrules, heat shrink", 1, "set"),
        ("buy", "4-pin 2.54 mm extension cable or crimp kit for the motor lead", 1, "only if the motor cable is too short"),
        ("buy", "10k potentiometer and knob (jitter amount)", 1, "optional, the same can be set over USB"),
        ("buy", "Bearing 684ZZ (4 x 9 x 4 mm)", 4, "2 used, 2 spare; light grease or none"),
        ("buy", "Steel or stainless rod 4 mm x 169 mm (or a longer rod cut to length)", 1, "hinge axle"),
        ("buy", f"Mirror acrylic 1.5 mm, {int(2 * MIR_R)} mm round discs", 3, "2 used, 1 spare or a 2 mm sample; peel the protective film last"),
        ("buy", f"Brass rod {int(SLUG_D)} mm cut to {int(SLUG_T)} mm (or a steel or aluminium slug)", 1, "eccentric weight about 2 g; try without it first"),
        ("buy", "Steel flat bar 38 x 6 mm, 180 mm long, cut in 3 pieces of 60 mm (about 320 g)", 1, "ballast: lay on the lid either side of the motor, glue down"),
        ("buy", "Heat-set inserts M3 x 5.7 (4 pedestal corner posts for the lid screws, 2 hub top for the ring screws, 2 hub sides for the grub screws)", 10, "2 spare"),
        ("buy", "Screws, stainless: M3 x 6 cap head (motor, 4), M3 x 8 pan head (lid, 4), M3 x 18 (ring to hub, 2, thread-locked), M3 x 6 cup-point grub (shaft, 2), M3 x 6 pan head (ring trim, 4)", 1, "set; also a few spares; if the motor holes are deeper than 5 mm use M3 x 8 for the motor"),
        ("buy", "Thread-locking compound (medium), cyanoacrylate glue, 2-part epoxy, double-sided foam tape", 1, "set"),
        ("buy", "Rubber feet 9 mm", 4, "stick-on, under the lid corners"),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


def summary():
    print(f"Overall: {2 * BASE_HALF:.0f} mm square base, ring centre {ZC:.1f} mm above the table, top of the ring {ZC + R_OUT:.1f} mm")
    print(f"Mirror {2 * MIR_R:.0f} mm x {MIR_T} mm, ring {2 * R_IN:.0f} inside / {2 * R_OUT:.0f} outside, clearance to the carrier "
          f"{R_IN - math.hypot(MIR_R, CAR_T / 2 + MIR_T):.1f} mm at its worst, boss face to mirror rim {BOSS_X0 - MIR_R:.1f} mm")
    print(f"Mass: spinning load {mass_g(('spin', 'tilt')):.0f} g (ring, hub, shaft, carrier, mirrors, weight), mirror group {mass_g(('tilt',)):.0f} g, "
          f"base about {mass_g(('fixed',)):.0f} g with the motor and ballast")
    i0, i1 = inertia_z(0), inertia_z(90)
    if i0:
        print(f"Spin inertia {i0:.2e} kg m2 (mirror in the ring plane) to {i1:.2e} (mirror flat), solid-print figures so about 20 to 30 % high; "
              f"torque for 100 rad/s2: {100 * i1:.3f} N m, for 300 rad/s2: {300 * i1:.3f} N m")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--az", type=float, default=0.0)
    ap.add_argument("--tilt", type=float, default=0.0)
    ap.add_argument("--up", choices=("y", "z"), default="y")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    a = ap.parse_args()
    build()
    summary()

    if a.check:
        names = {p[0] for p in PARTS_L if p[3] == "tilt"}
        total = 0
        for t in range(0, 360, 15):
            bad = sm.clashes(posed(0, t), only_with=names)
            bad = [b for b in bad if not (b[0].startswith(("axle", "bearing")) and b[1].startswith(("axle", "bearing")))]
            total += len(bad)
            if bad:
                print(f"tilt {t}: {len(bad)} clashes", bad[:6])
        print("total clashes in the tilt sweep (carrier, mirrors, weight, axle against the rest):", total)
        static = sm.clashes(posed(0, 0))
        print("static clashes at az 0, tilt 0:", len(static), static[:12])
        thin = [nm for nm, s, *_ in PARTS_L if nm.startswith("print_") and len(s.Solids()) != 1]
        print("printed parts that are not a single solid:", thin or "none")
        return

    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_parts(a.up == "y")
    write_bom()
    assemble(a.az, a.tilt, a.up == "y").save(str(OUTD / f"{TAG}-assembly.step"))
    print("Wrote", OUTD / f"{TAG}-assembly.step")
    bx = (-105, 105, -105, 105, 0, ZC + R_OUT + 15)
    sm.render(posed(0, 0), IMG / "overview.png", [(14, -50, "150 mm NEMA 17 test rig, 3/4 view"), (0, -90, "Front, mirror in the ring plane")], box_=bx, zoom=1.15)
    sm.render(posed(30, 55), IMG / "tilted.png", [(16, -40, "Ring at 30 deg, mirror tilted 55 deg"), (70, -40, "From above")], box_=bx, zoom=1.15)
    sm.render(posed(0, 0), IMG / "section.png", [(10, 90, "Section through the shaft (y > 0 cut away, seen from +Y)")],
              box_=(-105, 105, -105, 105, 0, ZC + R_OUT + 15), zoom=1.25, cut_y=0.0)
    sm.render(posed(0, 0), IMG / "base-section.png", [(8, 90, "Pedestal and motor (y > 0 cut away, seen from +Y)")],
              box_=(-85, 85, -85, 85, 0, HUB_Z1 + 25), zoom=1.3, cut_y=0.0, hide=("ring", "mirror", "axle", "bearing", "carrier", "weight"))
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
