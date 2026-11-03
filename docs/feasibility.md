> **Status: historical.** Assessment of the earlier arm concept. Not updated for the hinged mirror (see `cad-brief.md`).

# Build feasibility (first assessment, 2026-11-01)

Based on the simulation (`simulation.md`). All masses, torques, resolutions and prices below are my estimates (inference), not measured or priced. A priced UK BOM is still to do.

| Area | Assessment | Notes |
|---|---|---|
| Sun position and control software | Easy | NOAA formula is tiny; runs on an ESP32 |
| Pointing resolution | Easy | 1/16 microstepping (3200 steps per turn) through a 20:1 reduction is about 0.006° per step; backlash, not step size, limits accuracy |
| Quiet, slow motion | Easy to moderate | TMC2209 drivers are near silent; the Sun needs only about 0.25° per minute |
| Slip ring on the base | Easy to moderate | Controller on the rotating stage means only power crosses; capsule slip rings carry limited current per ring, so use several rings in parallel; check ratings when pricing |
| Holding the arm against gravity | Moderate | Shoulder and elbow carry the arm; hold current makes heat; consider a spring counterbalance or a self-locking stage |
| Low-backlash printed reductions | Hardest mechanical part | Options: two-stage belt (about 9:1 to 16:1, near zero backlash, some compliance), printed cycloidal (compact, low backlash), printed planetary (simplest, more backlash) |
| Stiff, good-looking tube links | Moderate | Links around 160 mm fit a normal print bed; the UR-style look needs careful print orientation and finishing |
| Knowing joint positions after power-up | Moderate | Limit switches or hall sensors per joint, plus a magnetic encoder (e.g. AS5600 class) per joint to catch missed steps |
| Pointing accurately at true north | Moderate | Mark north on the base at install; trim offset by aligning the pointer's shadow with the real Sun on a clear day (inference) |

## Architecture suggestion (inference, to verify in simulation)
Prescribe the base yaw, shoulder and elbow as the posture, then solve the two wrist joints in closed form so the pointer lies on the Sun. That is cheap enough to run on the ESP32 alone, so no host computer is needed.

## Prototype order
1. One joint test rig: NEMA 17 + reduction + magnetic encoder; measure backlash, holding temperature and smoothness.
2. Base: turntable bearing, slip ring, yaw drive and north marker.
3. Partial-scale or cardboard arm to check clearances.
4. Full arm.

## Main risks
Backlash and sag at the wrist, motor weight at the elbow, slip ring current limit, winter wrist limit (joint 4 near its range end).
