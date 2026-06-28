# VUNJA LUTI — Go (CLI + Wails GUI)

A Go port of VUNJA LUTI with a shared engine, a single-binary **CLI**, and a neon
**Wails GUI** (Go backend + web frontend). Built for **zero lag** — the CLI is
native and instant, and every GUI Tor/network call runs on a goroutine so the UI
never blocks.

```
go/
├── internal/core/   shared engine (Tor control, SOCKS5, geo, torrc, wrap) — stdlib only
├── cmd/vl/          the CLI  → static binary, no deps
├── app.go main.go   the Wails GUI backend (bound methods, events)
├── frontend/dist/   neon web UI (index.html, style.css, main.js) — no build step
├── wails.json       Wails project config
├── build-gui.sh     one-command GUI build (installs deps + wails, runs wails build)
└── go.mod
```

Interoperable with the Python build and with each other: all three share
`~/.config/vl/config.json` (incl. the control password) and the
`# VUNJA-LUTI managed block` in `/etc/tor/torrc`.

## CLI

```bash
cd go
CGO_ENABLED=0 go build -ldflags "-s -w" -o vl ./cmd/vl   # ~5 MB static, zero deps
./vl status            # ~5 ms — no lag
./vl doctor --fix      # enable password-auth control port
./vl rotate
```

Commands: `status · rotate · anoncheck · doctor [--fix] · reset · version`.

## GUI (Wails)

Linux needs the webkit2gtk + gtk3 dev libraries and the Wails CLI. The script does
it all:

```bash
cd go
./build-gui.sh        # installs libwebkit2gtk-4.1-dev + libgtk-3-dev + wails, then builds
./build/bin/vunja-luti-gui
```

Manual equivalent:
```bash
sudo apt install build-essential pkg-config libgtk-3-dev libwebkit2gtk-4.1-dev
go install github.com/wailsapp/wails/v2/cmd/wails@latest
wails build && ./build/bin/vunja-luti-gui
```

### GUI features
Live status card · animated **circuit map** with country flags · latency
sparkline (canvas) · live rotation feed · **auto-rotate** · **Toolbox** (run
hydra/ffuf/sqlmap/… through Tor, output streamed live) · exit-country filter ·
**doctor** (one-click control-port setup) · `reset` · 5 live-switchable neon themes.

### No-lag design
- backend methods are bound and each runs on its own goroutine
- status polls every 4 s asynchronously; the UI thread only paints
- rotations + tool output arrive as **events** (`rotated`, `tool:line`) — no blocking calls

## Why Go over the Python build (for distribution)

| | Python | Go |
|---|---|---|
| CLI install | `.deb` + python3-stem/requests/socks/pyqt6 | one static file |
| `vl status` | hundreds of ms | **~5 ms** |
| GUI | PyQt6 | Wails (web UI, smaller, snappy) |
| Runtime deps | several | CLI: none · GUI: webkit (system lib) |
