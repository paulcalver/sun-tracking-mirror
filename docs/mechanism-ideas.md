# Mechanism ideas for later: ball joint plus three linear actuators

Logged 2026-11-03. Not part of the current hinged-mirror design. Owner's note: Eliasson's World illuminator is believed to use a central ball joint and three linear actuators.

## Status of the Eliasson claim
- NOT confirmed by anything found. Studio page lists "mirror, tripod, steel, motors, control unit, custom electronics, and software" and no joint or actuator count: https://olafureliasson.net/archive/artwork/WEK108992/world-illuminator
- Creators Project / Vice says only "a set of actuators adjust the mirror", software in node.js on a Raspberry Pi, three years of development at the studio: https://www.vice.com/en/article/olafur-eliasson-harnesses-the-sun-with-giant-kinetic-mirrors/ (page opened). No ball joint, no actuator count.
- Where to verify: the SHIMURAbros film (https://vimeo.com/161100299), photos of the rig at the Bauhaus-Archiv and Fondation Louis Vuitton, or ask the studio. Check the film for the number of actuators and what sits under the mirror.

## The mechanism family (published work, so it is a known idea)
A mirror plate on a central spherical (ball) joint, tilted by three actuators spaced round it, is a parallel (tripod) mechanism. Closest published variants:
- 3-RPS heliostat, Ashith Shyam, Acharya and Ghosal (IISc), preprint 2017: three legs, each a passive revolute joint, a motorised sliding (prismatic) joint, and a spherical joint to the mirror. Claims (from the abstract, opened): less spillage and astigmatic aberration than two-axis mounts, three points of support so less deflection (supporting structure up to 60% lighter in their analysis), cheap linear actuators with no large precise speed reducers, and a prototype that tracked autonomously. https://mecheng.iisc.ac.in/~asitava/CJME-Ashith.pdf
- Talk slides, Ghosal, 2019: 3-RPS and a 3-UPU variant (the search summary says the UPU version has a fixed rotation centre; I did not confirm that in the slides). https://raml.iyte.edu.tr/wp-content/uploads/sites/298/2019/11/SunTrackingWithParallelRobots.pdf
- Commercial piezo tip/tilt stages use three actuators at 120 degrees with a coordinate transform (search summary, not opened): https://www.physikinstrumente.com/en/technology/parallel-kinematics/parallel-kinematics
- Patents describe ball and socket or universal joint mirror mounts moved by actuators (prior art, not the Eliasson design), e.g. https://patents.google.com/patent/US11082001

## Why it suits a heliostat but probably not this project (inference)
- A heliostat's mirror normal bisects the Sun direction and the target direction, so it only has to move through about half the Sun's sweep. That is a modest tilt range, which a tripod handles well.
- A mirror that faces the Sun must follow the full sweep: about +/-62 degrees tilt at London (design +/-70) plus a full turn in azimuth each day. A tripod on a ball joint has limited tilt and a limited spin, so earlier in this project it was rejected (limited range, three motors).
- Possible later use: a heliostat mode, or a small secondary mirror that only needs a few tens of degrees.

## Properties worth remembering
- Three actuators control three motions (two tilts and a height or spin); a mirror only needs two tilts, so one is spare (published 3-RPS work uses the spare). With a central ball joint holding the centre, the spare is the spin about the mirror's normal (inference).
- Linear actuators (leadscrew steppers, as in the current tilt drive) avoid big gearboxes; precision then comes from lead pitch and microstepping.
- Needs inverse kinematics (leg lengths from the mirror normal), a calibration routine, and three limit switches.
- Wind and gravity loads are shared across three points.
