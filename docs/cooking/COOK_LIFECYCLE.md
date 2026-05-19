# Cook Lifecycle and Timer Semantics

The easiest way to lose control of a Dome 2 cook is to misunderstand the timer. This
file is the authoritative lifecycle guide for humans, AI agents, and recipe authors.

Every fresh CLI session should read this before designing a cook.

## TL;DR

1. The Dome 2 timer counts down from `setTime`.
2. When the timer reaches `0`, the cook is over. Heating stops and the display shows
   `End` / `0:00`.
3. A cook that ended by timer expiry or STOP cannot be hot-modified back into life.
   Continuing requires a fresh cook config and another physical Start press.
4. Probe-driven cooks should end by probe target, not by countdown expiry.
5. Use `setTime=2400` as a control buffer for cooking phases, reassert it on every
   hot-modify, and send STOP at the pull target unless the recipe explicitly opts into
   an advanced warm-hold cue.

## Lifecycle

```
IDLE
  globalStatus=online
  no active cook
    |
    | cliron-chef cook ... sends cookingAction=1
    v
CONFIGURED
  display shows mode/temp/time
  cookUuid is bound to startClient=android
  heating elements are still off
    |
    | user presses physical Start
    v
COOKING
  cookingState=3
  timer counts down from setTime
  agent may hot-modify mode/temp/time with same cookUuid
    |
    | probe reaches pull target
    v
STOP SENT
  cookingAction=4
  display shows End / 0:00
  heating stops
    |
    v
ENDED
  no active cook for hot-modify
  next cook requires new config + physical Start
```

## The Normal Endpoint: STOP At Probe Target

For public recipes and first-time users, STOP is the default endpoint.

When the probe reaches `pull_temp_f`, the runner sends:

```python
api.stop_cook("AF04", dome_id, cook_uuid=active_cook_uuid)
```

What the user sees:

- Display changes to `End` / `0:00`
- The device beeps
- Heating stops
- The user pulls the food and rests it

This is terminal by design. That is fine at the correct probe target. It is a problem
only when it happens too early.

## Timer Zero Is Terminal

Do not use the timer as the endpoint for probe-managed cooking. The timer is only there
to keep the active cook session alive while probe telemetry decides what to do.

Never do these during an adaptive cook:

- Set `setTime=0`
- Shorten `setTime` so the countdown immediately expires
- Let `curRemainingTime` reach zero while the probe is still below target
- Treat a timer-ended cook as something the CLI can rearm without a human

If the timer reaches zero early, assume:

1. The display says `End` / `0:00`
2. Heating is off
3. The active `cookUuid` is no longer useful for normal hot-modify
4. A new command can configure a new cook, but the user must press physical Start again

## Timer Buffer Rules

Use these rules in every watcher, recipe runner, or AI-agent script:

- Initial cooking phase: `setTime=2400`
- Every hot-modify: re-send `setTime=2400`
- Monitor `curRemainingTime`
- If `curRemainingTime < 300` and the food is not done, refresh the active mode/temp
  with `setTime=2400` and the same `cookUuid`
- Use a `max_minutes` backstop that sends STOP if probe telemetry never reaches target
- Never use API PAUSE; this firmware treats it as effectively terminal

Example timer refresh:

```python
api.hot_modify(
    "AF04",
    dome_id,
    active_cook_uuid,
    mode=current_mode,
    temp_f=current_temp_f,
    time_s=2400,
)
```

## Warm-Hold Cue Is Advanced And Opt-In

`done_signal: "warm_hold"` hot-modifies the active cook to a low-temp cue mode instead of
sending STOP immediately:

```python
api.hot_modify("AF04", dome_id, active_cook_uuid, mode=13, temp_f=180, time_s=600)
```

This can be useful as a visible cue because the display changes to something like
`Dehydrate 180°F 10:00`. It is not a magic holding oven. Food can keep rising in
temperature, especially delicate fish and chicken breast.

Use warm-hold only when all of these are true:

- The recipe explicitly sets `done_signal: "warm_hold"`
- The user knows to pull promptly when the display changes
- The food is tolerant of a little carryover
- The agent remains online and ready to send STOP if anything looks wrong

Do not make warm-hold the default for public recipes. STOP is clearer and safer for
first-time users.

## Stuck State 5

`cookingState=5` is an undocumented state seen after invalid mid-cook structural
changes, especially changing `cookingStageNum`. It can look like a timer-zero event even
though telemetry still says the device is in a partial cook state.

Avoid it:

- Start with `cookingStageNum=1`
- Keep every hot-modify single-stage
- Do not add or remove stages mid-cook

If you see `cookingState=5`, do not assume recovery is safe. Run `cliron-chef status`,
tell the user what the device display shows, and prefer STOP unless you are deliberately
testing recovery with the user present.

## Watcher Checklist

- [ ] CLI configured the cook before the user pressed Start
- [ ] Active cook has `startClient=android`
- [ ] Initial phase uses `setTime=2400`
- [ ] Hot-modifies keep the same `cookUuid`
- [ ] Hot-modifies keep `cookingStageNum=1`
- [ ] Hot-modifies reassert `setTime=2400`
- [ ] Watcher subscribes to both AF04 and WT01 telemetry
- [ ] Watcher triggers phase changes by probe temperature
- [ ] Watcher sends STOP at `pull_temp_f` unless recipe explicitly uses warm-hold
- [ ] Watcher refreshes timer buffer below 300 seconds
- [ ] Watcher has a max-minutes STOP backstop
- [ ] Watcher logs enough telemetry to debug carryover and failures

## Action Values

| Action | Value | Use |
|---|---:|---|
| START | 1 | Initial configure and hot-modify |
| PAUSE | 2 | Avoid; effectively terminal in this firmware |
| CONTINUE | 3 | Avoid; API PAUSE is not a reliable resumable state |
| STOP | 4 | End an active cook at probe target or safety timeout |

## Cross-Reference

- [PROTOCOL.md](../reference/PROTOCOL.md) — wire payloads, `cmdError` values, and command shapes
- [MODES.md](MODES.md) — mode selection by element bias and fan behavior
- [RECIPES.md](RECIPES.md) — recipe schema and done-signal fields
- [GETTING_STARTED_AI_AGENT.md](../getting-started/GETTING_STARTED_AI_AGENT.md) — agent operating rules
