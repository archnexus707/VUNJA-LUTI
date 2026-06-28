"""Shared colour palettes for the CLI (ANSI/truecolour) and GUI (hex/QSS).

Ported from the original bash theme engine. Each palette is a dict of semantic
colour roles expressed as ``#rrggbb`` hex. The CLI converts these to truecolour
ANSI escapes on demand; the GUI feeds them straight into a QSS template.
"""

from __future__ import annotations

# role keys every palette must define
ROLES = (
    "base", "surface", "overlay", "text", "subtext",
    "accent", "accent2", "accent3", "good", "warn", "bad",
    "info", "mauve", "lavender", "blue", "teal", "pink", "peach",
)

PALETTES: dict[str, dict[str, str]] = {
    "catppuccin": {
        "base": "#1e1e2e", "surface": "#313244", "overlay": "#45475a",
        "text": "#cdd6f4", "subtext": "#a6adc8", "accent": "#cba6f7",
        "accent2": "#b4befe", "accent3": "#89b4fa", "good": "#a6e3a1",
        "warn": "#f9e2af", "bad": "#f38ba8", "info": "#94e2d5",
        "mauve": "#cba6f7", "lavender": "#b4befe", "blue": "#89b4fa",
        "teal": "#94e2d5", "pink": "#f5c2e7", "peach": "#fab387",
    },
    "tokyo-night": {
        "base": "#1a1b26", "surface": "#24283b", "overlay": "#414868",
        "text": "#c0caf5", "subtext": "#9aa5ce", "accent": "#bb9af7",
        "accent2": "#7aa2f7", "accent3": "#7dcfff", "good": "#9ece6a",
        "warn": "#e0af68", "bad": "#f7768e", "info": "#73daca",
        "mauve": "#bb9af7", "lavender": "#7aa2f7", "blue": "#7dcfff",
        "teal": "#73daca", "pink": "#ff75a0", "peach": "#ff9e64",
    },
    "nord": {
        "base": "#2e3440", "surface": "#3b4252", "overlay": "#434c5e",
        "text": "#eceff4", "subtext": "#d8dee9", "accent": "#88c0d0",
        "accent2": "#81a1c1", "accent3": "#8fbcbb", "good": "#a3be8c",
        "warn": "#ebcb8b", "bad": "#bf616a", "info": "#88c0d0",
        "mauve": "#b48ead", "lavender": "#81a1c1", "blue": "#5e81ac",
        "teal": "#8fbcbb", "pink": "#b48ead", "peach": "#d08770",
    },
    "everforest": {
        "base": "#2d353b", "surface": "#343f44", "overlay": "#475258",
        "text": "#d3c6aa", "subtext": "#9da9a0", "accent": "#a7c080",
        "accent2": "#83c092", "accent3": "#7fbbb3", "good": "#a7c080",
        "warn": "#dbbc7f", "bad": "#e67e80", "info": "#7fbbb3",
        "mauve": "#d699b6", "lavender": "#a7c080", "blue": "#7fbbb3",
        "teal": "#83c092", "pink": "#d699b6", "peach": "#e69875",
    },
    "rose-pine": {
        "base": "#232136", "surface": "#2a273f", "overlay": "#393552",
        "text": "#e0def4", "subtext": "#908caa", "accent": "#c4a7e7",
        "accent2": "#ea9a97", "accent3": "#9ccfd8",
        "good": "#3e8fb0", "warn": "#f6c177", "bad": "#eb6f92",
        "info": "#9ccfd8", "mauve": "#c4a7e7", "lavender": "#c4a7e7",
        "blue": "#3e8fb0", "teal": "#9ccfd8", "pink": "#ea9a97",
        "peach": "#f6c177",
    },
    "dracula": {
        "base": "#282a36", "surface": "#343746", "overlay": "#44475a",
        "text": "#f8f8f2", "subtext": "#bcc2cd", "accent": "#bd93f9",
        "accent2": "#ff79c6", "accent3": "#8be9fd", "good": "#50fa7b",
        "warn": "#f1fa8c", "bad": "#ff5555", "info": "#8be9fd",
        "mauve": "#bd93f9", "lavender": "#caa9fa", "blue": "#8be9fd",
        "teal": "#8be9fd", "pink": "#ff79c6", "peach": "#ffb86c",
    },
    "gruvbox": {
        "base": "#282828", "surface": "#3c3836", "overlay": "#504945",
        "text": "#ebdbb2", "subtext": "#bdae93", "accent": "#fe8019",
        "accent2": "#b8bb26", "accent3": "#83a598", "good": "#b8bb26",
        "warn": "#fabd2f", "bad": "#fb4934", "info": "#8ec07c",
        "mauve": "#d3869b", "lavender": "#83a598", "blue": "#83a598",
        "teal": "#8ec07c", "pink": "#d3869b", "peach": "#fe8019",
    },
    "cyberpunk": {
        "base": "#0b0e14", "surface": "#12161f", "overlay": "#1b2230",
        "text": "#f0f6fc", "subtext": "#8b98a9", "accent": "#ff2a6d",
        "accent2": "#05d9e8", "accent3": "#d300c5", "good": "#39ff14",
        "warn": "#f9f002", "bad": "#ff003c", "info": "#05d9e8",
        "mauve": "#ff2a6d", "lavender": "#d300c5", "blue": "#05d9e8",
        "teal": "#01ffc3", "pink": "#ff2a6d", "peach": "#ff9e64",
    },
    "matrix": {
        "base": "#000000", "surface": "#0a0f0a", "overlay": "#102010",
        "text": "#00ff41", "subtext": "#22aa33", "accent": "#00ff41",
        "accent2": "#39ff14", "accent3": "#008f11", "good": "#00ff41",
        "warn": "#aaff00", "bad": "#ff0000", "info": "#00ffaa",
        "mauve": "#00ff41", "lavender": "#39ff14", "blue": "#00ff41",
        "teal": "#00ffaa", "pink": "#00ff41", "peach": "#aaff00",
    },
}

DEFAULT_THEME = "cyberpunk"

# accept the bash aliases too
ALIASES = {
    "catppuccin-mocha": "catppuccin",
    "tokyo": "tokyo-night",
    "aurora": "nord",
    "rosepine": "rose-pine",
    "gruvbox-dark": "gruvbox",
}


def resolve(name: str | None) -> str:
    """Normalise a theme name to a known palette key."""
    if not name:
        return DEFAULT_THEME
    name = name.strip().lower()
    name = ALIASES.get(name, name)
    return name if name in PALETTES else DEFAULT_THEME


def palette(name: str | None) -> dict[str, str]:
    return PALETTES[resolve(name)]


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def ansi(hex_colour: str) -> str:
    """Truecolour ANSI foreground escape for a hex colour."""
    r, g, b = _hex_to_rgb(hex_colour)
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
