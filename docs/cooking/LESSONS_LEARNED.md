# Lessons Learned — Probe-Driven Cook Field Notes

On 2026-05-17, three CLI-driven AI agents competed to cook the best salmon on a single
Typhur Dome 2 + Sync ONE probe. Same hardware, same coating ingredients (lemon juice +
olive oil + garlic powder), same household judging panel. Three rounds.

The agents:
- **Gemini CLI**
- **Codex CLI**
- **Claude Code**

The results:
- 🥇 Gemini — best texture, best look, decisive win
- 🥈 Codex — well-executed, slightly over-cooked, missing the visual win
- 🥉 Claude — protocol mistakes mid-cook + pale surface; placed last

This doc captures what went right, what went wrong, and the lessons codified in this
codebase as a result.

---

## The dish

1" thick salmon fillet, skin-on, coated lightly with:
- 1 tbsp lemon juice
- 1 tbsp olive oil
- ½ tsp garlic powder
- (no other prep)

Probe inserted horizontally, skin-down placement, no parchment.

## The three approaches

### Gemini's winning plan

```
Mode: Grill (3) @ 450°F, timer 900s
Phase trigger at probe 95°F → Bake (10) @ 300°F
Pull at probe 120°F → STOP
Rest 3-5 min → final 125-130°F
```

Key wins:
- **Grill mode for the sear** — bottom-element bias hit the skin-down salmon's skin
  perfectly. The top of the salmon (where the garlic-oil glaze sat) got only indirect
  convection — no scorch.
- **Probe-driven phase change at 95°F** — early enough to prevent the dry outer band that
  comes from extended high-heat exposure.
- **Pull at 120°F** (final 125-130°F) — exactly in the chef-target silky-medium window.
  Looked properly cooked, flaked cleanly, juicy buttery interior.
- **Single-stage start** — no firmware locking issues.
- **40-min timer buffer** — never threatened zero.

Also: Gemini built `smart_cook_runner.py` as a declarative JSON recipe engine. That
tooling outlived the cook and is now the foundation for CLIronChef's `runner.py`.

### Codex's 2nd-place plan

```
Mode: Air Fry (1) @ 390°F, timer 2400s
Phase trigger at probe 104°F → Bake (10) @ 300°F
Pull at probe 128°F → STOP
Final after rest: 131-134°F
```

What Codex got right:
- **Single-stage start + long buffer** — no protocol issues
- **Phase change via hot-modify** — same pattern as Gemini, technically clean
- **JSONL telemetry logging** — captured the full cook for post-analysis

What Codex got wrong (Codex's own retrospective):
- **Air Fry instead of Grill** — top-element bias is wrong for skin-down salmon
- **Phase switch too late** (104°F vs Gemini's 95°F) — extended high-heat exposure
  produced a slight dry outer band
- **Pull too high** (128°F vs Gemini's 120°F) — final 131-134°F was solidly cooked but
  past the silky-medium sweet spot

Codex's diagnosis: "I cooked a careful medium salmon. Gemini cooked a more luxurious
salmon."

### Claude's 3rd-place plan (cautionary tale)

```
Multi-stage cook (cookingStageNum=2):
  Stage 1: Air Fry (1) @ 425°F, 90s "blast"
  Stage 2: Air Fry (1) @ 325°F, 720s
Phase transitions at TIMER, not probe
Pull at probe 120°F → STOP
```

What went wrong:
- **Air Fry instead of Grill** (same mode-bias mistake as Codex)
- **Multi-stage with cookingStageNum=2** — when Claude tried to hot-swap to a different
  mode mid-cook with cookingStageNum=1, the firmware rejected the stage-count change
  (cmdError 1/513), leaving the cook in `cookingState=5` with `curRemainingTime=0`
- **"Cold-start blast" did not work** — chamber needed ~4 min to reach 425°F from cold;
  the 90s Stage 1 only got to ~280°F. No real Maillard. Salmon top stayed pale.
- **Time-based phase transitions** instead of probe-driven (Stage 1 ended at 90s
  regardless of chamber state)
- **Short Stage 2 buffer** (720s) — when the cook got stuck in state 5, the safety
  margin was tiny

The salmon came out at the right internal temp (probe pulled at 120°F → final ~125°F),
but it looked undercooked because the surface was pale (no real sear) and the texture
was at the silky end of medium-rare. To some diners, it read as underdone.

### Claude's salvage round

After the verdict, the user put Claude's salmon back in for a salvage cook. By then
Claude had:
- Read the other two agents' approaches
- Heard the user's explicit corrections about timer buffer + stage-count change
- Understood that single-stage + hot-modify is the right pattern

The salvage:
```
Single-stage start: Air Fry (1) @ 425°F, 2400s buffer
At probe 120°F: hot-modify → Bake (10) @ 350°F, 2400s
At probe 138°F: hot-modify → Reheat (4) @ 180°F, 600s (attempted warm-hold cue; later docs
correct this to Dehydrate 13 because AF04 Reheat minimum is 210°F)
```

All three modes used cookingStageNum=1 throughout. Three commands succeeded; the cook
ran 6:14 total; the salmon came out clearly cooked, opaque, flaky. User said it would
have placed 2nd if the salvage counted.

The lesson learned in real-time was: the protocol mistakes are recoverable IF you
understand them. The mode-choice mistake is upstream of the cook — has to be fixed in
the design phase.

---

## What this taught us — codified

These lessons are now baked into CLIronChef. Specifically:

### Lesson 1: Read Typhur's modes guide BEFORE picking a mode

Neither Claude nor Codex initially read https://explore.typhur.com/typhur-dome-cooking-modes,
which documents element bias per mode. Gemini read it and won.

**Codified as**:
- [docs/cooking/MODES.md](MODES.md) — element-bias table at the top
- `src/cliron_chef/modes.py` — programmatic access to element_bias, fan, etc.
- `cliron-chef modes list --element bottom` — CLI command to filter modes by bias
- [docs/getting-started/GETTING_STARTED_AI_AGENT.md](../getting-started/GETTING_STARTED_AI_AGENT.md) — rule #1: "Pick mode by element bias, not by name"

### Lesson 2: Single-stage start + hot-modify within cookingStageNum=1

Claude's multi-stage cook + attempted stage-count change is the canonical anti-pattern.

**Codified as**:
- The runner ALWAYS sends `cookingStageNum=1` (no exception)
- The recipe schema doesn't expose `cookingStageNum` as a field — it's implicit
- `src/cliron_chef/runner.py` does phase transitions via hot-modify, not native staging
- [docs/cooking/COOK_LIFECYCLE.md](COOK_LIFECYCLE.md) — explains why
- [docs/getting-started/GETTING_STARTED_AI_AGENT.md](../getting-started/GETTING_STARTED_AI_AGENT.md) — rule #2: "Single-stage from the start"

### Lesson 3: 2400-second timer buffer; reassert on every hot-modify

Claude's 720s Stage 2 left no margin. The 2400s buffer used elsewhere provided the
necessary safety margin.

**Codified as**:
- Default `time_s` in every recipe phase is 2400
- The runner reasserts `setTime=2400` on recipe hot-modifies
- The runner rejects recipe cooking phases with unsafe short timers
- [docs/cooking/COOK_LIFECYCLE.md](COOK_LIFECYCLE.md) — the "don't accidentally hit 0" rules

### Lesson 4: Mode-swap to Reheat is useful, but not the public default

Claude's salvage round explored this pattern. It remains useful as an explicit
warm-hold cue, but STOP is the public default because it is clearer and less likely to
overcook delicate foods.

**Codified as**:
- The recipe schema has `done_signal: "warm_hold"` as an advanced option
- `warm_hold_mode`, `warm_hold_temp_f`, `warm_hold_time_s` are top-level recipe fields
- [docs/cooking/COOK_LIFECYCLE.md](COOK_LIFECYCLE.md) — explains STOP default vs warm-hold opt-in

### Lesson 5: Probe-driven phase transitions, not time-based

Claude's Stage 1 ending at 90s (regardless of chamber temp) was structurally wrong.

**Codified as**:
- Recipe phases use `trigger_temp_f` (probe temp), not `trigger_time_s`
- The runner only transitions phases when the probe crosses thresholds

### Lesson 6: Stuck-state-5 recovery procedure

Claude hit this state and (with user help) figured out the recovery.

**Codified as**:
- [docs/cooking/COOK_LIFECYCLE.md](COOK_LIFECYCLE.md) — "What if you DO get into stuck-state-5"
  section with the exact recovery payload
- `cliron-chef status` detects this state and warns

### Lesson 7: Pull temp matters for VISUAL doneness, not just internal

Claude pulled at probe 120°F → final ~125°F = correct chef-medium-rare but looked
underdone because the surface had little sear. Gemini also pulled at 120°F but with
better surface color, so it read as cooked.

**Codified as**:
- Recipes that prioritize visual cooked-ness use slightly higher pull temps (steak: 125,
  pork: 140, chicken thigh: 170)
- Recipes for delicate cooks (salmon, white fish) document the visual expectation in
  the `target_doneness` field of the JSON
- [docs/cooking/RECIPES.md](RECIPES.md) — "Decide the target temps" section walks through this
  trade-off

### Lesson 8: Don't trust JSON dictionaries alone for cooking decisions

`data/modes/af04_modes.json` has temp/time ranges but doesn't capture element bias or
fan speed. Both Claude and Codex relied on JSON alone and missed the modes-guide info.

**Codified as**:
- `data/modes/af04_modes.json` now includes `element_bias` and `fan` fields (synthesized
  from Typhur's modes guide)
- `src/cliron_chef/modes.py` exposes these as first-class data
- [docs/cooking/MODES.md](MODES.md) cross-references both the JSON and the modes guide

---

## Quotes from the agents' retrospectives

> **Codex**: "The core technical failure was not automation. The automation did what I
> told it to do. The root cause was target selection."

> **Claude**: "I lost the cook on culinary mode choice, not on protocol. The protocol
> mistakes in round 1 were embarrassing but recoverable — I recovered them in real-time.
> The mode choice (Air Fry instead of Grill) was a strategic decision made before I
> touched the device, and that's the one that cost me."

> **Gemini**: "Our Solution: The Dynamic Two-Phase Cook. We will mimic professional
> restaurant pan-searing by using a two-zone temperature profile. Phase 1 (The Sear):
> We blast the salmon with the Dome 2's bottom-heavy Grill Mode at 450°F just long
> enough to trigger the Maillard reaction… Before the lemon sugars and garlic can
> carbonize, we hot-modify the Dome down to a gentle 300°F Bake Mode."

---

## What this competition demonstrated

1. **AI agents can cook reasonably well from a CLI when the protocol is well-documented.**
   All three agents completed supervised cooks without device safety incidents.

2. **Strategic decisions matter more than tactical execution.** Codex executed cleanly
   but picked the wrong mode → 2nd place. Claude missed both → 3rd. Gemini got
   strategy right and executed cleanly → 1st.

3. **Reading appliance-manufacturer documentation is high-leverage.** The Typhur modes
   guide is one web page. Reading it was the difference between 1st and 3rd.

4. **Hard-won lessons should become tools and docs, not just memories.** That's why
   this project exists — to encode what was learned.

5. **The user's role should be evaluator, not orchestrator.** They provided minimal
   context ("cook this salmon, beat the other agent") and let the agents figure it out.
   The competition format surfaces which agent has done the work to understand the
   appliance, not just follow generic recipe defaults.

## Cross-reference

- [MODES.md](MODES.md) — the element-bias table that decides cooks
- [COOK_LIFECYCLE.md](COOK_LIFECYCLE.md) — timer rules + recovery
- [GETTING_STARTED_AI_AGENT.md](../getting-started/GETTING_STARTED_AI_AGENT.md) — agent-specific playbook
- [recipes/salmon_basic.json](../../recipes/salmon_basic.json) — Gemini's winning recipe, codified
