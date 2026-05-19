# Disclaimer

This document captures the full legal, ethical, and operational context of CLIronChef.
**Read it before you fork, distribute, or operate this project.**

---

## Not affiliated with Typhur Inc.

CLIronChef is a community-built interoperability project. It is **not affiliated with,
endorsed by, sponsored by, or approved by Typhur Inc.** All Typhur product names
(Dome 2, Sync ONE, Sync Air Fryer, etc.) are trademarks of Typhur Inc., used here under
nominative fair use to identify the hardware this software interoperates with.

The project's trademark and interoperability notice lives in [NOTICE](NOTICE). The
project license itself is the canonical MIT text in [LICENSE](LICENSE).

## Independent interoperability notice

CLIronChef is intended for owners of Typhur hardware who want to operate their own
devices from a CLI or automation workflow. It communicates with Typhur cloud services
using user-provided Typhur account credentials and documented local configuration files.

This project is not legal advice. Third-party service terms, platform policies, and local
law vary by region and use case. If you fork, redistribute, or operate this project
outside personal experimentation, you are responsible for understanding those obligations.

Typhur may change its cloud services, terms, firmware behavior, or account-enforcement
policies at any time. If that risk is unacceptable, keep your fork private and use the
official Typhur app instead.

## No warranty

THIS SOFTWARE IS PROVIDED "AS IS". The authors make no warranty about:

- **Food safety**: cook times and temperatures in `recipes/` reflect the authors'
  preferences. Use a food thermometer for any cook where doneness matters.
  Follow [USDA safe minimum internal temperatures](https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures)
  for vulnerable populations (children, pregnant individuals, immunocompromised).
- **Device safety**: this software talks to your Dome 2 over Typhur's official cloud
  using verified API calls. There is no known way for any cloud command to put the
  device into an unsafe state (the firmware itself enforces safety interlocks).
  However, we cannot guarantee what future firmware versions will do.
- **Account safety**: your Typhur credentials are stored on your machine (MD5-hashed
  per Typhur's protocol). We recommend a dedicated Typhur account for CLI use, not
  your primary one.
- **Continued functionality**: Typhur may change the cloud protocol at any time, may
  ban accounts they detect as "non-app traffic," or may take other actions that
  break this software.

## Operational safety

**Always supervise active cooks.** Do not walk away from a Dome 2 that's running.
This is true regardless of whether the cook is started from the phone app or this CLI.

The Dome 2 has hardware-level safety interlocks:
- 20-minute idle auto-shutoff
- Auto-pause when basket is removed
- Auto-shutdown on overheat (error codes E1, E2, E3, E11)

The **physical Start button is intentionally not bypassable** by any software path —
this is a UL/IEC safety compliance feature. The CLI configures the cook program; a
human must press Start. This is by design and we will not document any workaround
even if one existed.

See [SAFETY.md](SAFETY.md) for the full operational safety model.

## Privacy

Your Typhur credentials are stored locally only:
- `~/.cliron-chef/credentials` (your email + MD5-hashed password)
- `~/.cliron-chef/token` (the Typhur cloud auth token, expires periodically)
- `~/.cliron-chef/client.{p12,crt,key}` (the AWS IoT MQTT client cert)

These files are added to the project's `.gitignore`. They are NEVER sent anywhere
except to Typhur's own cloud servers (per Typhur's standard auth/MQTT flow).

The CLI itself does not phone home, collect telemetry, or send any data to project
authors. There is no analytics, no error reporting, no usage metrics.

See [docs/project/PRIVACY.md](docs/project/PRIVACY.md) for more.

## What we are NOT responsible for

- Bricked devices (we don't know of any cloud command that can brick a Dome 2, but
  Typhur firmware updates could change this)
- Burned food
- Account suspension by Typhur for "non-app traffic"
- Trademark / IP disputes from Typhur Inc.
- Personal injury from operating a heat appliance
- Fires (this is your responsibility regardless of whether you use a CLI)
- Loss of data in `~/.cliron-chef/`

## When to NOT use this software

- If you're cooking food for vulnerable populations who require strict USDA-temp
  adherence and you're not personally verifying internal temps
- If you're operating in a commercial kitchen where this would violate health code
- If local law, workplace policy, or Typhur's terms prohibit this type of automation

## Acknowledgments

This project builds on prior work by:
- [oleost/typhurHA](https://github.com/oleost/typhurHA) — read-only Home Assistant
  add-on for Typhur cloud telemetry
- Various owner-community forums and reviewers who documented Dome 2 quirks
- The broader home-automation and interoperability community

We attempt to give credit where due. If you believe your work is uncredited and should
be, please open an issue.
