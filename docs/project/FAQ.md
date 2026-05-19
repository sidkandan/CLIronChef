# Frequently Asked Questions

## General

### Is this affiliated with Typhur?

**No.** CLIronChef is a community interoperability project, not affiliated with,
endorsed by, or sponsored by Typhur Inc. See [DISCLAIMER.md](../../DISCLAIMER.md).

### Will using this get my Typhur account banned?

It might. Typhur could theoretically detect non-app traffic patterns and flag accounts.
Mitigations:
- Use a **dedicated Typhur account** for CLI use (don't risk your primary)
- Don't hammer the API (don't poll faster than the app would; the CLI is well-behaved by default)
- If your account gets flagged, contact Typhur support

In practice, the CLI uses the Typhur cloud command path expected by the device and avoids
aggressive polling.

### Is this legal?

CLIronChef is an independent interoperability client for user-owned hardware and
user-provided Typhur account credentials. Laws and platform terms vary by region and use
case, so review [DISCLAIMER.md](../../DISCLAIMER.md) before publishing forks or using it
outside personal experimentation.

This is not legal advice.

### Does this work with the Sync Air Fryer (AF13) instead of Dome 2?

Not yet at the CLI level. The protocol is similar but the CLI's recipe runner is
hardcoded to AF04. AF13 support is planned.

### Does this work with the Sync ONE Pro (WT13) instead of Sync ONE (WT01)?

Probably yes — both use the same MQTT protocol. The CLI auto-detects probes by `WT*`
model prefix. File a bug report if not.

### Does this support local LAN control (no cloud)?

No. The Dome 2 doesn't expose a LAN API. All control goes through Typhur's cloud. If
your internet is down, the CLI can't reach the device even if both are on your home LAN.

### Why can't I bypass the physical Start button?

Typhur's firmware requires it for UL/IEC safety compliance (countertop heating appliances
must have a physical actuation per cook). ~50 software bypasses have been tested; none
work. This is by design. See [SAFETY.md](../../SAFETY.md).

---

## Cooking

### Why does my salmon look "raw" when pulled at probe 120°F?

120°F probe → 125°F after 3-min rest carryover. That's chef-tier silky medium-rare. To
people used to USDA 145°F salmon, it can LOOK undercooked at first glance (translucent
center). Try slicing — it'll flake cleanly and be juicy.

If you want a firmer, more opaque texture, bump the pull temp:
```bash
cliron-chef cook salmon_basic --pull-temp-f 130
```

### Why is Grill (mode 3) better than Air Fry (mode 1) for salmon?

Grill biases heat to the BOTTOM element. With salmon placed skin-DOWN, this:
1. Crisps the skin from below (no flip needed)
2. Sears the bottom of the fillet
3. Keeps the delicate lemon-oil-garlic top coating away from direct top heat (which
   would burn the garlic)

Air Fry biases heat to the TOP element. For skin-down salmon, that's the wrong side.

See [MODES.md](../cooking/MODES.md) for the full element-bias table.

### Why use 2400-second timers for a 6-minute cook?

The timer is a safety floor, not the target. The probe drives the actual pull. If the
timer hits 0 unexpectedly (e.g., your hot-modify took longer than expected), the cook
ends and can't be resumed without the user pressing Start again. 2400s (40 min) gives
huge margin. See [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md).

### Can I cook two different proteins at the same time?

Yes, in the same basket, but the probe can only monitor ONE of them. Probe the THICKEST
or most-temp-sensitive item; the others will be at the mercy of time-based cooking.

For best results, batch similar items per cook.

### Why does the recipe say "lemon AFTER cook" instead of in the marinade?

Lemon juice in a pre-cook coating has two problems at high heat:
1. The acid denatures fish protein at the surface (ceviche effect, especially if marinated >30 min)
2. The trace sugars caramelize → bitter scorch above ~350°F

Squeezing fresh lemon at plating preserves the bright acid + flavor without those issues.

### Can I use this for sous-vide-style cooks?

Not directly. The Dome 2 isn't a sous-vide bath. But you can do **reverse-sear** which
is the dry-heat analog: low temp until probe hits ~110°F, then high-heat sear to finish.
See `recipes/steak_reverse_sear.json`.

For actual sous-vide, you'd need a separate immersion circulator, and you could use the
Dome 2 just for the post-sous-vide sear.

---

## Hardware

### Do I need the Sync ONE probe? Can I just use the Dome 2 standalone?

The probe enables probe-driven cooks (pull at exact internal temp). Without it, you'd
fall back to time-based cooks (the runner would still work, but cooks would be
time-only).

The probe is the difference between "good salmon" and "perfect salmon."

### Can I use a different probe (MEATER, Combustion, etc.)?

Not currently. The CLI is tightly integrated with Typhur's MQTT telemetry format. You
could write an adapter that translates other probe APIs into the same format, but it's
non-trivial. PRs welcome.

### What's the difference between Sync ONE (WT01) and Sync ONE Pro (WT13)?

- WT01 (Sync ONE): 5 sensors, BT range >66 ft enclosed
- WT13 (Sync ONE Pro): 6 sensors, Sub-1G enhanced signal, 3000 ft range, WiFi-unlimited

For most home cooks, WT01 is fine. WT13 is for big smokers / outdoor BBQ.

### My Wi-Fi is 5 GHz only. Will this work?

No. The Dome 2's WiFi module only supports 2.4 GHz. You'll need a router that broadcasts
2.4 GHz (most do, but some mesh systems only do 5 GHz by default).

---

## Development

### Can I use this from Python directly instead of the CLI?

Yes. See the [Python API examples](../../examples/python_api_example.py).

```python
from cliron_chef.api import TyphurAPI
from cliron_chef.runner import RecipeRunner

api = TyphurAPI.from_cached_credentials()
runner = RecipeRunner(api, recipe_path="recipes/salmon_basic.json")
runner.run()
```

### Can I add a new recipe?

Yes, please! See [RECIPES.md](../cooking/RECIPES.md) for the schema. Open a PR with your recipe +
a note about the actual test cook (protein source, thickness, taste result).

### Can I add support for a new Typhur device?

Yes. The Sync Air Fryer (AF13), Sync Oven (CV03/CV04), and others are documented but
not fully wired in. Pattern: add device-model constants to `src/cliron_chef/modes.py`,
adapt the runner to dispatch on model, add device-specific recipes.

### How do I run the tests?

```bash
pip install -e ".[dev]"
pytest
```

### How do I contribute?

See [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

## AI Agent specific

### Can Claude / Gemini / Codex use this autonomously?

Yes. There's an [AI agent getting-started guide](../getting-started/GETTING_STARTED_AI_AGENT.md) with the
specific rules and patterns that work.

### What about other LLMs?

Any agent that can:
- Run shell commands (or use the Python API)
- Spawn long-running background processes
- React to stream events from a process

…should work. The CLI is designed to be friendly to AI agents (clear exit codes,
machine-parseable JSON output options, predictable error messages).

### My agent kept setting the timer to 0 early

Read [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md) and [GETTING_STARTED_AI_AGENT.md](../getting-started/GETTING_STARTED_AI_AGENT.md).
Always use `setTime=2400` for cooking phases; reassert on every hot-modify.

### My agent picked Air Fry mode for salmon

Send it to [MODES.md](../cooking/MODES.md). The element-bias table is what determines mode choice;
Air Fry is wrong for skin-down salmon.

---

## Project / Community

### How can I support this project?

- Star the repo on GitHub
- Submit a recipe PR
- Report bugs or unclear docs
- Tell a friend

### Is there a Discord / Slack / forum?

Currently just GitHub Issues + Discussions. If demand grows, we'll spin up a community
space.

### What's the roadmap?

See [CHANGELOG.md](../../CHANGELOG.md) `[Unreleased]` section and the GitHub Issues with
the `enhancement` label.

Near-term wants:
- AF13 Sync Air Fryer support
- Telemetry log analyzer (`cliron-chef analyze runs/some.jsonl`)
- Interactive recipe builder (`cliron-chef recipes create`)
- Home Assistant integration (using the existing oleost/typhurHA as a base)

### How is this different from oleost/typhurHA?

`oleost/typhurHA` is read-only — it subscribes to MQTT telemetry but doesn't send any
commands. Great for monitoring; can't cook.

CLIronChef adds the WRITE path (POST `/app/command/send`) — it can configure cooks,
hot-modify mid-cook, stop, and run probe-driven recipes. Different scope, complementary.

### How is this different from the official Typhur app?

The Typhur app is the polished consumer UI. CLIronChef is for:
- Power users who want declarative recipes
- AI agents that orchestrate cooks
- Developers who want to integrate the Dome 2 into broader pipelines
- People who don't want their phone interrupted by cook notifications

The official app is better for most everyday cooks. CLIronChef is better when you want
adaptive, probe-driven, multi-phase cooks that the app doesn't support directly.

## Cross-reference

- [SETUP.md](../getting-started/SETUP.md) — installation guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — when things break
- [SAFETY.md](../../SAFETY.md) — operational safety
- [DISCLAIMER.md](../../DISCLAIMER.md) — legal context
