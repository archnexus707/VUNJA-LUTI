#!/usr/bin/env bash
#==============================================================================
#  VUNJA LUTI v6 — fallback installer (when you don't want the .deb)
#  Installs system + python dependencies and builds/installs the package.
#  Preferred install is the .deb: see packaging/build-deb.sh or the Releases page.
#==============================================================================
set -e

MAUVE='\033[38;5;183m'; CYAN='\033[38;5;51m'; GREEN='\033[38;5;46m'
YELLOW='\033[38;5;226m'; RED='\033[38;5;196m'; DIM='\033[2m'; R='\033[0m'
HERE="$(cd "$(dirname "$0")" && pwd)"

step() { echo -e "\n  ${MAUVE}[${CYAN}*${MAUVE}]${R} $1"; }
ok()   { echo -e "  ${GREEN}[OK]${R} $1"; }
warn() { echo -e "  ${YELLOW}[!!]${R} $1"; }

echo -e "${MAUVE}"
echo "   VUNJA LUTI v6 — setup"
echo -e "${R}  ${DIM}Tor proxy · IP rotator · tool wrapper (CLI + GUI)${R}\n"

step "Installing system + python dependencies (apt)…"
sudo apt-get update -qq
sudo apt-get install -y \
    tor proxychains4 \
    python3 python3-stem python3-requests python3-socks python3-pyqt6 \
    fonts-noto-color-emoji fonts-jetbrains-mono 2>/dev/null \
    && ok "dependencies installed" || warn "some packages may have been skipped"

step "Enabling Tor service…"
sudo systemctl enable --now tor 2>/dev/null || sudo service tor start 2>/dev/null || true

if command -v dpkg-deb >/dev/null 2>&1; then
    step "Building and installing the .deb…"
    bash "$HERE/packaging/build-deb.sh"
    sudo apt install -y "$HERE"/dist/vunja-luti_*_all.deb && ok "installed via .deb"
else
    step "dpkg-deb missing — installing with pip instead…"
    pip3 install --break-system-packages -e "$HERE" 2>/dev/null \
        || pip3 install --user -e "$HERE"
    ok "installed via pip (commands: vl, vunja-luti-gui)"
fi

step "Enabling Tor control port for rotation…"
vl doctor --fix 2>/dev/null || warn "run 'vl doctor --fix' manually once"

echo ""
ok "Done. Try:  ${MAUVE}vl status${R}   or launch ${MAUVE}Vunja Luti${R} from your app menu."
echo -e "  ${DIM}Author: archnexus707  |  github.com/archnexus707/VUNJA-LUTI${R}\n"
