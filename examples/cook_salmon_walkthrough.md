# Cooking Salmon: Annotated Walkthrough

This is a step-by-step real-cook walkthrough showing what each CLI command does and what
the output looks like. Useful for debugging your first cook or understanding what the
runner is doing under the hood.

## Setup (one time)

```bash
# Clone this repository, then:
cd CLIronChef
pip install -e .
cliron-chef login
# Enter your Typhur email + password + region
```

## Pre-cook (every time)

### 1. Wake the probe

Hold the "O" button on the Sync ONE base for 3 seconds. LEDs activate; WiFi
indicator confirms connection in ~15 sec.

### 2. Verify everything's ready

```
$ cliron-chef status

═══════════════════════════════════════════════════════════
📡 Typhur device state — 2026-05-18 19:14:23
═══════════════════════════════════════════════════════════

🔥 Dome 2 (AF04)   id=<your_dome_device_id>
  Status:        online
  Chamber:       0°F
  Error code:    0 (ok)

🌡️  Sync ONE probe (WT01)   id=<your_probe_device_id>
  Status:        online
  Internal:      64.1°F
  Ambient:       63°F
  Battery:       85%

═══════════════════════════════════════════════════════════
💡 Suggested next action
═══════════════════════════════════════════════════════════
  ✅ Ready to cook. Run preflight, then pick a recipe:
     cliron-chef preflight
     cliron-chef cook salmon_basic
```

If status says "wake the probe" — hold "O" 3 sec, then re-run `status`.

### 3. Run pre-flight check

```
$ cliron-chef preflight
═══════════════════════════════════════════════════════════
🔍 CLIronChef pre-flight check
═══════════════════════════════════════════════════════════

1. Credentials & auth
  ✓ Logged in (region=US)

2. Cloud reachability + device binding
  ✓ Listed 2 bound device(s)
  ✓ Dome 2 AF04 bound: Typhur Dome 2 (id <your_dome_device_id>)
  ✓ Sync ONE WT01 bound: Typhur Sync ONE (id <your_probe_device_id>)

3. Force fresh telemetry
  ✓ Fresh status requested + received

4. Dome 2 state
  ✓ Dome 2 errorCode=0
  ✓ Dome 2 globalStatus=online (idle, ready)
  ✓ Chamber at 0°F (cool)

5. Sync ONE probe state
  ✓ Probe globalStatus=online
  ✓ Probe internal 64.1°F (cold meat, normal pre-cook)
  ✓ Probe battery 85%

6. MQTT cert availability
  ✓ MQTT cert + key cached at ~/.cliron-chef

7. Disk space for telemetry logs
  ✓ runs/ has 124234 MB free

═══════════════════════════════════════════════════════════
🟢 GREEN — safe to cook
```

Exit code 0 = green, 1 = yellow (warnings), 2 = red (do not cook).

## Prep the salmon

1. Pat the salmon bone-dry with paper towels (both sides)
2. Sprinkle salt on both sides (~¼ tsp per fillet)
3. Mix olive oil + garlic powder into a paste (1 tbsp oil + ½ tsp garlic per fillet)
4. Brush the paste on the TOP side only (not skin)
5. Insert the probe HORIZONTALLY from the short edge into the thickest part, depth ~2/3
6. Place skin-DOWN in the Dome 2 basket
7. Push basket fully in (click)
8. Close the lid

## The cook

```
$ cliron-chef cook salmon_basic
🔥 SMART COOK RUNNER — Salmon (basic)
   Pull at probe 120.0°F → stop
   Phase 0 (initial): Grill (mode 3) @ 450°F
   Phase 1 @ probe 95.0°F: Bake (mode 10) @ 300°F

✅ Configuring initial cook on Dome 2...
   cookUuid: a36b503bb3b34d839c9de7ce92dc7a40
   Display now shows: mode 3 · 450°F · 40:00

👉 PRESS THE PHYSICAL START BUTTON ON THE DOME 2
   (firmware UL/IEC gate; not bypassable)

[mqtt] connected rc=0
🟢 Cook started! cookUuid=a36b503bb3b34d839c9de7ce92dc7a40
📡 t+0:18  probe 64.1°F  ambient 63°F
📡 t+1:30  probe 75.8°F  ambient 145°F
📡 t+3:00  probe 89.0°F  ambient 245°F
🔥 Phase transition at probe 95.2°F → Bake (mode 10) @ 300°F
📡 t+3:45  probe 95.2°F  ambient 280°F
📡 t+5:20  probe 110.4°F  ambient 305°F
📡 t+6:12  probe 118.0°F  ambient 287°F
🎯 DONE SIGNAL — sending STOP (cookingAction=4)
✅ Cook complete.
   Final probe: 120.3°F
   Total time:  412s
   Log:         runs/20260518T191523.jsonl
```

## What happened

- **t+0:00**: You pressed Start. Cook physically began.
- **t+0:18 to t+3:00**: Chamber ramped from cold to ~250°F in Grill mode. Bottom
  element heating up; probe slowly warmed from ambient as conduction reached the core.
- **t+3:45**: Probe crossed 95°F. Runner hot-modified the Dome from Grill 450°F → Bake
  300°F. Display visibly changed mode. Chamber started settling toward 300°F.
- **t+5:20**: Probe at 110°F; chamber stabilized at ~300°F.
- **t+6:12**: Probe at 118°F.
- **t+6:48**: Probe crossed 120°F. Runner sent STOP. Display shows "End" / 0:00.

## Pull and rest

1. Open the lid
2. Lift the basket out
3. Tent foil (or flip a bowl over the salmon) for 3 minutes
4. While resting:
   - Pat of cold butter on top (optional)
   - Squeeze fresh lemon
   - Pinch of flake salt
5. Plate

The probe internal will climb another ~5°F during the rest (carryover), landing at
125-130°F. Slice — should be opaque pink with a clean flake, juicy through.

## Reading the telemetry log

Each cook writes a JSONL log to `runs/{timestamp}.jsonl`. Example:

```jsonl
{"ts":"2026-05-18T19:14:23Z","event":"runner_start","recipe_name":"Salmon (basic)","pull_temp_f":120.0,"done_signal":"stop","dome_id":"<your_dome_device_id>","probe_id":"<your_probe_device_id>"}
{"ts":"2026-05-18T19:15:01Z","event":"cook_start","cook_uuid":"a36b503bb3b34d839c9de7ce92dc7a40"}
{"ts":"2026-05-18T19:15:19Z","event":"probe","internal_f":64.1,"ambient_f":63,"elapsed_s":18}
...
{"ts":"2026-05-18T19:18:46Z","event":"phase_transition","probe_f":95.2,"to_phase":1,"to_mode":10,"to_temp_f":300}
...
{"ts":"2026-05-18T19:21:23Z","event":"done_stop","probe_f":120.3}
{"ts":"2026-05-18T19:21:28Z","event":"runner_end"}
```

You can `grep`, `jq`, or otherwise analyze this for cook insights.

## Troubleshooting common deviations

### Salmon underdone
Probe was too shallow OR you opened the lid early. Next time, push the probe in deeper
(~2/3 of thickness, tip at center) and don't peek.

### Salmon overdone
Probe was too deep (touching basket) OR you let it rest too long OR pull temp too high
for your taste. Adjust:
```bash
cliron-chef cook salmon_basic --pull-temp-f 115
```

### Chamber didn't reach 450°F in Phase 1
Cold-start ramp takes 2-4 min. The 95°F probe threshold typically fires before the
chamber fully stabilizes — that's fine, the Bake phase finishes the cook properly.

### Probe disconnected mid-cook
Reseat / wake the probe. The watcher will resume reading. If it stays disconnected for
>2 min, the safety logic eventually sends STOP.

### Got cookingState=5 (timer stuck at 0)
Recovery in [docs/cooking/COOK_LIFECYCLE.md](../docs/cooking/COOK_LIFECYCLE.md). Quick fix:
```bash
cliron-chef modify --mode 10 --temp 300 --time 1800
```

## What to try next

- Bake mode swap at different probe temps (e.g., transition at 90°F instead of 95°F)
- Different pull temp (try 125°F for slightly firmer)
- Different recipe: `cliron-chef cook steak_reverse_sear` for steak
- Custom recipe: copy `salmon_basic.json` to `~/.cliron-chef/recipes/salmon_my_way.json`
  and tweak
