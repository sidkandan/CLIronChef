# Getting Started — For AI Agents

This guide is for a fresh CLI or AI-agent session operating a Typhur Dome 2 + Sync ONE
probe through CLIronChef. It focuses on the rules that matter during a live cook.

## Read this in order

1. This file (≈ 5 min)
2. [MODES.md](../cooking/MODES.md) — the cooking-mode table with element bias
3. [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md) — timer rules, done signals, stuck-state recovery
4. [RECIPES.md](../cooking/RECIPES.md) — recipe JSON schema
5. [LESSONS_LEARNED.md](../cooking/LESSONS_LEARNED.md) — field notes from real cooks; what worked, what didn't

If you're under time pressure, just read this file + MODES.md + COOK_LIFECYCLE.md.

---

## What you have access to

- **`cliron-chef` CLI** — single command, ~10 subcommands. See [CLI_REFERENCE.md](../reference/CLI_REFERENCE.md)
- **`cliron_chef` Python package** — programmatic API for fine-grained control
- **Recipe JSONs** in `recipes/` — declarative phase definitions; the runner consumes them
- **Mode reference** in `docs/cooking/MODES.md` — the element-bias table is the most important page in the repo

## The 5 Rules You Must Not Break

These are firmware-level and live-cook constraints learned from real tests.
Memorize them before designing any cook.

### 1. Pick mode by ELEMENT BIAS, not by name

The AF04 has dual top + bottom heating elements. Modes bias heat differently:

| Mode (ID) | Element bias | Fan | Best for |
|---|---|---|---|
| **Grill (3)** | **BOTTOM** | High | Skin-down protein (salmon, chicken thighs) |
| **Air Fry (1)** | **TOP** | High | Top-crisp items (fries, wings) |
| **Bake (10)** | **TOP** | Medium | Gentle finish, even cook |
| Broil (14) | TOP only | High | 60-90s blast for crust |
| Dehydrate (13) | Both | Low | Advanced 180°F warm-hold cue only when recipe opts in |
| Roast (12) | Both | Medium | Probe-driven protein cooks (Typhur's default for AF13 probes) |

**Skin-down salmon = Grill mode 3, not Air Fry.** Do not default to Air Fry because it is
mode 1; top-element bias is wrong for skin-down salmon. See the full table in
[MODES.md](../cooking/MODES.md).

### 2. Single-stage cook from the start (`cookingStageNum=1`)

The firmware rejects stage-count changes mid-cook (`cmdError 1` or `513`). If you set
`cookingStageNum=2` upfront and later want to hot-modify with a different number, you'll
get stuck in `cookingState=5` with `curRemainingTime=0` (looks "done" to the user but
isn't really). Always start single-stage; do phase transitions via hot-modify, not via
native multi-stage.

### 3. Timer buffer = 2400s (40 min) from minute zero

The Dome 2 timer counts DOWN. When it hits 0, the cook ENDS — irrecoverably without
human Start press. ALWAYS:
- Initial setTime: 2400s minimum
- Reassert setTime=2400 on every hot-modify (hot-modify REPLACES the setTime)
- Monitor `curRemainingTime`; extend proactively if it drops below 300s

### 4. Stop by probe, not by timer

Run a probe watcher that fires at the configured pull temp. The timer is a session
survival buffer, not the endpoint. Default done signal:

- **STOP** (`cookingAction: 4`) → display `End` / `0:00`, heating stops, user pulls now

Advanced opt-in done signal:

- **Mode-swap to Dehydrate 180°F** → display visibly changes, but food can continue
  carrying over. Use only if the recipe explicitly sets `done_signal: "warm_hold"` and
  the user knows to pull promptly.

### 5. Physical Start is unbypassable

Configure the cook from the CLI FIRST, then tell the user to press Start. Software
bypass approaches have been tested; none work reliably. Do not spend live-cook time
attempting one.
The order matters: configuring first binds `startClient=android`, which lets you do
hot-modifies. If the user presses Start with the device's default program (no prior
CLI config), `startClient=device` binds and your hot-modifies will be rejected with
`cmdError 512`.

---

## First commands you should run

```bash
# 1. Pretty state snapshot (use this often)
cliron-chef status

# 2. Safety pre-flight check (exit 0=GREEN, 1=YELLOW, 2=RED)
cliron-chef preflight

# 3. See what recipes are available
cliron-chef recipes list

# 4. Inspect a recipe before running
cliron-chef recipes show salmon_basic

# 5. Validate any new recipe JSON before relying on it
cliron-chef recipes validate path/to/my_recipe.json
```

## How to cook (the standard pattern)

For any cook, the flow is:

```
1. User loads food into Dome 2 with probe inserted into thickest part
2. Agent runs: cliron-chef preflight (verify green; abort if red)
3. Agent runs: cliron-chef cook <recipe_name>
4. CLI configures the Dome 2 cook program; displays "PRESS START" to user
5. User presses physical Start button on device
6. CLI begins probe-driven monitoring via MQTT
7. Phase transitions fire at probe thresholds (hot-modify to new mode/temp)
8. Pull signal fires at target probe temp (normally STOP; warm-hold only if recipe opts in)
9. User sees display change → pulls food
10. Agent confirms STOP / mode-change accepted; cook log written to runs/
```

The agent's job during steps 6-8 is to:
- Stream meaningful telemetry to the user (probe temp climbing, phase transitions, warnings)
- NOT spam (filter Monitor tool output; show milestones, not every probe reading)
- Push-notify ONLY for action moments (PULL NOW, PRESS START, errors)
- Handle errors gracefully (probe disconnect, firmware lockup, etc.)

## Standard cook profiles by protein

Quick-reference table — full per-protein detail in [MODES.md](../cooking/MODES.md):

| Protein | Phase 1 (sear) | Phase 2 trigger | Phase 2 (finish) | Pull probe | Final |
|---|---|---|---|---|---|
| Salmon | Grill 3 @ 450°F | 95°F | Bake 10 @ 300°F | 120°F | 125-130°F |
| Chicken thighs (bone-in) | Grill 3 @ 400°F | 145°F | Bake 10 @ 375°F | 170°F | 175°F |
| Steak (1.5"+ reverse-sear) | Bake 10 @ 250°F | 110°F | Broil 14 @ 450°F (60-90s) | 125°F | 130°F |
| Pork tenderloin | Grill 3 @ 425°F | 110°F | Bake 10 @ 325°F | 140°F | 145°F |
| Chicken breast | Bake 10 @ 375°F (single phase) | — | — | 155°F | 162°F |
| White fish (cod, halibut) | Bake 10 @ 350°F | — | — | 125°F | 130°F |

All profiles assume skin-down placement where appropriate, probe in thickest part,
single-stage start, 2400s timer buffer, and STOP at the probe target.

## Monitoring During A Cook

For normal operation, `cliron-chef cook <recipe>` is the watcher. It configures the
initial cook, waits for the physical Start press, subscribes to probe + dome telemetry,
hot-modifies phases at probe thresholds, refreshes the timer buffer if needed, and sends
the done signal.

```bash
cliron-chef cook salmon_basic
```

For a separate observer terminal, use `monitor`:

```bash
cliron-chef monitor --seconds 900
cliron-chef monitor --probe-only --seconds 900
cliron-chef monitor --dome-only --seconds 900
```

If your CLI agent supports background processes, keep the cook runner as the source of
truth and use `monitor` only as a secondary read-only observer. Do not try to drive mode
changes from two separate processes at the same time.

## Recovery procedures

### Probe disconnects mid-cook
- `cliron-chef status` to confirm probe is offline
- Ask user to wake probe (hold "O" 3 sec) and reseat if needed
- Watcher should detect re-connection automatically

### Dome cooking state appears stuck (cookingState=5, timer=0)
This is the firmware bug from cookingStageNum changes. Recovery (verified):
```bash
# Re-arm with SAME cookUuid, SAME cookingStageNum, EXTENDED setTime
cliron-chef modify --mode <SAME_MODE> --temp <SAME_TEMP> --time 1500
```
Same `cookUuid` is auto-detected from device state. Same `cookingStageNum` means don't
change the stage structure.

### User accidentally opens lid mid-cook
The Dome 2 auto-pauses. Replacing the basket auto-resumes. Tell the user, monitor the
state transition; cook should resume seamlessly.

### Cook timer threatens 0 before probe target
Send a hot-modify with the same params + extended setTime=2400.

## Communication style

Keep the user informed at action moments and useful milestones:

- **Probe milestones**: `📈 Probe 97.6°F (+3.8°F/20s = 11°F/min). ~2 min to pull.`
- **Trigger fires**: `🎯 SWAP fired at probe 95.2°F — Grill → Bake 300°F`
- **Pull signals**: `🚨 PULL NOW — STOP sent at probe 120.1°F; display should show End/0:00`
- **Errors**: `⚠️ Probe disconnect at t+4:30; cook still running but no probe data`

Push-notify (if your agent supports push) ONLY for:
- PRESS START moment
- PULL NOW moment
- Errors requiring user intervention

Don't push-notify routine telemetry.

## When you're done with the cook

Brief end-of-cook summary:
- Final probe temp at pull
- Total cook duration
- Phase transitions executed and at what probe temps
- Any anomalies (timer extensions, probe disconnects, etc.)

Optionally save a JSONL log to `runs/{timestamp}.jsonl` for the user to analyze later.

## What NEVER to do

1. ❌ Use Air Fry mode for skin-down delicate proteins (use Grill)
2. ❌ Use `cookingStageNum > 1` for any cook you might want to hot-modify
3. ❌ Set initial setTime < 2400s for probe-driven cooks
4. ❌ Forget to re-assert setTime=2400 on hot-modifies
5. ❌ Use warm-hold unless the recipe and user explicitly requested it
6. ❌ Pull salmon below probe 120°F unless the user explicitly wants very soft salmon;
   visual doneness matters
7. ❌ Use API PAUSE (`cookingAction: 2`) — terminal in this firmware; can't be resumed
8. ❌ Try to bypass the physical Start button — it does not work reliably
9. ❌ Overwrite another contributor's recipe changes without coordination
10. ❌ Make claims about Typhur firmware behavior without checking against
    [docs/reference/PROTOCOL.md](../reference/PROTOCOL.md) or running a live test

## Final mnemonics

- **Skin-DOWN → bottom heat → Grill (3)** (not Air Fry)
- **One stage to start, one stage to swap** (cookingStageNum=1 forever)
- **2400 always** (timer buffer, every cook, every modify)
- **Probe drives the pull** (timer is a fallback)
- **STOP is default** (warm-hold is an explicit advanced opt-in)

If you remember nothing else, remember those five.

## Cross-reference

- [CLI_REFERENCE.md](../reference/CLI_REFERENCE.md) — every CLI command and flag
- [MODES.md](../cooking/MODES.md) — element-bias table + decision matrix
- [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md) — timer states + done signals + recovery
- [RECIPES.md](../cooking/RECIPES.md) — JSON schema + how to author new recipes
- [ARCHITECTURE.md](../reference/ARCHITECTURE.md) — what's happening under the hood
- [PROTOCOL.md](../reference/PROTOCOL.md) — HTTP + MQTT wire details
- [LESSONS_LEARNED.md](../cooking/LESSONS_LEARNED.md) — field notes from real probe-driven cooks
