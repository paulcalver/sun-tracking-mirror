#!/usr/bin/env python3
"""CAD assembly: the smallest sun dial with light (CadQuery). Draft, nothing built or tested.

Builds on cad/src/sun_dial_small.py (same frame, motors, base and turntable) and adds the glow designed in sim/sun-dials/sun-dial-glow.html:
  - opal (milk-white) 3 mm cast acrylic discs, laser cut, with the black strip pressed in (the --discs laser variant)
  - a perimeter LED strip on three inner walls of the frame (left, top, right), LEDs facing in, so the cavity is a diffuse light box
    and both discs glow; the interior is painted matt white and the printed tub and lid stay black so the sides do not glow
  - a quarter arc of 16 pinholes (1.5 mm, every 6 degrees from 0 to 90, +X side, upper half) in each face plate just outside the
    window, with a small LED on a thin flex arc behind each hole: the lit hole is today's peak elevation
  - an ambient light sensor in the base looking out through a 3 mm hole in the base wall, to dim the glow with the room
The frame electronics drive both LED runs from one RP2040 data pin (strip first, then the two peak arcs in the same chain).
Colour and brightness come from the sun's elevation, sent by the base over the serial link. Estimated LED draw is about 0.4 A at
5 V in twilight and about 1 A in full daylight white for 20 + 32 LEDs, so cap the daytime brightness.

Usage (from the repo root):
  python3 cad/src/sun_dial_glow.py [--az DEG] [--el DEG] [--up y|z] [--check]
Writes cad/out/sun-dial/sun-dial-glow/, bom/bom-sun-dial-glow.csv and previews in cad/media/previews/sun-dial-glow/.
"""
import argparse
import csv
import math
from pathlib import Path

import cadquery as cq

import sun_dial_small as sd

CAD = sd.CAD
OUTD = CAD / "out" / "sun-dial" / "sun-dial-glow"
IMG = CAD / "media" / "previews" / "sun-dial-glow"
BOMF = CAD.parent / "bom" / "bom-sun-dial-glow.csv"

# ---- light parameters (mm, frame-local: axis +Z, up +Y, the sun side is +X)
PEAK_N, PEAK_STEP = 16, 6.0                    # pinholes every 6 degrees, 0 to 90
PEAK_R = sd.WIN_R + 4.5                        # 55.5: just outside the window, inside the frame edge (60)
HOLE_R = 0.75                                  # 1.5 mm pinholes
INT, FT = sd.INT, sd.FT
STRIP_W, STRIP_T = 10.0, 2.0                   # RGBW strip 10 mm wide, about 2 mm with the LEDs
WALL_IN = sd.S / 2 - FT                        # 57: inner face of the frame walls
SENSE_X, SENSE_Z = -12.0, 12.0                 # ambient sensor window in the base wall
LED_C, FLEX_C = "#f1c40f", "#8e6f3e"


def peak_pts():
    return [(PEAK_R * math.cos(math.radians(i * PEAK_STEP)), PEAK_R * math.sin(math.radians(i * PEAK_STEP))) for i in range(PEAK_N)]


# ---- frame pieces with the pinhole arcs (the base script calls these by name, so patch them in)
_tub, _lid = sd.frame_tub, sd.frame_lid


def tub_with_holes():
    t = _tub()
    for x, y in peak_pts():
        t = t.cut(sd.cylz(HOLE_R, INT - 1, INT + FT + 1, x, y))
    return t


def lid_with_holes():
    t = _lid()
    for x, y in peak_pts():
        t = t.cut(sd.cylz(HOLE_R, -INT - FT - 1, -INT + 1, x, y))
    return t


sd.frame_tub, sd.frame_lid = tub_with_holes, lid_with_holes


def peak_arc(sgn):
    """Thin flex arc with 16 small LEDs facing the pinholes, just inside the face plate (sgn +1 front, -1 back)."""
    pts = [(math.radians(a)) for a in range(-2, 93, 2)]
    outer = [((PEAK_R + 1.2) * math.cos(a), (PEAK_R + 1.2) * math.sin(a)) for a in pts]
    inner = [((PEAK_R - 1.2) * math.cos(a), (PEAK_R - 1.2) * math.sin(a)) for a in reversed(pts)]
    z0, z1 = (INT - 1.8, INT - 1.0) if sgn > 0 else (-INT + 1.0, -INT + 1.8)
    flex = cq.Workplane("XY").workplane(offset=z0).polyline(outer + inner).close().extrude(z1 - z0)
    lz0, lz1 = (z1, z1 + 0.8) if sgn > 0 else (z0 - 0.8, z0)
    leds = None
    for x, y in peak_pts():
        b = sd.box(x - 1.0, x + 1.0, y - 1.0, y + 1.0, lz0, lz1)
        leds = b if leds is None else leds.union(b)
    return flex, leds


def build():
    sd.PRINT_DISCS = False
    sd.DISC_C = "#f1ece0"                      # opal
    sd.build()
    W = sd.W
    # opal discs are the laser parts; keep their names but note them in the BOM
    # perimeter strip: left, top, right inner walls at mid-depth, LEDs facing the axis
    z0, z1 = -STRIP_W / 2, STRIP_W / 2
    sd.add("led_strip_top", W(sd.box(-WALL_IN, WALL_IN, WALL_IN - STRIP_T, WALL_IN, z0, z1)), LED_C, "yaw")
    sd.add("led_strip_left", W(sd.box(-WALL_IN, -WALL_IN + STRIP_T, -45.0, WALL_IN - STRIP_T, z0, z1)), LED_C, "yaw")
    sd.add("led_strip_right", W(sd.box(WALL_IN - STRIP_T, WALL_IN, -45.0, WALL_IN - STRIP_T, z0, z1)), LED_C, "yaw")
    for sgn, nm in ((1, "front"), (-1, "back")):
        flex, leds = peak_arc(sgn)
        sd.add(f"led_peak_flex_{nm}", W(flex), FLEX_C, "yaw")
        sd.add(f"led_peak_leds_{nm}", W(leds), LED_C, "yaw")
    # ambient light sensor looking out of the base wall (+Y side)
    for i, (nm, s, c, g) in enumerate(sd.PARTS_L):
        if nm == "base_shell":
            sd.PARTS_L[i] = (nm, s.cut(sd._shape(sd.cyly(1.5, 60.0, 72.0, SENSE_X, SENSE_Z))), c, g)
    sd.add("light_sensor_keepout", sd.box(SENSE_X - 3, SENSE_X + 3, 62.0, 65.0, SENSE_Z - 3, SENSE_Z + 3), sd.KEEP_C)


def write_bom():
    rows = [
        ("laser", f"Opal (milk-white) cast acrylic 3 mm: disc {sd.DISC_D:.0f} mm with a {sd.SLOT_W:.0f} mm radial slot", 2, "own cutter; about half the light passes"),
        ("laser", f"Black acrylic 3 mm: strip {sd.SLOT_W:.0f} x {sd.DISC_D / 2:.0f}, pressed into the slot", 2, "own cutter"),
        ("print", "PETG-CF: hub 2", 1, ""),
        ("print", "PETG-CF black: frame tub and lid (with 16 pinholes each), arm and tray; keep them opaque so the sides do not glow", 3, "Bambu P1S, hardened nozzle"),
        ("print", "PETG-CF: turntable (5 mm), base shell with the cable spool (140 mm, USB-C slot, 3 mm sensor window), az adapter, elevation adapter", 4, "Bambu P1S, hardened nozzle"),
        ("buy", "RGBW addressable LED strip (SK6812 RGBW), 10 mm wide, about 60 per metre: three runs of about 114 mm, 100 mm and 100 mm", 1, "about 20 LEDs, LEDs facing in"),
        ("buy", "Small flex PCB arc or hand-wired 2 x 2 mm RGB LEDs: 16 per face on a 55.5 mm radius, every 6 degrees from 0 to 90", 2, "32 LEDs, one data chain with the strip; check the minimum bend radius"),
        ("buy", "Ambient light sensor breakout (VEML7700 or TEMT6000), about 6 x 6 mm", 1, "in the base behind the 3 mm wall hole; I2C on the ESP32"),
        ("buy", "Matt white paint for the frame interior (no thickness modelled), black masking for the pinholes if needed", 1, "diffuse reflector"),
        ("buy", "Thin silicone wire, 4 cores (12 V, 5 V, ground, serial), about 400 mm", 1, "winds round the spool; LED data shares the serial wire pair via the RP2040, no extra core"),
        ("buy", "iPower GM2804 gimbal motor with AS5048A encoder (35 x 26.15 mm)", 2, "elevation and azimuth; confirm torque and screw size"),
        ("buy", "SimpleFOC Mini driver (26.1 x 21 x 7.6 mm)", 2, "one in the base, one in the frame"),
        ("buy", "XIAO ESP32-S3 (base) and XIAO RP2040 (frame)", 2, "ESP32 supplied"),
        ("buy", "Compass module about 12 mm square, small RTC clock breakout, USB-C PD 12 V trigger board with socket, buck converter to 5 V (size for about 1 A on the LEDs)", 4, "sizes are placeholders"),
        ("buy", "Steel rod 3 mm, 35 mm long (posts) and steel pin 6 mm, 20 mm long", 3, "cut from bars"),
        ("buy", "M3 heat-set inserts x12 (4 tub corners, 4 turntable, 4 az adapter), M3 screws, M2 screws, grub screws, thread-lock, acrylic cement or CA glue for hubs", 1, "fasteners not modelled"),
    ]
    BOMF.parent.mkdir(exist_ok=True)
    with open(BOMF, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["process", "item", "qty", "note"])
        w.writerows(rows)
    print("Wrote", BOMF)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--az", type=float, default=90.0)
    ap.add_argument("--el", type=float, default=0.0)
    ap.add_argument("--up", choices=("y", "z"), default="y")
    ap.add_argument("--check", action="store_true", help="run interference checks, no export")
    a = ap.parse_args()
    sd.OUTD, sd.PARTS, sd.IMG, sd.BOMF = OUTD, OUTD / "parts", IMG, BOMF
    build()
    print(f"Light: {PEAK_N} pinholes per face every {PEAK_STEP:.0f} deg at r {PEAK_R:.1f}, strip on three walls, sensor window in the base wall")

    if a.check:
        movers = {n for n, _, _, g in sd.PARTS_L if g == "el"}
        total = 0
        for el, az in ((0, 90), (60, 135), (-90, 200), (90, 20)):
            bad = sd.clashes(sd.posed(az, el), only_with=movers)
            total += len(bad)
            if bad:
                print(f"az {az} el {el}: {len(bad)} clashes", bad[:8])
        print("total clashes in the moving checks:", total)
        static = sd.clashes(sd.posed(90, 0))
        print("static clashes:", len(static), static[:12])
        return

    OUTD.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    sd.export_parts(a.up == "y")
    write_bom()
    sd.assemble(a.az, a.el, a.up == "y").save(str(OUTD / "sun-dial-glow-assembly.step"))
    print("Wrote", OUTD / "sun-dial-glow-assembly.step")
    P = sd.posed(a.az, a.el)
    sd.render(P, IMG / "overview.png", [(14, -58, "Sun dial with light, 3/4 view"), (4, -90, "Front")])
    sd.render(P, IMG / "section.png", [(0, 0, "Section through the axis, x > 0 removed")], cut=(0, 400, -400, 400, -10, 400), zoom=1.4)
    sd.render(P, IMG / "light-inside.png", [(0, -90, "Frame lit parts, front face and discs hidden")],
              hide=("disc_", "strip_black", "frame_tub", "post_", "adapter_hub", "hub2"), box_=(-75, 75, -75, 75, sd.ZC - 70, sd.ZC + 70), zoom=1.5)
    print("Wrote previews to", IMG)


if __name__ == "__main__":
    main()
