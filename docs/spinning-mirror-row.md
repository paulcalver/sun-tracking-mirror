# Spinning mirror rigs: trio, row of 7 and single test (updated 2026-11-14)

> Primary route from 2026-11-15: 150 mm mirrors on NEMA 17 steppers, see `spinning-mirror-150-nema17.md`. This brushless GM2804 version is the alternative.

Draft CAD, nothing cut, printed or tested. Model: `cad/src/spinning_mirror_row.py` (reuses the single unit from `spinning_mirror.py`; `--check` runs 8 random poses of all units against everything). Single-unit notes: `spinning-mirror-gimbal.md`.

## Current focus: the trio (`--units 3`)
Three units with the real iPower GM2804 + AS5048A encoder motor and an 80 mm mirror (ring 88 / 98 mm), same top support as below on a 420 x 140 mm plywood base. Unit pitch 115 mm (17 mm clear between rings), centres X = -115, 0, +115, carbon tube 380 mm with rod posts at X +/-189, no blades. Tube centre 184 mm above the table, ring centre 116 mm. Frame about 2.1 kg (1.36 kg steel ballast), units about 0.37 kg. No clashes in 8 random poses. Files in `cad/out/spinning-mirror/archive/spinning-mirror-trio/`, `bom/spinning-mirrors/archive/bom-spinning-mirror-trio.csv`, previews in `cad/media/previews/spinning-mirror-trio/`.
Run: `python3 cad/src/spinning_mirror_row.py --units 3`. The 7-unit row and the single test rig come from the same script (`--units 7`, `--units 1`) and are regenerated with the new unit; the 7-unit row (pitch 115, about 870 mm base) has the blades.
Motor mounting in the base: four M2 x 30 screws come up from under the bottom plywood layer through the layers and the printed boss into the stator bottom holes; the 11 mm cable hole under each motor lines up with the 6.5 mm hollow shaft.

## Original layout notes (first version at 60 mm, kept for the structure)

## Layout (revised: minimal top and side structure, symmetrical)
- 7 units at a uniform 95 mm pitch, centres X = -285 to +285, 17 mm clear between rings.
- Base 740 x 140 mm, three 6 mm plywood layers on four rubber feet. The middle layer has two windows for 38 x 6 x 620 steel flat bar (about 2.2 kg ballast), a cable channel that opens at the left end, and a hex pocket for a thin M8 nut under each end post.
- Motor boss (print) bolts to the top layer with M3 x 16 self-tapping screws; the unit geometry above it is unchanged.
- Top: a 10 x 8 mm carbon tube, 700 mm, centre line 158 mm above the table. Each ring has a 3 mm steel pin (16 mm) that runs in a 683ZZ in a 12 x 20 mm printed block clamped under the tube (block plus cap, 2 x M3).
- End posts: two 8 mm steel rods, 25 mm outside the end rings (X +/-349), threaded M8 at the bottom into captive thin nuts in the middle layer. The tube is clamped to the rod tops by a printed block and cap (28 mm block, rod bore 8.1 mm, one M3 grub screw).
- Blades: two 3 mm plywood blades, 26 mm wide, in the gaps between units 2|3 and 5|6 (X +/-142.5), each with a tube hole and a tab into the top layer. 7 mm clear to the rings each side. The row reads as 2 | 3 | 2.
- Compared with the first version: tube 20 x 20 mm to 10 mm, end plates 70 x 12 mm to 8 mm rods, one off-centre 6 mm plate to two symmetrical 3 mm blades.

## Checks (script)
No clashes in the static pose and over 8 random poses of all units. Mass about 3.4 kg frame (2.2 kg steel) and 1.5 kg for the 7 units.

## Cutting
Bed 1219 x 914, plywood: the base layers (6 mm) and blades (3 mm) fit on one sheet each. DXFs in `cad/out/spinning-mirror/archive/spinning-mirror-row/parts/laser/` (`laser_blade_3mm_x2.dxf` is one profile, cut twice). Needs both 6 mm and 3 mm ply.

## Open
- Motor size and bolt circles are still assumed.
- The tube stiffness (rough estimate, 15 Hz bending mode over the full span, much higher with the blades) and the rod posts are not analysed. The posts rely on a captive nut in a 6 mm plywood layer, so check them for wobble and add a second nut, a plate or a flange if they feel loose.
- Carbon tube ends are fragile in the clamps; do not overtighten.
- Ply tab slots are 0.2 mm loose, the blade slot 3.2 mm for a 3 mm blade; test on a scrap.
- 7 motors need 21 PWM outputs, two boards.
- Vibration through the shared base and tube between units, worth watching on the first run.

## Single mirror test rig
`python3 cad/src/spinning_mirror_row.py --units 1` writes the same design for one unit to `cad/out/spinning-mirror/archive/spinning-mirror-test/` (assembly STEP, parts split laser/print/purchase with DXF), `bom/spinning-mirrors/archive/bom-spinning-mirror-test.csv` and `cad/media/previews/spinning-mirror-test/`.
- Same unit, pin, top block, tube clamp and 8 mm rod posts as the row, so it tests the top bearing alignment, random tumbling, balance and the post mounting before building seven.
- Base 220 x 140 mm (three 6 mm plywood layers), two steel bars 38 x 6 x 180 (about 0.64 kg ballast), posts at X +/-64, carbon tube 130 mm long, tube centre 158 mm above the table. No blades.
- Mass: frame about 1.1 kg, unit about 0.21 kg. Checked for clashes at 8 random poses, none.
- One motor, one driver (SimpleFOC Mini or similar), one ESP32, 12 V 2 A supply.
- Things to learn from it: does the pin run free in its bearing (float and friction), is the random speed profile giving tumbling as the page predicts, how much the post wobbles, whether the single plywood layer holds the nut.

## Fix: tube clamps (2026-11-15)
The first printed caps were not usable: the tube groove cut through the whole 5 mm cap height, so each cap was two separate pieces, and the plastic under the bearing pin hole was 0.65 mm and under the post rod bore 0.45 mm. Now:
- Cap is 8.5 mm tall above the tube centre line (3.5 mm roof over the tube), one solid. Block top is 0.3 mm below and cap bottom 0.3 mm above the centre line, so the two halves close onto the tube when the M3 screws are tightened. Clamp is 23 mm wide, screws 8 mm either side of the tube.
- Tube centre line is 2 mm higher (13 mm above the block bottom): 2.7 mm of plastic between the pin hole and the tube saddle. Rod post tops are 10 mm below the centre line: 4.5 mm of plastic below the saddle, 18 mm rod engagement in the end clamp.
- `--check` now also reports any printed or cut part that is not a single solid.
- Clamp tightening on a carbon tube: tighten evenly and not hard; a thin strip of rubber or tape in the saddle spreads the load.

## Control deck and box (2026-11-15)
The base is now a plywood box with a deck level with the top of the hub adapters (option A from the discussion), so the electronics and cabling live inside and the controls sit on top.
- **Heights (trio):** base top 20 mm, deck 56.15 to 62.15 mm (1.0 mm above the rotor bell, top level with the hub tops, hub now 7 mm thick), ring bottom 68.2 mm, so the rings clear the deck by 6 mm. Box interior 36 mm tall, 400 x 150 mm (trio).
- **Base:** 170 mm wide (was 140), 420 mm long for the trio. Walls sit 4 mm in from the base edge, 6 mm plywood with finger tabs into slots in the top base layer and in the deck. Back and end walls are glued. The front panel is removable: bottom tabs locate it in the base, and three M3 x 20 wood screws go down through the deck into its top edge.
- **Deck:** 38 mm holes round the 35 mm hubs, 8.2 mm holes for the rod posts (the rods now pass through the deck, so they are held at two levels), a 7.5 mm hole for the jitter potentiometer at X -57.5, Y -62 (front strip, outside the ring sweep so the knob can be tall), and three screw holes along the front.
- **End walls:** left has an 11 mm hole for a DC barrel jack, right has a 14 x 8 mm USB slot (both assumed, edit `JACK_CUT` and `USB_CUT`).
- **Motor leads:** the old cable channel is gone. Each motor boss has a 7 mm slot at its base so the leads leave sideways (toward +Y) into the box, to a driver board sitting 50 mm behind the motor. Which way the real leads exit the stator is not confirmed.
- **Placeholders (not final):** driver boards 30 x 25 x 12 mm, controller 55 x 28 x 14 mm at X +57.5, Y -50, potentiometer and knob. Check real board sizes.
- **Ballast:** two 38 x 6 steel bars in windows in the middle base layer (1.36 kg for the trio); more steel could be added loose in the box floor.
- **Printed parts:** all printed parts are now matt black in the CAD colours (#262626; previews brighten them). The STEP only holds a colour, the matt finish comes from the filament. Black parts get hot in the sun: use PETG or ASA, not PLA.
- **Top bar kept** as before: carbon tube, rod posts, 3 mm blades for the 7-unit row.

## Clear acrylic hood (2026-11-15)
A safety cover over everything, standing on the base. It supersedes the deck-level controls above: the dial, DC jack and USB-C moved out of the box to a control pod on a front ledge outside the hood.
- **Hood:** 5 mm clear cast acrylic, one lift-off cover (top, front, back, two ends). Trio: 438 x 176 mm outside, inner top 211 mm above the table (191 mm tall from the base top), about 1.8 kg. The plywood box sits inside with an 8 mm gap all round (room for the reed switch and magnet, and an air channel). The ring and clamps clear the inside faces by 14 mm at the ends and 30 mm at the sides.
- **Joints (revised 2026-11-16, minimal edges):** plain butt joints at the four vertical corners and the top edge, solvent-welded, so the clear box shows only its outline. The end walls fit between the front and back walls (flush outer faces), and the top sheet sits on the walls. The only features left are the bottom tabs (6 mm, 20 mm wide) that drop into slots in `laser_base_top_6mm` and are not glued. They also work as the alignment jig: stand the four walls in the base slots, weld the vertical corners one at a time with a viscous cement (Weld-On 16 type), then weld the top sheet on, then lift the cover off. (The first version had finger joints and top tabs; they looked busy.)
- **Clear in CAD:** the hood is a near-white colour at 75 percent transparency in the assembly STEP, but Fusion usually ignores STEP transparency. For a clear box in Fusion use `spinning-mirror-trio-assembly-no-hood.step` plus `spinning-mirror-trio-hood.step` (hood only), and set the hood bodies' Appearance to Glass. The previews already draw it transparent.
- **Base:** now 450 x 224 mm for the trio: 6 mm rim outside the hood, plus a 36 mm ledge across the front for the pod. Plywood box 412 x 150 mm (narrower than before: it no longer needs a control strip). Ballast 1.47 kg in the middle layer; frame about 4.9 kg with the acrylic.
- **Vents:** six 40 x 6 mm slots low on the front and back walls just above the deck level (the plywood box blocks the air gap below it), and two rows of six 40 x 6 mm slots in the top. All 6 mm wide, well clear of the rings.
- **Control pod (printed, matt black):** 70 x 30 x 24 mm on the ledge, centre of the front, screwed from below with 4 M3 x 25 into heat-set inserts. Holds the jitter potentiometer (7.5 mm hole) on top, an 11 mm DC barrel jack on the left, a USB-C slot on the right. Wires leave the back of the pod, pass through a 14 x 6 mm notch in the bottom edge of the hood front wall and through a 10 mm hole in the removable front panel (X -20, 30 mm up) to the controller.
- **Interlock:** a glass reed switch (3 x 16 mm) on the outside of the plywood back wall (X +103, 30 mm up, lead hole 4 mm) and a 6 x 3 mm magnet glued to the inside of the hood back wall, 2 mm apart when the hood is seated. The controller should stop the motors when the switch opens. Magnet size and switch sensitivity need testing.
- **Laser cutter:** assumed CO2 (to be checked: a diode laser cannot cut clear acrylic). Polycarbonate cannot be laser cut.
- **Things to watch:** acrylic faces add faint ghost reflections to the beams, a closed hood warms up in the sun (the vents help), and a closed hood can amplify motor hum (foam strip under the walls).
- Outputs for the trio: `cad/out/spinning-mirror/archive/spinning-mirror-trio/` (DXFs for the hood panels and plywood parts, STEP with the hood at 25% opacity), previews `row.png` (hood on) and `row-open.png` (hood off), `row-pod.png`.
