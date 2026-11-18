#!/usr/bin/env python3
"""CAD assembly: smallest single sun dial, 100 mm discs, one GM2804 between them in a square frame on a round turning base,
azimuth GM2804 direct drive, no slip ring (CadQuery).
Draft, nothing built or tested.

World frame (mm): origin on the table at the centre of the round base, Z up (the STEP files are written Y up by default, for Fusion;
use --up z to keep Z up). X is east and Y is north when the dial points at
az = 90. The frame turns about Z (azimuth). At yaw 0 the frame faces run along X: the disc line points along +X when the
elevation is 0, the frame front looks towards -Y. Pose: yaw = 90 - az, so the line points at compass bearing az.

Groups:
  fixed      base shell, az stator, cable spool, base boards
  yaw        everything that turns to the azimuth: az rotor and adapter, turntable, the square frame, the elevation motor
             stator, its arm, the tray and frame boards, and the el group below
  el         turns about the disc axis (the elevation): rotor, adapter, two discs, strips, two posts, hub, pin

Design: a 120 mm square, 44 mm deep frame with a 102 mm round window in each face holds two flush 100 mm discs. The frame is
printed in three pieces: a tub (front face and four sides in one), a back lid with the second window held by four corner
screws, and an arm-and-tray piece carrying the motor bracket and the frame boards. The discs are printed in white with the
black line as a 0.6 mm inlay printed in the first layers (outer face down), or laser cut with --discs laser.
One GM2804 sits between the discs. Disc 1 rides on its rotor through a printed adapter, disc 2 is carried round the motor on two
3 mm steel posts and centred by a 6 mm pin in the motor bore. A fixed printed arm rises from a tray on the frame floor to a bracket
on the back of the motor. The posts stay on the top arc, so with the elevation within +/-90 deg they never reach the arm.
The tray carries a XIAO RP2040 and a SimpleFOC Mini for elevation. The azimuth GM2804 stands upright on the base axis with its
rotor carrying the turntable through a printed adapter, so there is no belt, tube, bearing or slip ring. Four thin wires run from the
frame through a hole in the turntable and wind round a fixed spool beside the motor, so the azimuth can turn about +/-150 deg
(enough for the Sun, Moon and planets seen from the UK, which never cross north). The base holds the XIAO ESP32-S3, the azimuth
SimpleFOC Mini, compass, clock, USB-C PD board and buck converter as keep-out boards.
Motor outline is from the supplied STEP (35 mm across, 26.15 mm tall, bore 6.5 mm, four 2.4 mm holes on a 19 mm circle in the rotor
cap and on a 15.8 mm circle in the back face). The SimpleFOC Mini is 26.1 x 21.0 x 7.6 mm from its STEP.

Usage (from the repo root):
  python3 cad/src/sun_dial_small.py [--az DEG] [--el DEG] [--up y|z] [--discs printed|laser] [--check]
Writes cad/out/sun-dial/sun-dial-small/ (assembly STEP, parts/<laser|print|purchase>/ with STEP and DXF), bom/archive/sun-dials/bom-sun-dial-small.csv and
previews in cad/media/previews/sun-dial-small/.
"""
import argparse
import csv
import math
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
OUTD = CAD / "out" / "sun-dial" / "sun-dial-small"
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / "sun-dial-small"
BOMF = CAD.parent / "bom" / "archive" / "sun-dials" / "bom-sun-dial-small.csv"

# ------------------------------------------------------------------ parameters (mm)
DISC_D, DISC_T, SLOT_W = 100.0, 3.0, 3.0
S, DF, FT = 120.0, 44.0, 3.0                   # frame square, depth, 3 mm walls
WIN_R = DISC_D / 2 + 1.0                       # 1 mm shadow gap round each disc
INT = DF / 2 - FT                              # interior half depth, 19

# GM2804 (from the STEP), local z: base back face -13.4, rotor cap front 12.75
M_R, M_TOTAL, M_FRONT, M_BASE_BACK = 17.5, 26.15, 12.75, -13.4
BASE_PCD_R, BASE_ANGLES = 7.91, (-130, 50, -61, 119)
CAP_PCD_R, CAP_ANGLES = 9.5, (45, 135, 225, 315)

# elevation stack, frame-local Z (axis out of the front face)
Z_CAP = 13.0                                   # rotor cap front face
FL_T, FL_R, BOSS_R, BOSS_T = 3.0, 25.0, 8.0, 3.0
BR_T, BR_HALF = 3.0, 12.0                      # bracket on the motor back
HUB2_T = 2.5
POST_R_POS, POST_D = 22.0, 3.0
PIN_R = 3.0

# base (direct-drive azimuth motor under the turntable, no tube, belt or slip ring)
BASE_R, BASE_WALL, BASE_FLOOR = 70.0, 3.0, 6.0
AZ_FL_T, AZ_FL_R = 3.0, 25.0                   # az adapter flange between the rotor cap and the turntable
AZ_CAP_Z = BASE_FLOOR + M_TOTAL                # az rotor cap front face, 32.15
TT_Z0 = AZ_CAP_Z + AZ_FL_T                     # turntable bottom, 35.15
TT_T, TT_R = 5.0, BASE_R                  # printed turntable, 5 mm so it can take inserts, same diameter as the base
BASE_TOP = TT_Z0 - 1.15                        # wall top, 1.15 mm under the turntable (the shadow gap)
SPOOL_RI, SPOOL_RO, SPOOL_Z1 = 19.0, 21.0, 30.0
CABLE_X = -30.0                                # cable hole in the turntable and frame floor, 30 mm from the axis
PD = 0.6                                       # printed discs: depth of the black line inlay on the outer face
SCREW_PTS = ((38.0, 14.0), (-38.0, 14.0), (38.0, -14.0), (-38.0, -14.0))   # frame-local (x, z): M3 through tray and tub floor into the turntable
CORNER = S / 2 - FT - 3.5                      # lid screw and corner boss positions
PRINT_DISCS = True
ZC = TT_Z0 + TT_T + S / 2                      # frame centre height above the table

LASER_C, PRINT_C, BUY_C, DISC_C, STRIP_C, KEEP_C = "#f2f2ef", "#3a3a3a", "#6b6b68", "#ffffff", "#111111", "#e67e22"
ROTOR_C, ADAPT_C, BRASS = "#2b2b2b", "#b8860b", "#b89b3c"


# ------------------------------------------------------------------ helpers
def _shape(wp):
    return wp.val() if hasattr(wp, "val") else wp


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def cyly(r, y0, y1, x=0.0, z=0.0):
    """Cylinder along +Y from y0 to y1 at (x, z)."""
    return cq.Workplane("XZ").workplane(offset=-y1).center(x, z).circle(r).extrude(y1 - y0)


def ring_pts(cx, cy, r, angles):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in angles]


def pitch_r(n):
    return n * GT_P / (2 * math.pi)


def toothed_disc(n, z0, z1, cx=0.0, cy=0.0):
    r_tip, r_root = pitch_r(n) + 0.3, pitch_r(n) - 0.7
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        da = 2 * math.pi / n
        for f, r in ((0.0, r_root), (0.2, r_tip), (0.5, r_tip), (0.7, r_root)):
            pts.append((cx + r * math.cos(a + f * da), cy + r * math.sin(a + f * da)))
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0)


PARTS_L = []


def add(name, wp, colour, grp="fixed"):
    PARTS_L.append((name, _shape(wp), colour, grp))


def W(wp):
    """Frame-local shape (axis along +Z, up along +Y) -> world at yaw 0, centred at height ZC. Local +Z -> world -Y."""
    return _shape(wp).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, ZC))


def motor_L(cx, cy, zcap):
    z = lambda zl: zcap + (zl - M_FRONT)
    base = cylz(M_R, z(M_BASE_BACK), z(-0.5), cx, cy)
    for x, y in ring_pts(cx, cy, BASE_PCD_R, BASE_ANGLES):
        base = base.cut(cylz(1.2, z(M_BASE_BACK) - 1, z(-9.9), x, y))
    stator = base.union(cylz(4.72, z(-0.5), z(7.7), cx, cy))
    stator = stator.cut(cylz(3.25, z(M_BASE_BACK) - 1, z(5), cx, cy)).cut(cylz(2.0, z(5) - 1, z(7.7) + 1, cx, cy))   # 6.5 mm bore, 4 mm neck
    rotor = cylz(M_R, z(0), z(M_FRONT), cx, cy).cut(cylz(16.0, z(-1), z(11.25), cx, cy))
    for x, y in ring_pts(cx, cy, CAP_PCD_R, CAP_ANGLES):
        rotor = rotor.cut(cylz(1.2, z(11), z(13), x, y))
    return stator, rotor


# ------------------------------------------------------------------ frame and the elevation stack (frame-local, then W())
def hub2_solid():
    z0 = -INT
    h2 = cq.Workplane("XY").workplane(offset=z0).circle(10).extrude(HUB2_T).union(box(-24, 24, 8, 23, z0, z0 + HUB2_T))
    for x, y in ring_pts(0, 0, POST_R_POS, (45, 135)):
        h2 = h2.cut(cylz(POST_D / 2 + 0.1, z0 - 1, z0 + HUB2_T + 1, x, y))
    return h2.cut(cylz(PIN_R + 0.1, z0 - 1, z0 + HUB2_T + 1))


def disc_parts(sgn):
    """Disc and black line (frame-local). sgn +1 front, -1 back. Printed: line is a PD-deep inlay on the outer face; the back disc
    carries hub 2 as one piece. Laser: a through slot and a full-thickness strip."""
    z0 = INT if sgn > 0 else -INT - DISC_T
    z1 = z0 + DISC_T
    d = cylz(DISC_D / 2, z0, z1)
    if PRINT_DISCS:
        oz0, oz1 = (z1 - PD, z1) if sgn > 0 else (z0, z0 + PD)
        d = d.cut(box(0, DISC_D / 2 + 1, -SLOT_W / 2, SLOT_W / 2, oz0 - (0 if sgn > 0 else 1), oz1 + (1 if sgn > 0 else 0)))
        strip = box(0, DISC_D / 2, -SLOT_W / 2, SLOT_W / 2, oz0, oz1)
        if sgn < 0:
            d = d.union(hub2_solid())
    else:
        d = d.cut(box(0, DISC_D / 2 + 1, -SLOT_W / 2, SLOT_W / 2, z0 - 1, z1 + 1))
        strip = box(0, DISC_D / 2, -SLOT_W / 2, SLOT_W / 2, z0, z1)
    return d, strip


def frame_tub():
    outer = box(-S / 2, S / 2, -S / 2, S / 2, -INT, INT + FT)
    cav = box(-S / 2 + FT, S / 2 - FT, -S / 2 + FT, S / 2 - FT, -INT - 1, INT)
    tub = outer.cut(cav).cut(cylz(WIN_R, INT - 1, INT + FT + 1))
    for sx in (1, -1):
        for sy in (1, -1):
            cx, cy = sx * CORNER, sy * CORNER
            tub = tub.union(box(cx - 3.5, cx + 3.5, cy - 3.5, cy + 3.5, -INT, -INT + 14))
            tub = tub.cut(cylz(2.1, -INT - 1, -INT + 8, cx, cy))                  # M3 heat-set insert
    for x, z in SCREW_PTS:
        tub = tub.cut(cyly(1.7, -S / 2 - 1, -S / 2 + FT + 1, x, z))
    return tub.cut(cyly(5.0, -S / 2 - 1, -S / 2 + FT + 1, CABLE_X, 0))


def frame_lid():
    lid = box(-S / 2, S / 2, -S / 2, S / 2, -INT - FT, -INT).cut(cylz(WIN_R, -INT - FT - 1, -INT + 1))
    for sx in (1, -1):
        for sy in (1, -1):
            lid = lid.cut(cylz(1.7, -INT - FT - 1, -INT + 1, sx * CORNER, sy * CORNER))
    return lid


def build():
    PARTS_L.clear()
    # ---- printed frame (three pieces: tub, lid, arm and tray) and the discs
    add("frame_tub", W(frame_tub()), "#2b2b2b", "yaw")
    add("frame_lid", W(frame_lid()), "#2b2b2b", "yaw")
    for sgn, nm in ((1, "front"), (-1, "back")):
        d, strip = disc_parts(sgn)
        if PRINT_DISCS:
            add(f"disc_{nm}_printed", W(d), DISC_C, "el")
            add(f"strip_{nm}_printed", W(strip), STRIP_C, "el")
        else:
            add(f"disc_3mm_{nm}", W(d), DISC_C, "el")
            add(f"strip_black_3mm_{nm}", W(strip), STRIP_C, "el")

    # ---- elevation GM2804, adapter, posts, hub, pin, arm
    st, ro = motor_L(0, 0, Z_CAP)
    add("gm2804_stator_el", W(st), BUY_C, "yaw")
    add("gm2804_rotor_el", W(ro), ROTOR_C, "el")
    ad = cylz(FL_R, Z_CAP, Z_CAP + FL_T).union(cylz(BOSS_R, Z_CAP + FL_T, Z_CAP + FL_T + BOSS_T))
    for x, y in ring_pts(0, 0, CAP_PCD_R, CAP_ANGLES):
        ad = ad.cut(cylz(1.2, Z_CAP - 1, Z_CAP + FL_T + 1, x, y))
    post_pts = ring_pts(0, 0, POST_R_POS, (45, 135))
    for x, y in post_pts:
        ad = ad.cut(cylz(POST_D / 2 + 0.1, Z_CAP - 1, Z_CAP + FL_T + 1, x, y))
    add("adapter_hub_el", W(ad), ADAPT_C, "el")
    if not PRINT_DISCS:
        add("hub2_el", W(hub2_solid()), ADAPT_C, "el")
    for k, (x, y) in enumerate(post_pts):
        add(f"post_3mm_{k + 1}", W(cylz(POST_D / 2, -INT, Z_CAP + FL_T, x, y)), BUY_C, "el")
    add("pin_6mm", W(cylz(PIN_R, -INT, 1.0)), BUY_C, "el")
    z_bk0 = Z_CAP - M_TOTAL - BR_T
    y_floor = -(S / 2 - FT)
    arm = box(-BR_HALF, BR_HALF, -BR_HALF, BR_HALF, z_bk0, z_bk0 + BR_T).union(box(-4, 4, y_floor + 2.0, -BR_HALF + 0.5, z_bk0, z_bk0 + BR_T))
    arm = arm.cut(cylz(3.6, z_bk0 - 1, z_bk0 + BR_T + 1))
    for x, y in ring_pts(0, 0, BASE_PCD_R, BASE_ANGLES):
        arm = arm.cut(cylz(1.3, z_bk0 - 1, z_bk0 + BR_T + 1, x, y))
    tray = box(-45, 45, y_floor, y_floor + 2.0, -18, 18).union(arm)
    for x, z in SCREW_PTS:
        tray = tray.cut(cyly(1.7, y_floor - 1, y_floor + 3, x, z))
    tray = tray.cut(cyly(5.0, y_floor - 1, y_floor + 3, CABLE_X, 0))
    add("arm_tray", W(tray), PRINT_C, "yaw")
    add("xiao_rp2040_keepout", W(box(-21, 0, y_floor + 2.0, y_floor + 2.0 + 7.0, -2, 15.8)), KEEP_C, "yaw")
    add("simplefoc_mini_el_keepout", W(box(8, 34.1, y_floor + 2.0, y_floor + 2.0 + 7.6, -3.5, 17.5)), KEEP_C, "yaw")

    # ---- azimuth: GM2804 upright on the base axis, rotor carries the turntable through an adapter
    sta, rot = motor_L(0, 0, AZ_CAP_Z)
    add("gm2804_stator_az", sta, BUY_C)
    add("gm2804_rotor_az", rot, ROTOR_C, "yaw")
    ada = cylz(AZ_FL_R, AZ_CAP_Z, TT_Z0)
    for x, y in ring_pts(0, 0, CAP_PCD_R, CAP_ANGLES):
        ada = ada.cut(cylz(1.2, AZ_CAP_Z - 1, TT_Z0 + 1, x, y))
    for x, y in ring_pts(0, 0, 19.0, (45, 135, 225, 315)):
        ada = ada.cut(cylz(1.3, AZ_CAP_Z - 1, TT_Z0 + 1, x, y))
    add("az_adapter", ada, ADAPT_C, "yaw")
    tt = cylz(TT_R, TT_Z0, TT_Z0 + TT_T)
    for x, y in ring_pts(0, 0, 19.0, (45, 135, 225, 315)):
        tt = tt.cut(cylz(1.7, TT_Z0 - 1, TT_Z0 + TT_T + 1, x, y))               # screws into the az adapter
    for x, z in SCREW_PTS:
        tt = tt.cut(cylz(2.1, TT_Z0 + TT_T - 4.5, TT_Z0 + TT_T + 1, x, -z))     # M3 heat-set inserts for the frame
    tt = tt.cut(cylz(5.0, TT_Z0 - 1, TT_Z0 + TT_T + 1, CABLE_X, 0))             # hole for the four frame wires
    add("turntable_print", tt, "#2b2b2b", "yaw")

    # ---- base shell, with the cable spool printed in
    shell = cylz(BASE_R, 0, BASE_TOP).cut(cylz(BASE_R - BASE_WALL, BASE_FLOOR, BASE_TOP + 1))
    spool = cylz(SPOOL_RO, BASE_FLOOR - 0.5, SPOOL_Z1).cut(cylz(SPOOL_RI, BASE_FLOOR - 1, SPOOL_Z1 + 1))
    spool = spool.cut(box(SPOOL_RO - 3, SPOOL_RO + 1, -3, 3, BASE_FLOOR - 1, BASE_FLOOR + 6))      # wire slot to the boards
    shell = shell.union(spool).cut(box(-5, 5, -BASE_R - 1, -BASE_R + BASE_WALL + 1, 10, 14))         # USB-C slot at the back (-Y)
    add("base_shell", shell, PRINT_C)

    # ---- base boards (keep-out volumes on 3 mm standoffs)
    z0 = BASE_FLOOR + 3.0
    def board(nm, cx, cy, w, d, h):
        add(nm, box(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0, z0 + h), KEEP_C)
    board("xiao_esp32s3_keepout", 10, 45, 21.0, 17.8, 5.0)
    board("simplefoc_mini_az_keepout", -45, -20, 26.1, 21.0, 7.6)
    board("compass_keepout", 48, -32, 12.0, 12.0, 3.0)
    board("clock_keepout", -40, 30, 18.0, 12.0, 5.0)
    board("pd_usbc_keepout", 0, -53.5, 13.0, 25.0, 6.0)
    board("buck_keepout", 30, -45, 15.0, 10.0, 5.0)


# ------------------------------------------------------------------ pose, assembly, checks
def posed(az=90.0, el=0.0):
    yaw = 90.0 - az
    out = []
    for nm, s, col, grp in PARTS_L:
        if grp == "el" and el:
            s = s.rotate((0, 0, ZC), (0, -1, ZC), el)
        if grp in ("yaw", "el") and yaw:
            s = s.rotate((0, 0, 0), (0, 0, 1), yaw)
        out.append((nm, s, col, grp))
    return out


def cqc(h):
    return cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255)


def assemble(az, el, yup=True):
    root = cq.Assembly(name="sun_dial_small")
    subs = {"fixed": "base_fixed", "yaw": "frame_and_turntable_yaw", "el": "discs_elevation"}
    sa = {g: cq.Assembly(name=n) for g, n in subs.items()}
    for nm, s, col, grp in posed(az, el):
        if yup:
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        sa[grp].add(s, name=nm, color=cqc(col))
    for g, a in sa.items():
        root.add(a, name=subs[g])
    return root


def clashes(parts, tol=2.0, only_with=None):
    found = []
    bbs = [(n, s, s.BoundingBox()) for n, s, _, _ in parts]
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


LASER = ("disc_3mm_", "strip_black_3mm_")
PRINT = ("arm_tray", "frame_tub", "frame_lid", "adapter_hub_el", "hub2_el", "base_shell", "az_adapter", "turntable_print",
         "disc_front_printed", "disc_back_printed", "strip_front_printed", "strip_back_printed")


def process_of(nm):
    if nm.startswith(LASER):
        return "laser"
    return "print" if nm.startswith(PRINT) else "purchase"


# print orientation, Z up for the slicer: rotation about X in degrees applied to the assembly-pose (world) shape
PRINT_ROT = {"disc_front_printed": 90, "strip_front_printed": 90, "frame_tub": 90, "disc_back_printed": -90, "strip_back_printed": -90,
             "frame_lid": -90, "adapter_hub_el": -90, "hub2_el": -90, "arm_tray": 0, "base_shell": 0, "turntable_print": 0, "az_adapter": 0}


def lay_flat(sh, rot):
    r = sh.rotate((0, 0, 0), (1, 0, 0), rot) if rot else sh
    bb = r.BoundingBox()
    return r.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def export_parts(yup=True):
    for sub in ("laser", "print", "purchase", "print_ready"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")) + list(d.glob("*.dxf")):
            old.unlink()
    for nm, s, _, _ in PARTS_L:
        sh = s.rotate((0, 0, 0), (1, 0, 0), -90) if yup else s
        cq.exporters.export(cq.Workplane(obj=sh), str(PARTS / process_of(nm) / f"{nm}.step"))
    # print-ready files: each printed part laid in its print orientation (Z up), flat on the bed
    byname = {nm: s for nm, s, _, _ in PARTS_L}
    n = 0
    for nm, rot in PRINT_ROT.items():
        if nm in byname:
            cq.exporters.export(cq.Workplane(obj=lay_flat(byname[nm], rot)), str(PARTS / "print_ready" / f"{nm}.step")); n += 1
    if PRINT_DISCS:                                  # two-body STEP so Bambu Studio loads each disc as one multi-colour object
        for side in ("front", "back"):
            rot = PRINT_ROT[f"disc_{side}_printed"]
            disc, strip = byname[f"disc_{side}_printed"], byname[f"strip_{side}_printed"]
            r = disc.rotate((0, 0, 0), (1, 0, 0), rot)
            bb = r.BoundingBox()
            tr = (-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin)
            comp = cq.Compound.makeCompound([r.translate(tr), strip.rotate((0, 0, 0), (1, 0, 0), rot).translate(tr)])
            cq.exporters.export(cq.Workplane(obj=comp), str(PARTS / "print_ready" / f"disc_{side}_2colour.step")); n += 1
    d = PARTS / "laser"
    nflat = 0
    if not PRINT_DISCS:
        flat = {"disc_3mm_x2": cylz(DISC_D / 2, 0, DISC_T).cut(box(0, DISC_D / 2 + 1, -SLOT_W / 2, SLOT_W / 2, -1, DISC_T + 1)),
                "strip_black_3mm_x2": box(0, DISC_D / 2, 0, SLOT_W, 0, DISC_T)}
        for nm, w in flat.items():
            cq.exporters.exportDXF(cq.Workplane(obj=_shape(w)).faces("<Z").val(), str(d / f"{nm}.dxf"))
        nflat = len(flat)
    print("Wrote", len(PARTS_L), "part STEP files,", n, "print-ready STEP files and", nflat, "laser DXF outlines to", PARTS)


def write_bom():
    rows = []
    if PRINT_DISCS:
        rows += [("print", f"White PETG or ASA, {DISC_D:.0f} mm disc with a {PD} mm black inlay line (printed outer face down, 2 colours via the AMS): front disc, and back disc with hub 2 in one piece", 2, "files: print_ready/disc_*_2colour.step"),
                 ("print", "Black filament for the two line inlays (same print jobs)", 0, "")]
    else:
        rows += [("laser", f"White acrylic 3 mm: disc {DISC_D:.0f} mm with a {SLOT_W:.0f} mm radial slot", 2, "own cutter"),
                 ("laser", f"Black acrylic 3 mm: strip {SLOT_W:.0f} x {DISC_D / 2:.0f}, pressed into the slot", 2, "own cutter"),
                 ("print", "PETG-CF: hub 2", 1, "")]
    rows += [
        ("print", "PETG-CF: frame tub (front face and four sides), frame lid (back face), arm and tray with the motor bracket", 3, "Bambu P1S, hardened nozzle"),
        ("print", "PETG-CF: turntable (5 mm), base shell with the cable spool (140 mm, 34 mm tall, USB-C slot), az adapter, elevation adapter and hub", 4, "Bambu P1S, hardened nozzle"),
        ("buy", "iPower GM2804 gimbal motor with AS5048A encoder (35 x 26.15 mm)", 2, "elevation and azimuth; confirm torque and screw size"),
        ("buy", "SimpleFOC Mini driver (26.1 x 21 x 7.6 mm)", 2, "one in the base, one in the frame"),
        ("buy", "XIAO ESP32-S3 (base) and XIAO RP2040 (frame)", 2, "ESP32 supplied"),
        ("buy", "Compass module about 12 mm square, small RTC clock breakout, USB-C PD 12 V trigger board with socket, buck converter to 5 V", 4, "sizes are placeholders"),
        ("buy", "Thin silicone wire, 4 cores (12 V, 5 V, ground, serial), about 400 mm", 1, "winds round the spool; no slip ring"),
        ("buy", "Steel rod 3 mm, 35 mm long (posts) and steel pin 6 mm, 20 mm long", 3, "cut from bars"),
        ("buy", "M3 heat-set inserts x12 (4 tub corners, 4 turntable, 4 az adapter), M3 screws, M2 screws, grub screws, thread-lock, acrylic cement or CA glue for hubs", 1, "fasteners not modelled"),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


def render(parts, path, views, hide=(), box_=None, zoom=1.2, cut=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris, cols = [], []
    light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
    for nm, s, col, _ in parts:
        if any(h in nm for h in hide):
            continue
        if cut is not None:
            s = s.cut(_shape(box(*cut)))
            if s.Volume() < 1e-6:
                continue
        v, t = s.tessellate(0.5, 0.4)
        v = np.array([(p.x, p.y, p.z) for p in v])
        base = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        for a, b, c in t:
            tri = v[[a, b, c]]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            sh = 0.55 + 0.45 * abs(float(n @ light) / nn) if nn > 1e-9 else 0.8
            tris.append(tri); cols.append(np.clip(base * sh, 0, 1))
    x0, x1, y0, y1, z0, z1 = box_ or (-90, 90, -90, 90, 0, ZC + S / 2 + 10)
    fig = plt.figure(figsize=(7 * len(views), 8.5))
    for k, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(1, len(views), k + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolors="none"))
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1)
        ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0), zoom=zoom); ax.set_axis_off(); ax.view_init(elev, azim)
        ax.set_title(title, fontsize=12)
    fig.subplots_adjust(0.0, 0.0, 1.0, 0.94, wspace=0.0)
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--az", type=float, default=90.0, help="azimuth, compass bearing in degrees (90 = line points along +X)")
    ap.add_argument("--el", type=float, default=0.0, help="elevation, degrees above horizontal (range +/-90)")
    ap.add_argument("--up", choices=("y", "z"), default="y", help="up axis of the STEP files (y for Fusion)")
    ap.add_argument("--discs", choices=("printed", "laser"), default="printed", help="printed two-colour discs (default) or laser-cut discs")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    a = ap.parse_args()
    global PRINT_DISCS
    PRINT_DISCS = a.discs == "printed"
    build()
    print(f"Base {2 * BASE_R:.0f} mm across, {BASE_TOP:.0f} mm tall; turntable top at {TT_Z0 + TT_T:.1f}; frame {S:.0f} x {S:.0f} x {DF:.0f}, centre {ZC:.0f} mm up, overall {ZC + S / 2:.0f} mm")
    print(f"Frame corner swing radius {math.hypot(S / 2, DF / 2):.1f} mm against a turntable radius of {TT_R:.0f} mm")
    print("Azimuth: GM2804 direct drive under the turntable; cable winds on a spool, travel about +/-150 deg")

    if a.check:
        movers = {n for n, _, _, g in PARTS_L if g in ("el",)}
        total = 0
        for el, az in ((0, 90), (60, 135), (-90, 200), (90, 20)):
            bad = clashes(posed(az, el), only_with=movers)
            total += len(bad)
            if bad:
                print(f"az {az} el {el}: {len(bad)} clashes", bad[:8])
        print("total clashes in the moving checks:", total)
        static = clashes(posed(90, 0))
        print("static clashes:", len(static), static[:12])
        return

    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_parts(a.up == "y")
    write_bom()
    assemble(a.az, a.el, a.up == "y").save(str(OUTD / "sun-dial-small-assembly.step"))
    print("Wrote", OUTD / "sun-dial-small-assembly.step")
    P = posed(a.az, a.el)
    keep = ("keepout",)
    render(P, IMG / "overview.png", [(14, -58, "Sun dial, 3/4 view"), (4, -90, "Front")], hide=())
    render(P, IMG / "section.png", [(0, 0, "Section through the axis, x > 0 removed")], cut=(0, 400, -400, 400, -10, 400), hide=(), zoom=1.4, box_=(-90, 90, -90, 90, 0, ZC + S / 2 + 10))
    render(P, IMG / "base-plan.png", [(90, -90, "Base from above, turntable and frame hidden")], hide=("turntable", "frame_", "gm2804_stator_el", "gm2804_rotor_el", "adapter_hub_el", "hub2_el", "post_3mm", "pin_6mm", "disc_", "strip_", "arm_tray", "xiao_rp2040", "simplefoc_mini_el", "az_adapter", "gm2804_rotor_az"),
           box_=(-80, 80, -80, 80, 0, 50), zoom=1.7)
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
