"""User configuration: load/save ``~/.config/vl/config.json``."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("VL_CONFIG_DIR", Path.home() / ".config" / "vl"))
CONFIG_FILE = CONFIG_DIR / "config.json"
SESSION_DIR = CONFIG_DIR / "sessions"
LOG_DIR = CONFIG_DIR / "logs"

# Tor endpoints VL standardises on.
SOCKS_HOST = "127.0.0.1"
SOCKS_PORT = 9050
CONTROL_PORT = 9051
DNS_PORT = 5353


@dataclass
class Config:
    theme: str = "cyberpunk"
    rotate_interval: int = 60          # seconds between automatic rotations
    rotate_on_requests: int = 0        # 0 = disabled
    exit_filter: str = ""              # e.g. "us,nl,de"
    log_file: str = ""                 # explicit JSON log path ("" = auto)
    sound: bool = True
    notifications: bool = True
    socks_port: int = SOCKS_PORT
    control_port: int = CONTROL_PORT
    control_password: str = ""          # plaintext for stem; torrc stores only the hash
    font_family: str = "JetBrainsMono Nerd Font"

    extra: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Config":
        try:
            data = json.loads(CONFIG_FILE.read_text())
        except (FileNotFoundError, ValueError, OSError):
            return cls()
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        cfg = cls(**kwargs)
        cfg.extra = {k: v for k, v in data.items() if k not in known}
        return cfg

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        extra = data.pop("extra", {})
        data.update(extra)
        CONFIG_FILE.write_text(json.dumps(data, indent=2))
        # config can hold the control password — keep it private
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except OSError:
            pass


def ensure_dirs() -> None:
    for d in (CONFIG_DIR, SESSION_DIR, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)
