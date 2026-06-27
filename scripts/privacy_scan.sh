#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

patterns=(
  "workspace_id"
  "webhook"
  "access_token"
  "secret"
  "password"
  "private_key"
  "client_secret"
  "TAPD"
  "GitLab"
  "Jenkins"
  "DingTalk"
)

local_patterns_file="$ROOT_DIR/config/privacy_patterns.local.txt"
if [[ -f "$local_patterns_file" ]]; then
  while IFS= read -r pattern; do
    [[ -z "$pattern" || "$pattern" == \#* ]] && continue
    patterns+=("$pattern")
  done < "$local_patterns_file"
fi

allowlist=(
  ".gitignore"
  "README.md"
  "scripts/privacy_scan.sh"
  "docs/security.md"
  "app/storage.py"
)

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

cd "$ROOT_DIR"

for pattern in "${patterns[@]}"; do
  rg -n --hidden --glob '!.git/**' --glob '!tasks/**' --glob '!knowledge/**' --glob '!logs/**' --glob '!reports/**' --glob '!config/*.local.json' --glob '!config/*.secret.json' --glob '!*.token' --glob '!*.key' --glob '!*.pem' -- "$pattern" . >> "$tmp_file" || true
done

if [[ ! -s "$tmp_file" ]]; then
  echo "privacy scan passed: no sensitive markers found"
  exit 0
fi

blocked=0
while IFS= read -r line; do
  file="${line#./}"
  file="${file%%:*}"
  allowed=0
  for allowed_file in "${allowlist[@]}"; do
    if [[ "$file" == "$allowed_file" ]]; then
      allowed=1
      break
    fi
  done
  if [[ "$allowed" -eq 0 ]]; then
    echo "privacy scan blocked: $line"
    blocked=1
  fi
done < "$tmp_file"

if [[ "$blocked" -eq 1 ]]; then
  exit 1
fi

echo "privacy scan passed: only allowlisted safety documentation/template matches found"
