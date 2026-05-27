#!/usr/bin/env sh
# Public-release leak scan for CLIronChef.
#
# Keep this script free of real maintainer IDs or serial numbers. Use generic
# patterns so the scan can be committed to a public repository without publishing
# the sensitive values it is meant to prevent.
set -eu

FAIL=0

tracked_files() {
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files -- "$@"
  else
    find . -type f "$@"
  fi
}

scan_grep() {
  label="$1"
  pattern="$2"
  shift 2
  files="$(mktemp)"

  echo "Scanning for ${label}..."
  tracked_files "$@" | grep -Ev '(^|/)(docs/project/PUBLIC_RELEASE_CHECKLIST.md|\.pre-commit-config.yaml)$' > "$files" || true
  if [ -s "$files" ] && xargs grep -nE "$pattern" < "$files"; then
    echo "ERROR: ${label} detected"
    FAIL=1
  fi
  rm -f "$files"
}

scan_grep \
  "/Users/<name>/ personal paths" \
  "/Users/[A-Za-z]" \
  "*.md" "*.py" "*.json" "*.toml" "*.yml" "*.yaml"

scan_grep \
  "long numeric device/cmd IDs" \
  "\\b[0-9]{15,24}\\b" \
  "*.md" "*.py" "*.json" "*.toml" "*.yml" "*.yaml"

scan_grep \
  "Typhur-like serial numbers" \
  "\\b(AF|WT)[0-9A-Z]{10,}\\b" \
  "*.md" "*.py" "*.json" "*.toml" "*.yml" "*.yaml"

scan_grep \
  "likely cached credential values" \
  "(password_md5|p12Password|x-token)[[:space:]]*[:=][[:space:]]*[\"']?[A-Za-z0-9._:-]{16,}" \
  "*.py" "*.json" "*.md" "*.yml" "*.yaml"

scan_grep \
  "inline private key material" \
  "BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY" \
  "*.md" "*.py" "*.json" "*.toml" "*.yml" "*.yaml"

echo "Scanning for credential files..."
if tracked_files | grep -E '(^|/)([^/]*\.p12|[^/]*\.key|[^/]*\.pem|client\.crt)$'; then
  echo "ERROR: credential files detected"
  FAIL=1
fi

echo "Scanning for runtime telemetry logs..."
if tracked_files | grep -E '(^|/)[^/]*\.(jsonl|log|cook\.log)$'; then
  echo "ERROR: runtime logs detected"
  FAIL=1
fi

echo "Scanning JPEG metadata..."
if command -v file >/dev/null 2>&1; then
  jpgs="$(mktemp)"
  tracked_files "*.jpg" "*.jpeg" "*.JPG" "*.JPEG" > "$jpgs"
  if [ -s "$jpgs" ] && xargs file < "$jpgs" | grep -Ei "Exif|GPS-Data|iPhone|Apple"; then
    echo "ERROR: JPEG EXIF/device metadata detected; strip images before committing"
    FAIL=1
  fi
  rm -f "$jpgs"
fi

echo "Scanning for raw phone media..."
if tracked_files | grep -Ei '(^|/)[^/]*\.(mov|heic|heif)$'; then
  echo "ERROR: raw phone media detected; commit stripped derivatives instead"
  FAIL=1
fi

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi

echo "Leak scan passed"
