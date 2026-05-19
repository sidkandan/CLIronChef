"""Test that every warm-hold recipe uses VALID mode + temp combinations.

This test would have caught the Reheat-180°F bug — Reheat (mode 4) has temp_min=210°F,
so a recipe specifying warm_hold_mode=4 + warm_hold_temp_f=180 would be REJECTED by the
firmware at runtime. The fix is to use Dehydrate (mode 13, range 105-300°F) for warm-hold
at 180°F.

This test asserts the constraint at the test-suite level, so a future contributor can't
silently reintroduce the bug.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cliron_chef.modes import validate_mode_params

RECIPES_DIR = Path(__file__).resolve().parents[1] / "recipes"


def _warm_hold_recipes():
    """Yield (path, recipe_dict) for every recipe with done_signal=warm_hold."""
    for f in sorted(RECIPES_DIR.glob("*.json")):
        if f.name == "schema.json":
            continue
        with open(f) as fp:
            r = json.load(fp)
        if r.get("done_signal") == "warm_hold":
            yield (f, r)


@pytest.mark.parametrize(
    "path_and_recipe",
    list(_warm_hold_recipes()),
    ids=lambda pr: pr[0].name,
)
def test_warm_hold_params_valid_for_mode(path_and_recipe):
    """Warm-hold mode + temp + time must pass validate_mode_params."""
    path, recipe = path_and_recipe
    mode = recipe.get("warm_hold_mode")
    temp_f = recipe.get("warm_hold_temp_f")
    time_s = recipe.get("warm_hold_time_s")

    assert mode is not None, f"{path.name}: warm_hold_mode required when done_signal=warm_hold"
    assert temp_f is not None, f"{path.name}: warm_hold_temp_f required when done_signal=warm_hold"
    assert time_s is not None, f"{path.name}: warm_hold_time_s required when done_signal=warm_hold"

    err = validate_mode_params(mode, temp_f, time_s)
    assert err is None, (
        f"{path.name}: warm_hold params (mode={mode}, temp={temp_f}°F, time={time_s}s) "
        f"are INVALID: {err}"
    )


def test_reheat_at_180f_is_rejected():
    """Regression test for the specific bug Codex caught."""
    # Reheat (mode 4) has temp_min=210; 180°F should be rejected
    err = validate_mode_params(4, 180, 600)
    assert err is not None
    assert "out of range" in err.lower()


def test_dehydrate_at_180f_is_accepted():
    """Dehydrate (mode 13) range is 105-300°F; 180°F should be valid."""
    err = validate_mode_params(13, 180, 600)
    assert err is None


def test_no_recipe_uses_reheat_below_210():
    """Defense in depth: no recipe should set Reheat mode (4) below 210°F anywhere."""
    for f in sorted(RECIPES_DIR.glob("*.json")):
        if f.name == "schema.json":
            continue
        with open(f) as fp:
            r = json.load(fp)
        # Check warm_hold params
        if r.get("warm_hold_mode") == 4:
            assert r.get("warm_hold_temp_f", 0) >= 210, (
                f"{f.name}: Reheat mode 4 requires temp >= 210°F"
            )
        # Check all phases too
        for phase in r.get("phases", []):
            if phase.get("mode") == 4:
                assert phase.get("temp_f", 0) >= 210, (
                    f"{f.name}: phase {phase.get('name')} uses Reheat (4) at "
                    f"{phase['temp_f']}°F; must be >= 210°F"
                )
