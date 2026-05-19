# Contributing to CLIronChef

Thanks for your interest! This project welcomes contributions from cooks, developers, and
AI agents alike. Here's how to participate.

## Quick links

- 🐛 Bug reports: use the [bug report issue template](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 Feature requests: use the [feature request issue template](.github/ISSUE_TEMPLATE/feature_request.md)
- 🍳 Recipe proposals: use the [recipe proposal issue template](.github/ISSUE_TEMPLATE/recipe_proposal.md)
- 📚 Documentation improvements: just open a PR

## Beyond stars — how to support the project

Stars from humans are welcome; bots and AI agents should not star the repo from their
own credentials. The more meaningful signals for a niche cooking-automation tool:

- **Recipe PRs** — direct evidence people are cooking with this. Highest-value
  contribution.
- **Discussions** — share your cook outcomes, ask questions, swap techniques.
- **Bug reports with reproduction** — even unfixable issues teach the community.
- **Forks** — using/extending privately (visible in GitHub Insights).
- **External writeups** — blog posts, social posts, talks about a cook you did. Drop
  a link in Discussions so we can see.
- **Watching the repo** — subscribe to releases if you actually use it.

If you've cooked with CLIronChef, share what worked (and what didn't). The repo grows
when users share recipes back.

## What we love receiving

### 🍽️ New recipes

Recipes are JSON files in [recipes/](recipes/). Each is a declarative phase definition that
the `cliron-chef cook` runner can execute. Adding a new recipe is the lowest-effort,
highest-value contribution.

Steps:
1. Find a protein or preparation not yet covered (`salmon_basic.json` exists, but
   `salmon_teriyaki.json` doesn't)
2. Copy a similar existing recipe
3. Adjust phases per the [MODES doc element-bias guidance](docs/cooking/MODES.md)
4. Validate: `cliron-chef recipes validate recipes/your_recipe.json`
5. Cook it at home, verify result, note actual carryover (so we can refine the recipe)
6. Open a PR with the recipe + a brief note about your test cook (protein source,
   thickness, taste result)

### 🔧 Code improvements

We especially want:
- Better error messages when things go wrong mid-cook
- Support for additional Typhur devices (AF13 Sync Air Fryer, AF05/AF14 successors)
- Telemetry logging improvements (richer JSONL schema, cook analysis tools)
- A simpler "interactive recipe builder" CLI subcommand

### 📖 Documentation

If you read the docs and find something confusing, missing, or wrong, please open a PR.
We try to write for first-time readers; you are exactly the audience whose feedback we need.

### 🚫 What we won't accept

- Bypasses for the physical Start button (it's a firmware safety gate; we won't touch it
  even if you find a way)
- API PAUSE usage (it's effectively terminal in this firmware; don't promote it)
- Recipes that target unsafe internal temps for vulnerable populations without clear
  warnings
- Code that exfiltrates user data, calls home, or adds analytics
- Republished Typhur trademark assets (logos, photos, etc.)

## Dev setup

```bash
# Clone this repository, then:
cd CLIronChef
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Try the CLI
cliron-chef --help
```

## PR checklist

- [ ] Code passes `ruff check .`
- [ ] Tests pass: `pytest`
- [ ] New code has docstrings + type hints where reasonable
- [ ] If adding a new recipe, it's been actually cooked and tasted
- [ ] If changing behavior, README.md / docs/ updated
- [ ] CHANGELOG.md updated (under `[Unreleased]`)
- [ ] No `~/.cliron-chef/`, `*.p12`, `*.key`, `runs/`, or other gitignored artifacts staged

## Coding style

- **Python**: PEP 8 via ruff. 100-char lines.
- **Docstrings**: short summary on first line; describe purpose, not mechanics.
- **Type hints**: required on public functions in `src/cliron_chef/`.
- **Comments**: only when the *why* is non-obvious. Don't comment the *what* — well-named
  identifiers do that.

## Commit messages

We loosely follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(recipes): add chicken_thighs_with_herbs.json
fix(watcher): handle probe-disconnect mid-cook gracefully
docs(modes): clarify Broil mode element bias
refactor(api): extract MQTT cert fetching to its own module
```

## How to propose a major change

Open an issue with `[RFC]` in the title before writing the code. We'll discuss design,
trade-offs, and whether to land it. This avoids wasted work.

## AI-agent contributions

This project is friendly to LLM-generated PRs **if**:
- The PR follows the checklist above
- A human has tested the code
- The PR description states it was AI-assisted (we just like knowing)

AI-assisted contributions are welcome when a human reviews the diff, validates the
commands, and tests any live-cook behavior before submitting.

## Code of conduct

Be respectful and precise. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Reporting security issues

Please don't open public GitHub issues for security problems. See [SECURITY.md](SECURITY.md)
for the private reporting process.

## Questions

Open a GitHub Discussion for general questions. Issues are for bugs and feature requests.
