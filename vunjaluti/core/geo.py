"""Exit-IP discovery and country/flag lookup, routed through Tor's SOCKS proxy."""

from __future__ import annotations

import functools

from .config import SOCKS_HOST, SOCKS_PORT

# IP-echo endpoints tried in order (all reachable over Tor).
_IP_ENDPOINTS = (
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
)


def _socks_proxies(port: int) -> dict[str, str]:
    # socks5h => resolve DNS through Tor (no DNS leak)
    url = f"socks5h://{SOCKS_HOST}:{port}"
    return {"http": url, "https": url}


def exit_ip(port: int = SOCKS_PORT, timeout: float = 8.0) -> str | None:
    """Return the current Tor exit IP, or ``None`` if unreachable."""
    try:
        import requests
    except ImportError:
        return None
    proxies = _socks_proxies(port)
    for url in _IP_ENDPOINTS:
        try:
            r = requests.get(url, proxies=proxies, timeout=timeout)
            ip = r.text.strip()
            if ip and len(ip) <= 45:
                return ip
        except Exception:
            continue
    return None


def real_ip(timeout: float = 6.0) -> str | None:
    """Return the *direct* (non-Tor) IP — used by the leak/anonymity check."""
    try:
        import requests
    except ImportError:
        return None
    try:
        return requests.get("https://api.ipify.org", timeout=timeout).text.strip()
    except Exception:
        return None


def cc_to_flag(cc: str) -> str:
    """Two-letter country code -> regional-indicator emoji flag."""
    cc = (cc or "").upper()
    if len(cc) != 2 or not cc.isalpha():
        return "🏴"
    return chr(ord(cc[0]) + 127397) + chr(ord(cc[1]) + 127397)


@functools.lru_cache(maxsize=256)
def country_of(ip: str, port: int = SOCKS_PORT, timeout: float = 6.0) -> tuple[str, str]:
    """Return ``(country_code, flag_emoji)`` for an IP, looked up through Tor."""
    if not ip:
        return ("??", "🏴")
    try:
        import requests
    except ImportError:
        return ("??", "🏴")
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}?fields=countryCode",
            proxies=_socks_proxies(port),
            timeout=timeout,
        )
        cc = r.json().get("countryCode", "??")
        return (cc, cc_to_flag(cc))
    except Exception:
        return ("??", "🏴")


def latency_ms(port: int = SOCKS_PORT, timeout: float = 10.0) -> int:
    """Round-trip latency through Tor in milliseconds (0 = failed)."""
    try:
        import requests
    except ImportError:
        return 0
    try:
        r = requests.get(
            "https://check.torproject.org",
            proxies=_socks_proxies(port),
            timeout=timeout,
        )
        return int(r.elapsed.total_seconds() * 1000)
    except Exception:
        return 0


def quality(ms: int) -> str:
    if ms <= 0:
        return "⚫"
    if ms < 300:
        return "🟢"
    if ms < 800:
        return "🟡"
    return "🔴"
