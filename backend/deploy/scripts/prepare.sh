#!/bin/bash
set -euo pipefail
mkdir -p /opt/tenderlens/releases /etc/tenderlens
# Containers remain up until ApplicationStart, including during a first deploy.
# A previous revision cannot block preparing a replacement release.
systemctl is-active --quiet docker
