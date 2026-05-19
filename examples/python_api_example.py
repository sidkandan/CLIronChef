#!/usr/bin/env python3
"""Example: cook a salmon programmatically using the CLIronChef Python API.

This is functionally equivalent to running `cliron-chef cook salmon_basic`, but shows
the underlying API for custom flows.

Run:
    python3 examples/python_api_example.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make src importable if running from repo root
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cliron_chef import TyphurAPI
from cliron_chef.watcher import ProbeWatcher


def main():
    print("=== CLIronChef Python API example: salmon cook ===\n")

    # 1. Load credentials and find devices
    api = TyphurAPI.from_cached_credentials()
    dome = api.find_dome()
    probe = api.find_probe()
    if not dome:
        print("No AF04 Dome 2 bound. Pair one via the Typhur app first.")
        return 1
    if not probe:
        print("No WT01 probe bound. Pair one via the Typhur app first.")
        return 1
    dome_id = str(dome["deviceId"])
    probe_id = str(probe["deviceId"])
    print(f"Found Dome 2: {dome['deviceName']} (id {dome_id})")
    print(f"Found Probe: {probe['deviceName']} (id {probe_id})\n")

    # 2. Configure the initial cook (Grill mode 3 at 450°F, 40-min timer buffer)
    print("Configuring initial cook (Grill mode 3 @ 450°F, 2400s timer buffer)...")
    _, cook_uuid = api.start_cook(
        "AF04", dome_id,
        [{"cookingMode": 3, "setTemperature": 450, "setTime": 2400}],
    )
    print(f"  cookUuid: {cook_uuid}")
    print("  Display now shows: Grill 450°F 40:00\n")

    # 3. Prompt for physical Start
    print("👉 PRESS THE PHYSICAL START BUTTON ON THE DOME 2 NOW.")
    print("   (Firmware UL/IEC safety gate; cannot be bypassed by software.)")
    input("   Press ENTER once you've pressed it...\n")

    # 4. Set up the probe-driven watcher
    watcher = ProbeWatcher(api, dome_id, probe_id, cook_uuid=cook_uuid)
    # Phase 2: at probe 95°F, swap to Bake mode 10 at 300°F (gentle finish)
    watcher.add_swap_at(95, mode=10, temp_f=300, label="Bake gentle finish")
    # Done signal: at probe 120°F, send STOP.
    watcher.stop_at(120)

    # 5. Run it — blocks until probe target is reached
    print("Watching probe... (warning: this will take ~6-10 min)\n")
    result = watcher.run(max_minutes=20)

    print("\n=== Cook complete ===")
    print(f"  Final probe: {result['final_internal_f']:.1f}°F")
    print(f"  Samples received: {result['samples']}")
    print(f"  Completed: {result['completed']}")
    print("\n👉 STOP sent. Display should show 'End' / '0:00' — pull now and rest 3 min.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
