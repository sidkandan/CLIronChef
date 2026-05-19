# CLI Reference

Complete reference for every `cliron-chef` subcommand. See also `cliron-chef --help` for
short inline help, and `cliron-chef <subcommand> --help` for per-subcommand flags.

## Subcommand index

| Subcommand | Purpose |
|---|---|
| [`login`](#login) | Authenticate with Typhur cloud |
| [`info`](#info) | List bound devices (raw JSON) |
| [`status`](#status) | Pretty-printed device state |
| [`preflight`](#preflight) | Safety check before any cook |
| [`cook`](#cook) | Run a declarative recipe |
| [`modify`](#modify) | Hot-modify the active cook |
| [`stop`](#stop) | Stop the active cook (send STOP) |
| [`monitor`](#monitor) | Stream live MQTT telemetry |
| [`recipes list`](#recipes-list) | List available recipes |
| [`recipes show`](#recipes-show) | Display a recipe's contents |
| [`recipes validate`](#recipes-validate) | Validate a recipe JSON file |
| [`modes list`](#modes-list) | Show AF04 modes with element bias |

## Global flags

Currently supported at the top level:

- `--version` — print the installed CLIronChef version

Other options are subcommand-specific. Use `cliron-chef <subcommand> --help` before
automating a command.

---

## `login`

Authenticate with Typhur cloud and cache credentials.

```bash
cliron-chef login
# Prompts interactively for email + password + region.
```

Or non-interactive (e.g., for scripts):
```bash
cliron-chef login --email YOUR@EMAIL --password 'YOUR_PASSWORD' --region US --yes
```

Stores at `~/.cliron-chef/credentials` (chmod 600). Token at `~/.cliron-chef/token`.

---

## `info`

List all bound devices on your account as raw JSON.

```bash
cliron-chef info
# Prints the full device list from /app/device/bind/list
```

Useful for finding device IDs if you have multiple Dome 2s or probes.

---

## `status`

Pretty-printed snapshot of Dome 2 + probe state. **Use this constantly** — every time
you're about to make a decision.

```bash
cliron-chef status
```

Output sections:
- 🔥 Dome 2 state (globalStatus, chamber temp, error code, active cook details if any)
- 🌡️ Probe state (online/offline, internal/ambient temp, battery)
- 💡 Suggested next action (context-aware: ready to cook, wake probe, etc.)

Exit code: always 0 (informational only).

---

## `preflight`

Automated safety check before any cook. Verifies 7 things:
1. Credentials & auth
2. Cloud reachability + device binding
3. Force fresh telemetry
4. Dome 2 state (idle, no errors, chamber not still-hot)
5. Probe state (online, sensible readings, battery OK)
6. MQTT cert availability
7. Disk space for telemetry logs

```bash
cliron-chef preflight
```

Exit codes:
- `0` GREEN — safe to cook
- `1` YELLOW — review warnings before proceeding (e.g., low probe battery)
- `2` RED — do not cook (e.g., probe offline, Dome in error state)

---

## `cook`

Run a declarative recipe end-to-end.

```bash
# By recipe name (looks in recipes/ + ~/.cliron-chef/recipes/)
cliron-chef cook salmon_basic

# By file path
cliron-chef cook --recipe-file /path/to/my_recipe.json

# Interactive: pick from menu
cliron-chef cook --interactive

# With overrides
cliron-chef cook salmon_basic --pull-temp-f 125
cliron-chef cook salmon_basic --dome-id <id> --probe-id <id>
cliron-chef cook salmon_basic --max-minutes 30

# Dry run (validate + show what would be sent, don't actually send)
cliron-chef cook salmon_basic --dry-run

```

Flow:
1. Load + validate the recipe
2. Configure the initial cook on the Dome (Phase 0)
3. Prompt user to press physical Start
4. Subscribe to MQTT telemetry
5. Stream events; hot-modify at each phase trigger
6. Send STOP at pull target, unless the recipe explicitly opts into warm-hold
7. Write JSONL telemetry to `runs/{timestamp}.jsonl`

Run `cliron-chef preflight` yourself before `cook`; the current `cook` command does not
automatically run preflight.

---

## `modify`

Hot-modify the active cook (single-stage). Auto-detects active cookUuid from device state.

```bash
# Required: new mode + temp; setTime defaults to 2400 (40-min buffer)
cliron-chef modify --mode 10 --temp 300

# Override the cookUuid if needed
cliron-chef modify --mode 10 --temp 300 --cook-uuid <uuid>

# Custom setTime (rarely needed; default 2400 is correct)
cliron-chef modify --mode 10 --temp 300 --time 1800
```

Requires an active cook (errors out if Dome is idle).

---

## `stop`

Stop the active cook by sending cookingAction=4. Display goes to "End"/0.

```bash
cliron-chef stop
# Confirms before sending. Use -y to skip the prompt.

cliron-chef stop -y
```

Use only when you intend to terminate the active cook. If no cook is active, Typhur may
return a "no active cook" command error.

---

## `monitor`

Stream live MQTT telemetry (probe + dome) to stdout. For debugging or watching cooks in
a separate terminal.

```bash
# Watch both devices
cliron-chef monitor

# Just the probe
cliron-chef monitor --probe-only

# Just the dome
cliron-chef monitor --dome-only

# Limited duration (default: 300 seconds)
cliron-chef monitor --seconds 300
```

Press Ctrl+C to stop.

---

## `recipes list`

List all available recipes (bundled + user).

```bash
cliron-chef recipes list

# Filter by protein
cliron-chef recipes list --protein salmon
```

Output: name | protein | pull_temp_f | description

---

## `recipes show`

Display a recipe's contents (parsed + pretty-printed).

```bash
cliron-chef recipes show salmon_basic
```

---

## `recipes validate`

Validate a recipe JSON file against the schema.

```bash
cliron-chef recipes validate path/to/my_recipe.json
```

Exit code:
- `0` — valid
- `1` — invalid (errors printed to stderr with field paths)

---

## `modes list`

Show all AF04 cooking modes with element bias, fan speed, and ranges.

```bash
cliron-chef modes list

# Filter by element bias
cliron-chef modes list --element bottom
cliron-chef modes list --element top
```

Equivalent to reading the table in [docs/cooking/MODES.md](../cooking/MODES.md) but at the command line.

---

## Exit codes (summary)

- `0` — success
- `1` — generic error (validation failure, network error, etc.)
- `2` — preflight RED (do not cook)
- `3` — cook in progress; cannot run requested operation
- `4` — device error (E1, E11, etc.)
- `130` — interrupted by user (Ctrl+C)

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `TYPHUR_EMAIL` | Login email (skip `login` prompt) | (none) |
| `TYPHUR_PASSWORD` | Login password | (none) |
| `TYPHUR_REGION` | `US` or `EU` | `US` |
| `CLIRON_CHEF_CONFIG_DIR` | Override `~/.cliron-chef/` location | `~/.cliron-chef/` |
| `NO_COLOR` | If set, disables ANSI colors | (unset) |

## Configuration file

There is no `config.toml` parser in v0.1.0. Runtime configuration comes from:

1. CLI flags supported by the specific subcommand
2. Environment variables listed above
3. Cached auth files in `~/.cliron-chef/`
4. Hardcoded defaults

## Cross-reference

- [GETTING_STARTED_HUMAN.md](../getting-started/GETTING_STARTED_HUMAN.md) — first cook walkthrough
- [GETTING_STARTED_AI_AGENT.md](../getting-started/GETTING_STARTED_AI_AGENT.md) — for AI agents
- [RECIPES.md](../cooking/RECIPES.md) — recipe schema
- [TROUBLESHOOTING.md](../project/TROUBLESHOOTING.md) — when commands fail
