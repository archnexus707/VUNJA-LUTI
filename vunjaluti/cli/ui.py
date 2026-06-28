"""Tiny dependency-free ANSI styling helpers for the CLI, theme-aware."""

from __future__ import annotations

import sys

from .. import __version__, themes

_PAL = themes.palette(themes.DEFAULT_THEME)


def set_theme(name: str) -> None:
    global _PAL
    _PAL = themes.palette(name)


def c(role: str, text: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{themes.ansi(_PAL[role])}{text}{themes.RESET}"


def bold(text: str) -> str:
    return text if not sys.stdout.isatty() else f"{themes.BOLD}{text}{themes.RESET}"


def dim(text: str) -> str:
    return text if not sys.stdout.isatty() else f"{themes.DIM}{text}{themes.RESET}"


def say(msg: str) -> None:
    print(f"  {c('accent', '◆')}  {msg}")


def warn(msg: str) -> None:
    print(f"  {c('warn', '◇')}  {msg}")


def err(msg: str) -> None:
    print(f"  {c('bad', '✖')}  {msg}")


def ok(msg: str) -> None:
    print(f"  {c('good', '✔')}  {msg}")


BANNER = r"""
   ██╗   ██╗██╗   ██╗███╗   ██╗      ██╗  █████╗     ██╗     ██╗   ██╗████████╗██╗
   ██║   ██║██║   ██║████╗  ██║      ██║ ██╔══██╗    ██║     ██║   ██║╚══██╔══╝██║
   ██║   ██║██║   ██║██╔██╗ ██║      ██║ ███████║    ██║     ██║   ██║   ██║   ██║
   ╚██╗ ██╔╝██║   ██║██║╚██╗██║ ██   ██║ ██╔══██║    ██║     ██║   ██║   ██║   ██║
    ╚████╔╝ ╚██████╔╝██║ ╚████║ ╚█████╔╝ ██║  ██║    ███████╗╚██████╔╝   ██║   ██║
     ╚═══╝   ╚═════╝ ╚═╝  ╚═══╝  ╚════╝  ╚═╝  ╚═╝    ╚══════╝ ╚═════╝    ╚═╝   ╚═╝
"""


def banner(theme: str = "") -> None:
    if theme:
        set_theme(theme)
    roles = ["mauve", "lavender", "accent", "accent2", "blue", "teal"]
    for i, line in enumerate(BANNER.strip("\n").splitlines()):
        print(c(roles[i % len(roles)], line))
    print()
    print(f"  {bold('VUNJA LUTI')}  {dim('— v' + __version__)}   "
          f"{c('subtext', 'Tor Proxy · IP Rotator · Tool Wrapper')}")
    print(f"  {dim('archnexus707  ·  github.com/archnexus707/VUNJA-LUTI')}")
    print()
