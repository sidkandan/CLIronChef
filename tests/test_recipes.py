"""Validate that all bundled recipes pass the schema check."""
import json
from pathlib import Path

import pytest

RECIPES_DIR = Path(__file__).resolve().parents[1] / "recipes"


def _all_recipe_files():
    return sorted(f for f in RECIPES_DIR.glob("*.json") if f.name != "schema.json")


@pytest.mark.parametrize("recipe_file", _all_recipe_files(), ids=lambda f: f.name)
def test_recipe_loads(recipe_file):
    """Every recipe is valid JSON."""
    with open(recipe_file) as f:
        recipe = json.load(f)
    assert "name" in recipe
    assert "pull_temp_f" in recipe
    assert "phases" in recipe


@pytest.mark.parametrize("recipe_file", _all_recipe_files(), ids=lambda f: f.name)
def test_recipe_has_phase_0_at_zero(recipe_file):
    """Phase 0 must trigger at 0.0."""
    with open(recipe_file) as f:
        recipe = json.load(f)
    phases = sorted(recipe["phases"], key=lambda p: p["trigger_temp_f"])
    assert phases[0]["trigger_temp_f"] == 0.0


@pytest.mark.parametrize("recipe_file", _all_recipe_files(), ids=lambda f: f.name)
def test_recipe_pull_temp_above_phases(recipe_file):
    """pull_temp_f must be higher than the highest phase trigger."""
    with open(recipe_file) as f:
        recipe = json.load(f)
    max_phase = max(p["trigger_temp_f"] for p in recipe["phases"])
    assert recipe["pull_temp_f"] > max_phase


@pytest.mark.parametrize("recipe_file", _all_recipe_files(), ids=lambda f: f.name)
def test_recipe_all_phases_use_2400s_timer(recipe_file):
    """All cooking phases should use 2400s (40-min) buffer per cook-lifecycle rules."""
    with open(recipe_file) as f:
        recipe = json.load(f)
    for phase in recipe["phases"]:
        assert phase["time_s"] >= 2400, (
            f"{recipe_file.name}: phase '{phase.get('name')}' has time_s={phase['time_s']}; "
            "should be 2400 per cook-lifecycle rules"
        )


@pytest.mark.parametrize("recipe_file", _all_recipe_files(), ids=lambda f: f.name)
def test_recipe_modes_valid(recipe_file):
    """All cookingMode values must be valid AF04 mode IDs."""
    from cliron_chef.modes import AF04_MODES_BY_ID
    with open(recipe_file) as f:
        recipe = json.load(f)
    for phase in recipe["phases"]:
        assert phase["mode"] in AF04_MODES_BY_ID, (
            f"{recipe_file.name}: unknown cookingMode {phase['mode']}"
        )


def test_at_least_seven_bundled_recipes():
    """Sanity check that we ship the documented set of recipes."""
    recipes = _all_recipe_files()
    assert len(recipes) >= 7, f"Expected ≥7 recipes; found {len(recipes)}"
    names = {r.stem for r in recipes}
    expected = {
        "salmon_basic", "salmon_gourmet", "steak_reverse_sear",
        "chicken_thighs", "chicken_breast", "pork_tenderloin", "fish_white",
    }
    missing = expected - names
    assert not missing, f"Missing recipes: {missing}"
