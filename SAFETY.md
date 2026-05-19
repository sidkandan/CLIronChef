# Safety

Operating a heat appliance from a CLI doesn't change physics. Same safety rules apply
as when you cook with the Typhur app or the device's front panel.

This doc captures food safety, device safety, electrical safety, and a few CLI-specific
considerations.

---

## Food safety

### Internal temperature targets

CLIronChef's built-in recipes target **chef-preferred** internal temperatures, which
are LOWER than [USDA safe minimum internal temperatures](https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures).

| Protein | CLIronChef target | USDA safe minimum |
|---|---|---|
| Salmon | 125-130°F (medium) | **145°F** |
| Steak (beef) | 130°F (med-rare) | **145°F** |
| Pork tenderloin | 145°F | **145°F (matches)** |
| Chicken thighs | 175°F (juicy) | **165°F (matches)** |
| Chicken breast | 162°F (after rest) | **165°F** ⚠️ |
| White fish | 130°F | **145°F** |

**If you are cooking for vulnerable populations** (children under 5, pregnant
individuals, immunocompromised, elderly), follow the USDA temps, not ours. Either:
- Edit the recipe JSON to bump `pull_temp_f` and re-validate
- Use `cliron-chef cook <recipe> --pull-temp-f 165` to override
- Hold longer at a lower temp (pasteurization is time-AND-temp; 165°F for 1 sec ≈ 145°F
  for several minutes for poultry)

### Cross-contamination

- Wash hands + utensils between raw and cooked food contact
- Use a separate cutting board for raw protein
- The Sync ONE probe is dishwasher-safe (top rack); wash between cooks

### Leftovers

- Refrigerate within 2 hours of cooking (1 hour if ambient is >90°F)
- Reheat to 165°F before serving
- Don't reheat air-fryer-cooked food more than once

### Recipe taste targets are subjective

The recipes ship with the authors' preferences for texture. If you like your salmon
firmer, your steak more done, etc., adjust the recipe — the schema is intentionally
simple ([docs/cooking/RECIPES.md](docs/cooking/RECIPES.md)).

---

## Device safety

### The physical Start button is unbypassable

This is **intentional and required by UL/IEC safety standards** for countertop heating
appliances. The CLI cannot start the cook for you. We've tested ~50 software bypass
approaches; none work; we will not document one even if discovered.

Practical impact: you must press one button per cook. The CLI handles everything before
and after that press.

### Automatic safety interlocks

The Dome 2 firmware enforces these regardless of how the cook was initiated:

- **20-min idle auto-shutoff** — if device sits in standby/paused for 20 min
- **Auto-pause on basket removal** — basket pulled mid-cook → cook pauses
- **Auto-shutdown on overheat** — error codes E1, E2, E3, E11
- **Display "---" if basket not detected** — prevents starting without basket seated

### Errors you might see

| Code | Meaning | Action |
|---|---|---|
| E1, E2, E3, E11 | Overheat | Power off, let cool 30 min, restart |
| E4, E12, E16 | Motor / sensor / comm failure | Power cycle; contact Typhur if persists |

Other codes: see [docs/project/TROUBLESHOOTING.md](docs/project/TROUBLESHOOTING.md).

### Smoke / fire prevention

- **Never run Self Clean (mode 9) when the kitchen is unattended.** It heats to 500°F
  for 1-2 hr and produces enough smoke to trigger sensitive alarms.
- **Wipe the top heating element with a damp cloth** between cooks once cool. Drip
  residue causes next-cook smoke and, eventually, scorching.
- **Don't use parchment paper without weighting it down**. The Dome 2 basket is
  non-magnetic aluminum, so magnetic liners don't work. High-fan modes (Air Fry, Grill,
  Broil) can blow loose parchment into the top element, where it burns and produces
  smoke.
- **Keep 6" clearance** on all sides of the Dome 2 during operation. The exhaust gets hot.

### Never do these

- Operate the Dome 2 on a non-level surface
- Cover the top of the Dome 2 (it has a top vent)
- Use it as an enclosed storage container when off
- Plug it into an extension cord (use a wall outlet directly; ~1750W appliance)
- Cook frozen items >2" thick without a thaw-first plan (uneven cook + probe lag)

---

## Electrical safety

- Dome 2 draws ~1750W. Use a 15A circuit. Don't share with other high-draw appliances.
- Don't operate with damaged power cord, frayed insulation, or visible heater damage
- Don't immerse the Dome 2 base in water
- The basket + crisper plate are dishwasher-safe; the base is NOT
- The Sync ONE probe is IP67 (probe end); the base is IPX2

---

## CLI-specific safety considerations

### Never leave an active cook unsupervised

Even with the probe-driven STOP. Things can go wrong:
- Probe disconnects (BT/WiFi flake)
- Network drops between your machine and Typhur cloud → MQTT subscription pauses
- Power cycle on your machine kills the watcher script
- A bug in the recipe JSON sets too high a target

The CLI watcher has a `--max-minutes` safety timeout that sends STOP if probe target is
never reached, but that's a fallback, not a substitute for human supervision.

### Test new recipes before relying on them

If you create a new recipe, cook it once with you watching the device. Verify:
- Display shows the configured cook
- Each phase transition fires at the expected probe temp
- The pull/done signal works as designed
- The food comes out as expected

### Don't run cooks while you're sleeping

Tempting for long cooks (dehydrate, slow roast). Don't. The 20-min auto-shutoff is a
floor, not a ceiling — fires can start and spread in less time.

### Watch for cookingState=5

This is an undocumented firmware state where the cook display shows `0:00` but the
device might still be in a partial cook state. CLIronChef detects and warns about this.
If you see it, query device state and run the recovery procedure in
[docs/cooking/COOK_LIFECYCLE.md](docs/cooking/COOK_LIFECYCLE.md).

### Don't share credentials between users

If multiple people in your household have Typhur accounts, each one needs their own
`~/.cliron-chef/` directory. Sharing creds invites confusion about who's cooking what.

---

## When to call Typhur support, not us

- Device won't power on
- Display is dead or showing weird characters
- Smoke from the BASE (not the chamber) of the device
- Wi-Fi pairing failures
- Firmware update issues

Typhur support is at [typhur.com/support](https://www.typhur.com/support). For hardware
or firmware issues, reproduce the problem in the official app when possible and report
the device symptoms. This project can help with CLI behavior, not appliance repair.

## When to call US

- CLI errors (open a bug report with the issue template)
- Recipe didn't produce the expected result (open a discussion with details)
- Documentation is unclear or wrong (open a PR or issue)
- You found a way to break the CLI (please report, especially privately if it's a
  security issue — see [SECURITY.md](SECURITY.md))

## Final word

This project exists to make cooking with the Dome 2 more flexible and fun. Not safer.
Treat it the same way you'd treat a manual oven, a sous-vide bath, or any other heat
appliance: **stay engaged, use your senses, trust your judgment over any device or
script.** If something smells wrong, looks wrong, or feels wrong, abort.
