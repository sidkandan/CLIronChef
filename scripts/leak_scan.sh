#!/usr/bin/env sh
# Public-release leak scan for CLIronChef.
#
# Keep this script free of real maintainer IDs or serial numbers. Use generic
# patterns so the scan can be committed to a public repository without publishing
# the sensitive values it is meant to prevent.
set -eu

FAIL=0

scan_grep() {
  label="$1"
  pattern="$2"
  shift 2

  echo "Scanning for ${label}..."
  if grep -rnE "$pattern" "$@" \
      --exclude-dir=.git \
      --exclude-dir=.venv \
      --exclude-dir=__pycache__ \
      --exclude=PUBLIC_RELEASE_CHECKLIST.md \
      --exclude=.pre-commit-config.yaml \
      .; then
    echo "ERROR: ${label} detected"
    FAIL=1
  fi
}

scan_grep \
  "/Users/<name>/ personal paths" \
  "/Users/[A-Za-z]" \
  --include="*.md" --include="*.py" --include="*.json" --include="*.toml" \
  --include="*.yml" --include="*.yaml"

scan_grep \
  "long numeric device/cmd IDs" \
  "\\b[0-9]{15,24}\\b" \
  --include="*.md" --include="*.py" --include="*.json" --include="*.toml" \
  --include="*.yml" --include="*.yaml"

scan_grep \
  "Typhur-like serial numbers" \
  "\\b(AF|WT)[0-9A-Z]{10,}\\b" \
  --include="*.md" --include="*.py" --include="*.json" --include="*.toml" \
  --include="*.yml" --include="*.yaml"

scan_grep \
  "likely cached credential values" \
  "(password_md5|p12Password|x-token)[[:space:]]*[:=][[:space:]]*[\"']?[A-Za-z0-9._:-]{16,}" \
  --include="*.py" --include="*.json" --include="*.md" --include="*.yml" --include="*.yaml"

scan_grep \
  "inline private key material" \
  "BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY" \
  --include="*.md" --include="*.py" --include="*.json" --include="*.toml" \
  --include="*.yml" --include="*.yaml"

echo "Scanning for credential files..."
if find . -type f \( -name "*.p12" -o -name "*.key" -o -name "*.pem" -o -name "client.crt" \) \
    -not -path "./.git/*" \
    -not -path "./.venv/*" \
    -not -path "./__pycache__/*" | grep .; then
  echo "ERROR: credential files detected"
  FAIL=1
fi

echo "Scanning for runtime telemetry logs..."
if find . -type f \( -name "*.jsonl" -o -name "*.log" -o -name "*.cook.log" \) \
    -not -path "./.git/*" \
    -not -path "./.venv/*" \
    -not -path "./__pycache__/*" | grep .; then
  echo "ERROR: runtime logs detected"
  FAIL=1
fi

echo "Scanning for raw phone media..."
if find . -type f \( -iname "*.mov" -o -iname "*.heic" -o -iname "*.heif" \) \
    -not -path "./.git/*" \
    -not -path "./.venv/*" \
    -not -path "./__pycache__/*" | grep .; then
  echo "ERROR: raw phone media detected; commit stripped derivatives instead"
  FAIL=1
fi

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi

echo "Leak scan passed"
