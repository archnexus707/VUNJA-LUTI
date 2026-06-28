"""Route arbitrary commands through Tor via proxychains, with optional rotation.

Fixes from the original:
  * the command is handled as an **argv list**, never re-split by the shell, so
    quoted arguments like ``-u 'http://x?id=1'`` survive intact.
  * rotation runs in a background thread and is cleanly stopped afterwards.
  * ``rotate_on_requests`` is honoured for the built-in request loop and is
    documented as time-approximated for opaque external tools.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from .config import SOCKS_HOST, SOCKS_PORT


def build_proxychains_conf(ports: list[int] | None = None, dest: str | None = None) -> str:
    ports = ports or [SOCKS_PORT]
    lines = [
        "# VUNJA-LUTI auto-generated proxychains config",
        "strict_chain",
        "proxy_dns",
        "remote_dns_subnet 224",
        "tcp_read_time_out 15000",
        "tcp_connect_time_out 8000",
        "",
        "[ProxyList]",
        *[f"socks5 {SOCKS_HOST} {p}" for p in ports],
        "",
    ]
    text = "\n".join(lines)
    if dest is None:
        fd = tempfile.NamedTemporaryFile(
            "w", prefix="vl_proxychains_", suffix=".conf", delete=False
        )
        fd.write(text)
        fd.close()
        return fd.name
    Path(dest).write_text(text)
    return dest


def to_argv(command) -> list[str]:
    """Accept either a list (used as-is) or a string (parsed once, safely)."""
    if isinstance(command, (list, tuple)):
        return list(command)
    return shlex.split(command)


def has_proxychains() -> bool:
    return shutil.which("proxychains4") is not None or shutil.which("proxychains") is not None


def _proxychains_bin() -> str:
    return shutil.which("proxychains4") or shutil.which("proxychains") or "proxychains4"


def wrap(
    command,
    rotate_fn=None,
    rotate_interval: int = 0,
    conf_path: str | None = None,
    on_output=None,
) -> int:
    """Run ``command`` through proxychains. Returns the child's exit code.

    ``rotate_fn`` (callable) is invoked every ``rotate_interval`` seconds in a
    background thread while the command runs, if both are provided.
    """
    if not has_proxychains():
        raise RuntimeError("proxychains4 is not installed (sudo apt install proxychains4)")

    argv = to_argv(command)
    conf = conf_path or build_proxychains_conf()
    full = [_proxychains_bin(), "-f", conf, *argv]

    stop = threading.Event()
    rot_thread = None
    if rotate_fn and rotate_interval > 0:
        def _rotator():
            while not stop.wait(rotate_interval):
                try:
                    rotate_fn()
                except Exception:
                    pass
        rot_thread = threading.Thread(target=_rotator, daemon=True)
        rot_thread.start()

    try:
        if on_output is None:
            return subprocess.run(full, check=False).returncode
        proc = subprocess.Popen(
            full, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            on_output(line.rstrip("\n"))
        proc.wait()
        return proc.returncode
    finally:
        stop.set()
        if rot_thread:
            rot_thread.join(timeout=2)


# Toolbox command templates. {placeholders} are filled from user input.
TOOLBOX = {
    "hydra":    'hydra {auth} -P {passlist} {service}://{target}',
    "ffuf":     'ffuf -u {target}/FUZZ -w {wordlist} -mc 200,301,302,403',
    "gobuster": 'gobuster dir -u {target} -w {wordlist}',
    "sqlmap":   "sqlmap -u {target} --batch",
    "nmap":     'nmap -sT -Pn -p {ports} {target}',
    "nikto":    'nikto -h {target}',
    "wpscan":   'wpscan --url {target} --random-user-agent',
    "curl":     'curl -sSL {target}',
}
