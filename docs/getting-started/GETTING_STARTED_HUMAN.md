# Getting Started — For Humans

A walkthrough for your first cook with CLIronChef. Assumes you've done the [SETUP](SETUP.md)
already.

We'll cook **salmon** as the example because (a) it's fast, (b) it shows off the probe-driven
adaptive features, and (c) it's a forgiving entry-point recipe.

---

## The cook we're about to do

Two-phase reverse-sear:
1. **Phase 1: Grill mode @ 450°F** — the Dome 2's bottom-element bias sears the skin from
   below while the top of the salmon (where your glaze sits) gets only indirect heat
2. **Phase 2: Bake mode @ 300°F** — fires when probe internal hits 95°F; gentle finish
   so the core comes up evenly to 120°F without overcooking the outer band

Pull target: **probe = 120°F**. After 3 min rest, carryover brings it to **125-130°F**,
a silky medium finish.

Total time: ~10 min cook + 3 min rest.

---

## What you need on the counter

- 1-2 salmon fillets, **skin-on**, ~1" thick at the thickest point
- A pinch of kosher salt (or any salt)
- 1 tbsp olive oil
- ½ tsp garlic powder, fresh garlic, or your favorite seasoning
- 1 lemon (optional, for finishing)
- Paper towels for patting the salmon dry
- Tongs (or two forks) for pulling the cooked salmon out

You don't need: parchment paper (Dome 2's bottom element wants direct skin contact),
foil (lemon acid + foil = bad chemistry), butter (optional finisher).

---

## Step 1 — Wake the probe

The Sync ONE goes to sleep after 30 min of idle. To wake:
1. Find the **"O" button** on the probe base
2. Hold it for **3 seconds** until you see the LED ring activate
3. Watch for the WiFi/BT indicator to confirm it's connected to your network

Optional sanity check:
```bash
cliron-chef status
```
Probe should show `Status: online`.

---

## Step 2 — Prep the salmon

Quick version:
1. Pat the salmon **bone-dry** with paper towels on both sides — wet salmon won't crisp
2. Sprinkle salt evenly on both sides (about ¼ tsp per fillet)
3. Mix olive oil + garlic powder in a small bowl into a paste
4. **Brush the paste on the top side only.** Don't coat the skin — keeps it dry for crisping.

Fancier version (if you have 15 extra minutes):
- After salting, let the salmon sit uncovered in the fridge 15 min (forms a tacky pellicle
  that crisps better)
- Pat dry again before brushing the oil-garlic paste

---

## Step 3 — Insert the probe

This is the critical step. The probe is your eyes inside the cook.

```
        TOP VIEW of salmon fillet
        ┌────────────────────────┐
        │ ░░░░░░░░░░░░░░░░░░░░░░ │  ← oil-garlic glaze on top
        │           ┃            │
        │           ┃            │  Insert probe HORIZONTALLY from the
   ─────┤  PROBE ━━━┻━━━━━━━     │  short edge into the thickest section.
        │           ▼            │  Parallel to surface, depth ~2/3 of
        │                        │  thickness, tip at the geometric center.
        └────────────────────────┘
```

Rules:
- **Insert from the side, not from the top** (sideways = parallel to surface)
- Push in until ~2/3 of the probe length is inside the meat
- Don't push the tip through the bottom of the fish (it'll read chamber temp, not core)
- The handle/ambient sensor stays OUTSIDE
- For multiple fillets, probe the **thickest** one

If you cooked salmon with a probe before and got readings >100°F before the cook started,
your probe was too shallow. Push it in deeper this time.

---

## Step 4 — Load the basket

1. Place the salmon **skin-DOWN** on the basket (no parchment)
2. Keep the wireless probe handle outside the thickest part of the fish, with the sensor
   section fully inserted
3. Push the basket fully into the Dome 2 until it clicks
4. Close the lid

---

## Step 5 — Run the cook

```bash
cliron-chef cook salmon_basic
```

You'll see something like:
```
🔥 SMART COOK RUNNER — recipes/salmon_basic.json
   Phase 1: Grill (mode 3) @ 450°F (bottom-element sear for skin-down salmon)
   Phase 2 @ probe 95°F: Bake (mode 10) @ 300°F (gentle finish)
   Pull at probe 120°F → final 125-130°F after rest

✅ Cook configured. cookUuid: a1b2c3d4...
   Display now shows: Grill · 450°F · 40:00

👉 PRESS THE PHYSICAL START BUTTON ON THE DOME 2
```

**This is the one human step in the cook.** Walk over to the Dome 2 and press the **Start
button** on the device. The CLI is waiting for that physical press.

(Yes, the CLI *could* technically be told to start the cook over the cloud, but Typhur's
firmware ignores any cloud "start" command and waits for the physical press. This is a
UL/IEC safety thing. See [SAFETY.md](../../SAFETY.md).)

---

## Step 6 — Watch the live progress

After pressing Start, you'll see live telemetry:

```
📡 t+0:18  probe 64.1°F  chamber 138°F  remain 39:42  mode=Grill
📡 t+1:30  probe 76°F    chamber 387°F  remain 38:30
📡 t+3:45  probe 95°F    🔥 SWAP: Grill → Bake 300°F (Phase 2)
📡 t+5:20  probe 110°F   chamber 312°F
📡 t+6:12  probe 118°F   ⚠️  WARN — pull imminent
🎯 t+6:48  probe 120°F   ✅ DONE — STOP sent; pull now
```

What's happening:
- The probe internal temp climbs as the salmon cooks
- When it hits 95°F, the CLI hot-modifies the Dome from Grill 450°F → Bake 300°F
- When it hits 120°F, the CLI sends STOP
- The Dome 2 display changes to `End` / `0:00` — that's the cue that food is ready to pull

---

## Step 7 — Pull and rest

When you see **STOP sent** in the CLI, or the Dome 2 display shows **End / 0:00**:

1. Open the lid
2. Pull the basket out
3. Rest uncovered, or loosely cover with an upside-down bowl, for **3 minutes**
4. During rest:
   - Optional: pat of cold butter on top → melts into the hot crust for restaurant gloss
   - Squeeze fresh lemon over (lemon AFTER cook, not before — preserves bright flavor)
   - Pinch of flake salt if you have it
5. Plate

The probe internal will climb another 5°F during the rest (carryover), landing at the
target 125-130°F = silky medium that flakes cleanly.

---

## Step 8 — Clean up

- Take the probe out of the salmon (let it cool 30 sec first)
- Wash the probe under warm water with mild soap (it's IP67 — dishwasher-safe top rack)
- Set the probe back on its charging base
- Wash the Dome 2 basket and crisper plate (warm soapy water; dishwasher-safe but hand
  wash is faster)
- Wipe the Dome 2 interior with a damp cloth if any splatter
- **Wipe the top heating element** with a damp cloth (drip residue causes next-cook smoke)

---

## What just happened (the geek explanation)

1. The CLI logged into Typhur's cloud (HTTPS REST) and got an auth token
2. It POSTed your cook configuration to `/app/command/send` (cookingMode 3, 450°F, 2400s buffer)
3. The Dome 2 received the config from Typhur's cloud over MQTT and updated its display
4. You pressed Start; the Dome 2 began physically cooking
5. The CLI subscribed to AWS IoT MQTT and started receiving probe + chamber telemetry every ~2 sec
6. When probe internal crossed 95°F, the CLI POSTed a new cooking command with the same
   cookUuid, mode 10, temp 300°F (a "hot-modify"). The Dome accepted and changed mode.
7. At 120°F, the CLI sent STOP so the Dome ended the cook
8. The Dome 2 display changed to `End` / `0:00`, so you knew to pull and rest the salmon

For the full protocol details, see [PROTOCOL.md](../reference/PROTOCOL.md) and
[ARCHITECTURE.md](../reference/ARCHITECTURE.md).

---

## Troubleshooting

### The CLI says "PRESS START" but I already did

Sometimes the MQTT subscription doesn't pick up the cooking state change immediately.
Wait 10 seconds. If nothing happens, run `cliron-chef status` in another terminal — if
the dome status is `cooking`, the CLI just missed the event; let the cook continue and
you'll see telemetry start flowing.

### The probe reading seems too high (e.g., 150°F at cook start)

The probe tip is touching the surface of the salmon, not the core. Pause the cook (open
the lid), reseat the probe deeper, close the lid, and the cook resumes automatically (the
basket-removal triggered the firmware auto-pause; replacing the basket triggers auto-resume).

### Chamber temp seems to drop mid-cook

Normal — elements cycle on/off to maintain the setpoint. As long as probe internal is
climbing, the cook is healthy.

### The Dome 2 timer hits 0 unexpectedly

If the timer hits 0 before the recipe's pull target, the cook session is effectively
over. The CLI cannot reliably continue that same cook without a new configuration and
another physical Start press. Read [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md), run
`cliron-chef status`, and prefer STOP/restart over improvising.

### My salmon came out underdone

Two possibilities:
1. The probe was too shallow — reseat deeper next time
2. The pull temp in `salmon_basic.json` is too low for your taste — try `cliron-chef
   cook salmon_basic --pull-temp-f 130` to overshoot to firmer

### My salmon came out overdone

Possibilities:
1. The probe was too deep (touching basket) — reseat
2. You let it rest too long (carryover continues for several minutes)
3. The pull temp is too high for your taste — try `--pull-temp-f 115`

---

## What to try next

- A different recipe: `cliron-chef recipes list` to see them all
- A custom recipe: edit a JSON file in `recipes/` and re-run
- Watch the live cook telemetry in a separate terminal: `cliron-chef monitor`
- Read [MODES.md](../cooking/MODES.md) to design your own cooks (the element-bias table is the key)
- Read [LESSONS_LEARNED.md](../cooking/LESSONS_LEARNED.md) for field notes from real probe-driven cooks
