#!/usr/bin/env python3
"""CAD assembly: trio of 150 mm spinning mirrors on NEMA 17 steppers, on a laser-cut plywood box (CadQuery). Draft, nothing built or tested.

This is the primary route. Each unit is the one in spinning_mirror_150_nema17.py (150 mm x 1.5 mm mirror on a free hinge in a ring, ring on a
The Pi Hut NEMA 17 42/60, open-loop step/dir, random jittering speed per motor). The printed pedestal of the single rig is replaced by a shared
plywood box: 6 mm floor, 6 mm walls, and a 6 mm deck that is the motor plate (the motors hang below it, shafts up). Drivers and the controller sit in the
box on the floor beside the steel ballast bars; the DC jack, USB-C and jitter dial are in the removable front panel.
Not in this version (the brushless trio has them): the acrylic hood and the top bar. The ring edge runs at about 2.7 m/s at 300 rpm, so
treat it as an exposed machine and keep hands clear; see docs/spinning-mirror-150-nema17.md.

World frame (mm): origin on the table at the centre of the box, Z up, X along the row, units on Y = 0.
Usage (from the repo root):
  python3 cad/src/spinning_mirror_150_nema17_trio.py [--check] [--up y|z] [--seed N]
Writes cad/out/spinning-mirror-150-nema17-trio/ (assembly STEP, parts/<laser|print|purchase>/ with DXF for the laser parts),
bom/bom-spinning-mirror-150-nema17-trio.csv and previews in cad/media/previews/spinning-mirror-150-nema17-trio/.
"""
import argparse
import csv
import math
import random
import sys
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spinning_mirror as sm                       # noqa: E402  (helpers)
import spinning_mirror_150_nema17 as u             # noqa: E402  (the unit)

CAD = HERE.parent
TAG = "spinning-mirror-150-nema17-trio"
OUTD = CAD / "out" / TAG
PARTS = OUTD / "parts"
IMG = CAD / "media" / "previews" / TAG
BOMF = CAD.parent / "bom" / f"bom-{TAG}.csv"

box, cylz, cylx, cyly = sm.box, sm.cylz, sm.cylx, sm.cyly
N = 3
ZC, R_OUT = u.ZC, u.R_OUT

# ------------------------------------------------------------------ parameters (mm)
PITCH = 2 * R_OUT + 17.0                                      # 17 mm clear between rings (186)
XS = [(i - (N - 1) / 2) * PITCH for i in range(N)]
PLY = 6.0
FLOOR_Z1 = PLY                                               # floor plate 0..6 on stick-on feet (motor bottoms are 2 mm above it)
DECK_Z1 = u.BASE_H                                           # deck top (74), the motor plate
DECK_Z0 = DECK_Z1 - PLY                                      # underside, against the motor front faces
BOX_W = 170.0
BOX_L = math.ceil(2 * (XS[-1] + R_OUT + 12.0) / 10) * 10.0    # 570
WALL_X, WALL_Y = BOX_L / 2, BOX_W / 2
TAB_W = 24.0
BALLAST_L, BALLAST_W, BALLAST_Y = 500.0, 38.0, 45.0           # two 38 x 6 flat bars stacked on the floor behind the motors
ELEC_Y = -48.0                                                # drivers and controller on the floor in front of the motors
FRONT_CUT = [(-215.0, 38.0, "round", 12.0),                   # DC barrel jack, 11 mm bushing
             (-175.0, 38.0, "rect", (11.0, 4.6)),             # USB-C panel socket
             (215.0, 38.0, "round", 7.5)]                     # jitter dial, 7 mm bushing
BACK_CUT = [(u_, 38.0, "rect", (40.0, 5.0)) for u_ in range(-240, 241, 60)]   # vents, 9 slots
WOOD = "#d2b48c"


# ------------------------------------------------------------------ laser parts
def flat_rect(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, PLY, centered=False).translate((x0, y0, 0))


def cutter(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, PLY + 2, centered=False).translate((x0, y0, -1))


def tab_centres(length, pitch=80.0):
    n = max(2, round(length / pitch))
    return [-length / 2 + (i + 0.5) * length / n for i in range(n)]


def wall_slots(w, front=True, back=True, ends=True):
    t = PLY + 0.2
    if front:
        for c in tab_centres(BOX_L):
            w = w.cut(cutter(c - TAB_W / 2 - 0.1, c + TAB_W / 2 + 0.1, -WALL_Y - 0.1, -WALL_Y + t - 0.1))
    if back:
        for c in tab_centres(BOX_L):
            w = w.cut(cutter(c - TAB_W / 2 - 0.1, c + TAB_W / 2 + 0.1, WALL_Y - t + 0.1, WALL_Y + 0.1))
    if ends:
        for sx in (-1, 1):
            x0, x1 = (-WALL_X - 0.1, -WALL_X + t - 0.1) if sx < 0 else (WALL_X - t + 0.1, WALL_X + 0.1)
            for c in tab_centres(2 * (WALL_Y - PLY)):
                w = w.cut(cutter(x0, x1, c - TAB_W / 2 - 0.1, c + TAB_W / 2 + 0.1))
    return w


def floor_flat():
    return wall_slots(flat_rect(-WALL_X, WALL_X, -WALL_Y, WALL_Y))


def deck_flat():
    w = flat_rect(-WALL_X, WALL_X, -WALL_Y, WALL_Y)
    for x in XS:
        w = w.cut(cylz(u.N_PILOT_R + 0.15, -1, PLY + 1, x, 0))                                # pilot boss and shaft
        for sx in (-1, 1):
            for sy in (-1, 1):
                w = w.cut(cylz(1.7, -1, PLY + 1, x + sx * u.N_HOLE_PITCH / 2, sy * u.N_HOLE_PITCH / 2))   # M3 from above into the motor
    for x in (-BOX_L / 4, 0.0, BOX_L / 4):                                                    # M3 wood screws into the top edge of the front panel
        w = w.cut(cylz(1.7, -1, PLY + 1, x, -WALL_Y + PLY / 2))
    return wall_slots(w, front=False)


def wall_flat(length, bottom=True, top=True, cuts=()):
    w = box(-length / 2, length / 2, FLOOR_Z1, DECK_Z0, 0, PLY)
    for c in tab_centres(length):
        if bottom:
            w = w.union(box(c - TAB_W / 2, c + TAB_W / 2, 0, FLOOR_Z1, 0, PLY))
        if top:
            w = w.union(box(c - TAB_W / 2, c + TAB_W / 2, DECK_Z0, DECK_Z1, 0, PLY))
    for (cu, cv, kind, size) in cuts:
        wp = cq.Workplane("XY").workplane(offset=-1).center(cu, cv)
        w = w.cut(wp.circle(size / 2).extrude(PLY + 2) if kind == "round" else wp.rect(*size).extrude(PLY + 2))
    return w


WALL_LEN_X = BOX_L
WALL_LEN_Y = 2 * (WALL_Y - PLY)


def place_xz(flat, y_shift):
    s = flat.val() if hasattr(flat, "val") else flat
    return s.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y_shift, 0))


def place_yz(flat, x_min):
    s = flat.val() if hasattr(flat, "val") else flat
    return s.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 90).translate((x_min, 0, 0))


# ------------------------------------------------------------------ parts
UNIT, FRAME = [], []
SKIP = {"print_base_pedestal", "print_base_lid", "rubber_feet_x4", "ballast_steel_washers"}


def build():
    u.build()
    UNIT.clear()
    FRAME.clear()
    for nm, s, col, grp, mat in u.PARTS_L:
        if nm not in SKIP:
            UNIT.append((nm, s, col, grp, mat))
    FRAME.append(("laser_floor_6mm", floor_flat().val(), WOOD, "frame", "ply"))
    FRAME.append(("laser_deck_6mm", deck_flat().translate((0, 0, DECK_Z0)).val(), WOOD, "frame", "ply"))
    FRAME.append(("laser_front_panel_6mm", place_xz(wall_flat(WALL_LEN_X, bottom=True, top=False, cuts=FRONT_CUT), -(WALL_Y - PLY)), WOOD, "frame", "ply"))
    FRAME.append(("laser_back_wall_6mm", place_xz(wall_flat(WALL_LEN_X, cuts=BACK_CUT), WALL_Y), WOOD, "frame", "ply"))
    FRAME.append(("laser_end_wall_left_6mm", place_yz(wall_flat(WALL_LEN_Y), -WALL_X), WOOD, "frame", "ply"))
    FRAME.append(("laser_end_wall_right_6mm", place_yz(wall_flat(WALL_LEN_Y), WALL_X - PLY), WOOD, "frame", "ply"))
    for k in range(2):
        FRAME.append((f"ballast_steel_bar_{k + 1}", box(-BALLAST_L / 2, BALLAST_L / 2, BALLAST_Y - BALLAST_W / 2, BALLAST_Y + BALLAST_W / 2,
                                                       FLOOR_Z1 + k * 6, FLOOR_Z1 + (k + 1) * 6).val(), sm.STEEL, "frame", "steel"))
    for k, x in enumerate(XS):
        FRAME.append((f"placeholder_driver_tmc2209_25x20x14_{k + 1}", box(x - 12.5, x + 12.5, ELEC_Y - 10, ELEC_Y + 10, FLOOR_Z1, FLOOR_Z1 + 14).val(), "#2e6f4e", "frame", "ph"))
    FRAME.append(("placeholder_controller_esp32_55x28x14", box(PITCH / 2 - 27.5, PITCH / 2 + 27.5, ELEC_Y - 14, ELEC_Y + 14, FLOOR_Z1, FLOOR_Z1 + 14).val(), "#2e6f4e", "frame", "ph"))
    for k, (hx, hy) in enumerate(((-WALL_X + 15, -WALL_Y + 15), (WALL_X - 15, -WALL_Y + 15), (-WALL_X + 15, WALL_Y - 15), (WALL_X - 15, WALL_Y - 15))):
        FRAME.append((f"rubber_foot_{k + 1}", cylz(6.0, -1.0, 0.0, hx, hy).val(), sm.RUBBER, "frame", "rubber"))


def pose_unit(i, az, tilt):
    out = []
    for nm, s, col, grp, mat in UNIT:
        if grp == "tilt":
            s = s.rotate((0, 0, ZC), (1, 0, ZC), tilt + 90)
        if grp in ("tilt", "spin"):
            s = s.rotate((0, 0, 0), (0, 0, 1), az)
        out.append((f"u{i + 1}_{nm}", s.translate((XS[i], 0, 0)), col, f"unit{i + 1}_{grp}", mat))
    return out


def all_parts(poses):
    out = list(FRAME)
    for i, (az, t) in enumerate(poses):
        out += pose_unit(i, az, t)
    return out


def random_poses(seed):
    rnd = random.Random(seed)
    return [(rnd.uniform(0, 360), rnd.uniform(0, 360)) for _ in range(N)]


RHO = dict(u.RHO, ply=0.65e-3, rubber=1.1e-3, ph=0.3e-3)


def mass_kg():
    m = {"frame": 0.0, "units": 0.0}
    for _, s, _, grp, mat in all_parts([(0, 0)] * N):
        m["units" if grp.startswith("unit") else "frame"] += s.Volume() * RHO[mat] / 1000
    return m


def export_all(yup):
    for sub in ("laser", "print", "purchase"):
        d = PARTS / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in list(d.glob("*.step")) + list(d.glob("*.dxf")):
            old.unlink()

    def put(nm, s, proc):
        sh = s.rotate((0, 0, 0), (1, 0, 0), -90) if yup else s
        u.write_step(nm, sh, PARTS / proc / f"{nm}.step")
    ready = PARTS / "print_ready"
    ready.mkdir(parents=True, exist_ok=True)
    for old in list(ready.glob("*.step")):
        old.unlink()
    for nm, s, *_ in UNIT:
        put(nm, s, "print" if nm.startswith("print_") else "purchase")
        if nm.startswith("print_"):
            u.write_step(nm, u.print_oriented(nm, s), ready / f"{nm}.step")        # one copy each; print it three times
    for nm, s, *_ in FRAME:
        put(nm, s, "laser" if nm.startswith("laser_") else "print" if nm.startswith("print_") else "purchase")
    flat = {"laser_floor_6mm": floor_flat(), "laser_deck_6mm": deck_flat(), "laser_front_panel_6mm": wall_flat(WALL_LEN_X, top=False, cuts=FRONT_CUT),
            "laser_back_wall_6mm": wall_flat(WALL_LEN_X, cuts=BACK_CUT), "laser_end_wall_6mm_x2": wall_flat(WALL_LEN_Y)}
    for nm, w in flat.items():
        cq.exporters.exportDXF(cq.Workplane(obj=w.val() if hasattr(w, "val") else w).faces("<Z").val(), str(PARTS / "laser" / f"{nm}.dxf"))
    print("Wrote", len(UNIT) + len(FRAME), "part STEP files and", len(flat), "laser DXF outlines to", PARTS)


def assemble(poses, yup):
    root = cq.Assembly(name="spinning_mirror_150_nema17_trio")
    subs = {}
    for nm, s, col, grp, _ in all_parts(poses):
        if yup:
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        subs.setdefault(grp, cq.Assembly(name=grp)).add(s, name=nm, color=sm.cqc(col))
    for a in subs.values():
        root.add(a)
    return root


def write_bom():
    rows = [
        ("laser", f"Plywood 6 mm: floor {int(BOX_L)} x {int(BOX_W)} mm (wall slots) and deck {int(BOX_L)} x {int(BOX_W)} mm (3 motor openings with M3 holes, front-panel screw holes, wall slots)", 2, "own cutter, bed 1219 x 914; DXF laser_floor_6mm, laser_deck_6mm"),
        ("laser", "Plywood 6 mm: back wall (9 vent slots), two end walls (same profile), front panel (removable: 3 screws through the deck; holes for DC jack, USB-C, dial)", 4, "DXF laser_*_wall / panel"),
        ("print", f"PETG or ASA, matt black: ring with foot, mirror carrier, hub adapter (x{N} each)", 3 * N, "Bambu P1S, 0.4 mm, 4 walls; print each ring flat"),
        ("buy", "NEMA 17 stepper 42/60 (The Pi Hut, 60 mm body): 1.68 A, 1.65 ohm, 6.2 mH, 0.64 N m holding, 5 mm D shaft, 0.5 kg", N, "check the wire order and the shaft length (24 mm assumed)"),
        ("buy", "Stepper driver TMC2209 module with heatsink; set the current to about 1.2 to 1.5 A", N, "step/dir, default 1/8 microstep (interpolated), StealthChop"),
        ("buy", "ESP32 dev board, three independent random-walk speed setpoints, acceleration limited; step pulses from the RMT or hardware timers", 1, "one board is enough for three open-loop steppers"),
        ("buy", "24 V 5 A supply (3 motors at 1.2 to 1.5 A), 5.5 x 2.1 mm DC barrel jack (12 mm hole), fuse, 100 uF 35 V capacitor per driver, 5 V buck for the ESP32", 1, ""),
        ("buy", "USB-C panel-mount socket (11 x 4.6 mm slot), wired to the ESP32 for programming", 1, ""),
        ("buy", "10k rotary potentiometer, 7 mm bushing (7.5 mm hole), knob about 20 mm: jitter amount", 1, "optional, the same can be set over USB"),
        ("buy", "Bearing 684ZZ (4 x 9 x 4)", 2 * N, ""),
        ("buy", "Steel or stainless rod 4 mm x 169 mm (hinge axle)", N, "glue to the carrier"),
        ("buy", "Acrylic mirror 1.5 mm, 150 mm discs, laser-cut, two per unit", 2 * N, "try a sample first; 2 mm if 1.5 mm dishes"),
        ("buy", "Brass slug 8 x 5 mm", N, "tune the random behaviour"),
        ("buy", f"Steel flat bar 38 x 6 mm, {int(BALLAST_L)} mm (about {BALLAST_W * 6 * BALLAST_L * 7.85e-6:.2f} kg each)", 2, "stacked on the floor behind the motors, glued or screwed down"),
        ("buy", "Heat-set inserts M3 x 5 (per unit: 2 hub top for the ring screws, 2 hub sides for the grub screws)", 4 * N, ""),
        ("buy", f"Fasteners: M3 x 10 (motor to deck, {4 * N}), M3 x 18 (ring to hub, {2 * N}, thread-locked), M3 x 5 grub ({2 * N}), M3 x 6 trim ({4 * N}), M3 x 20 wood screws (3, front panel), wood glue", 1, "set; thread-lock the grub screws"),
        ("buy", "Rubber feet 12 mm", 4, "stick-on, under the floor corners"),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--up", choices=("y", "z"), default="y")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    build()
    m = mass_kg()
    print(f"Trio: unit centres X = {', '.join(f'{x:.0f}' for x in XS)}; gap between rings {PITCH - 2 * R_OUT:.0f} mm; ring centre {ZC:.1f} mm, ring top {ZC + R_OUT:.1f} mm above the table")
    print(f"Box {BOX_L:.0f} x {BOX_W:.0f} mm, interior {DECK_Z0 - FLOOR_Z1:.0f} mm tall, deck {DECK_Z0:.0f} to {DECK_Z1:.0f} mm; ring bottom {ZC - R_OUT:.1f} mm, {ZC - R_OUT - DECK_Z1:.1f} mm over the deck")
    print(f"Mass: frame about {m['frame']:.1f} kg (steel ballast {2 * BALLAST_W * 6 * BALLAST_L * 7.85e-6:.2f} kg), {N} units about {m['units']:.2f} kg, total about {m['frame'] + m['units']:.1f} kg")
    if a.check:
        multi = [(nm, len(s.Solids())) for nm, s, *_ in UNIT + FRAME if nm.startswith(("print_", "laser_")) and len(s.Solids()) != 1]
        print("printed or cut parts that are not a single solid:", multi or "none")
        moving = lambda parts: {p[0] for p in parts if "_spin" in p[3] or "_tilt" in p[3]}
        ok = lambda b: not (b[0].split("_", 1)[1].startswith(("axle", "bearing")) and b[1].split("_", 1)[1].startswith(("axle", "bearing")))
        total = 0
        for seed in range(8):
            P = all_parts(random_poses(seed))
            bad = [b for b in sm.clashes(P, only_with=moving(P)) if ok(b)]
            total += len(bad)
            if bad:
                print(f"seed {seed}: {len(bad)} clashes", bad[:8])
        print("total clashes over 8 random poses (moving parts against everything):", total)
        static = sm.clashes(all_parts([(0, 0)] * N))
        print("static clashes at az 0, tilt 0:", len(static), static[:12])
        return

    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    export_all(a.up == "y")
    write_bom()
    P0 = random_poses(a.seed)
    assemble(P0, a.up == "y").save(str(OUTD / f"{TAG}-assembly.step"))
    print("Wrote", OUTD / f"{TAG}-assembly.step")
    P = all_parts(P0)
    bx = (-WALL_X - 15, WALL_X + 15, -WALL_Y - 15, WALL_Y + 15, 0, ZC + R_OUT + 15)
    sm.render(P, IMG / "trio.png", [(14, -35, "Trio of 150 mm mirrors, NEMA 17 drive")], box_=bx, zoom=1.05)
    sm.render(P, IMG / "trio-front.png", [(0, -90, "Front")], box_=bx, zoom=1.05)
    sm.render(P, IMG / "trio-plan.png", [(90, -90, "Plan")], box_=bx, zoom=1.05)
    sm.render(P, IMG / "trio-section.png", [(6, 90, "Section through the motors (y > 0 cut away, seen from +Y)")], box_=bx, zoom=1.05, cut_y=0.0)
    sm.render(P, IMG / "trio-box.png", [(10, -50, "Box and front panel, units hidden")], box_=(-WALL_X - 15, WALL_X + 15, -WALL_Y - 15, WALL_Y + 15, 0, 120), zoom=1.05,
              only=("laser_", "ballast", "placeholder", "rubber", "motor_"))
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
