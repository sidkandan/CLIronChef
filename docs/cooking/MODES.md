# Cooking Modes (AF04 Dome 2)

This is the single most important reference doc in the project. Read it before designing
any cook. **Mode choice is the lever that determines whether your dish looks restaurant-tier
or amateur-tier.**

## The element-bias / fan-speed table

The AF04 Dome 2 has dual heating elements (top + bottom) and a variable-speed fan.
Different modes bias heat differently:

| ID | Mode | Element bias | Fan | Default | Range | Best for |
|:---:|---|:---:|:---:|:---:|---|---|
| 1 | **Air Fry** | TOP | High | 330°F | 210-450°F | Fries, wings, top-crisp items, NOT delicate coatings |
| 2 | Toast | Bottom | Low | 385°F | 210-450°F | Bread |
| **3** | **Grill** | **BOTTOM** | High | 450°F | 210-450°F | Skin-down protein (salmon, chicken thighs), crispy skin |
| **4** | **Reheat** | Both (gentle) | Low | 375°F | 210-450°F | Gentle reheat for leftovers |
| 5 | Pizza (preset) | Both + preheat | High | 340°F | 210-400°F | Pizza only — has mandatory 8-min 450°F preheat |
| 6 | Bacon (preset) | Top | Med | 335°F | 210-450°F | Bacon |
| 7 | Steak (preset) | Both + preheat | High | 450°F | 210-450°F | Steak — mandatory preheat; 2-touch cook |
| 8 | Wings (preset) | Top | High | 395°F | 210-450°F | Wings |
| 9 | Self Clean | Both | High | 500°F | 500-500°F | Cleaning only; do not put food inside |
| **10** | **Bake** | TOP | **Medium** | 350°F | 210-450°F | Gentle finish, even cook, less drying |
| 11 | Griddle | Bottom | Low | 375°F | 210-400°F | Tortillas, pancakes (low fan = no liner blow) |
| **12** | **Roast** | Both | Med | 395°F | 210-450°F | Typhur's default for AF13 probe-driven protein cooks |
| 13 | Dehydrate | Both (gentle) | Low | 175°F | 105-300°F | Jerky, dried fruit; up to 24h |
| **14** | **Broil** | **TOP only** | High | 450°F | 210-450°F | Short crust blast (60-90s); use sparingly |
| 15 | Fries (preset) | Top | High | 330°F | 210-450°F | French fries |
| 16 | Frozen (preset) | Top | High | 375°F | 210-450°F | Frozen items |

The **bold rows** are the 5-6 modes you'll use 95% of the time for proteins.

## The element-bias mnemonic

```
   SKIN-DOWN protein
   ──────────────────► BOTTOM element → GRILL (3)
                       (crisps skin AND seals bottom; top of protein gets only
                        indirect convection — perfect for delicate top coatings)

   TOP-COATED item
   ──────────────────► TOP element → AIR FRY (1) or BAKE (10)
                       (browns the top directly; high fan = crispy, medium fan = moister)

   SHORT FINISHING BLAST
   ──────────────────► TOP element only → BROIL (14) for 60-90 seconds
                       (max top-down heat; use sparingly; can burn quickly)

   OPTIONAL WARM-HOLD CUE
   ──────────────────► Low temp + low fan → REHEAT (4) at 180°F
                       (visible mode change on display; pull promptly)
```

## Fan-speed considerations

Fan affects surface texture more than internal cooking rate:

- **High fan** (Air Fry, Grill, Broil, Wings, Steak, Pizza-preheat): aggressive
  convection, fast surface drying, best for crisping. **Risk**: blows loose parchment
  into the top element (causes smoke); dries delicate top coatings.
- **Medium fan** (Bake, Roast, Bacon): balanced convection, more moist, slower surface
  development. Best for proteins where moisture retention matters more than crisp.
- **Low fan** (Reheat, Dehydrate, Griddle, Toast): gentle, no liner-blow risk, slow
  even cook. Best for delicate items or warm-hold.

## Decision matrix — pick a mode by what you want

| If your dish is... | Use mode | Why |
|---|---|---|
| Skin-on protein, **skin-DOWN** | Grill (3) for sear | Bottom-element bias crisps skin |
| Skin-on protein, **skin-UP** | Air Fry (1) for sear | Top-element bias crisps top |
| Top-coated with delicate aromatics (garlic, herbs) | Bake (10) | Medium fan, gentler — won't burn coating |
| Top-coated, needs aggressive crust | Broil (14) for last 60-90s | Top blast caramelizes |
| Reverse-sear thicker protein | Bake (10) → Broil (14) | Gentle warmup then surface blast |
| Whole frozen pizza | Pizza preset (5) | Auto preheats at 450°F |
| Steak >1.5" thick | Steak preset (7) OR Bake→Broil | 450°F preheat or reverse-sear |
| Fries / wings | Air Fry (1) or Fries (15) | Top + high fan = crispy |
| Optional warm-hold cue | Dehydrate (13) at 180°F | Low temp, visible mode change |
| Long even cook (custards, bread) | Bake (10) | Medium fan, top-bias, even |
| Probe-driven protein cook | Roast (12) | Typhur's own default for AF13 probe presets |
| Dehydrating jerky / fruit | Dehydrate (13) | Up to 24h, low temp |
| Cleaning device | Self Clean (9) | 500°F for 1-2 hr; ventilate kitchen |

## Cook patterns by protein

### Salmon (1" fillet, skin-on, skin-DOWN)
```
Phase 1: Grill (3) @ 450°F    [sear; bottom heat crisps skin]
Phase 2 at probe 95°F:
         Bake (10) @ 300°F    [gentle finish to prevent edge overcook]
Phase 3 at probe 120°F:
         STOP                  [pull immediately; rest 3 min]
Final after 3-min rest: 125-130°F (silky medium)
```

### Bone-in skin-on chicken thighs (skin-DOWN)
```
Phase 1: Grill (3) @ 400°F    [sear skin]
Phase 2 at probe 145°F:
         Bake (10) @ 375°F    [even finish; dark meat is forgiving]
Phase 3 at probe 170°F:
         STOP                  [pull immediately; rest 3-5 min]
Final after 3-min rest: 175°F (juicy)
```

### Ribeye / NY strip (1.5"+ reverse sear)
```
Phase 1: Bake (10) @ 250°F    [slow even warmup; no edge overcook]
Phase 2 at probe 110°F:
         Broil (14) @ 450°F   [top-element blast for crust, 60-90s]
Phase 3 at probe 125°F:
         STOP                  [pull immediately; rest 3-5 min]
Final after rest: 130°F (medium-rare)
```

### Pork tenderloin
```
Phase 1: Grill (3) @ 425°F    [sear all sides]
Phase 2 at probe 110°F:
         Bake (10) @ 325°F    [gentle finish]
Phase 3 at probe 140°F:
         STOP                  [pull immediately; rest 3-5 min]
Final after 3-min rest: 145°F (Typhur's chef's-choice pork-medium)
```

### Boneless skinless chicken breast (single-phase)
```
Phase 1: Bake (10) @ 375°F    [start to finish, no swap; even cook is the priority]
Phase 2 at probe 155°F:
         STOP                  [rest 3-5 min, carryover to 162°F]
Final: 162°F (safe + juicy)
```

### White fish (cod, halibut, sea bass) — single phase
```
Phase 1: Bake (10) @ 350°F    [gentle even cook; high fan would dry it]
Phase 2 at probe 125°F:
         STOP                  [pull immediately; rest 2-3 min]
Final after 3-min rest: 130°F (flaky moist)
```

### Frozen pizza
```
Use Pizza preset (5) at 340°F for 14 min. Has built-in 450°F preheat.
You'll be prompted to load the pizza AFTER preheat finishes (2-touch cook).
```

### Bacon
```
Bake (10) @ 335°F for 13 min. Medium fan keeps grease from spattering.
```

### Fries
```
Fries preset (15) @ 330°F for 17 min, single layer.
Shake basket at the 8-min mark for even browning.
```

## Mode-specific gotchas

- **Air Fry**: high fan can lift loose parchment into the top element → smoke. Weight
  parchment down with food or skip it.
- **Pizza preset (5)**: temp capped at 400°F (not 450°F). Has mandatory ~8-min preheat
  at 450°F. Food loaded AFTER preheat. Counts as a 2-touch cook.
- **Steak preset (7)**: same as Pizza — mandatory preheat phase, food loaded after.
  For a one-touch sear at 450°F, use **Grill mode 3** instead.
- **Grill (3)**: counter-intuitive name — it's not "outdoor grill"; it's bottom-element
  searing. Use it for skin-down protein, NOT for grill-marked steaks (Broil is closer
  to that).
- **Self Clean (9)**: 500°F for 1-2 hr produces smoke. Run with vent hood on. Never
  load food.
- **Griddle (11)**: capped at 400°F. Designed for direct-contact pancake/egg cooking.
- **Broil (14)**: official max time is 60 min, but USE FOR BURSTS ONLY (60-90s). Extended
  broil at 450°F will scorch most foods.
- **Dehydrate (13)**: time can extend to 24 hours (86400s). Useful for jerky/dried fruit.
- **Dehydrate (13)** at 180°F: optional low-temp cue for recipes that explicitly opt in.
  It changes the display, but delicate food can keep carrying over and drying. Pull promptly.

## Pizza/Steak preset preheat behavior

Both Pizza (5) and Steak (7) have an explicit `preheat` config in their dictionary
(unique among modes):
- `fanSpeed: 1600` (high)
- `temperature: 450°F`
- `time: 480s` (8 min)
- `heatPriority: "down-first"`

The device runs the preheat phase BEFORE the cook timer starts. Per Typhur's official
recipes, the user is supposed to load the food AFTER preheat completes (the app
notifies). This makes Pizza and Steak **two-touch cooks** — not "load and walk away."

If you want a one-touch high-heat sear: use **Grill mode 3 at 450°F** instead. Same
target temp, no preheat phase, immediate start when user presses Start button.

## Why we don't use multi-stage cooks

The firmware supports native multi-stage cooks (`cookingStageNum=N` + `setParams[]`).
But mid-cook changes to stage count are FORBIDDEN — the firmware returns `cmdError 1`
or `cmdError 513`. If you start with stage_count=2 and try to change anything
structural, you can get the cook stuck in `cookingState=5` with `curRemainingTime=0`
on the display (looks "done" to the user but isn't).

CLIronChef ALWAYS uses single-stage cooks + hot-modify mid-cook (which works cleanly).
The runner reads the recipe's phases and hot-modifies through them, never touching
stage count.

## Programmatic access

```python
from cliron_chef.modes import AF04_MODES, get_mode

# Get info about a mode by ID
mode = get_mode(3)
# Returns: {
#   "id": 3,
#   "name": "Grill",
#   "element_bias": "bottom",
#   "fan": "high",
#   "default_temp_f": 450,
#   "temp_min": 210,
#   "temp_max": 450,
#   "best_for": "skin-down protein, crispy skin",
# }

# Or look up by name
mode = AF04_MODES["Grill"]
```

## Cross-reference

- [data/modes/af04_modes.json](../../data/modes/af04_modes.json) — raw mode dictionary
- [data/modes/af04_probe_presets.json](../../data/modes/af04_probe_presets.json) — Typhur's
  recommended pull-temps per protein (from AF13 probe presets, applicable to AF04 + WT01)
- [RECIPES.md](RECIPES.md) — how to use these modes in a recipe JSON
- [COOK_LIFECYCLE.md](COOK_LIFECYCLE.md) — the timer + state semantics
