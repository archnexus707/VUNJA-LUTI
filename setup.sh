#!/usr/bin/env bash
#==============================================================================
#   VUNJA LUTI — Setup & Dependency Installer
#   Author : archnexus_707
#   Donate : archnexus_707
#==============================================================================
set -e

RED='\033[38;5;196m'; GREEN='\033[38;5;46m'; MAUVE='\033[38;5;183m'
CYAN='\033[38;5;51m'; YELLOW='\033[38;5;226m'; DIM='\033[2m'; R='\033[0m'

banner() {
    echo ""
    echo -e "${MAUVE}       ▄▄    ▄▄  ▄▄    ▄▄  ▄▄▄   ▄▄     ▄▄▄▄▄     ▄▄       ${R}"
    echo -e "${MAUVE}        ▀██  ██▀  ██    ██  ███   ██     ▀▀▀██    ████      ${R}"
    echo -e "${CYAN}         ██  ██   ██    ██  ██▀█  ██        ██    ████      ${R}"
    echo -e "${CYAN}         ██  ██   ██    ██  ██ ██ ██        ██   ██  ██     ${R}"
    echo -e "${GREEN}          ████    ██    ██  ██  █▄██        ██   ██████     ${R}"
    echo -e "${GREEN}          ████    ▀██▄▄██▀  ██   ███  █▄▄▄▄▄██  ▄██  ██▄    ${R}"
    echo -e "${MAUVE}          ▀▀▀▀      ▀▀▀▀    ▀▀   ▀▀▀   ▀▀▀▀▀    ▀▀    ▀▀    ${R}"
    echo ""
    echo -e "  ${DIM}VUNJA LUTI — Dependency Setup${R}"
    echo -e "  ${DIM}Author: archnexus_707  |  Donations welcome${R}"
    echo ""
}

step()  { echo -e "\n  ${MAUVE}[${CYAN}*${MAUVE}]${R} ${1}"; }
ok()    { echo -e "  ${GREEN}[OK]${R} ${1}"; }
warn()  { echo -e "  ${YELLOW}[!!]${R} ${1}"; }
fail()  { echo -e "  ${RED}[XX]${R} ${1}"; }

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo ""
        echo -e "  ${YELLOW}Some steps need root. Using sudo where required.${R}"
        echo -e "  ${YELLOW}You may be prompted for your password.${R}"
        echo ""
    fi
}

# ── 1. System packages ─────────────────────────────────────────
install_system_deps() {
    step "Installing system packages (tor, curl, tmux, fzf, toilet, figlet)..."
    
    sudo apt-get update -qq
    
    local pkgs="tor curl tmux fzf toilet figlet sqlite3"
    for pkg in $pkgs; do
        if dpkg -l "$pkg" 2>/dev/null | grep -q '^ii'; then
            ok "$pkg already installed"
        else
            sudo apt-get install -y "$pkg" 2>/dev/null && ok "$pkg installed" || warn "Failed: $pkg"
        fi
    done
    
    # proxychains4 (optional, for nmap proxying)
    if ! command -v proxychains4 >/dev/null 2>&1; then
        sudo apt-get install -y proxychains4 2>/dev/null && ok "proxychains4 installed" || true
    fi
}

# ── 2. Nerd Fonts (for icon rendering) ─────────────────────────
install_nerd_fonts() {
    step "Installing Nerd Fonts for icon support..."
    
    local font_dir="${HOME}/.local/share/fonts"
    mkdir -p "$font_dir"
    
    # Download JetBrainsMono Nerd Font (compact, full icon support)
    local font_zip="/tmp/JetBrainsMono.zip"
    if [ ! -d "$font_dir/JetBrainsMono" ]; then
        curl -fsSL "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.2.1/JetBrainsMono.zip" \
            -o "$font_zip" 2>/dev/null && {
            unzip -qo "$font_zip" -d "$font_dir/JetBrainsMono" 2>/dev/null
            rm -f "$font_zip"
            fc-cache -fv "$font_dir" 2>/dev/null >/dev/null
            ok "JetBrainsMono Nerd Font installed"
        } || warn "Nerd Font download failed — icons may not render"
    else
        ok "Nerd Font already installed"
    fi
    
    # Emoji font (for flag/country emojis)
    if ! dpkg -l fonts-noto-color-emoji 2>/dev/null | grep -q '^ii'; then
        sudo apt-get install -y fonts-noto-color-emoji 2>/dev/null && \
            ok "Emoji font installed" || warn "Emoji font skipped"
    else
        ok "Emoji font already installed"
    fi
    
    echo -e "  ${DIM}  Restart your terminal after fonts are installed.${R}"
}

# ── 3. Python dependencies ─────────────────────────────────────
install_python_deps() {
    step "Installing Python dependencies..."

    # requests + socks support (try user, then venv, then break-system-packages)
    if python3 -c "import requests" 2>/dev/null; then
        ok "requests already available"
    else
        pip3 install --user requests 'requests[socks]' 2>/dev/null || \
        pip3 install --break-system-packages requests 'requests[socks]' 2>/dev/null || \
        warn "requests install failed — tornet may not work"
    fi

    # rich — beautiful terminal formatting (optional)
    if python3 -c "import rich" 2>/dev/null; then
        ok "rich already available"
    else
        pip3 install --user rich 2>/dev/null && ok "rich installed" || \
        pip3 install --break-system-packages rich 2>/dev/null && ok "rich installed" || \
        warn "rich skipped (optional formatting library)"
    fi
}

# ── 4. tornet module check ─────────────────────────────────────
check_tornet() {
    step "Checking tornet module..."

    local tornet_dir="$(cd "$(dirname "$0")" && pwd)/tornet"

    if [ -f "$tornet_dir/tornet/tornet.py" ]; then
        ok "tornet module found: $tornet_dir"
        return 0
    fi

    warn "tornet module NOT found"

    # Try git clone first
    echo -e "  ${DIM}  Cloning from GitHub (ayadseghairi/tornet)...${R}"
    if git clone https://github.com/ayadseghairi/tornet.git "$tornet_dir" 2>/dev/null; then
        ok "tornet cloned successfully"
        return 0
    fi

    # Fallback: download ZIP
    echo -e "  ${DIM}  Git failed — trying ZIP download...${R}"
    local zip_url="https://github.com/ayadseghairi/tornet/archive/refs/heads/main.zip"
    curl -fsSL "$zip_url" -o /tmp/tornet.zip 2>/dev/null && {
        rm -rf "$tornet_dir"
        unzip -qo /tmp/tornet.zip -d /tmp/tornet_extract 2>/dev/null
        mv /tmp/tornet_extract/tornet-main "$tornet_dir" 2>/dev/null
        rm -f /tmp/tornet.zip
        ok "tornet installed via ZIP"
        return 0
    }

    fail "Could not download tornet — install manually:"
    echo -e "  ${DIM}  git clone https://github.com/ayadseghairi/tornet.git tornet${R}"
}

# ── 5. Tor configuration ───────────────────────────────────────
configure_tor() {
    step "Configuring Tor..."
    
    # Ensure tor is running/enabled
    if ! pgrep -x tor >/dev/null 2>&1; then
        sudo systemctl start tor 2>/dev/null || sudo service tor start 2>/dev/null || true
    fi
    
    # Enable at boot
    sudo systemctl enable tor 2>/dev/null || true
    
    # Check SOCKS port
    sleep 2
    if ss -tln | grep -q '127.0.0.1:9050'; then
        ok "Tor SOCKS5 running on 127.0.0.1:9050"
    else
        warn "Tor SOCKS5 port not detected — check 'sudo systemctl status tor'"
    fi
}

# ── 6. Environment setup ───────────────────────────────────────
setup_environment() {
    step "Setting up environment..."
    
    local config_dir="${HOME}/.config/vl"
    mkdir -p "$config_dir"
    
    # Create default config if missing
    if [ ! -f "$config_dir/config" ]; then
        cat > "$config_dir/config" << 'EOF'
# Vunja Luti Configuration
VL_THEME="catppuccin"
ROTATE_INTERVAL="60"
LOG_FILE=""
BRIDGE_MODE="0"
EXIT_FILTER=""
EOF
        ok "Config created: $config_dir/config"
    fi
    
    # Add to .bashrc if not present (optional alias)
    if ! grep -q "vunja-luti\|Vunja_Luti" "${HOME}/.bashrc" 2>/dev/null; then
        echo "" >> "${HOME}/.bashrc"
        echo "# Vunja Luti Tor Proxy" >> "${HOME}/.bashrc"
        echo "alias vl='$(pwd)/Vunja_Luti.sh'" >> "${HOME}/.bashrc"
        ok "Alias 'vl' added to ~/.bashrc (reload with: source ~/.bashrc)"
    else
        ok "Alias already in ~/.bashrc"
    fi
}

# ── Summary ─────────────────────────────────────────────────────
summary() {
    echo ""
    echo -e "  ${GREEN}╔══════════════════════════════════════════════╗${R}"
    echo -e "  ${GREEN}║     ${MAUVE}VUNJA LUTI — Setup Complete${GREEN}               ║${R}"
    echo -e "  ${GREEN}╚══════════════════════════════════════════════╝${R}"
    echo ""
    
    local checks=()
    command -v tor  >/dev/null 2>&1 && checks+=("${GREEN}Tor") || checks+=("${RED}Tor missing")
    command -v curl >/dev/null 2>&1 && checks+=("${GREEN}curl") || checks+=("${RED}curl missing")
    command -v tmux >/dev/null 2>&1 && checks+=("${GREEN}tmux") || checks+=("${DIM}tmux optional")
    command -v fzf  >/dev/null 2>&1 && checks+=("${GREEN}fzf") || checks+=("${DIM}fzf optional")
    command -v toilet >/dev/null 2>&1 && checks+=("${GREEN}toilet") || checks+=("${DIM}toilet optional")
    python3 -c "import requests" 2>/dev/null && checks+=("${GREEN}requests") || checks+=("${RED}requests missing")
    
    echo -e "  Components: $(IFS=' '; echo "${checks[*]}")${R}"
    echo ""
    echo -e "  ${DIM}To start:${R}    ${MAUVE}./Vunja_Luti.sh start${R}"
    echo -e "  ${DIM}Or via alias:${R} ${MAUVE}vl start${R} ${DIM}(reload terminal first)${R}"
    echo ""
    echo -e "  ${DIM}Author : archnexus_707  |  Donations welcome${R}"
    echo ""
}

# ── Main ────────────────────────────────────────────────────────
banner
check_root
install_system_deps
install_nerd_fonts
install_python_deps
check_tornet
configure_tor
setup_environment
summary
