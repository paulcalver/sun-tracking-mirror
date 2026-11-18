> **Status: historical.** Simulation of the earlier arm concept. The Sun maths it uses is reused by the animations (`cad/src/sun_day.py`).

# Simulation results (first pass)

Script: `sim/arm/arm_sim.py` (run from the repo root). Sun position from `sun-path/scripts/sun_path.py` (NOAA low precision, London). Outputs in `sim/arm/output/` (joint-angle CSVs per minute, `arm-poses.png`); terminal summary in `sim/arm/output-summary.txt`. Draft geometry: shoulder 60 mm above table, links 160 + 160 mm, pointer 90 mm, wrist held 200 mm out. All numbers below are simulation results from those draft lengths, not tested hardware.

## Findings

1. **Elevation range confirmed:** about -62° to +62° across the year (winter solstice -61.9° to +15.1°; summer solstice -15.0° to +61.9°).
2. **The flip-over idea does not work in London. This corrects an earlier suggestion.** Yaw travel is about 360° per day in both arm branches (yaw = azimuth, or yaw = azimuth + 180 with the arm leaning back). Reason (inference, from geometry): the two branches only join where the pointer is vertical, and the London Sun never goes there, so the arm cannot switch branch smoothly. The base must either rotate continuously or unwind once a day.
3. **Table clearance is easy.** With the wrist held 200 mm out and rising as the pointer tips down, the pointer tip stays at least 35 mm above the table, the elbow at least 185 mm, with no unreachable moments across the three days.
4. **Joint speeds are very low.** Fastest per-minute movement: yaw about 0.5°, wrist about 0.2 to 0.3°, shoulder 0.2° or less, elbow 0.03° or less. Backlash is the main enemy, not torque.
5. **Posture rule so far is dull.** Under the "clearance" rule the shoulder and elbow barely move; the wrist does the pointing. The expressive use of the spare joints still needs designing (see open questions).

## Consequence for the yaw joint

Options, none yet chosen:
- **Slip ring on the base.** Cheap and simple (price unverified). If the ESP32 and drivers rotate with the yaw stage, only power (2 rings) needs to cross the joint, and commands can go over Wi-Fi. Inference, not yet designed.
- **Cable-limited yaw with a daily unwind.** One visible fast rotation each day; could be timed for a quiet hour.

# Six-joint, UR-style simulation (second pass)

Script: `sim/arm/arm6_sim.py` (`--five` locks the last joint). Outputs: `sim/arm/output6/` and `sim/arm/output6-five/` (joint-angle CSVs per 2 minutes, `poses.png`, `winter-solstice.gif`); terminal summaries in `sim/arm/output6-summary.txt` and `sim/arm/output6-five-summary.txt`. Geometry is UR-like proportions recalled from public figures (approximate, not manufacturer data) scaled to 0.65, giving about 300 mm reach and a shoulder 99 mm above the table; 70 mm pointer. Simulation only, no hardware tested.

## Method
The pointer axis is forced onto the Sun direction. The spare freedom is used for a slow, visible posture: the base yaw swings up to 45° either side of the Sun's compass heading, the shoulder swings 25° and the elbow 30° (periods 72, 40 and 60 minutes), and joint 6 swings back and forth as a decorative roll. The solver also keeps links above the table, apart from each other, and away from the wrist singularity.

## Findings
1. **Aim is exact:** pointing error at most 0.002° on all three days.
2. **Six joints and five joints give the same result.** The sixth joint rolls the pointer about its own axis, so it does not change the aim. It only adds decoration. Five joints are enough for the job (inference from the model, and the runs agree).
3. **The base must turn once round every day.** Net yaw change is about -365° per day. Every other joint stays within about ±175° and returns to its start each day. So the slip ring (or daily unwind) question is back on the base, not the wrist.
4. **A wrist-only solution does not exist at the equinox.** The wrist cannot avoid a full turn on a head limited to ±175°. Reasoning (inference): the Sun's equinox path is a great circle, so any two-axis head must either wind 360° or pass through its singular position. Letting the base do the winding avoids both.
5. **Winter is the tight case.** Joint 4 sits at its 175° limit for much of the winter day and the posture drifts up to 32° from its preferred swing. A wider joint 4 range, or a different home pose, would relax this.
6. **Clearance:** lowest link point 41 mm above the table (winter), closest links 75 mm apart, wrist singularity never approached (|sin q5| at least 0.71).
7. **Speed:** fastest joint about 4 to 7° per minute, set by the posture swings, not the Sun. These can be slowed to taste.

## Caveats
Link thicknesses, motor housings and cables are not modelled, so the clearances are for centre lines only. Joint torque and backlash are untested.
