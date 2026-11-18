# Sun dial with light (2026-11-16)

The smallest dial (`docs/sun-dial-small.md`) with the glow from `sim/sun-dials/sun-dial-glow.html`: translucent discs lit from inside, colour and brightness following the sun's elevation, and a lit pinhole marking the day's peak. Draft CAD, nothing printed or tested. Source of truth: `cad/src/sun_dial_glow.py`, which imports `sun_dial_small.py` and adds the light, so frame, motors, base and turntable are unchanged.

## What was added
- **Discs:** opal (milk-white) 3 mm cast acrylic, laser cut, black strip pressed in (the `--discs laser` variant of the small dial, hub 2 printed). About half the light passes.
- **Light box:** a 10 mm RGBW addressable strip on three inner walls (left, top, right), LEDs facing in, at mid-depth. The floor side is left clear for the tray and boards. The inside is painted matt white (not modelled) so the cavity diffuses the light onto both discs. Tub and lid stay black and opaque so the sides do not glow.
- **Peak indicator:** 16 pinholes (1.5 mm) every 6 degrees from 0 to 90 on the +X, upper side of each face plate, 55.5 mm from the axis, just outside the window. Behind each face a thin flex arc carries 16 small LEDs aimed at the holes. Firmware lights the hole nearest today's peak (blending the two nearest) or fills a trail up to it.
- **Light sensor:** a small ambient sensor in the base behind a 3 mm hole in the +Y wall, so the glow can dim with the room.
- **Wiring:** one RP2040 data pin drives the strip and both arcs in one chain. No extra cable core.

## Checks run
- `python3 cad/src/sun_dial_glow.py --check`: 0 clashes at four az/el pairs including el +/-90, 0 static clashes.
- Not checked: light level and evenness, how visible the motor and hub shadows are through the opal, strip and flex bend radius, current at full white, heat, whether the pinhole LEDs line up behind the holes in practice.

## Things to know or decide
1. **Current.** About 20 strip LEDs plus 32 peak LEDs. Twilight is about 0.4 A at 5 V, full daylight white would be about 1 A or more, so cap the daytime brightness and check the buck converter and the thin cable wires.
2. **Motor shadow.** The motor sits behind disc 1 and close to disc 2, so expect a faint dark patch. If it bothers you, the next step is edge-lit discs, which need clear acrylic with etched faces and tiny side-emitting LEDs.
3. **Peak arc LEDs.** A normal strip will not bend edgewise on a 55.5 mm radius; use a small flex PCB or hand-wired 2 mm LEDs. The pinhole spacing is a trade-off between resolution and LED count.
4. **Halo.** The 1 mm gap round each disc will glow a little; mask it if unwanted.
5. **Not modelled:** white paint, wiring, standoffs, the sensor board detail, the data connections.

## Regenerating
```
python3 cad/src/sun_dial_glow.py            # STEP, parts, BOM, previews (add --az 135 --el 30 to pose)
python3 cad/src/sun_dial_glow.py --check
```
Outputs: `cad/out/sun-dial/sun-dial-glow/`, `bom/bom-sun-dial-glow.csv`, `cad/media/previews/sun-dial-glow/`.
