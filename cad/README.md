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
