#!/bin/bash
set -euo pipefail
cd /opt/tenderlens/incoming
python3 scripts/deploy_release.py
