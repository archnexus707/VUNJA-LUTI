"""Hardened Firefox profile routed through Tor for anonymous browsing.

Creates a self-contained Firefox profile under the VL config dir whose traffic
and DNS go through Tor's SOCKS proxy, with WebRTC, geolocation, prefetch and
telemetry disabled so the real IP cannot leak from the browser. The profile is
separate from the user's normal Firefox, and is rewritten on every launch so it
always reflects the current SOCKS port.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import CONFIG_DIR, SOCKS_HOST, SOCKS_PORT

PROFILE_DIR = CONFIG_DIR / "firefox-profile"

FIREFOX_BINS = ("firefox", "firefox-esr")


def firefox_bin() -> str | None:
    for name in FIREFOX_BINS:
        path = shutil.which(name)
        if path:
            return path
    return None


def _user_js(socks_host: str, socks_port: int) -> str:
    return f"""// VUNJA-LUTI hardened profile — route through Tor, no IP/DNS/WebRTC leaks.
// Auto-generated; edits are overwritten on the next `vl browser`.

// SOCKS5 -> Tor
user_pref("network.proxy.type", 1);
user_pref("network.proxy.socks", "{socks_host}");
user_pref("network.proxy.socks_port", {socks_port});
user_pref("network.proxy.socks_version", 5);
// Resolve DNS through Tor, never locally (stops DNS leak)
user_pref("network.proxy.socks_remote_dns", true);
user_pref("network.proxy.no_proxies_on", "");
user_pref("network.proxy.allow_hijacking_localhost", true);

// Kill WebRTC (largest real-IP leak in browsers)
user_pref("media.peerconnection.enabled", false);
user_pref("media.peerconnection.ice.default_address_only", true);
user_pref("media.peerconnection.ice.no_host", true);
user_pref("media.peerconnection.ice.proxy_only_if_behind_proxy", true);

// No geolocation
user_pref("geo.enabled", false);
user_pref("geo.provider.network.url", "");

// Anti-fingerprint + first-party isolation
user_pref("privacy.resistFingerprinting", true);
user_pref("privacy.firstparty.isolate", true);
user_pref("webgl.disabled", true);

// No prefetch / predictor / speculative connections (can bypass the proxy)
user_pref("network.prefetch-next", false);
user_pref("network.dns.disablePrefetch", true);
user_pref("network.predictor.enabled", false);
user_pref("network.http.speculative-parallel-limit", 0);
user_pref("browser.urlbar.speculativeConnect.enabled", false);
user_pref("network.dns.disableIPv6", true);

// No phone-home (Safe Browsing, captive portal, telemetry, beacons)
user_pref("browser.safebrowsing.malware.enabled", false);
user_pref("browser.safebrowsing.phishing.enabled", false);
user_pref("network.captive-portal-service.enabled", false);
user_pref("captivedetect.canonicalURL", "");
user_pref("beacon.enabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);

// Permanent private mode; keep nothing on disk between sessions
user_pref("browser.privatebrowsing.autostart", true);
user_pref("places.history.enabled", false);
"""


def create_profile(socks_host: str = SOCKS_HOST, socks_port: int = SOCKS_PORT) -> Path:
    """Create or refresh the hardened profile. Returns its path."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILE_DIR / "user.js").write_text(_user_js(socks_host, socks_port))
    return PROFILE_DIR


def launch(socks_host: str = SOCKS_HOST, socks_port: int = SOCKS_PORT) -> tuple[bool, str]:
    """Refresh the profile and launch Firefox with it, detached."""
    fb = firefox_bin()
    if not fb:
        return False, "firefox not found (install firefox or firefox-esr)"
    profile = create_profile(socks_host, socks_port)
    try:
        subprocess.Popen(
            [fb, "--profile", str(profile), "--no-remote"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as e:
        return False, f"failed to launch firefox: {e}"
    return True, f"hardened Firefox launched (profile: {profile})"
