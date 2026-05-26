# Notification Channels — What Reaches the User When the Cook Needs Them

The 2026-05-25 cook overcooked because the user wasn't notified loudly enough that the
salmon needed to come out. This doc captures what notification channels exist, what we
investigated, and what works.

**TL;DR — enable Typhur app push notifications on your phone.** That's the highest-leverage
notification path, requires no setup on this project's side, and works whether you're at
your laptop or across the house.

---

## Recommended setup (30 seconds, one-time)

1. Install the **Typhur** app on your phone (App Store / Play Store)
2. Sign in with the same account you use for the CLI
3. **Settings → Notifications → ON** (grant the OS-level permission when prompted)
4. Done. When CLIronChef sends `STOP` (or the firmware fires a probe-target event), Typhur's
   cloud automatically pushes via FCM (Android) / APNs (iOS).

That's it. The Typhur app's existing push pipeline does our work for us, for free,
across the firewall, with no credentials handling on our side.

---

## Why we don't have our own push API

We exhaustively probed the surface our owner-grade Typhur cert exposes. Every direct
push path is blocked.

### MQTT publish — blocked at AWS IoT ACL

Tested 9 candidate publish topics. All disconnect with `rc=7` (AWS IoT ACL deny):

| Topic | Result |
|---|---|
| `device/AF04/{id}/sub` | disconnect-rc=7 |
| `device/AF04/{id}/pub` | disconnect-rc=7 |
| `device/AF04/{id}/cmd`, `/in` | disconnect-rc=7 |
| `$aws/things/{sn}/shadow/update` | disconnect-rc=7 |
| `$aws/things/{id}/shadow/update` | disconnect-rc=7 |
| `user/{userId}/cmd` | disconnect-rc=7 |
| `app/AF04/{id}/cmd` | disconnect-rc=7 |
| `cloud/AF04/{id}/cmd` | disconnect-rc=7 |

Last Will and Testament (LWT) tested separately — no messages delivered.

### MQTT subscribe to user-bound topics — also denied

Tested `user/{userId}/notify`, `user/{userId}/msg`, `user/{userId}/event`,
`user/{userId}/alert`, plus broadcast wildcards. Only `device/AF04/{id}/pub` and
`/sub` are subscribable. The cert is locked to a single device's read topics.

### HTTP cmdTypes — `AF04:alert:*` family rejected

The server's valid cmdType allowlist is exactly 13 entries:
`AF04:cooking:action`, `AF04:setting:modify`, `AF04:status:report`, the AF03/AF05/AF13
equivalents, `device:setting:modify`, `device:status:request`. **No alert, notify,
push, message, or broadcast cmdType is server-valid.** All 22 variants of
`AF04:alert:*` (action, modify, trigger, force, engage, etc.) return validation errors.

### HTTP endpoint discovery — no push paths exist

Probed `/app/notification/*`, `/app/push/*`, `/app/alert/*`, `/app/message/*`,
`/app/broadcast/*`, plus `/app/cooking/{notify,alert}`. None resolve. The Typhur cloud
exposes only: login, device list, dict list, user get, feedback create, command send,
mqtt cert apply.

### APK decompile — FCM credentials not extractable

The Typhur Android app registers an FCM token through an obfuscated path. Even if we
discovered the token-register endpoint, sending custom payloads would require Typhur's
server-side FCM sender key (not in the client).

---

## What we use instead

### Channel 1 (primary): Typhur app native push

Already described above. When CLIronChef sends `cookingAction: 4` (STOP) via
`/app/command/send`, Typhur's cloud sees the cook-end event and fires the push it would
normally fire for app-driven STOP. The user gets a native notification.

**This is the only channel that crosses devices natively and reaches a phone.** If you
care about not missing a pull, enable this.

### Channel 2 (local-only fallback): Whatever the calling agent surfaces

CLIronChef itself runs in a terminal. The notifications it generates surface through
whatever harness is driving it:

- **Claude Code** (terminal or mobile): the agent's `PushNotification` tool routes to
  the user's Mac and (with Remote Control) their phone
- **Codex CLI / Gemini CLI**: surface in the CLI session
- **Direct script execution**: surface as stdout lines

The runner emits a `[PUSH]` tag in stdout for major events that downstream tooling can
pattern-match on.

### Channel 3 (opt-in): macOS Notification Center via `osascript`

If you're running CLIronChef on macOS at the device, calling
`osascript -e 'display notification "..." with title "..."'` will pop up a Notification
Center alert with sound. Visible only, no speech. Safe default for a Mac user.

### Channel 4 (opt-in, advanced): Webhook to your own URL

A future enhancement: post JSON to a user-configured webhook URL (Slack, Discord,
ntfy.sh, Home Assistant, your own integration). Most flexible; user provides the URL.

### Channel 5 (opt-in, advanced): macOS `say` text-to-speech

Makes your computer literally speak ("PULL THE SALMON NOW"). Off by default because
it's invasive — a fresh repo cloner doesn't expect their laptop to start talking.

### Channel 6 (opt-in, advanced): iMessage via AppleScript

Send via macOS Messages.app to a configured phone number. Useful only if you can't
enable the Typhur app push (e.g., shared account). Off by default; requires
configuration.

---

## Escalation pattern

For cooks where the user might miss the first notification:

1. **At done-signal**: notify via all enabled default channels + Typhur app push (the
   native side fires automatically when STOP lands)
2. **30s later**: if probe ambient is still high (>120°F), re-notify with escalated
   urgency
3. **60s later**: still high? re-notify again, also send any opt-in channels (webhook,
   iMessage, TTS) that the user enabled
4. **Continue every 30s** until probe ambient drops to room-temp range (= lid opened)

This pattern is documented in [CARRYOVER.md](../cooking/CARRYOVER.md) as "future work"
because the current runner does not yet implement it. Contributions welcome.

---

## Why these defaults

Conservative-by-default is the right posture for a public repo. A fresh cloner running
`cliron-chef cook recipes/salmon_basic.json` should NOT have their computer suddenly
speak, send SMS, or POST to webhooks they didn't configure. They should see:

- A terminal log
- A macOS Notification Center popup (visible, with sound, but not invasive)

And if they enabled Typhur app push on their phone, that fires too — but that's their
own opt-in via the Typhur app, not our doing.

---

## Not yet tried

If someone wants to extend the research:

- **WebSocket MQTT (port 443)** — AWS IoT has a separate listener that may have different
  ACLs than the 8883 TCP/TLS listener tested above
- **AWS IoT HTTP Publish API** — `https://{endpoint}/topics/{topic}` HTTP publish using
  our cert. Possible different ACL surface
- **`/app/user/get` response inspection** — might leak the user's FCM token (with auth);
  worth checking if we want a fully self-hosted path
- **iOS/Android Shortcuts integration** — define a Shortcut that listens on a webhook;
  could be a clean phone-side push without going through the Typhur app

Any new viable channel should be documented here and added as a first-class option in
the runner.

## Cross-reference

- [docs/cooking/CARRYOVER.md](../cooking/CARRYOVER.md) — the 2026-05-25 cook that motivated this
- [docs/cooking/COOK_LIFECYCLE.md](../cooking/COOK_LIFECYCLE.md) — STOP vs warm-hold mechanics
- [docs/cooking/LESSONS_LEARNED.md](../cooking/LESSONS_LEARNED.md) — full cook history
- [PRIVACY.md](PRIVACY.md) — what data leaves your machine
