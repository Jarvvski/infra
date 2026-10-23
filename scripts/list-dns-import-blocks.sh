#!/usr/bin/env bash
# List jarvis.gg DNS records and print Terraform import blocks.
# Requires CLOUDFLARE_API_TOKEN. See scripts/list-dns-import-blocks.py.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/list-dns-import-blocks.py "$@"
