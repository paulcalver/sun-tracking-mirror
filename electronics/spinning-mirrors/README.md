# Spinning mirrors: electronics

One subfolder per build. Pin map and firmware: `firmware/README.md`. Parts and order list: `docs/spinning-mirror-150-nema17-wiring-and-order.md`.

| Build | Folder | Status |
|---|---|---|
| 150 mm single test unit (1 NEMA 17, ESP32, 1 TMC2209) | `150mm-test-unit/wiring.svg` | drawn, not built or tested |
| 150 mm trio (3 motors, one ESP32) | `150mm-trio/` | not drawn yet |
| 100 mm wall piece (2 motors in series on one driver) | `wall-row-100/wiring.svg` and `wall-row-100/breadboard-layout.svg` (solderable breadboard, XIAO ESP32-S3) | drawn, not built or tested |
| Remote dial (2 pots on a second ESP32, ESP-NOW) | `remote-dial/wiring.svg` | drawn, not built or tested |

Add a new build as a new subfolder here and a row above. Open the .svg files in a browser.
