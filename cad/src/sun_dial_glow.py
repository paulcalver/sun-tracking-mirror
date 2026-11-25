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
Writes cad/out/sun-dial/sun-dial-glow/, bom/sun-dials/bom-sun-dial-glow.csv and previews in cad/media/previews/sun-dial-glow/.
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
BOMF = CAD.parent / "bom" / "sun-dials" / "bom-sun-dial-glow.csv"

# ---- light parameters (mm, frame-local: axis +Z, up +Y, the sun side is +X)
PEAK_N, PEAK_STEP = 16, 6.0                    # pinholes every 6 degrees, 0 to 90
PEAK_R = sd.WIN_R + 3.5                        # 54.5: just outside the window; the carrier band (+/-1.8) stays inside the 57 mm inner wall
HOLE_R = 0.75                                  # 1.5 mm pinholes
INT, FT = sd.INT, sd.FT
STRIP_W, STRIP_T = 10.0, 2.0                   # RGBW strip 10 mm wide, about 2 mm with the LEDs
WALL_IN = sd.S / 2 - FT                        # 57: inner face of the frame walls
SENSE_X, SENSE_Z = -12.0, 12.0                 # ambient sensor window in the base wall
LED_C, FLEX_C = "#f1c40f", "#8e6f3e"


# ---- cable and wiring parameters
CABLE_D = 3.5                                  # 4-core 24 AWG silicone cable, about 3.5 mm
FLANGE_R = 30.0                                # spool flanges (the base boards stay outside r 37)
TIE_X = ((-34.1, -32.5), (-27.5, -25.9))       # frame-side cable-tie slots, either side of the cable lying along -Z from the hole
TIE_Z = (-10.1, -6.9)
BASE_TIE_X = ((-4.2, -2.6), (2.6, 4.2))        # base-side tie slots either side of the cable lying along -Y from the spool
BASE_TIE_Y = (-29.0, -25.8)


def peak_pts():
    return [(PEAK_R * math.cos(math.radians(i * PEAK_STEP)), PEAK_R * math.sin(math.radians(i * PEAK_STEP))) for i in range(PEAK_N)]


# ---- frame pieces with the pinhole arcs (the base script calls these by name, so patch them in)
_tub, _lid = sd.frame_tub, sd.frame_lid


def tub_with_holes():
    t = _tub()
    for x0, x1 in TIE_X:                                                       # cable-tie slots through the floor
        t = t.cut(sd.box(x0, x1, -sd.S / 2 - 1, -sd.S / 2 + FT + 1, TIE_Z[0], TIE_Z[1]))
    t = t.cut(sd.box(TIE_X[0][0], TIE_X[1][1], -sd.S / 2 - 0.1, -sd.S / 2 + 1.5, TIE_Z[0], TIE_Z[1]))   # groove for the strap on the underside
    for x, y in peak_pts():
        t = t.cut(sd.cylz(HOLE_R, INT - 1, INT + FT + 1, x, y))
    return t


def lid_with_holes():
    t = _lid()
    for x, y in peak_pts():
        t = t.cut(sd.cylz(HOLE_R, -INT - FT - 1, -INT + 1, x, y))
    return t


sd.frame_tub, sd.frame_lid = tub_with_holes, lid_with_holes


def arc_band(r0, r1, z0, z1, a0=-3, a1=93, step=3):
    ang = [math.radians(a) for a in range(a0, a1 + 1, step)]
    outer = [(r1 * math.cos(a), r1 * math.sin(a)) for a in ang]
    inner = [(r0 * math.cos(a), r0 * math.sin(a)) for a in reversed(ang)]
    return cq.Workplane("XY").workplane(offset=z0).polyline(outer + inner).close().extrude(z1 - z0)


def peak_arc(sgn):
    """Flex arc with 16 small LEDs, and the printed carrier that holds them against the face plate (sgn +1 front, -1 back).
    Distances d are measured inward from the inner face of the face plate: carrier d 0..2, LEDs d 1.2..2.0, flex d 2.0..2.8."""
    zb = INT if sgn > 0 else -INT

    def zi(d0, d1):
        a, b = zb - sgn * d0, zb - sgn * d1
        return min(a, b), max(a, b)

    flex = arc_band(PEAK_R - 1.2, PEAK_R + 1.2, *zi(2.0, 2.8))
    car = arc_band(PEAK_R - 1.8, PEAK_R + 1.8, *zi(0.0, 2.0))
    leds = None
    for i, (x, y) in enumerate(peak_pts()):
        z0, z1 = zi(1.2, 2.0)
        led = sd.box(-1.0, 1.0, -1.0, 1.0, z0, z1).rotate((0, 0, 0), (0, 0, 1), i * PEAK_STEP).translate((x, y, 0))
        leds = led if leds is None else leds.union(led)
        z0, z1 = zi(1.0, 2.2)                                   # LED pocket, open at the back of the carrier
        pocket = sd.box(-1.1, 1.1, -1.1, 1.1, z0, z1).rotate((0, 0, 0), (0, 0, 1), i * PEAK_STEP).translate((x, y, 0))
        z0, z1 = zi(-0.2, 1.0)                                  # light well through to the pinhole
        car = car.cut(pocket).cut(sd.cylz(0.9, z0, z1, x, y))
    return flex, leds, car


def rework_spool_and_tray():
    """Cable spool flanges, base tie slots, frame tie slots on the tray."""
    ys0, ys1 = BASE_TIE_Y
    for i, (nm, sh, c, g) in enumerate(sd.PARTS_L):
        if nm == "base_shell":
            lo = sd.cylz(FLANGE_R, sd.BASE_FLOOR - 0.5, sd.BASE_FLOOR + 2.0).cut(sd.cylz(sd.SPOOL_RI, sd.BASE_FLOOR - 1, sd.BASE_FLOOR + 3))                                     # bottom flange
            hi = sd.cylz(24.0, 28.0, sd.SPOOL_Z1).cut(sd.cylz(sd.SPOOL_RI, 27.0, sd.SPOOL_Z1 + 1))                 # top flange, clear of the az adapter (r 25, z 32.15 up)
            sh = sh.fuse(sd._shape(lo)).fuse(sd._shape(hi))
            sh = sh.cut(sd._shape(sd.box(sd.SPOOL_RO - 3, FLANGE_R + 1, -3, 3, sd.BASE_FLOOR - 1, sd.BASE_FLOOR + 6)))   # motor-lead slot through the flange
            for x0, x1 in BASE_TIE_X:
                sh = sh.cut(sd._shape(sd.box(x0, x1, ys0, ys1, -1.0, sd.BASE_FLOOR + 3.0)))
            sh = sh.cut(sd._shape(sd.box(BASE_TIE_X[0][0], BASE_TIE_X[1][1], ys0, ys1, -0.1, 1.5)))              # strap groove under the base
            sd.PARTS_L[i] = (nm, sh, c, g)
        if nm == "arm_tray":
            for x0, x1 in TIE_X:
                sh = sh.cut(sd._shape(sd.box(x0, x1, -sd.S / 2 + FT - 1, -sd.S / 2 + FT + 3, TIE_Z[0], TIE_Z[1])))
            sd.PARTS_L[i] = (nm, sh, c, g)


def build():
    sd.PRINT = sd.PRINT + ("peak_carrier",)
    sd.PRINT_ROT.update({"peak_carrier_front": 0, "peak_carrier_back": 0})
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
        flex, leds, car = peak_arc(sgn)
        sd.add(f"led_peak_flex_{nm}", W(flex), FLEX_C, "yaw")
        sd.add(f"led_peak_leds_{nm}", W(leds), LED_C, "yaw")
        sd.add(f"peak_carrier_{nm}", W(car), "#2b2b2b", "yaw")
    rework_spool_and_tray()
    yf = -(sd.S / 2 - FT)
    sd.add("frame_hub_keepout", W(sd.box(-24, -5.5, yf + 2.0, yf + 11.0, -17.5, -6.5)), sd.KEEP_C, "yaw")      # perfboard: cable plug, level shifter, caps, LED lead terminals
    sd.add("buck_5v_frame_keepout", W(sd.box(6, 21, yf + 2.0, yf + 7.0, -17.0, -7.0)), sd.KEEP_C, "yaw")     # 12 to 5 V buck for the LEDs and the RP2040
    sd.add("lid_plug_keepout", W(sd.box(-5, 5, 48.5, 53.0, -14.0, -6.0)), sd.KEEP_C, "yaw")                  # 3-pin plug for the back arc (lid comes off)
    sd.add("base_cable_plug_keepout", sd.box(-6, 6, -38.5, -31.5, sd.BASE_FLOOR + 3.0, sd.BASE_FLOOR + 10.0), sd.KEEP_C)
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
        ("print", "PETG-CF black: peak LED carrier arc, one per face (16 pockets and light wells, stops light leaking between holes)", 2, "glue to the inside of the face plate over the pinholes"),
        ("print", "PETG-CF: turntable (5 mm), base shell with the cable spool (140 mm, USB-C slot, 3 mm sensor window), az adapter, elevation adapter", 4, "Bambu P1S, hardened nozzle"),
        ("buy", "RGBW addressable LED strip (SK6812 RGBW), 10 mm wide, about 60 per metre: three runs of about 114 mm, 100 mm and 100 mm", 1, "about 20 LEDs, LEDs facing in"),
        ("buy", "Small flex PCB arc or hand-wired 2 x 2 mm RGB LEDs: 16 per face on a 55.5 mm radius, every 6 degrees from 0 to 90", 2, "32 LEDs, one data chain with the strip; check the minimum bend radius"),
        ("buy", "Ambient light sensor breakout (VEML7700 or TEMT6000), about 6 x 6 mm", 1, "in the base behind the 3 mm wall hole; I2C on the ESP32"),
        ("buy", "Matt white paint for the frame interior (no thickness modelled), black masking for the pinholes if needed", 1, "diffuse reflector"),
        ("buy", "Silicone cable, 4 cores 24 AWG, about 3.5 mm round: 12 V, ground, serial, one spare", 1, "about 300 mm; winds one layer round the spool, tied at both ends; 5 V is made in the frame"),
        ("buy", "Mini buck 12 V to 5 V, 2 A or more (frame), and a small 12 V to 5 V for the XIAO ESP32 (base)", 2, "frame one feeds the RP2040 and all LEDs"),
        ("buy", "74AHCT1G125 level shifter, 330 ohm resistor, 1000 uF 10 V capacitor, perfboard about 18 x 11 mm", 1, "LED data 3.3 V to 5 V, on the frame hub board"),
        ("buy", "JST-XH 4-pin plug and socket (cable at both ends), JST-SH or XH 3-pin plug (lid arc)", 3, "cable is removable at the frame, the lid comes off"),
        ("buy", "Cable ties 2.5 mm wide, 6 (2 per tie point and spare)", 1, "strain relief at the frame floor and the spool"),
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
