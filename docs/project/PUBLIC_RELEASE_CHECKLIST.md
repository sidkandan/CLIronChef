# Public Release Checklist

Use this before pushing CLIronChef to a public GitHub repository.

## Repository Hygiene

- [ ] Initialize git in this clean public folder, not in any private research workspace.
- [ ] Remove generated files: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`,
      `build/`, `dist/`, `*.egg-info/`.
- [ ] Confirm no credentials or certs: `*.p12`, `*.crt`, `*.key`, `token`,
      `credentials`, `.env`.
- [ ] Confirm no vendor app archives, binary analysis output, or unrelated research
      artifacts.
- [ ] Confirm no personal paths such as `/Users/<name>/`.
- [ ] Confirm no real device IDs, serial numbers, email addresses, auth tokens, or
      telemetry logs.
- [ ] Confirm any media in `docs/assets/` is cropped, resized, metadata-stripped, and
      muted unless audio is essential.
- [ ] Enable GitHub private vulnerability reporting or publish a security contact.

## Validation Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m py_compile src/cliron_chef/*.py scripts/*.py examples/*.py
python -m pytest -q
ruff check .
python -m cliron_chef --help
cliron-chef recipes list
```

Also recommended (one-time setup):

```bash
pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push
pre-commit run --all-files
pre-commit run --hook-stage pre-push --all-files
```

The `pre-commit` hooks run ruff + JSON/YAML/TOML validation + leak scan automatically
on every commit. The pre-push hook runs pytest. See `.pre-commit-config.yaml`.

CI (`.github/workflows/ci.yml`) runs three jobs on every push/PR:
- `test` — ruff + pytest + py_compile + CLI smoke across Python 3.9-3.12
- `validate-recipes` — every bundled recipe passes `cliron-chef recipes validate`
- `leak-scan` — fails if any personal paths, real device IDs, or credentials are committed

Sanity scans:

```bash
scripts/leak_scan.sh
find . -type f \( -name "*.pyc" -o -name "*.p12" -o -name "*.key" -o -name "*.jsonl" -o -name "*.log" \) -print
find . -type f \( -iname "*.mov" -o -iname "*.heic" -o -iname "*.heif" \) -print
find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".ruff_cache" -o -name "build" -o -name "dist" -o -name "*.egg-info" \) -print
```

The scans may still find documentation that says where credentials are stored or which
environment variables exist. They should not find real secret values.

## Docs Review

- [ ] README quick start matches actual CLI flags.
- [ ] `docs/reference/CLI_REFERENCE.md` matches `cliron-chef --help`.
- [ ] `docs/cooking/COOK_LIFECYCLE.md` clearly says timer zero is terminal.
- [ ] `AGENTS.md` gives fresh AI sessions the live-cook safety rules.
- [ ] `LICENSE`, `NOTICE`, `SAFETY.md`, `DISCLAIMER.md`, `SECURITY.md`, and
      `docs/project/PRIVACY.md` are linked from README or the docs index.
- [ ] Examples use placeholders for device IDs.
- [ ] Warm-hold is documented as advanced opt-in, not the public default.

## Legal And Practical Risk

This project is an interoperability client for a third-party connected appliance. Before
publishing, the maintainer should understand:

- Typhur may change the protocol and break the CLI.
- Typhur may object to public protocol details.
- Users must supervise live cooks and follow local food-safety rules.
- The project is not affiliated with Typhur.

If those risks are unacceptable, keep the repository private.
