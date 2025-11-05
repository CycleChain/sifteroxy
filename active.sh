#!/usr/bin/env bash
# Activate sifteroxy systemd timer

set -euo pipefail

sudo systemctl daemon-reload
sudo systemctl enable --now sifteroxy.timer
sudo systemctl status sifteroxy.timer

