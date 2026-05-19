# Recipes

Recipes are JSON files in [`recipes/`](../../recipes/) that the `cliron-chef cook` runner
executes. Each recipe declares:
- The target devices
- The pull temperature (probe core temp at which to end the cook)
- An ordered list of cooking phases, each triggered by a probe temperature

The runner handles MQTT subscription, probe-driven phase transitions, hot-modify
commands, timer-buffer maintenance, and final done-signaling.

## Quick example — salmon_basic.json

```json
{
  "name": "Salmon (basic)",
  "description": "Skin-down salmon, reverse-sear with Grill→Bake→STOP",
  "protein": "salmon, 1 inch fillet, skin-on",
  "target_doneness": "medium (silky, clean flake)",
  "final_internal_after_rest": "125-130°F",
  "pull_temp_f": 120.0,
  "done_signal": "stop",
  "phases": [
    {
      "trigger_temp_f": 0.0,
      "mode": 3,
      "temp_f": 450,
      "time_s": 2400,
      "name": "Sear (Grill 450°F — bottom-element bias for skin-down salmon)"
    },
    {
      "trigger_temp_f": 95.0,
      "mode": 10,
      "temp_f": 300,
      "time_s": 2400,
      "name": "Gentle finish (Bake 300°F — top-element, medium fan)"
    }
  ]
}
```

Run it:
```bash
cliron-chef cook salmon_basic
```

## Full schema

See [recipes/schema.json](../../recipes/schema.json) for the JSON Schema. Top-level fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✓ | Display name |
| `description` | string | ✓ | One-line summary |
| `protein` | string |   | Target ingredient (helps the user pick) |
| `target_doneness` | string |   | What the result should taste/feel like |
| `final_internal_after_rest` | string |   | Expected core temp after rest, in plain English |
| `dome2_id` | string |   | Override the auto-detected Dome 2 ID |
| `probe_id` | string |   | Override the auto-detected probe ID |
| `pull_temp_f` | number | ✓ | Probe core temp at which to fire the done signal |
| `done_signal` | string |   | `"stop"` (default) or `"warm_hold"` for an advanced low-temp cue |
| `warm_hold_mode` | int |   | If `done_signal` is `"warm_hold"`, the cookingMode to swap to (default: 13 = Dehydrate) |
| `warm_hold_temp_f` | number |   | Warm-hold cue temp (default: 180) |
| `warm_hold_time_s` | int |   | Warm-hold cue setTime (default: 600) |
| `phases` | array | ✓ | Ordered list of cooking phases (see below) |

Each phase:

| Field | Type | Required | Description |
|---|---|---|---|
| `trigger_temp_f` | number | ✓ | Probe core temp that triggers this phase (Phase 0 must use 0.0) |
| `mode` | int | ✓ | AF04 cookingMode integer (1=Air Fry, 3=Grill, 10=Bake, etc. — see [MODES.md](MODES.md)) |
| `temp_f` | number | ✓ | Target chamber temp in Fahrenheit |
| `time_s` | int | ✓ | Timer buffer in seconds — **always use 2400** (40 min); the probe controls the actual pull |
| `name` | string |   | Human-readable label for logging |

## How phase transitions work

1. The runner subscribes to probe MQTT telemetry
2. As each probe sample arrives, it checks every phase's `trigger_temp_f`
3. The HIGHEST trigger temp that the probe has crossed becomes the active phase
4. If the active phase has changed since the last sample, the runner sends a hot-modify
   command to the Dome (same cookUuid, single-stage, new mode/temp/time)
5. When the probe crosses `pull_temp_f`, the runner sends STOP unless the recipe
   explicitly opts into `done_signal: "warm_hold"`
6. The runner exits after the done signal is acknowledged

Phase 0 (the initial phase, `trigger_temp_f: 0.0`) is the cook the user actually starts
with. It's configured on the Dome BEFORE the user presses Start.

## Writing a new recipe

### Step 1 — Decide the cooking strategy

Read [MODES.md](MODES.md) to pick modes by element bias. For most proteins:
- Skin-down → Grill (3) for sear → Bake (10) for finish → STOP
- Reverse-sear thick cuts → Bake (10) gentle → Broil (14) finish → STOP
- Single-mode even cooks (chicken breast, white fish) → Bake (10) start to finish

### Step 2 — Decide the target temps

From the [AF13 probe presets](../../data/modes/af04_probe_presets.json) (Typhur's own
recommended pull temps):

| Protein | Typhur chef's choice |
|---|---|
| Beef medium | 130°F |
| Pork medium | 145°F |
| Chicken (whole-bird) | 165°F |
| Fish medium | 122°F |
| Whole chicken | 155°F |

These are CONSERVATIVE chef-target temps (lower than USDA). For salmon, 120°F probe →
125-130°F final after rest is the "silky medium" target. For chicken breast, 155°F probe →
162°F final is safe + juicy.

### Step 3 — Write the JSON

Copy an existing recipe. Adjust phases. Make sure:
- `phases[0].trigger_temp_f` is `0.0`
- Each subsequent phase has a higher `trigger_temp_f`
- `pull_temp_f` is higher than the highest phase's `trigger_temp_f`
- All `time_s` values are `2400` (40 min buffer)

### Step 4 — Validate

```bash
cliron-chef recipes validate path/to/your_recipe.json
```

This checks against the JSON Schema. Errors will be specific (missing field, wrong type,
out-of-range value).

### Step 5 — Test cook

Actually cook it. Watch the device. Note:
- Did each phase transition fire at the expected probe temp?
- Did the pull/done signal work as designed?
- Did the food come out as expected after rest?

Adjust accordingly and re-cook.

### Step 6 — Contribute back

If your recipe works well, [open a PR](../../CONTRIBUTING.md) so others can use it.

## Examples library

| Recipe | What it demonstrates |
|---|---|
| [`salmon_basic.json`](../../recipes/salmon_basic.json) | Standard 2-phase reverse-sear, STOP done signal |
| [`salmon_gourmet.json`](../../recipes/salmon_gourmet.json) | Advanced Dehydrate 180°F cue variant; pull promptly |
| [`steak_reverse_sear.json`](../../recipes/steak_reverse_sear.json) | Reverse-sear with Broil finish (top-element blast) |
| [`chicken_thighs.json`](../../recipes/chicken_thighs.json) | Bone-in skin-down, Grill→Bake |
| [`chicken_breast.json`](../../recipes/chicken_breast.json) | Single-phase even cook (no swap; moisture priority) |
| [`pork_tenderloin.json`](../../recipes/pork_tenderloin.json) | Whole tenderloin, sear-then-gentle-finish |
| [`fish_white.json`](../../recipes/fish_white.json) | Cod / halibut / sea bass, single-phase Bake |

## Override recipe values at runtime

```bash
# Override pull temp (e.g., if you prefer salmon a little firmer)
cliron-chef cook salmon_basic --pull-temp-f 125

# Override the active device IDs
cliron-chef cook salmon_basic --dome-id <id> --probe-id <id>

# Run a recipe by file path instead of name
cliron-chef cook --recipe-file ~/my_recipes/special_salmon.json

# Dry-run (validate + show what would be sent, but don't actually send commands)
cliron-chef cook salmon_basic --dry-run
```

## Anti-patterns

❌ **Don't write a cooking phase with `time_s < 2400`.** The runner rejects unsafe short
phase timers. Warm-hold cue duration is controlled separately by `warm_hold_time_s`.

❌ **Don't write a recipe with overlapping or out-of-order `trigger_temp_f` values.** The
runner sorts phases by trigger temp, but recipes are easier to reason about when written
in order.

❌ **Don't write a recipe whose `pull_temp_f` is below the highest phase trigger.** The
runner will fire the done signal before reaching that last phase.

❌ **Don't include `cookingStageNum > 1` in any recipe.** The CLI runner always sends
single-stage cook commands. Multi-stage native cooks are firmware-supported but
intentionally not exposed (see [COOK_LIFECYCLE.md](COOK_LIFECYCLE.md)).

❌ **Don't use Mode 2 (PAUSE) or any non-existent mode ID.** Recipe validation catches
this.

## How recipes are bundled

User recipes live in two locations:
1. `recipes/` (project-bundled, included with the install)
2. `~/.cliron-chef/recipes/` (per-user, your custom recipes)

`cliron-chef cook <name>` looks in both. Per-user recipes shadow project-bundled ones if
they have the same name.

## Cross-reference

- [MODES.md](MODES.md) — pick the right cookingMode by element bias
- [COOK_LIFECYCLE.md](COOK_LIFECYCLE.md) — why setTime should always be 2400
- [recipes/schema.json](../../recipes/schema.json) — JSON Schema for validation
- [recipes/README.md](../../recipes/README.md) — recipe-folder-specific notes
