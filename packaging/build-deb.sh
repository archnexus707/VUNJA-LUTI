#!/usr/bin/env bash
#==============================================================================
#  VUNJA LUTI — .deb builder (self-contained, no debhelper required)
#  Stages a package tree and builds with dpkg-deb. Renders the SVG icon to the
#  standard hicolor PNG sizes when a converter is available.
#==============================================================================
set -euo pipefail

VERSION="${VERSION:-6.0.0}"
ARCH="all"
PKG="vunja-luti"
HERE="$(cd "$(dirname "$0")/.." && pwd)"          # repo root
BUILD="${HERE}/build"
ROOT="${BUILD}/${PKG}_${VERSION}"
OUT="${HERE}/dist"

echo "[*] Cleaning build tree"
rm -rf "$ROOT"
mkdir -p "$OUT" \
  "$ROOT/DEBIAN" \
  "$ROOT/usr/bin" \
  "$ROOT/usr/lib/python3/dist-packages/vunjaluti" \
  "$ROOT/usr/share/applications" \
  "$ROOT/usr/share/icons/hicolor/scalable/apps" \
  "$ROOT/usr/share/doc/${PKG}"

echo "[*] Installing Python package"
cp -r "$HERE/vunjaluti/." "$ROOT/usr/lib/python3/dist-packages/vunjaluti/"
# drop caches
find "$ROOT/usr/lib/python3/dist-packages/vunjaluti" -name '__pycache__' -type d -prune -exec rm -rf {} +

echo "[*] Creating launchers"
cat > "$ROOT/usr/bin/vl" <<'EOF'
#!/usr/bin/env python3
from vunjaluti.cli.main import main
import sys
sys.exit(main())
EOF
cp "$ROOT/usr/bin/vl" "$ROOT/usr/bin/vunja-luti"
cat > "$ROOT/usr/bin/vunja-luti-gui" <<'EOF'
#!/usr/bin/env python3
from vunjaluti.gui.app import main
import sys
sys.exit(main())
EOF
chmod 755 "$ROOT/usr/bin/vl" "$ROOT/usr/bin/vunja-luti" "$ROOT/usr/bin/vunja-luti-gui"

echo "[*] Desktop entry + icon"
cp "$HERE/packaging/vunja-luti.desktop" "$ROOT/usr/share/applications/"
SVG="$HERE/vunjaluti/resources/icons/vunja-luti.svg"
cp "$SVG" "$ROOT/usr/share/icons/hicolor/scalable/apps/vunja-luti.svg"

# Preferred: render crisp neon PNGs with the QPainter generator (PyQt6).
ICONS="${BUILD}/icons"
if QT_QPA_PLATFORM=offscreen python3 "$HERE/packaging/make_icon.py" "$ICONS" \
       >/dev/null 2>&1 && [ -f "$ICONS/vunja-luti-128.png" ]; then
  for s in 16 24 32 48 64 128 256 512; do
    dest="$ROOT/usr/share/icons/hicolor/${s}x${s}/apps/vunja-luti.png"
    mkdir -p "$(dirname "$dest")"
    cp "$ICONS/vunja-luti-${s}.png" "$dest" && echo "    icon ${s}px"
  done
  # master PNG bundled with the package (GUI tray + docs)
  cp "$ICONS/vunja-luti-256.png" \
     "$ROOT/usr/lib/python3/dist-packages/vunjaluti/resources/icons/vunja-luti.png"
else
  echo "    [!] PyQt6 icon generator unavailable — falling back to convert/SVG"
  for s in 32 48 64 128 256; do
    dest="$ROOT/usr/share/icons/hicolor/${s}x${s}/apps/vunja-luti.png"
    mkdir -p "$(dirname "$dest")"
    command -v convert >/dev/null 2>&1 && \
      convert -background none -resize "${s}x${s}" "$SVG" "$dest" && echo "    icon ${s}px (convert)"
  done
fi

echo "[*] Docs"
cp "$HERE/README.md" "$ROOT/usr/share/doc/${PKG}/README.md" 2>/dev/null || true
cp "$HERE/legacy/Vunja_Luti.sh" "$ROOT/usr/share/doc/${PKG}/Vunja_Luti.legacy.sh" 2>/dev/null || true

echo "[*] Control files"
INSTALLED_KB=$(du -ks "$ROOT/usr" | cut -f1)
cat > "$ROOT/DEBIAN/control" <<EOF
Package: ${PKG}
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.9), python3-stem, python3-requests, python3-socks, tor
Recommends: python3-pyqt6, proxychains4, fonts-noto-color-emoji, fonts-jetbrains-mono
Suggests: tmux, fzf
Installed-Size: ${INSTALLED_KB}
Maintainer: archnexus707 <archnexus707@gmail.com>
Homepage: https://github.com/archnexus707/VUNJA-LUTI
Description: Tor proxy, IP rotator and offensive-tool wrapper (CLI + GUI)
 Vunja Luti routes traffic through Tor's SOCKS5 proxy, rotates the exit IP on a
 schedule via the Tor control protocol, wraps any command through proxychains,
 and enforces kill-switch / leak-guard policies. Ships a neon PyQt6 desktop app
 and a themed command-line interface that share one engine.
 .
 For authorised security testing and privacy protection only.
EOF

cat > "$ROOT/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
# refresh desktop + icon caches
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
# enable tor so SOCKS is available
if command -v systemctl >/dev/null 2>&1; then
    systemctl enable tor >/dev/null 2>&1 || true
fi
echo "Vunja Luti installed. Run 'vl doctor --fix' once to enable Tor rotation."
exit 0
EOF

cat > "$ROOT/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
exit 0
EOF
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/postrm"

echo "[*] Building package"
DEB="${OUT}/${PKG}_${VERSION}_${ARCH}.deb"
if command -v fakeroot >/dev/null 2>&1; then
    fakeroot dpkg-deb --build --root-owner-group "$ROOT" "$DEB"
else
    dpkg-deb --build --root-owner-group "$ROOT" "$DEB"
fi

echo "[✓] Built: $DEB"
dpkg-deb --info "$DEB" | sed 's/^/    /'
