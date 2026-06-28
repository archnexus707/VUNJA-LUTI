"""First-run / health checks, with optional auto-fix.

``vl doctor`` verifies the whole stack (Tor, control port, proxychains, python
deps, fonts) and can repair the most common problem — the missing control port —
by writing VL's managed torrc block and reloading Tor.
"""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass

from . import torrc
from .config import Config
from .engine import TorEngine


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    fixable: bool = False


def _has_module(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def run_checks(cfg: Config | None = None) -> list[Check]:
    cfg = cfg or Config.load()
    eng = TorEngine(cfg.socks_port, cfg.control_port)
    checks: list[Check] = []

    checks.append(Check("tor binary", shutil.which("tor") is not None,
                        "found" if shutil.which("tor") else "missing (apt install tor)"))
    checks.append(Check("tor running", eng.is_running(),
                        f"SOCKS on 127.0.0.1:{cfg.socks_port}" if eng.is_running()
                        else "not listening — `vl start`"))
    ctrl = eng.control_available()
    checks.append(Check("control port", ctrl,
                        f"reachable on {cfg.control_port}" if ctrl
                        else "disabled — needed for rotation", fixable=not ctrl))
    checks.append(Check("proxychains4", shutil.which("proxychains4") is not None,
                        "found" if shutil.which("proxychains4") else "missing (optional)"))

    for mod, pkg in (("stem", "python3-stem"), ("requests", "python3-requests"),
                     ("socks", "python3-socks")):
        checks.append(Check(f"python: {mod}", _has_module(mod),
                            "ok" if _has_module(mod) else f"missing ({pkg})"))

    pyqt = _has_module("PyQt6")
    checks.append(Check("python: PyQt6", pyqt,
                        "ok" if pyqt else "missing (python3-pyqt6) — GUI only"))

    return checks


def fix_control_port(cfg: Config | None = None) -> tuple[bool, str]:
    """Enable Tor's control port with cookie auth via the managed torrc block."""
    cfg = cfg or Config.load()
    lines = torrc.ensure_control_port(cfg.control_port, cfg.socks_port)
    if not torrc.write_block(lines):
        return False, "failed to write /etc/tor/torrc (need sudo)"
    if not torrc.reload_tor():
        return False, "wrote torrc but could not reload tor"
    return True, "control port enabled; tor reloaded"
