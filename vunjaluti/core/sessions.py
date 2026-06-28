"""Named sessions, rotation logging, and JSON/CSV export."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import LOG_DIR, SESSION_DIR


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def start(name: str) -> dict:
    """Create or resume a named session; returns its metadata."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    sfile = SESSION_DIR / f"{name}.json"
    if sfile.exists():
        meta = json.loads(sfile.read_text())
        meta["resumed_at"] = _now()
    else:
        meta = {"name": name, "started": _now(), "rotations": 0}
    sfile.write_text(json.dumps(meta, indent=2))
    return meta


def log_rotation(log_file: str | Path, ip: str, cc: str, flag: str, latency_ms: int) -> None:
    entry = {
        "timestamp": _now(), "ip": ip, "country": cc,
        "flag": flag, "latency_ms": latency_ms,
    }
    p = Path(log_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def list_sessions() -> list[dict]:
    if not SESSION_DIR.exists():
        return []
    out = []
    for f in sorted(SESSION_DIR.glob("*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except ValueError:
            continue
    return out


def auto_log_path(session: str | None = None) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = session or "rotation"
    return LOG_DIR / f"{base}_{stamp}.json"


def export(log_file: str | Path, out_base: str | None = None) -> tuple[Path, Path]:
    """Export a JSON-lines rotation log to ``.json`` and ``.csv``."""
    log_file = Path(log_file)
    if not log_file.exists():
        raise FileNotFoundError(log_file)
    out_base = out_base or f"vl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    json_out = Path(f"{out_base}.json")
    csv_out = Path(f"{out_base}.csv")

    rows = []
    for line in log_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue

    json_out.write_text(json.dumps(rows, indent=2))
    with csv_out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "ip", "country", "flag", "latency_ms"])
        for r in rows:
            w.writerow([r.get("timestamp", ""), r.get("ip", ""), r.get("country", ""),
                        r.get("flag", ""), r.get("latency_ms", "")])
    return json_out, csv_out
