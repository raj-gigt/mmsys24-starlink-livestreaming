#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f docker-compose-emulation.yaml -f docker-compose.lock.yaml -f docker-compose.phase-a.yaml -f docker-compose.player.yaml)
case "${1:-status}" in
  up)
    python3 scripts/prepare_player.py
    "${compose[@]}" up -d --build dashjs chrome stat-server mongo mongo-express nginx livesim2 pyodide
    ;;
  down) "${compose[@]}" down ;;
  status) "${compose[@]}" ps ;;
  *) printf 'Usage: bash scripts/testbed.sh {up|status|down}\n' >&2; exit 2 ;;
esac
