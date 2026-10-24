#!/bin/bash
set -euo pipefail
mkdir -p /opt/tenderlens/release /etc/tenderlens
# Containers remain up until ApplicationStart, including during a first deploy.
# No ApplicationStop hook: a previous revision cannot block future releases.
systemctl is-active --quiet docker
