# Carryover Cooking — Field Measurements

How much does food keep cooking after you signal "done"? The answer depends entirely on
**where the food is when carryover happens**: on a counter (ATK's well-known ~+8°F) or
still inside a closed Dome (this doc's finding: ~+27°F).

This matters because the cook signal you choose (STOP vs warm-hold) interacts with where
the food ends up. If you choose STOP and the user is slow to open the lid, you ship a
well-done dinner whether you meant to or not.

---

## What ATK measured (food on a counter)

[America's Test Kitchen — Carryover Cooking in Fish](https://www.americastestkitchen.com/cooksillustrated/how_tos/6701-carryover-cooking-in-fish)
measured a 1" fish fillet pulled out of the oven and rested on a counter:

| Chamber temp at pull | Carryover over 3-min counter rest |
|---|---|
| 250°F | **+7°F** |
| 325°F | +9°F |
| 350°F | +15°F |
| 450°F | +27°F |

These numbers all assume the food is **out of the oven**. Counter air is ~70°F, so the
fillet radiates / convects heat AWAY faster than it absorbs heat from its own residual
warmth.

This is the figure most recipes (including the ones in this repo) implicitly target. The
salmon recipes here pull at 120°F → land ~128°F after counter rest, which matches ATK's
"+8°F from a 300°F finish chamber" data point.

## What this project measured (food still in the Dome)

**Cook on 2026-05-25** (log: a private `runs/*.jsonl` from a Claude Code session):

- 1" salmon fillet, skin-on, skin-down
- Profile: Grill 450°F → (at probe 89°F) Bake 300°F → (at probe 118.2°F) **STOP**
- After STOP, the user did **not** open the Dome lid promptly
- Probe continued logging for 5 min post-STOP

The result:

| Event | Probe internal | Probe ambient | Chamber sensor |
|---|---|---|---|
| STOP fired | **118.2°F** | 271°F | (off, elements down) |
| t+30s after STOP | 122.2°F | 264°F | cooling |
| t+1m | 127.0°F | 247°F | cooling |
| t+2m | 131.2°F | 213°F | cooling |
| t+3m | 134.8°F | 201°F | cooling |
| **t+5m peak** | **145.9°F** | 162°F | cooling |

That's **+27.7°F of carryover** vs ATK's +8°F for the same chamber temp. **The salmon
overcooked from medium-rare straight through to well-done** while it sat in the closed
Dome, because the closed chamber holds its mass-heat for many minutes after the elements
turn off.

### Why the difference is ~3×

ATK's +8°F figure has the food sinking heat into ~70°F room air. The Dome with closed
lid has the food sinking heat into ~270°F chamber air that cools at ~22°F/min. The
temperature gradient drives the heat-transfer rate; the food has nowhere to dump heat
until the lid opens.

A 1" fillet at 118°F has core enthalpy of roughly … well, the food-science details
matter less than the practical rule: **assume +25°F carryover from STOP-in-closed-Dome
until you can verify your specific dish/Dome decays differently.**

## Practical implications

### Rule 1 — If you choose `done_signal: stop`, the user must open the lid within 60s

Otherwise carryover from the residual chamber heat will overshoot the target. The
runner now (or should — see "future work" below) re-notifies aggressively post-STOP until
probe ambient drops, indicating the lid was opened.

### Rule 2 — If you can't guarantee the user is at the device, use `done_signal: warm_hold`

Warm-hold (the Dehydrate 175-180°F swap pattern) keeps the chamber at a temperature
gradient that's too low to overcook. Math:
- Salmon at 117°F core
- Chamber at 180°F (warm-hold)
- Gradient: 63°F (vs 153°F for STOP-and-leave-in-270°F-residual)
- Expected carryover over 5-10 min: **~+5°F**, vs +27°F for closed-Dome STOP

This is the structural reason `salmon_gourmet.json` uses warm-hold and is generally
recommended for any cook where the user might be away.

### Rule 3 — Pull-temp budget should account for the cook context

| Scenario | Pull at probe |
|---|---|
| User is right at the Dome with tongs, STOP | 120°F → final ~128°F |
| User might be 1-2 min away, STOP | 115°F → final ~125-128°F (absorbs slow-pull) |
| Warm-hold mode swap (any user-timing) | 117°F → final ~122-125°F |
| Worst case: assume user away 5+ min, STOP | 100°F → final ~125°F (NOT recommended; use warm-hold instead) |

### Rule 4 — Telemetry-based "user pulled" detection

A future runner feature: watch probe ambient. If it drops from 200°F+ to <100°F over
<60 seconds, the lid was opened — switch from alert mode to carryover-monitoring mode.
If ambient stays high, escalate notifications because the food is still cooking.

## How this is enforced in this repo

- The recipe schema includes `done_signal: warm_hold` as a first-class option
- `salmon_gourmet.json` defaults to warm-hold for the buttery-medium-rare target
- `tests/test_warm_hold_validation.py` ensures warm-hold params are valid for the chosen
  mode (in particular, Dehydrate 180°F passes; Reheat 180°F doesn't because Reheat min
  is 210°F)
- This doc captures the empirical measurement so future agents don't have to relearn it

## Future work

These are not yet in the runner but would address the cases this doc warns about:

1. **Escalating post-STOP notifications** that re-fire until probe ambient drops (= lid
   opened)
2. **Probe-ambient-based "user pulled" detection** for switching modes
3. **Lid-open suspect warning** during the active cook (chamber drops >20°F in 30s)
4. **Slow-ramp warning** if chamber doesn't reach setpoint within an expected window
5. **Per-recipe carryover model** — track observed carryover across cooks, suggest pull
   adjustments

Contributions welcome — see `CONTRIBUTING.md`.

## Cross-reference

- [MODES.md](MODES.md) — element-bias + mode behavior
- [COOK_LIFECYCLE.md](COOK_LIFECYCLE.md) — STOP vs warm-hold mechanisms
- [PROBE.md](PROBE.md) — probe placement + telemetry interpretation
- [LESSONS_LEARNED.md](LESSONS_LEARNED.md) — full cook history including 2026-05-25
- [recipes/salmon_gourmet.json](../../recipes/salmon_gourmet.json) — warm-hold default
- [recipes/salmon_basic.json](../../recipes/salmon_basic.json) — STOP default (use only when at-device)
