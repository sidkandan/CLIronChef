# Security Policy

## Supported Versions

This project is pre-1.0. Only the latest commit on `main` is supported.

## Reporting a vulnerability

If you find a security issue, please **do NOT open a public GitHub issue.**

Use GitHub private vulnerability reporting if it is enabled for the repository. If it is
not enabled, open a minimal public issue asking for a private security contact channel;
do not include exploit details, credentials, tokens, certs, logs, or device identifiers
in the public issue.

The maintainer should respond within 7 days. Critical issues will be fixed promptly; others on a
best-effort schedule.

## What counts as a security issue here

This project's threat model is unusual — we're a CLI client talking to a third-party
cloud (Typhur) on behalf of the user. Security issues include:

- **Credential leakage**: any code path that could log, transmit, or persist the user's
  Typhur password or auth token to anywhere except `~/.cliron-chef/`
- **MQTT cert leakage**: same for the AWS IoT client cert
- **Code execution in recipe JSON**: recipe parsing should be data-only; no `eval()` or
  similar. Report if you find a path that's not.
- **Command injection** in any CLI subcommand that interpolates user input into shell
  commands
- **Path traversal** in recipe loading (`cliron-chef cook ../../etc/passwd`)
- **Network downgrades**: if MQTT or HTTPS connections can be downgraded to plain TCP/HTTP
- **DoS amplification**: if the CLI can be tricked into hammering Typhur's cloud in a way
  that gets the user's account banned

## What's NOT a security issue (in scope of this project)

These are intentional, documented behaviors:

- **The Typhur cloud sees your cook activity**. That's how the protocol works. This is
  not a CLIronChef issue; it's how the Dome 2 operates regardless of which client you use.
- **The Typhur SIGN_CONSTANT is in source code**. It is a protocol constant used for
  cloud request signing, not a user secret. Hiding it here would not materially improve
  user security.
- **The CLI does not encrypt your stored credential material.** It stores the MD5
  password hash required by Typhur's protocol and protects local files with filesystem
  permissions (chmod 600). If your OS account is compromised, your Typhur account is at
  risk too — that's a general OS-trust issue, not ours specifically.
- **The physical Start button cannot be bypassed.** This is a firmware safety feature.
  Don't report it as a "missing feature." (Conversely, if you discover a firmware bypass
  exists, please report privately so it can be handled through responsible disclosure.)

## Disclosure timeline

- Day 0: report received
- Day 7: acknowledgment + initial assessment
- Day 14-30: fix developed and tested (if confirmed)
- Day 30-90: coordinated disclosure (release notes + advisory)

## Credit

Reporters who follow this process and want public credit will be named in the release
notes / CHANGELOG. Reporters who want to stay anonymous, will.

## What we WON'T do

- Pursue legal action against good-faith security researchers
- Demand NDAs as a precondition for fixing
- Sit on a critical fix because of PR optics
