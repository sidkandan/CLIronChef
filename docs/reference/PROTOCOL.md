# Wire Protocol

How CLIronChef talks to Typhur's cloud, at the byte level. This doc is for power users,
contributors, and anyone debugging unusual cook behavior.

## Endpoints

### HTTP REST

- **US**: `https://api.iot.typhur.com`
- **EU**: `https://api.iot.typhur.de`

All endpoints are `POST` with JSON body.

| Endpoint | Purpose |
|---|---|
| `/app/account/login` | Authenticate; returns token |
| `/app/account/logout` | Invalidate token |
| `/app/device/bind/list` | List bound devices |
| `/app/mqtt/cert/apply` | Get MQTT client cert (P12) |
| `/app/dict/list` | Server-side dictionaries (mode definitions, broker config) |
| `/app/command/send` | **Send cook commands (the write path)** |
| `/app/device/info/get` | Single-device info |
| `/app/notification/page` | Push notifications history |
| `/app/preset/parameters/list` | Mode parameters (alternate way to get mode dict) |

### MQTT (AWS IoT)

- **US broker**: `a2rac2pr1im2vr-ats.iot.us-west-2.amazonaws.com:8883`
- **EU broker**: dynamic per `/app/dict/list`

Connection: TLS 1.2 with client cert from `/app/mqtt/cert/apply`. The P12 contains:
- Client X.509 cert (subject: CN=AWS IoT Certificate)
- Client private key
- Password: returned in the same API response

### Topics (subscribe-only from our cert)

- `device/{deviceModel}/{deviceId}/pub` — telemetry from device → cloud (we listen)
- `device/{deviceModel}/{deviceId}/sub` — commands from cloud → device (we can also listen, but cannot publish)

Our cert's IoT policy is read-only. Publishing requires server-side relay via REST.

## Authentication

All HTTP requests are signed:

```
sign = MD5(SIGN_CONSTANT | "x-appId=...;x-appVersion=...;...;x-token=..." | body)
```

Header order is alphabetical: `x-appId; x-appVersion; x-deviceSn; x-lang; x-nonce; x-region; x-timestamp; x-token`.

```python
SIGN_CONSTANT = "7d02d81bd7f4483a9a0ac580f2b6ad44"
APP_ID        = "ap206cba3069ed4a11"
APP_VERSION   = "4200"
```

These are protocol constants used by Typhur cloud request signing. They are not user
secrets.

For unauthenticated calls (login), `x-token` is the literal string `"none"`. After login,
use the real token returned in the response.

## Login flow

```
POST /app/account/login
{
  "accountName": "you@example.com",
  "accountPassword": "<MD5 hex of password>",   // 32 hex chars
  "deviceInfo": "cliron-chef"                    // any identifier
}

200 OK
{
  "code": "0",
  "data": {
    "token": "abc123...",
    "userId": "<your_user_id>",
    ...
  }
}
```

Token is valid ~30 days. After expiry, re-login.

## Device discovery flow

```
POST /app/device/bind/list
(empty body, x-token in headers)

200 OK
{
  "code": "0",
  "data": [
    {
      "deviceId": "<your_dome_device_id>",
      "deviceSn": "<device_serial>",
      "deviceType": "airfryer",
      "deviceModel": "AF04",
      "deviceName": "Typhur Dome 2",
      "subTopics": ["device/AF04/<your_dome_device_id>/pub"],
      "lastStatusCmd": { ... },
      ...
    },
    {
      "deviceId": "<your_probe_device_id>",
      "deviceModel": "WT01",
      ...
    }
  ]
}
```

`lastStatusCmd` is a cached snapshot of the last MQTT telemetry from the device — useful
to inspect device state without subscribing to MQTT.

## MQTT cert provisioning

```
POST /app/mqtt/cert/apply
(empty body, x-token in headers)

200 OK
{
  "code": "0",
  "data": {
    "p12Url": "https://file.iot.typhur.com/.../<cert>.p12",
    "p12Password": "<password>",
    "clientId": "android-{userId}-US-{deviceSn}-{appVersion}"
  }
}
```

Download the P12; extract cert + key with openssl:
```bash
openssl pkcs12 -legacy -in client.p12 -out client.crt -clcerts -nokeys -password pass:<password>
openssl pkcs12 -legacy -in client.p12 -out client.key -nocerts -nodes -password pass:<password>
```

(The `-legacy` flag is required because Typhur's P12 uses RC2-40 encryption, which
newer OpenSSL versions disable by default.)

**Important**: AWS IoT disconnects duplicate MQTT client IDs. The phone app uses the
same `clientId` format. To avoid kicking each other off the broker, suffix our connection
with random hex:

```python
client_id = f"{cert['clientId']}-cliron-{uuid.uuid4().hex[:8]}"
```

## Cook command (the write path)

```
POST /app/command/send
{
  "cmdType":  "AF04:cooking:action",
  "deviceId": "<your_dome_device_id>",
  "cmdData": {
    "cookingAction": 1,                  // 1=START, 2=PAUSE, 3=CONTINUE, 4=STOP
    "cookUuid": "<32 hex chars>",        // must match regex [0-9a-z]{32}
    "cookingStageNum": 1,                // ALWAYS 1 for CLIronChef
    "setParams": [
      {
        "cookingMode": 3,                // AF04 mode ID
        "setTemperature": 4500,          // tenths of °F → 450°F
        "setTime": 2400                  // seconds
      }
    ],
    "startClient": "android",            // must be "android" or "ios"
    "cookingData": {                     // metadata for the device display
      "dataType": "preset",
      "dataId": "3",
      "dataName": "Grill",
      "dataImgUrl": ""
    }
  }
}

200 OK
{
  "code": "0",
  "data": { "cmdId": "<cmd_id>" }
}
```

The cloud accepts the command synchronously, returns a `cmdId`, then forwards it to the
device on MQTT. The device receives, acknowledges via `device:cmd:receipt` MQTT
message, and updates its state.

### Hot-modify (mid-cook adjustment)

Same payload, same `cookUuid`. The device firmware accepts and changes its state:

```python
# Configure initial cook
result_1 = send_command("AF04", dome_id, {
    "cookingAction": 1, "cookUuid": <uuid>, "cookingStageNum": 1,
    "setParams": [{"cookingMode": 3, "setTemperature": 4500, "setTime": 2400}],
    ...
})

# Later, hot-modify to a different mode
result_2 = send_command("AF04", dome_id, {
    "cookingAction": 1, "cookUuid": <SAME uuid>, "cookingStageNum": 1,
    "setParams": [{"cookingMode": 10, "setTemperature": 3000, "setTime": 2400}],
    ...
})
```

The device transitions to the new mode without interrupting the cook. This works ONLY if:
- Same `cookUuid` (preserves cook session)
- Same `cookingStageNum` (firmware rejects stage-count changes mid-cook)
- `startClient` matches the original (otherwise `cmdError 512`)

## cmdType matrix

For each device model, the cmdType vocabulary is `{model}:{namespace}:{action}`.

| Model | cooking:action | status:report | setting:modify | probe:search | alert:dismiss |
|---|---|---|---|---|---|
| AF04 | ✓ | ✓ | ✓ | | |
| AF03 (legacy Dome) | ✓ | ✓ | | | |
| AF05 (future Dome) | ✓ | ✓ | ✓ | | |
| AF13 (Sync Air Fryer) | ✓ | ✓ | ✓ | | |
| AF14 (future Sync AF) | ✓ | ✓ | ✓ | | |
| CV03/CV04 (Sync Oven) | ✓ | ✓ | | | |
| CM03/CM04 (Coffee) | ✓ | ✓ | ✓ | | |
| SV03 (Sous Vide) | ✓ | ✓ | | | |
| WT01 (Sync ONE) | ✓ | ✓ | ✓ | ✓ | ✓ |
| WT04/05/08/10/13/14 | ✓ | ✓ | ✓ | ✓ | ✓ |

Cross-device (BLE-related):
- `BT:apply:trust` — pair via Bluetooth
- `BT:user:unbind` — unbind via BT

## MQTT telemetry payload (AF04:status:report)

Active cook example:
```json
{
  "cmdSeqNo": 6202,
  "cmdType": "AF04:status:report",
  "cmdData": {
    "globalStatus": "cooking",
    "cookingState": 3,                   // 3=cooking, 0=paused, 5=stuck/transitional
    "cookingStage": 1,
    "cookingStageNum": 1,
    "cookUuid": "a36b503bb3b34d839c9de7ce92dc7a40",
    "setParams": [
      {"cookingMode": 3, "setTemperature": 4500, "setTime": 2400}
    ],
    "curCookSec": 78,                    // elapsed in current stage (s)
    "curTemperature": 2280,              // chamber temp in tenths of °F (228°F)
    "curRemainingTime": 2322,            // seconds remaining
    "curPreheatTime": 0,
    "curPreheatRemainingTime": 0,
    "curFanSpeed": -1,                   // -1 = firmware-decided
    "curBasketState": 0,                 // 0 in most observed cases (NOT reliable basket-detect)
    "totalCookingTime": [16 ints],       // total seconds per cookingMode (1-16) since lifetime
    "cookingTimeSinceLastClean": [16 ints], // per-mode counter since last self-clean
    "startClient": "android",
    "errorCode": 0
  },
  "deviceTimeSecond": <unix>,
  "userId": "<our userId>",
  "appVersion": "000032",                // device firmware version
  "controlBoardVersion": "020013"
}
```

Idle cook example (no active cook):
```json
{
  "cmdData": {
    "globalStatus": "online",
    "errorCode": 0,
    "totalCookingTime": [16 ints],
    "cookingTimeSinceLastClean": [16 ints],
    "curBasketState": 0
  },
  ...
}
```

## MQTT telemetry payload (WT01:status:report)

```json
{
  "cmdType": "WT01:status:report",
  "cmdData": {
    "globalStatus": "online",
    "probes": [
      {
        "probeColor": "probe1",
        "curTemperature": 1230,              // tenths of °F (123°F)
        "curAmbientTemperature": 1850,       // tenths of °F (185°F)
        "batteryValue": 85,                  // percent
        "cookingState": "cooking"            // probe state machine
      }
    ],
    "batteryValue": 92,
    "wifiRssi": -65
  },
  ...
}
```

If the probe is offline:
```json
{
  "cmdData": {
    "globalStatus": "offline"
  }
}
```

## device:cmd:receipt

After every command, the device emits a receipt:
```json
{
  "cmdType": "device:cmd:receipt",
  "cmdData": {
    "cmdId": "<cmd_id>",                    // matches the cmdId from the REST response
    "cmdType": "AF04:cooking:action",
    "executeResult": "success" | "failure",
    "cmdError": <int>,                       // only on failure
    "deviceStatus": "normal",
    "volume": "normal"
  }
}
```

CLIronChef's watcher logs receipts but doesn't strictly require them to determine
success (we read state from the next `status:report` instead).

## cmdError catalog

| cmdError | Likely meaning |
|---|---|
| 1 | Invalid cook structure (e.g., stage count change attempt) |
| 8 | setTime below curCookSec+safety floor |
| 16 | "No active cook to pause" |
| 32 | "No paused cook to resume" |
| 128 | "No active cook to stop/modify" |
| 512 | startClient mismatch (single-stage) |
| 513 | startClient mismatch on multi-stage |
| 1024 | Device busy / wrong state |

## Temperature encoding

Wire format is **tenths of °F**:
- 4500 = 450.0°F
- 1230 = 123.0°F
- 0 = no value / sensor not active

Conversion: `wire / 10 = °F`.

## Time encoding

Seconds. Time fields:
- `setTime`: programmed cook duration
- `curCookSec`: elapsed in current stage (counts up from 0)
- `curRemainingTime`: setTime - curCookSec (counts down to 0)

## device:status:request (force a fresh report)

```
POST /app/command/send
{
  "cmdType": "device:status:request",
  "deviceId": "<id>",
  "cmdData": { "deviceId": "<id>" }
}
```

The device emits a fresh status:report within ~1 sec. Useful when the cached
`lastStatusCmd` in the device list is stale.

## Server-side validation quirks

- `cookUuid` must match `[0-9a-z]{32}` (UUID hex no dashes). Empty string rejected.
- `cmdId` must NOT be sent by client (server assigns and returns).
- Body schema is `{cmdType, deviceId, cmdData}` only — no other top-level fields permitted.
- `setFanSpeed`, `setHeatPriority`, `setPreheat` are stripped by `/app/command/send`
  (recipe-only fields; not directly settable for cooks).

## Cross-reference

- [ARCHITECTURE.md](ARCHITECTURE.md) — higher-level overview
- [COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md) — state machine + lifecycle
- [`src/cliron_chef/api.py`](../../src/cliron_chef/api.py) — the Python implementation
- Related project: oleost/typhurHA (read-only Typhur telemetry support)
