"""Sanity tests for the AF04 mode table."""

from cliron_chef.modes import (
    AF04_MODES,
    AF04_MODES_BY_ID,
    get_mode,
    list_modes_by_element_bias,
    validate_mode_params,
)


def test_16_modes_total():
    assert len(AF04_MODES) == 16
    assert len(AF04_MODES_BY_ID) == 16


def test_grill_mode_is_bottom_element():
    """The key fact that decides skin-down protein cooks."""
    grill = get_mode(3)
    assert grill is not None
    assert grill["name"] == "Grill"
    assert grill["element_bias"] == "bottom"
    assert grill["temp_max"] == 450


def test_air_fry_is_top_element():
    """The mode most agents incorrectly default to for protein."""
    air_fry = get_mode(1)
    assert air_fry["element_bias"] == "top"
    assert air_fry["fan"] == "high"


def test_dehydrate_is_warm_hold_cue_appropriate():
    """Dehydrate at 180°F is the valid opt-in warm-hold cue."""
    dehydrate = get_mode(13)
    assert dehydrate["element_bias"] == "both"
    assert dehydrate["fan"] == "low"
    assert dehydrate["temp_min"] <= 180 <= dehydrate["temp_max"]


def test_self_clean_is_fixed_500f():
    sc = get_mode(9)
    assert sc["temp_min"] == sc["temp_max"] == 500


def test_pizza_max_temp_capped_400():
    """Pizza mode is intentionally capped — preset constraint."""
    pizza = get_mode(5)
    assert pizza["temp_max"] == 400


def test_griddle_max_temp_capped_400():
    griddle = get_mode(11)
    assert griddle["temp_max"] == 400


def test_dehydrate_supports_24h_timer():
    dh = get_mode(13)
    assert dh["time_max_s"] == 86400


def test_get_mode_by_name():
    assert get_mode("Bake")["id"] == 10
    assert get_mode("Grill")["element_bias"] == "bottom"


def test_get_mode_invalid():
    assert get_mode(99) is None
    assert get_mode("Nonexistent") is None


def test_list_bottom_element_modes():
    bottom_modes = list_modes_by_element_bias("bottom")
    assert any(m["name"] == "Grill" for m in bottom_modes)
    assert any(m["name"] == "Griddle" for m in bottom_modes)
    assert not any(m["name"] == "Air Fry" for m in bottom_modes)


def test_validate_mode_params_valid():
    assert validate_mode_params(3, 450, 2400) is None  # Grill 450°F 40min


def test_validate_mode_params_temp_out_of_range():
    err = validate_mode_params(11, 450, 600)  # Griddle max is 400°F
    assert err is not None
    assert "out of range" in err.lower()


def test_validate_mode_params_time_out_of_range():
    err = validate_mode_params(1, 350, 10)  # below min 60s
    assert err is not None
    assert "time" in err.lower()


def test_validate_mode_params_invalid_mode_id():
    err = validate_mode_params(99, 400, 600)
    assert err is not None
    assert "unknown" in err.lower()
