<p align="center">
  <img src="assets/neon_realm.webp" alt="Vunja Luti — Neon Realm" width="100%">
</p>

<h1 align="center">
  <img src="assets/icon.png" width="34" align="top" alt=""> &nbsp;VUNJA LUTI <code>v6.0</code>
</h1>

<h3 align="center">Tor Proxy · IP Rotator · Tool Wrapper — now with a neon GUI &amp; a one-click <code>.deb</code></h3>

<p align="center">
  <img src="https://img.shields.io/badge/version-6.0.1-ff2a6d?style=flat-square">
  <img src="https://img.shields.io/badge/platform-Kali%20%2F%20Debian-05d9e8?style=flat-square">
  <img src="https://img.shields.io/badge/interface-CLI%20%2B%20GUI-d300c5?style=flat-square">
  <img src="https://img.shields.io/badge/engine-stem%20(Tor%20control)-39ff14?style=flat-square">
  <img src="https://img.shields.io/badge/license-Ethical%20Use%20Only-ff003c?style=flat-square">
</p>

---

## 🧠 What is it?

**Vunja Luti** *(Swahili: “break the web”)* routes your traffic through Tor's SOCKS5
proxy, **rotates the exit IP** on a schedule using Tor's control protocol, **wraps any
command** through `proxychains`, and enforces **kill-switch** and **leak-guard** policies.

Version 6 is a full rebuild: a single Python engine now powers both a **themed CLI** and a
**neon PyQt6 desktop app**, packaged as an installable **`.deb`**.

<p align="center">
  <img src="assets/screenshot-gui.png" alt="Vunja Luti GUI — Dashboard" width="92%">
</p>

---

## ✨ Highlights

| | |
|---|---|
| 🖥️ **Desktop GUI** | Live status, animated **circuit map** with country flags, latency sparkline, live rotation feed, system-tray controls + notifications. |
| ⌨️ **Themed CLI** | `vl start / status / rotate / wrap / toolbox / monitor / doctor`, 9 colour themes, truecolour output. |
| 🔁 **Real rotation** | Identity changes via the Tor **control port** (`stem`) — deterministic, not screen-scraping. |
| 🧰 **Tool wrapper** | Push hydra / ffuf / gobuster / sqlmap / nmap / nikto / wpscan / curl through Tor, with auto IP rotation. |
| 🛡️ **Kill-switch** | iptables egress lock with **full backup/restore** — never nukes your existing rules. |
| 🚱 **Leak-guard** | Disables IPv6 + routes DNS through Tor to stop DNS/IPv6 leaks. |
| 🌍 **Exit filter** | Pin exit countries (`us,nl,de`) using **valid** Tor syntax. |
| 🩺 **Doctor** | One command checks the whole stack and auto-enables the Tor control port. |
| 📦 **.deb package** | `apt`-installable, app-menu entry, crisp neon icon, real `vl` / `vunja-luti-gui` commands. |

---

## 🚀 Install (recommended — `.deb`)

Download the latest `vunja-luti_6.0.1_all.deb` from the
[**Releases**](https://github.com/archnexus707/VUNJA-LUTI/releases) page, then:

```bash
sudo apt install ./vunja-luti_6.0.1_all.deb
vl doctor --fix      # enable Tor control port (one time)
```

That's it. Launch the GUI from your app menu (**Vunja Luti**) or run:

```bash
vunja-luti-gui       # GUI
vl start             # CLI rotation loop
```

---

## 🖼️ Gallery

<p align="center">
  <img src="assets/screenshot-toolbox.png" width="48%" alt="Toolbox tab">
  &nbsp;
  <img src="assets/screenshot-tokyo.png" width="48%" alt="Tokyo Night theme">
</p>
<p align="center">
  <img src="assets/ghost_proxy.png" width="45%" alt="Ghost Proxy">
  &nbsp;&nbsp;
  <img src="assets/dark_circuit.png" width="45%" alt="Dark Circuit">
</p>

---

## ⌨️ CLI usage

```bash
vl start                       # start Tor + rotate IPs on a loop
vl status                      # exit IP, country flag, latency, circuit
vl rotate                      # force one new identity now
vl anoncheck                   # confirm exit IP ≠ real IP
vl monitor                     # live circuit-health watch + auto-recovery
vl --theme matrix status       # any of 9 themes

# route any tool through Tor (quotes & flags are preserved safely)
vl --rotate 30 wrap -- sqlmap -u 'http://target/page?id=1' --batch
vl wrap -- nmap -sT -Pn -p 80,443 target.com

# security
sudo vl --killswitch start         # block all non-Tor egress (auto-restored on stop)
sudo vl --leak-guard start         # disable IPv6 + DNS-through-Tor
vl --exit-filter us,nl,de status   # pin exit countries
vl reset                           # revert every torrc / firewall change VL made

vl doctor --fix                    # diagnose + auto-enable control port
vl toolbox                         # interactive tool picker
```

---

## 🎨 Themes

`catppuccin` · `tokyo-night` · `nord` · `everforest` · `rose-pine` · `dracula` ·
`gruvbox` · `cyberpunk` *(default)* · `matrix`

Switch live from the GUI header, or `vl --theme <name> …` on the CLI.

---

## 🧩 How rotation works

```
┌──────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────┐
│ Your tool│──▶│ proxychains4 │──▶│  Tor SOCKS5  │──▶│ Target │
│ (sqlmap) │   │ (auto-config)│   │ 127.0.0.1:   │   │        │
└──────────┘   └──────────────┘   │     9050     │   └────────┘
                                  └──────┬───────┘
              NEWNYM via control port ◀──┘  every N seconds
              → fresh exit IP, IDS sees only Tor exits
```

---

## 🛠️ Build from source

```bash
git clone https://github.com/archnexus707/VUNJA-LUTI.git
cd VUNJA-LUTI

# build the .deb (no debhelper needed; uses dpkg-deb)
bash packaging/build-deb.sh
sudo apt install ./dist/vunja-luti_6.0.1_all.deb

# …or run straight from the tree
pip install -e .
vl status
```

**Dependencies** (pulled in by the `.deb`): `python3-stem`, `python3-requests`,
`python3-socks`, `tor`; recommends `python3-pyqt6`, `proxychains4`,
`fonts-noto-color-emoji`, `fonts-jetbrains-mono`.

---

## ⚠️ Troubleshooting

| Problem | Fix |
|---|---|
| Rotation does nothing | `vl doctor --fix` — enables Tor's control port |
| GUI won't launch | `sudo apt install python3-pyqt6` |
| `proxychains4 not found` | `sudo apt install proxychains4` |
| Flags show as letters | install `fonts-noto-color-emoji`, restart the app |
| Killswitch locked me out | `vl reset` (restores the iptables snapshot) |
| No exit IP after start | wait ~15 s for Tor to bootstrap |

---

## 🗂️ Project layout

```
vunjaluti/
├── core/      engine·geo·firewall·torrc·wrap·sessions·doctor·config
├── cli/       vl / vunja-luti  (argparse, themed)
├── gui/       PyQt6 app · widgets · workers · neon QSS
└── resources/ icons + fonts
packaging/     build-deb.sh · make_icon.py · vunja-luti.desktop
legacy/        the original Vunja_Luti.sh (kept for reference)
```

---

## 👤 Author

**archnexus707** — offensive-security researcher & privacy advocate.
☕ Support: `archnexus707@gmail.com`

## 📜 License

**Ethical use only** — authorised testing and privacy protection. Not for illegal activity.

<p align="center"><sub>Made with ⚡ on Kali Linux by archnexus707</sub></p>
