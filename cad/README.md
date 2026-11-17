# cad

```
src/      CadQuery and matplotlib scripts (run from the repo root, e.g. python3 cad/src/hinge_mirror.py)
out/          (2026-11-16 tidy: one folder per project, older versions in an archive/ inside it)
  sun-dial/             sun-dial-glow/ (small dial with light) and sun-dial-small/ are the latest; archive/ holds sun-dial-one (150 mm, slip ring) and gm2804-dials (two-dial plate)
  spinning-mirror/      spinning-mirror-150-nema17/ and spinning-mirror-150-nema17-trio/ are the main ones; archive/ holds the GM2804 versions (single, test rig, trio, row of 7)
  hinge-mirror/         assembly/ (hinge-mirror-assembly.step, open in Fusion), parts/ (one STEP per part: print/ for the P1S, laser/ for flat parts with DXF cut outlines and *_engrave.dxf locating pockets, purchase/ reference shapes), archive/ (v1 exposed, test rig)
  earlier-concepts/     finger-pointer, line-mirrors, sun-pointer, wall-mirror
media/    pictures and video, in subfolders:
              animations/   sun-tracking videos (MP4) by mirror: square-mirror/ (the design), round-mirror/ (150 mm disc on clear panel), hole-mirror/ (20 mm hole, white table, shadows); gif-drafts/ older GIFs
              previews/     renders of the current model
              earlier-concepts/   to-scale drawings of earlier layouts (goalpost, pedestal, disc head, v1 exposed hinge)
              test-rig/     test joint rig drawings
```
Scripts for the current design: `hinge_mirror.py` (model, STEP, DXF, previews, `--check`), `make_bom.py` (BOM from the model), `animate.py` and `sun_day.py` (GIFs), `sun_seasons.py` (MP4s). The rest in `src/` are earlier concepts.

Current design: `src/hinge_mirror.py` writes `out/hinge-mirror/assembly/hinge-mirror-assembly.step`. Earlier layouts (goal post, pedestal, exposed-hinge v1, test rig) are kept for reference. Needs `pip install cadquery matplotlib`. Details: `../docs/cad-brief.md`.

Wall mirror concept (2026-11-04): `src/wall_mirror_nema11.py` writes `out/earlier-concepts/wall-mirror/wall-mirror-nema11.step` and renders to `media/previews/wall-mirror/`; notes in `../docs/wall-mirror-nema11.md`.

Line of 7 wall mirrors, passive and wedge versions (2026-11-04): `src/line_mirrors.py` writes `out/earlier-concepts/line-mirrors/*.step` and renders to `media/previews/line-mirrors/`; `--check` runs clash and Sun-view ray checks; notes in `../docs/line-mirrors.md`.

Sun pointer bead (2026-11-12): `src/sun_pointer_bead.py` writes `out/earlier-concepts/sun-pointer/sun-pointer-bead.step` and renders to `media/previews/sun-pointer/`; `--check` tests the tip against the sun formulas and sweeps spin and tilt for clashes; notes in `../docs/sun-pointer-bead.md`; the interactive concept is `../docs/sun-ring-concept.html`.

Finger pointer (2026-11-13): `src/finger_pointer.py` writes `out/earlier-concepts/finger-pointer/` (assembly STEP, parts split laser/print/purchase with DXF and engraving PNGs) and `../bom/bom-finger-pointer.csv`, previews in `media/previews/finger-pointer/`; `src/trace_finger.py` traces the hand outline from `src/assets/finger-source.jpg`; `--check` runs interference tests; notes in `../docs/finger-pointer.md`.

Spinning mirror gimbal (2026-11-14): `src/spinning_mirror.py` writes `out/spinning-mirror/archive/spinning-mirror/` (assembly STEP, parts split print/purchase) and `../bom/bom-spinning-mirror.csv`, previews in `media/previews/spinning-mirror/`; `--check` sweeps the mirror tilt for clashes; notes in `../docs/spinning-mirror-gimbal.md`, concept page `../docs/spinning-mirror-gimbal-concept.html`.

Spinning mirror row of 7 (2026-11-14): `src/spinning_mirror_row.py` writes `out/spinning-mirror/archive/spinning-mirror-row/` (assembly STEP, parts split laser/print/purchase with DXF) and `../bom/bom-spinning-mirror-row.csv`, carbon-tube top bar on steel rod posts with two thin blades; previews in `media/previews/spinning-mirror-row/`; `--check` runs random-pose clash checks; notes in `../docs/spinning-mirror-row.md`.

Single mirror test rig (2026-11-14): `python3 src/spinning_mirror_row.py --units 1` writes `out/spinning-mirror/archive/spinning-mirror-test/` and `../bom/bom-spinning-mirror-test.csv`, previews in `media/previews/spinning-mirror-test/`; same top support as the row on a 220 mm base; notes at the end of `../docs/spinning-mirror-row.md`.

Spinning mirror trio (2026-11-14): the unit is now an 80 mm mirror on the real iPower GM2804 + AS5048A motor (STEP in `src/assets/`). `python3 src/spinning_mirror_row.py --units 3` writes `out/spinning-mirror/archive/spinning-mirror-trio/`, `../bom/bom-spinning-mirror-trio.csv` and previews in `media/previews/spinning-mirror-trio/`; `--units 1` and `--units 7` rebuild the test rig and the row with the new unit.

Spinning mirror control deck (2026-11-15): the rigs now sit on a plywood box with a deck level with the hub tops (electronics inside, jitter knob, DC jack and USB cut-outs), 170 mm wide, printed parts matt black; see `../docs/spinning-mirror-row.md`.

Spinning mirror hood (2026-11-15): 5 mm clear acrylic cover on the base top layer, front ledge with a printed control pod (dial, DC jack, USB-C) and a reed-switch interlock; see `../docs/spinning-mirror-row.md`.

Spinning mirror 150 mm NEMA 17 test rig (2026-11-15): `python3 src/spinning_mirror_150_nema17.py` writes `out/spinning-mirror/spinning-mirror-150-nema17/`, `../bom/bom-spinning-mirror-150-nema17.csv` and previews in `media/previews/spinning-mirror-150-nema17/`; `--check` runs the tilt-sweep clash check. Single unit on a printed pedestal, no top bar, box or hood; notes in `../docs/spinning-mirror-150-nema17.md`.

Spinning mirror 150 mm NEMA 17 trio (2026-11-15), now the primary route: `python3 src/spinning_mirror_150_nema17_trio.py` (`--check` for clashes) writes `out/spinning-mirror/spinning-mirror-150-nema17-trio/`, `../bom/bom-spinning-mirror-150-nema17-trio.csv` and previews in `media/previews/spinning-mirror-150-nema17-trio/`: three 150 mm units on a laser-cut plywood box with the motors hanging under the deck. No hood or top bar yet. The brushless GM2804 versions above are the alternative.

Sun dial with light (2026-11-16): `python3 src/sun_dial_glow.py` (`--check` for clashes) builds on `sun_dial_small.py` and writes `out/sun-dial/sun-dial-glow/`, `../bom/bom-sun-dial-glow.csv` and previews in `media/previews/sun-dial-glow/`: opal discs, perimeter LED strip, pinhole peak-elevation arcs, ambient sensor; notes in `../docs/sun-dial-glow.md`, behaviour in `../sim/sun-dial-glow.html`.

Wall-mounted piece, 3 rows of eight 50 mm mirrors with one NEMA 17 per row (2026-11-17): `python3 src/spinning_mirror_wall_row_50.py` (`--check` for clashes) writes `out/spinning-mirror/spinning-mirror-wall-row-50/` (assembly STEP, `parts/print`, `parts/print_ready`, `parts/purchase`), `../bom/bom-spinning-mirror-wall-row-50.csv` and previews in `media/previews/spinning-mirror-wall-row-50/`: a 2020 rail per row on three printed wall standoffs, sliding printed bearing blocks, double-head GT2 pulleys chained by eight 200 mm belt loops per row, glass mirrors on a free hinge, and an electronics box under the bottom rail. See `docs/spinning-mirror-wall-row-50.md`.

Alternative, one row of ten (2026-11-17): `python3 src/spinning_mirror_wall_row_50.py --single10` writes `out/spinning-mirror/spinning-mirror-wall-row-50-single10/`, `../bom/bom-spinning-mirror-wall-row-50-single10.csv` and previews in `media/previews/spinning-mirror-wall-row-50-single10/`: one 850 mm rail, ten units, one NEMA 17, three printed wall standoffs. See `docs/spinning-mirror-wall-row-50-single10.md`.

100 mm version (2026-11-17): `python3 src/spinning_mirror_wall_row_50.py --mirror100` writes `out/spinning-mirror/spinning-mirror-wall-row-100/`, `../bom/bom-spinning-mirror-wall-row-100.csv` and previews in `media/previews/spinning-mirror-wall-row-100/`: eight 100 mm acrylic mirrors on one 1150 mm rail with a NEMA 17 at each end driving four, held by screwless push-and-twist printed bezels, 8 mm spindles on 608ZZ, 140 mm pitch. See `docs/spinning-mirror-wall-row-100.md`. The 100 mm and 150 mm carriers now have a 4.15 mm axle bore with a teardrop roof and a 6 mm thickness (100 mm: 6 mm too). This change also fixed the 50 mm unit's hinge bearing size (683ZZ, not the 150 mm unit's 684ZZ).
