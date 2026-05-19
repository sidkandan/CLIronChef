# Architecture

How CLIronChef talks to your Dome 2 and probe. Skim this if you're a power user or want
to understand what's happening when the CLI runs.

## The big picture

```
   ┌──────────────────────┐                                ┌──────────────────────┐
   │   YOUR COMPUTER      │                                │   YOUR HOME WiFi     │
   │                      │                                │                      │
   │   cliron-chef CLI    │                                │   Typhur Dome 2      │
   │      │               │                                │   (AF04)             │
   │      │  HTTPS POST   │                                │      ▲               │
   │      │  to api.iot.  │                                │      │ MQTT (TLS)    │
   │      │  typhur.com   │   ┌──────────────────────┐    │      │               │
   │      ├──────────────►│   │  TYPHUR CLOUD        │    │      │               │
   │      │               │   │                      │    │      │               │
   │      │  cmdType:     │   │  api.iot.typhur.com  │    │      │               │
   │      │  cooking:     │   │  ────────────────►   │ ───┼─────►│               │
   │      │  action       │   │                      │    │      │               │
   │      │               │   │  AWS IoT MQTT broker │    │      │               │
   │      │  ◄──────────  │◄──┤  ────────────────    │ ◄──┼──────┤               │
   │      │  MQTT TLS     │   │  (telemetry relay)   │    │      │               │
   │      │  cert auth    │   │                      │    │      │               │
   │      ▼               │   └──────────────────────┘    │      ▼               │
   │  AWS IoT MQTT        │                                │   Typhur Sync ONE    │
   │  subscriber          │                                │   probe (WT01)       │
   │  device/AF04/.../pub │                                │      ▲               │
   │  device/WT01/.../pub │                                │      │ BT (probe to  │
   │                      │                                │      │  base; base   │
   │                      │                                │      │  has its own  │
   │                      │                                │      │  WiFi to MQTT)│
   └──────────────────────┘                                └──────────────────────┘
```

Three things to notice:

1. **Two protocols, two directions.** The CLI sends commands via HTTPS REST (`POST
   /app/command/send`). The CLI receives telemetry via AWS IoT MQTT subscribe. These
   are separate paths.

2. **The Typhur cloud is a command relay.** When you POST a cook command, the cloud
   forwards it to the device on MQTT. The cloud doesn't add hidden state, doesn't
   validate beyond schema, doesn't enforce safety beyond what the device itself does.
   We verified this experimentally — see [PROTOCOL.md](PROTOCOL.md) for the protocol
   details.

3. **Devices talk to the cloud, not directly to your computer.** Both the Dome 2 and the
   Sync ONE probe have their own WiFi modules that connect to your home network, then
   talk to AWS IoT. Your computer subscribes to the same MQTT topics, with its own
   TLS client cert.

## Components

### `cliron_chef.api` — HTTPS REST client

Wraps `requests` to talk to `api.iot.typhur.com`. Handles:
- Login (MD5-hashed password → token)
- Device list
- MQTT cert provisioning (`/app/mqtt/cert/apply` returns a P12 file)
- Cooking commands (`/app/command/send`)
- Status requests (force a fresh device telemetry report)
- Request signing (MD5 over sorted headers + body, per Typhur's auth protocol)

### `cliron_chef.mqtt_client` — AWS IoT MQTT subscriber

Wraps `paho-mqtt` to subscribe to two topics:
- `device/AF04/<dome_id>/pub` — Dome 2 telemetry (chamber temp, cooking state, cookUuid)
- `device/WT01/<probe_id>/pub` — probe telemetry (internal temp, ambient, battery)

Uses TLS client-cert auth with the cert from the API client. Generates a unique client
ID per session to avoid colliding with the phone app's MQTT connection (AWS IoT
disconnects duplicate client IDs).

### `cliron_chef.runner` — Declarative recipe runner

Reads a JSON recipe (see [RECIPES.md](../cooking/RECIPES.md)) and executes its phases:
1. Configure the initial cook (Phase 0)
2. Tell the user to press Start
3. Subscribe to MQTT
4. As probe temp crosses each phase's `trigger_temp_f`, hot-modify the Dome to the
   phase's `mode` + `temp_f` + `time_s`
5. At `pull_temp_f`, send STOP by default, or hot-modify to warm-hold only when the
   recipe explicitly opts into it

### `cliron_chef.watcher` — Lower-level probe watcher

A library function for one-off probe-driven cook control. Used by the runner; can also
be used directly from Python for custom flows.

### `cliron_chef.modes` — Mode constants + element-bias table

The single source of truth for AF04 mode IDs, default temps, ranges, element bias, and
fan speeds. Programmatically queryable.

### `cliron_chef.cli` — argparse entry point

Defines all the `cliron-chef <subcommand>` flags and dispatches to the right module.

## Data flow during a cook

```
TIME    AGENT ACTION                        DEVICE STATE                  USER ACTION
────    ────────────                        ─────────────                  ───────────
t=-10s  cliron-chef cook salmon_basic       online, no active cook
        │
        ├─ POST /app/command/send           cookingMode=3, temp=4500,
        │  with Grill 450°F, setTime=2400   setTime=2400, awaiting Start
        │  (returns cookUuid)
        │
        └─ "PRESS START NOW" prompt
t=0     ▲                                                                  Presses Start
        │                                   cookingState=3 (cooking)
        │                                   timer counting down from 2400
        ▼
        ├─ MQTT subscribe (TLS)
        │  capture cookUuid from telemetry
        │  begin streaming events
t+15s   ▼ first event: probe 65°F, chamber 138°F
t+1:30  ▼ probe 75°F, chamber 380°F
t+3:45  ▼ probe 95°F → THRESHOLD HIT
        │
        ├─ POST /app/command/send            chamber retargets 300°F
        │  with same cookUuid, mode=10,      mode visibly changes on display
        │  temp=3000, setTime=2400
        │  (hot-modify)
        ▼ telemetry confirms mode=10 active
t+6:48  ▼ probe 120°F → PULL THRESHOLD HIT
        │
        ├─ POST /app/command/send            cook ends
        │  with cookingAction=4 STOP         display "End" / "0:00"
        ▼
        ├─ "PULL NOW — STOP sent"
t+7:00  ▲                                                                   Sees mode change
                                                                            Pulls salmon
                                                                            Tents foil, 3-min rest
t+10:00 ▲                                                                   Eats
```

## Why this architecture?

### Why HTTPS for write, MQTT for read?

That's how Typhur's cloud control path works. We tested heavily and confirmed:
- MQTT publish from our cert is rejected (cert grants subscribe-only)
- The cloud accepts cooking commands ONLY via REST
- The cloud forwards them to the device on MQTT internally

### Why subscribe to both AF04 AND WT01 topics?

The Dome 2 and probe are separate devices on the same Typhur account. They report
independently. The Dome topic gives us chamber temp, cooking state, and the active
cookUuid (needed for hot-modify). The probe topic gives us internal + ambient temps
(needed for phase transitions).

### Why hot-modify instead of native multi-stage?

The firmware supports native multi-stage cooks (`cookingStageNum=N`), but mid-cook
changes to stage count are forbidden (`cmdError 1` or `513`). If you start single-stage
and hot-modify within it, the firmware is happy and you have full control. If you start
multi-stage and try to change anything structural mid-cook, you can get the cook stuck
in a half-state.

We chose simplicity over the native feature.

### Why STOP by default, with warm-hold as opt-in?

STOP is clearer for public recipes: the display shows `End` / `0:00`, heating stops, and
the user pulls immediately. It also avoids the false impression that a delicate protein
can sit unattended in a warm appliance without continuing to cook.

Warm-hold is still supported as an advanced recipe option. It can be useful when a user
specifically wants a visible mode-change cue:

Two reasons people use it:
1. **The display visibly changes** ("Bake 300°F 30:00" → "Dehydrate 180°F 10:00") which
   is unambiguous to the user
2. **The chamber target drops** while the user takes a moment to plate

The tradeoff is carryover. Food can keep rising, especially fish and chicken breast. For
that reason, built-in public recipes use STOP unless they are explicitly labeled as a
warm-hold cue variant.

### Why a unique MQTT client ID per session?

AWS IoT disconnects duplicate client IDs. The Typhur app uses a deterministic ID format
(`android-{userId}-US-{deviceSn}-{appVersion}`). If our CLI uses the same ID, we and the
phone app would knock each other off the broker repeatedly. So we suffix our cert's
client ID with a random hex string (`-cliron-{8 hex chars}`).

## Network topology

```
            ┌─────────────────────────────────────────────────┐
            │  Your home WiFi (2.4 GHz)                       │
            │                                                  │
            │   [Dome 2] ─────► your router ────► internet    │
            │      ▲                                           │
            │      │ MQTT TLS port 8883                        │
            │      │                                           │
            │   [Probe base] ──► your router ─► internet      │
            │      ▲                                           │
            │      │ BT to probe (915 MHz Sub-1G for WT13)    │
            │      │                                           │
            │   [Probe] (in your food)                         │
            │                                                  │
            │   [Your computer] ► router ──► internet         │
            │                                                  │
            └─────────────────────────────────────────────────┘
                                  │
                                  ▼ internet
                            ┌──────────────────────┐
                            │  Typhur Cloud (AWS)  │
                            │  - REST API (HTTPS)  │
                            │  - MQTT broker (TLS) │
                            └──────────────────────┘
```

Both devices and your computer reach the Typhur cloud independently. They DO NOT talk to
each other directly; everything is mediated by the cloud.

## What CLIronChef does NOT do

- **No local LAN control.** The Dome 2 doesn't expose a LAN API; everything goes via the
  Typhur cloud. You need internet for this to work.
- **No BLE direct control.** The Dome 2's BLE radio is mostly off after initial WiFi
  pairing; re-enabling it requires a button-hold that also breaks WiFi config. Cloud is
  the practical path.
- **No firmware modification.** All commands go through the official cloud protocol.
  The Dome 2's firmware is untouched.
- **No bypass of safety interlocks.** Physical Start, basket-detection auto-pause,
  overheat shutdown, etc. all work exactly as Typhur designed.
- **No analytics or phoning home.** The CLI never sends data to project authors. The
  only network traffic is to Typhur's cloud (which sees your cook activity regardless
  of whether you use the app or this CLI).

## Cross-reference

- [PROTOCOL.md](PROTOCOL.md) — exact HTTP/MQTT wire details (cmdType values, signing, etc.)
- [MODES.md](../cooking/MODES.md) — what each cooking mode does at the device level
- [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md) — the timer-and-state machine in detail
- [HARDWARE.md](HARDWARE.md) — Dome 2 + probe hardware specs
