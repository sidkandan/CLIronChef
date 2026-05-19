# Recipes

This directory contains declarative JSON recipes for the `cliron-chef cook` runner.

## Quick start

```bash
# List available recipes
cliron-chef recipes list

# Run a recipe
cliron-chef cook salmon_basic

# Validate a recipe before running
cliron-chef recipes validate salmon_basic.json
```

## How they work

Each recipe is a JSON file declaring:
- The target devices (auto-detected by default)
- The pull temperature (probe core temp at which to fire the done signal)
- An ordered list of cooking phases, each triggered by a probe temperature

The CLI runner:
1. Sends the initial cook configuration (Phase 0) to the Dome 2
2. Prompts the user to press the physical Start button
3. Subscribes to probe telemetry
4. Hot-modifies the Dome to the next phase's mode + temp when the probe crosses
   `trigger_temp_f`
5. Sends STOP when probe hits `pull_temp_f`, unless the recipe explicitly opts into a
   warm-hold cue

## Schema

See [schema.json](schema.json) for the JSON Schema. Full docs in
[../docs/cooking/RECIPES.md](../docs/cooking/RECIPES.md).

Quick reference:
```json
{
  "name": "Display name",
  "description": "One-line summary",
  "protein": "salmon fillet, 1 inch, skin-on",
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
      "name": "Sear (Grill)"
    },
    {
      "trigger_temp_f": 95.0,
      "mode": 10,
      "temp_f": 300,
      "time_s": 2400,
      "name": "Gentle finish (Bake)"
    }
  ]
}
```

## Built-in recipes

| File | Protein | Pull at | Final | Done signal |
|---|---|---|---|---|
| `salmon_basic.json` | 1" salmon, skin-on, skin-down | 120°F | 125-130°F | STOP |
| `salmon_gourmet.json` | Same | 120°F | 125-130°F if pulled promptly | Advanced Dehydrate 180°F cue |
| `steak_reverse_sear.json` | 1.5" ribeye/strip | 125°F | 130°F | STOP |
| `chicken_thighs.json` | Bone-in skin-on | 170°F | 175°F | STOP |
| `chicken_breast.json` | Boneless skinless | 155°F | 162°F | STOP |
| `pork_tenderloin.json` | Whole tenderloin | 140°F | 145°F | STOP |
| `fish_white.json` | Cod / halibut / sea bass | 125°F | 130°F | STOP |

All cooking phases use `time_s: 2400` (40-min buffer) per the
[cook lifecycle](../docs/cooking/COOK_LIFECYCLE.md) timer rule.

## Choosing modes

Read [../docs/cooking/MODES.md](../docs/cooking/MODES.md) for the AF04 mode element-bias table. The key
insight: different modes bias heat to different elements (top vs bottom), which matters
a lot for skin-down protein.

Mode IDs you'll commonly use:
- **3** (Grill) — bottom element, high fan; best for skin-down sear
- **10** (Bake) — top element, medium fan; best for gentle finish
- **14** (Broil) — top element only, high fan; short bursts only
- **13** (Dehydrate) — both elements, low fan; valid 180°F cue only when requested
- **1** (Air Fry) — top element, high fan; for fries/wings, NOT delicate proteins

## Adding your own recipes

Two locations are searched when you run `cliron-chef cook <name>`:
1. `recipes/` (project-bundled, this directory)
2. `~/.cliron-chef/recipes/` (per-user)

Per-user recipes shadow project-bundled ones with the same name. To add a personal
recipe:

```bash
mkdir -p ~/.cliron-chef/recipes/
cp recipes/salmon_basic.json ~/.cliron-chef/recipes/salmon_my_way.json
# Edit ~/.cliron-chef/recipes/salmon_my_way.json
cliron-chef recipes validate ~/.cliron-chef/recipes/salmon_my_way.json
cliron-chef cook salmon_my_way
```

## Contributing recipes upstream

If you've test-cooked a recipe and it works well, please [open a PR](../CONTRIBUTING.md)!
Include in the PR:
- The recipe JSON
- A note in the PR description: protein source, thickness, expected vs actual outcome
- Any caveats (e.g., "best for farmed salmon; reduce 5°F for wild")

We'll review, possibly tweak naming/comments, and merge.

## Override at runtime

```bash
# Override pull temp
cliron-chef cook salmon_basic --pull-temp-f 125

# Override device IDs
cliron-chef cook salmon_basic --dome-id <id> --probe-id <id>

# Dry run (validate + show what would be sent)
cliron-chef cook salmon_basic --dry-run

# Use a file path instead of recipe name
cliron-chef cook --recipe-file /path/to/your.json
```

## Cross-reference

- [docs/cooking/RECIPES.md](../docs/cooking/RECIPES.md) — full schema documentation
- [docs/cooking/MODES.md](../docs/cooking/MODES.md) — mode element-bias table
- [docs/cooking/COOK_LIFECYCLE.md](../docs/cooking/COOK_LIFECYCLE.md) — timer rules + done signals
