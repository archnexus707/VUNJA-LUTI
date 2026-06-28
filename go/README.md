# VUNJA LUTI — Go proof-of-concept

A **single static binary** (no Python, no runtime deps) that does the core of VL:
Tor control + IP rotation, talking the Tor control protocol directly with password
auth. Built **stdlib-only** — the SOCKS5 client and control-protocol client are
hand-rolled, so `go build` produces one ~5 MB executable that runs anywhere.

It deliberately **shares state with the Python build**:
- reads/writes the same `~/.config/vl/config.json` (incl. the control password)
- manages the same `# >>> VUNJA-LUTI managed block >>>` fence in `/etc/tor/torrc`

So `vl doctor --fix` from either tool sets up the other.

## Build

```bash
cd go
CGO_ENABLED=0 go build -ldflags "-s -w" -o vl .
./vl status
```

Cross-compile (e.g. for an ARM box) — still one static file:
```bash
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o vl-arm64 .
```

## Commands

```
vl status            exit IP, country, latency, control state   (~5 ms, no lag)
vl rotate            new Tor identity (needs `vl doctor --fix`)
vl anoncheck         exit IP vs real IP
vl doctor [--fix]    diagnose; --fix enables password-auth control port
vl reset             remove VL's torrc managed block
vl version
```

## Why this over Python (for distribution)

| | Python build | Go PoC |
|---|---|---|
| Install | `.deb` pulls `python3-stem`, `requests`, `socks`, `pyqt6`… | one file, `chmod +x`, done |
| Startup | interpreter + imports | instant (native) |
| `vl status` | ~hundreds of ms | **~5 ms** |
| Deps to break | several | none |

## Next step: GUI

The plan is a **Wails** app (Go backend + web frontend) — the neon look in
HTML/CSS/JS, with every Tor/network call in a goroutine so the UI **never blocks**.
This `main.go` logic becomes the Wails bound backend.
