"""Background QThread workers so the UI never blocks on Tor/network calls."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from ..core.engine import TorEngine


class StatusWorker(QThread):
    """Polls Tor status on an interval and emits a Status dataclass."""

    updated = pyqtSignal(object)

    def __init__(self, engine: TorEngine, interval_ms: int = 4000):
        super().__init__()
        self.engine = engine
        self.interval_ms = interval_ms
        self._stop = False

    def run(self) -> None:
        while not self._stop:
            try:
                st = self.engine.status()
                self.updated.emit(st)
            except Exception:
                pass
            # sleep in small slices so stop is responsive
            slept = 0
            while slept < self.interval_ms and not self._stop:
                self.msleep(200)
                slept += 200

    def stop(self) -> None:
        self._stop = True


class RotateWorker(QThread):
    """One-shot identity rotation; emits (ip, cc, flag, ms)."""

    done = pyqtSignal(object, str, str, int)
    failed = pyqtSignal(str)

    def __init__(self, engine: TorEngine):
        super().__init__()
        self.engine = engine

    def run(self) -> None:
        try:
            ip, cc, flag, ms = self.engine.rotate()
            self.done.emit(ip, cc, flag, ms)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class AutoRotateWorker(QThread):
    """Rotates on an interval until stopped; emits each new exit."""

    rotated = pyqtSignal(object, str, str, int)
    failed = pyqtSignal(str)

    def __init__(self, engine: TorEngine, interval_s: int):
        super().__init__()
        self.engine = engine
        self.interval_s = max(5, interval_s)
        self._stop = False

    def run(self) -> None:
        while not self._stop:
            slept = 0
            while slept < self.interval_s * 1000 and not self._stop:
                self.msleep(200)
                slept += 200
            if self._stop:
                break
            try:
                ip, cc, flag, ms = self.engine.rotate()
                self.rotated.emit(ip, cc, flag, ms)
            except Exception as e:  # noqa: BLE001
                self.failed.emit(str(e))

    def stop(self) -> None:
        self._stop = True


class ServiceWorker(QThread):
    """Start / stop / restart the Tor service off the UI thread."""

    done = pyqtSignal(bool, str)

    def __init__(self, engine: TorEngine, action: str):
        super().__init__()
        self.engine = engine
        self.action = action

    def run(self) -> None:
        try:
            if self.action == "start":
                ok = self.engine.start_service()
            elif self.action == "stop":
                ok = self.engine.stop_service()
            else:
                ok = self.engine.restart_service()
            self.done.emit(ok, self.action)
        except Exception as e:  # noqa: BLE001
            self.done.emit(False, str(e))


class WrapWorker(QThread):
    """Run a wrapped (Tor-routed) command, streaming output lines."""

    line = pyqtSignal(str)
    finished_code = pyqtSignal(int)

    def __init__(self, engine: TorEngine, command, rotate_interval: int):
        super().__init__()
        self.engine = engine
        self.command = command
        self.rotate_interval = rotate_interval

    def run(self) -> None:
        from ..core import wrap
        rotate_fn = self.engine.new_identity if (
            self.rotate_interval > 0 and self.engine.control_available()
        ) else None
        try:
            rc = wrap.wrap(
                self.command,
                rotate_fn=rotate_fn,
                rotate_interval=self.rotate_interval,
                on_output=self.line.emit,
            )
        except Exception as e:  # noqa: BLE001
            self.line.emit(f"[error] {e}")
            rc = 1
        self.finished_code.emit(rc)
