#!/usr/bin/env bash
# Write a gitignored backend.hcl from R2_ENDPOINT.
# The endpoint contains the Cloudflare account id, so this file must stay untracked.
set -euo pipefail

dest="${1:-backend.hcl}"
endpoint="${R2_ENDPOINT:-}"

if [[ ! "$endpoint" =~ ^https://[0-9a-fA-F]{32}(\.(eu|fedramp))?\.r2\.cloudflarestorage\.com$ ]]; then
  echo "R2_ENDPOINT must be https://<account_id>.r2.cloudflarestorage.com" >&2
  echo "Optional jurisdiction labels: .eu or .fedramp before .r2. The value was not printed." >&2
  exit 1
fi

umask 077
cat >"$dest" <<EOF
endpoints = {
  s3 = "${endpoint}"
}
EOF
