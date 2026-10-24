#!/bin/bash
set -euo pipefail
for attempt in $(seq 1 60); do
  if curl --fail --silent http://127.0.0.1:8080/health/ready > /dev/null; then
    curl --fail --silent http://127.0.0.1:8080/ > /dev/null
    exit 0
  fi
  sleep 2
done
echo 'Application readiness check failed.' >&2
exit 1
