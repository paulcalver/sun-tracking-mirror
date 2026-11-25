#!/usr/bin/env python3
"""Host data pipe for firmware/spinning_mirror_sun.

Owns the clock (LIVE or REPLAY at a chosen date and speed), reads a replay file,
normalises the values with percentile tables and sends `feed` lines at about 1 Hz.
The MAPPING to rpm / jitter lives on the device, not here.

    python3 sun_feed.py --dry-run                      # fake device, no hardware
    python3 sun_feed.py --port /dev/cu.usbmodem1101    # real device (needs pyserial)
    python3 sun_feed.py --make-fixture                 # rewrite the synthetic fixture

Terminal commands (type and press Enter):
    date 2024-05-10[T12:00]   jump the replay clock (UTC)       +1h -30m +2d   step it
    play | pause              start / stop the replay clock     speed 60       replay speed (1 = real time)
    live                      follow real time (live feeds are a STUB: nothing is sent yet)
    flare 0..3                send a test flare onset now       status         ask the device
    send <raw line>           send any raw line to the device   help | quit

Nothing here is verified on hardware. Percentile tables below are PLACEHOLDERS.
No personal data is sent anywhere; the only network code would be the live-feed
stub, which does nothing yet.
"""
import argparse, bisect, csv, math, os, queue, random, sys, threading, time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "synthetic_two_days.csv")
UTC = timezone.utc

# ---- PLACEHOLDER percentile tables (p5, p50, p95, p99) ------------------------
# Replace with the tables from the Nasa Research repo (1975 to 2016) when they
# arrive. These are rough guesses so the pipeline can be exercised.
PERCENTILES = {
    "wind_kms": (300.0, 400.0, 600.0, 700.0),     # PLACEHOLDER solar wind speed, km/s
    "kp":       (0.3, 1.3, 4.3, 6.0),             # PLACEHOLDER Kp index
}
# GOES long-band X-ray flux thresholds (W/m2): C, M, X. These are the standard
# class boundaries, not placeholders.
FLARE_THRESHOLDS = ((1e-6, 1), (1e-5, 2), (1e-4, 3))


def normalise(name, value):
    """Percentile -> 0..1 : p5 -> 0, p50 -> 0.5, p95 -> 0.95, p99 -> 1.0 (piecewise linear)."""
    p5, p50, p95, p99 = PERCENTILES[name]
    xs, ys = (p5, p50, p95, p99), (0.0, 0.5, 0.95, 1.0)
    if value <= xs[0]:
        return 0.0
    if value >= xs[-1]:
        return 1.0
    i = bisect.bisect_right(xs, value) - 1
    return ys[i] + (ys[i + 1] - ys[i]) * (value - xs[i]) / (xs[i + 1] - xs[i])


def flare_class(flux):
    c = 0
    for thr, cls in FLARE_THRESHOLDS:
        if flux >= thr:
            c = cls
    return c


# ---- clock -----------------------------------------------------------------
class Clock:
    """LIVE = real UTC time. REPLAY = a simulated UTC time that advances `speed` x real time."""
    def __init__(self, start=None, speed=1.0, playing=True):
        self.live = start is None
        self.speed, self.playing = speed, playing
        self.epoch = 0          # bumps on every jump, so flare detection does not span a jump
        self._sim = start or datetime.now(UTC)
        self._wall = time.monotonic()
        self.jump_to = self._sim

    def now(self):
        if self.live:
            return datetime.now(UTC)
        if self.playing:
            t = time.monotonic()
            self._sim += timedelta(seconds=(t - self._wall) * self.speed)
            self._wall = t
        else:
            self._wall = time.monotonic()
        return self._sim

    def set_date(self, dt):
        self.live = False
        self.epoch += 1
        self.jump_to = dt
        self._sim, self._wall = dt, time.monotonic()

    def go_live(self):
        self.live = True
        self.epoch += 1
        self.jump_to = datetime.now(UTC)

    def step(self, delta):
        self.set_date(self.now() + delta)

    def set_speed(self, s):
        self.now(); self.speed = s

    def pause(self, on):
        self.now(); self.playing = not on

    def label(self):
        if self.live:
            return "LIVE"
        return "REPLAY %s x%g%s" % (self._sim.strftime("%Y-%m-%dT%H:%M:%SZ"), self.speed, "" if self.playing else " (paused)")


def parse_when(text):
    text = text.strip().rstrip("Zz")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            pass
    raise ValueError("bad date %r (use YYYY-MM-DD or YYYY-MM-DDTHH:MM)" % text)


def parse_step(text):
    unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(text[-1:])
    if unit is None:
        raise ValueError("step like +1h, -30m, +2d")
    return timedelta(seconds=float(text[:-1]) * unit)


# ---- data sources ------------------------------------------------------------
class ReplayData:
    """Minute-resolution CSV: time_utc,wind_kms,kp,xray_wm2 (blank = missing)."""
    def __init__(self, path):
        self.t, self.rows = [], []
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                self.t.append(parse_when(r["time_utc"]).timestamp())
                self.rows.append(tuple(float(r[k]) if r[k].strip() else None
                                       for k in ("wind_kms", "kp", "xray_wm2")))
        self.start = datetime.fromtimestamp(self.t[0], UTC)
        self.end = datetime.fromtimestamp(self.t[-1], UTC)

    def _idx(self, ts):
        i = bisect.bisect_right(self.t, ts) - 1
        return i if 0 <= i < len(self.t) and ts - self.t[i] <= 600 else None   # >10 min gap = missing

    def sample(self, dt):
        """-> (wind_kms, kp) at dt, or None when the file has no data there."""
        i = self._idx(dt.timestamp())
        if i is None:
            return None
        w, kp, _ = self.rows[i]
        return None if w is None or kp is None else (w, kp)

    def max_flare(self, t0, t1):
        """Highest flare class whose onset (an upward threshold crossing) lies in (t0, t1]."""
        lo = bisect.bisect_right(self.t, t0.timestamp())
        hi = bisect.bisect_right(self.t, t1.timestamp())
        best = 0
        for i in range(max(lo, 1), hi):
            a, b = self.rows[i - 1][2], self.rows[i][2]
            if a is None or b is None:
                continue                      # a gap is not a flare
            ca, cb = flare_class(a), flare_class(b)
            if cb > ca:
                best = max(best, cb)
        return best


class LiveData:
    """STUB. Live feed fetching is not implemented: the feed list, cadence and latency are still
    to be confirmed by the Nasa Research repo. It returns no data, so in LIVE mode nothing is
    sent and the device's watchdog eases to idle. Do not add personal details to any request."""
    def sample(self, dt):
        return None

    def max_flare(self, t0, t1):
        return 0


# ---- fixture ---------------------------------------------------------------
def make_fixture(path):
    """Synthetic, NOT real data. Day 1 quiet, day 2 stormy, with flare onsets (minute resolution)."""
    rng = random.Random(7)
    day1 = datetime(2000, 1, 1, tzinfo=UTC)
    flares = {  # minute-of-file -> peak flux, with a 20 minute decay
        6 * 60 + 15: 1.5e-6,                                   # C1.5 on the quiet day
        1440 + 3 * 60 + 40: 3e-6, 1440 + 9 * 60 + 5: 2.4e-5,   # C3, M2.4
        1440 + 14 * 60 + 30: 1.2e-4, 1440 + 20 * 60 + 10: 6e-5,  # X1.2, M6
    }
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "wind_kms", "kp", "xray_wm2"])
        wind, kp = 380.0, 1.0
        for m in range(2 * 1440):
            storm = m >= 1440
            hour = (m % 1440) / 60.0
            if not storm:
                tw, tk = 380 + 40 * math.sin(hour / 24 * 6.283), 1.0 + 0.3 * math.sin(hour / 4)
            else:   # storm ramps up from 05:00, peaks around 14:00, eases late
                s = max(0.0, min(1.0, (hour - 5) / 9.0)) if hour < 14 else max(0.2, 1.0 - (hour - 14) / 12.0)
                tw, tk = 420 + 380 * s, 1.5 + 6.5 * s
            wind += (tw - wind) * 0.05 + rng.gauss(0, 3)
            kp = max(0.0, min(9.0, kp + (tk - kp) * 0.03 + rng.gauss(0, 0.03)))
            flux = 2e-7 if not storm else 8e-7
            for fm, peak in flares.items():
                d = m - fm
                if d >= 0:
                    flux += peak * (1.0 if d < 3 else math.exp(-(d - 3) / 20.0))
                if d == -1:
                    flux = min(flux, 5e-7)       # clean upward crossing at the onset minute
            t = day1 + timedelta(minutes=m)
            w.writerow([t.strftime("%Y-%m-%dT%H:%M:%SZ"), "%.1f" % wind, "%.2f" % kp, "%.3e" % flux])


# ---- serial (real and fake) ---------------------------------------------------
class RealSerial:
    def __init__(self, port, baud):
        import serial                                   # pip install pyserial
        self.s = serial.Serial(port, baud, timeout=0.1)
        self._buf = b""

    def write_line(self, line):
        self.s.write((line + "\n").encode())

    def read_lines(self):
        self._buf += self.s.read(4096)
        out = []
        while b"\n" in self._buf:
            ln, self._buf = self._buf.split(b"\n", 1)
            if ln.strip():
                out.append(ln.decode(errors="replace").strip())
        return out

    def close(self):
        self.s.close()


class FakeDevice:
    """Dry-run stand-in for the firmware. Parses the same lines and mirrors the device's mapping
    and watchdog APPROXIMATELY (constants copied by hand from the .ino), so a dry run shows
    what the motors would be asked to do. It is NOT the firmware."""
    RPM_MIN, RPM_MAX, JIT_CALM, JIT_STORM, CAP = 40.0, 200.0, 0.10, 0.60, 300.0
    SURGE = {1: (0.60, 4.0), 2: (0.80, 7.0), 3: (0.80, 10.0)}

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.out = queue.Queue()
        self.mode, self.wind, self.storm, self.date = "manual", 0.0, 0.0, "-"
        self.last_feed, self.enabled, self.surge_until, self.surge = None, False, 0.0, 0.0
        self.wd_idle, self.wd_stop, self.flare = 120.0, 1800.0, 0
        self.out.put("spinning-mirror SUN firmware (FAKE, dry run)")

    def write_line(self, line):
        p = line.split()
        if not p:
            return
        c = p[0].lower()
        now = self.clock()
        if c == "mode" and len(p) > 1:
            self.mode = p[1]
            self.last_feed = now
            self.out.put("ok mode " + p[1])
        elif c == "wd" and len(p) > 1:
            self.wd_idle = float(p[1]); self.out.put("ok wd %.0f" % self.wd_idle)
        elif c == "feed" and len(p) > 1:
            k, v = p[1].lower(), (p[2] if len(p) > 2 else None)
            if k == "wind": self.wind = min(1, max(0, float(v)))
            elif k == "storm": self.storm = min(1, max(0, float(v)))
            elif k == "flare":
                self.flare = int(v)
                if self.flare in self.SURGE:
                    self.surge, hold = self.SURGE[self.flare]; self.surge_until = now + hold
            elif k == "date": self.date = v
            if self.mode == "sun":
                self.enabled = True
            self.last_feed = now
            self.out.put("ok feed")
        elif c == "status":
            age = None if self.last_feed is None else now - self.last_feed
            state = "off" if self.mode != "sun" else "stopped" if age is not None and age >= self.wd_stop \
                else "idle" if age is not None and age >= self.wd_idle else "live"
            rpm, jit = self.target(state, now)
            self.out.put("status mode=%s feed_age_ms=%d wd_state=%s wind=%.2f storm=%.2f flare=%d date=%s "
                         "rpm_set=%.1f jit=%.2f (approx)" % (self.mode, -1 if age is None else age * 1000, state,
                                                             self.wind, self.storm, self.flare, self.date, rpm, jit))
        else:
            self.out.put("ok (fake)")

    def target(self, state, now):
        if state == "stopped":
            return 0.0, 0.0
        if state == "idle":
            return 20.0, 0.10
        jit = max(self.JIT_CALM + (self.JIT_STORM - self.JIT_CALM) * self.storm, self.surge if now < self.surge_until else 0.0)
        rpm = min(self.RPM_MIN + (self.RPM_MAX - self.RPM_MIN) * self.wind, self.CAP / (1 + 2 * jit))
        return rpm, jit

    def read_lines(self):
        out = []
        while not self.out.empty():
            out.append(self.out.get())
        return out

    def close(self):
        pass


# ---- main loop -------------------------------------------------------------
HELP = __doc__.split("Terminal commands")[1].split("Nothing here")[0]


def handle_command(text, clock, dev, state):
    p = text.split()
    if not p:
        return True
    c = p[0].lower()
    try:
        if c in ("quit", "exit", "q"):
            return False
        elif c == "date":
            clock.set_date(parse_when(p[1]))
        elif c[0] in "+-" and len(c) > 1:
            clock.step(parse_step(c))
        elif c == "play":
            clock.pause(False)
        elif c == "pause":
            clock.pause(True)
        elif c == "speed":
            clock.set_speed(max(0.0, float(p[1])))
        elif c == "live":
            clock.go_live()
        elif c == "flare":
            state["test_flare"] = int(p[1])
        elif c == "status":
            dev.write_line("status")
        elif c == "send":
            dev.write_line(text.split(None, 1)[1])
        elif c == "help":
            print(HELP)
        else:
            print("unknown command (help)")
    except (IndexError, ValueError) as e:
        print("error:", e)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", help="serial port of the XIAO (e.g. /dev/cu.usbmodem1101)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--dry-run", action="store_true", help="fake device, no hardware, no pyserial needed")
    ap.add_argument("--data", default=FIXTURE, help="replay CSV (default: the synthetic fixture)")
    ap.add_argument("--date", help="start replay at this UTC date (default: LIVE)")
    ap.add_argument("--speed", type=float, default=1.0, help="replay speed, 1 = real time (60 = a minute per second)")
    ap.add_argument("--rate", type=float, default=1.0, help="feed lines per second (default 1)")
    ap.add_argument("--wd", type=float, help="send `wd <s>` to the device at start")
    ap.add_argument("--no-mode", action="store_true", help="do not send `mode sun` at start")
    ap.add_argument("--script", help="commands to run instead of reading the terminal, ';' separated, "
                                     "e.g. 'speed 600;date 2000-01-02T04:00;wait 5;quit'")
    ap.add_argument("--duration", type=float, help="stop after this many wall seconds")
    ap.add_argument("--make-fixture", action="store_true", help="rewrite the synthetic fixture and exit")
    ap.add_argument("-v", "--verbose", action="store_true", help="show the device's `ok feed` replies too")
    a = ap.parse_args()

    if a.make_fixture:
        os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
        make_fixture(FIXTURE)
        print("wrote", FIXTURE)
        return 0
    if not a.dry_run and not a.port:
        ap.error("give --port or --dry-run")

    data = ReplayData(a.data) if os.path.exists(a.data) else None
    live_data = LiveData()
    clock = Clock(parse_when(a.date) if a.date else None, a.speed)
    if data:
        print("replay data: %s .. %s UTC (%s)" % (data.start, data.end, os.path.basename(a.data)))
    else:
        print("no replay file at", a.data, "(LIVE only, and live is a stub)")
    dev = FakeDevice() if a.dry_run else RealSerial(a.port, a.baud)

    cmds = queue.Queue()
    if a.script:
        for c in a.script.split(";"):
            cmds.put(c.strip())
    else:
        threading.Thread(target=lambda: [cmds.put(l.strip()) for l in sys.stdin], daemon=True).start()

    if not a.no_mode:
        dev.write_line("mode sun")
    if a.wd:
        dev.write_line("wd %g" % a.wd)
    state = {"test_flare": 0, "epoch": 0}
    prev = clock.now()
    t_end = time.monotonic() + a.duration if a.duration else None
    wait_until, nxt = 0.0, time.monotonic()
    run = True
    try:
        while run and (t_end is None or time.monotonic() < t_end):
            # commands (a script `wait N` pauses the script, not the feed)
            while run and time.monotonic() >= wait_until and not cmds.empty():
                c = cmds.get()
                if c.startswith("wait "):
                    wait_until = time.monotonic() + float(c.split()[1])
                else:
                    run = handle_command(c, clock, dev, state)
            if a.script and cmds.empty() and time.monotonic() >= wait_until and not a.duration:
                run = False
            for ln in dev.read_lines():
                if a.verbose or not ln.startswith("ok feed"):
                    print("  device:", ln)
            if time.monotonic() < nxt:
                time.sleep(0.02)
                continue
            nxt += 1.0 / a.rate
            now = clock.now()
            if clock.epoch != state.get("epoch"):
                state["epoch"] = clock.epoch
                prev = clock.jump_to
            src = live_data if clock.live else data
            s = src.sample(now) if src else None
            flare = max(state["test_flare"], src.max_flare(prev, now) if (src and not clock.live) else 0)
            state["test_flare"] = 0
            if s is None and not flare:
                if not state.get("nodata"):
                    print("%s | no data here: sending nothing (the device watchdog will ease to idle)" % clock.label())
                state["nodata"] = True
                prev = now
                continue
            state["nodata"] = False
            if s:
                w, kp = s
                dev.write_line("feed wind %.3f" % normalise("wind_kms", w))
                dev.write_line("feed storm %.3f" % normalise("kp", kp))
                info = "wind %.0f km/s -> %.2f  kp %.1f -> %.2f" % (w, normalise("wind_kms", w), kp, normalise("kp", kp))
            else:
                dev.write_line("feed ping")
                info = "ping"
            if flare:
                dev.write_line("feed flare %d" % flare)
                info += "  FLARE class %d (%s)" % (flare, "CMX"[flare - 1])
            dev.write_line("feed date " + ("LIVE" if clock.live else now.strftime("%Y-%m-%dT%H:%M:%SZ")))
            print("%s | %s" % (clock.label(), info))
            prev = now
    except KeyboardInterrupt:
        pass
    finally:
        # Do not command the motors on exit: the device's watchdog eases it to idle by itself.
        dev.close()
    print("bye (the device eases to idle after its watchdog time)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
