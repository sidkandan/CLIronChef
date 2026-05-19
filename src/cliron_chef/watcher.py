"""Lower-level probe watcher with mode-swap support.

Use this when you want fine-grained control beyond what the declarative RecipeRunner
provides. The RecipeRunner internally uses this pattern but exposes a JSON-driven
interface; for ad-hoc Python code or custom flows, use ProbeWatcher directly.

Example:
    api = TyphurAPI.from_cached_credentials()
    watcher = ProbeWatcher(api, dome_id="...", probe_id="...", cook_uuid="...")
    watcher.add_swap_at(95, mode=10, temp_f=300)   # phase transition
    watcher.stop_at(120)                            # done signal
    watcher.run(max_minutes=25)
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from cliron_chef.api import TyphurAPI
from cliron_chef.mqtt_client import TyphurMQTT, tenths_to_f

log = logging.getLogger("cliron_chef.watcher")


class ProbeSwapAction:
    """A single probe-threshold-triggered mode swap."""

    def __init__(self, trigger_temp_f: float, mode: int, temp_f: int,
                 time_s: int = 2400, label: str = ""):
        self.trigger_temp_f = trigger_temp_f
        self.mode = mode
        self.temp_f = temp_f
        self.time_s = time_s
        self.label = label or f"Swap to mode {mode} @ {temp_f}°F"
        self.fired = False


class ProbeWatcher:
    """Probe-driven Dome 2 controller.

    Subscribes to MQTT telemetry, fires hot-modify commands when the probe crosses
    configured thresholds. Keeps `cookingStageNum=1` and reasserts `setTime=2400` on
    every swap (per docs/cooking/COOK_LIFECYCLE.md rules).
    """

    def __init__(self, api: TyphurAPI, dome_id: str, probe_id: str,
                 cook_uuid: Optional[str] = None, timer_refresh_guard_s: int = 300):
        self.api = api
        self.dome_id = dome_id
        self.probe_id = probe_id
        self.cook_uuid = cook_uuid

        self.swaps: List[ProbeSwapAction] = []
        self.stop_at_f: Optional[float] = None

        self.last_internal_f: Optional[float] = None
        self.last_ambient_f: Optional[float] = None
        self.last_chamber_f: Optional[float] = None
        self.last_remain_s: Optional[int] = None
        self.last_mode: Optional[int] = None
        self.last_set_temp_f: Optional[float] = None
        self.last_timer_refresh_at: Optional[float] = None
        self.timer_refresh_guard_s = timer_refresh_guard_s
        self.samples = 0
        self.started_at: Optional[float] = None
        self.completed = False

    def add_swap_at(self, trigger_temp_f: float, mode: int, temp_f: int,
                    time_s: int = 2400, label: str = ""):
        """Add a mode-swap that fires when probe internal hits trigger_temp_f."""
        self.swaps.append(ProbeSwapAction(trigger_temp_f, mode, temp_f, time_s, label))
        self.swaps.sort(key=lambda s: s.trigger_temp_f)

    def stop_at(self, temp_f: float):
        """Configure a STOP command to fire when probe internal hits temp_f."""
        self.stop_at_f = temp_f

    def _fire_swap(self, swap: ProbeSwapAction):
        if swap.fired:
            return
        swap.fired = True
        log.info("Firing swap at probe %.1f°F: %s", self.last_internal_f, swap.label)
        try:
            self.api.hot_modify("AF04", self.dome_id, self.cook_uuid,
                                 swap.mode, swap.temp_f, swap.time_s)
        except Exception as e:
            log.error("Swap failed: %s", e)

    def _fire_stop(self):
        if self.completed:
            return
        self.completed = True
        log.info("Firing STOP at probe %.1f°F", self.last_internal_f)
        try:
            self.api.stop_cook("AF04", self.dome_id, cook_uuid=self.cook_uuid)
        except Exception as e:
            log.error("STOP failed: %s", e)

    def _refresh_timer_buffer(self):
        if self.completed:
            return
        now = time.monotonic()
        if self.last_timer_refresh_at and now - self.last_timer_refresh_at < 60:
            return
        if self.last_mode is None or self.last_set_temp_f is None:
            log.warning("Timer low but active mode/temp are unknown; cannot refresh safely")
            return
        if not self.cook_uuid:
            log.warning("Timer low but active cookUuid is unknown; cannot refresh safely")
            return
        self.last_timer_refresh_at = now
        log.warning(
            "Timer low (%ss); refreshing active mode=%s temp=%s°F to 2400s",
            self.last_remain_s,
            self.last_mode,
            self.last_set_temp_f,
        )
        self.api.hot_modify(
            "AF04",
            self.dome_id,
            self.cook_uuid,
            int(self.last_mode),
            int(round(self.last_set_temp_f)),
            2400,
        )

    def _on_probe(self, probe_data: dict):
        internal = tenths_to_f(probe_data.get("curTemperature"))
        ambient = tenths_to_f(probe_data.get("curAmbientTemperature"))
        self.last_internal_f = internal
        self.last_ambient_f = ambient
        self.samples += 1

        # Check swaps in order
        for swap in self.swaps:
            if not swap.fired and internal >= swap.trigger_temp_f:
                self._fire_swap(swap)
                # Don't break — multiple swaps can fire on same sample if thresholds close

        # Check STOP threshold
        if self.stop_at_f is not None and internal >= self.stop_at_f and not self.completed:
            self._fire_stop()

    def _on_dome(self, dome_data: dict):
        self.last_chamber_f = tenths_to_f(dome_data.get("curTemperature"))
        self.last_remain_s = dome_data.get("curRemainingTime")
        params = dome_data.get("setParams") or []
        if params:
            stage_index = max(0, int(dome_data.get("cookingStage") or 1) - 1)
            active = params[min(stage_index, len(params) - 1)]
            self.last_mode = active.get("cookingMode")
            self.last_set_temp_f = tenths_to_f(active.get("setTemperature"))
        cu = dome_data.get("cookUuid")
        if cu and not self.cook_uuid:
            self.cook_uuid = cu
        if self.last_remain_s is not None and not self.completed:
            if self.last_remain_s <= 0:
                log.warning("Timer reached zero; active cook should be treated as terminal")
            elif self.last_remain_s < self.timer_refresh_guard_s:
                self._refresh_timer_buffer()

    def run(self, max_minutes: float = 25.0):
        """Run the watcher. Blocks until completed or max_minutes elapses."""
        self.started_at = time.monotonic()
        mq = TyphurMQTT(self.api)
        mq.subscribe("AF04", self.dome_id)
        mq.subscribe("WT01", self.probe_id)
        mq.on_probe = self._on_probe
        mq.on_dome = self._on_dome
        mq.start()

        deadline = time.monotonic() + max_minutes * 60
        try:
            while time.monotonic() < deadline:
                if self.completed:
                    time.sleep(5)  # allow final telemetry to arrive
                    break
                time.sleep(1)
            else:
                # Safety timeout — force STOP
                log.warning("Watcher hit max_minutes safety timeout; sending STOP")
                self._fire_stop()
                time.sleep(3)
        finally:
            mq.stop()

        return {
            "samples": self.samples,
            "final_internal_f": self.last_internal_f,
            "completed": self.completed,
        }
