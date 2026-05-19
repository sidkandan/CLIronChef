#!/usr/bin/env python3
"""CLIronChef pre-flight safety check.

Runs 7 categories of checks; exits 0 (green), 1 (yellow warnings), 2 (red issues).
Standalone — can run before `pip install -e .` if you have the deps installed.

Usage:
    python3 scripts/preflight.py
    # or
    cliron-chef preflight
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Make src importable when run from the repo root
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from cliron_chef.api import TyphurAPI, _config_dir
except ImportError as e:
    print(f"ERROR: {e}\nInstall with `pip install -e .` first.", file=sys.stderr)
    sys.exit(2)


GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"
BOLD = "\033[1m"


class Status:
    def __init__(self):
        self.issues = []
        self.warnings = []

    def red(self, msg):
        self.issues.append(msg)
        print(f"  {RED}✗{RESET} {msg}")

    def yellow(self, msg):
        self.warnings.append(msg)
        print(f"  {YELLOW}!{RESET} {msg}")

    def green(self, msg):
        print(f"  {GREEN}✓{RESET} {msg}")


def section(title):
    print(f"\n{BOLD}{title}{RESET}")


def main():
    print(f"{BOLD}═══════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}🔍 CLIronChef pre-flight check{RESET}")
    print(f"{BOLD}═══════════════════════════════════════════════════════════{RESET}")

    s = Status()

    # 1. Credentials
    section("1. Credentials & auth")
    try:
        api = TyphurAPI.from_cached_credentials()
        s.green(f"Logged in (region={api.region})")
    except Exception as e:
        s.red(f"Login failed: {e}")
        return _summary(s)

    # 2. Device list reachable
    section("2. Cloud reachability + device binding")
    try:
        devs = api.list_devices()
        s.green(f"Listed {len(devs)} bound device(s)")
    except Exception as e:
        s.red(f"Device list failed: {e}")
        return _summary(s)

    dome = next((d for d in devs if d.get("deviceModel") == "AF04"), None)
    probe = next((d for d in devs if d.get("deviceModel") == "WT01"), None)
    if not dome:
        s.red("No AF04 Dome 2 bound to account")
    else:
        s.green(f"Dome 2 AF04 bound: {dome.get('deviceName', '?')} (id {dome['deviceId']})")
    if not probe:
        s.red("No WT01 Sync ONE probe bound to account")
    else:
        s.green(f"Sync ONE WT01 bound: {probe.get('deviceName', '?')} (id {probe['deviceId']})")

    if not dome or not probe:
        return _summary(s)

    # 3. Fresh telemetry
    section("3. Force fresh telemetry")
    try:
        api.request_status("AF04", str(dome["deviceId"]))
        api.request_status("WT01", str(probe["deviceId"]))
        time.sleep(2)
        devs = api.list_devices()
        dome = next(d for d in devs if str(d["deviceId"]) == str(dome["deviceId"]))
        probe = next(d for d in devs if str(d["deviceId"]) == str(probe["deviceId"]))
        s.green("Fresh status requested + received")
    except Exception as e:
        s.yellow(f"Could not force fresh status: {e}")

    # 4. Dome state
    section("4. Dome 2 state")
    dsc = (dome.get("lastStatusCmd") or {}).get("cmdData", {}) or {}
    dgs = dsc.get("globalStatus")
    dcs = dsc.get("cookingState")
    err = dsc.get("errorCode", 0)
    chamber_f = (dsc.get("curTemperature", 0) or 0) / 10

    if err:
        s.red(f"Dome 2 errorCode={err} — investigate before cook")
    else:
        s.green("Dome 2 errorCode=0")

    if dgs == "cooking" and dcs not in (None, 0):
        s.red(f"Active cook already running on Dome 2 (state={dcs}); finish/stop it first")
    elif dgs == "online":
        s.green("Dome 2 globalStatus=online (idle, ready)")
    elif dgs == "offline":
        s.red("Dome 2 is offline — check WiFi / power")
    else:
        s.yellow(f"Dome 2 unfamiliar state: globalStatus={dgs} cookingState={dcs}")

    if chamber_f > 200:
        s.yellow(f"Chamber still hot ({chamber_f:.0f}°F); cold-start blast strategies will be skewed")
    elif chamber_f > 0:
        s.green(f"Chamber at {chamber_f:.0f}°F (cool)")

    # 5. Probe state
    section("5. Sync ONE probe state")
    psc = (probe.get("lastStatusCmd") or {}).get("cmdData", {}) or {}
    pgs = psc.get("globalStatus")
    probes = psc.get("probes", [])

    if pgs != "online":
        s.red(f"Probe globalStatus={pgs} — user must wake it (hold 'O' button 3 sec)")
    else:
        s.green("Probe globalStatus=online")
        if probes:
            p = probes[0]
            internal_f = (p.get("curTemperature", 0) or 0) / 10
            battery = p.get("batteryValue")
            if 35 <= internal_f <= 75:
                s.green(f"Probe internal {internal_f:.1f}°F (cold meat, normal pre-cook)")
            elif internal_f > 100:
                s.yellow(f"Probe internal {internal_f:.1f}°F — probe tip likely in air or near surface; reseat")
            elif internal_f < 35:
                s.yellow(f"Probe internal {internal_f:.1f}°F — very cold (freezer?)")
            if battery is not None:
                if battery < 20:
                    s.yellow(f"Probe battery {battery}% — charge before long cook")
                else:
                    s.green(f"Probe battery {battery}%")

    # 6. MQTT cert
    section("6. MQTT cert availability")
    cfg = _config_dir()
    cert_path = cfg / "client.crt"
    key_path = cfg / "client.key"
    if cert_path.exists() and key_path.exists():
        s.green(f"MQTT cert + key cached at {cfg}")
    else:
        s.yellow("MQTT cert not cached locally — first cook will fetch")

    # 7. Disk space for logs
    section("7. Disk space for telemetry logs")
    runs = Path.cwd() / "runs"
    if not runs.exists():
        runs.mkdir(exist_ok=True)
    try:
        st = os.statvfs(runs)
        free_mb = (st.f_bavail * st.f_frsize) / (1024 * 1024)
        if free_mb < 50:
            s.yellow(f"Only {free_mb:.0f} MB free in {runs} — telemetry logs may fail")
        else:
            s.green(f"runs/ has {free_mb:.0f} MB free")
    except Exception:
        s.green("runs/ directory exists")

    return _summary(s)


def _summary(s: Status) -> int:
    print(f"\n{BOLD}═══════════════════════════════════════════════════════════{RESET}")
    if s.issues:
        print(f"{RED}{BOLD}🔴 RED — DO NOT COOK YET ({len(s.issues)} issue(s)){RESET}")
        return 2
    if s.warnings:
        print(f"{YELLOW}{BOLD}🟡 YELLOW — review before cooking ({len(s.warnings)} warning(s)){RESET}")
        return 1
    print(f"{GREEN}{BOLD}🟢 GREEN — safe to cook{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
