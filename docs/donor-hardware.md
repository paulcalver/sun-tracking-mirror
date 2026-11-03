> **Status: historical (2026-11-02).** Donor product search for the earlier arm concept. Not part of the current design.

# Donor hardware: consumer products that already have the degrees of freedom

Written 2026-11-02. Purpose: find ready-made pan/tilt (azimuth/elevation) products that could be hacked into the Sun pointer, conceptually and mechanically, instead of building the goal-post or nod mount from scratch.

Marking: **[web]** = from a search result, linked. **[general]** = from my general knowledge, not checked in this session. **[inference]** = my reasoning. Prices are snapshots, not re-verified.

## What the job needs (from HANDOVER.md)

- Azimuth: a full 360 degrees every day, in one direction. Endless rotation is ideal; 340 degrees plus a daily unwind is workable.
- Tilt: the Sun's elevation at London runs from about -62 to +62 degrees over the year, and the owner wants it tracked 24/7 including below the horizon. So the **pointing axis** must swing about 124 degrees centred on the horizon (design for 130 to 140).
- Slow (0.25 degrees per minute), light load (a 12 inch / 305 mm polished disc, or a smaller mirror, about 0.5 to 1.5 kg), indoors.

**Key trap (inference):** camera specs quote *coverage*, which adds the lens's field of view to the motor's travel. The Sun pointer needs the *mechanical* range of the axis, which is smaller. Example: Tapo C225 is 340 degrees mechanical pan and 60 degrees mechanical tilt, quoted as 360 and 149 degrees coverage [web: [Tapo C225 specs](https://www.tapo.com/en/product/tapo-c225-security-camera/v1/1-pack/specs/)].

Second trap (inference): most products only point at or above the horizon (telescopes, antenna rotators) or only below it (ceiling cameras). Below-horizon pointing is the demanding part of the owner's brief. Tricks are listed per candidate.

## Shortlist by fit

| Rank | Donor | Az | Tilt | Cost | Why |
|---|---|---|---|---|---|
| 1 | DMX moving head or mirror scanner | 540 deg | 270 deg | £0 to £1,100 | Only class that covers the whole sphere, so below horizon is free |
| 2 | Sky-Watcher AZ-GTi (or a direct-drive alt-az) | 360, endless | to check | about £319 | Built to track slowly, has a solar rate, WiFi API |
| 3 | Yaesu G-5500 az-el rotator | 450 deg | 180 deg | about £650 | Ready-made az-el with computer interface, but cannot go below horizon |
| 4 | Dome PTZ camera, mounted upside down or sideways | 360, endless | 90 deg | £60 to £300 | Cheapest real pan/tilt, has a slip ring |
| 5 | Pair of Syrp Genie Mini II heads | 360 | 360 (second unit) | about £600 | Beautiful, quiet, designed for slow moves |
| 6 | Cheap Wi-Fi pan/tilt cameras (Tapo) | 340 | 60 to 70 | £25 to £50 | Cheapest, but tilt too small without a linkage |

## The wide pool

### A. Security and webcam family

1. **Tapo C210 / C220 / C225 (TP-Link).** 340 degrees mechanical pan, tilt 60 (C225) or 70 (C210) degrees mechanical [web: [C225](https://www.tapo.com/en/product/tapo-c225-security-camera/v1/1-pack/specs/), [C210 comparison](https://yo-facturo.com/blog/tapo-c210-caracteristicas-y-diferencias-con-la-c200/)]. Documents RTSP and ONVIF [web, same comparison; ONVIF *PTZ* commands not confirmed]. Hack: strip the housing, keep the two small steppers and gearing, drive with your own board; or keep the firmware and send ONVIF move commands from the host. Weakness: pan not endless, tilt only 60 to 70 (inference: a 2:1 linkage or gear step-up on the tilt would double it, at the cost of resolution and torque). Payload is tiny, so only a small mirror.
2. **Reolink RLC-523WA.** 360 degrees pan, 0 to 90 degrees tilt, pan speed 2.5 to 150 degrees per second, tilt 1.5 to 60 [web: [Reolink](https://reolink.com/product/rlc-523wa)]. Slow speeds are close to what the Sun needs. ONVIF presence reviewed, PTZ speed over ONVIF unverified [web: [review](https://moderncastle.com/reolink-rlc-523wa-review/)]. Hack: mount the dome on a wall so the tilt axis becomes horizontal, or upside down for below-horizon.
3. **Hikvision / Dahua / Axis speed domes.** [general] Industrial PTZ domes have endless pan (slip ring inside), tilt about 0 to 90 with auto-flip, Pelco-D/P serial or ONVIF control, and many appear second hand for £50 to £150. Hack: RS-485 Pelco-D from an ESP32 is a well-trodden path [web: hobbyists note Pelco is the common protocol, [All About Circuits thread](https://forum.allaboutcircuits.com/threads/ptz-standards.7759/post-44821)]. Weakness: designed for high speed, so slow motion can be jerky (inference, test first).
4. **Insta360 Link / Link 2 (AI gimbal webcam).** Pan/tilt exposed as standard UVC controls, with community tools on Linux and macOS [web: [link-ctl](https://pypi.org/project/link-ctl/), [Linux controller](https://github.com/vrwallace/Insta360-Link-1-and-2-Controller-for-Linux)]. Range is only loosely quoted (over 180 degrees pan, 90 tilt, press coverage [web: [Digital Camera World](https://www.digitalcameraworld.com/news/insta360-link-announced-a-4k-webcam-with-an-ai-powered-gimbal)]). Cheap to try as a *conceptual* piece: a webcam that stares at the Sun's position without any image.
5. **Eufy, Ring, Wyze pan cams, baby monitors, Echo Show 10.** [general] Same family as Tapo. The Echo Show 10 has a motorised base that rotates a screen to follow a person; pan only. Not researched in detail.
6. **Arducam and Raspberry Pi PTZ camera kits.** [web: [Arducam docs](https://docs.arducam.com/Raspberry-Pi-Camera/Pan-Tilt-Zoom-Camera/PTZ/)] Open, documented, small. Good for learning, too light for a disc.
7. **Pimoroni Pan-Tilt HAT.** Two servos, 180 degrees each axis, £30 to £42 for the full kit but retired and mostly out of stock [web: [Pi Hut](https://thepihut.com/products/pan-tilt-hat), [Rapid](https://rapidonline.com/pimoroni-pim183-raspberry-pi-pan-tilt-hat-75-0790)]. Fine as a pocket-sized proof of concept of the sun maths; servo jitter at slow speeds is a known nuisance [general].

### B. Photography and film motion control

8. **Syrp / Manfrotto Genie Mini II.** Quiet, 360 degree pan, 3 kg, app and Bluetooth, built for slow time-lapse moves; two units give pan and tilt [web: [Scan UK, £298.99 pre-order](https://www.scan.co.uk/products/manfrotto-genie-mini-ii-motion-control-pan-head-timelapse-turntable-mode-app-control)]. The Genie II (6 kg pan) is discontinued but turns up second hand around £134 to £524 [web: [MPB](https://www.mpb.com/en-uk/product/syrp-genie-ii-pan-tilt-head/sku-3299305)]. A Genie lying on its side is a tilt axis; stack two for az plus tilt (inference). Control protocol is proprietary, so expect to use the app, or open it up and drive the motor yourself.
9. **Motorised 360 photography turntables (about £30 to £100).** [general] Endless rotation, slow speeds, mains or USB. Cheapest azimuth stage. Needs a gear-motor swapped for a stepper or a speed re-map.
10. **Phone and camera gimbals (DJI Osmo, Zhiyun, Hohem).** [general] Three brushless axes with Bluetooth remote. Tilt range wide, pan often ±180 or endless in follow mode. Stock motors are made for holding, not slow rotation, but SimpleFOC-style brushless control is possible. Hacking proprietary firmware is hard; replacing the controller is easier.
11. **Camera slider and pan heads for video (eMotimo, Edelkrone).** [general] Not searched, premium priced, not recommended first.

### C. Astronomy

12. **Sky-Watcher AZ-GTi (alt-az, WiFi).** About £319 UK with tripod [web: [Park Cameras](https://www.parkcameras.com/shop/sky-watcher-az-gti-alt-azimuth-wi-fi-mount-and-tripod_9801141k), [Campkins £379](https://www.campkinscameras.com/?p=107972)]. Payload up to 5 kg, makes its own WiFi network, controlled by the SynScan app [web: same results]. The bigger AZ-GTiX listing mentions a solar tracking rate [web: [Astroshop](https://www.astroshop.eu/azimutal-mit-goto/skywatcher-montierung-az-gtix-wifi/p,77228)]; check the standard AZ-GTi has it too. **Open:** altitude range was not in any result, so read the manual. [general] It speaks a documented protocol (SynScan WiFi / INDI / ASCOM), so a host script can slew it from sun maths. Likely the best "off-the-shelf" pointer. Below horizon probably blocked by the mount geometry (inference).
13. **Equatorial tracker (Sky-Watcher Star Adventurer and similar).** [general] A polar-aligned single axis turning 15 degrees per hour: this is the lean-over layout in the handover, bought rather than built. Add a second small axis for the seasonal 23 degree declination swing and you have the lean-over mount. Strong conceptual match.
14. **Direct-drive alt-az mounts (iOptron, others).** [general] Not researched. Smoother, pricier.

### D. Antenna and satellite

15. **Yaesu G-5500 az-el rotator.** 450 degree azimuth, 180 degree elevation, about £650 at Moonraker, about $750 on [SatNOGS](https://wiki.satnogs.org/G-5500) [web: [Moonraker](https://moonrakeronline.com/eu/antennas/antenna-hardware/rotators/yaesu-1)]. Takes analogue voltage control, has a computer interface (GS-232) used by satellite tracking software [general]. Elevation 0 to 180 covers the upper hemisphere only, so below-horizon needs a flipped mount (inference).
16. **DiSEqC 1.2 satellite dish motors (about £20 to £60).** One axis of ±80 degrees, for dishes up to 1.2 m [web: [Jaycar LS3330](https://jaycar.co.nz/diseqc-12-motor-with-metal-gear/p/LS3330)]. Too little range alone; two stacked, one as elevation, give an az-el of ±80 each. Controlled by a documented DiSEqC command set [web: forum threads, [Arduino forum](https://forum.arduino.cc/t/puntamento-antenna-satellitare-motorizzata/1357847)]. Cheap, metal geared, built to sit outdoors.
17. **Marine radar pedestals and old rotating antennas.** [general] Endless azimuth, heavy, slip ring built in. Second hand only.

### E. Stage and architectural lighting (the widest DOF per pound)

18. **DMX moving head, mini spot or wash.** 540 degree pan and 270 degree tilt are standard, which covers the whole sphere including below the horizon [web: [Farnell TINYMOVER2, no longer stocked, £82.50](https://cpc.farnell.com/qtx/tinymover2/2-in-1-40w-led-moving-head/dp/DP37680), [Thomann Futurelight DMH-160 MK2 £1,111](https://www.thomann.co.uk/futurelight_dmh_160_mk2_led_moving_head.htm), spec lists for Eliminator Stealth Spot]. These use stepper motors and ship with a DMX controller built in [web: Promobile listing]. Second-hand mini heads should be cheap (price not checked). Hack path with least effort: leave the electronics alone, remove the lamp and lens, bolt a mirror disc to the yoke head, and send DMX from Max/MSP or an ESP32 using the 16-bit pan/tilt channels (resolution about 0.008 degrees per step in 16 bit, my arithmetic). This also suits the owner's Max/MSP workflow and the "light fixture reborn as Sun pointer" concept. Caution: motors are made for fast moves, so check slow-speed smoothness on a bench unit.
19. **Mirror scanners and "gobo scanners" (older DJ lights).** [general] A fixed lamp with a motorised tilting mirror: conceptually close to a heliostat. Much limited in range. Second hand.
20. **Motorised spotlight rigs and stage "followspots".** [general] Heavy, not researched.

### F. Solar and building hardware

21. **Dual-axis solar tracker kits (ECO-WORTHY and similar).** Two 12V linear actuators (150 mm and 300 mm, 1500 N), controller, wind sensor, about the real thing [web: [Fab Academy write-up and kit pages](https://fabacademy.org/2025/labs/leon/students/david-fernandez/assignments/week16.html), [FIRGELLI guide](https://www.firgelliauto.com/blogs/tutorials/maximize-energy-how-to-build-a-dual-axis-diy-solar-tracker)]. Strong concept (a Sun tracker tracking the Sun for no energy gain), but travel is limited (about 90 degrees tilt and a limited az sweep, inference) and far too industrial in look.
22. **Slew drives.** Worm-gear azimuth units for trackers; heavy and costly at consumer scale [web: manufacturer listing only, no price found].
23. **Motorised TV wall brackets, window blind and awning motors, garage-door and gate motors.** [general] TV swivel brackets give about 90 to 180 degree az; tubular blind motors give endless slow rotation. Not researched.
24. **Car wing-mirror actuators.** [general] Two tiny geared motors in one housing, cheap, gives about 20 degrees of tilt each way. Good for a tiny expressive mirror but not a pointer.

### G. Toys, robots and curiosities

25. **Robot lamps and Luxo-style desk lamps.** [web: [Hackster](https://www.hackster.io/news/a-diy-luxo-jr-lamp-that-any-pixar-fan-will-appreciate-e919692270b9), [Autonomous Lamp](https://creativebloq.com/ai/meet-lamp-an-alive-pixar-like-robot-that-watches-your-posture-remembers-strangers-faces-and-answers-your-emails)] Lots of servo-based builds; a commercial robot lamp exists. Direct echo of the original UR-style articulated-arm idea.
26. **Robot vacuum lidar turrets, hobby 360 degree lidar.** [general] Endless spinning stage but no tilt.
27. **Hobby brushless gimbals for FPV and cinema cameras (iFlight, Tarot).** [general] Wide tilt, controlled by PWM or serial, quiet.
28. **Galvo mirrors (laser show scanners).** [general] Very small mirrors only, speed far beyond need; mentioned for completeness.

## Satellite dish family, in depth (added 2026-11-02)

Why it is interesting: a dish is already a big round reflector on an az-el mount that tracks something slowly. Swap the LNB and mesh for a polished disc and the dish becomes the Sun pointer, with its own history (a dish "listening" to the sky, now "looking" at the Sun). Visual scale is also right: a 60 to 85 cm dish is far larger than the 305 mm disc, so a smaller dish or a dome is the sensible size.

### Ranges found [web unless marked]

| Donor | Azimuth | Elevation | Notes |
|---|---|---|---|
| Intellian t130N marine TV dome (1.25 m) | unlimited (rotary joint and slip ring) | -15 to +115 deg | 284 lb with radome, so too big. [Retailer listing](https://theyachtrigger.com/products/intellian-t130n-1-25m-maritime-global-satellite-tv-antenna-system-in-v130nx-matching-radome) |
| Intellian t110 (1.05 m) | 680 deg | -15 to +120 deg | [Data sheet](https://www.psicompany.com/man-prod-info/A_Z_Manufacturer/Intellian/Intellian%20T%20Series_/Intellian%20t110/t110%20Data%20Sheet.pdf) |
| Intellian i2 (13 in, 2-axis, for 20 ft boats) | 680 deg | +10 to +80 deg | Small enough for a table, range too narrow. [West Marine](https://www.westmarine.com/intellian-i2-13inch-marine-satellite-tv-antenna-north-america-16230674.html) |
| Intellian B4-619Q (27.5 in dome) | 680 deg | 5 to 90 deg | source page not captured, recheck before relying on it |
| Caravanman Kompakt 4 (motorhome, GPS) | 360 deg | 15 to 62 deg | [Reimo](https://www.reimo.com/en/new-in/camping-tv-satellite-and-multimedia-systems/automatische-sat-anlage/79721/caravanman-kompakt-4-single) |
| Megasat Traveller (motorhome dome) | not stated | 0 to 90 deg | [Reimo](https://www.reimo.com/en/camping-shop/camping-tv-satellite-and-multimedia-systems/automatic-dome-antennas/39026/sat-system-megasat-traveller-man-3) |
| Maxview Target, Omnisat Seeker, Teleco MotoSat | not stated in my results | not stated | Automatic, GPS aided. Datasheets needed. [Maxview Target](https://www.jacksonsleisure.com/caravan-motorhome/maxview-target-fully-automatic-satellite-systems/) |
| Fixed-dish DiSEqC 1.2 motor | about 160 deg (80 east to 80 west) | none (one axis) | See D16 above |
| Dish with DiSEqC motor plus linear actuator | about 160 deg | about 140 deg arc | Under 50 euro for the motor and under 30 euro for the actuator, per [AK-Homberger](https://github.com/AK-Homberger/Satellite-Dish-Positioner) |

### Why marine and motorhome domes fit the brief (inference)

- The marine domes reach **-15 deg**, which is already below the horizon, and **+115 to +120 deg**, which is past the zenith. Their span (130 to 135 deg) is as big as the 124 deg the Sun needs.
- The Sun needs -62 to +62 deg, not -15 to +115. Fix: mount the disc on the dish arm with its normal offset by about 47 deg from the dish boresight (my arithmetic: -15 minus 47 gives -62, and 115 minus 47 gives 68). The pointing direction is then centred on the horizon. The offset only needs a bracket.
- The t130N has unlimited azimuth (no unwind). The 680 deg models need the usual once a day unwind or a reverse sweep (680 deg is a little under two turns, so the daily 360 deg fits with room).
- Problems: the big domes weigh a lot, are made for ships and cost hundreds to thousands new. Second-hand prices not found. A user anecdote says a second-hand unit worked for two years but alignment and elevation faults occurred [web: [Trawler Forum](https://www.trawlerforum.com/goto/post?id=501781)]. Slip rings and worn encoder paint are known wear points in used gear [web: observatory forum, [IceInSpace](https://www.iceinspace.com.au/forum/showthread.php?p=1374614)].
- Smaller motorhome domes are lighter but only reach 15 to 62 deg or 0 to 90 deg elevation: not enough alone, though a 2:1 linkage on the elevation axis (as noted for the cameras) would stretch 62 deg to about 124 deg (inference, with the torque halved).

### DIY and open-source dish rotators (documented, copyable)

- **SatNOGS rotator** (open hardware az-el, steppers plus worm gears, from Libre Space Foundation) [web: [forum thread](https://community.libre.space/t/newbie-interested-in-building-a-satnogs-rotator-with-wayy-too-many-questions/3251), [wiki](https://wiki.satnogs.org/G-5500) for the Yaesu comparison]. Uses the EasyComm protocol.
- **rtl-sdr.com DIY AZ/EL rotator** build write-up [web: [article](https://www.rtl-sdr.com/building-a-diy-azel-antenna-rotator-for-satellite-tracking/)].
- **AK-Homberger Satellite-Dish-Positioner** (ESP-class controller, DiSEqC rotor plus linear actuator) [web: [GitHub](https://github.com/AK-Homberger/Satellite-Dish-Positioner)].
- **VK4GHZ forum** costings: about $70 worm gearbox, about $100 for a stepper with 15:1 gearbox and controller, about $50 for a 24 in linear actuator for elevation [web: [thread](https://vk4ghz.com/forum/viewtopic.php?p=26910)].
- **Software:** gpredict, Hamlib's rotctl and EasyComm are the usual way to drive these [web: Hackster and libre.space threads above]. I believe gpredict can also track the Sun and Moon as targets [general, unchecked], which would give a ready-made front end.
- A NTIA report describes a lab dish with two steppers and absolute optical encoders, a useful reference for the encoder question [web: [NTIA TM-18-531](https://its.ntia.gov/publications/download/TM-18-531.pdf)].
- The control electronics are the easy part, according to one AMSAT reply [web: [AMSAT-BB](https://mail.amsat.org/archives/pipermail/amsat-bb/2013-February/044190.html)]. Matches my view: the mechanics and the look are where the work is.

### Starlink and similar flat terminals

My search found **no teardown or reverse engineering write-ups**, so I cannot say what motors or ranges the Starlink dishes use. [General, unchecked] some Starlink models self-orient with built-in motors, and a flat panel on a motor is visually close to a polished disc. Worth a manual look, and note that tampering with a purchased terminal may breach its terms or the manufacturer's warranty. Leave as an open question.

### Top dish route (inference)

1. Cheap test: DiSEqC rotor (az, about 160 deg) plus a linear actuator, as in AK-Homberger. Proves the maths for under 100 euro but does not cover a full circle.
2. Real thing: a second-hand marine or motorhome dome with the disc offset bracket. Costly in size and weight, so pick the smallest model and check it with the seller.
3. Open hardware: a SatNOGS-style stepper and worm rotator with a disc instead of a dish. Closest to what the goal-post sketches already do, but with a solved mechanism.

## More odd ones (added 2026-11-02)

Marking: **[web]** found in a search; **[general]** from my own knowledge, not checked.

### Time and clock based (conceptual favourites)

29. **24 hour clock movement or synchronous clock motor as the azimuth drive.** [general] The Sun's azimuth turns once a day, so a one-revolution-per-24-hours clock movement turns at the right rate. No electronics needed, and the "clock that tells Sun time" idea. The azimuth is not constant (the Sun's azimuth rate varies through the day, my knowledge), so a pure clock motor drifts by a few degrees against true Sun azimuth; a cam or a stepper correction fixes this. Elevation drive stays separate.
30. **Analemma cam.** [general] A shaped cam on a year shaft produces the seasonal tilt without a computer, as in old sundial-clock mechanisms. Hard to make, but a good sculptural echo of the "analemma" in the sun-path notes.
31. **Barn-door tracker and clock-drive telescope mounts.** [general] Astrophotographers' hand-cranked or motor-driven slow hinge. Direct template for a one-axis lean-over drive.

### Home appliances with a slow turning part

32. **Microwave turntable synchronous motors (about 5 rpm, a few pounds).** [general] Far too fast, but cheap mains gear motors that can be geared down 1000:1 for azimuth.
33. **Rotisserie, kebab and BBQ spit motors, rotating display cabinet motors, shop-window turntables.** [general] Endless rotation, slow, often 1 to 4 rpm.
34. **Gramophone and DJ turntables.** [general] 33 rpm is too fast but the idea of a platter driven by belt or direct drive with a precise speed controller is neat; a record deck is a precision azimuth stage.
35. **Oscillating desk fan gearbox (pan only).** [general] Gives a back and forth sweep, which could add an expressive wobble on top of the main tracking.
36. **Robot vacuum bumper, wheel gearboxes.** [general] Small geared motors with encoders, cheap second hand.

### Display, home and AV hardware

37. **Motorised pan/tilt TV and projector mounts.** Sanus VisionMount, OmniMount Power55 (pan and tilt by remote, IR and RS-232 control), Future Automation motorised ceiling and pole mounts [web: [Rave](https://www.ravepubs.com/?p=10401), [Home Technology Review](https://hometechnologyreview.com/omnimountss-new-hdtv-mount-goes-video/), [Future Automation](https://soundapproach.com/future-automation-pme-motorized-projector-ceiling-mountpm-tech-pdf.html)]. Ready-made serial protocols; ranges not found, and UK pole-mounted versions are built to order with a long lead time.
38. **Bescor MP-101 motorised pan/tilt head** (two independent motors, adjustable speeds, about $200) [web: [listing](https://m.reach.dog/shop/kellards/products/bescor-mp101_mp-101-only)]. A 1990s video head, found second hand; mains or battery powered; no computer interface stated.
39. **Projectors on gimbal stands** (Samsung Freestyle, Anker Nebula) and **Echo Show 10**. [general] Searches did not confirm details; worth checking the Freestyle's tilt and its rotation.
40. **Hospital theatre lights and dentist chair lamps.** [general] Counterbalanced arms with large round heads, wide freedom, no motors. Retrofit steppers. Lovely visual match (a round reflector on a jointed arm), and second hand units appear from clinic closures. Not researched.
41. **Anglepoise-type lamps and monitor arms.** [general] Spring-balanced arms; motorising the joints echoes the original UR-style arm concept at tiny cost.

### Observatory and astronomy extras

42. **Observatory dome rotation drives.** Hobbyists motorise dome rotation with wheels and a controller; commercial small domes (Pulsar) offer motorised rotation [web: [British Astronomical Association](https://britastro.org/?p=584398), [Astroshop Pulsar](https://www.astroshop.eu/instruments/pulsar-observatories-2-2m-2nd-generation/p,85571)]. A dome is a rotating hemisphere with a slit: the slit can be the "Sun window" and the whole thing turns with the Sun. Conceptually rich, physically large.
43. **Heliostat and coelostat designs from solar astronomy.** [general] Two-mirror or one-mirror systems that follow the Sun and send light to a fixed target, historically used in solar observatories. Not researched; this is the "half the angles" case from the handover.
44. **Fixed-slit solar spectrographs and Lunt or Coronado solar telescope mounts.** Not found in search; a Sky-Watcher or similar alt-az mount is the usual carrier.

### Mechanical and industrial oddities

45. **CNC rotary tables, 4th axes and dividing heads.** [general] Precise slow azimuth, worm gear, often with a stepper ready. A tilting rotary table pair is a ready-made az and tilt (trunnion table). Heavy and very industrial.
46. **Lazy Susan bearings and slew bearings.** [general] Bearing part only, to carry the platform in the goal-post sketch.
47. **Theatre revolve and moving stage motors; lighting truss rotators.** [general] Same family as DMX heads but bigger.
48. **Wind-vane and anemometer rotators; weather station mast rotators (TV aerial rotators).** [general] Old-school TV aerial rotators (Channel Master, Yagi) turn slowly with a control box. Cheap used, but az only (they return a pointer on the control box, a nice antique look).
49. **Automatic cat toys and laser pointer toys.** [general] Tiny two-axis servo pointer, entertaining prototype for sun maths.
50. **Kinetic art motors (sculpture kits, Meccano, Technic).** [general] Fast to prototype gear trains.

### Quick rank of the odd list for the Sun pointer (inference)

- **Best concept per pound:** 24 hour clock movement for azimuth, with a stepper for tilt (29).
- **Best visual match:** hospital theatre or dental lamp arm with added steppers (40), and the dish family above.
- **Easiest cheap tests:** TV aerial rotator (48) for az, cat laser pointer (49) for the sun maths, oscillating fan wobble (35).

## Sorting by the hack you could do

- **Leave electronics alone, control from outside** (least effort, most "software hack"): AZ-GTi over WiFi, Insta360 Link over UVC, Tapo or Reolink over ONVIF, DMX moving head from Max/MSP, Yaesu G-5500 with a serial interface.
- **Keep the mechanics, replace the brain** (a good middle path): PTZ dome steppers on a TMC2209 board; moving head steppers; Tapo steppers.
- **Raid for parts** (mechanical hacking): DiSEqC motors as geared joints, blind motors, turntables as azimuth stages, moving-head yoke and bearings.

## My recommendation to try first (inference)

1. **A second-hand DMX moving head** is the only donor class that reaches below the horizon. Cheap enough to be a throw-away experiment, and Max/MSP speaks DMX natively. Ask first whether the look suits the owner; a wash light on a table can be disguised or hidden under a polished disc.
2. **AZ-GTi** if the owner would rather have a proven slow tracker with an app, accepting that it looks like a telescope mount.
3. **Tapo C225 or Reolink dome as a £30 to £60 bench toy** to test the sun maths and the "pointer replaced by a mirror" idea. Not a final answer because of the mechanical tilt limit.

## Open items

- Fetch the AZ-GTi manual and find its altitude and azimuth limits and solar rate.
- Check a second-hand moving head's slow-speed smoothness (a few visits to eBay or a lighting shop would settle it).
- Confirm whether any Tapo or Reolink model exposes ONVIF PTZ with absolute positioning (Tapo had no primary source in my searches).
- Check whether Yaesu rotators can be flipped to reach below the horizon, or whether the owner will accept an elevation floor.
- Not covered: eBay used-market prices, DJI gimbal protocols, Hikvision/Dahua models by number.
