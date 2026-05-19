# Sync ONE Probe Guide

The Typhur Sync ONE (model WT01) is a wireless meat thermometer. It's the eyes inside
your cook — when you trust the probe, you trust the cook.

This doc covers: pairing, placement, signal reliability, troubleshooting, and using the
probe with the CLI.

## Hardware specs

- 5 internal sensors (4 along the shaft + 1 ambient in the handle)
- Max probe-end temp: 212°F / 100°C (internal sensors)
- Max ambient temp: 572°F / 300°C (handle sensor)
- Material: stainless steel
- IP rating: IP67 probe end, IPX2 base
- Battery: 3.7V 3020 mAh; ~50 hours per charge
- Charging: USB-C (5V 1400 mA min)
- Display: 2.4" TFT LCD on the base
- Wireless: Bluetooth (probe ↔ base); WiFi (base ↔ Typhur cloud)
- Range: >230 ft outdoor / >66 ft enclosed
- Accuracy: ±0.5°F NIST-calibrated

## Pairing (first time)

1. Charge the probe for >30 min before first use
2. Open the Typhur app → Devices → Add Device → "Typhur Sync"
3. The app walks through:
   - Push the "Pair" button on the base
   - Connect to your 2.4 GHz Wi-Fi (provide SSID + password)
   - Wait for the base to confirm connection (LED stops flashing)
4. Verify in the Typhur app's device list

The probe and Dome 2 are independent devices; they don't need to be paired to each
other. Both just need to be paired to your Typhur account.

## Waking the probe

After **30 min of inactivity**, the Sync ONE auto-sleeps to save battery. To wake:

1. Hold the **"O" button** on the probe base for **3 seconds**
2. The LED ring should activate
3. The WiFi/BT indicator confirms reconnection (~5-15 sec)
4. Verify: `cliron-chef status` should show probe globalStatus=online

If the probe doesn't wake, plug it in (USB-C) — battery may be dead.

## Probe insertion

### General rules

- **Insert horizontally from the side**, not from the top
- **Aim for the geometric center** of the thickest section
- **Depth: ~2/3 of the food's thickness** — tip at the core, but not touching the
  basket bottom (would read chamber temp, not core)
- **Handle/ambient sensor stays OUTSIDE** — it reads chamber air, not meat
- For multiple pieces, probe the **THICKEST one** and design the cook around it

### Salmon / fish fillet

```
        TOP VIEW
        ┌────────────────────────┐
        │ ░░░░░░░░░░░░░░░░░░░░░░ │  ← coating/glaze on top
        │           ┃            │
        │           ┃            │  Insert probe horizontally from the
   ─────┤  PROBE ━━━┻━━━━━━━     │  short edge into the thickest section.
        │           ▼            │  Parallel to surface, depth ~2/3 of
        │                        │  thickness, tip at the center.
        └────────────────────────┘
                                    Cable exits the short edge.
```

### Chicken thigh (bone-in)

Insert into the thickest meat near (but NOT touching) the bone. The bone conducts heat
faster than meat, so probing against it gives a misleading high reading.

### Steak / ribeye

Insert horizontally from the side, midway between top and bottom, depth = 2/3 of the
steak's thickness. Don't probe near fat caps (fat heats faster than muscle).

### Whole chicken / large roast

Probe into the thickest part of the breast or thigh meat. For whole chicken, the
breast is the conservative target (it reaches temp before the thigh, so if breast is
done, thigh is done).

### Probe in air, not in meat

If the probe reads >80°F before you've started cooking, it's too shallow or the tip is
exposed. Push it in further until 2/3 of the probe length is buried in meat.

## Signal reliability

The Dome 2 chamber is a metal cavity with a glass viewing window. BT/WiFi signals don't
travel through metal well. To maximize reliability:

1. **Place the probe BASE within 1-2 ft of the Dome 2** — closer is better
2. **Don't put the base behind walls, cabinets, or appliances** — line of sight to the
   Dome's glass window helps
3. **Make sure the probe is fully connected to the base before cooking** — base display
   should show probe temp before you start the cook
4. **Charge the probe** if battery is <20% — low battery weakens transmission

If the probe disconnects mid-cook:
- The Sync ONE base will retry automatically (usually reconnects within 30 sec)
- CLIronChef's watcher will warn but won't immediately stop the cook (network blips happen)
- If reconnection takes >2 min, the watcher's safety logic kicks in

## Probe states

The Sync ONE has its own state machine (separate from the Dome 2's cooking state):

| State string | Meaning |
|---|---|
| `idle` | Probe is on but not actively measuring a target |
| `cooking` | Probe target set; measuring toward it |
| `remove_from_heat` | Pre-target reached (Typhur's "almost done" alert) |
| `resting` | Probe in carryover-tracking mode |
| `ready` | Final target reached |

When using CLIronChef's recipe runner, we ignore the probe's own state machine and just
read `curTemperature` (internal) + `curAmbientTemperature` (ambient). The runner's own
threshold logic decides when phases transition.

## Battery management

- ~50 hours of continuous cooking per full charge (Typhur spec)
- Charge by setting the probe on its dock OR plug USB-C directly
- Battery percentage is in MQTT telemetry; `cliron-chef status` displays it
- Below 20%, charge before any long cook (smoker brisket, etc.)

## Cleaning

- After each use, **let the probe cool** for ~30 sec before handling
- Wash under warm water with mild soap (probe end is IP67, dishwasher-safe top rack)
- Do NOT submerge the BASE (IPX2 only — splash-resistant, not waterproof)
- Avoid abrasive cleaners on the probe shaft (preserves finish)

## Sleep timer configuration

The default sleep timeout is 30 min of inactivity. You can adjust this in the Typhur app:
- Open the Typhur app → Sync ONE device settings → Auto-Sleep Timer
- Options: 15 min, 30 min, 1 hr, 2 hr, "never" (not recommended; drains battery)

CLIronChef doesn't currently expose sleep timer configuration; use the Typhur app.

## Pairing the probe to the Dome 2 (native probe-mode)

Typhur supports a "native probe-mode" where you pair the Sync ONE directly to a Dome 2:
- Hold both time-adjust buttons (▲ + ▼) on the Dome 2 for ~3 seconds until the WiFi
  icon flashes
- Pair via the Typhur app
- In this mode, the Dome 2 itself auto-stops the cook when the probe hits the user's
  target temp

**CLIronChef does NOT require this pairing.** We use the standalone probe over MQTT and
drive cook control independently. The native pairing is fine to enable, but the CLI's
recipe runner ignores it (handles probe-driven control itself).

## Troubleshooting

### Probe shows online but no temperature readings

The probe is connected to its base, but the base hasn't received recent samples. Try:
- Hold "O" button 3 sec to wake the base
- Push the probe deeper into the meat (a fully-disconnected probe wire vs base will show
  no readings)

### Probe readings are wildly fluctuating

Usually means the probe tip is right at a fat seam or near a bone. Repositions to a
more uniform muscle area.

### Probe disconnects every 30 sec

Wi-Fi signal at the base is weak. Move the base closer to your router OR closer to the
Dome 2 (whichever helps). The base needs to relay probe data to the cloud over Wi-Fi.

### Probe reads 32°F (or 0°C) constantly

Probe sensor failure. Try a different probe or contact Typhur support.

### "Hold for 3 sec" doesn't wake the probe

Battery may be dead. Plug in USB-C for 10 minutes, then try again.

### Probe never appears in `cliron-chef status` device list

It's not bound to your account. Open the Typhur app → Add Device → "Typhur Sync" to
pair it.

## Multiple probes

CLIronChef currently supports ONE probe per cook. If you have multiple Sync ONE probes
(or a Sync Quad / Sync Gold Dual / etc.) and need multi-probe control, open a feature
request issue.

For now, just use the most-relevant single probe (typically the thickest piece of meat).

## Cross-reference

- [MODES.md](MODES.md) — picking the right cooking mode for each protein
- [RECIPES.md](RECIPES.md) — how recipes use probe temp for phase triggers
- [HARDWARE.md](../reference/HARDWARE.md) — full hardware specs
- [TROUBLESHOOTING.md](../project/TROUBLESHOOTING.md) — general issue resolution
