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


def _output_has_killswitch_drop() -> bool:
    """True if the OUTPUT chain still ends in our catch-all DROP (i.e. egress
    is still blocked). Used to verify teardown actually opened the network."""
    cp = _run(["sh", "-c", "iptables -S OUTPUT"])
    if cp.returncode != 0:
        return False
    return "-A OUTPUT -j DROP" in cp.stdout


def _hard_open_egress() -> None:
    """Guaranteed fallback restore. Surgically clears the OUTPUT chain and
    opens its policy on both v4 and v6, without touching nat/mangle or Docker's
    own chains. Safe on the iptables-nft backend used by Kali."""
    _run(["iptables", "-P", "OUTPUT", "ACCEPT"])
    _run(["iptables", "-F", "OUTPUT"])
    _run(["ip6tables", "-P", "OUTPUT", "ACCEPT"])
    _run(["ip6tables", "-F", "OUTPUT"])


def enable(socks_port: int = 9050) -> tuple[bool, str]:
    """Block all non-Tor egress. Returns (ok, message)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Snapshot current rules — but NEVER overwrite a good snapshot while the
    # killswitch is already active, or we would capture the DROP rule itself and
    # "restore" the lock-out later. Keep the clean pre-killswitch snapshot.
    if is_active() and V4_BACKUP.exists():
        pass
    else:
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
    """Restore egress. Tries the snapshot first, then ALWAYS verifies the
    network is actually open and force-opens it if not, so the user can never be
    left offline by a failed restore (common on the nftables backend)."""
    restored = False
    if V4_BACKUP.exists():
        cp = _run(["sh", "-c", f"iptables-restore < {V4_BACKUP}"])
        restored = cp.returncode == 0
    if V6_BACKUP.exists():
        _run(["sh", "-c", f"ip6tables-restore < {V6_BACKUP}"])

    # The critical guarantee: if the snapshot was missing, failed to apply, or
    # left our DROP rule in place, force the OUTPUT chain open regardless.
    forced = False
    if not restored or _output_has_killswitch_drop():
        _hard_open_egress()
        forced = True

    STATE.unlink(missing_ok=True)

    if _output_has_killswitch_drop():
        # Should be impossible after _hard_open_egress, but report honestly.
        return False, "killswitch teardown FAILED — OUTPUT still DROPs; run: sudo iptables -F OUTPUT && sudo iptables -P OUTPUT ACCEPT"
    if forced and not restored:
        return True, "killswitch disengaged — egress force-opened (snapshot restore failed)"
    if forced:
        return True, "killswitch disengaged — snapshot restored and egress verified open"
    return True, "killswitch disengaged — firewall restored from snapshot"


def set_ipv6(disabled: bool) -> bool:
    val = "1" if disabled else "0"
    ok = True
    for key in ("net.ipv6.conf.all.disable_ipv6", "net.ipv6.conf.default.disable_ipv6"):
        ok &= _run(["sysctl", "-w", f"{key}={val}"]).returncode == 0
    return ok
