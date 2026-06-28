"""Managed ``torrc`` editing.

Every change VL makes lives inside a single fenced block so it can be applied,
updated, and **cleanly removed** without disturbing the user's own torrc lines.
This fixes the original tool's habit of blindly appending to ``/etc/tor/torrc``.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from . import privexec

TORRC = Path("/etc/tor/torrc")
BEGIN = "# >>> VUNJA-LUTI managed block >>>"
END = "# <<< VUNJA-LUTI managed block <<<"


def _run_priv(argv: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    """Run a command, escalating (pkexec/sudo) when not already root."""
    return privexec.run(argv, input_text)


def hash_password(password: str) -> str | None:
    """Return Tor's HashedControlPassword for ``password`` (via ``tor --hash-password``)."""
    tor = shutil.which("tor") or "/usr/sbin/tor"
    cp = subprocess.run([tor, "--hash-password", password],
                        text=True, capture_output=True, check=False)
    for line in reversed(cp.stdout.splitlines()):
        if line.startswith("16:"):
            return line.strip()
    return None


def read() -> str:
    try:
        return TORRC.read_text()
    except (FileNotFoundError, PermissionError):
        cp = _run_priv(["cat", str(TORRC)])
        return cp.stdout if cp.returncode == 0 else ""


def _strip_block(text: str) -> str:
    out, skip = [], False
    for line in text.splitlines():
        if line.strip() == BEGIN:
            skip = True
            continue
        if line.strip() == END:
            skip = False
            continue
        if not skip:
            out.append(line)
    # collapse trailing blank lines
    while out and out[-1].strip() == "":
        out.pop()
    return "\n".join(out) + "\n"


def write_block(lines: list[str]) -> bool:
    """Replace the managed block with ``lines`` (atomic, privilege-aware)."""
    base = _strip_block(read())
    block = "\n".join([BEGIN, *lines, END])
    new = base.rstrip("\n") + "\n\n" + block + "\n"
    return _atomic_write(new)


def clear_block() -> bool:
    """Remove the managed block entirely."""
    return _atomic_write(_strip_block(read()))


def _atomic_write(content: str) -> bool:
    import os

    if os.access(TORRC, os.W_OK):
        try:
            TORRC.write_text(content)
            return True
        except OSError:
            pass
    # privileged path: write temp then install with sudo
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".torrc") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    cp = _run_priv(["install", "-m", "644", tmp_path, str(TORRC)])
    Path(tmp_path).unlink(missing_ok=True)
    return cp.returncode == 0


def ensure_control_port(control_port: int, socks_port: int,
                        hashed_password: str | None = None) -> list[str]:
    """Return the managed lines that enable the control port.

    stem needs a control port; Debian's tor ships with it disabled. We prefer
    **password auth** (``HashedControlPassword``) because it works for any user
    immediately — unlike cookie auth, which requires reading the root-owned
    ``/run/tor/control.authcookie`` (needs debian-tor group membership + re-login).
    """
    lines = [
        f"SocksPort {socks_port}",
        f"ControlPort {control_port}",
    ]
    if hashed_password:
        lines.append(f"HashedControlPassword {hashed_password}")
    else:
        # fall back to group-readable cookie if no password was set up
        lines += ["CookieAuthentication 1", "CookieAuthFileGroupReadable 1"]
    return lines


def exit_nodes_lines(country_csv: str) -> list[str]:
    """Build a valid ``ExitNodes`` directive.

    Tor wants lowercase, individually-braced country codes:
        ExitNodes {us},{nl},{de}
    The original tool emitted ``{US,DE}`` which Tor silently ignored.
    """
    codes = [c.strip().lower() for c in country_csv.split(",") if c.strip()]
    if not codes:
        return []
    spec = ",".join("{%s}" % c for c in codes)
    return [f"ExitNodes {spec}", "StrictNodes 1"]


def reload_tor() -> bool:
    for argv in (["systemctl", "reload", "tor"], ["systemctl", "reload", "tor@default"]):
        if _run_priv(argv).returncode == 0:
            return True
    # last resort: HUP the daemon
    if shutil.which("killall"):
        return _run_priv(["killall", "-HUP", "tor"]).returncode == 0
    return False
