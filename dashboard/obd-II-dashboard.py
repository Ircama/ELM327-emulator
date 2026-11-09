#!/usr/bin/env python3
"""
Console OBD-II dashboard (curses) for an ELM327 over TCP.

Connects to localhost:35000 by default (e.g. an ELM327 emulator or an ESP32/WiFi ELM327).
Uses only the Python standard library.

Usage:
    python3 obd-II-dashboard.py
    python3 obd-II-dashboard.py --host 192.168.0.10 --port 35000 --interval 0.5
    python3 obd-II-dashboard.py --record 0D=speed.csv --record 0C,05=engine.csv
    python3 obd-II-dashboard.py --record all=session.csv
    python3 obd-II-dashboard.py --list-pids

Recording (--record PIDS=FILE, repeatable):
    PIDS is a comma separated list of PID codes (see --list-pids) or "all"
    (= every parameter enabled on the dashboard). Samples are appended to FILE
    as CSV, one row per sample:
        timestamp,unix_time,pid,name,value,unit
    Recorded PIDs are always polled, also in chart focus mode.

Keys (main screen):
    ↑↓ select parameter Enter  open live chart
    q  quit             m  settings menu
    +  slower           -  faster (refresh interval)
    r  reset min/max    c  reconnect

Keys (chart view):
    ←→ / [ ]  time window          ↑↓  previous / next parameter
    a  autoscale on/off            f   focus mode (poll only this PID)
    +/- refresh interval           c   clear history
    q / Esc / Backspace  back
"""

import argparse
import csv
import curses
import datetime
import json
import locale
import os
import socket
import threading
import time
from collections import deque

CONFIG_PATH = os.path.expanduser("~/.config/obd_dash.json")

# key: (name, unit, byte count, formula, format, bar max or None)
PIDS = {
    "0D": ("Speed", "km/h", 1, lambda b: b[0], "{:.0f}", 200),
    "0C": ("Engine RPM", "rpm", 2, lambda b: (b[0] * 256 + b[1]) / 4, "{:.0f}", 7000),
    "04": ("Engine load", "%", 1, lambda b: b[0] * 100 / 255, "{:.1f}", 100),
    "11": ("Throttle position", "%", 1, lambda b: b[0] * 100 / 255, "{:.1f}", 100),
    "05": ("Coolant temp", "°C", 1, lambda b: b[0] - 40, "{:.0f}", None),
    "0F": ("Intake air temp", "°C", 1, lambda b: b[0] - 40, "{:.0f}", None),
    "46": ("Ambient air temp", "°C", 1, lambda b: b[0] - 40, "{:.0f}", None),
    "0B": ("Manifold pressure (MAP)", "kPa", 1, lambda b: b[0], "{:.0f}", None),
    "10": ("Mass air flow (MAF)", "g/s", 2, lambda b: (b[0] * 256 + b[1]) / 100, "{:.2f}", None),
    "2F": ("Fuel level", "%", 1, lambda b: b[0] * 100 / 255, "{:.1f}", 100),
    "42": ("Control module voltage", "V", 2, lambda b: (b[0] * 256 + b[1]) / 1000, "{:.2f}", None),
    "1F": ("Engine run time", "s", 2, lambda b: b[0] * 256 + b[1], "{:.0f}", None),
    "RV": ("Battery voltage (ELM)", "V", 0, None, "{:.1f}", None),
    # fuel system / mixture
    "06": ("Short term fuel trim B1", "%", 1, lambda b: (b[0] - 128) * 100 / 128, "{:+.1f}", None),
    "07": ("Long term fuel trim B1", "%", 1, lambda b: (b[0] - 128) * 100 / 128, "{:+.1f}", None),
    "44": ("Commanded lambda", "λ", 2, lambda b: (b[0] * 256 + b[1]) * 2 / 65536, "{:.3f}", None),
    # 4 data bytes: lambda (AB) + sensor voltage (CD); only lambda is shown
    "24": ("O2 S1 lambda (wideband)", "λ", 4, lambda b: (b[0] * 256 + b[1]) * 2 / 65536, "{:.3f}", None),
    # 2 data bytes: voltage (A) + short term trim (B, 0xFF = not used); only voltage is shown
    "15": ("O2 B1S2 voltage", "V", 2, lambda b: b[0] / 200, "{:.3f}", None),
    # ignition / load
    "0E": ("Timing advance", "°", 1, lambda b: b[0] / 2 - 64, "{:.1f}", None),
    "43": ("Absolute load", "%", 2, lambda b: (b[0] * 256 + b[1]) * 100 / 255, "{:.1f}", 100),
    # electronic throttle
    "45": ("Relative throttle position", "%", 1, lambda b: b[0] * 100 / 255, "{:.1f}", 100),
    "47": ("Absolute throttle position B", "%", 1, lambda b: b[0] * 100 / 255, "{:.1f}", 100),
    "4C": ("Commanded throttle actuator", "%", 1, lambda b: b[0] * 100 / 255, "{:.1f}", 100),
    # exhaust / catalyst
    "3C": ("Catalyst temp B1S1", "°C", 2, lambda b: (b[0] * 256 + b[1]) / 10 - 40, "{:.0f}", None),
    "3E": ("Catalyst temp B1S2", "°C", 2, lambda b: (b[0] * 256 + b[1]) / 10 - 40, "{:.0f}", None),
    # environment
    "33": ("Barometric pressure", "kPa", 1, lambda b: b[0], "{:.0f}", None),
    # derived values (computed from other PIDs, see DERIVED)
    "FH": ("Fuel consumption (petrol)", "L/h", 0, None, "{:.2f}", None),
    "FK": ("Fuel consumption (petrol)", "L/100km", 0, None, "{:.1f}", None),
}
PID_ORDER = list(PIDS.keys())

# Petrol: stoichiometric air/fuel ratio and fuel density [g/L].
AFR_PETROL = 14.7
FUEL_DENSITY = 745.0
MIN_SPEED_L100 = 3          # below this speed L/100km makes no sense (division by ~0)


def _fuel_lph(v):
    return v["10"] * 3600 / (AFR_PETROL * FUEL_DENSITY)


def _fuel_l100(v):
    if v["0D"] < MIN_SPEED_L100:
        return None
    return _fuel_lph(v) * 100 / v["0D"]


# key: (PIDs that must be read first, function(dict pid -> value) -> value or None)
DERIVED = {
    "FH": (["10"], _fuel_lph),
    "FK": (["10", "0D"], _fuel_l100),
}
DEFAULT_ENABLED = ["0D", "0C", "05", "04", "11", "RV"]
INTERVALS = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
WINDOWS = [10, 30, 60, 120, 300, 600]   # chart time windows in seconds
HISTORY_LEN = 10000                     # samples kept per PID (~16 min at 0.1 s)
BLOCKS = " ▁▂▃▄▅▆▇█"                    # 1/8-step vertical blocks for the chart


# --------------------------------------------------------------------- ELM327

class ELM327:
    """Minimal ELM327 client over TCP."""

    def __init__(self, host, port, timeout=3.0):
        self.host, self.port, self.timeout = host, port, timeout
        self.sock = None
        self.version = "?"

    def connect(self):
        self.close()
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.sock.settimeout(self.timeout)
        lines = self.query("ATZ", timeout=5.0)
        self.version = next((l for l in lines if "ELM" in l.upper()), " ".join(lines) or "?")
        for cmd in ("ATE0", "ATL0", "ATS0", "ATH0", "ATSP0"):
            self.query(cmd)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None

    def query(self, cmd, timeout=None):
        if not self.sock:
            raise ConnectionError("not connected")
        self.sock.sendall((cmd + "\r").encode())
        buf = b""
        deadline = time.time() + (timeout or self.timeout)
        while b">" not in buf:
            if time.time() > deadline:
                raise TimeoutError(f"timeout on {cmd}")
            try:
                chunk = self.sock.recv(1024)
            except socket.timeout:
                continue
            if not chunk:
                raise ConnectionError("server closed the connection")
            buf += chunk
        text = buf.decode(errors="ignore").replace(">", "").replace("\n", "\r")
        lines = [l.strip() for l in text.split("\r") if l.strip()]
        # drop the command echo and intermediate status messages
        return [l for l in lines
                if l.replace(" ", "").upper() != cmd.upper() and not l.upper().startswith("SEARCHING")]

    def read_pid(self, pid, nbytes):
        lines = self.query("01" + pid)
        for line in lines:
            hexstr = line.replace(" ", "").upper()
            idx = hexstr.find("41" + pid)
            if idx >= 0:
                data = hexstr[idx + 4: idx + 4 + nbytes * 2]
                if len(data) == nbytes * 2:
                    return bytes.fromhex(data)
        raise ValueError(" ".join(lines) or "no response")

    def read_voltage(self):
        lines = self.query("ATRV")
        for line in lines:
            try:
                return float(line.upper().replace("V", "").strip())
            except ValueError:
                continue
        raise ValueError(" ".join(lines) or "no response")


# -------------------------------------------------------------------- settings

class Settings:
    def __init__(self, host="localhost", port=35000, interval=1.0, enabled=None):
        self.host = host
        self.port = port
        self.interval = interval
        self.enabled = list(enabled or DEFAULT_ENABLED)

    @classmethod
    def load(cls):
        try:
            with open(CONFIG_PATH) as f:
                d = json.load(f)
            s = cls(d.get("host", "localhost"), int(d.get("port", 35000)),
                    float(d.get("interval", 1.0)), d.get("enabled"))
            s.enabled = [p for p in s.enabled if p in PIDS]
            return s
        except (OSError, ValueError):
            return cls()

    def save(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"host": self.host, "port": self.port,
                       "interval": self.interval, "enabled": self.enabled}, f, indent=2)


# ------------------------------------------------------------------- recorder

class Recorder:
    """Appends samples to CSV files (long format: one row per sample)."""

    HEADER = ["timestamp", "unix_time", "pid", "name", "value", "unit"]

    def __init__(self, settings):
        self.settings = settings
        self.targets = []         # list of (set of PIDs or None for "all", path)
        self._files = {}          # abs path -> (file, csv writer)

    @staticmethod
    def parse(spec):
        """Parse 'PID[,PID...]=FILE' or 'all=FILE' into (set or None, path)."""
        left, sep, path = spec.partition("=")
        if not sep or not left.strip() or not path.strip():
            raise ValueError(f"expected PIDS=FILE, got '{spec}'")
        if left.strip().lower() == "all":
            return None, path.strip()
        pids = {p.strip().upper() for p in left.split(",") if p.strip()}
        unknown = sorted(p for p in pids if p not in PIDS)
        if unknown:
            raise ValueError(f"unknown PID(s): {', '.join(unknown)} (see --list-pids)")
        return pids, path.strip()

    def add(self, pids, path):
        key = os.path.abspath(os.path.expanduser(path))
        if key not in self._files:
            os.makedirs(os.path.dirname(key), exist_ok=True)
            new = not os.path.exists(key) or os.path.getsize(key) == 0
            f = open(key, "a", newline="", encoding="utf-8")
            w = csv.writer(f)
            if new:
                w.writerow(self.HEADER)
                f.flush()
            self._files[key] = (f, w)
        self.targets.append((pids, key))

    def pids(self):
        """PIDs that must be polled because they are recorded."""
        out = set()
        for pids, _ in self.targets:
            out |= set(self.settings.enabled) if pids is None else pids
        return out

    def files_for(self, pid):
        return [path for pids, path in self.targets
                if (pid in self.settings.enabled if pids is None else pid in pids)]

    def write(self, pid, t, value):
        paths = set(self.files_for(pid))
        if not paths:
            return
        name, unit = PIDS[pid][0], PIDS[pid][1]
        ts = datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec="milliseconds")
        row = [ts, f"{t:.3f}", pid, name, f"{value:.6g}", unit]
        for path in paths:
            f, w = self._files[path]
            try:
                w.writerow(row)
                f.flush()             # keep data even if the program is killed
            except OSError:
                pass

    def close(self):
        for f, _ in self._files.values():
            try:
                f.close()
            except OSError:
                pass
        self._files.clear()


# --------------------------------------------------------------------- poller

class Poller(threading.Thread):
    """Polls the ELM327 in the background and stores results in self.data."""

    def __init__(self, settings, recorder=None):
        super().__init__(daemon=True)
        self.settings = settings
        self.recorder = recorder
        self.lock = threading.Lock()
        self.data = {}            # pid -> dict(value, min, max, t, err)
        self.status = "connecting…"
        self.connected = False
        self.version = "?"
        self.cycle_ms = 0
        self.history = {}         # pid -> deque[(timestamp, value)]
        self.focus = None         # when set, only this PID is polled (faster chart)
        self._stop = threading.Event()
        self._reconnect = threading.Event()
        self.elm = None

    def stop(self):
        self._stop.set()

    def reconnect(self):
        self._reconnect.set()

    def reset_minmax(self):
        with self.lock:
            for d in self.data.values():
                d["min"] = d["max"] = d.get("value")

    def clear_history(self, pid):
        with self.lock:
            self.history.pop(pid, None)

    def _connect(self):
        s = self.settings
        self.elm = ELM327(s.host, s.port)
        self.status = f"connecting to {s.host}:{s.port}…"
        self.elm.connect()
        self.version = self.elm.version
        self.connected = True
        self.status = "connected"

    def _store(self, pid, value=None, err=None):
        with self.lock:
            d = self.data.setdefault(pid, {"value": None, "min": None, "max": None, "t": 0, "err": None})
            d["err"] = err
            if err is None:
                d["value"] = value
                d["t"] = time.time()
                d["min"] = value if d["min"] is None else min(d["min"], value)
                d["max"] = value if d["max"] is None else max(d["max"], value)
                self.history.setdefault(pid, deque(maxlen=HISTORY_LEN)).append((d["t"], value))
                t = d["t"]
        if err is None and self.recorder:
            self.recorder.write(pid, t, value)   # file I/O outside the lock

    def poll_list(self):
        """PIDs polled in one cycle: focus PID or enabled ones, plus recorded ones."""
        base = [self.focus] if self.focus else list(self.settings.enabled)
        if self.recorder:
            base += [p for p in PID_ORDER if p in self.recorder.pids() and p not in base]
        # derived values need their source PIDs read earlier in the same cycle
        out = []
        for pid in base:
            for dep in DERIVED.get(pid, ((), None))[0]:
                if dep not in out:
                    out.append(dep)
            if pid not in out:
                out.append(pid)
        # a source PID listed after its derived value must still come first
        for pid in [p for p in out if p in DERIVED]:
            out.remove(pid)
            out.append(pid)
        return out

    def _derive(self, pid, cycle_start):
        """Compute a derived value from source PIDs read in this cycle."""
        deps, func = DERIVED[pid]
        with self.lock:
            src = {p: self.data.get(p, {}) for p in deps}
        if any(d.get("err") or d.get("value") is None or d.get("t", 0) < cycle_start
               for d in src.values()):
            return None
        return func({p: d["value"] for p, d in src.items()})

    def run(self):
        while not self._stop.is_set():
            if self._reconnect.is_set():
                self._reconnect.clear()
                self.connected = False
                if self.elm:
                    self.elm.close()
            if not self.connected:
                try:
                    self._connect()
                except (OSError, TimeoutError, ConnectionError) as e:
                    self.connected = False
                    self.status = f"connection error: {e}"
                    self._stop.wait(2.0)
                    continue

            start = time.time()
            for pid in self.poll_list():
                if self._stop.is_set() or self._reconnect.is_set():
                    break
                if pid in DERIVED:
                    value = self._derive(pid, start)
                    if value is not None:        # e.g. L/100km while standing still
                        self._store(pid, value)
                    continue
                try:
                    if pid == "RV":
                        value = self.elm.read_voltage()
                    else:
                        _, _, nbytes, formula, _, _ = PIDS[pid]
                        value = formula(self.elm.read_pid(pid, nbytes))
                    self._store(pid, value)
                except ValueError as e:
                    self._store(pid, err=str(e))
                except (OSError, TimeoutError, ConnectionError) as e:
                    self.connected = False
                    self.status = f"disconnected: {e}"
                    break
            self.cycle_ms = (time.time() - start) * 1000
            self._stop.wait(max(0.0, self.settings.interval - (time.time() - start)))
        if self.elm:
            self.elm.close()


# ------------------------------------------------------------------------- UI

def safe_addstr(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    text = text[: max(0, w - x - 1)]
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def bar(value, vmax, width):
    if vmax is None or value is None or width <= 0:
        return ""
    frac = max(0.0, min(1.0, value / vmax))
    full = int(frac * width)
    return "█" * full + "░" * (width - full)


def fmt(pid, value):
    if value is None:
        return "—"
    return PIDS[pid][4].format(value)


def fmt_window(sec):
    return f"{sec // 60} min" if sec >= 60 else f"{sec} s"


def fmt_axis(value, span):
    """Format an axis label with precision matching the visible range."""
    dec = 2 if span < 1 else 1 if span < 10 else 0
    return f"{value:.{dec}f}"


def resample(hist, start, end, ncols, max_gap):
    """Turn (t, v) samples into one value per column (bucket average).

    Empty buckets repeat the last value as long as it is not older than max_gap,
    so a slow refresh rate still gives a continuous chart.
    """
    step = (end - start) / ncols
    out = [None] * ncols
    last_v, last_t, i, n = None, None, 0, len(hist)
    while i < n and hist[i][0] < start:
        last_t, last_v = hist[i]
        i += 1
    for c in range(ncols):
        b_end = start + (c + 1) * step
        total, k = 0.0, 0
        while i < n and hist[i][0] < b_end:
            total += hist[i][1]
            last_t = hist[i][0]
            k += 1
            i += 1
        if k:
            last_v = total / k
            out[c] = last_v
        elif last_v is not None and b_end - last_t <= max_gap:
            out[c] = last_v
    return out


class App:
    COLS = [("Parameter", 30), ("Value", 10), ("Unit", 8), ("Min", 9), ("Max", 9)]

    def __init__(self, stdscr, settings, poller):
        self.scr = stdscr
        self.sel = 0              # selected row on the main screen
        self.s = settings
        self.p = poller
        curses.curs_set(0)
        stdscr.timeout(100)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)    # values
        curses.init_pair(2, curses.COLOR_YELLOW, -1)   # stale data
        curses.init_pair(3, curses.COLOR_RED, -1)      # errors
        curses.init_pair(4, curses.COLOR_CYAN, -1)     # headers
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_CYAN)  # menu selection

    # ---- main screen
    def draw(self):
        scr = self.scr
        scr.erase()
        h, w = scr.getmaxyx()
        conn_attr = curses.color_pair(1) if self.p.connected else curses.color_pair(3)

        safe_addstr(scr, 0, 1, "OBD-II Dashboard", curses.A_BOLD | curses.color_pair(4))
        safe_addstr(scr, 0, 19, f"│ {self.s.host}:{self.s.port} │ ")
        x = 19 + len(f"│ {self.s.host}:{self.s.port} │ ")
        safe_addstr(scr, 0, x, self.p.status, conn_attr)
        safe_addstr(scr, 1, 1, f"{self.p.version}  │  refresh: {self.s.interval:g} s"
                               f"  │  cycle: {self.p.cycle_ms:.0f} ms  │  {time.strftime('%H:%M:%S')}")
        rec = self.p.recorder
        if rec and rec.targets:
            files = sorted({os.path.basename(path) for _, path in rec.targets})
            safe_addstr(scr, 2, 1, f"● REC {len(rec.pids())} PID(s) → {', '.join(files)}",
                        curses.color_pair(3) | curses.A_BOLD)

        widths = [c[1] for c in self.COLS]
        bar_w = max(0, min(25, w - sum(widths) - 3 * len(widths) - 6))
        all_w = widths + ([bar_w] if bar_w >= 5 else [])
        heads = [c[0] for c in self.COLS] + (["Graph"] if bar_w >= 5 else [])

        def line(left, mid, right):
            return left + mid.join("─" * (cw + 2) for cw in all_w) + right

        y = 3
        safe_addstr(scr, y, 0, line("┌", "┬", "┐")); y += 1
        row = "│" + "│".join(f" {hd:<{cw}} " for hd, cw in zip(heads, all_w)) + "│"
        safe_addstr(scr, y, 0, row, curses.color_pair(4) | curses.A_BOLD); y += 1
        safe_addstr(scr, y, 0, line("├", "┼", "┤")); y += 1

        now = time.time()
        with self.p.lock:
            snapshot = {k: dict(v) for k, v in self.p.data.items()}
        if self.s.enabled:
            self.sel = max(0, min(self.sel, len(self.s.enabled) - 1))
        for row_i, pid in enumerate(self.s.enabled):
            if y >= h - 3:
                break
            name, unit, _, _, _, vmax = PIDS[pid]
            selected = row_i == self.sel
            d = snapshot.get(pid, {})
            val = d.get("value")
            err = d.get("err")
            if err:
                val_txt, attr = "error", curses.color_pair(3)
            elif val is None:
                val_txt, attr = "—", 0
            else:
                val_txt = fmt(pid, val)
                stale = now - d.get("t", 0) > max(3 * self.s.interval, 3)
                attr = curses.color_pair(2) if stale else curses.color_pair(1) | curses.A_BOLD
            cells = [name, val_txt, unit, fmt(pid, d.get("min")), fmt(pid, d.get("max"))]
            xpos = 0
            safe_addstr(scr, y, xpos, "│")
            for i, (cell, cw) in enumerate(zip(cells, widths)):
                text = f" {cell:>{cw}} " if i in (1, 3, 4) else f" {cell:<{cw}} "
                cell_attr = attr if i == 1 else 0
                if i == 0 and selected:
                    cell_attr = curses.color_pair(5) | curses.A_BOLD
                safe_addstr(scr, y, xpos + 1, text[: cw + 2], cell_attr)
                xpos += cw + 3
                safe_addstr(scr, y, xpos, "│")
            if bar_w >= 5:
                safe_addstr(scr, y, xpos + 1, f" {bar(val, vmax, bar_w):<{bar_w}} ", curses.color_pair(1))
                safe_addstr(scr, y, xpos + bar_w + 3, "│")
            if err:
                safe_addstr(scr, y, xpos + (bar_w + 4 if bar_w >= 5 else 1) + 1, err[:30], curses.color_pair(3))
            y += 1
        safe_addstr(scr, y, 0, line("└", "┴", "┘"))

        help_txt = (" q quit │ ↑↓ select │ Enter chart │ m menu │ +/- refresh"
                    " │ r reset min/max │ c reconnect ")
        safe_addstr(scr, h - 1, 0, help_txt, curses.A_REVERSE)
        scr.refresh()

    def change_interval(self, step):
        cur = min(range(len(INTERVALS)), key=lambda i: abs(INTERVALS[i] - self.s.interval))
        self.s.interval = INTERVALS[max(0, min(len(INTERVALS) - 1, cur + step))]

    # ---- live chart view
    def draw_chart(self, pid, window, auto):
        scr = self.scr
        scr.erase()
        h, w = scr.getmaxyx()
        name, unit, _, _, _, vmax = PIDS[pid]
        green = curses.color_pair(1)
        now = time.time()
        with self.p.lock:
            hist = list(self.p.history.get(pid, ()))
            d = dict(self.p.data.get(pid, {}))
        vals = [v for t, v in hist if t >= now - window]

        # header
        safe_addstr(scr, 0, 1, f"{name} [{unit}]", curses.A_BOLD | curses.color_pair(4))
        conn_attr = green if self.p.connected else curses.color_pair(3)
        status = f"{self.p.status}  {time.strftime('%H:%M:%S')}"
        safe_addstr(scr, 0, max(1, w - len(status) - 2), status, conn_attr)

        cur = d.get("value")
        if d.get("err"):
            safe_addstr(scr, 1, 1, f"error: {d['err']}", curses.color_pair(3) | curses.A_BOLD)
        else:
            safe_addstr(scr, 1, 1, f"now: {fmt(pid, cur)} {unit}", green | curses.A_BOLD)
        if vals:
            stats = (f"window {fmt_window(window)}:  min {fmt(pid, min(vals))}"
                     f"  avg {fmt(pid, sum(vals) / len(vals))}  max {fmt(pid, max(vals))}"
                     f"  │  {len(vals)} samples")
        else:
            stats = f"window {fmt_window(window)}:  no data yet"
        safe_addstr(scr, 1, 26, stats)
        mode = "auto" if auto or vmax is None else f"fixed 0–{vmax}"
        focus = "ON (only this PID is polled)" if self.p.focus else "off"
        safe_addstr(scr, 2, 1, f"refresh: {self.s.interval:g} s  │  cycle: {self.p.cycle_ms:.0f} ms"
                               f"  │  scale: {mode}  │  focus: {focus}", curses.A_DIM)
        rec_files = self.p.recorder.files_for(pid) if self.p.recorder else []
        if rec_files:
            rec_txt = "● REC → " + ", ".join(os.path.basename(f) for f in rec_files)
            safe_addstr(scr, 1, max(1, w - len(rec_txt) - 2), rec_txt,
                        curses.color_pair(3) | curses.A_BOLD)

        help_txt = (" ←→ window │ ↑↓ parameter │ a autoscale │ f focus │ +/- refresh"
                    " │ c clear │ q back ")
        safe_addstr(scr, h - 1, 0, help_txt, curses.A_REVERSE)

        # chart geometry
        top, bottom = 4, h - 4            # rows used by the plot
        ch = bottom - top + 1
        if auto or vmax is None:
            if vals:
                lo, hi = min(vals), max(vals)
                pad = (hi - lo) * 0.1 or max(abs(hi) * 0.05, 1.0)
                lo, hi = lo - pad, hi + pad
                if min(vals) >= 0 > lo:
                    lo = 0.0
            else:
                lo, hi = 0.0, 1.0
        else:
            lo, hi = 0.0, float(vmax)
        span = hi - lo
        labels = [fmt_axis(hi, span), fmt_axis((lo + hi) / 2, span), fmt_axis(lo, span)]
        lw = max(len(l) for l in labels)
        left = lw + 2                     # first plot column
        cw = w - left - 2                 # plot width in columns
        if ch < 3 or cw < 10:
            safe_addstr(scr, 4, 1, "terminal too small for the chart", curses.color_pair(3))
            scr.refresh()
            return

        # axes and labels
        for r in range(top, bottom + 1):
            safe_addstr(scr, r, left - 1, "│", curses.A_DIM)
        for r, label in ((top, labels[0]), ((top + bottom) // 2, labels[1]), (bottom, labels[2])):
            safe_addstr(scr, r, 0, f"{label:>{lw}} ┤", curses.A_DIM)
            safe_addstr(scr, r, left, "┈" * cw, curses.A_DIM)       # light grid line
        safe_addstr(scr, bottom + 1, left - 1, "└" + "─" * cw, curses.A_DIM)
        safe_addstr(scr, bottom + 2, left, f"-{fmt_window(window)}", curses.A_DIM)
        mid_lbl = f"-{fmt_window(window // 2)}"
        safe_addstr(scr, bottom + 2, left + cw // 2 - len(mid_lbl) // 2, mid_lbl, curses.A_DIM)
        safe_addstr(scr, bottom + 2, left + cw - 3, "now", curses.A_DIM)

        # bars, 8 sub-steps per character cell
        max_gap = max(3 * self.s.interval, 2 * window / cw, 3.0)
        for c, v in enumerate(resample(hist, now - window, now, cw, max_gap)):
            if v is None:
                continue
            frac = max(0.0, min(1.0, (v - lo) / span))
            eighths = int(round(frac * ch * 8))
            for r in range(ch):
                level = eighths - r * 8
                if level <= 0:
                    break
                safe_addstr(scr, bottom - r, left + c, BLOCKS[min(level, 8)], green)
        scr.refresh()

    def chart(self, pid):
        win_idx = WINDOWS.index(60)
        auto = True
        self.p.focus = pid                # faster sampling while watching one value
        self.p.clear_history(pid)         # every chart starts from an empty history
        try:
            while True:
                self.draw_chart(pid, WINDOWS[win_idx], auto)
                key = self.scr.getch()
                if key in (27, ord("q"), ord("Q"), curses.KEY_BACKSPACE, 127, 8):
                    break
                elif key in (curses.KEY_LEFT, ord("[")):
                    win_idx = max(0, win_idx - 1)
                elif key in (curses.KEY_RIGHT, ord("]")):
                    win_idx = min(len(WINDOWS) - 1, win_idx + 1)
                elif key in (curses.KEY_UP, curses.KEY_DOWN) and self.s.enabled:
                    step = -1 if key == curses.KEY_UP else 1
                    self.sel = (self.sel + step) % len(self.s.enabled)
                    pid = self.s.enabled[self.sel]
                    self.p.clear_history(pid)
                    if self.p.focus:
                        self.p.focus = pid
                elif key in (ord("a"), ord("A")):
                    auto = not auto
                elif key in (ord("f"), ord("F")):
                    self.p.focus = None if self.p.focus else pid
                elif key in (ord("+"), ord("=")):
                    self.change_interval(+1)
                elif key in (ord("-"), ord("_")):
                    self.change_interval(-1)
                elif key in (ord("c"), ord("C")):
                    self.p.clear_history(pid)
        finally:
            self.p.focus = None

    # ---- menu
    def prompt(self, label, default):
        h, w = self.scr.getmaxyx()
        win = curses.newwin(3, min(60, w - 2), h // 2 - 1, max(0, (w - 60) // 2))
        win.box()
        safe_addstr(win, 1, 2, f"{label}: ")
        curses.echo()
        curses.curs_set(1)
        try:
            raw = win.getstr(1, 4 + len(label), 40).decode(errors="ignore").strip()
        finally:
            curses.noecho()
            curses.curs_set(0)
        return raw or default

    def menu(self):
        sel = 0
        while True:
            items = ([("interval", f"Refresh: ◀ {self.s.interval:g} s ▶"),
                      ("host", f"Host: {self.s.host}"),
                      ("port", f"Port: {self.s.port}")]
                     + [(pid, f"[{'x' if pid in self.s.enabled else ' '}] {PIDS[pid][0]}") for pid in PID_ORDER]
                     + [("reconnect", "Reconnect"),
                        ("save", "Save settings"),
                        ("back", "Back")])
            h, w = self.scr.getmaxyx()
            mh = min(len(items) + 4, h - 2)
            mw = min(48, w - 2)
            win = curses.newwin(mh, mw, max(0, (h - mh) // 2), max(0, (w - mw) // 2))
            win.keypad(True)
            win.box()
            safe_addstr(win, 0, 2, " Settings ", curses.A_BOLD | curses.color_pair(4))
            visible = mh - 4
            top = max(0, min(sel - visible // 2, len(items) - visible))
            for i, (_, label) in enumerate(items[top: top + visible]):
                idx = top + i
                attr = curses.color_pair(5) if idx == sel else 0
                safe_addstr(win, 1 + i, 2, f" {label:<{mw - 6}}", attr)
            safe_addstr(win, mh - 2, 2, "↑↓ select  ←→ change  space/enter  Esc", curses.A_DIM)
            win.refresh()

            key = win.getch()
            kid = items[sel][0]
            if key in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(items)
            elif key in (curses.KEY_DOWN, ord("j")):
                sel = (sel + 1) % len(items)
            elif key in (27, ord("m"), ord("q")):
                break
            elif kid == "interval" and key in (curses.KEY_LEFT, ord("-")):
                self.change_interval(-1)
            elif kid == "interval" and key in (curses.KEY_RIGHT, ord("+")):
                self.change_interval(+1)
            elif key in (ord(" "), 10, 13, curses.KEY_ENTER):
                if kid in PIDS:
                    if kid in self.s.enabled:
                        self.s.enabled.remove(kid)
                    else:
                        self.s.enabled = [p for p in PID_ORDER if p in self.s.enabled or p == kid]
                elif kid == "host":
                    self.s.host = self.prompt("Host", self.s.host)
                    self.p.reconnect()
                elif kid == "port":
                    try:
                        self.s.port = int(self.prompt("Port", str(self.s.port)))
                        self.p.reconnect()
                    except ValueError:
                        pass
                elif kid == "reconnect":
                    self.p.reconnect()
                elif kid == "save":
                    self.s.save()
                elif kid == "back":
                    break
            del win
            self.scr.touchwin()
            self.draw()

    # ---- main loop
    def run(self):
        while True:
            self.draw()
            key = self.scr.getch()
            if key in (ord("q"), ord("Q")):
                break
            elif key in (ord("m"), ord("M")):
                self.menu()
            elif key in (curses.KEY_UP, ord("k")) and self.s.enabled:
                self.sel = (self.sel - 1) % len(self.s.enabled)
            elif key in (curses.KEY_DOWN, ord("j")) and self.s.enabled:
                self.sel = (self.sel + 1) % len(self.s.enabled)
            elif key in (10, 13, curses.KEY_ENTER, curses.KEY_RIGHT) and self.s.enabled:
                self.chart(self.s.enabled[self.sel])
            elif key in (ord("+"), ord("=")):
                self.change_interval(+1)
            elif key in (ord("-"), ord("_")):
                self.change_interval(-1)
            elif key in (ord("r"), ord("R")):
                self.p.reset_minmax()
            elif key in (ord("c"), ord("C")):
                self.p.reconnect()


def main():
    locale.setlocale(locale.LC_ALL, "")
    os.environ.setdefault("ESCDELAY", "25")   # make Esc react immediately
    settings = Settings.load()
    ap = argparse.ArgumentParser(description="OBD-II dashboard (ELM327 over TCP)")
    ap.add_argument("--host", default=settings.host)
    ap.add_argument("--port", type=int, default=settings.port)
    ap.add_argument("--interval", type=float, default=settings.interval, help="refresh interval in seconds")
    ap.add_argument("--record", action="append", default=[], metavar="PIDS=FILE",
                    help="append samples of PIDS (comma separated codes or 'all') to FILE as CSV;"
                         " repeatable, e.g. --record 0D=speed.csv --record all=session.csv")
    ap.add_argument("--list-pids", action="store_true", help="print PID codes and exit")
    args = ap.parse_args()

    if args.list_pids:
        for pid in PID_ORDER:
            name, unit = PIDS[pid][:2]
            mark = "*" if pid in settings.enabled else " "
            src = f"  (computed from {', '.join(DERIVED[pid][0])})" if pid in DERIVED else ""
            print(f"{mark} {pid}  {name} [{unit}]{src}")
        print("\n* = enabled on the dashboard ('all' records these)")
        return

    settings.host, settings.port, settings.interval = args.host, args.port, args.interval

    recorder = Recorder(settings)
    try:
        for spec in args.record:
            recorder.add(*Recorder.parse(spec))
    except (ValueError, OSError) as e:
        recorder.close()
        ap.error(f"--record: {e}")

    poller = Poller(settings, recorder if recorder.targets else None)
    poller.start()
    try:
        curses.wrapper(lambda scr: App(scr, settings, poller).run())
    finally:
        poller.stop()
        poller.join(timeout=5)        # let the last sample reach the files
        recorder.close()
        settings.save()
        for pids, path in recorder.targets:
            print(f"recorded {'all' if pids is None else ','.join(sorted(pids))} → {path}")


if __name__ == "__main__":
    main()
