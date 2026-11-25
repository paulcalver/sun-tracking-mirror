# Spinning-mirror sun firmware (`spinning_mirror_sun.ino`)

A second sketch beside `../spinning_mirror/` (which is untouched and stays the main one). It is a copy of that motion core (100 kHz lock-step timer, accel ramp, `MAX_SPINDLE_RPM` 300 hard cap, `ou` jitter, ESP-NOW remote receiver, every old serial command, same pins, `NUM_MOTORS` 1 as the original) with **sun mode** added: a host sends normalised space-weather signals and the **mapping to motion lives on the device**.

## Status: read this first

- **Compiles** for the XIAO ESP32-S3 with esp32 core 3.3.12 (Arduino IDE's bundled `arduino-cli`):
  `arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:CDCOnBoot=cdc firmware/spinning_mirror_sun`
- **Nothing has run on hardware**, not this sketch and not the sketch it copies. Untested: the sun mapping and slews by eye and ear, the flare surge, the watchdog timings, the remote takeover and resume, driver start from the first feed, and the whole motion core. The dry-run host test used a Python stand-in for the device, not this code.
- First bench runs: **one motor, low rpm, no ring**. Use `mode manual`, `rpm 30`, then try `mode sun` with a calm replay date.
- Boot state: manual mode, drivers off, `AUTOSTART 0`. Set `BOOT_IN_SUN_MODE 1` to boot into sun mode (drivers still stay off until the first `feed` arrives).

## Serial protocol (115200, one command per line, `;` also separates)

| Command | Effect |
|---|---|
| `mode sun` / `mode manual` | sun: feed lines drive `rpm`, `jit`, `jtau` every 20 ms. The first `feed` after `mode sun` enables the drivers (soft start). In sun mode `rpm`, `jit`, `jtau`, `jitter`, `jmode`, `jrev` are refused (`err sun mode drives ...`). `stop`, `estop`, `enable 0` also switch to manual, so a later feed cannot undo them. `jrev 0` is set on entering sun. |
| `feed wind <0..1>` | centre speed, `SUN_RPM_MIN` 40 to `SUN_RPM_MAX` 200 rpm |
| `feed storm <0..1>` | `jit` 0.10 (calm) to 0.60 (storm); `jtau` 0.5 s (calm) to 0.15 s (storm) |
| `feed flare <0..3>` | one onset event: 0 none, 1 C, 2 M, 3 X. Visible surge: `jit` rises to 0.6 (C, held 4 s), 0.8 (M, 7 s), 0.8 (X, 10 s), then decays with a 3 s time constant; `jtau` shrinks toward 0.12 during the surge. A bigger class takes over, a hold is never shortened |
| `feed date <ISO or LIVE>` | display/status only (the hook for a later dial plus screen unit) |
| `feed ping` | heartbeat only |
| `wd <5..3600>` | watchdog: no `feed` line for this long (default 120 s) = ease to idle (20 rpm, `jit` 0.1, `jtau` 0.5) through the same slew limits, not an abrupt stop |
| `wdstop <s>` | no feed for this long (default 1800 s) = `stop` and release the drivers. The next `feed` restarts it. Watchdog exists only in this sketch |
| `resume <s>` | see the remote dial below (default 600, 0 = never) |
| `status` | old fields unchanged, then `mode`, `feed_age_ms`, `wd`, `wdstop`, `wd_state` (live/idle/stopped, `off` in manual), `wind`, `storm`, `flare`, `flare_age_ms`, `surge`, `date`, `sun_rpm`, `sun_jit`, `resume` appended |

Any valid `feed` line (including `ping` and `date`) is a heartbeat.

## Safety

- `MAX_SPINDLE_RPM` 300 and the accel cap are unchanged and still enforced in the ramp and in the final step-rate conversion.
- Sun mode additionally clamps `rpm * (1 + 2 * jit)` to the cap, and rpm to the 200 rpm working ceiling. At `jit` 0.8 this holds rpm to about 115, so a flare in fast wind slows the centre speed while the wobble grows. All values are slew-limited (rpm 8 rpm/s, `jit` 0.1 per s, `jtau` 0.2 s per s; flare rise 0.6 jit/s), because the accel ramp (about 955 rpm/s) does not smooth slow drift.
- Runs 24 hours: no daylight gate.
- Does not join Wi-Fi (that would break ESP-NOW on channel 1). Data fetching stays on the host.

## Remote dial

Unchanged receiver. The first time a pot moves past its dead band while in sun mode the sketch prints `sun: remote dial took over (mode manual)` and the dial drives as in the old sketch. Sun mode resumes when you send `mode sun`, or by itself `resume` seconds (default 600) after the dial was last moved; the speed and jitter then slew back to the sun values from where the dial left them. `resume 0` turns the automatic return off. Stop/go on the remote sends speed 0, which also counts as a takeover.

## Host script: `../host/sun_feed.py`

A clock that is LIVE or REPLAY (chosen date and speed), a replay file, percentile normalisation, `feed` lines at about 1 Hz and a terminal UI (`date`, `+1h`, `play`, `pause`, `speed`, `live`, `flare`, `status`, `send`). `--dry-run` uses a fake device so it runs with no hardware and no pyserial; a real run needs `pip install pyserial` and `--port`.

```
python3 firmware/host/sun_feed.py --dry-run --date 2000-01-02T14:00 --speed 600
python3 firmware/host/sun_feed.py --port /dev/cu.usbmodem1101 --date 2000-01-01T08:00
```

Placeholders and stubs to replace when the Nasa Research repo delivers: the **percentile tables** in `PERCENTILES` (invented), the **replay file** (`fixtures/synthetic_two_days.csv`: synthetic, a quiet and a storm day with flare onsets, regenerate with `--make-fixture`), and **live fetching** (`LiveData`, a stub: in LIVE nothing is sent, so the device idles). Flares are detected as upward X-ray flux crossings of the C/M/X thresholds, not from counts. A gap in the data sends nothing. The real serial path has not been tried (pyserial is not installed here); the host never commands the motors on exit and relies on the device watchdog.

## Not in this version

The dial plus small screen unit (date or LIVE). The `feed date` line is the hook; a wired link is preferred over Wi-Fi so ESP-NOW is not disturbed. Tuning of the mapping by ear in replay is still to do.
