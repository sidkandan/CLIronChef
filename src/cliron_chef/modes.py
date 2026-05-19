"""AF04 (Typhur Dome 2) cooking-mode constants + element-bias / fan-speed metadata.

This module is the SINGLE SOURCE OF TRUTH for mode information. It combines:
- The bundled AF04 mode dictionary (`data/modes/af04_modes.json`)
- The element-bias / fan-speed info from Typhur's modes guide
  (https://explore.typhur.com/typhur-dome-cooking-modes)

The element-bias info is NOT in the JSON dictionary — it's the missing piece that
determines whether a mode is right for skin-down protein vs top-coated items. See
docs/cooking/MODES.md for the full discussion.
"""

from __future__ import annotations

from typing import Dict, Optional

# Cook-action enum values (cookingAction integer in cmdData)
ACTION_START = 1
ACTION_PAUSE = 2  # AVOID — terminal in firmware
ACTION_CONTINUE = 3  # never useful (PAUSE is unusable)
ACTION_STOP = 4

# Cooking-state integer enum (cmdData.cookingState)
COOKING_STATE_PAUSED = 0
COOKING_STATE_COOKING = 3
COOKING_STATE_STUCK = 5  # undocumented; stuck-state-5 bug


# --- AF04 mode metadata --------------------------------------------------------
# Each entry has:
#   - id: cookingMode integer
#   - name: display name
#   - group: "Modes" | "Presets" | "Self Cleaning"
#   - element_bias: "top" | "bottom" | "both" | "top-only" | "bottom-only"
#   - fan: "high" | "medium" | "low"
#   - default_temp_f / temp_min / temp_max (°F)
#   - default_time_s / time_min_s / time_max_s
#   - best_for: short description of intended use
#   - has_preheat: True/False (only Pizza + Steak have explicit preheat config)
#   - notes: any gotchas

AF04_MODES: Dict[str, dict] = {
    "Air Fry": {
        "id": 1,
        "group": "Modes",
        "element_bias": "top",
        "fan": "high",
        "default_temp_f": 330,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 1020,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Fries, wings, top-crisp items. NOT delicate proteins with surface coatings.",
        "has_preheat": False,
    },
    "Toast": {
        "id": 2,
        "group": "Modes",
        "element_bias": "bottom",
        "fan": "low",
        "default_temp_f": 385,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 300,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Bread, light browning.",
        "has_preheat": False,
    },
    "Grill": {
        "id": 3,
        "group": "Modes",
        "element_bias": "bottom",
        "fan": "high",
        "default_temp_f": 450,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 600,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Skin-down protein, crispy skin from below, fish, fatty cuts.",
        "has_preheat": False,
        "notes": "Bottom-element bias is the key. Counter-intuitive name; not outdoor grill.",
    },
    "Reheat": {
        "id": 4,
        "group": "Modes",
        "element_bias": "both",
        "fan": "low",
        "default_temp_f": 375,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 300,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Optional warm-hold cue at 180°F. Gentle reheat for leftovers.",
        "has_preheat": False,
    },
    "Pizza": {
        "id": 5,
        "group": "Presets",
        "element_bias": "both",
        "fan": "high",
        "default_temp_f": 340,
        "temp_min": 210,
        "temp_max": 400,
        "default_time_s": 840,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Frozen pizza. Two-touch cook (preheat phase, then load).",
        "has_preheat": True,
        "preheat": {"temp_f": 450, "time_s": 480, "fan_speed": 1600, "heat_priority": "down-first"},
        "notes": "Max temp is 400°F (capped); preset constraint.",
    },
    "Bacon": {
        "id": 6,
        "group": "Presets",
        "element_bias": "top",
        "fan": "medium",
        "default_temp_f": 335,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 780,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Bacon. Medium fan keeps grease spatter contained.",
        "has_preheat": False,
    },
    "Steak": {
        "id": 7,
        "group": "Presets",
        "element_bias": "both",
        "fan": "high",
        "default_temp_f": 450,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 600,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Thick steaks (1.5\"+) — has mandatory 450°F preheat phase.",
        "has_preheat": True,
        "preheat": {"temp_f": 450, "time_s": 480, "fan_speed": 1600, "heat_priority": "down-first"},
        "notes": "Two-touch cook. For one-touch high-heat sear, use Grill (3) instead.",
    },
    "Wings": {
        "id": 8,
        "group": "Presets",
        "element_bias": "top",
        "fan": "high",
        "default_temp_f": 395,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 840,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Wings. Owner consensus: bump to 410°F and 25-30 min for large wings.",
        "has_preheat": False,
    },
    "Self Clean": {
        "id": 9,
        "group": "Self Cleaning",
        "element_bias": "both",
        "fan": "high",
        "default_temp_f": 500,
        "temp_min": 500,
        "temp_max": 500,
        "default_time_s": 7200,
        "time_min_s": 3600,
        "time_max_s": 7200,
        "best_for": "Cleaning only. Don't load food. Produces smoke; ventilate kitchen.",
        "has_preheat": False,
        "notes": "Only mode that exceeds 450°F. 1-2 hour cycle.",
    },
    "Bake": {
        "id": 10,
        "group": "Modes",
        "element_bias": "top",
        "fan": "medium",
        "default_temp_f": 350,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 1200,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Gentle finish phase, even cooks, baked goods. Less drying than Air Fry.",
        "has_preheat": False,
    },
    "Griddle": {
        "id": 11,
        "group": "Modes",
        "element_bias": "bottom",
        "fan": "low",
        "default_temp_f": 375,
        "temp_min": 210,
        "temp_max": 400,
        "default_time_s": 600,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Delicate items prone to fan-blow (tortillas, pancakes). Low fan = no liner blow.",
        "has_preheat": False,
        "notes": "Max temp 400°F (capped).",
    },
    "Roast": {
        "id": 12,
        "group": "Modes",
        "element_bias": "both",
        "fan": "medium",
        "default_temp_f": 395,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 840,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Probe-driven protein cooks. Typhur's own default for AF13 probe presets.",
        "has_preheat": False,
    },
    "Dehydrate": {
        "id": 13,
        "group": "Modes",
        "element_bias": "both",
        "fan": "low",
        "default_temp_f": 175,
        "temp_min": 105,
        "temp_max": 300,
        "default_time_s": 7200,
        "time_min_s": 60,
        "time_max_s": 86400,
        "best_for": "Jerky, dried fruit. Up to 24 hours.",
        "has_preheat": False,
    },
    "Broil": {
        "id": 14,
        "group": "Modes",
        "element_bias": "top-only",
        "fan": "high",
        "default_temp_f": 450,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 480,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Short top-blast bursts (60-90s) for crust. Use sparingly.",
        "has_preheat": False,
        "notes": "Top element only. Extended broil at 450°F will scorch most foods.",
    },
    "Fries": {
        "id": 15,
        "group": "Presets",
        "element_bias": "top",
        "fan": "high",
        "default_temp_f": 330,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 1020,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "French fries. Single layer; shake at 8 min for even browning.",
        "has_preheat": False,
    },
    "Frozen": {
        "id": 16,
        "group": "Presets",
        "element_bias": "top",
        "fan": "high",
        "default_temp_f": 375,
        "temp_min": 210,
        "temp_max": 450,
        "default_time_s": 1080,
        "time_min_s": 60,
        "time_max_s": 3600,
        "best_for": "Frozen items (chicken nuggets, etc.). No need to thaw first.",
        "has_preheat": False,
    },
}


# Reverse lookup by integer ID
AF04_MODES_BY_ID: Dict[int, dict] = {v["id"]: {"name": k, **v} for k, v in AF04_MODES.items()}


def get_mode(mode_id_or_name) -> Optional[dict]:
    """Look up a mode by integer ID or string name.

    Returns the mode dict (with 'name' added) or None if not found.

    Examples:
        >>> get_mode(3)["element_bias"]
        'bottom'
        >>> get_mode("Bake")["fan"]
        'medium'
    """
    if isinstance(mode_id_or_name, int):
        return AF04_MODES_BY_ID.get(mode_id_or_name)
    if isinstance(mode_id_or_name, str):
        mode = AF04_MODES.get(mode_id_or_name)
        if mode:
            return {"name": mode_id_or_name, **mode}
    return None


def list_modes_by_element_bias(bias: str) -> list:
    """Return all modes matching the given element bias.

    bias: 'top' | 'bottom' | 'both' | 'top-only' | 'bottom-only'
    """
    return [
        {"name": name, **info}
        for name, info in AF04_MODES.items()
        if info["element_bias"] == bias
    ]


def validate_mode_params(mode_id: int, temp_f: float, time_s: int) -> Optional[str]:
    """Validate that temp/time are in range for the given mode.

    Returns None if valid, or an error string if not.
    """
    mode = AF04_MODES_BY_ID.get(mode_id)
    if not mode:
        return f"Unknown mode ID: {mode_id}"
    if not (mode["temp_min"] <= temp_f <= mode["temp_max"]):
        return (
            f"Temperature {temp_f}°F out of range for {mode['name']} "
            f"({mode['temp_min']}-{mode['temp_max']}°F)"
        )
    if not (mode["time_min_s"] <= time_s <= mode["time_max_s"]):
        return (
            f"Time {time_s}s out of range for {mode['name']} "
            f"({mode['time_min_s']}-{mode['time_max_s']}s)"
        )
    return None
