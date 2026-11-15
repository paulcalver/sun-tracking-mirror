# cad

```
src/      CadQuery and matplotlib scripts (run from the repo root, e.g. python3 cad/src/hinge_mirror.py)
out/
  assembly/   hinge-mirror-assembly.step only (open in Fusion)
  parts/      one STEP per part, split to match the BOM:
              print/ (P1S), laser/ (flat parts to cut: STEP plus a DXF cut outline, and a *_engrave.dxf of the shallow locating pockets where parts glue in), purchase/ (reference shapes of bought parts, not for making)
  archive/    older versions: hinge-mirror v1 exposed, test rig
media/    pictures and video, in subfolders:
              animations/   sun-tracking videos (MP4) by mirror: square-mirror/ (the design), round-mirror/ (150 mm disc on clear panel), hole-mirror/ (20 mm hole, white table, shadows); gif-drafts/ older GIFs
              previews/     renders of the current model
              earlier-concepts/   to-scale drawings of earlier layouts (goalpost, pedestal, disc head, v1 exposed hinge)
              test-rig/     test joint rig drawings
```
Scripts for the current design: `hinge_mirror.py` (model, STEP, DXF, previews, `--check`), `make_bom.py` (BOM from the model), `animate.py` and `sun_day.py` (GIFs), `sun_seasons.py` (MP4s). The rest in `src/` are earlier concepts.

Current design: `src/hinge_mirror.py` writes `out/assembly/hinge-mirror-assembly.step`. Earlier layouts (goal post, pedestal, exposed-hinge v1, test rig) are kept for reference. Needs `pip install cadquery matplotlib`. Details: `../docs/cad-brief.md`.

Wall mirror concept (2026-11-04): `src/wall_mirror_nema11.py` writes `out/wall-mirror/wall-mirror-nema11.step` and renders to `media/previews/wall-mirror/`; notes in `../docs/wall-mirror-nema11.md`.

Line of 7 wall mirrors, passive and wedge versions (2026-11-04): `src/line_mirrors.py` writes `out/line-mirrors/*.step` and renders to `media/previews/line-mirrors/`; `--check` runs clash and Sun-view ray checks; notes in `../docs/line-mirrors.md`.

Sun pointer bead (2026-11-12): `src/sun_pointer_bead.py` writes `out/sun-pointer/sun-pointer-bead.step` and renders to `media/previews/sun-pointer/`; `--check` tests the tip against the sun formulas and sweeps spin and tilt for clashes; notes in `../docs/sun-pointer-bead.md`; the interactive concept is `../docs/sun-ring-concept.html`.

Finger pointer (2026-11-13): `src/finger_pointer.py` writes `out/finger-pointer/` (assembly STEP, parts split laser/print/purchase with DXF and engraving PNGs) and `../bom/bom-finger-pointer.csv`, previews in `media/previews/finger-pointer/`; `src/trace_finger.py` traces the hand outline from `src/assets/finger-source.jpg`; `--check` runs interference tests; notes in `../docs/finger-pointer.md`.

Spinning mirror gimbal (2026-11-14): `src/spinning_mirror.py` writes `out/spinning-mirror/` (assembly STEP, parts split print/purchase) and `../bom/bom-spinning-mirror.csv`, previews in `media/previews/spinning-mirror/`; `--check` sweeps the mirror tilt for clashes; notes in `../docs/spinning-mirror-gimbal.md`, concept page `../docs/spinning-mirror-gimbal-concept.html`.

Spinning mirror row of 7 (2026-11-14): `src/spinning_mirror_row.py` writes `out/spinning-mirror-row/` (assembly STEP, parts split laser/print/purchase with DXF) and `../bom/bom-spinning-mirror-row.csv`, carbon-tube top bar on steel rod posts with two thin blades; previews in `media/previews/spinning-mirror-row/`; `--check` runs random-pose clash checks; notes in `../docs/spinning-mirror-row.md`.

Single mirror test rig (2026-11-14): `python3 src/spinning_mirror_row.py --units 1` writes `out/spinning-mirror-test/` and `../bom/bom-spinning-mirror-test.csv`, previews in `media/previews/spinning-mirror-test/`; same top support as the row on a 220 mm base; notes at the end of `../docs/spinning-mirror-row.md`.

Spinning mirror trio (2026-11-14): the unit is now an 80 mm mirror on the real iPower GM2804 + AS5048A motor (STEP in `src/assets/`). `python3 src/spinning_mirror_row.py --units 3` writes `out/spinning-mirror-trio/`, `../bom/bom-spinning-mirror-trio.csv` and previews in `media/previews/spinning-mirror-trio/`; `--units 1` and `--units 7` rebuild the test rig and the row with the new unit.

Spinning mirror control deck (2026-11-15): the rigs now sit on a plywood box with a deck level with the hub tops (electronics inside, jitter knob, DC jack and USB cut-outs), 170 mm wide, printed parts matt black; see `../docs/spinning-mirror-row.md`.

Spinning mirror hood (2026-11-15): 5 mm clear acrylic cover on the base top layer, front ledge with a printed control pod (dial, DC jack, USB-C) and a reed-switch interlock; see `../docs/spinning-mirror-row.md`.
