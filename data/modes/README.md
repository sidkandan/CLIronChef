# Mode Dictionaries

This directory contains the source-of-truth data files describing what each Typhur Dome 2
(AF04) cooking mode does.

## Files

### `af04_modes.json`

The full mode dictionary: 16 modes with their default temps, temp/time ranges, and the
element-bias / fan-speed metadata. This is what `src/cliron_chef/modes.py` consumes.

**Sources:**
- Mode IDs, ranges, and preheat configs: bundled AF04 mode metadata maintained by this
  project
- Element bias and fan speed: from Typhur's official modes guide
  (https://explore.typhur.com/typhur-dome-cooking-modes)

### `af04_probe_presets.json`

Typhur's official probe-cook target temperatures per protein (Beef, Pork, Chicken, Fish,
Whole Chicken).

**Why this file is named "af04" but the data is from "AF13":**
The AF13 (Sync Air Fryer) has an integrated probe. Typhur ships preset target temps for
that probe — those temps are what their engineering team considers "right" for each
protein. The temps don't depend on which model of probe is measuring them; they're
properties of the meat. So the AF13 presets apply equally to the AF04 Dome 2 +
standalone WT01 Sync ONE combination that CLIronChef supports.

The CLIronChef recipes use these temps (especially the `chefsChoice` ones) as targets.

## See also

- [docs/cooking/MODES.md](../../docs/cooking/MODES.md) — human-readable mode reference
- [docs/reference/PROTOCOL.md](../../docs/reference/PROTOCOL.md) — wire format details
- [src/cliron_chef/modes.py](../../src/cliron_chef/modes.py) — Python access
