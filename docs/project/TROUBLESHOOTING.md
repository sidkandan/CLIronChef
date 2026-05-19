# Troubleshooting

Common issues and fixes. If your issue isn't here,
open a bug report with the issue template.

## Installation issues

### `pip install -e .` fails

Try a fresh virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

If you see `error: command 'gcc' failed`, you may need build tools:
- macOS: `xcode-select --install`
- Ubuntu/Debian: `sudo apt install build-essential python3-dev`

### `cliron-chef: command not found`

Your shell's `PATH` doesn't include where `pip` installed scripts. Either:
1. Activate the virtual environment: `source .venv/bin/activate`
2. Use the module form: `python3 -m cliron_chef --help`
3. Find the script and add its directory to `PATH`:
   `pip show -f cliron-chef | grep cliron-chef$`

### `ModuleNotFoundError: No module named 'paho'`

Dependencies didn't install. Try:
```bash
pip install -r requirements.txt
```

---

## Login issues

### "Invalid credentials" on login

- Verify you can log in with the same email + password in the Typhur phone app
- Check region (US vs EU). The CLI tries both if you don't specify, but you can force:
  `cliron-chef login --region EU`
- Try resetting your password via the Typhur app, then login again

### Login succeeds but `cliron-chef status` shows no devices

- Open the Typhur phone app: are your Dome 2 and Sync ONE paired to this account?
- If you have a household sharing setup, you may need to accept a device-share invite

### Token expired errors

The auth token cached at `~/.cliron-chef/token` expires after ~30 days. Re-run
`cliron-chef login` to refresh. Or delete the cache and let it re-login automatically:
```bash
rm ~/.cliron-chef/token
cliron-chef status   # will trigger login flow
```

---

## Probe issues

### Probe shows offline in `cliron-chef status`

The Sync ONE auto-sleeps after 30 min of inactivity. Wake it:
- **Hold the "O" button on the base for 3 seconds**
- Wait 15 sec for it to reconnect to WiFi
- Re-run `cliron-chef status`

### Probe reads 100°F+ before cook even starts

The probe tip is in air, near the surface, or near the basket bottom — not in the meat
core. Open the lid (this auto-pauses any cook), reseat the probe deeper, close the lid.

### Probe disconnects mid-cook

Usually a Wi-Fi reliability issue at the base. Try:
- Move the base closer to the Dome 2 (within 1-2 ft)
- Move your router closer (or use a Wi-Fi extender)
- Check that the probe battery is >20% (low battery weakens transmission)

If the probe reconnects within ~30 sec, the cook continues fine. If it stays disconnected,
CLIronChef's safety logic will eventually send STOP via the `--max-minutes` timeout.

### Probe shows wildly fluctuating readings

The probe tip is at a fat seam or against a bone, which conducts heat irregularly.
Pause the cook, reseat the probe in solid muscle, resume.

### "Hold for 3 sec" doesn't wake the probe

Battery is dead. Plug in USB-C for 10 minutes, then try again. A full charge takes ~2 hr.

### Probe is the wrong device ID

If you have multiple Sync ONE / WT01 probes, the CLI auto-picks the first one. Override:
```bash
cliron-chef cook salmon_basic --probe-id <correct_id>
```
Get the ID via `cliron-chef info`.

---

## Dome 2 issues

### Dome 2 shows offline

- Check it's powered on (front-panel LCD should show time or last-cook state)
- Verify it's on 2.4 GHz Wi-Fi (NOT 5 GHz — Dome 2 doesn't support 5 GHz)
- Open the Typhur app: does the Dome 2 show online there?
- Reboot the Dome 2 (unplug for 30 sec, plug back in)

### Cook command accepted but device doesn't start cooking

This is by design — the physical Start button must be pressed. The CLI configured the
cook program (display shows your mode/temp/time), but the device waits for the human
press.

### `cliron-chef cook` says "PRESS START" but I already pressed it

The CLI might be stale on MQTT state. Wait 10 sec, then check `cliron-chef status`. If
status says `cooking`, the CLI just missed the transition event; telemetry will start
flowing shortly.

### Dome timer hits 0 unexpectedly

If the timer reaches `0` before the probe target, treat the cook session as terminal.
The CLI cannot reliably continue that same cook without configuring a fresh program and
having the user press physical Start again.

Immediate response:

1. Tell the user the cook ended early.
2. Run `cliron-chef status`.
3. If food is under target and the user wants to continue, configure a new cook and ask
   for another physical Start press.
4. If the device reports `cookingState=5`, read [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md)
   before attempting any recovery.

If the cook is still active and the timer is merely low, refresh the buffer:

```bash
cliron-chef modify --mode <current_mode> --temp <current_temp_f> --time 2400
```

### Error code E1, E2, E3, or E11 on display

Overheat. Power off the device, wait 30 min for it to cool, restart. If it persists,
contact Typhur support.

### Error code E4, E12, or E16 on display

Motor / sensor / communication failure. Power cycle the device. If persists, contact
Typhur support.

### Dome 2 is making whining or grinding noises

Stop the cook. Power off. Don't operate until you've contacted Typhur.

### "---" or "--" on the display

The basket isn't fully seated. Push it in until it clicks.

### Chamber chamber temperature reads 0°F constantly

Sensor failure. Open `cliron-chef status`; if Dome chamber stays at 0°F even while
heating, contact Typhur support. (This is rare.)

---

## Cook issues

### Salmon (or other protein) came out underdone

Two possibilities:
1. **Probe was too shallow** — reseat deeper next time
2. **Pull temp was too low for your taste** — bump it:
   ```bash
   cliron-chef cook salmon_basic --pull-temp-f 130
   ```

### Salmon (or other protein) came out overdone

Possibilities:
1. **Probe was too deep (touching basket)** — reseat with tip in the core, not at the bottom
2. **You let it rest too long** — carryover continues for ~5 min; pull at lower probe temp
3. **Pull temp was too high** — drop it:
   ```bash
   cliron-chef cook salmon_basic --pull-temp-f 115
   ```

### Cook started fine but the probe reading is stuck

Probe may have lost connection. Check `cliron-chef status` for probe state. If offline,
the cook can continue (timer-based) but won't be probe-driven. Press the probe's
"O" button to wake it.

### Smoke from the Dome 2 mid-cook

This is typically residual grease on the top heating element from a prior cook. Open the
lid; if the smoke is from fat dripping onto the element, lower the cook temp (`cliron-chef
modify --mode 10 --temp 300`). If smoke persists, abort the cook.

### Garlic powder / spices burning visibly

Drop the temp:
```bash
cliron-chef modify --mode 10 --temp 300
```
Garlic powder burns above ~375°F without oil insulation. The salmon recipes pre-mix
garlic into oil to mitigate, but if you used dry rub, the threshold is lower.

---

## Recipe / runner issues

### "Recipe not found"

The recipe name doesn't match any file. List available recipes:
```bash
cliron-chef recipes list
```

Or pass a full file path:
```bash
cliron-chef cook --recipe-file /path/to/my.json
```

### "Recipe validation failed"

Run validation to see the specific error:
```bash
cliron-chef recipes validate /path/to/my.json
```

Common errors:
- Missing `phases` array
- A phase missing `mode` / `temp_f` / `time_s`
- `pull_temp_f` lower than highest phase trigger
- `mode` value not in the AF04 mode dictionary
- `temp_f` out of range for the chosen mode (e.g., 450°F for Griddle which caps at 400°F)

### Phase transition fires at the wrong probe temp

Your recipe's `trigger_temp_f` is being interpreted correctly; the issue is probably
that your probe is reading higher/lower than the actual core (probe placement). Reseat.

---

## MQTT / network issues

### MQTT connection refused (rc=7)

Your AWS IoT MQTT cert may be expired or invalid. Refresh:
```bash
rm ~/.cliron-chef/client.*
cliron-chef status   # triggers fresh cert fetch
```

### MQTT keeps disconnecting (rc=4)

Duplicate client ID. The Typhur app may be using the same MQTT client ID. CLIronChef
suffixes its client ID with random hex, but if you see this, check that nothing else is
using the same cert.

### `cliron-chef monitor` shows no events

- Device might be sleeping; trigger a status request:
  ```bash
  cliron-chef status   # forces a fresh telemetry report
  ```
- Verify network connectivity to AWS IoT (port 8883):
  ```bash
  nc -zv a2rac2pr1im2vr-ats.iot.us-west-2.amazonaws.com 8883
  ```

---

## Performance issues

### CLI is slow to start

`pip install -e .` should be fast (no compilation). If startup is slow, profile:
```bash
python3 -c "import cliron_chef; print(dir(cliron_chef))"
```

Usually it's network latency to Typhur cloud (login, device list). Try `--no-network`
operations like `cliron-chef recipes list` to verify CLI startup itself is fast.

### `runs/*.jsonl` files growing large

Telemetry logs accumulate. Clean them periodically:
```bash
find runs/ -name "*.jsonl" -mtime +30 -delete   # delete logs older than 30 days
```

---

## Account / cloud issues

### "Account banned" / 401 on API calls

Typhur may detect unusual API patterns. If your account gets flagged:
- Check the Typhur app — can you log in there?
- Wait 24 hours and try again
- Contact Typhur support if needed
- Long-term: use a dedicated account for CLI use (see [SETUP.md](../getting-started/SETUP.md))

### Typhur cloud is down

If `cliron-chef status` consistently fails with network errors, check:
- Whether the official Typhur app can reach your devices
- Typhur's official support channels if the app is also unavailable
- Your home internet
- DNS: `dig api.iot.typhur.com`

The CLI cannot work without Typhur's cloud. The Dome 2 does not expose a supported local
LAN control path.

---

## When all else fails

1. Run `cliron-chef --version` to confirm install
2. Run `cliron-chef status -v` to get verbose output
3. Check `~/.cliron-chef/` exists and has the expected files
4. Try the Typhur phone app — does the issue reproduce there? If yes, it's a Typhur
   issue, not a CLI issue.
5. Open a bug report with the issue template
   with verbose logs

## Cross-reference

- [SETUP.md](../getting-started/SETUP.md) — installation + first-time setup
- [SAFETY.md](../../SAFETY.md) — operational safety
- [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md) — recovery from stuck-state-5
- [FAQ.md](FAQ.md) — frequently asked questions
