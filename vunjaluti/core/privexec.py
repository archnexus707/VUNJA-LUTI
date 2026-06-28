"""Privilege escalation helper shared by torrc / engine / firewall.

Picks the right escalator automatically:
  * already root      -> run directly
  * GUI (no tty) +X   -> pkexec (graphical polkit prompt)
  * terminal          -> sudo
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def escalator() -> list[str]:
    if os.geteuid() == 0:
        return []
    no_tty = not sys.stdin or not sys.stdin.isatty()
    if no_tty and os.environ.get("DISPLAY") and shutil.which("pkexec"):
        return ["pkexec"]
    return ["sudo"]


def run(argv: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    cmd = [*escalator(), *argv]
    return subprocess.run(
        cmd, input=input_text, text=True, capture_output=True, check=False
    )


def can_escalate() -> bool:
    """True if we can run a privileged command without an interactive prompt."""
    if os.geteuid() == 0:
        return True
    return subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0
