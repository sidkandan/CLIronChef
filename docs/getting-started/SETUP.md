# Setup Guide

End-to-end first-time setup for CLIronChef. Should take ~10 minutes if you already have
a Typhur account; ~20 if you're setting one up.

## Prerequisites

### Hardware

- **Typhur Dome 2** (model `AF04`) — the air fryer
- **Typhur Sync ONE wireless probe** (model `WT01`) — paired to the same account
- Both connected to **2.4 GHz Wi-Fi** (5 GHz is not supported by the Dome 2)
- A standard wall outlet (NOT an extension cord; ~1750W appliance)

### Software

- Python 3.9 or newer (`python3 --version` to check)
- `pip` (usually bundled with Python)
- A computer that stays on during cooks (Mac, Linux, Windows-via-WSL all work)
- ~30 MB disk space

### Typhur account

- Download the [Typhur app](https://www.typhur.com/) on iOS or Android
- Create an account with email + password (no SSO/Google login — we need the password)
- Pair your Dome 2 to the account in the app (one-time setup)
- Pair your Sync ONE probe to the account in the app (one-time)
- Verify both devices show up in the app's device list

> 💡 **Recommendation**: create a **dedicated Typhur account** for CLI use rather than
> using your primary one. Reasons: (1) lets you keep using the phone app concurrently
> without MQTT clientId collisions; (2) reduces blast radius if Typhur ever bans
> "non-app traffic"; (3) makes credential cleanup easier if you stop using this project.
>
> To set up a dedicated account: in the Typhur app, go to Device Settings → Share Device,
> and share your Dome 2 + probe to a second account that you use only for CLI.

## Install CLIronChef

```bash
# Clone this repository, then:
cd CLIronChef
pip install -e .
```

Verify:
```bash
cliron-chef --version
# Should print: cliron-chef 0.1.0
```

If `pip install -e .` fails with permission errors, use a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -e .
```

## Log in

```bash
cliron-chef login
```

The CLI will prompt for:
- Your Typhur account email
- Your Typhur account password (input is hidden)
- Region (US or EU — pick the one for your Typhur account)

What happens:
1. The CLI MD5-hashes your password (per Typhur's protocol requirement)
2. Sends a login request to `api.iot.typhur.com` (or `api.iot.typhur.de` for EU)
3. Receives an auth token
4. Caches the token + email + hashed password locally at `~/.cliron-chef/`
5. Sets permissions on those files to `chmod 600` (owner read/write only)

You won't need to re-login unless your token expires (typically 30 days) or you change
your Typhur password.

## Verify it works

```bash
cliron-chef status
```

Expected output (yours will differ in device names + IDs):
```
═══════════════════════════════════════════════════════════
📡 Typhur device state — 2026-05-18 17:36:59
═══════════════════════════════════════════════════════════

🔥 Dome 2 (AF04)   id=<your_dome_device_id>
  Status:        online
  Chamber:       0°F
  Error code:    0 (ok)

🌡️  Sync ONE probe (WT01)   id=<your_probe_device_id>
  Status:        offline  (hold O button 3 sec to wake)

═══════════════════════════════════════════════════════════
💡 Suggested next action
═══════════════════════════════════════════════════════════
  🔌 Wake the Sync ONE probe (hold 'O' button 3 sec)
```

If you see your Dome 2 + probe listed, you're set up correctly.

## Run a pre-flight check

```bash
cliron-chef preflight
```

This runs 7 safety checks and exits with code 0 (green), 1 (yellow warnings), or 2 (red
issues). Read [docs/reference/CLI_REFERENCE.md](../reference/CLI_REFERENCE.md) for what each check does.

## Try your first cook

Wake the probe (hold the "O" button on its base for 3 seconds). Insert it into your food.
Load food into the Dome 2 basket. Then:

```bash
cliron-chef cook salmon_basic
```

The CLI will:
1. Configure a cook program on the Dome 2 (Grill 450°F, 40-min timer buffer)
2. Tell you to press the physical **Start** button on the device
3. Subscribe to the MQTT telemetry stream
4. Hot-modify the cook phases as the probe crosses configured thresholds
5. Send STOP at your target probe temp
6. Tell you to pull and rest the food

Walk through what's happening in [GETTING_STARTED_HUMAN.md](GETTING_STARTED_HUMAN.md).

## Troubleshooting installation

### `cliron-chef: command not found`
Your shell's `PATH` doesn't include where `pip` installed the script. Try:
```bash
python3 -m cliron_chef --help
```
Or use a virtual environment (instructions above).

### `ModuleNotFoundError: No module named 'paho'`
`pip install -e .` didn't install dependencies. Try:
```bash
pip install -r requirements.txt
```

### Login fails with "invalid credentials"
- Double-check you're using your Typhur app email + password (not Google SSO)
- Verify you can log in with the same credentials in the Typhur app
- Check region (US vs EU)
- Reset password via the Typhur app and try again

### `cliron-chef status` shows probe always offline
The Sync ONE auto-sleeps after 30 min of inactivity. To wake it:
- Hold the "O" button on the probe base for 3 seconds
- The LED ring should activate; the WiFi/BT indicator should reconnect
- Wait ~15 sec for telemetry to start flowing

### Multiple Typhur devices on the same account
The CLI auto-discovers your Dome 2 + Sync ONE from the device list. If you have
multiple Dome 2s or probes, you'll need to specify which to use:
```bash
cliron-chef cook salmon_basic --dome-id <id> --probe-id <id>
```
Run `cliron-chef info` to get device IDs.

### Operating across regions (US ↔ EU)
The Typhur cloud is split by region (`api.iot.typhur.com` for US, `api.iot.typhur.de`
for EU). Your account is tied to one region. If you move regions, you'll need a new
account; CLIronChef can't bridge them.

## Next steps

- 👤 Humans: read [GETTING_STARTED_HUMAN.md](GETTING_STARTED_HUMAN.md) for your first cook walkthrough
- 🤖 AI agents: read [GETTING_STARTED_AI_AGENT.md](GETTING_STARTED_AI_AGENT.md) for the agent-specific guide
- 📖 Power users: read [CLI_REFERENCE.md](../reference/CLI_REFERENCE.md) for every command and flag
- 🍳 Recipe authors: read [RECIPES.md](../cooking/RECIPES.md) for the JSON schema
