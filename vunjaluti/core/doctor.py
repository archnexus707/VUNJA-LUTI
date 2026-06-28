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
    eng = TorEngine(cfg.socks_port, cfg.control_port, cfg.control_password)
    checks: list[Check] = []

    checks.append(Check("tor binary", shutil.which("tor") is not None,
                        "found" if shutil.which("tor") else "missing (apt install tor)"))
    checks.append(Check("tor running", eng.is_running(),
                        f"SOCKS on 127.0.0.1:{cfg.socks_port}" if eng.is_running()
                        else "not listening — `vl start`"))
    # verify we can actually authenticate, not just that the port is open
    auth_ok = False
    auth_detail = "disabled — needed for rotation"
    if eng.control_available():
        try:
            eng.bootstrap_phase()  # opens + authenticates a controller
            with eng._controller():
                pass
            auth_ok = True
            auth_detail = f"authenticated on {cfg.control_port}"
        except Exception:
            auth_detail = "open but auth fails — needs password setup"
    checks.append(Check("control port", auth_ok, auth_detail, fixable=not auth_ok))
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
    """Enable Tor's control port using password auth (works for any user).

    Generates a random control password, stores the *hash* in torrc and the
    plaintext in the user config (chmod 600), then reloads Tor. This avoids the
    cookie-permission problem where ``/run/tor/control.authcookie`` is unreadable
    without debian-tor group membership + re-login.
    """
    import secrets

    cfg = cfg or Config.load()
    password = secrets.token_urlsafe(24)
    hashed = torrc.hash_password(password)
    if not hashed:
        return False, "could not run `tor --hash-password` (is tor installed?)"

    lines = torrc.ensure_control_port(cfg.control_port, cfg.socks_port, hashed)
    if not torrc.write_block(lines):
        return False, "failed to write /etc/tor/torrc (need sudo/pkexec)"
    if not torrc.reload_tor():
        return False, "wrote torrc but could not reload tor"

    cfg.control_password = password
    cfg.save()
    return True, "control port enabled with password auth; tor reloaded"
