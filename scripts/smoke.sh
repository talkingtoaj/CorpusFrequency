#!/usr/bin/env bash
# Smoke Test: proves the deployed app really answers. Every stage runs this
# same script against a base URL (production, staging, or a "candidate" tag URL).
#
#   scripts/smoke.sh https://corpusfrequency-abc-uc.a.run.app
#
# Grow it with the stage:
#   Auto-deploy: /health returns 200.
#   Gated:       /health checks the database and bucket for real, plus one real
#                user path (create something and load it back).
#   Staged:      plus config guards (e.g. the frontend's baked API URL is https).
set -euo pipefail
URL="${1:?usage: smoke.sh BASE_URL}"
URL="${URL%/}"

check() {  # check PATH [grep-pattern]
  local body
  body="$(curl -fsS --retry 5 --retry-delay 3 --retry-all-errors --max-time 20 "$URL$1")" \
    || { echo "FAIL $1"; exit 1; }
  if [[ -n "${2:-}" ]] && ! grep -q "$2" <<<"$body"; then
    echo "FAIL $1: missing '$2'"; exit 1
  fi
  echo "ok   $1"
}

check /health
check /accounts/login/
# check /api/things '"id"'      # one real user path (Gated and up)
