# Sun-facing mirror sculpture

A raw 6 mm glass mirror, hinged on a bar level with the top of a black square plinth, that faces the Sun (or a planet) directly. A turning drum under it gives azimuth, a lead-screw scotch yoke gives tilt (+/-70 deg). Sun position is calculated from time and place (no Wi-Fi, a Pico and a clock chip), not sensed.

Status (2026-11-03): CAD v4 drawn around real parts, BOM and laser files made, animations rendered. Nothing ordered, printed or tested.

Read in this order:
1. `docs/cad-brief.md`: the current design, sizes, checks, open points.
2. `bom/archive/arm-v4/bom-v4.md` (and `bom/archive/arm-v4/bom-v4.csv`): parts split into laser cutting, 3D printing and purchase. `bom/archive/arm-v4/bom-for-suppliers.md` is the plain buy list for a UK supplier search.
3. `docs/parts-sourcing.md`: where each bought part comes from, its status and the decisions.
4. `cad/README.md`: folder layout (`cad/src` scripts, `cad/out` STEP and DXF, `cad/media` pictures and video).
5. `HANDOVER.md`: long decision log of the earlier arm and disc concepts, kept for history.

`docs/` also holds older notes from earlier concepts (arm simulation, feasibility, donor hardware, HDP30, test rig); each starts with a status line saying it is historical.
