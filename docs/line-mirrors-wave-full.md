# Wave version, full detail (concept CAD, 2026-11-04)

Status: concept model, nothing built or tested. Source: `cad/src/line_wave_full.py` (CadQuery, builds on `line_mirrors.py`). Parts list and BOM: [line-mirrors-wave-bom.md](line-mirrors-wave-bom.md) (`--bom`). STEP: `cad/out/line-mirrors/line-mirrors-wave-full.step` (`--step`). Renders: `cad/media/previews/line-mirrors/full-*.png` (`--render`, blue = laser cut, orange = 3D print, grey = bought). Viewer animation: `cad/media/animations/line-wave-viewer.mp4` (`line_mirrors_anim.py`).

## Even spacing
The strip is now symmetric: 824 x 96 x 62 mm, mirror row centred, 177 mm from the outer mirror edges to each end. The right 80 mm that was empty now holds the controller (Pico, 3 x TMC2209, RTC, buck converter, DC jack).

## What the full drawing added, and what it found wrong in the first wave model
- **Cam was impossible.** Cam radius 3.5 mm on a 5 mm shaft with 1 mm throw left a 0 mm wall. Now: 4 mm shaft, 9 mm cams, 1.5 mm minimum wall. That needed the tab layer lifted 2 mm (tip plane 29.2), so the cams clear the pan bar by 1.6 mm. The tab rests on the cam 1 mm above its axis, which shifts the wave phase equally for all seven and adds about 3 % amplitude.
- **Camshaft sagged.** A 5 mm rod supported at the ends only would bend about 2 mm under the tab springs (throw is 1 mm). Added 7 printed support blocks, one between each pair of mirrors.
- **Tab preload.** The mirror's weight pushes each tip up about 0.24 N, away from the cam. Added a spring per tab (about 1.2 N) and a comb that guides the tabs.
- **3 mm stem rod does not pass the 4.4 mm slot** when tilted 25 degrees in the pan direction (it touched with the 1 mm lip, and the old 0.8 mm lip hid it under the clash threshold). Now a 2 mm rod and a 0.5 mm stainless lip with a 1.5 mm relief layer above it.
- **Guides were missing.** Pan bar: two printed C rails (ledge, fence, cap) top and bottom. Tilt frame: two M4 guide pins in slots in the comb. Y home switch must trigger at 13.2 mm, because the cam motor body reaches the bottom wall at 13.9 mm.
- X belt clamp, motor mounts, tail from pan bar to belt, limit switches, controller and DC jack are now drawn.

## Checks (all in `--check`, `--sun`)
- 45 poses, all parts: tilt cone 0 and 25 degrees in 8 directions with cam at 0 to 330, pan and tilt at both stops, home over-travel (pan +14.3, tilt +/-13.2): **0 clashes** (threshold 0.5 mm3).
- Near-contact scan (neutral and four corner poses, cam 0 and 90): every pair closer than 0.6 mm is a stacked plate or a designed touch (ball in slot edge, pivot ball in bore). Loose clearances: comb to guide pin 0.1, pan bar to rails 0.3, motor to bottom wall 0.35.
- Sun view (1680 rays at 25, 50, 65 degrees off the wall axis): enclosure blocks 0.0 %, other mirrors block 0.0 % at 25 and 50 degrees, 4.8 % at 65.
- Cam wall 1.5 mm, belt loops 152 mm (X) and 148 mm (Y), tab spring 1.2 N against 0.24 N mirror torque.

## Not modelled or not decided
- Laser joints (T-slots, captive nuts), screws, wiring and the cable loop to the cam motor, glue joints.
- Laser cut size: the back plate, walls and front plate are 824 mm long. Needs a service with a bed of about 850 mm or a split. Pan bar blank is 588 mm.
- 0.5 mm stainless lip needs a fibre-laser service; a 2 mm acrylic lip can be tried only if the stem stays 2 mm and the cone is reduced.
- Spot at 3 m: parallax and convergence trim still not in firmware; the 0.3 mm tolerance of cams/ slots is hidden by the wave.
- Prices are estimates; Pi Hut NEMA 17 about 11 GBP ex VAT, GT2 pulleys about 2 to 5 GBP each, TMC2209 about 3 to 7 GBP were seen in UK listings.
- The animation uses the earlier wave geometry (2 mm lower); it is only a view of motion.
