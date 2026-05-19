# Changelog

All notable changes to CLIronChef are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-05-19

Initial public release.

### Added
- Python CLI + library for supervised, probe-driven cooks on the Typhur Dome 2 air fryer and Sync ONE wireless probe.
- 7 built-in recipes (salmon basic + gourmet, steak reverse-sear, chicken thighs + breast, pork tenderloin, white fish).
- Declarative JSON recipe schema with probe-driven phase transitions.
- Live MQTT telemetry subscription and mid-cook hot-modify (mode/temp/time).
- Probe-driven STOP at target internal temperature.
- AGENTS.md operating contract (10 non-negotiable rules) for Claude Code, Codex CLI, Gemini CLI, and other agent harnesses.
- Public-release leak scan and pre-commit hygiene tooling.

### Lessons codified from the 2026-05-17 three-agent cook-off
- Single-stage cook setup (cookingStageNum=1) is the only safe pattern; cross-stage hot-modify is firmware-locked.
- 2400-second timer buffer is reasserted on every hot-modify.
- Phase transitions are probe-driven, not time-driven.
- Mode selection uses element-bias metadata, not mode names.

### Safety
- Physical Start button on the Dome 2 is intentionally not bypassed (UL/IEC interlock). Human always presses Start; everything after is automated.

[0.1.0]: https://github.com/sidkandan/CLIronChef/releases/tag/v0.1.0
