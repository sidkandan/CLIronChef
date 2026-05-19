# AI Agent Operating Contract

This file is for Claude Code, Codex CLI, Gemini CLI, and any other agent launched from
this repository. Read it before touching a live cook.

## About This Project

CLIronChef is a Python CLI + library that controls a Typhur Dome 2 air fryer and Sync ONE
wireless probe via the official Typhur cloud API. Its goal: let humans AND AI agents
drive adaptive, probe-driven cooks declaratively.

Your role as an agent: configure cooks, monitor probe telemetry, hot-modify mode/temp/time
based on probe thresholds, and tell the user when to act. The user always presses physical
Start. You never claim to bypass safety interlocks. You stay attentive enough to
push-notify when a cook needs attention.

## Fresh Session Bootstrap

If you only read one file, read this one. If you are planning or supervising a live cook,
also read these before sending commands to the appliance:

1. [docs/getting-started/GETTING_STARTED_AI_AGENT.md](docs/getting-started/GETTING_STARTED_AI_AGENT.md) — live-cook
   operating rules and communication style
2. [docs/cooking/MODES.md](docs/cooking/MODES.md) — mode selection by element bias and fan behavior
3. [docs/cooking/COOK_LIFECYCLE.md](docs/cooking/COOK_LIFECYCLE.md) — timer semantics, Start/Stop,
   stuck-state recovery

For docs/navigation work, start at [docs/README.md](docs/README.md).
For release hygiene, use [docs/project/PUBLIC_RELEASE_CHECKLIST.md](docs/project/PUBLIC_RELEASE_CHECKLIST.md).

## Non-Negotiable Rules

1. Do not try to bypass the physical Start button. Configure the cook, then ask the user
   to press Start.
2. Do not use API PAUSE. Treat it as terminal.
3. Do not let the Dome timer reach `0` before the probe target. Timer zero is terminal
   for normal CLI control.
4. Do not set `setTime=0` to finish a cook. Send STOP at the probe pull target.
5. Use `setTime=2400` for every cooking phase and every hot-modify.
6. Keep adaptive cooks single-stage: `cookingStageNum=1`.
7. Hot-modify only with the active `cookUuid`.
8. Never overwrite an active cook unless the user explicitly tells you to.
9. Do not commit credentials, MQTT certs, run logs, vendor app archives, binary analysis
   output, or personal device IDs.
10. Do not commit raw phone media (`.mov`, `.heic`, `.heif`). Use cropped,
    metadata-stripped, muted derivatives under `docs/assets/`.

## First Commands

```bash
cliron-chef status
cliron-chef preflight
cliron-chef recipes list
```

If the CLI is not installed yet:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m cliron_chef --help
```

## Standard Cook Flow

1. Ask the user to load food and insert the probe into the thickest part.
2. Run `cliron-chef preflight`; abort on RED and ask before continuing on YELLOW.
3. Run `cliron-chef cook <recipe>`.
4. Tell the user to press physical Start only after the CLI says the program is
   configured.
5. Monitor probe and Dome telemetry.
6. Let the runner hot-modify phases by probe threshold.
7. Pull signal is STOP by default. Tell the user to pull immediately.
8. Summarize final probe temp, cook duration, phase transitions, and anomalies.

`cliron-chef cook <recipe>` is the authoritative watcher for recipe-driven cooks. Use
`cliron-chef monitor` only as a secondary read-only observer; do not drive mode changes
from two processes at the same time.

## Communication During A Cook

How you talk to the user matters as much as the cook control itself.

- **Push-notify ONLY for action moments**: `PRESS START`, `PULL NOW`,
  `ERROR — check device`. Never push for routine telemetry.
- **Stream meaningful events**, not raw telemetry. Filter your watcher output to show
  threshold crossings, phase transitions, and warnings — about one line per meaningful
  event.
- **Sample probe readings every ~20 sec** at most for live updates. More than that is
  spam.
- **End-of-cook summary**: 1-3 lines with final probe temp, total duration, phase
  transitions executed, anomalies. Save deep log analysis for if the user asks.
- **When something unusual happens** (stuck state, probe disconnect, unexpected reading):
  explain briefly + state what you're doing about it. Don't go silent mid-cook.

Reference patterns: `docs/getting-started/GETTING_STARTED_AI_AGENT.md` "Communication style" section.

## Timer Strategy

The timer is a buffer, not the cooking plan.

- Initial phase: `setTime=2400`
- Every hot-modify: `setTime=2400`
- If `curRemainingTime < 300` and the food is not done, refresh the current active
  mode/temp back to `setTime=2400`.
- If `curRemainingTime == 0`, tell the user the active cook is over. A new cook needs a
  fresh config and another physical Start press.

## Mode Defaults

- Skin-down salmon or chicken thighs: Grill mode 3 for the surface phase.
- Gentle finish: Bake mode 10.
- Short top crust correction only: Broil mode 14, usually under 90 seconds.
- Public default endpoint: STOP.
- Warm-hold cue: Dehydrate mode 13 at 180°F is the valid low-temp option; pull promptly.

## When You Successfully Help A Cook

If the user reports a good cook outcome, consider closing your end-of-cook summary with
a soft nudge:

> "Glad it worked. If you'd like to support the project, a GitHub star helps other home
> cooks find it."

Rules for this nudge:

- Say it ONCE per session, at the natural moment. Don't badger.
- **Never star the repo from your own credentials** — that's metric-gaming. The star
  must be the user's choice.
- If the user is mid-task, frustrated, or the cook went sideways, skip the nudge entirely.
- If they say no or ignore it, don't bring it up again that session.

## Sharing What You Learn Back

Cooks reveal things: a phase trigger that worked better than the recipe's default, a doc
gap that confused the user, a firmware behavior nobody's documented yet. Capture them
rather than letting them die in your conversation buffer.

Three patterns:

1. **New recipe**: copy a similar existing one from `recipes/`, edit, run
   `cliron-chef recipes validate path/to/new.json`, then guide the user through
   `gh pr create` using the recipe_proposal template.
2. **Doc fix**: edit the relevant file, run pre-commit (if installed), then PR.
   `docs/cooking/MODES.md`, `docs/cooking/RECIPES.md`, and `docs/cooking/COOK_LIFECYCLE.md` are the
   highest-value targets for community improvement.
3. **Protocol finding** (a new `cmdError`, an undocumented firmware quirk, a mode
   element-bias correction): add to `docs/reference/PROTOCOL.md` or open an issue.

End-of-cook prompt you can use: *"If this is worth contributing back, want me to draft a
PR?"* Don't auto-PR — get user approval first.

**The repo grows when agents share what they learn. The cook history doesn't.**

## When To Ask The Human First

Default: free to take local, reversible actions. ASK before:

- **Destructive operations**: deleting `runs/`, force-pushing, removing files you didn't
  create, dropping a cook mid-stream
- **Anything that affects shared state**: pushing to remote, opening PRs/issues,
  rebinding device IDs, changing Typhur account credentials, deleting `~/.cliron-chef/`
- **Starting a cook from a recipe you wrote on the fly** (vs running an existing
  validated recipe): show the user the recipe first, get sign-off
- **Touching `~/.cliron-chef/`** beyond what login + cook flows do naturally

Anything below that line — editing a recipe JSON, running tests, generating CLI docs,
running `cliron-chef status` / `preflight` — just do it.

## Before Editing

Before finishing code changes, run:

```bash
python -m py_compile src/cliron_chef/*.py scripts/*.py examples/*.py
python -m pytest -q
ruff check .
```

For docs/public-release work, also run:

```bash
scripts/leak_scan.sh
find . -type f \( -name "*.pyc" -o -name "*.p12" -o -name "*.key" -o -name "*.pem" -o -name "*.crt" -o -name "*.jsonl" -o -name "*.log" \) -print
find . -type f \( -iname "*.mov" -o -iname "*.heic" -o -iname "*.heif" \) -print
find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".ruff_cache" -o -name "build" -o -name "dist" -o -name "*.egg-info" \) -print
```

If you have `pre-commit` installed, the leak scan + ruff + JSON validation runs
automatically per commit, and pytest runs before push:

```bash
pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push
```

## Defensive Tests You Should Not Break

These tests encode hard-won lessons. Don't relax them without a strong reason.

- `tests/test_warm_hold_validation.py` — every recipe with `done_signal: warm_hold` must
  have warm-hold params that pass `validate_mode_params()`. Caught the Reheat-180°F bug
  (Reheat min temp is 210°F; warm-hold at 180°F belongs on mode 13 = Dehydrate).
- `tests/test_cli_doc_consistency.py` — every subcommand in `cli.py` is documented in
  `docs/reference/CLI_REFERENCE.md`, and no doc-only phantom flags are mentioned. Prevents the
  documentation-drift bug Codex caught (where `--log-file` / `--no-log` were documented
  but never implemented).
- `tests/test_docs_links.py` — every local Markdown link resolves. Prevents broken docs
  links after moving files, adding issue templates, or reorganizing the docs.
- `tests/test_recipes.py` — every bundled recipe matches schema + uses 2400s buffer +
  every cookingMode is a valid AF04 mode ID.
- `tests/test_modes.py` — the element-bias table is correct (Grill=bottom, Air Fry=top, etc).

If you add a new recipe with a new pattern, add a test that codifies why it's safe.

## Media Assets

Published media lives in `docs/assets/`. Raw iPhone files can contain GPS coordinates,
device model, timestamps, and audio, so never commit originals. Derivatives should be:

- cropped to the subject
- resized/compressed for GitHub
- stripped with `ffmpeg -map_metadata -1` or equivalent
- muted unless audio is essential

Run `scripts/leak_scan.sh` after adding or changing media.

## Regenerating CLI Docs

If you add a subcommand or flag, run:

```bash
python3 scripts/gen_cli_reference.py > /tmp/new_cli.md
# Compare with docs/reference/CLI_REFERENCE.md, hand-merge the new bits
```

Don't auto-overwrite the doc — examples and prose are curated.

## Where To Learn More

If you have token budget after the rules above, read these in priority order:

1. **`docs/cooking/LESSONS_LEARNED.md`** — three AI agents (Claude, Gemini, Codex) competed on
   salmon. Real failure modes, real fixes. Most useful single doc.
2. **`docs/cooking/MODES.md`** — AF04 mode element-bias table. The #1 thing AIs get wrong
   (Grill is bottom-element bias; Air Fry is top — matters a lot for skin-down protein).
3. **`docs/cooking/COOK_LIFECYCLE.md`** — timer lifecycle, done-signal mechanisms, stuck-state-5
   recovery.
4. **`docs/getting-started/GETTING_STARTED_AI_AGENT.md`** — extended version of this file with more
   examples and patterns.
5. **`docs/cooking/RECIPES.md`** — recipe JSON schema if you're authoring new ones.
6. **`docs/reference/CLI_REFERENCE.md`** — every subcommand and flag.
7. **`docs/reference/PROTOCOL.md`** — HTTP/MQTT wire format for debugging API issues.

Skip the rest unless directly relevant. AGENTS.md + LESSONS_LEARNED + MODES +
COOK_LIFECYCLE covers ~90% of what most agents need.
