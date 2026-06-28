"""TorEngine — reliable Tor control via the ``stem`` library.

Responsibilities:
  * report whether Tor is running and bootstrapped
  * start/stop the system Tor service
  * request a new identity (NEWNYM) — the real, correct way to rotate
  * read live circuit / hop information for the circuit map
  * surface the current exit IP, country and latency

Unlike the original ``tornet`` approach this uses Tor's control protocol, so
rotation is deterministic and we get real telemetry instead of screen-scraping.
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
from dataclasses import dataclass

from . import geo
from .config import CONTROL_PORT, SOCKS_HOST, SOCKS_PORT


@dataclass
class Hop:
    nickname: str
    fingerprint: str
    country: str       # cc
    flag: str
    address: str | None = None


@dataclass
class Status:
    running: bool
    bootstrapped: int          # 0-100, -1 if unknown
    exit_ip: str | None
    country: str
    flag: str
    latency_ms: int
    control: bool              # control port reachable
    socks_port: int
    control_port: int


class TorError(RuntimeError):
    pass


def _port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _run_priv(argv: list[str]) -> subprocess.CompletedProcess:
    if os.geteuid() != 0:
        argv = ["sudo", *argv]
    return subprocess.run(argv, text=True, capture_output=True, check=False)


class TorEngine:
    def __init__(self, socks_port: int = SOCKS_PORT, control_port: int = CONTROL_PORT):
        self.socks_port = socks_port
        self.control_port = control_port

    # ── lifecycle ────────────────────────────────────────────────
    def is_running(self) -> bool:
        return _port_open(SOCKS_HOST, self.socks_port)

    def control_available(self) -> bool:
        return _port_open(SOCKS_HOST, self.control_port)

    def start_service(self) -> bool:
        for unit in ("tor", "tor@default"):
            if _run_priv(["systemctl", "start", unit]).returncode == 0:
                break
        else:
            _run_priv(["service", "tor", "start"])
        return self._wait_for_socks(timeout=30)

    def stop_service(self) -> bool:
        ok = False
        for unit in ("tor", "tor@default"):
            if _run_priv(["systemctl", "stop", unit]).returncode == 0:
                ok = True
        if not ok:
            ok = _run_priv(["service", "tor", "stop"]).returncode == 0
        return ok

    def restart_service(self) -> bool:
        for unit in ("tor", "tor@default"):
            _run_priv(["systemctl", "restart", unit])
        return self._wait_for_socks(timeout=30)

    def _wait_for_socks(self, timeout: float = 30) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_running():
                return True
            time.sleep(0.5)
        return False

    # ── control-port operations (stem) ───────────────────────────
    def _controller(self):
        try:
            from stem.control import Controller
        except ImportError as e:  # pragma: no cover
            raise TorError("python3-stem is not installed") from e
        try:
            ctrl = Controller.from_port(address=SOCKS_HOST, port=self.control_port)
        except Exception as e:
            raise TorError(
                f"cannot reach Tor control port {self.control_port} "
                "(run `vl doctor` to enable it)"
            ) from e
        try:
            ctrl.authenticate()
        except Exception as e:
            ctrl.close()
            raise TorError(f"control authentication failed: {e}") from e
        return ctrl

    def new_identity(self) -> bool:
        """Signal NEWNYM — the canonical way to get a fresh circuit/exit."""
        from stem import Signal

        with self._controller() as ctrl:
            ctrl.signal(Signal.NEWNYM)
        return True

    def bootstrap_phase(self) -> int:
        try:
            with self._controller() as ctrl:
                line = ctrl.get_info("status/bootstrap-phase")
            for tok in line.split():
                if tok.startswith("PROGRESS="):
                    return int(tok.split("=", 1)[1])
        except Exception:
            return -1
        return -1

    def circuits(self) -> list[list[Hop]]:
        """Return the active general-purpose circuits as lists of hops."""
        out: list[list[Hop]] = []
        try:
            with self._controller() as ctrl:
                for circ in ctrl.get_circuits():
                    if circ.status != "BUILT" or circ.purpose != "GENERAL":
                        continue
                    hops: list[Hop] = []
                    for fp, nick in circ.path:
                        cc = "??"
                        try:
                            cc = (ctrl.get_info(f"ip-to-country/relay/{fp}") or "??").upper()
                        except Exception:
                            pass
                        hops.append(Hop(nick or "?", fp, cc, geo.cc_to_flag(cc)))
                    if hops:
                        out.append(hops)
        except Exception:
            pass
        return out

    # ── high-level status ────────────────────────────────────────
    def status(self, with_geo: bool = True) -> Status:
        running = self.is_running()
        control = self.control_available()
        ip = country = flag = None
        ms = 0
        cc = "??"
        flag = "🏴"
        if running and with_geo:
            ip = geo.exit_ip(self.socks_port)
            if ip:
                cc, flag = geo.country_of(ip, self.socks_port)
            ms = geo.latency_ms(self.socks_port)
        return Status(
            running=running,
            bootstrapped=self.bootstrap_phase() if control else (100 if running else 0),
            exit_ip=ip,
            country=cc,
            flag=flag,
            latency_ms=ms,
            control=control,
            socks_port=self.socks_port,
            control_port=self.control_port,
        )

    def rotate(self, settle: float = 2.0) -> tuple[str | None, str, str, int]:
        """Rotate identity and return ``(ip, cc, flag, latency_ms)`` afterwards."""
        self.new_identity()
        time.sleep(settle)
        ip = geo.exit_ip(self.socks_port)
        cc, flag = geo.country_of(ip, self.socks_port) if ip else ("??", "🏴")
        ms = geo.latency_ms(self.socks_port)
        return ip, cc, flag, ms
