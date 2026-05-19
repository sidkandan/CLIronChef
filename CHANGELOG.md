# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `tests/test_warm_hold_validation.py` — asserts every warm-hold recipe uses valid mode+temp combinations (regression test for the Reheat-180°F bug)
- `tests/test_cli_doc_consistency.py` — detects drift between `cli.py` subcommands/flags and `docs/reference/CLI_REFERENCE.md`
- `tests/test_docs_links.py` — validates local Markdown links across docs, templates, and root files
- `.pre-commit-config.yaml` — ruff + JSON/YAML/TOML validation + leak scan + secret detection
- `scripts/gen_cli_reference.py` — helper to regenerate the CLI reference skeleton from live argparse setup
- `scripts/leak_scan.sh` — reusable public-release scan shared by CI and pre-commit
- CI `leak-scan` job — fails the build if personal paths, real device IDs, or credentials are committed
- CI `validate-recipes` job — runs `cliron-chef recipes validate` on every bundled recipe

### Improved
- CI `test` job — added `py_compile` check + `--help` smoke + `fail-fast: false` matrix
- README + getting-started docs — clearer public entry points and less competition-specific front-door language
- Public docs — removed private research-project naming and clone-URL placeholders
- `scripts/leak_scan.sh` — also blocks accidentally committed `.log` cook/debug files
- `docs/assets/` — added cropped, metadata-stripped cook media derivatives for the README
- AGENTS.md — added fresh-session bootstrap, live-cook timer rules, media policy, and defensive-test guidance
- CLAUDE.md / GEMINI.md — added tool-specific bootstrap shims that redirect agents to AGENTS.md
- PUBLIC_RELEASE_CHECKLIST.md — documents pre-commit + the three CI jobs

### Community / Adoption
- AGENTS.md — added "About This Project", "Communication During A Cook", "When You
  Successfully Help A Cook" (star-nudge ethics), "Sharing What You Learn Back"
  (contribution pathway), "When To Ask The Human First" (permission patterns), and
  "Where To Learn More" (priority-ordered reading list) sections
- README.md — added shields.io badges (license, Python, recipe count, CI status)
- README.md — replaced GitHub owner placeholders with the canonical `sidkandan/CLIronChef`
  repo path and made software dependencies explicit
- README.md — added "🤖 Have an AI agent install this for you" section with
  copy-pasteable prompt for Claude/Gemini/Codex/Cursor
- README.md — added a recipe/field-note sharing section that clarifies human stars vs
  agent-authored contribution drafts
- README media — replaced the tight salmon crop with the wider HEIC-derived setup photo
- SECURITY.md / CODE_OF_CONDUCT.md — clarified private-reporting guidance without relying
  on an unpublished maintainer email
- README.md — added "Where to get the hardware" subsection with neutral, no-affiliate
  links to Typhur product pages
- CONTRIBUTING.md — added "Beyond stars — how to support the project" section
  documenting alternative engagement signals (recipe PRs, Discussions, forks, etc.)

## [0.1.0] — 2026-05-18

Initial public release.

### Added
- **CLI** (`cliron-chef`): login, info, status, preflight, cook, modify, stop, monitor,
  recipes (list/show/validate), modes (list)
- **Python API** (`cliron_chef` package): Typhur HTTP client, MQTT subscriber wrapper,
  declarative recipe runner, probe-driven watcher with mode-swap support
- **Built-in recipes**: salmon_basic, salmon_gourmet, steak_reverse_sear, chicken_thighs,
  chicken_breast, pork_tenderloin, fish_white
- **Docs**: setup and first-cook guides, agent guide, architecture, modes, lifecycle,
  recipes, probe placement, CLI reference, troubleshooting, FAQ, safety, hardware,
  protocol, lessons learned, and privacy notes
- **Scripts**: preflight.py, status.py
- **Tests**: recipe schema validation, modes table sanity checks
- **GitHub templates**: bug_report, feature_request, recipe_proposal, PR template
- **CI**: GitHub Actions workflow for lint + tests

### Protocol features supported
- Cloud HTTP API (login, device list, MQTT cert, cooking command, status request)
- AWS IoT MQTT telemetry subscription (probe + dome)
- Single-stage cook configuration
- Hot-modify mid-cook (mode + temperature + time, single-stage)
- Probe-driven phase transitions
- Probe-driven STOP at target
- Mode-swap to warm-hold (Dehydrate 180°F) as optional done-signal cue (advanced opt-in only — see COOK_LIFECYCLE.md)

### Known limitations
- Physical Start button is unbypassable (firmware UL/IEC gate; verified, not a CLIronChef bug)
- API PAUSE is effectively terminal in firmware; the CLI refuses to send it
- Multi-stage native cook (`cookingStageNum>1`) is supported by the firmware but
  intentionally not exposed in the CLI — single-stage + hot-modify is more flexible
  and recoverable
- Only AF04 (Dome 2) is fully supported; AF13 (Sync Air Fryer) bindings exist but the
  CLI's high-level commands target AF04

### Acknowledgments
- [oleost/typhurHA](https://github.com/oleost/typhurHA) — protocol foundation
- The private prototype notes that this public project was extracted from
