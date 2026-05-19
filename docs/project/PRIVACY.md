# Privacy

What data CLIronChef handles, where it lives, and what it does (and doesn't do) with it.

## What CLIronChef stores locally

In `~/.cliron-chef/` (created on first `cliron-chef login`):

| File | Contents | Permissions |
|---|---|---|
| `credentials` | Your Typhur email + MD5-hashed password + region | `chmod 600` (owner read/write) |
| `token` | Typhur cloud auth token (expires ~30 days) | `chmod 600` |
| `client.p12` | AWS IoT MQTT client cert (binary P12) | `chmod 600` |
| `client.crt` | Same cert extracted to PEM | `chmod 600` |
| `client.key` | Cert private key extracted to PEM | `chmod 600` |
| `recipes/` (optional) | Your custom recipes | `chmod 700` |

These are all gitignored. NEVER commit `~/.cliron-chef/` to a repo.

## What CLIronChef transmits

Only to Typhur's own cloud servers:

| Destination | What | When |
|---|---|---|
| `api.iot.typhur.com` (or `.de` for EU) | HTTPS POSTs for auth, device list, cook commands | When you run any CLI command that needs cloud state |
| `a2rac2pr1im2vr-ats.iot.us-west-2.amazonaws.com:8883` (US AWS IoT) | TLS MQTT subscription for telemetry | When you run `cook`, `monitor`, or other live-telemetry commands |
| `file.iot.typhur.com` | TLS download of MQTT P12 cert | Once per login (cached) |

That's all. Nothing else.

## What CLIronChef does NOT do

- **No analytics.** The CLI does not phone home with usage data.
- **No crash reporting.** Errors go to your stderr only.
- **No telemetry beyond Typhur's own protocol.** We don't send data to project authors.
- **No code execution from remote sources.** Recipes are parsed as data only; no `eval()`.
- **No background daemons.** The CLI runs only when you invoke it. The probe watcher
  exits when the cook ends.
- **No persistent network listeners.** Outbound connections only; we don't bind to any
  ports.

## Telemetry logs in `runs/`

By default, `cliron-chef cook` writes a JSONL log of the cook to `runs/{timestamp}.jsonl`:

```jsonl
{"ts": "2026-05-17T17:30:00Z", "event": "cook_start", "cookUuid": "...", "recipe": "salmon_basic"}
{"ts": "2026-05-17T17:30:18Z", "event": "probe", "internal_f": 64.1, "ambient_f": 63}
{"ts": "2026-05-17T17:33:45Z", "event": "phase_transition", "from_mode": 3, "to_mode": 10, "probe_f": 95.2}
{"ts": "2026-05-17T17:36:48Z", "event": "cook_done", "final_probe_f": 120.1, "duration_s": 408}
```

These logs are local-only. They include:
- Timestamps
- Cook parameters (mode, temp, time, probe thresholds)
- Probe readings (internal + ambient temp)
- Phase transitions and STOP events
- Errors / warnings

They do NOT include:
- Your email or password
- Your auth token
- Your device serial numbers (only the deviceId, which is a numeric identifier)

Logs are gitignored by default. v0.1.0 does not expose a CLI flag to disable or relocate
the cook log; use a custom `RecipeRunner(log_dir=...)` from Python if you need that.

## What Typhur sees

Same as if you used the Typhur app:
- Your account login attempts
- Your device pairings
- Your cook commands (mode, temp, time, cook UUID, timestamps)
- Your device telemetry (chamber temp, probe temp, cooking state)
- Your phone/CLI's IP address (for the API calls)
- Approximate location (from IP geolocation)

Typhur's privacy policy governs what they do with this data. CLIronChef does not change
their data collection — we just speak the same protocol as the app.

If you don't want Typhur to see your cook activity, you can't use the Dome 2 in any
cloud-connected way (including via the app). The device has no offline mode.

## Multi-account considerations

If you set up a **dedicated Typhur account** for CLI use (recommended):
- That account has its own login + token + MQTT cert
- It's separate from your primary account
- Stopping CLIronChef use = deleting that account = no remaining footprint with Typhur

To switch accounts:
```bash
rm -rf ~/.cliron-chef/credentials ~/.cliron-chef/token ~/.cliron-chef/client.*
cliron-chef login   # log in with the other account
```

## Cleaning up

If you stop using CLIronChef:

```bash
# Remove all locally cached credentials and certs
rm -rf ~/.cliron-chef/

# Optionally remove telemetry logs
rm -rf path/to/CLIronChef/runs/

# Uninstall the package
pip uninstall cliron-chef
```

For full removal, also:
- Delete or unbind your Typhur account (via the Typhur app: Account → Delete Account)
- Note that Typhur retains some data per their privacy policy even after account deletion

## Reporting privacy issues

If you find a privacy issue (e.g., we're transmitting data somewhere we shouldn't be),
follow [SECURITY.md](../../SECURITY.md) for private reporting.

## Cross-reference

- [SECURITY.md](../../SECURITY.md) — security reporting + threat model
- [DISCLAIMER.md](../../DISCLAIMER.md) — legal context and affiliation notes
- [PROTOCOL.md](../reference/PROTOCOL.md) — exact API calls made
