# Sun dial with light: wiring pass

Draft, nothing built or tested. Covers `cad/src/sun_dial_glow.py` (the glow variant of the smallest dial).
Regenerate the CAD with `python3 cad/src/sun_dial_glow.py`; check with `--check`.

## What changed in the CAD

- Cable spool: bottom flange (r 30) and top flange (r 24) added, motor-lead slot kept, one layer of cable fits.
- Tie points: two slots through the base floor (with a strap groove underneath) at the fixed cable end, and two slots through the frame floor and tray (groove under the tub) at the frame end.
- Peak LEDs: pinhole radius moved from 55.5 to 54.5 mm so a printed carrier (`peak_carrier_front/back`, 2 mm) fits inside the 57 mm wall. It holds the 16 LEDs in pockets, with light wells to the pinholes so neighbours do not leak.
- Keep-outs added: frame hub board, frame 12 to 5 V buck, lid 3-pin plug, base cable plug.
- 0 clashes in the moving checks and 0 static.

## Power

| Rail | Source | Goes to |
|---|---|---|
| 12 V | USB-C PD board, base | azimuth driver, cable core 1, elevation driver (frame), frame buck |
| 5 V base | small buck in the base | XIAO ESP32-S3, sensors |
| 5 V frame | buck on the frame tray | XIAO RP2040, LED strip, both peak arcs |
| 3.3 V | each XIAO | encoder, logic |

Only 12 V, ground and one data wire cross the rotation. Estimated draw in the frame: LEDs up to 5 W (1 A at 5 V), elevation motor and driver about 3 W, RP2040 0.5 W: about 0.8 A at 12 V in full daylight white. 24 AWG is fine; cap the daytime LED brightness anyway so the PD supply (20 W) and buck are not stressed.

Frame hub board (about 18 x 11 mm perfboard): cable plug, 1000 uF across the 5 V LED feed, 330 ohm in the data line, 74AHCT1G125 to take the RP2040 3.3 V data up to the 5 V the SK6812 needs.

## Cable (the rotation solution)

4-core 24 AWG silicone, about 3.5 mm, about 300 mm long.

| Core | Use |
|---|---|
| 1 | 12 V |
| 2 | ground |
| 3 | serial, base TX to frame RX (3.3 V) |
| 4 | spare |

- It leaves the base at a tie point on the spool flange (-Y side), winds one layer on the spool, rises to the 10 mm turntable hole 30 mm from the axis, passes down through the frame floor and is tied to the tray.
- Travel is about +/-150 degrees. The wrap length swings by about 21.75 mm x 5.24 rad = 114 mm over the full travel, which is 0.83 turn on a 22.75 mm radius, so one layer is enough.
- The absolute encoder on the azimuth motor always knows the wrap, so firmware can hold the limit even after a power cycle.
- Plugs: 4-pin JST-XH at both ends. Not yet checked: fatigue life of silicone wire on a 22 mm radius (flex test needed), and a mechanical hard stop (currently only firmware).

## Pin maps

XIAO ESP32-S3, base (all 11 header pins used):

| Pin | Function |
|---|---|
| D0, D1, D2 | azimuth driver PWM A, B, C |
| D3 | azimuth driver enable |
| D4, D5 | I2C SDA, SCL: compass, RTC, light sensor |
| D6 | UART TX to frame |
| D7 | azimuth encoder CS |
| D8, D9, D10 | encoder SPI SCK, MISO, MOSI |

XIAO RP2040, frame (10 of 11 used):

| Pin | Function |
|---|---|
| D0, D1, D2 | elevation driver PWM A, B, C |
| D3 | elevation driver enable |
| D4 | elevation encoder CS |
| D5 | spare |
| D6 | LED data out (via the level shifter) |
| D7 | UART RX from base |
| D8, D9, D10 | encoder SPI SCK, MISO, MOSI |

## LED data chain (one pin)

Left strip (bottom to top), top strip (left to right), right strip (top to bottom), then the front peak arc (0 to 90 degrees, LED 0 to 15), then through the lid plug to the back peak arc (90 to 0 degrees, so LED index 15 is first, 0 last). About 52 LEDs in total; the firmware must reverse the back-arc index. Each run needs 5 V and ground in parallel, not only the data.

## Open questions and risks

- Peak arcs: 16 hand-wired 2 x 2 mm LEDs per face (3 joints each) or a small flex PCB (design in KiCad, order from a flex PCB maker). The flex PCB is better but is a separate job.
- Compass 58 mm from the azimuth motor magnets can read wrongly. Use it for the start-up north only with the motor free, or drop it and set north by hand.
- No board outlines are real yet. Check the keep-outs once the boards are in hand.
- Strap grooves are under the tub and base, and the printed strap slots have not been tried.
- Elevation head can be test-printed now; the base shell and turntable should be printed after the cable has been flex-tested on the spool.
