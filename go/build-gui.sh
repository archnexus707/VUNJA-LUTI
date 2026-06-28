#!/usr/bin/env bash
#==============================================================================
#  Build the VUNJA LUTI Wails GUI (Go backend + neon web frontend).
#  Linux: needs webkit2gtk + gtk3 dev libs and the Wails CLI.
#==============================================================================
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

echo "[*] Checking GUI build prerequisites…"

# 1. webkit2gtk + gtk dev libraries (one-time, needs sudo)
need_apt=0
for pc in gtk+-3.0 webkit2gtk-4.1; do
  pkg-config --exists "$pc" 2>/dev/null || need_apt=1
done
if [ "$need_apt" = 1 ]; then
  echo "    Installing webkit2gtk + gtk3 dev libs (sudo)…"
  sudo apt-get update -qq
  sudo apt-get install -y build-essential pkg-config libgtk-3-dev libwebkit2gtk-4.1-dev \
    || sudo apt-get install -y build-essential pkg-config libgtk-3-dev libwebkit2gtk-4.0-dev
fi

# 2. Wails CLI
if ! command -v wails >/dev/null 2>&1; then
  echo "    Installing Wails CLI…"
  go install github.com/wailsapp/wails/v2/cmd/wails@latest
  export PATH="$PATH:$(go env GOPATH)/bin"
fi

echo "[*] wails doctor:"
wails doctor || true

echo "[*] Building GUI…"
# Modern distros ship webkit2gtk-4.1 → needs the webkit2_41 build tag.
if pkg-config --exists webkit2gtk-4.1 2>/dev/null; then
  wails build -clean -tags webkit2_41
else
  wails build -clean
fi

echo "[✓] Built: $HERE/build/bin/vunja-luti-gui"
echo "    Run it:  ./build/bin/vunja-luti-gui"
echo "    (first run: vl doctor --fix  — enables Tor control port for rotation)"
