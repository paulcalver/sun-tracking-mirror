"""Adapter sleeve for the already printed electronics box: its DC socket hole is 11 mm through a 3 mm wall, the socket needs 7.8 mm.
A plain sleeve (bore 7.8 mm, outside 10.9 mm so it presses into the 11.0 mm hole) with a thin flange on the OUTER face of the back wall.
Print with the flange on the bed. If the printed hole measures differently, pass --od (outside diameter of the sleeve, mm).

  python3 cad/src/dc_socket_adapter.py [--od 10.9] [--bore 7.8] [--wall 3.0]
Writes cad/out/spinning-mirror/dc-socket-adapter/print_dc_socket_adapter.step
"""
import argparse
import sys
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spinning_mirror_150_nema17 as u  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--od", type=float, default=10.9)      # sleeve outside diameter: the 11.0 mm hole less 0.1 mm for a press fit
ap.add_argument("--bore", type=float, default=7.8)     # the socket's hole
ap.add_argument("--wall", type=float, default=3.0)     # box wall thickness (EB_DC_WALL)
ap.add_argument("--flange-d", type=float, default=14.0)
ap.add_argument("--flange-t", type=float, default=1.2)
a = ap.parse_args()

ft = a.flange_t
adapter = (cq.Workplane("XY").circle(a.flange_d / 2).extrude(ft)
           .union(cq.Workplane("XY").circle(a.od / 2).extrude(ft + a.wall))
           .cut(cq.Workplane("XY").circle(a.bore / 2).extrude(ft + a.wall)))
out = HERE.parent / "out" / "spinning-mirror" / "dc-socket-adapter"
out.mkdir(parents=True, exist_ok=True)
u.write_step("print_dc_socket_adapter", adapter.val(), out / "print_dc_socket_adapter.step")
print(f"Wrote {out}: sleeve {a.od:g} outside, {a.bore:g} bore, {a.wall:g} long plus a {a.flange_d:g} x {ft:g} mm flange (total {ft + a.wall:g} mm); "
      f"the socket's thread must reach through {ft + a.wall:g} mm plus its nut")
