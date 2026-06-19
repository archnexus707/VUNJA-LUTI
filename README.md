<p align="center">
  <img src="assets/neon_realm.webp" alt="Neon Realm — Animated 4K Cyberpunk" width="100%">
</p>

<h1 align="center">⚡ VUNJA LUTI v5.0 ⚡</h1>
<h3 align="center">Tor Proxy + IP Rotator + Tool Wrapper</h3>

<p align="center">
  <img src="https://img.shields.io/badge/version-5.0-mauve?style=flat-square">
  <img src="https://img.shields.io/badge/platform-Kali%20Linux-blue?style=flat-square">
  <img src="https://img.shields.io/badge/features-10%20new-green?style=flat-square">
  <img src="https://img.shields.io/badge/license-Ethical%20Use%20Only-red?style=flat-square">
  <img src="https://img.shields.io/badge/author-archnexus__707-orange?style=flat-square">
</p>

<p align="center">
  <img src="assets/ghost_proxy.png" width="45%" alt="Ghost Proxy — Terminal + Hood">
  &nbsp;&nbsp;
  <img src="assets/dark_circuit.png" width="45%" alt="Dark Circuit — Tor Network">
</p>

---

## 🧠 What Is It?

**Vunja Luti** *(Swahili: "break the web")* is an advanced Tor SOCKS5 proxy manager that rotates your IP address, wraps offensive security tools through Tor, enforces killswitch policies, guards against DNS/IPv6 leaks, and provides an interactive toolbox for penetration testing — all invisible to IDS/firewalls.

```
   ██╗   ██╗██╗   ██╗███╗   ██╗      ██╗██╗   ██╗████████╗██╗
   ██║   ██║██║   ██║████╗  ██║      ██║██║   ██║╚══██╔══╝██║
   ██║   ██║██║   ██║██╔██╗ ██║      ██║██║   ██║   ██║   ██║
   ╚██╗ ██╔╝██║   ██║██║╚██╗██║      ██║██║   ██║   ██║   ██║
   ╚████╔╝ ╚██████╔╝██║ ╚████║      ██║╚██████╔╝   ██║   ██║
    ╚═══╝   ╚═════╝ ╚═╝  ╚═══╝      ╚═╝ ╚═════╝    ╚═╝   ╚═╝
```

---

## 🔥 v5.0 — 10 New Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | `--wrap "CMD"` | Route **ANY** command through Tor (hydra, ffuf, sqlmap, nmap, gobuster) |
| 2 | `--autochain` | Auto-generate/install `proxychains4.conf` for Tor routing |
| 3 | `--help` | Full **nmap-style** man page with usage examples for every scenario |
| 4 | `--rotate-on N` | Rotate IP every **N requests** (not just time-based) |
| 5 | `--leak-guard` | Block DNS + IPv6 leaks at **kernel level** (iptables) |
| 6 | `--stealth` | Anti-fingerprinting: randomize timing, rotate entry guards |
| 7 | `--session NAME` | Save/resume named sessions with rotation stats |
| 8 | `--toolbox` | **Interactive menu**: pick tool + auto-configure and execute |
| 9 | `--monitor` | Real-time circuit health monitor + **auto-recovery** on dead circuits |
| 10 | `--multi-hop N` | Chain **N Tor circuits** for deeper anonymity |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/archnexus707/VUNJA-LUTI.git
cd VUNJA-LUTI

# 2. Install dependencies
chmod +x setup.sh && ./setup.sh

# 3. Start Tor + rotation
./Vunja_Luti.sh start

# 4. (Optional) Use alias after setup
vl start
```

---

## 🔑 Tool Integration (The Main Feature)

Route **any** offensive security tool through Tor with automatic IP rotation:

```bash
# Brute force SSH (IP rotates every 60s automatically)
vl --wrap "hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://10.10.10.1"

# Directory fuzzing through Tor
vl --wrap "ffuf -u http://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt"

# Gobuster with 15s rotation
vl --rotate 15 --wrap "gobuster dir -u http://target.com -w wordlist.txt"

# SQLMap through Tor
vl --wrap "sqlmap -u 'http://target.com/page?id=1' --batch"

# Nmap port scan (TCP connect only — works through Tor)
vl --wrap "nmap -sT -Pn -p 80,443,8080 target.com"

# WPScan WordPress scanner
vl --wrap "wpscan --url http://target.com --random-user-agent"

# Nikto web scanner
vl --wrap "nikto -h http://target.com"
```

### How It Works

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌────────┐
│ Your Tool│────→│ proxychains4 │────→│ Tor SOCKS5  │────→│ Target │
│ (hydra)  │     │ (auto-config)│     │ 127.0.0.1:  │     │        │
└──────────┘     └──────────────┘     │    9050     │     └────────┘
                                      └──────┬──────┘
                                             │ IP rotates every Ns
                                             ▼
                                      IDS/Firewall sees
                                      ONLY Tor exit IPs
```

---

## 🎮 Interactive Toolbox

```bash
vl --toolbox
```

Interactive menu to select and configure tools:

```
  ╭─── VUNJA LUTI TOOLBOX ────────────────────────╮
  │                                               │
  │  1  🔑 Hydra (password brute force)           │
  │  2  📂 FFuf (directory/vhost fuzzing)         │
  │  3  📂 Gobuster (directory brute force)       │
  │  4  🗄️  SQLMap (SQL injection)                 │
  │  5  🌐 Nmap (port scan via Tor)               │
  │  6  🕷️  Nikto (web vulnerability scanner)      │
  │  7  🔗 Curl (anonymous HTTP requests)         │
  │  8  🛡️  WPScan (WordPress scanner)             │
  │  9  ⚡ Custom command                         │
  │                                               │
  ╰───────────────────────────────────────────────╯
```

---

## 🛡️ Security Features

### Killswitch (blocks ALL non-Tor traffic)

```bash
sudo vl start --killswitch
```

### Leak Guard (DNS + IPv6 protection)

```bash
sudo vl start --leak-guard
```

### Full Stealth Mode

```bash
sudo vl start --killswitch --leak-guard --stealth --exit-filter US,NL,DE
```

### Multi-Hop (chain Tor circuits)

```bash
vl --multi-hop 3 --wrap "curl http://target.com"
```

---

## 📸 Screenshot

<p align="center">
  <img src="assets/screenshot.png" alt="Vunja Luti Terminal" width="85%">
</p>

---

## 🎮 All Commands

| Command | Description |
|---------|-------------|
| `start` | Start Tor + begin rotating IPs |
| `stop` | Stop Tor service |
| `status` | Show exit IP, country flag, latency, killswitch status |
| `rotate` | Force a single IP rotation now |
| `anoncheck` | Verify anonymity + DNS leak test |
| `sessions` | List saved sessions |

---

## ⚙️ All Flags

### Tool Integration

| Flag | Description |
|------|-------------|
| `--wrap "CMD"` | Execute any command through Tor with IP rotation |
| `--autochain` | Generate/install proxychains4 config |
| `--toolbox` | Interactive tool selector menu |
| `--proxify APP` | Launch specific app through Tor (firefox, chromium, curl, nmap) |

### Security

| Flag | Description |
|------|-------------|
| `--killswitch` | Block ALL non-Tor traffic (iptables, needs root) |
| `--leak-guard` | Enable DNS + IPv6 leak protection |
| `--stealth` | Anti-fingerprinting mode (jitter + guard rotation) |
| `--multi-hop N` | Chain N Tor circuits for deeper anonymity |

### Rotation

| Flag | Description |
|------|-------------|
| `--rotate N` | IP rotation interval in seconds (default: 60) |
| `--rotate-on N` | Rotate IP every N requests |
| `--exit-filter CC` | Restrict exit nodes: `US`, `DE`, `NL`, `FR`, `JP`... |
| `--fzf-picker` | Interactive exit country selector |

### Session & Logging

| Flag | Description |
|------|-------------|
| `--session NAME` | Save/resume named session with stats |
| `--log FILE` | Save rotation history as JSON |
| `--export LOG OUT` | Export rotation log to JSON + CSV report |
| `--monitor` | Real-time circuit health monitor + auto-recovery |

### Display

| Flag | Description |
|------|-------------|
| `--dashboard` | 3-pane tmux dashboard (live feed + circuit + log) |
| `--theme NAME` | Color theme (see below) |
| `--help` | Full reference manual with examples |

---

## 🎨 Themes

```bash
vl --theme <name> start
```

| Theme | Vibe |
|-------|------|
| `catppuccin` | Mauve + lavender pastel *(default)* |
| `tokyo-night` | Deep blue/purple night |
| `nord` | Frost blue, cold & clean |
| `everforest` | Forest green, earthy |
| `rose-pine` | Rose gold + pink |
| `dracula` | Classic purple dark |
| `gruvbox` | Retro warm tones |
| `cyberpunk` | Neon pink + cyan |
| `matrix` | Full green terminal |

---

## 📟 Dashboard

```bash
vl --dashboard start
```

3-pane tmux layout with live rotation feed, circuit map, latency sparklines, and history log.

---

## 📋 Full Help

```bash
vl --help
```

Displays a complete **nmap-style** reference manual with:
- All commands and flags
- Usage examples for every scenario
- Tool integration examples (hydra, ffuf, nmap, sqlmap, gobuster)
- Exit country codes
- Security recommendations

---

## 📂 Requirements

All installed automatically by `setup.sh`:

| Package | Purpose |
|---------|---------|
| `tor` | SOCKS5 proxy daemon |
| `proxychains4` | Route tools through Tor |
| `curl` | HTTP requests + anonymity checks |
| `tmux` | Dashboard layout |
| `fzf` | Interactive selectors |
| `toilet` / `figlet` | ASCII banners |
| `python3` + `requests[socks]` | tornet IP rotation engine |

---

## 🧩 Directory Structure

```
VUNJA-LUTI/
├── Vunja_Luti.sh       ← Main script (1320 lines, 10 features)
├── setup.sh            ← One-shot dependency installer
├── README.md           ← This file
├── assets/             ← Images
├── tornet/             ← Auto-cloned by setup.sh (git-ignored)
└── .gitignore
```

---

## ⚠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `tornet module not found` | Run `./setup.sh` or `git clone https://github.com/ayadseghairi/tornet.git tornet` |
| Tor not running | `sudo systemctl start tor` |
| `--wrap` says "rotation disabled" | Start Tor first: `sudo systemctl start tor` |
| No exit IP after start | Wait 15s for Tor bootstrap |
| Icons broken | Install Nerd Font via `setup.sh`, restart terminal |
| Killswitch/leak-guard needs root | Run with `sudo` |
| proxychains4 not found | `sudo apt install proxychains4` |

---

## 👤 Author

**archnexus707** — solo developer, privacy advocate, offensive security researcher.

## ☕ Support

If Vunja Luti keeps you invisible, consider buying me a coffee:

[![](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-archnexus707@gmail.com-yellow?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](mailto:archnexus707@gmail.com)

---

## 📜 License

Ethical use only. Authorized testing and privacy protection. Not for illegal activity.

<p align="center">
  <sub>Made with ❤️ on Kali Linux by archnexus707</sub>
</p>
