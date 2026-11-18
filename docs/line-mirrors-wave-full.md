# Wave version, full detail (concept CAD, 2026-11-04)

Status: concept model, nothing built or tested. Source: `cad/src/line_wave_full.py` (CadQuery, builds on `line_mirrors.py`). Parts list and BOM: [line-mirrors-wave-bom.md](../bom/archive/line-mirrors/line-mirrors-wave-bom.md) (`--bom`). STEP: `cad/out/earlier-concepts/line-mirrors/line-mirrors-wave-full.step` (`--step`). Renders: `cad/media/previews/line-mirrors/full-*.png` (`--render`; blue = laser cut, orange = 3D print, grey = bought or metal). Viewer animation: `cad/media/animations/line-wave-viewer.mp4` (`line_mirrors_anim.py`, earlier geometry, motion only).

## Layout
- Strip 824 x 96 x 62 mm, mirror row centred (177 mm from the outer mirror edges to each end).
- **Mirrors:** 7 x 50 mm glass on printed carriers; 2 mm rod with a 10 mm pivot ball sliding in the 8 mm front plate and a 6 mm tip ball held between two slotted lips (pan bar above, tab below).
- **Pan (X):** NEMA 17 at the left, GT2 belt to a tail on the pan bar. The pan bar runs between printed rails and is pushed against the rail caps by the balls.
- **Tilt (Y):** the tilt frame is a 20 x 10 aluminium bar with a printed end block (left) and bracket (right). A NEMA 17 at the right turns a cross shaft along the top through a short transfer belt; a vertical belt at each end of the frame lifts it. The frame slides on PTFE strips on the back plate.
- **Wave:** 5 mm D camshaft on the frame, 7 printed eccentric cams (1 mm throw, each printed with its bore turned 60 degrees), driven by a 28BYJ-48 geared stepper on the end block. Each cam lifts a POM tab; a spring over two tongues pushes the tab down onto its cam, and two printed flexure pads push it up against the tip ball.
- **Electronics:** Pico, 3 x TMC2209, RTC, buck converter, 12 V jack at the right end. Home switches: X at the right of the pan bar, Y at the top (the comb trips it).

## Review 2: problems found and fixed
1. **Tilt frame held at one end.** The Y belt clamped only the right end, and the two guide pins (in vertical slots) could not stop the frame swinging. The left end, with a 220 g NEMA 17 on it, was a 540 mm acrylic cantilever. Even held at both ends, the acrylic frame would sag about 40 mm. Now: aluminium backbone (sag 0.07 mm, constant) and belts at both ends on one cross shaft, so both ends move together.
2. **No preload on the tip balls.** The pan bar had 0.3 mm of float and the tabs had nothing behind them, so each tip could rattle about 0.65 mm (about 130 mm of spot movement at 3 m). Now: printed retainers behind the tabs with two flexure pads each (about 0.5 N), and the pan bar runs against its rail caps (0.05 mm, PTFE tape).
3. **Springs and tabs not located.** Springs now sit over a tongue on the tab and a tongue on the comb. Tabs are held in the comb windows (x), by the retainer (back) and by the ball (front).
4. **Cams had no phase reference** (glued on a round shaft). Now a 5 mm D shaft and D-bored cams, each printed at its 60 degree step. Cam radius 5 mm, wall 1.5 mm.
5. **NEMA 17 cam motor on the moving frame** was heavy, rubbed on the back plate and hit the bottom wall at the home position. Now a 28BYJ-48 (35 g, geared, slow) bolted to the end block.
6. **Thermal mismatch.** The stainless lip expands much less than the acrylic front plate (0.37 mm at the end mirrors for 30 K, about 75 mm of spot). Now a 0.5 mm PET lip (0.06 mm). The comb is fixed at the left and slides in a long pocket at the right; the cross shaft floats in its bearings. Carriers in PETG or ASA (PLA softens in sun).
7. **Front plate could not come off** with the carriers glued on. Carriers now have a hub with an M2 grub: slide the carriers off, remove 10 screws, lift the front plate over the pivot balls.
8. **Cams hit the bottom pan rail** at full tilt once the cams grew: rail guard ledges removed (the bar is held by the caps).
9. Small ones: left pin flange touched the end plate (pin moved 2 mm), PCB screw 0.08 mm from a driver (layout moved), X clamp 0.2 mm from its mount (now 0.5), X switch post 0.13 mm from a shaft block (raised), two wall-fixing holes would have been under the cross shaft (moved), Y motor upgraded to 42 x 40 (frame now about 0.5 kg).

## Checks (`--check`, `--sun`)
- 43 poses, all 240+ parts and 130 fasteners: tilt cone 0 and 25 degrees in 8 directions, cam angle varied, pan and tilt at their stops, home over-travel (X +14.3, Y +13.4): **0 clashes**.
- Near-contact scan: every pair under 0.6 mm is a designed touch or a stated clearance (rail caps 0.05, comb to pin 0.1, cam to pan bar 0.59, cam to retainer 0.93).
- Sun view, 1680 rays at 25, 50, 65 degrees: enclosure blocks 0.0 %; other mirrors 0 % up to 50 degrees, 4.8 % at 65.
- Numbers: Y motor load about 3.7 N cm (42 x 40 holds about 40); tab motion -0.96 to +1.05 mm; belts X 152, Y 2 x 186, transfer 124 mm.

## Assembly order (mirror unit)
Tip ball epoxied on the rod; tab, retainer and comb in place; rod through the pan bar slot from behind; pan bar into its rails; pivot ball slid onto the rod and set at 30 mm from the tip ball with a jig, epoxied; front plate on; carriers (with glass) slid on and the M2 grubs tightened.

## Still open
- Flexure pad preload depends on print accuracy: print the pads 0.3 mm proud and sand or shim.
- Y belts must be clamped so the frame is level: loosen one clamp, set the frame square to the rails, re-tighten.
- The tilt frame drops under gravity if the Y motor is unpowered (keep a holding current, or add a light counter-spring).
- Laser parts over 600 mm (back, walls, front, pan bar) need a large-bed service or a split.
- Wiring and the cable loop to the cam motor are not drawn; grub screws in pulleys and the coupler are not drawn.
- Weather: the pivot bores are open; indoors behind glass, or add a brush seal.
- Parallax and convergence trim still to do in firmware.
