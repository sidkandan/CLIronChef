---
name: Recipe proposal
about: Suggest a new built-in recipe for the project
title: '[RECIPE] '
labels: recipe
assignees: ''
---

## Protein / dish

(Name + brief description of what you want to cook)

## Proposed recipe JSON

```json
{
  "name": "...",
  "description": "...",
  "protein": "...",
  "target_doneness": "...",
  "final_internal_after_rest": "...",
  "pull_temp_f": ...,
  "done_signal": "stop" | "warm_hold",
  "phases": [
    {
      "trigger_temp_f": 0.0,
      "mode": <int>,
      "temp_f": <int>,
      "time_s": 2400,
      "name": "..."
    }
  ]
}
```

## Why this recipe / what's the technique

(Explain the cooking strategy — element-bias choice, why these temps, why the phase
transitions land where they do. Reference [docs/MODES.md](../../docs/cooking/MODES.md) where useful.)

## Have you actually cooked it?

(YES / NO. If yes, please describe the result: how the food came out, any tweaks you'd
suggest. If no, please test before we merge — recipes need real-world validation.)

## Source

(If this is from a published recipe, link it. If from your own kitchen, just say so.)
