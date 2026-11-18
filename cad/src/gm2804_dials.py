#!/usr/bin/env python3
"""CAD assembly: two-dial wall piece, each dial a 150 mm disc turned directly by an iPower GM2804 gimbal motor (CadQuery).
Draft, nothing built or tested.

World frame (mm): origin on the wall at the bottom-left corner of the plate, X to the right, Y up, Z out from the wall
towards the viewer. The left dial shows the Sun's elevation, the right dial the Sun's azimuth.

Layout (Z): wall 0 | posts to the plate back at PB | 3 mm acrylic plate | 5 mm gap | 3 mm disc. Behind the plate: a printed
case round each motor (motor in front, cable out of the back) and, between the motors, two printed bays each holding a
50 x 50 x 50 mm keep-out for a SimpleFOC Mini driver.
Drive: the motor base (stator, with the AS5048A encoder inside) is held by the case back wall. The rotor faces the plate and
carries a small printed adapter (flange plus boss) screwed to the four holes in its cap. A 6 mm pin in the boss passes through
the plate hole to a small hub bonded to the back of the disc, so the front shows only the plain disc and its black line.

Parts that turn: rotor, adapter, pin, hub, disc, strip (group rot_L, rot_R). Everything else is fixed.
Motor outline from the supplied STEP (iPower GM2804 with AS5048A): 35 mm across, 26.15 mm tall, rotor cap 1.5 mm thick with four
2.4 mm holes on a 19 mm circle, base back face four 2.4 mm holes on a 15.8 mm circle. Here it is a simplified reference shape.

Usage (from the repo root):
  python3 cad/src/gm2804_dials.py [--el DEG] [--az DEG] [--check]
Writes cad/out/sun-dial/archive/gm2804-dials/ (assembly STEP, parts/<laser|print|purchase>/ with STEP and DXF), bom/archive/sun-dials/bom-gm2804-dials.csv and
previews in cad/media/previews/gm2804-dials/.
"""
import argparse
import csv
import math
import shutil
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
OUTD = CAD / "out" / "sun-dial" / "archive" / "gm2804-dials"
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / "gm2804-dials"
BOMF = CAD.parent / "bom" / "archive" / "sun-dials" / "bom-gm2804-dials.csv"

# ------------------------------------------------------------------ parameters (mm)
PW, PH, PT = 550.0, 220.0, 3.0                 # plate (3 mm white acrylic)
DISC_D, DISC_T, GAP_D = 150.0, 3.0, 5.0        # disc, and its gap in front of the plate
CXS = (165.0, 385.0)                           # dial centres (left: elevation, right: azimuth)
CY = PH / 2
SLOT_W = 3.0                                   # radial slot in the disc (black strip pressed in)

# SimpleFOC Mini keep-out (as given: 50 mm cube) in a printed bay
KEEP = 50.0
BAY_CLR, BAY_WALL = 1.0, 2.5
BAY_IN = KEEP + 2 * BAY_CLR                    # 52
BAY_OUT = BAY_IN + 2 * BAY_WALL                # 57
BAY_GAP = 8.0
WALL_CLEAR = 5.0                               # space between the bay back and the wall (cables)
PB = BAY_OUT + WALL_CLEAR                      # plate back face height off the wall, 62

# GM2804 (from the STEP), local z: base back face -13.4, rotor cap front 12.75
M_R, M_TOTAL, M_FRONT, M_BASE_BACK = 17.5, 26.15, 12.75, -13.4
BASE_PCD_R, BASE_ANGLES = 7.91, (-130, 50, -61, 119)      # four 2.4 mm holes in the back face
CAP_PCD_R, CAP_ANGLES = 9.5, (45, 135, 225, 315)          # four 2.4 mm holes in the rotor cap
FL_T, FL_R, FL_GAP = 3.0, 12.5, 1.0            # adapter flange: thickness, radius, gap to the plate back
BOSS_R = 5.0                                   # boss through the plate
HOLE_R = 6.0                                   # plate hole
PIN_R = 3.0                                    # 6 mm pin
HUB_R, HUB_T, HUB_GAP = 8.0, 4.0, 1.0          # hub bonded to the disc back, 1 mm off the plate front
CASE_R_IN, CASE_WALL, CASE_BACK, CASE_FL_R, CASE_FL_T = 18.5, 2.0, 2.0, 28.0, 3.0
CASE_SCREW_R = 24.0                            # four M3 screws from the plate front, hidden behind the disc
POST_R, POST_H = 7.0, None                     # corner posts (height = PB)
POST_IN = 12.0

Z_CAP = PB - FL_T - FL_GAP                     # rotor cap front face
Z_PF = PB + PT                                 # plate front face
Z_DISC0 = Z_PF + GAP_D                         # disc back face
Z_DISC1 = Z_DISC0 + DISC_T

LASER_C, PRINT_C, BUY_C, DISC_C, STRIP_C, KEEP_C = "#f2f2ef", "#3a3a3a", "#6b6b68", "#ffffff", "#111111", "#e67e22"
ROTOR_C, ADAPT_C = "#2b2b2b", "#b8860b"


# ------------------------------------------------------------------ helpers
def _shape(wp):
    return wp.val() if hasattr(wp, "val") else wp


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cylz(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def ring_pts(cx, cy, r, angles):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in angles]


PARTS_L = []


def add(name, wp, colour, grp="fixed"):
    PARTS_L.append((name, _shape(wp), colour, grp))


def zmotor(zl):
    """Motor local z -> world z (rotor cap front sits at Z_CAP)."""
    return Z_CAP + (zl - M_FRONT)


# ------------------------------------------------------------------ parts
def motor(cx, cy):
    z = zmotor
    base = cylz(M_R, z(M_BASE_BACK), z(-0.5), cx, cy).cut(cylz(3.25, z(-15), z(5), cx, cy))
    for x, y in ring_pts(cx, cy, BASE_PCD_R, BASE_ANGLES):
        base = base.cut(cylz(1.2, z(M_BASE_BACK) - 1, z(-9.9), x, y))
    stator = base.union(cylz(4.72, z(-0.5), z(7.7), cx, cy))
    rotor = cylz(M_R, z(0), z(M_FRONT), cx, cy).cut(cylz(16.0, z(-1), z(11.25), cx, cy))
    for x, y in ring_pts(cx, cy, CAP_PCD_R, CAP_ANGLES):
        rotor = rotor.cut(cylz(1.2, z(11), z(13), x, y))
    return stator, rotor


def motor_case(cx, cy):
    z_back = zmotor(M_BASE_BACK) - CASE_BACK
    cup = cylz(CASE_R_IN + CASE_WALL, z_back, PB, cx, cy).cut(cylz(CASE_R_IN, z_back + CASE_BACK, PB + 1, cx, cy))
    fl = cylz(CASE_FL_R, PB - CASE_FL_T, PB, cx, cy).cut(cylz(CASE_R_IN, PB - CASE_FL_T - 1, PB + 1, cx, cy))
    c = cup.union(fl)
    c = c.cut(cylz(5.0, z_back - 1, z_back + CASE_BACK + 1, cx, cy))                       # cable hole in the back wall
    for x, y in ring_pts(cx, cy, BASE_PCD_R, BASE_ANGLES):
        c = c.cut(cylz(1.6, z_back - 1, z_back + CASE_BACK + 1, x, y))                     # M3 clearance for the base screws
    for x, y in ring_pts(cx, cy, CASE_SCREW_R, (45, 135, 225, 315)):
        c = c.cut(cylz(1.3, PB - CASE_FL_T - 1, PB + 1, x, y))                             # holes for heat-set inserts (M3)
    c = c.cut(box(cx - 4, cx + 4, cy - CASE_R_IN - CASE_WALL - 1, cy - CASE_R_IN + 1, z_back + CASE_BACK, z_back + CASE_BACK + 8))  # side cable slot
    return c


def adapter(cx, cy):
    fl = cylz(FL_R, Z_CAP, Z_CAP + FL_T, cx, cy)
    boss = cylz(BOSS_R, Z_CAP + FL_T, Z_PF - 0.5, cx, cy)
    a = fl.union(boss)
    for x, y in ring_pts(cx, cy, CAP_PCD_R, CAP_ANGLES):
        a = a.cut(cylz(1.2, Z_CAP - 1, Z_CAP + FL_T + 1, x, y))
    return a.cut(cylz(PIN_R, Z_PF - 7.0, Z_PF + 1, cx, cy))                                # 6 mm pin bore, 7 mm deep from the front


def hub(cx, cy):
    z0 = Z_PF + HUB_GAP
    h = cylz(HUB_R, z0, Z_DISC0, cx, cy).cut(cylz(PIN_R, z0 - 1, Z_DISC0 + 1, cx, cy))
    grub = cq.Workplane("YZ").workplane(offset=cx).center(cy, (z0 + Z_DISC0) / 2).circle(1.3).extrude(HUB_R + 1)   # M3 grub screw hole
    return h.cut(grub)


def disc_flat(cx=0.0, cy=0.0, z0=0.0):
    d = cylz(DISC_D / 2, z0, z0 + DISC_T, cx, cy)
    return d.cut(box(cx, cx + DISC_D / 2 + 1, cy - SLOT_W / 2, cy + SLOT_W / 2, z0 - 1, z0 + DISC_T + 1))


def strip(cx, cy, z0):
    return box(cx, cx + DISC_D / 2, cy - SLOT_W / 2, cy + SLOT_W / 2, z0, z0 + DISC_T)


def plate():
    p = cq.Workplane("XY").box(PW, PH, PT, centered=False).edges("|Z").fillet(6.0).translate((0, 0, PB))
    for cx in CXS:
        p = p.cut(cylz(HOLE_R, PB - 1, Z_PF + 1, cx, CY))
        for x, y in ring_pts(cx, CY, CASE_SCREW_R, (45, 135, 225, 315)):
            p = p.cut(cylz(1.7, PB - 1, Z_PF + 1, x, y))
    for x, y in ((POST_IN, POST_IN), (PW - POST_IN, POST_IN), (POST_IN, PH - POST_IN), (PW - POST_IN, PH - POST_IN)):
        p = p.cut(cylz(2.3, PB - 1, Z_PF + 1, x, y))
    return p


def bay(cx):
    z0, z1 = PB - BAY_OUT, PB
    h = BAY_OUT / 2
    shell = box(cx - h, cx + h, CY - h, CY + h, z0 + BAY_WALL, z1)             # lid goes at the back (z0 .. z0+wall)
    shell = shell.cut(box(cx - h + BAY_WALL, cx + h - BAY_WALL, CY - h + BAY_WALL, CY + h - BAY_WALL, z0 + BAY_WALL - 1, z1 - BAY_WALL))
    flange = box(cx - h - 3, cx + h + 3, CY - h - 3, CY + h + 3, z1 - BAY_WALL, z1).cut(
        box(cx - h + BAY_WALL, cx + h - BAY_WALL, CY - h + BAY_WALL, CY + h - BAY_WALL, z1 - BAY_WALL - 1, z1 + 1))
    return shell.union(flange)


def bay_lid(cx):
    h = BAY_OUT / 2
    return box(cx - h, cx + h, CY - h, CY + h, PB - BAY_OUT, PB - BAY_OUT + BAY_WALL)


def build():
    PARTS_L.clear()
    add("plate_3mm", plate(), LASER_C)
    for k, cx in enumerate(CXS):
        side = "L" if k == 0 else "R"
        stator, rotor = motor(cx, CY)
        add(f"gm2804_stator_{side}", stator, BUY_C)
        add(f"motor_case_{side}", motor_case(cx, CY), PRINT_C)
        add(f"gm2804_rotor_{side}", rotor, ROTOR_C, f"rot_{side}")
        add(f"adapter_{side}", adapter(cx, CY), ADAPT_C, f"rot_{side}")
        pin = cylz(PIN_R, Z_PF - 7.0 - 0.0, Z_DISC0 - 0.5, cx, CY)
        add(f"pin_6mm_{side}", pin, BUY_C, f"rot_{side}")
        add(f"hub_{side}", hub(cx, CY), ADAPT_C, f"rot_{side}")
        add(f"disc_3mm_{side}", disc_flat(cx, CY, Z_DISC0), DISC_C, f"rot_{side}")
        add(f"strip_black_3mm_{side}", strip(cx, CY, Z_DISC0), STRIP_C, f"rot_{side}")
    mid = sum(CXS) / 2
    for k, cx in enumerate((mid - (BAY_OUT + BAY_GAP) / 2, mid + (BAY_OUT + BAY_GAP) / 2)):
        nm = "AB"[k]
        add(f"driver_bay_{nm}", bay(cx), PRINT_C)
        add(f"driver_bay_lid_{nm}", bay_lid(cx), PRINT_C)
        z0 = PB - BAY_OUT + BAY_WALL + BAY_CLR
        add(f"simplefoc_mini_keepout_{nm}", box(cx - KEEP / 2, cx + KEEP / 2, CY - KEEP / 2, CY + KEEP / 2, z0, z0 + KEEP), KEEP_C)
    for k, (x, y) in enumerate(((POST_IN, POST_IN), (PW - POST_IN, POST_IN), (POST_IN, PH - POST_IN), (PW - POST_IN, PH - POST_IN))):
        post = cylz(POST_R, 0, PB, x, y).cut(cylz(2.3, -1, PB + 1, x, y))
        add(f"post_{k + 1}", post, PRINT_C)


def posed(el=0.0, az=0.0):
    """Turn the rotating groups: left disc line at el above +X, right disc line at compass bearing az (north up, east right)."""
    ang = {"rot_L": el, "rot_R": 90.0 - az}
    out = []
    for nm, s, col, grp in PARTS_L:
        if grp in ang and ang[grp]:
            cx = CXS[0] if grp == "rot_L" else CXS[1]
            s = s.rotate((cx, CY, 0), (cx, CY, 1), ang[grp])
        out.append((nm, s, col, grp))
    return out


def cqc(h):
    return cq.Color(int(h[1:3], 16) / 255, int(h[3:5], 16) / 255, int(h[5:7], 16) / 255)


def assemble(el, az):
    root = cq.Assembly(name="gm2804_dials")
    subs = {"fixed": "wall_fixed", "rot_L": "left_dial_rotating", "rot_R": "right_dial_rotating"}
    sa = {g: cq.Assembly(name=n) for g, n in subs.items()}
    for nm, s, col, grp in posed(el, az):
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


LASER = ("plate_3mm", "disc_3mm_", "strip_black_3mm_")
PRINT = ("motor_case_", "adapter_", "hub_", "driver_bay_", "post_")


def process_of(nm):
    if nm.startswith(LASER):
        return "laser"
    return "print" if nm.startswith(PRINT) else "purchase"


def export_parts():
    for sub in ("laser", "print", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")) + list(d.glob("*.dxf")):
            old.unlink()
    for nm, s, _, _ in PARTS_L:
        cq.exporters.export(cq.Workplane(obj=s), str(PARTS / process_of(nm) / f"{nm}.step"))
    d = PARTS / "laser"
    flat = {"plate_3mm": plate().translate((0, 0, -PB)),
            "disc_3mm": disc_flat(0, 0, 0),
            "strip_black_3mm": strip(0, 0, 0)}
    for nm, w in flat.items():
        cq.exporters.exportDXF(cq.Workplane(obj=_shape(w)).faces("<Z").val(), str(d / f"{nm}.dxf"))
    print("Wrote", len(PARTS_L), "part STEP files and", len(flat), "laser DXF outlines to", PARTS)


def write_bom():
    rows = [
        ("laser", f"White acrylic 3 mm: back plate {PW:.0f} x {PH:.0f} (2 x 12 mm shaft holes, 8 x 3.4 mm case screw holes, 4 x 4.6 mm post holes)", 1, "own cutter"),
        ("laser", f"White acrylic 3 mm: disc {DISC_D:.0f} mm with a {SLOT_W:.0f} mm radial slot", 2, "own cutter"),
        ("laser", f"Black acrylic 3 mm: strip {SLOT_W:.0f} x {DISC_D / 2:.0f}, pressed into the slot", 2, "own cutter"),
        ("print", "PETG-CF: motor case x2, shaft adapter x2, hub x2, driver bay x2, bay lid x2, wall post x4", 12, "Bambu P1S, hardened nozzle"),
        ("buy", "iPower GM2804 gimbal motor with AS5048A encoder", 2, "35 mm x 26.15 mm, STEP supplied; check torque and screw size with the supplier"),
        ("buy", "SimpleFOC Mini driver (kept as a 50 mm cube each)", 2, "the real board may be smaller; the bay could shrink"),
        ("buy", "ESP32 board, 12 V supply and buck converter (no space reserved yet)", 1, "needs its own place"),
        ("buy", "Silver steel pin 6 mm, 10.5 mm long", 2, "cut from one bar"),
        ("buy", "M2 screws (adapter to rotor cap, short, with thread-lock) x8, M3 screws and heat-set inserts (case to plate x8, motor base to case x8), M3 grub screws x2, M4 wall screws, plugs and spacers x4", 1, "fasteners not modelled"),
        ("buy", "VHB tape or acrylic cement for the driver bays and hubs", 1, ""),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


# ------------------------------------------------------------------ preview
def render(parts, path, views, hide=(), box_=None, zoom=1.2, cut_x=None):
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
        if cut_x is not None:
            s = s.cut(_shape(box(cut_x, 9999, -9999, 9999, -9999, 9999)))
            if s.Volume() < 1e-6:
                continue
        s = s.rotate((0, 0, 0), (1, 0, 0), 90)      # draw with Y up as plot Z; viewer on the wall front is at -Y
        v, t = s.tessellate(0.5, 0.4)
        v = np.array([(p.x, p.y, p.z) for p in v])
        base = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        for a, b, c in t:
            tri = v[[a, b, c]]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            sh = 0.55 + 0.45 * abs(float(n @ light) / nn) if nn > 1e-9 else 0.8
            tris.append(tri); cols.append(np.clip(base * sh, 0, 1))
    x0, x1, y0, y1, z0, z1 = box_ or (-20, PW + 20, -Z_DISC1 - 20, 20, -20, PH + 20)
    fig = plt.figure(figsize=(7 * len(views), 6))
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
    ap.add_argument("--el", type=float, default=30.0, help="left disc: line angle above horizontal, deg")
    ap.add_argument("--az", type=float, default=135.0, help="right disc: compass bearing, deg (north up, east right)")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    a = ap.parse_args()
    build()

    print(f"Plate {PW:.0f} x {PH:.0f} mm, {PB:.0f} mm off the wall; disc front at {Z_DISC1:.0f} mm from the wall, {GAP_D:.0f} mm in front of the plate")
    print(f"Motor case: {2 * (CASE_R_IN + CASE_WALL):.0f} mm across, back at {zmotor(M_BASE_BACK) - CASE_BACK:.1f} mm from the wall")
    print(f"Driver bays: {BAY_OUT:.0f} mm cubes holding a {KEEP:.0f} mm keep-out each ({BAY_CLR:.0f} mm clearance), {BAY_GAP:.0f} mm apart, centred between the motors")

    if a.check:
        movers = {n for n, _, _, g in PARTS_L if g.startswith("rot_")}
        total = 0
        for el, az in ((0, 0), (30, 135), (-60, 250), (90, 45)):
            bad = clashes(posed(el, az), only_with=movers)
            total += len(bad)
            if bad:
                print(f"el {el} az {az}: {len(bad)} clashes", bad[:8])
        print("total clashes in the moving checks:", total)
        static = clashes(posed(0, 0))
        print("static clashes:", len(static), static[:12])
        return

    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_parts()
    write_bom()
    assemble(a.el, a.az).save(str(OUTD / "gm2804-dials-assembly.step"))
    print("Wrote", OUTD / "gm2804-dials-assembly.step")
    P = posed(a.el, a.az)
    render(P, IMG / "front.png", [(10, -90, "Front"), (14, -60, "3/4 view")], hide=("keepout",))
    render(P, IMG / "rear.png", [(10, 90, "From behind, driver lids and plate hidden"), (24, 120, "From behind, 3/4")],
           hide=("plate_3mm", "driver_bay_lid"))
    render(P, IMG / "section.png", [(0, 0, "Side section through the left dial")], cut_x=CXS[0],
           box_=(0, 160, -Z_DISC1 - 15, 15, -15, PH + 15), zoom=1.3, hide=("keepout",))
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
