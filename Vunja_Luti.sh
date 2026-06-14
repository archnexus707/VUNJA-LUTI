#!/usr/bin/env bash
#==============================================================================
#   VL v4.0 — VUNJA LUTI — Tor Proxy + IP Rotator
#   Enhanced: SOCKS5-routed geo, stream isolation, obfs4 bridges,
#            circuit visualization, proxy chain fallback, per-app proxy,
#            bandwidth sparklines, exit node filter, traffic normalization,
#            kill switch, live progress bars, 3-panel tmux dashboard,
#            theme engine, fzf menus, sound design, ASCII rings,
#            keyboard shortcuts, status bars, FIGlet banners, JSON export
#==============================================================================
set -e

TORN_DIR="$(cd "$(dirname "$0")" && pwd)/tornet"
if [ ! -d "$TORN_DIR/tornet" ]; then
    echo -e "\033[38;5;196m[FATAL] tornet module not found at: $TORN_DIR/tornet\033[0m"
    echo -e "\033[2mClone it: git clone https://github.com/AnonC0D3/tornet.git \"$TORN_DIR\"\033[0m"
    exit 1
fi
if [ ! -f "$TORN_DIR/tornet/tornet.py" ]; then
    echo -e "\033[38;5;196m[FATAL] tornet.py not found — tornet directory incomplete\033[0m"
    exit 1
fi
CONFIG_DIR="${HOME}/.config/vl"
mkdir -p "$CONFIG_DIR"

# ═══════════════════════════════════════════════════════════════
#   THEME ENGINE — Hyprland-Rice Inspired Color Systems
# ═══════════════════════════════════════════════════════════════

THEME="${VL_THEME:-catppuccin}"

# ── Palette definitions ────────────────────────────────────────
declare -A PALETTE
palette_catppuccin() {  # Catppuccin Mocha (mauve + lavender gradient)
    PALETTE=(
        [base]='\033[38;5;235m'      [surface]='\033[38;5;237m'
        [overlay]='\033[38;5;239m'   [text]='\033[38;5;188m'
        [subtext]='\033[38;5;145m'   [accent]='\033[38;5;183m'
        [accent2]='\033[38;5;147m'   [accent3]='\033[38;5;111m'
        [mauve]='\033[38;5;183m'     [lavender]='\033[38;5;147m'
        [blue]='\033[38;5;111m'      [teal]='\033[38;5;80m'
        [green]='\033[38;5;114m'     [yellow]='\033[38;5;221m'
        [peach]='\033[38;5;216m'     [red]='\033[38;5;210m'
        [pink]='\033[38;5;211m'      [maroon]='\033[38;5;132m'
        [sky]='\033[38;5;117m'       [sapphire]='\033[38;5;75m'
        [flamingo]='\033[38;5;218m'  [rosewater]='\033[38;5;224m'
    )
}
palette_tokyo_night() {  # Tokyo Night Storm
    PALETTE=(
        [base]='\033[38;5;234m'      [surface]='\033[38;5;236m'
        [overlay]='\033[38;5;59m'    [text]='\033[38;5;189m'
        [subtext]='\033[38;5;103m'   [accent]='\033[38;5;111m'
        [accent2]='\033[38;5;68m'    [accent3]='\033[38;5;140m'
        [mauve]='\033[38;5;140m'     [lavender]='\033[38;5;111m'
        [blue]='\033[38;5;75m'       [teal]='\033[38;5;73m'
        [green]='\033[38;5;114m'     [yellow]='\033[38;5;221m'
        [peach]='\033[38;5;216m'     [red]='\033[38;5;204m'
        [pink]='\033[38;5;212m'      [maroon]='\033[38;5;96m'
        [sky]='\033[38;5;81m'        [sapphire]='\033[38;5;69m'
        [flamingo]='\033[38;5;211m'  [rosewater]='\033[38;5;224m'
    )
}
palette_nord() {  # Nord Aurora
    PALETTE=(
        [base]='\033[38;5;235m'      [surface]='\033[38;5;59m'
        [overlay]='\033[38;5;60m'    [text]='\033[38;5;189m'
        [subtext]='\033[38;5;109m'   [accent]='\033[38;5;111m'
        [accent2]='\033[38;5;110m'   [accent3]='\033[38;5;115m'
        [mauve]='\033[38;5;147m'     [lavender]='\033[38;5;111m'
        [blue]='\033[38;5;75m'       [teal]='\033[38;5;80m'
        [green]='\033[38;5;114m'     [yellow]='\033[38;5;222m'
        [peach]='\033[38;5;216m'     [red]='\033[38;5;204m'
        [pink]='\033[38;5;211m'      [maroon]='\033[38;5;132m'
        [sky]='\033[38;5;117m'       [sapphire]='\033[38;5;69m'
        [flamingo]='\033[38;5;218m'  [rosewater]='\033[38;5;224m'
    )
}
palette_everforest() {  # Everforest Dark
    PALETTE=(
        [base]='\033[38;5;234m'      [surface]='\033[38;5;236m'
        [overlay]='\033[38;5;59m'    [text]='\033[38;5;187m'
        [subtext]='\033[38;5;144m'   [accent]='\033[38;5;150m'
        [accent2]='\033[38;5;108m'   [accent3]='\033[38;5;72m'
        [mauve]='\033[38;5;175m'     [lavender]='\033[38;5;147m'
        [blue]='\033[38;5;75m'       [teal]='\033[38;5;80m'
        [green]='\033[38;5;114m'     [yellow]='\033[38;5;221m'
        [peach]='\033[38;5;216m'     [red]='\033[38;5;204m'
        [pink]='\033[38;5;211m'      [maroon]='\033[38;5;132m'
        [sky]='\033[38;5;117m'       [sapphire]='\033[38;5;69m'
        [flamingo]='\033[38;5;218m'  [rosewater]='\033[38;5;224m'
    )
}
palette_rose_pine() {  # Rosé Pine Moon
    PALETTE=(
        [base]='\033[38;5;234m'      [surface]='\033[38;5;236m'
        [overlay]='\033[38;5;95m'    [text]='\033[38;5;224m'
        [subtext]='\033[38;5;181m'   [accent]='\033[38;5;218m'
        [accent2]='\033[38;5;211m'   [accent3]='\033[38;5;175m'
        [mauve]='\033[38;5;183m'     [lavender]='\033[38;5;147m'
        [blue]='\033[38;5;117m'      [teal]='\033[38;5;80m'
        [green]='\033[38;5;114m'     [yellow]='\033[38;5;222m'
        [peach]='\033[38;5;216m'     [red]='\033[38;5;204m'
        [pink]='\033[38;5;211m'      [maroon]='\033[38;5;132m'
        [sky]='\033[38;5;117m'       [sapphire]='\033[38;5;75m'
        [flamingo]='\033[38;5;218m'  [rosewater]='\033[38;5;224m'
    )
}
palette_dracula() {  # Dracula
    PALETTE=(
        [base]='\033[38;5;235m'      [surface]='\033[38;5;237m'
        [overlay]='\033[38;5;239m'   [text]='\033[38;5;255m'
        [subtext]='\033[38;5;145m'   [accent]='\033[38;5;141m'
        [accent2]='\033[38;5;212m'   [accent3]='\033[38;5;117m'
        [mauve]='\033[38;5;141m'     [lavender]='\033[38;5;111m'
        [blue]='\033[38;5;117m'      [teal]='\033[38;5;80m'
        [green]='\033[38;5;120m'     [yellow]='\033[38;5;228m'
        [peach]='\033[38;5;216m'     [red]='\033[38;5;210m'
        [pink]='\033[38;5;212m'      [maroon]='\033[38;5;132m'
        [sky]='\033[38;5;117m'       [sapphire]='\033[38;5;75m'
        [flamingo]='\033[38;5;218m'  [rosewater]='\033[38;5;224m'
    )
}
palette_gruvbox() {  # Gruvbox Dark
    PALETTE=(
        [base]='\033[38;5;234m'      [surface]='\033[38;5;236m'
        [overlay]='\033[38;5;240m'   [text]='\033[38;5;223m'
        [subtext]='\033[38;5;144m'   [accent]='\033[38;5;208m'
        [accent2]='\033[38;5;142m'   [accent3]='\033[38;5;130m'
        [mauve]='\033[38;5;175m'     [lavender]='\033[38;5;147m'
        [blue]='\033[38;5;109m'      [teal]='\033[38;5;108m'
        [green]='\033[38;5;142m'     [yellow]='\033[38;5;214m'
        [peach]='\033[38;5;208m'     [red]='\033[38;5;203m'
        [pink]='\033[38;5;175m'      [maroon]='\033[38;5;131m'
        [sky]='\033[38;5;109m'       [sapphire]='\033[38;5;69m'
        [flamingo]='\033[38;5;218m'  [rosewater]='\033[38;5;224m'
    )
}
palette_cyberpunk() {  # Classic Cyberpunk Neon
    PALETTE=(
        [base]='\033[38;5;233m'      [surface]='\033[38;5;235m'
        [overlay]='\033[38;5;238m'   [text]='\033[38;5;255m'
        [subtext]='\033[38;5;245m'   [accent]='\033[38;5;201m'
        [accent2]='\033[38;5;51m'    [accent3]='\033[38;5;129m'
        [mauve]='\033[38;5;201m'     [lavender]='\033[38;5;129m'
        [blue]='\033[38;5;51m'       [teal]='\033[38;5;50m'
        [green]='\033[38;5;46m'      [yellow]='\033[38;5;226m'
        [peach]='\033[38;5;214m'     [red]='\033[38;5;196m'
        [pink]='\033[38;5;201m'      [maroon]='\033[38;5;125m'
        [sky]='\033[38;5;45m'        [sapphire]='\033[38;5;33m'
        [flamingo]='\033[38;5;206m'  [rosewater]='\033[38;5;225m'
    )
}
palette_matrix() {  # Matrix Green
    PALETTE=(
        [base]='\033[38;5;232m'      [surface]='\033[38;5;234m'
        [overlay]='\033[38;5;236m'   [text]='\033[38;5;46m'
        [subtext]='\033[38;5;70m'    [accent]='\033[38;5;46m'
        [accent2]='\033[38;5;82m'    [accent3]='\033[38;5;34m'
        [mauve]='\033[38;5;46m'      [lavender]='\033[38;5;82m'
        [blue]='\033[38;5;46m'       [teal]='\033[38;5;48m'
        [green]='\033[38;5;46m'      [yellow]='\033[38;5;190m'
        [peach]='\033[38;5;208m'     [red]='\033[38;5;196m'
        [pink]='\033[38;5;46m'       [maroon]='\033[38;5;34m'
        [sky]='\033[38;5;48m'        [sapphire]='\033[38;5;34m'
        [flamingo]='\033[38;5;46m'   [rosewater]='\033[38;5;82m'
    )
}

apply_theme() {
    # Select palette by theme name
    case "$THEME" in
        catppuccin|catppuccin-mocha)   palette_catppuccin ;;
        tokyo|tokyo-night)             palette_tokyo_night ;;
        nord|aurora)                   palette_nord ;;
        everforest)                    palette_everforest ;;
        rose-pine|rosepine)            palette_rose_pine ;;
        dracula)                       palette_dracula ;;
        gruvbox|gruvbox-dark)          palette_gruvbox ;;
        cyberpunk)                     palette_cyberpunk ;;
        matrix)                        palette_matrix ;;
        *)                             palette_catppuccin ;;
    esac

    # Primary semantic colors (derived from palette)
    C_ACCENT="${PALETTE[accent]}"      C_ACCENT2="${PALETTE[accent2]}"
    C_ACCENT3="${PALETTE[accent3]}"    C_GOOD="${PALETTE[green]}"
    C_WARN="${PALETTE[yellow]}"        C_BAD="${PALETTE[red]}"
    C_INFO="${PALETTE[teal]}"          C_SUBTLE="${PALETTE[subtext]}"
    C_HI="${PALETTE[text]}"            C_DIM='\033[2m'
    C_BOLD='\033[1m'                   C_ITALIC='\033[3m'
    C_UNDERLINE='\033[4m'              C_BLINK='\033[5m'
    C_INVERT='\033[7m'                 C_PANE="${PALETTE[overlay]}"
    C_MAUVE="${PALETTE[mauve]}"        C_LAV="${PALETTE[lavender]}"
    C_BLUE="${PALETTE[blue]}"          C_TEAL="${PALETTE[teal]}"
    C_PINK="${PALETTE[pink]}"          C_FLAMINGO="${PALETTE[flamingo]}"
    C_ROSE="${PALETTE[rosewater]}"     C_PEACH="${PALETTE[peach]}"
    C_SKY="${PALETTE[sky]}"            C_SAPPHIRE="${PALETTE[sapphire]}"
    C_SURFACE="${PALETTE[surface]}"    C_BASE="${PALETTE[base]}"
    R='\033[0m'
}
apply_theme

# ── Gradient & visual helpers ──────────────────────────────────
# Gradient box: gradient_box "top-left" "top-right" "horizontal" "vertical" "bottom-left" "bottom-right"
gradient_box() {
    echo -e "${C_ACCENT3}╭${C_ACCENT2}─${C_ACCENT}─${C_ACCENT2}─${C_ACCENT3}╮${R}"
}

# Color cycling spinner frames (gradient through accent colors)
declare -a SPINNER_FRAMES
SPINNER_FRAMES=(
    "${C_ACCENT}⠋${R}" "${C_ACCENT2}⠙${R}" "${C_LAV}⠹${R}" "${C_BLUE}⠸${R}"
    "${C_TEAL}⠼${R}" "${C_GREEN}⠴${R}" "${C_WARN}⠦${R}" "${C_PEACH}⠧${R}"
    "${C_PINK}⠇${R}" "${C_ACCENT}⠏${R}"
)

# Gradient bar characters: ▁▂▃▄▅▆▇█ (colored by intensity)
gradient_bar_char() {
    local level="$1"  # 0-7
    local chars='▁▂▃▄▅▆▇█'
    local colors=(
        "${C_ACCENT3}" "${C_ACCENT3}" "${C_ACCENT2}" "${C_ACCENT2}"
        "${C_ACCENT}" "${C_ACCENT}" "${C_MAUVE}" "${C_PINK}"
    )
    printf '%b%s%b' "${colors[$level]}" "${chars:$level:1}" "$R"
}

# ── Hyprland-style rounded panel box ────────────────────────────
panel_top() {
    local title="$1" width="${2:-64}"
    local pad=$(( (width - ${#title} - 4) / 2 ))
    [ $pad -lt 0 ] && pad=0
    printf '%b╭%s%s%s╮%b\n' "$C_ACCENT" "$(printf '─%.0s' $(seq 1 $pad))" " ${C_HI}${title}${R}${C_ACCENT} " "$(printf '─%.0s' $(seq 1 $pad))" "$R"
    printf '%b│%b%*s%b│%b\n' "$C_ACCENT" "$R" "$width" " " "$C_ACCENT" "$R"
}
panel_bottom() {
    local width="${1:-64}"
    printf '%b╰%s╯%b\n' "$C_ACCENT" "$(printf '─%.0s' $(seq 1 $width))" "$R"
}

# ── Hyprland-style status pill (rounded segment) ───────────────
status_pill() {
    local label="$1" value="$2" color="$3"
    printf '%b%b %s %b %s %b%b' "$color" "$C_SURFACE" "$label" "$color" "$value" "$color" "$R"
}

# ── Globals ────────────────────────────────────────────────────
LOG_FILE=""; DASHBOARD=0; KV_NAV=0; KILLSWITCH=0
BRIDGE_MODE=0; EXIT_FILTER=""; ISOLATE=0; PROXY_CHAIN="tor"
declare -A LATENCY_HISTORY

# ── Python bridge ──────────────────────────────────────────────
py() {
    PYTHONPATH="$TORN_DIR" python3 -c "
import sys; sys.path.insert(0,'$TORN_DIR')
from tornet.tornet import *
$1
" 2>/dev/null
}

# ── FIGlet / ASCII banner ─────────────────────────────────────
banner() {
    clear 2>/dev/null || true

    # ═══════════════════════════════════════════════════════════════
    #  VUNJA LUTI — Tor Proxy + IP Rotator v4.0
    #  Author : archnexus_707   |   Donations welcome
    # ═══════════════════════════════════════════════════════════════

    echo ""
    echo -e "  ${C_MAUVE}   ██╗   ██╗██╗   ██╗███╗   ██╗      ██╗██╗   ██╗████████╗██╗${R}"
    echo -e "  ${C_MAUVE}   ██║   ██║██║   ██║████╗  ██║      ██║██║   ██║╚══██╔══╝██║${R}"
    echo -e "  ${C_LAV}   ██║   ██║██║   ██║██╔██╗ ██║      ██║██║   ██║   ██║   ██║${R}"
    echo -e "  ${C_LAV}   ╚██╗ ██╔╝██║   ██║██║╚██╗██║      ██║██║   ██║   ██║   ██║${R}"
    echo -e "  ${C_ACCENT}   ╚████╔╝ ╚██████╔╝██║ ╚████║      ██║╚██████╔╝   ██║   ██║${R}"
    echo -e "  ${C_ACCENT}    ╚═══╝   ╚═════╝ ╚═╝  ╚═══╝      ╚═╝ ╚═════╝    ╚═╝   ╚═╝${R}"
    echo ""
    echo -e "  ${C_ACCENT2}       █████╗     ██╗██╗   ██╗████████╗██╗${R}"
    echo -e "  ${C_ACCENT2}      ██╔══██╗    ██║██║   ██║╚══██╔══╝██║${R}"
    echo -e "  ${C_ACCENT3}      ███████║    ██║██║   ██║   ██║   ██║${R}"
    echo -e "  ${C_ACCENT3}      ██╔══██║    ██║██║   ██║   ██║   ██║${R}"
    echo -e "  ${C_PINK}      ██║  ██║    ██║╚██████╔╝   ██║   ██║${R}"
    echo -e "  ${C_PINK}      ╚═╝  ╚═╝    ╚═╝ ╚═════╝    ╚═╝   ╚═╝${R}"
    echo ""

    # ── Subtitle ──────────────────────────────────────────────────
    echo -e "  ${C_HI}V U N J A   L U T I${R}  ${C_DIM}— v4.0${R}"
    echo -e "  ${C_SUBTLE}Tor Proxy  +  IP Rotator${R}"

    # ── Info Bar ───────────────────────────────────────────────────
    local ks_text="disarmed" ks_color="$C_DIM"
    [ "$KILLSWITCH" -eq 1 ] && ks_text="ENGAGED" && ks_color="$C_GOOD"
    local br_text="none" br_color="$C_DIM"
    [ "$BRIDGE_MODE" -eq 1 ] && br_text="obfs4" && br_color="$C_GOOD"

    echo ""
    echo -e "  ${C_ACCENT}┌──────────────────────────────────────────────┐${R}"
    printf "  ${C_ACCENT}│${R}  %-15s %b%-30s%b ${C_ACCENT}│${R}\n" "Theme" "$C_MAUVE" "$THEME" "$R"
    printf "  ${C_ACCENT}│${R}  %-15s %b%-30s%b ${C_ACCENT}│${R}\n" "Killswitch" "$ks_color" "$ks_text" "$R"
    printf "  ${C_ACCENT}│${R}  %-15s %b%-30s%b ${C_ACCENT}│${R}\n" "Bridges" "$br_color" "$br_text" "$R"
    printf "  ${C_ACCENT}│${R}  %-15s %b%-30s%b ${C_ACCENT}│${R}\n" "Exit Nodes" "$C_PEACH" "${EXIT_FILTER:-any}" "$R"
    echo -e "  ${C_ACCENT}└──────────────────────────────────────────────┘${R}"
    echo ""
    echo -e "  ${C_DIM}Author : archnexus_707  |  Donations welcome${R}"
    echo ""
}

# ── Color-cycling output (each line a different accent) ────────
_say_colors=("$C_MAUVE" "$C_LAV" "$C_ACCENT" "$C_ACCENT2" "$C_BLUE" "$C_TEAL" "$C_PINK" "$C_FLAMINGO")
_say_idx=0
say() {
    _say_idx=$(( (_say_idx + 1) % ${#_say_colors[@]} ))
    printf "  %b◆%b  %s\n" "${_say_colors[$_say_idx]}" "$R" "$1"
}

# ── Unicode country flag ──────────────────────────────────────
cc2flag() {
    python3 -c "c='$1'; print(chr(ord(c[0])+127397)+chr(ord(c[1])+127397)) if len(c)==2 else print('??')" 2>/dev/null
}

# ── FIXED: GeoIP routed through Tor ───────────────────────────
geo_flag() {
    local ip="$1" cc
    cc=$(curl -sk --socks5-hostname 127.0.0.1:9050 --connect-timeout 5 \
        "http://ip-api.com/json/$ip" 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('countryCode','??'))" 2>/dev/null)
    if [ -n "$cc" ] && [ "$cc" != "??" ]; then
        printf '%s %s' "$(cc2flag "$cc")" "$cc"
    else
        printf '??'
    fi
}

# ── Latency through Tor (ms) ──────────────────────────────────
latency() {
    local ms=$(curl -sk --connect-timeout 10 --max-time 10 \
        --socks5-hostname 127.0.0.1:9050 \
        -w '%{time_total}' -o /dev/null \
        https://check.torproject.org 2>/dev/null || echo "0")
    printf '%.0f' "$(python3 -c "print(float('$ms')*1000)" 2>/dev/null || echo 0)"
}

quality_icon() {
    local ms="$1"
    [ "$ms" -eq 0 ] 2>/dev/null && { printf '⚫'; return; }
    [ "$ms" -lt 300 ] 2>/dev/null && printf '🟢' && return
    [ "$ms" -lt 800 ] 2>/dev/null && printf '🟡' && return
    printf '🔴'
}

# ── Sound effects ─────────────────────────────────────────────
sound() {
    case "$1" in
        rotate)
            command -v paplay >/dev/null 2>&1 && \
                paplay /usr/share/sounds/freedesktop/stereo/message.oga 2>/dev/null || true ;;
        start)
            command -v paplay >/dev/null 2>&1 && \
                paplay /usr/share/sounds/freedesktop/stereo/service-login.oga 2>/dev/null || true ;;
        stop)
            command -v paplay >/dev/null 2>&1 && \
                paplay /usr/share/sounds/freedesktop/stereo/service-logout.oga 2>/dev/null || true ;;
        alert)
            command -v aplay >/dev/null 2>&1 && \
                aplay /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null || true ;;
    esac
}

notify() {
    command -v notify-send >/dev/null 2>&1 && \
        notify-send -t 4000 "VL v4.0" "$1" 2>/dev/null || true
}

# ── JSON log ──────────────────────────────────────────────────
log_json() {
    local ip="$1" flag="$2" lat="$3" circuit="$4"
    local ts=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    python3 -c "
import json
entry = {'timestamp':'$ts','ip':'$ip','geo':'$flag','latency_ms':$lat,'circuit':'$circuit'}
with open('$LOG_FILE','a') as f: f.write(json.dumps(entry)+'\n')
" 2>/dev/null || true
}

# ── NEW: Bandwidth sparkline ──────────────────────────────────
sparkline() {
    local data="$1" out=""
    local vals=($data)
    if [ ${#vals[@]} -eq 0 ]; then echo ""; return; fi
    local min=${vals[0]} max=${vals[0]}
    for v in "${vals[@]}"; do
        [ "$v" -lt "$min" ] && min=$v
        [ "$v" -gt "$max" ] && max=$v
    done
    local range=$((max - min))
    [ "$range" -eq 0 ] && range=1
    local chars='▁▂▃▄▅▆▇█'
    for v in "${vals[@]}"; do
        local idx=$(( (v - min) * 7 / range ))
        [ "$idx" -gt 7 ] && idx=7
        [ "$idx" -lt 0 ] && idx=0
        out+="${chars:$idx:1}"
    done
    printf '%s' "$out"
}

# ── NEW: Circuit hop visualization ────────────────────────────
show_circuit() {
    echo -e "  ${C_DIM}$(gradient_hop 1) → $(gradient_hop 2) → $(gradient_hop 3) → ${C_GOOD}🌐${R}"
}
gradient_hop() {
    local n="$1"
    case "$n" in
        1) printf '%b🛡 Guard%b' "${C_ACCENT3}$C_BOLD" "$R" ;;
        2) printf '%b🔗 Middle%b' "${C_ACCENT}$C_BOLD" "$R" ;;
        3) printf '%b🚪 Exit%b' "${C_MAUVE}$C_BOLD" "$R" ;;
    esac
}

# ── NEW: Status bar (placeholder, used below) ──────────────────
status_bar() {
    local ip="${1:-???}" flag="${2:-??}" ms="${3:-0}" rots="${4:-0}" upt="${5:-0s}"
    local qi=$(quality_icon "$ms")
    local ks_txt="OFF" ks_col="$C_DIM"
    [ "$KILLSWITCH" -eq 1 ] && ks_txt="ON" && ks_col="$C_GOOD"
    printf "${C_PANE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${R}\n"
    printf "${C_PANE}[VL]${R} %s %s %s ${C_HI}%sms${R} | ${C_PANE}#%s${R} | ${C_PANE}up %s${R} | ${C_PANE}KS %b%s%b${R}\n" \
        "${C_ACCENT}${ip}${R}" "$flag" "$qi" "$ms" "$rots" "$upt" "$ks_col" "$ks_txt" "$R"
    printf "${C_PANE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${R}\n"
}

# ── NEW: Interactive FZF exit node picker ─────────────────────
fzf_exit_picker() {
    local exits=("US" "GB" "DE" "NL" "FR" "SE" "CH" "CA" "JP" "SG" "AU" "BR")
    if command -v fzf >/dev/null 2>&1; then
        local choice=$(printf '%s\n' "${exits[@]}" | fzf --prompt="Pick exit country: " --height=15 2>/dev/null)
        [ -n "$choice" ] && EXIT_FILTER="$choice"
        echo -e "  ${C_GOOD}◆${R} Exit filter set: ${C_ACCENT}${EXIT_FILTER}${R}"
    else
        echo -e "  ${C_WARN}◇${R} fzf not installed — use --exit-filter COUNTRY"
        echo -e "  ${C_DIM}Available: ${exits[*]}${R}"
    fi
}

# ── NEW: Kill switch via iptables ─────────────────────────────
killswitch_on() {
    [ "$EUID" -eq 0 ] || { echo -e "  ${C_BAD}◆ killswitch needs root${R}"; return 1; }
    # Allow Tor user
    iptables -A OUTPUT -m owner --uid-owner debian-tor -j ACCEPT 2>/dev/null || true
    # Allow loopback
    iptables -A OUTPUT -o lo -j ACCEPT 2>/dev/null || true
    # Allow DNS to Tor
    iptables -A OUTPUT -p udp --dport 53 -m owner --uid-owner debian-tor -j ACCEPT 2>/dev/null || true
    # Default drop
    iptables -P OUTPUT DROP 2>/dev/null || true
    KILLSWITCH=1
    say "Killswitch ENGAGED — only Tor traffic allowed"
    sound alert
}

killswitch_off() {
    [ "$EUID" -eq 0 ] || { echo -e "  ${C_BAD}◆ needs root${R}"; return 1; }
    iptables -P OUTPUT ACCEPT 2>/dev/null || true
    iptables -F OUTPUT 2>/dev/null || true
    KILLSWITCH=0
    echo -e "  ${C_WARN}◇ Killswitch DISENGAGED${R}"
}

# ── Per-app proxy toggle ──────────────────────────────────────
proxify() {
    local app="$1"; shift
    case "$app" in
        firefox)
            firefox --proxy-server="socks5://127.0.0.1:9050" "$@" 2>/dev/null &
            say "Firefox proxified through Tor"
            ;;
        chromium|chrome)
            chromium --proxy-server="socks5://127.0.0.1:9050" "$@" 2>/dev/null &
            say "Chromium proxified through Tor"
            ;;
        curl)
            curl --socks5-hostname 127.0.0.1:9050 "$@" 2>/dev/null
            ;;
        nmap)
            proxychains4 nmap -sT -Pn "$@" 2>/dev/null || echo "  ${C_WARN}◇ Install proxychains4 for nmap proxying${R}"
            ;;
        *)
            echo -e "  ${C_WARN}◇ Unknown app: $app. Supported: firefox, chromium, curl, nmap${R}"
            ;;
    esac
}

# ── Gradient progress bar ─────────────────────────────────────
progress_bar() {
    local current=$1 total=$2 label="$3" width=36
    local pct=$((current * 100 / total))
    local filled=$((current * width / total))
    local i
    printf "\r  ${C_ACCENT3}"
    for ((i=0; i<filled; i++)); do
        local idx=$(( i * 7 / width ))
        local chars='▁▂▃▄▅▆▇█'
        printf '%b%s' "${C_ACCENT}" "${chars:$idx:1}"
    done
    for ((i=filled; i<width; i++)); do
        printf '%b%s' "$C_SURFACE" '·'
    done
    printf '%b %3d%% %b%s%b' "$R" "$pct" "$C_SUBTLE" "$label" "$R"
}

# ── Rotation step (gradient styled) ────────────────────────────
rotate_step() {
    local count="$1"
    py "change_ip()"
    sleep 2
    local ip=$(py "print(get_current_ip() or '???')")
    local ts=$(date '+%H:%M:%S')
    local flag=$(geo_flag "$ip")
    local ms=$(latency)
    local qi=$(quality_icon "$ms")

    # Store latency for sparkline
    LATENCY_HISTORY["$count"]=$ms

    printf "  ${C_DIM}%s${R} " "$ts"
    printf "${C_ACCENT}#%s${R}  " "$count"
    printf "${C_HI}%s${R}  " "$ip"
    printf "%s  %s " "$flag" "$qi"
    printf "${C_GOOD}%sms${R}\n" "$ms"

    [ -n "$LOG_FILE" ] && log_json "$ip" "$flag" "$ms" "tor"
    notify "Tor Exit: $ip ($flag) — ${ms}ms"
    sound rotate
}

# ── Show header (Hyprland-style) ───────────────────────────────
show_header() {
    local ip=$(py "print(get_current_ip() or '???')")
    local flag=$(geo_flag "$ip")
    local ms=$(latency)
    local qi=$(quality_icon "$ms")

    echo ""
    echo -e "  ${C_ACCENT}╭─────────────────────────────────────────────────────────╮${R}"
    printf  "  ${C_ACCENT}│${R}  %s " "🌐"
    printf  "${C_HI}Tor LIVE  —  Exit: ${C_BOLD}%s${R}  %s  %s  ${C_GOOD}%sms${R}" "$ip" "$flag" "$qi" "$ms"
    printf  "  ${C_ACCENT}│${R}\n"
    printf  "  ${C_ACCENT}│${R}  %s SOCKS5 -> ${C_BOLD}127.0.0.1:9050${R}" "🔒"
    printf  "     ${C_ACCENT}│${R}\n"
    local bottom=""
    [ -n "$LOG_FILE" ] && bottom="${bottom}  📄 ${LOG_FILE}${R}"
    [ -n "$EXIT_FILTER" ] && bottom="${bottom}  🚩 Exit: ${EXIT_FILTER}${R}"
    [ -n "$bottom" ] && printf "  ${C_ACCENT}│${R}%s  ${C_ACCENT}│${R}\n" "$bottom"
    echo -e "  ${C_ACCENT}╰─────────────────────────────────────────────────────────╯${R}"
    echo ""
    echo -e "  ${C_DIM}⏳ Rotating every ${C_BOLD}${ROTATE_INTERVAL:-60}s${R}${C_DIM}  —  Ctrl+C to quit${R}"
    echo ""
}

# ── Live rotation loop ────────────────────────────────────────
live_loop() {
    local interval="${ROTATE_INTERVAL:-60}"
    local count=0
    while true; do
        sleep "$interval"
        count=$((count + 1))
        rotate_step "$count"
    done
}

# ── Dashboard: 3-panel enhanced ────────────────────────────────
start_dashboard() {
    local session="VL_DASH"
    local self="$(readlink -f "$0")"
    local log="${LOG_FILE:-/tmp/vl_dash_$(date +%s).json}"
    local interval="${ROTATE_INTERVAL:-60}"
    
    tmux kill-session -t "$session" 2>/dev/null || true
    tmux new-session -d -s "$session" -x 130 -y 45
    
    # Top-left: live rotation feed (60%)
    tmux send-keys -t "$session:0.0" \
        "bash \"$self\" _dash_top \"$log\" \"$interval\"" Enter
    
    # Split horizontal: top-right = sparkline + circuit
    tmux split-window -h -t "$session:0.0" -l 45
    tmux send-keys -t "$session:0.1" \
        "bash \"$self\" _dash_info \"$log\"" Enter
    
    # Split vertical: bottom = IP history log
    tmux split-window -v -t "$session:0.0" -l 12
    tmux send-keys -t "$session:0.2" \
        "bash \"$self\" _dash_bottom \"$log\"" Enter
    
    tmux select-pane -t "$session:0.0"
    tmux attach-session -t "$session"
}

cmd_dash_top() {
    LOG_FILE="$1"; ROTATE_INTERVAL="${2:-60}"
    echo -e "${C_ACCENT}╔══════════════════ VL DASHBOARD v4.0 — LIVE ROTATION ══════════════════╗${R}"
    echo -e "${C_ACCENT}║${R}  SOCKS5: ${C_HI}127.0.0.1:9050${R}  ${C_DIM}|${R}  Interval: ${C_HI}${ROTATE_INTERVAL}s${R}  ${C_DIM}|${R}  ${C_ACCENT}$(date '+%H:%M')${R}"
    echo -e "${C_ACCENT}╚══════════════════════════════════════════════════════════════════════╝${R}"
    echo ""
    
    local count=0
    while true; do
        sleep "$ROTATE_INTERVAL"
        count=$((count + 1))
        py "change_ip()"
        sleep 2
        local ip=$(py "print(get_current_ip() or '???')")
        local ts=$(date '+%H:%M:%S')
        local flag=$(geo_flag "$ip")
        local ms=$(latency)
        local qi=$(quality_icon "$ms")
        
        LATENCY_HISTORY["$count"]=$ms
        
        echo -e "  ${C_DIM}[${ts}]${R} ${C_ACCENT}#${count}${R}  ${C_HI}${ip}${R}  ${flag}  ${qi} ${C_HI}${ms}ms${R}"
        
        [ -n "$LOG_FILE" ] && log_json "$ip" "$flag" "$ms" "tor"
        notify "Tor Exit: $ip ($flag) — ${ms}ms"
        sound rotate
    done
}

cmd_dash_info() {
    local log="$1"
    while true; do
        clear
        echo -e "${C_ACCENT}── CIRCUIT MAP ──────────────────────────────────────────────${R}"
        show_circuit
        echo ""
        echo -e "${C_ACCENT}── LATENCY TREND ────────────────────────────────────────────${R}"
        # Sparkline of recent entries from log
        if [ -f "$log" ]; then
            local vals=$(python3 -c "
import json
vals=[]
try:
    with open('$log') as f:
        for line in f.readlines()[-20:]:
            try: vals.append(str(json.loads(line.strip()).get('latency_ms',0)))
            except: pass
    print(' '.join(vals))
" 2>/dev/null)
            if [ -n "$vals" ]; then
                echo -e "  $(sparkline "$vals")"
            else
                echo -e "  ${C_DIM}Waiting for data...${R}"
            fi
        fi
        echo ""
        echo -e "${C_ACCENT}── STATS ───────────────────────────────────────────────────${R}"
        local tor_status="DEAD"
        pgrep -x tor >/dev/null 2>&1 && tor_status="${C_GOOD}RUNNING${R}"
        echo -e "  Tor: ${tor_status}"
        local ip=$(py "print(get_current_ip() or '???')")
        echo -e "  Exit: ${C_HI}${ip}${R}  $(geo_flag "$ip")"
        echo -e "  KS: ${KILLSWITCH:+${C_GOOD}⚡ ON}${KILLSWITCH:-${C_DIM}OFF}${R}  Filter: ${EXIT_FILTER:-any}"
        sleep 3
    done
}

cmd_dash_bottom() {
    local log="$1"
    echo -e "${C_DIM}── IP ROTATION HISTORY ───────────────────────────────────${R}"
    if [ -f "$log" ]; then
        tail -f "$log" 2>/dev/null
    else
        echo -e "  ${C_DIM}Waiting for rotations...${R}"
        # Wait for log file to appear, then tail it
        while [ ! -f "$log" ]; do sleep 2; done
        tail -f "$log" 2>/dev/null
    fi
}

# ── Commands ──────────────────────────────────────────────────
cmd_start() {
    say "Fixing dependencies..."
    py "auto_fix()" &
    local pid=$!; local i=0

    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i+1) % ${#SPINNER_FRAMES[@]} ))
        printf "\r  %b %bWorking...%b" "${SPINNER_FRAMES[$i]}" "$C_SUBTLE" "$R"
        sleep 0.15
    done
    echo ""

    say "Starting Tor service..."
    py "initialize_environment()"

    for i in $(seq 1 12); do
        progress_bar "$i" 12 "Bootstrapping Tor circuits"
        sleep 1
    done
    echo ""

    local interval="${ROTATE_INTERVAL:-60}"
    sound start

    if [ "$DASHBOARD" -eq 1 ]; then
        start_dashboard
    else
        show_header
        live_loop
    fi
}

cmd_stop() {
    say "Stopping Tor services..."
    py "stop_services()"
    [ "$KILLSWITCH" -eq 1 ] && killswitch_off
    sound stop
    say "Tor stopped."
}

cmd_rotate() {
    say "Rotating Tor circuit..."
    local old=$(py "print(get_current_ip() or '???')")
    py "change_ip()"
    sleep 3
    local new=$(py "print(get_current_ip() or '???')")
    local flag=$(geo_flag "$new")
    local ms=$(latency)
    local qi=$(quality_icon "$ms")
    printf "  ${C_DIM}%s${R} ${C_DIM}->${R} ${C_HI}%s${R}  %s  %s  ${C_GOOD}%sms${R}\n" "$old" "$new" "$flag" "$qi" "$ms"
    notify "VL: IP rotated to $new ($flag)"
    sound rotate
}

cmd_stop() {
    py "stop_services()"
    [ "$KILLSWITCH" -eq 1 ] && killswitch_off
    sound stop
    echo -e "  ${C_GOOD}◆${R} Tor stopped."
}

cmd_rotate() {
    local old=$(py "print(get_current_ip() or '???')")
    py "change_ip()"
    sleep 3
    local new=$(py "print(get_current_ip() or '???')")
    local flag=$(geo_flag "$new")
    local ms=$(latency)
    local qi=$(quality_icon "$ms")
    echo -e "  ${C_DIM}${old}${R} ${C_DIM}→${R} ${C_HI}${new}${R}  ${flag}  ${qi} ${C_HI}${ms}ms${R}"
    notify "VL: IP rotated to $new ($flag)"
    sound rotate
}

cmd_status() {
    local ip=$(py "print(get_current_ip() or '???')")
    local flag=$(geo_flag "$ip")
    local ms=$(latency)
    local qi=$(quality_icon "$ms")
    local tor_status
    pgrep -x tor >/dev/null 2>&1 && tor_status="${C_GOOD}🌐  RUNNING${R}" || tor_status="${C_BAD}⛔  DEAD${R}"
    
    banner
    echo ""
    echo -e "  ${C_ACCENT}╭──  STATUS  ──────────────────────────────────────────╮${R}"
    printf  "  ${C_ACCENT}│${R}  Tor:        %b  ${C_ACCENT}│${R}\n" "$tor_status"
    printf  "  ${C_ACCENT}│${R}  Exit IP:    ${C_BOLD}%s${R}  %s  ${C_ACCENT}│${R}\n" "$ip" "$flag"
    printf  "  ${C_ACCENT}│${R}  Latency:    %s  ${C_GOOD}%sms${R}  ${C_ACCENT}│${R}\n" "$qi" "$ms"
    printf  "  ${C_ACCENT}│${R}  SOCKS5:     ${C_TEAL}127.0.0.1:9050${R}  ${C_ACCENT}│${R}\n"
    printf  "  ${C_ACCENT}│${R}  Killswitch: ${KILLSWITCH:+${C_GOOD}⚡ ENGAGED}${KILLSWITCH:-${C_DIM}○ disarmed}${R}  ${C_ACCENT}│${R}\n"
    printf  "  ${C_ACCENT}│${R}  Exit Nodes: ${C_PEACH}${EXIT_FILTER:-any}${R}  ${C_ACCENT}│${R}\n"
    printf  "  ${C_ACCENT}│${R}  Bridges:    ${BRIDGE_MODE:+${C_GOOD}obfs4 active}${BRIDGE_MODE:-${C_DIM}none}${R}  ${C_ACCENT}│${R}\n"
    echo -e "  ${C_ACCENT}╰──────────────────────────────────────────────────────╯${R}"
    echo ""
    show_circuit
    echo ""
}

cmd_anoncheck() {
    local tor=$(py "print(get_current_ip() or '???')")
    # Route through Tor to avoid leaking real IP to ipify.org
    local real=$(curl -sk --socks5-hostname 127.0.0.1:9050 --connect-timeout 5 https://api.ipify.org 2>/dev/null || echo "???")
    echo ""
    echo -e "  Tor Exit: ${C_ACCENT}${tor}${R}  $(geo_flag "$tor")"
    echo -e "  Exit IP:  ${C_DIM}${real}${R}"
    if [ "$tor" != "???" ] && [ "$tor" != "$real" ]; then
        echo -e "  ${C_GOOD}◆ ANONYMOUS${R}"
    else
        echo -e "  ${C_BAD}◆ EXPOSED — Tor may not be working${R}"
    fi
    echo ""
}

# ── NEW: Export reports ───────────────────────────────────────
cmd_export() {
    local log="${1:-$LOG_FILE}"
    [ -z "$log" ] && log="/tmp/vl_dash_"$(date +%s)".json"
    [ ! -f "$log" ] && { echo -e "  ${C_BAD}◆ Log not found: $log${R}"; return 1; }
    
    local out="${2:-vl_report_$(date +%Y%m%d_%H%M%S)}"
    
    # JSON export
    cp "$log" "${out}.json"
    echo -e "  ${C_GOOD}◆${R} JSON exported: ${C_DIM}${out}.json${R}"
    
    # CSV export
    python3 -c "
import json
with open('${out}.json') as f, open('${out}.csv','w') as out:
    out.write('timestamp,ip,geo,latency_ms,circuit\n')
    for line in f:
        try:
            d=json.loads(line.strip())
            out.write(f\"{d['timestamp']},{d['ip']},{d['geo']},{d['latency_ms']},{d.get('circuit','')}\n\")
        except: pass
" 2>/dev/null && echo -e "  ${C_GOOD}◆${R} CSV exported: ${C_DIM}${out}.csv${R}"
    
    echo -e "  ${C_GOOD}◆${R} Reports generated"
}

# ── Usage ─────────────────────────────────────────────────────
usage() {
    echo -e "${C_ACCENT}VL v4.0 — Vunja Luti — Tor Proxy + IP Rotator${R}\n"
    echo "  start [--rotate N] [--log FILE] [--dashboard]  Start Tor + rotate"
    echo "  stop                                              Stop Tor"
    echo "  status                                            Show exit IP + flag + quality"
    echo "  rotate                                            Change IP now"
    echo "  anoncheck                                         Verify anonymity"
    echo ""
    echo "  --killswitch              Enable iptables kill switch (needs root)"
    echo "  --no-killswitch           Disable kill switch"
    echo "  --exit-filter COUNTRY     Restrict exit nodes (US, DE, NL, ...)"
    echo "  --fzf-picker              Interactive exit node picker"
    echo "  --proxify APP [args]      Launch app through Tor (firefox, curl, nmap)"
    echo "  --export [LOG] [OUT]      Export rotation log to JSON + CSV"
    echo "  --theme THEME             cyberpunk | matrix | midnight | minimal"
    echo "  --sound-on|--sound-off    Toggle sound effects"
    echo "  --help                    This message"
    exit 0
}

# ── Main ──────────────────────────────────────────────────────
ROTATE_INTERVAL="60"
# Parse flags
for i in $(seq 1 $#); do
    arg="${!i}"; next_i=$((i+1))
    case "$arg" in
        --rotate)       j=$next_i; ROTATE_INTERVAL="${!j}" ;;
        --log)          j=$next_i; LOG_FILE="${!j}" ;;
        --dashboard)    DASHBOARD=1 ;;
        --killswitch)   KILLSWITCH=1 ;;
        --no-killswitch) KILLSWITCH=0 ;;
        --exit-filter)  j=$next_i; EXIT_FILTER="${!j}" ;;
        --fzf-picker)   fzf_exit_picker ;;
        --theme)        j=$next_i; THEME="${!j}"; apply_theme ;;
        --proxify)      j=$next_i; proxify "${!j}" "${@:$((j+1))}"; exit 0 ;;
        --export)       j=$next_i; k=$((i+2)); cmd_export "${!j}" "${!k}"; exit 0 ;;
    esac
done

# Apply exit filter if set
[ -n "$EXIT_FILTER" ] && export TOR_EXIT_NODES="{$EXIT_FILTER}"

banner
CMD="${1:-start}"
case "$CMD" in
    start|stop|status|rotate|anoncheck) "cmd_$CMD" ;;
    _dash_top)   cmd_dash_top "$2" "$3" ;;
    _dash_info)  cmd_dash_info "$2" ;;
    _dash_bottom) cmd_dash_bottom "$2" ;;
    help|-h|--help) usage ;;
    "")           cmd_start ;;
    *)            usage ;;
esac
