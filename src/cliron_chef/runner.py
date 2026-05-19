"""Declarative recipe runner.

Reads a recipe JSON, configures the initial cook on the Dome 2, waits for the user to
press Start, then hot-modifies the cook through probe-driven phase transitions until the
pull-temp target is reached.

See docs/cooking/RECIPES.md for the JSON schema.
"""

from __future__ import annotations

import json
import logging
import sysconfig
import time
from pathlib import Path
from typing import Optional

from cliron_chef.api import TyphurAPI
from cliron_chef.modes import AF04_MODES_BY_ID, validate_mode_params
from cliron_chef.mqtt_client import TyphurMQTT, tenths_to_f

log = logging.getLogger("cliron_chef.runner")


# Recipe done-signal mechanisms
DONE_SIGNAL_STOP = "stop"
DONE_SIGNAL_WARM_HOLD = "warm_hold"
VALID_DONE_SIGNALS = {DONE_SIGNAL_STOP, DONE_SIGNAL_WARM_HOLD}

# Probe-driven cooks should not end by countdown expiry. Keep a large timer buffer
# alive and end by STOP, or by an explicit warm-hold mode if the recipe opts into it.
DEFAULT_TIMER_BUFFER_S = 2400
DEFAULT_TIMER_REFRESH_GUARD_S = 300
TIMER_REFRESH_COOLDOWN_S = 60

# Default warm-hold cue (Dehydrate at 180°F for 10 min; Reheat minimum is 210°F)
DEFAULT_WARM_HOLD_MODE = 13
DEFAULT_WARM_HOLD_TEMP_F = 180
DEFAULT_WARM_HOLD_TIME_S = 600


class RecipeError(Exception):
    """Raised when a recipe JSON is invalid or contains nonsensical phase ordering."""


class RecipeRunner:
    """Run a declarative recipe end-to-end.

    Usage:
        api = TyphurAPI.from_cached_credentials()
        runner = RecipeRunner(api, recipe_path="recipes/salmon_basic.json")
        runner.run()
    """

    def __init__(self, api: TyphurAPI, recipe_path: Optional[str] = None,
                 recipe: Optional[dict] = None,
                 dome_id: Optional[str] = None, probe_id: Optional[str] = None,
                 log_dir: Optional[Path] = None, dry_run: bool = False,
                 timer_refresh_guard_s: int = DEFAULT_TIMER_REFRESH_GUARD_S):
        self.api = api
        self.dry_run = dry_run

        if recipe is not None:
            self.recipe = recipe
        elif recipe_path:
            with open(recipe_path) as f:
                self.recipe = json.load(f)
        else:
            raise RecipeError("Must provide either recipe_path or recipe dict")

        self._validate_recipe()

        # Auto-detect device IDs if not provided
        if dome_id:
            self.dome_id = dome_id
        elif self.recipe.get("dome2_id"):
            self.dome_id = str(self.recipe["dome2_id"])
        else:
            dome = api.find_dome()
            if not dome:
                raise RecipeError("No AF04 Dome 2 found in bound devices. Pass --dome-id.")
            self.dome_id = str(dome["deviceId"])

        if probe_id:
            self.probe_id = probe_id
        elif self.recipe.get("probe_id"):
            self.probe_id = str(self.recipe["probe_id"])
        else:
            probe = api.find_probe()
            if not probe:
                raise RecipeError("No WT01 probe found in bound devices. Pass --probe-id.")
            self.probe_id = str(probe["deviceId"])

        # Sort phases by trigger temp
        self.phases = sorted(self.recipe["phases"], key=lambda p: p["trigger_temp_f"])
        self.pull_temp_f = float(self.recipe["pull_temp_f"])

        # Done-signal config
        self.done_signal = self.recipe.get("done_signal", DONE_SIGNAL_STOP)
        self.warm_hold_mode = self.recipe.get("warm_hold_mode", DEFAULT_WARM_HOLD_MODE)
        self.warm_hold_temp_f = self.recipe.get("warm_hold_temp_f", DEFAULT_WARM_HOLD_TEMP_F)
        self.warm_hold_time_s = self.recipe.get("warm_hold_time_s", DEFAULT_WARM_HOLD_TIME_S)
        self.timer_refresh_guard_s = int(timer_refresh_guard_s)

        # State during cook
        self.cook_uuid: Optional[str] = None
        self.current_phase_idx = -1
        self.dome_started = False
        self.pull_triggered = False
        self.started_at: Optional[float] = None
        self.last_probe_f: float = 0.0
        self.last_chamber_f: float = 0.0
        self.last_remain_s: Optional[int] = None
        self.last_mode: Optional[int] = None
        self.last_set_temp_f: Optional[float] = None
        self.last_timer_refresh_at: Optional[float] = None

        # Telemetry log
        self.log_dir = log_dir or (Path.cwd() / "runs")
        self.log_dir.mkdir(exist_ok=True)
        self._log_path = self.log_dir / f"{time.strftime('%Y%m%dT%H%M%S')}.jsonl"
        self._log_file = None

    def _validate_recipe(self):
        required = ["name", "pull_temp_f", "phases"]
        for key in required:
            if key not in self.recipe:
                raise RecipeError(f"Recipe missing required field: {key}")
        done_signal = self.recipe.get("done_signal", DONE_SIGNAL_STOP)
        if done_signal not in VALID_DONE_SIGNALS:
            raise RecipeError(
                f"Invalid done_signal '{done_signal}'. Expected one of {sorted(VALID_DONE_SIGNALS)}"
            )
        if done_signal == DONE_SIGNAL_WARM_HOLD:
            err = validate_mode_params(
                self.recipe.get("warm_hold_mode", DEFAULT_WARM_HOLD_MODE),
                self.recipe.get("warm_hold_temp_f", DEFAULT_WARM_HOLD_TEMP_F),
                self.recipe.get("warm_hold_time_s", DEFAULT_WARM_HOLD_TIME_S),
            )
            if err:
                raise RecipeError(f"Warm-hold cue is invalid: {err}")
        phases = self.recipe["phases"]
        if not phases:
            raise RecipeError("Recipe has no phases")
        for i, p in enumerate(phases):
            for field in ("trigger_temp_f", "mode", "temp_f", "time_s"):
                if field not in p:
                    raise RecipeError(f"Phase {i} missing field: {field}")
            err = validate_mode_params(p["mode"], p["temp_f"], p["time_s"])
            if err:
                raise RecipeError(f"Phase {i} ({p.get('name', '?')}): {err}")
            if int(p["time_s"]) < DEFAULT_TIMER_BUFFER_S:
                raise RecipeError(
                    f"Phase {i} ({p.get('name', '?')}) uses time_s={p['time_s']}. "
                    f"Use time_s={DEFAULT_TIMER_BUFFER_S}; timer zero is terminal."
                )
        # Phase 0 must trigger at 0.0
        if phases[0]["trigger_temp_f"] != 0.0:
            raise RecipeError("First phase (Phase 0) must have trigger_temp_f: 0.0")
        # Pull temp should be higher than max phase trigger
        max_phase_trigger = max(p["trigger_temp_f"] for p in phases)
        if self.recipe["pull_temp_f"] <= max_phase_trigger:
            raise RecipeError(
                f"pull_temp_f ({self.recipe['pull_temp_f']}) must be > highest phase "
                f"trigger ({max_phase_trigger})"
            )

    def _log(self, event: str, **fields):
        """Append a JSONL event to the log file."""
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event}
        entry.update(fields)
        if self._log_file:
            self._log_file.write(json.dumps(entry) + "\n")
            self._log_file.flush()

    def _print(self, msg: str, **kwargs):
        """Print a user-facing message."""
        print(msg, flush=True, **kwargs)

    def _send_phase(self, phase_idx: int, is_initial: bool = False) -> dict:
        """Configure (or hot-modify to) the given phase."""
        phase = self.phases[phase_idx]
        mode = phase["mode"]
        temp_f = phase["temp_f"]
        time_s = phase["time_s"]
        name = phase.get("name", f"Phase {phase_idx}")

        if self.dry_run:
            mode_name = AF04_MODES_BY_ID.get(mode, {}).get("name", "?")
            self._print(f"[DRY-RUN] Would send: mode={mode} ({mode_name}) temp={temp_f}°F time={time_s}s — {name}")
            return {}

        result, cook_uuid = self.api.start_cook(
            "AF04", self.dome_id,
            [{"cookingMode": mode, "setTemperature": temp_f, "setTime": time_s}],
            cook_uuid=self.cook_uuid,
        )
        if is_initial:
            self.cook_uuid = cook_uuid
        return result

    def _send_done_signal(self):
        if self.dry_run:
            self._print(f"[DRY-RUN] Would send done signal: {self.done_signal}")
            return

        if self.done_signal == DONE_SIGNAL_WARM_HOLD:
            self._print(
                f"🎯 DONE SIGNAL — hot-swap to mode {self.warm_hold_mode} @ "
                f"{self.warm_hold_temp_f}°F for {self.warm_hold_time_s}s warm-hold"
            )
            self._print("   Pull promptly; warm-hold is an opt-in cue, not unattended cooking.")
            self.api.start_cook(
                "AF04", self.dome_id,
                [{"cookingMode": self.warm_hold_mode,
                  "setTemperature": self.warm_hold_temp_f,
                  "setTime": self.warm_hold_time_s}],
                cook_uuid=self.cook_uuid,
            )
            self._log("done_warm_hold",
                      probe_f=self.last_probe_f,
                      warm_hold_temp_f=self.warm_hold_temp_f)
        else:  # DONE_SIGNAL_STOP
            self._print("🎯 DONE SIGNAL — sending STOP (cookingAction=4)")
            self.api.stop_cook("AF04", self.dome_id, cook_uuid=self.cook_uuid)
            self._log("done_stop", probe_f=self.last_probe_f)

    def _refresh_timer_buffer(self):
        """Keep the active cook from ending by countdown expiry."""
        if not self.dome_started or self.pull_triggered:
            return

        now = time.monotonic()
        if self.last_timer_refresh_at and now - self.last_timer_refresh_at < TIMER_REFRESH_COOLDOWN_S:
            return

        mode = self.last_mode
        temp_f = self.last_set_temp_f
        if mode is None or temp_f is None:
            if 0 <= self.current_phase_idx < len(self.phases):
                phase = self.phases[self.current_phase_idx]
                mode = int(phase["mode"])
                temp_f = float(phase["temp_f"])
            else:
                self._log("timer_refresh_skipped", reason="missing_active_phase")
                return

        self.last_timer_refresh_at = now
        self._print(
            f"⏱️  Timer low ({self.last_remain_s}s). Refreshing active "
            f"mode {mode} @ {int(round(temp_f))}°F to {DEFAULT_TIMER_BUFFER_S}s."
        )
        self._log(
            "timer_refresh",
            remaining_s=self.last_remain_s,
            mode=mode,
            temp_f=temp_f,
            timer_s=DEFAULT_TIMER_BUFFER_S,
        )
        if not self.dry_run:
            self.api.hot_modify(
                "AF04",
                self.dome_id,
                self.cook_uuid,
                int(mode),
                int(round(temp_f)),
                DEFAULT_TIMER_BUFFER_S,
            )

    def _check_phase_transition(self):
        """Called on every probe sample. Fires phase transitions or pull signal."""
        if self.pull_triggered:
            return

        # Check for pull
        if self.last_probe_f >= self.pull_temp_f:
            self.pull_triggered = True
            self._send_done_signal()
            return

        # Check for next phase
        next_idx = self.current_phase_idx + 1
        if next_idx < len(self.phases):
            next_phase = self.phases[next_idx]
            if self.last_probe_f >= next_phase["trigger_temp_f"]:
                self.current_phase_idx = next_idx
                self._print(
                    f"🔥 Phase transition at probe {self.last_probe_f:.1f}°F → "
                    f"{next_phase.get('name', f'Phase {next_idx}')}"
                )
                self._log("phase_transition",
                          probe_f=self.last_probe_f,
                          to_phase=next_idx,
                          to_mode=next_phase["mode"],
                          to_temp_f=next_phase["temp_f"])
                self._send_phase(next_idx)

    def _on_probe(self, probe_data: dict):
        internal_f = tenths_to_f(probe_data.get("curTemperature"))
        ambient_f = tenths_to_f(probe_data.get("curAmbientTemperature"))
        self.last_probe_f = internal_f
        elapsed = int(time.monotonic() - self.started_at) if self.started_at else 0

        # Only print every Nth sample to avoid spam
        self._probe_count = getattr(self, "_probe_count", 0) + 1
        if self._probe_count % 10 == 1:
            self._print(
                f"📡 t+{elapsed//60}:{elapsed%60:02d}  probe {internal_f:.1f}°F  "
                f"ambient {ambient_f:.0f}°F"
            )

        self._log("probe", internal_f=internal_f, ambient_f=ambient_f, elapsed_s=elapsed)

        if self.dome_started:
            self._check_phase_transition()

    def _on_dome(self, dome_data: dict):
        cooking_state = dome_data.get("cookingState")
        chamber_f = tenths_to_f(dome_data.get("curTemperature"))
        remain = dome_data.get("curRemainingTime")
        params = dome_data.get("setParams") or []
        self.last_chamber_f = chamber_f
        self.last_remain_s = remain
        if params:
            stage_index = max(0, int(dome_data.get("cookingStage") or 1) - 1)
            active = params[min(stage_index, len(params) - 1)]
            self.last_mode = active.get("cookingMode")
            self.last_set_temp_f = tenths_to_f(active.get("setTemperature"))

        # Detect cook start
        if not self.dome_started and cooking_state and cooking_state > 0:
            self.dome_started = True
            self.started_at = time.monotonic()
            self.current_phase_idx = 0
            cu = dome_data.get("cookUuid")
            if cu and not self.cook_uuid:
                self.cook_uuid = cu
            self._print(f"🟢 Cook started! cookUuid={self.cook_uuid}")
            self._log("cook_start", cook_uuid=self.cook_uuid)

        if remain is not None and not self.pull_triggered:
            if remain <= 0:
                self._print(
                    "⚠️  Timer reached 0. Treat this cook session as terminal; "
                    "a new cook requires another physical Start press."
                )
                self._log("timer_zero_terminal", probe_f=self.last_probe_f)
            elif remain < self.timer_refresh_guard_s:
                self._refresh_timer_buffer()

    def run(self, max_minutes: float = 25.0, start_timeout_s: int = 180):
        """Run the recipe end-to-end. Blocks until cook completes or max_minutes hits."""
        self._log_file = open(self._log_path, "a")
        self._log("runner_start",
                  recipe_name=self.recipe["name"],
                  pull_temp_f=self.pull_temp_f,
                  done_signal=self.done_signal,
                  dome_id=self.dome_id,
                  probe_id=self.probe_id)

        try:
            # Print recipe summary
            self._print(f"🔥 SMART COOK RUNNER — {self.recipe['name']}")
            self._print(f"   Pull at probe {self.pull_temp_f}°F → {self.done_signal}")
            for i, p in enumerate(self.phases):
                mode_name = AF04_MODES_BY_ID.get(p["mode"], {}).get("name", "?")
                if i == 0:
                    self._print(f"   Phase 0 (initial): {mode_name} (mode {p['mode']}) @ {p['temp_f']}°F")
                else:
                    self._print(f"   Phase {i} @ probe {p['trigger_temp_f']}°F: "
                                f"{mode_name} (mode {p['mode']}) @ {p['temp_f']}°F")

            # Configure initial cook
            self._print("\n✅ Configuring initial cook on Dome 2...")
            self._send_phase(0, is_initial=True)
            self._print(f"   cookUuid: {self.cook_uuid}")
            self._print(f"   Display now shows: mode {self.phases[0]['mode']} · "
                        f"{self.phases[0]['temp_f']}°F · {self.phases[0]['time_s']//60}:00")

            if self.dry_run:
                self._print("\n[DRY-RUN] Would now wait for user to press Start...")
                return

            # Prompt for Start
            self._print("\n👉 PRESS THE PHYSICAL START BUTTON ON THE DOME 2")
            self._print("   (firmware UL/IEC gate; not bypassable)")

            # Start MQTT subscriber
            mq = TyphurMQTT(self.api)
            mq.subscribe("AF04", self.dome_id)
            mq.subscribe("WT01", self.probe_id)
            mq.on_probe = self._on_probe
            mq.on_dome = self._on_dome
            mq.on_connect = lambda rc: self._print(f"[mqtt] connected rc={rc}")
            mq.start()

            # Wait for physical Start, then for cook completion (or max_minutes)
            start_deadline = time.monotonic() + start_timeout_s
            deadline = time.monotonic() + max_minutes * 60
            try:
                while time.monotonic() < deadline:
                    if not self.dome_started and time.monotonic() > start_deadline:
                        self._print(
                            f"⏱️  Start timeout ({start_timeout_s}s). Exiting; no cook started."
                        )
                        self._log("start_timeout", start_timeout_s=start_timeout_s)
                        break
                    if self.pull_triggered:
                        # Give telemetry a few seconds to confirm
                        time.sleep(5)
                        break
                    time.sleep(1)
                else:
                    self._print(f"⏱️  Hit max-minutes safety timeout ({max_minutes} min). Sending STOP.")
                    self.api.stop_cook("AF04", self.dome_id, cook_uuid=self.cook_uuid)
                    self._log("timeout", max_minutes=max_minutes)
            finally:
                mq.stop()

            # Final summary
            self._print("\n✅ Cook complete." if self.dome_started else "\nℹ️  Cook did not start.")
            self._print(f"   Final probe: {self.last_probe_f:.1f}°F")
            if self.started_at:
                self._print(f"   Total time:  {int(time.monotonic() - self.started_at)}s")
            else:
                self._print("   Total time:  cook never started")
            self._print(f"   Log:         {self._log_path}")
        finally:
            self._log("runner_end")
            if self._log_file:
                self._log_file.close()
                self._log_file = None


def load_recipe(name_or_path: str) -> dict:
    """Resolve a recipe by name (searches recipes/ and ~/.cliron-chef/recipes/) or path."""
    p = Path(name_or_path)
    if p.is_file():
        with open(p) as f:
            return json.load(f)

    # Try by name
    candidate_dirs = [
        Path.home() / ".cliron-chef" / "recipes",  # user override (shadows built-in)
        Path.cwd() / "recipes",  # source checkout
        Path(__file__).resolve().parents[2] / "recipes",  # project bundled
        Path(sysconfig.get_path("data")) / "share" / "cliron-chef" / "recipes",
    ]
    name = name_or_path
    if not name.endswith(".json"):
        name = name + ".json"
    for d in candidate_dirs:
        candidate = d / name
        if candidate.is_file():
            with open(candidate) as f:
                return json.load(f)
    raise FileNotFoundError(
        f"Recipe '{name_or_path}' not found. Tried: {[str(d / name) for d in candidate_dirs]}"
    )


def list_recipes() -> list:
    """List all available recipes (built-in + user)."""
    out = []
    seen_paths = set()
    candidate_dirs = [
        Path.cwd() / "recipes",
        Path(__file__).resolve().parents[2] / "recipes",
        Path(sysconfig.get_path("data")) / "share" / "cliron-chef" / "recipes",
        Path.home() / ".cliron-chef" / "recipes",
    ]
    for d in candidate_dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            if f.name == "schema.json":
                continue
            resolved = f.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            try:
                with open(f) as fp:
                    r = json.load(fp)
                out.append({
                    "name": f.stem,
                    "path": str(f),
                    "display_name": r.get("name", f.stem),
                    "protein": r.get("protein", "?"),
                    "pull_temp_f": r.get("pull_temp_f"),
                    "description": r.get("description", ""),
                })
            except Exception:
                pass
    return out
