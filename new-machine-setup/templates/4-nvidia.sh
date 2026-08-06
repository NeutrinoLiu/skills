#!/usr/bin/env bash
# Install the NVIDIA driver Ubuntu recommends for this machine.
# Generated ONLY when an NVIDIA GPU was detected. Requires sudo, ends in a reboot
# — which is why it is last and separate from the other scripts.
#
#   ./4-nvidia.sh          review the plan, then confirm
#   ./4-nvidia.sh --yes    no prompt (for unattended runs)

set -euo pipefail

ASSUME_YES=0
case "${1:-}" in
  --yes|-y) ASSUME_YES=1 ;;
  "")       ;;
  *)        printf 'usage: %s [--yes]\n' "$0" >&2; exit 2 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_env-report.sh
. "$SCRIPT_DIR/_env-report.sh"

die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }
info() { printf '\033[36m==>\033[0m %s\n' "$*"; }

# --- preflight ------------------------------------------------------------
command -v apt-get >/dev/null || die "this script targets Debian/Ubuntu (no apt-get found)"

# Re-check the hardware at run time, not just at generation time — the box may
# have changed, or this script may have been copied to a different machine.
if ! lspci 2>/dev/null | grep -qi 'nvidia'; then
  info "no NVIDIA GPU found on the PCI bus — nothing to do"
  exit 0
fi

info "NVIDIA hardware detected:"
lspci | grep -i nvidia | sed 's/^/    /'

if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  info "a working driver is already installed:"
  nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | sed 's/^/    /'
  printf '\nNothing to do. Re-run only if you intend to change driver versions.\n'
  exit 0
fi

# --- find the recommended driver -----------------------------------------
if ! command -v ubuntu-drivers >/dev/null 2>&1; then
  info "installing ubuntu-drivers-common"
  sudo apt-get update
  sudo apt-get install -y ubuntu-drivers-common
fi

info "available drivers for this GPU:"
ubuntu-drivers devices | sed 's/^/    /'

# The line ubuntu-drivers marks 'recommended' is the one we want.
RECOMMENDED=$(ubuntu-drivers devices 2>/dev/null \
  | awk '/recommended/ {for (i=1;i<=NF;i++) if ($i ~ /^nvidia-driver-/) {print $i; exit}}')

[ -n "$RECOMMENDED" ] || die "could not parse a recommended driver from 'ubuntu-drivers devices' — install manually"

# --- confirm --------------------------------------------------------------
printf '\n'
info "recommended driver: $RECOMMENDED"
printf '    will run: sudo apt-get install -y %s\n' "$RECOMMENDED"
printf '    a reboot is required afterwards.\n\n'

if [ "$ASSUME_YES" -ne 1 ]; then
  read -r -p "Proceed? [y/N] " reply
  case "$reply" in
    [yY]|[yY][eE][sS]) ;;
    *) info "aborted — nothing was changed"; exit 0 ;;
  esac
fi

# --- install --------------------------------------------------------------
sudo apt-get update
sudo apt-get install -y "$RECOMMENDED"

printf '\n'
info "$RECOMMENDED installed."

env_report

printf '\033[1mNEXT:\033[0m  sudo reboot        # required — the kernel module loads on boot\n'
printf '        nvidia-smi         # verify once you are back up\n'
