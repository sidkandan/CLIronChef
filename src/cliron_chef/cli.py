"""CLI entry point for the `cliron-chef` command.

This is a thin argparse-based dispatcher. The heavy lifting lives in:
- cliron_chef.api      — HTTP client
- cliron_chef.mqtt_client — MQTT subscriber
- cliron_chef.runner   — declarative recipe runner
- cliron_chef.watcher  — lower-level probe watcher
- cliron_chef.modes    — mode constants
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time

from cliron_chef import __version__
from cliron_chef.api import TyphurAPI, TyphurAPIError
from cliron_chef.modes import AF04_MODES, AF04_MODES_BY_ID
from cliron_chef.mqtt_client import tail_telemetry
from cliron_chef.runner import RecipeError, RecipeRunner, list_recipes, load_recipe


# ANSI colors
def _color(s, code):
    return f"\033[{code}m{s}\033[0m" if sys.stdout.isatty() and os.environ.get("NO_COLOR") is None else s


def BOLD(s):
    return _color(s, "1")


def GREEN(s):
    return _color(s, "32")


def YELLOW(s):
    return _color(s, "33")


def RED(s):
    return _color(s, "31")


def CYAN(s):
    return _color(s, "36")


def DIM(s):
    return _color(s, "2")


# -- Subcommand implementations ------------------------------------------------

def cmd_login(args):
    email = args.email or input("Typhur email: ")
    password = args.password or getpass.getpass("Typhur password: ")
    region = args.region or input("Region (US/EU, default US): ").strip().upper() or "US"

    try:
        TyphurAPI.login(email, password, region=region)
    except TyphurAPIError as e:
        print(RED(f"Login failed: {e}"), file=sys.stderr)
        return 1
    print(GREEN(f"✓ Logged in successfully (region={region})"))
    print(DIM("  Credentials cached at ~/.cliron-chef/credentials"))
    return 0


def cmd_info(args):
    api = TyphurAPI.from_cached_credentials()
    devs = api.list_devices()
    print(json.dumps(devs, indent=2, default=str))
    return 0


def cmd_status(args):
    api = TyphurAPI.from_cached_credentials()
    dome = api.find_dome()
    probe = api.find_probe()
    if not dome:
        print(RED("No AF04 Dome 2 found in device list."), file=sys.stderr)
        return 1

    # Force fresh status
    try:
        api.request_status("AF04", str(dome["deviceId"]))
        if probe:
            api.request_status("WT01", str(probe["deviceId"]))
        time.sleep(1.5)
        devs = api.list_devices()
        dome = next(d for d in devs if str(d["deviceId"]) == str(dome["deviceId"]))
        if probe:
            probe = next(d for d in devs if str(d["deviceId"]) == str(probe["deviceId"]))
    except Exception as e:
        print(YELLOW(f"Warning: could not force fresh status ({e})"), file=sys.stderr)

    print()
    print(BOLD("═" * 60))
    print(BOLD(f"📡 Typhur device state — {time.strftime('%Y-%m-%d %H:%M:%S')}"))
    print(BOLD("═" * 60))

    # Dome
    print()
    print(BOLD("🔥 Dome 2 (AF04)") + "  " + DIM(f"id={dome['deviceId']}"))
    sc = (dome.get("lastStatusCmd") or {}).get("cmdData", {}) or {}
    gs = sc.get("globalStatus", "?")
    print(f"  Status:        {GREEN(gs) if gs == 'online' else (CYAN(gs) if gs == 'cooking' else RED(gs))}")
    print(f"  Chamber:       {(sc.get('curTemperature', 0) / 10):.0f}°F")
    err = sc.get("errorCode", 0)
    print(f"  Error code:    {GREEN('0 (ok)') if err == 0 else RED(str(err))}")

    cooking_state = sc.get("cookingState")
    if gs == "cooking" and cooking_state not in (None, 0):
        print()
        print(BOLD("  Active cook:"))
        print(f"    cookUuid:    {sc.get('cookUuid')}")
        print(f"    Stage:       {sc.get('cookingStage')}/{sc.get('cookingStageNum')}")
        print(f"    Elapsed:     {sc.get('curCookSec')}s")
        remain = sc.get("curRemainingTime")
        remain_str = f"{remain}s" + (YELLOW(" (LOW!)") if remain and remain < 300 else "")
        print(f"    Remaining:   {remain_str}")
        for i, p in enumerate(sc.get("setParams") or [], 1):
            mode_id = p.get("cookingMode")
            mode_name = AF04_MODES_BY_ID.get(mode_id, {}).get("name", "?")
            print(f"    Stage {i}:     mode={mode_id} ({mode_name}) @ "
                  f"{p.get('setTemperature', 0)/10:.0f}°F for {p.get('setTime', 0)//60}min")

    # Probe
    print()
    print(BOLD("🌡️  Sync ONE probe (WT01)") + ("  " + DIM(f"id={probe['deviceId']}") if probe else ""))
    if not probe:
        print(f"  {RED('NOT BOUND TO ACCOUNT')}")
    else:
        psc = (probe.get("lastStatusCmd") or {}).get("cmdData", {}) or {}
        pgs = psc.get("globalStatus", "?")
        pgs_color = GREEN(pgs) if pgs == "online" else RED(pgs)
        suffix = "" if pgs == "online" else "  " + YELLOW("(hold O button 3 sec to wake)")
        print(f"  Status:        {pgs_color}{suffix}")
        probes = psc.get("probes", [])
        if probes:
            p = probes[0]
            internal_f = (p.get("curTemperature", 0) or 0) / 10
            print(f"  Internal:      {BOLD(f'{internal_f:.1f}°F')}")
            print(f"  Ambient:       {(p.get('curAmbientTemperature', 0) or 0)/10:.0f}°F")
            print(f"  Battery:       {p.get('batteryValue')}%")

    print()
    print(BOLD("═" * 60))
    print(BOLD("💡 Suggested next action"))
    print(BOLD("═" * 60))
    if err:
        print(f"  {RED(f'⚠️  Dome has error code {err} — power-cycle and investigate')}")
    elif gs == "cooking" and cooking_state not in (None, 0):
        print(f"  {CYAN('🍳 Cook in progress — run a probe watcher or wait for completion')}")
    elif gs == "online" and probe and (probe.get("lastStatusCmd") or {}).get("cmdData", {}).get("globalStatus") == "online":
        print(f"  {GREEN('✅ Ready to cook. Run preflight, then pick a recipe:')}")
        print(f"     {DIM('cliron-chef preflight')}")
        print(f"     {DIM('cliron-chef cook salmon_basic')}")
    elif not probe or (probe.get("lastStatusCmd") or {}).get("cmdData", {}).get("globalStatus") != "online":
        print("  " + YELLOW('🔌 Wake the Sync ONE probe (hold "O" button 3 sec)'))
    else:
        print(f"  {DIM('State unclear — inspect raw output above')}")
    print()
    return 0


def cmd_preflight(args):
    # Defer to the standalone script (or replicate inline)
    import subprocess
    from pathlib import Path
    script = Path(__file__).resolve().parents[2] / "scripts" / "preflight.py"
    if not script.is_file():
        # If script not present, do a minimal inline check
        print(YELLOW("Note: scripts/preflight.py not found; running minimal inline check"), file=sys.stderr)
        try:
            api = TyphurAPI.from_cached_credentials()
            api.list_devices()
            print(GREEN("✓ Minimal check passed"))
            return 0
        except Exception as e:
            print(RED(f"✗ Check failed: {e}"), file=sys.stderr)
            return 2
    return subprocess.call([sys.executable, str(script)])


def cmd_cook(args):
    if args.recipe_file:
        recipe = json.load(open(args.recipe_file))
    elif args.recipe:
        recipe = load_recipe(args.recipe)
    elif args.interactive:
        recipes = list_recipes()
        if not recipes:
            print(RED("No recipes available."), file=sys.stderr)
            return 1
        for i, r in enumerate(recipes, 1):
            print(f"  {i}. {r['display_name']} ({r['protein']}) — pull at {r['pull_temp_f']}°F")
        choice = input(f"Pick (1-{len(recipes)}): ").strip()
        try:
            recipe = load_recipe(recipes[int(choice) - 1]["name"])
        except (ValueError, IndexError):
            print(RED("Invalid selection."), file=sys.stderr)
            return 1
    else:
        print(RED("Specify a recipe name, --recipe-file, or --interactive"), file=sys.stderr)
        return 1

    # Override pull temp
    if args.pull_temp_f is not None:
        recipe["pull_temp_f"] = args.pull_temp_f

    api = TyphurAPI.from_cached_credentials()
    try:
        runner = RecipeRunner(api, recipe=recipe, dome_id=args.dome_id,
                              probe_id=args.probe_id, dry_run=args.dry_run)
    except RecipeError as e:
        print(RED(f"Recipe error: {e}"), file=sys.stderr)
        return 1

    try:
        runner.run(max_minutes=args.max_minutes)
    except KeyboardInterrupt:
        print(YELLOW("\nInterrupted by user. Sending STOP for safety..."))
        api.stop_cook("AF04", runner.dome_id, cook_uuid=runner.cook_uuid)
        return 130

    return 0


def cmd_modify(args):
    api = TyphurAPI.from_cached_credentials()
    dome = api.find_dome()
    if not dome:
        print(RED("No Dome 2 found."), file=sys.stderr)
        return 1
    last_cmd = dome.get("lastStatusCmd") or {}
    cook_uuid = args.cook_uuid or (last_cmd.get("cmdData") or {}).get("cookUuid", "")
    if not cook_uuid:
        print(RED("No active cookUuid. Pass --cook-uuid."), file=sys.stderr)
        return 1
    if not args.yes:
        confirm = input(f"Hot-modify active cook? mode={args.mode} temp={args.temp}°F time={args.time}s [y/N] ")
        if confirm.lower() != "y":
            return 1
    result = api.hot_modify("AF04", str(dome["deviceId"]), cook_uuid,
                             args.mode, args.temp, args.time)
    print(json.dumps({"sent": "modify", "cookUuid": cook_uuid, "result": result}, default=str))
    return 0


def cmd_stop(args):
    api = TyphurAPI.from_cached_credentials()
    dome = api.find_dome()
    if not dome:
        print(RED("No Dome 2 found."), file=sys.stderr)
        return 1
    if not args.yes:
        confirm = input("Stop the active cook? [y/N] ")
        if confirm.lower() != "y":
            return 1
    result = api.stop_cook("AF04", str(dome["deviceId"]))
    print(json.dumps({"sent": "stop", "result": result}, default=str))
    return 0


def cmd_monitor(args):
    api = TyphurAPI.from_cached_credentials()
    dome_id = args.dome_id
    probe_id = args.probe_id
    if not dome_id and not args.probe_only:
        dome = api.find_dome()
        if dome:
            dome_id = str(dome["deviceId"])
    if not probe_id and not args.dome_only:
        probe = api.find_probe()
        if probe:
            probe_id = str(probe["deviceId"])
    tail_telemetry(api, dome_id, probe_id, seconds=args.seconds)
    return 0


def cmd_recipes_list(args):
    recipes = list_recipes()
    if args.protein:
        recipes = [r for r in recipes if args.protein.lower() in (r.get("protein") or "").lower()]
    if not recipes:
        print("No recipes found.")
        return 0
    print(f"{'NAME':<30} {'PROTEIN':<35} {'PULL °F':>8}  DESCRIPTION")
    print("-" * 100)
    for r in recipes:
        print(f"{r['name']:<30} {(r.get('protein') or '?')[:34]:<35} "
              f"{(r.get('pull_temp_f') or '?'):>8}  {r.get('description', '')[:40]}")
    return 0


def cmd_recipes_show(args):
    r = load_recipe(args.name)
    print(json.dumps(r, indent=2))
    return 0


def cmd_recipes_validate(args):
    try:
        with open(args.file) as f:
            r = json.load(f)
        api = TyphurAPI(token="none")  # don't need login for validation
        # Use the runner's validation (without actually running)
        RecipeRunner(api, recipe=r, dome_id="dummy", probe_id="dummy")._validate_recipe()
    except Exception as e:
        print(RED(f"✗ Invalid: {e}"), file=sys.stderr)
        return 1
    print(GREEN("✓ Recipe is valid"))
    return 0


def cmd_modes_list(args):
    modes = list(AF04_MODES.items())
    if args.element:
        modes = [(name, info) for name, info in modes if info["element_bias"] == args.element]
    print(f"{'ID':>3}  {'MODE':<14} {'ELEMENT':<11} {'FAN':<7} {'DEFAULT':<8} {'RANGE':<14}  BEST FOR")
    print("-" * 110)
    for name, info in sorted(modes, key=lambda x: x[1]["id"]):
        print(f"{info['id']:>3}  {name:<14} {info['element_bias']:<11} {info['fan']:<7} "
              f"{info['default_temp_f']:>4}°F   {info['temp_min']}-{info['temp_max']}°F     "
              f"{info.get('best_for', '')[:50]}")
    return 0


# -- argparse wiring -----------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(
        prog="cliron-chef",
        description="CLI / AI-agent control of the Typhur Dome 2 + Sync ONE probe",
    )
    p.add_argument("--version", action="version", version=f"cliron-chef {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    # login
    sp = sub.add_parser("login", help="Authenticate with Typhur cloud")
    sp.add_argument("--email")
    sp.add_argument("--password")
    sp.add_argument("--region", choices=["US", "EU"])
    sp.add_argument("-y", "--yes", action="store_true")
    sp.set_defaults(func=cmd_login)

    # info
    sub.add_parser("info", help="List bound devices (raw JSON)").set_defaults(func=cmd_info)

    # status
    sub.add_parser("status", help="Pretty-printed device state").set_defaults(func=cmd_status)

    # preflight
    sub.add_parser("preflight", help="Safety check before cooking").set_defaults(func=cmd_preflight)

    # cook
    sp = sub.add_parser("cook", help="Run a declarative recipe")
    sp.add_argument("recipe", nargs="?", help="Recipe name (or use --recipe-file or --interactive)")
    sp.add_argument("--recipe-file", help="Path to a recipe JSON file")
    sp.add_argument("--interactive", "-i", action="store_true", help="Pick recipe from menu")
    sp.add_argument("--pull-temp-f", type=float, help="Override the recipe's pull_temp_f")
    sp.add_argument("--dome-id")
    sp.add_argument("--probe-id")
    sp.add_argument("--dry-run", action="store_true", help="Validate + show payloads but don't actually send")
    sp.add_argument("--max-minutes", type=float, default=25.0)
    sp.set_defaults(func=cmd_cook)

    # modify
    sp = sub.add_parser("modify", help="Hot-modify the active cook")
    sp.add_argument("--mode", type=int, required=True)
    sp.add_argument("--temp", type=int, required=True)
    sp.add_argument("--time", type=int, default=2400)
    sp.add_argument("--cook-uuid")
    sp.add_argument("-y", "--yes", action="store_true")
    sp.set_defaults(func=cmd_modify)

    # stop
    sp = sub.add_parser("stop", help="Stop the active cook")
    sp.add_argument("-y", "--yes", action="store_true")
    sp.set_defaults(func=cmd_stop)

    # monitor
    sp = sub.add_parser("monitor", help="Stream live MQTT telemetry")
    sp.add_argument("--dome-id")
    sp.add_argument("--probe-id")
    sp.add_argument("--probe-only", action="store_true")
    sp.add_argument("--dome-only", action="store_true")
    sp.add_argument("--seconds", type=int, default=300)
    sp.set_defaults(func=cmd_monitor)

    # recipes
    sp_r = sub.add_parser("recipes", help="Recipe management")
    sub_r = sp_r.add_subparsers(dest="recipes_cmd", required=True)
    sp = sub_r.add_parser("list")
    sp.add_argument("--protein")
    sp.set_defaults(func=cmd_recipes_list)
    sp = sub_r.add_parser("show")
    sp.add_argument("name")
    sp.set_defaults(func=cmd_recipes_show)
    sp = sub_r.add_parser("validate")
    sp.add_argument("file")
    sp.set_defaults(func=cmd_recipes_validate)

    # modes
    sp_m = sub.add_parser("modes", help="Mode reference")
    sub_m = sp_m.add_subparsers(dest="modes_cmd", required=True)
    sp = sub_m.add_parser("list")
    sp.add_argument("--element", choices=["top", "bottom", "both", "top-only", "bottom-only"])
    sp.set_defaults(func=cmd_modes_list)

    args = p.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
