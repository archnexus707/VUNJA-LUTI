"""Kill-switch and leak-guard with safe backup/restore.

The original tool ran ``iptables -F OUTPUT`` on disable, nuking unrelated rules,
and could lock the user out. Here we snapshot the full ruleset with
``iptables-save`` before touching anything and restore it verbatim on disable.
"""

from __future__ import annotations

from pathlib import Path

from . import privexec
from .config import CONFIG_DIR

V4_BACKUP = CONFIG_DIR / "iptables.v4.bak"
V6_BACKUP = CONFIG_DIR / "iptables.v6.bak"
STATE = CONFIG_DIR / "killswitch.state"

TOR_UID_USERS = ("debian-tor", "tor")


def _run(argv: list[str]):
    return privexec.run(argv)


def _tor_uid() -> str | None:
    import pwd

    for name in TOR_UID_USERS:
        try:
            pwd.getpwnam(name)
            return name
        except KeyError:
            continue
    return None


def is_active() -> bool:
    return STATE.exists()


def enable(socks_port: int = 9050) -> tuple[bool, str]:
    """Block all non-Tor egress. Returns (ok, message)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # snapshot current rules
    v4 = _run(["sh", "-c", "iptables-save"])
    if v4.returncode != 0:
        return False, "iptables-save failed (need root?)"
    V4_BACKUP.write_text(v4.stdout)
    v6 = _run(["sh", "-c", "ip6tables-save"])
    if v6.returncode == 0:
        V6_BACKUP.write_text(v6.stdout)

    uid = _tor_uid()
    if not uid:
        return False, "could not find tor system user (debian-tor)"

    rules = [
        ["iptables", "-F", "OUTPUT"],
        ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
        # allow already-established return paths
        ["iptables", "-A", "OUTPUT", "-m", "state",
         "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        # allow the Tor process itself to reach the network
        ["iptables", "-A", "OUTPUT", "-m", "owner",
         "--uid-owner", uid, "-j", "ACCEPT"],
        # everything else is dropped
        ["iptables", "-A", "OUTPUT", "-j", "DROP"],
    ]
    for r in rules:
        cp = _run(r)
        if cp.returncode != 0:
            # roll back to snapshot on any failure
            disable()
            return False, f"rule failed: {' '.join(r)} :: {cp.stderr.strip()}"

    # kill IPv6 egress entirely (prevents v6 leaks)
    _run(["ip6tables", "-P", "OUTPUT", "DROP"])
    _run(["ip6tables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])

    STATE.write_text(str(socks_port))
    return True, "killswitch ENGAGED — only Tor egress allowed"


def disable() -> tuple[bool, str]:
    """Restore the exact ruleset captured at enable time."""
    restored = False
    if V4_BACKUP.exists():
        cp = _run(["sh", "-c", f"iptables-restore < {V4_BACKUP}"])
        restored = cp.returncode == 0
    else:
        # no snapshot: at least re-open the policy
        _run(["iptables", "-P", "OUTPUT", "ACCEPT"])
        _run(["iptables", "-F", "OUTPUT"])
    if V6_BACKUP.exists():
        _run(["sh", "-c", f"ip6tables-restore < {V6_BACKUP}"])
    else:
        _run(["ip6tables", "-P", "OUTPUT", "ACCEPT"])
    STATE.unlink(missing_ok=True)
    return True, "killswitch disengaged — firewall restored" if restored else \
        "killswitch disengaged (no snapshot; policy reset)"


def set_ipv6(disabled: bool) -> bool:
    val = "1" if disabled else "0"
    ok = True
    for key in ("net.ipv6.conf.all.disable_ipv6", "net.ipv6.conf.default.disable_ipv6"):
        ok &= _run(["sysctl", "-w", f"{key}={val}"]).returncode == 0
    return ok
