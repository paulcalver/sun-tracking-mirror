> **Status: not built, not part of the current design (2026-11-03).** Files moved to `cad/out/archive/test-rig` and `cad/media/test-rig`.

# Single-joint test rig (belt reduction variant), design v0.1

Purpose: before building the arm, measure whether a printed belt reduction is smooth, quiet and stiff enough for a pitch joint, and learn what holding the load costs in heat. CAD: `cad/src/test_joint_rig.py` (CadQuery, run from the repo root). Outputs: `cad/out/archive/test-rig/rig_*.stl` and `.step` (single parts), `cad/out/assembly/test_joint_rig_assembly.step` and `.glb` (full assembly, 13 named parts, bought parts in grey and the belt in black), preview in `cad/images/test-rig-preview.png`, labelled views in `cad/images/test-rig-labelled.png` (from `rig_labelled_views.py`). The belt is drawn as a plain band, without teeth.

Status: drafted and checked for part overlaps in software only. Nothing has been printed or test-fitted. Check every bought part against its drawing before printing.

## What it is
- NEMA 17 (42x34 mm) with a 20-tooth pulley drives a 60-tooth printed GT2 pulley (3:1) through a 200 mm closed belt. Centre distance 58.6 mm; the motor bracket has 16 mm slots for belt tension.
- 8 mm output shaft on two 608 bearings in a printed block.
- A 150 mm lever arm on the shaft with weight holes at 30, 50, 75, 100, 125 and 145 mm. Hanging a weight loads the joint with gravity, like the arm's shoulder.
- A 6x2.5 mm diametric magnet on the back of the shaft, read by an AS5600 board in a bracket, so output angle is measured directly.

## Printed parts (PETG)
`base_plate`, `bearing_block`, `motor_bracket`, `output_pulley_60T`, `lever_arm`, `encoder_bracket`. STLs are in assembly orientation; reorient in the slicer (suggestion: block with a bearing face down, pulley on its flange, lever flat, bracket on its foot). The GT2 tooth shape is an approximation and will probably need a tolerance tweak on the first print.

## Extra parts for the rig (beyond the arm BOM)
2 x 608 bearings, 80 mm of 8 mm rod, 6x2.5 mm diametric magnet, 20-tooth GT2 pulley (5 mm bore) and a 200 mm closed belt, M3 and M4 bolts and nuts, a few weights (e.g. bags of coins or M8 nuts). The AS5600 board, TMC2209, ESP32 and 24 V supply are already in the BOM. Prices for the extras are not yet looked up.

## Limits to know about
- The 45 mm axis height means the lever can only swing downward by about 27 degrees with a weight at the 100 mm hole (about 18 degrees at 145 mm) before the weight reaches the table. For wider swings, clamp the rig over a table edge.
- Rough torque check (my estimate): a 0.5 kg weight at 100 mm is about 0.5 N.m. The motor holds about 0.25 N.m, so 3:1 gives roughly 0.75 N.m at best before losses. Start with lighter weights.
- The AS5600 module size varies by seller. The bracket pocket is 23.6 mm and the gap to the magnet is designed to be about 2 mm; adjust to the board you buy.
- Base plate and motor bracket slots need M4 bolts with nuts under the plate; no nut recess is drawn.

## Test procedure (proposed; thresholds are my suggestions, not requirements)
1. **Resolution and smoothness:** command very slow moves (0.25 degrees per minute and 0.05 degrees steps) and log the encoder. Look for steps, stalls and ripple.
2. **Backlash:** hold the motor still, push the lever each way with a known small weight, and read the encoder difference. Target at most 0.5 degrees at the output.
3. **Repeatability:** go to the same angle from both directions 20 times. Target spread at most 0.2 degrees.
4. **Gravity hold and heat:** load the lever, hold at several hold-current settings for 30 minutes and read motor temperature. Target a case temperature below 50 degrees C and no slipping.
5. **Noise and stability:** listen at running and holding speed; watch for belt ripple and resonance.
6. **Belt tension:** repeat 2 and 3 at two tensions to see the trade-off between backlash and bearing load.

## Not yet designed
- A coaxial planetary or cycloidal variant to compare (the motor bracket's 22 mm boss and M3 pattern can be reused; a printable gearbox design has not been chosen).
- Test firmware (ESP32 with TMC2209 and AS5600 logging).
- A second belt stage (9:1).
