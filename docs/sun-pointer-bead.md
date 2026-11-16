# Sun pointer: the bead (concept CAD, 2026-11-12)

Status: concept model only, nothing built or tested. Source: `cad/src/sun_pointer_bead.py` (CadQuery). STEP: `cad/out/earlier-concepts/sun-pointer/sun-pointer-bead.step` (named parts, posed for 21 Dec 09:30 at 51.5 N, south wall, `--step --day --hour --lat`). Renders: `cad/media/previews/sun-pointer/` (`--render`). Design idea and the interactive view: `docs/sun-ring-concept.html` (Support: pointer).

## What it is
A horizontal arm from the wall ends in a ball socket; the bead hangs on the ball. Inside the bead a polar shaft turns once a day (spin); on its front end a fork carries a hinge, and a 390 mm carbon rod with a side-glow fibre tilts on it by the Sun's declination (+/-23.44 deg). The rod tip (a diffuser bead) is the Sun. The hinge point is the viewer.

Set once at install: turn the ball in its socket so the shaft points at the celestial pole (latitude and wall bearing), lock two M4 grub screws. The model is built for a south wall at 51.5 N: the shaft is 51.5 deg above horizontal, pointing at the wall.

## Mechanism (local axis frame, mm)
- Polar shaft: 8 mm tube (6 mm bore, wires through it), 688ZZ bearings at z 30 and 123. Spin motor: 28BYJ-48 with its axis parallel to the shaft, a 12T pinion and a 44T gear on the shaft (about 7:1 on top of the motor's 64:1, about 30,000 steps per turn, 0.012 deg, 0.08 mm at the tip). A magnet on the gear and a Hall sensor give the noon home.
- Slip ring (4-wire capsule) on the shaft's rear end carries power to the tilt motor and the LED. It sits in the hollow neck, with the wires leaving through the ball.
- Fork (printed, one part) on the shaft front: base, two arms, front bridge. 3 mm hinge pin. Rod hub (printed) with a 54 deg worm sector on the opposite side of the hinge, which also acts as the counterweight.
- Tilt: second 28BYJ-48 on the fork bridge with an 8 mm worm on the +z side, meshing with the sector (module 0.5, 31 mm pitch). Self-locking. Tilt resolution about 0.0015 deg.
- Rod: 3 mm carbon tube, 1.6 mm side-glow fibre alongside, LED in the hub lights it, 10 mm diffuser bead at the tip.
- Arm: 20 mm aluminium tube, flange and 4 screws to the wall, ball socket with a 40 deg opening for the neck.

## Checks (`--check`)
- Tip against the sun formulas of the tool (`sunReal`): six cases (solstices, equinox, night) agree to 0.000 mm.
- Clash sweep: 60 poses, spin 0 to 330 deg in 30 deg steps, tilt -23.44, -12, 0, +12, +23.44: 0 clashes (gear and worm contacts and joined parts excluded).
- Clearances at the tilt limits: rod to housing front 7.7 mm at +23.4 deg (it swings towards the housing), fork to housing 10 mm, rod hub 16 mm; tip to wall plate 113 mm at the worst pose (arm 495 mm, rod 390 mm).

## What changed while drawing it
- A worm for the spin drive put the motor body outside a 42 mm housing radius, so the spin drive is a spur pair with the motor parallel to the shaft. That lost the self-locking worm on the spin axis (the 28BYJ-48 gearbox holds a balanced load), and the housing is 92 mm across, a little more than the 70 to 90 mm guessed earlier.
- The LED had to move to the -z side of the hub (at +23 deg tilt it hit the fork base).
- The fork base moved 2 mm back, the worm sector was limited to 54 deg and the bridge shortened, so the sector's rim clears the bridge at full tilt.
- The magnet moved to a smaller radius so it does not strike the spin motor as the shaft turns.

## Not modelled or open
- Gear and worm teeth, wires, the cable path through the shaft and ball, fasteners (flange screws and grub screws are drawn, bearing and gear fixings are not), balance weights (the sector and tilt motor are on the far side of the hinge, mass not computed).
- The 28BYJ-48 output shaft is 8 mm off its body centre; the model puts it on the axis. Real placement needs the offset.
- The ball socket is one piece with two grub screws; a split clamp would hold better.
- Waterproofing, LED brightness through the fibre, fibre and rod flex at the hinge, and the drive firmware are untested.
