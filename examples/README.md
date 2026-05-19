# Examples

Real, runnable example code showing how to use CLIronChef from Python (vs. from the CLI).

## Files

| File | What it shows |
|---|---|
| [`python_api_example.py`](python_api_example.py) | Use the Python API directly: login, list devices, run a custom probe-driven cook |
| [`cook_salmon_walkthrough.md`](cook_salmon_walkthrough.md) | Annotated walkthrough of cooking salmon with the CLI, what telemetry looks like, and how to debug |

## Quick recipes for common scripted tasks

### Just get the current Dome 2 chamber temp

```python
from cliron_chef.api import TyphurAPI

api = TyphurAPI.from_cached_credentials()
dome = api.find_dome()
chamber_tenths = dome["lastStatusCmd"]["cmdData"].get("curTemperature", 0)
print(f"Chamber: {chamber_tenths / 10:.1f}°F")
```

### Run a recipe from a script

```python
from cliron_chef import TyphurAPI, RecipeRunner

api = TyphurAPI.from_cached_credentials()
runner = RecipeRunner(api, recipe_path="recipes/salmon_basic.json")
runner.run(max_minutes=20)
```

### Custom probe-driven flow without a recipe

```python
from cliron_chef import TyphurAPI
from cliron_chef.watcher import ProbeWatcher

api = TyphurAPI.from_cached_credentials()
dome = api.find_dome()
probe = api.find_probe()

# Configure the initial cook
_, cook_uuid = api.start_cook("AF04", str(dome["deviceId"]),
    [{"cookingMode": 3, "setTemperature": 450, "setTime": 2400}])

print(f"Configured cook (uuid={cook_uuid}). Press the physical Start button now!")
input("Press ENTER when you've pressed Start...")

# Watch the probe; swap to Bake at 95°F; stop at 120°F
watcher = ProbeWatcher(api, str(dome["deviceId"]), str(probe["deviceId"]), cook_uuid)
watcher.add_swap_at(95, mode=10, temp_f=300, label="Bake gentle finish")
watcher.stop_at(120)
result = watcher.run(max_minutes=20)
print(result)
```

### Subscribe to live telemetry for monitoring

```python
from cliron_chef import TyphurAPI
from cliron_chef.mqtt_client import TyphurMQTT, tenths_to_f
import time

api = TyphurAPI.from_cached_credentials()
mq = TyphurMQTT(api)
mq.subscribe("WT01", str(api.find_probe()["deviceId"]))
mq.on_probe = lambda p: print(f"Probe: {tenths_to_f(p.get('curTemperature')):.1f}°F")
mq.start()
time.sleep(60)
mq.stop()
```

### List all modes biased toward the bottom element (for skin-down protein)

```python
from cliron_chef.modes import list_modes_by_element_bias

for m in list_modes_by_element_bias("bottom"):
    print(f"{m['id']}: {m['name']} — {m['best_for']}")
```

## See also

- [docs/reference/CLI_REFERENCE.md](../docs/reference/CLI_REFERENCE.md) — CLI equivalents of these patterns
- [docs/getting-started/GETTING_STARTED_AI_AGENT.md](../docs/getting-started/GETTING_STARTED_AI_AGENT.md) — for AI agents
