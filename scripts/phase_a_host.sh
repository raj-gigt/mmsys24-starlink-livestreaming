#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts/setup artifacts/logs
case "${1:-verify}" in
  verify)
    docker version --format '{{json .}}' > artifacts/setup/docker-version.json
    docker info --format '{"os":"{{.OSType}}","architecture":"{{.Architecture}}","cpus":{{.NCPU}},"memory_bytes":{{.MemTotal}}}' > artifacts/setup/docker-host.json
    docker compose version > artifacts/setup/compose-version.txt
    docker compose -f docker-compose-emulation.yaml config > artifacts/setup/compose-upstream.yaml
    docker run --rm --cap-add NET_ADMIN alpine:3.20 sh -c 'ip link add leo-check type dummy; ip link show leo-check; ip link del leo-check' > artifacts/setup/net-admin.txt
    printf 'Host and container NET_ADMIN checks passed.\n'
    ;;
  pull-analysis)
    docker pull clarkzjw/mmsys24-reproducibility > artifacts/logs/pull-analysis.log 2>&1
    docker image inspect clarkzjw/mmsys24-reproducibility > artifacts/setup/analysis-image.json
    printf 'Analysis image ready.\n'
    ;;
  reproduce)
    mkdir -p paper-figures
    docker run --rm --name leo-phase-a-reproduction \
      -v "$PWD/paper-data/data:/data:ro" \
      -v "$PWD/paper-figures:/app/src/figures" \
      clarkzjw/mmsys24-reproducibility > artifacts/logs/reproduction.log 2>&1
    printf 'Archived figures regenerated.\n'
    ;;
  pull-testbed)
    for attempt in 1 2 3; do
      if docker compose --parallel 2 -f docker-compose-emulation.yaml pull >> artifacts/logs/pull-testbed.log 2>&1; then break; fi
      if [ "$attempt" = 3 ]; then exit 1; fi
      sleep 5
    done
    printf 'Testbed images ready.\n'
    ;;
  *) printf 'Unknown operation\n' >&2; exit 2 ;;
esac
