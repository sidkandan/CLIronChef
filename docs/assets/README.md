# Media Assets

Public-safe media derivatives for the README and documentation.

## Files

- `salmon-result.jpg` — resized, metadata-stripped still image from the first salmon
  cook. Source was an iPhone HEIC; original is not committed.
## Source Media Policy

Do not commit raw phone media (`.mov`, `.heic`, `.heif`). iPhone originals commonly
contain precise GPS location, device model, software version, timestamps, and audio.

Before adding media here:

1. Crop out anything irrelevant or private.
2. Strip metadata with `ffmpeg -map_metadata -1` or an equivalent tool.
3. Remove audio unless there is a clear reason to keep it.
4. Keep README-facing assets small; target under 500 KB when practical.
