#!/usr/bin/env bash
# Deactivate sifteroxy systemd timer

set -euo pipefail

sudo systemctl stop sifteroxy.timer
sudo systemctl disable sifteroxy.timer
sudo systemctl status sifteroxy.timer

