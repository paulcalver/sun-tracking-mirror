# References: related work (web-sourced, 2026-11-03)

## Olafur Eliasson, World illuminator (2014)
- Studio page: https://olafureliasson.net/artwork/world-illuminator-2014/
  - Materials listed: mirror, tripod, steel, motors, control unit, custom electronics, software. No dimensions given.
  - A sun tracker (heliostat) that adjusts a mirror in step with the Sun's apparent motion so the light stays on one fixed point.
  - Shown: test build-up at Studio Olafur Eliasson, Berlin (2013); Bauhaus-Archiv, Berlin courtyard, in the group show Sensing the Future: Laszlo Moholy-Nagy, die Medien und die Kuenste (2014); Fondation Louis Vuitton, Paris (2014, Contact exhibition).
  - Film by SHIMURAbros (fall 2014) on soe.tv, per the studio page.
- Creators Project article (search snippet only; the page could not be fetched because the host is outside this session's allowed network): https://thecreatorsproject.vice.com/blog/olafur-eliasson-harnesses-the-sun-with-giant-kinetic-mirrors . The snippet says the software is node.js on a small Raspberry Pi in the heliostat. Unverified.
- The tripod, round mirror and box shown in the Instagram still are as seen in a screenshot the owner supplied. Mount type and drive are not documented anywhere I found.

## Key difference from this project (inference)
A heliostat sends sunlight to a fixed target, so its mirror normal points halfway between the Sun and the target. This project points the mirror normal at the Sun, so the reflection goes back towards the Sun. The same az/el hardware can do both; only the aiming maths changes.

## Related works found 2026-11-03 (search results; "snippet" = page not opened, unverified)
Art with sun-tracking mirrors (heliostats)
- Philippe Parreno, Untitled, Swiss Re Next, Zurich (2014-2017): ten motorised mirrors (heliostats) cast the Sun's path on atrium walls. https://www.swissre.com/about-us/art-at-swiss-re/artworks/c-parreno-KB1083-untitled.html (snippet; page returned 403)
- Philippe Parreno, Heliotrope (2023, Sharjah): heliostats topped with coloured mirrors. https://v1.sharjahart.org/sharjah-art-foundation/projects/heliotrope-2023 (snippet)
- Project AURORA, 38C3 (Chaos Communication Congress 2024): 40 two-axis mirrors over an entrance, both heliostat and artistic lighting. https://events.ccc.de/congress/2024/hub/assembly/aurora (page opened; maker not named)
- Bigert and Bergstrom, Sunshell: heliostat at the top directs sunlight into the shell. https://www.kth.se/prototype-center/projects/projects/sunshell-1.1172078 (snippet)
- Janet Saad Cook, Sun Drawing, Boston University Photonics Center: heliostat feeds an atrium artwork. https://www.bu.edu/photonics/community/photonics-center-art/ (snippet)
- Joseph McShane, Language of Light, Phoenix (1991): automated tracker sends daylight into a library. https://phoenix.gov/arts/public-art-program/explore-the-collection/languageoflight (snippet)
- Olafur Eliasson, Your sun machine (1997): a round hole in the ceiling of the Marc Foxx Gallery, Los Angeles; the Sun's beam crosses the room. No mirror or motor. https://www.olafureliasson.net/artwork/your-sun-machine-1997 (snippet)
Heliostats at town scale
- Rjukan, Norway: three computer controlled heliostats about 450 m above the town light the market square (since October 2013). Viganella, Italy: one fixed steel mirror (2006). https://visitrjukan.com/en/p/the-giant-sun-mirrors-in-rjukan/ and https://www.amusingplanet.com/2015/07/the-giant-sun-mirrors-of-rjukan.html (snippets; sources disagree on mirror sizes)
Maker builds
- ESP32-S3 indoor heliostat (winter sunlight into rooms), sun position fetched from an online astronomy API, recalculated every minute. https://www.hackster.io/news/it-s-all-sunshine-and-heliostats-6ce78f8e9c1c (snippet; page returned 403)
- Time Sink Studio, Living Mirror: ESP32, stepper control, MQTT, maps mirror angle to spot position (not sun tracking). https://www.hackster.io/timesinkstudio/draw-with-light-living-mirror-29ed37 (snippet)
