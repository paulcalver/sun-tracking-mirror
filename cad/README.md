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

Spinning mirror row of 7 (2026-11-14): `src/spinning_mirror_row.py` writes `out/spinning-mirror-row/` (assembly STEP, parts split laser/print/purchase with DXF) and `../bom/bom-spinning-mirror-row.csv`, previews in `media/previews/spinning-mirror-row/`; `--check` runs random-pose clash checks; notes in `../docs/spinning-mirror-row.md`.
