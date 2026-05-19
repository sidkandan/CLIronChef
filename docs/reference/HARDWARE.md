# Hardware Reference

Physical specs of the devices CLIronChef controls. Useful background for debugging,
buying decisions, or just curiosity.

## Typhur Dome 2 (model AF04)

### Marketing & branding

- Marketed as: "Typhur Dome 2"
- Internal model code: AF04
- The Typhur app shows model as "AF03" in some UIs (legacy; AF03 was the gen-1 Dome)
- FCC declared as AF03 (same IoT module family)

### Physical specs

- **Basket**: 12" × 12" flat floor, ~2-3" usable vertical clearance
- **Total cooking chamber**: ~13L (12.7 quarts)
- **Heating elements**: dual top + bottom, ~1750W total
- **Fan**: variable speed (high/medium/low per mode)
- **Display**: front-panel LCD with temp + time + mode indicators
- **Hardware buttons**: Power, Up, Down, Start (also doubles as Stop), mode presets

### Capacity (independently verified)

- 6 large bone-in skin-on chicken thighs (single layer)
- 20 large wings or 32 small wings (~2 lb)
- 2-4 salmon fillets, 1" thick
- Full 12" frozen pizza
- 1.5 lb fries
- **Won't fit**: whole non-spatchcocked chicken, thick roasts, tall casseroles

### Hardware presets (front-panel buttons)

8 dedicated buttons: Pizza, Bacon, Steak, Wings, Air Fry, Toast, Grill, Reheat

### Modes available via app/CLI but NOT front-panel

7 additional modes: Fries, Frozen, Bake, Griddle, Roast, Dehydrate, Broil

(Full mode table in [docs/cooking/MODES.md](../cooking/MODES.md))

### Wireless

- Wi-Fi: 2.4 GHz only, 2402-2480 MHz, 21 dBm (NOT 5 GHz)
- Bluetooth: 2412-2472 MHz, 18 dBm
- IoT module: FCC ID `2BEFM-WT1000R`

### Power

- Input: 120V AC / 60 Hz (US) or 220-240V AC / 50 Hz (EU)
- Wattage: ~1750W
- Use a 15A dedicated circuit; don't share with other high-draw appliances
- Wall outlet required; do not use extension cord

### Hardware safety interlocks

- **Auto-shutoff after 20 min idle** (standby/paused)
- **Auto-pause on basket removal** — basket pulled mid-cook → cook pauses
- **Auto-shutdown on overheat** — error codes E1, E2, E3, E11
- **Display "---" if basket not detected** — refuses to start
- **Physical Start button required** — UL/IEC compliance; not bypassable

### Error codes

| Code | Meaning | User action |
|---|---|---|
| E1, E2, E3, E11 | Overheating | Power off, cool 30 min, restart |
| E4, E12, E16 | Motor / sensor / comm failure | Power cycle; contact Typhur if persists |

### Cleaning

- Basket + crisper plate: dishwasher-safe (top rack) or warm soapy water
- Interior: damp cloth (don't soak)
- Top heating element: damp cloth after cool (drip residue causes next-cook smoke)
- Self-clean cycle: cookingMode=9, 500°F, 1-2 hr; produces smoke (ventilate kitchen)

### What it's NOT good for

- Slow cooks beyond 60 min (mode max for most modes)
- Thick roasts that need 90+ min
- Items wider than 12" or taller than ~3"
- Liquid-based cooks (no sealed lid for steaming)

---

## Typhur Sync ONE (model WT01)

### Marketing & branding

- Marketed as: "Typhur Sync ONE" (or "Sync One")
- Note: distinct from "Sync ONE Pro" which is model WT13 (better range, more sensors)
- FCC module ID: 2BEFM-WTP1000 family (probe RF)
- IoT base module: 2BEFM-WT1000R (same as Dome 2)

### Probe specs

- **Sensors**: 5 total
  - 4 internal (along the probe shaft)
  - 1 ambient (in the handle, max 572°F / 300°C)
- **Internal sensor max**: 212°F / 100°C
- **Material**: stainless steel
- **IP rating**: IP67 probe end (dishwasher-safe top rack), IPX2 base
- **Accuracy**: ±0.5°F NIST-calibrated

### Base specs

- **Display**: 2.4" TFT LCD
- **Battery**: 3.7V 3020 mAh
- **Battery life**: ~50 hours per charge
- **Charging**: USB-C (5V 1400 mA min)
- **Wireless**:
  - Bluetooth (probe ↔ base)
  - 2.4 GHz Wi-Fi (base ↔ Typhur cloud)
- **Range**: >230 ft outdoor / >66 ft enclosed

### Sleep behavior

- Auto-sleep after 30 min of probe-removed inactivity (configurable in Typhur app)
- Screen lock after 30 sec inactivity
- Wake by holding "O" button 3 sec

### State machine

| State | Meaning |
|---|---|
| `idle` | Probe is on but no target set |
| `cooking` | Probe target set; measuring toward it |
| `remove_from_heat` | Pre-target reached (Typhur's "almost done" alert) |
| `resting` | Probe in carryover-tracking mode |
| `ready` | Final target reached |

CLIronChef ignores this state machine and uses the raw `curTemperature` directly.

---

## Related Typhur hardware (NOT yet supported by CLIronChef)

### Sync Air Fryer (AF13)

- 8 QT capacity
- 9 modes (vs Dome 2's 16)
- **Integrated probe** — has the probe built into the device (not standalone)
- 4 sensors on integrated probe

CLIronChef supports the binding/auth for AF13 but the recipe runner is hardcoded to
AF04. Adding AF13 support would mostly be:
- Adapting `src/cliron_chef/runner.py` to dispatch on model
- Adapting `src/cliron_chef/modes.py` to include AF13's mode dictionary
- Writing AF13-specific recipes (different default cookingMode IDs)

### Sync ONE Pro (WT13)

- 6 sensors (vs WT01's 5)
- Sub-1G enhanced signal (~3000 ft range)
- WiFi-unlimited (better cloud connectivity)

Likely works with CLIronChef as-is (same MQTT protocol) but not tested. File a bug
report if you have one and try it.

### Sync Quad (WT08)

- 4-probe smoker thermometer
- Different model code; partially supported (oleost/typhurHA verified the read path)
- CLIronChef would need a recipe runner that picks the right probe slot

### Sync Gold Dual (WT04 / WT05)

- 2-probe variant; same protocol family

### Sync Oven (CV03 / CV04)

- Different cooking appliance; out of scope for this project

### Coffee Machine (CM03 / CM04)

- Different appliance; out of scope

### Sous Vide (SV03)

- Different appliance; out of scope

---

## Why "Dome 2" specifically

The Dome 2's **dual heating elements** are the distinguishing feature vs basket-style
air fryers. With both top and bottom heat:
- Skin-down protein crisps from below (no flip needed)
- Top-coated items brown from above
- Reverse-sear in a single device (gentle bottom, broil-blast top)

A standard basket air fryer (one element, fan-driven convection) can't do these
patterns. The Dome 2's mode dictionary maps these dual elements to specific use cases —
see [docs/cooking/MODES.md](../cooking/MODES.md).

## Cross-reference

- [MODES.md](../cooking/MODES.md) — element bias per mode
- [PROBE.md](../cooking/PROBE.md) — probe usage
- [PROTOCOL.md](PROTOCOL.md) — HTTP + MQTT wire format
- [Typhur's official product pages](https://www.typhur.com/) — authoritative for marketing claims
