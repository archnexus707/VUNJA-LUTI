"""VUNJA LUTI — PyQt6 desktop application."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFontDatabase, QIcon
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QSpinBox, QSystemTrayIcon, QTabWidget,
    QVBoxLayout, QWidget,
)

from .. import __version__, themes
from ..core import firewall, sessions, torrc, wrap
from ..core.config import Config, ensure_dirs
from ..core.engine import TorEngine
from . import style
from .widgets import CircuitMap, Sparkline
from .workers import AutoRotateWorker, RotateWorker, ServiceWorker, StatusWorker, WrapWorker

RES = Path(__file__).resolve().parent.parent / "resources"


def _card(obj_name: str = "") -> QFrame:
    f = QFrame()
    f.setProperty("class", "card")
    if obj_name:
        f.setObjectName(obj_name)
    return f


class MainWindow(QMainWindow):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.engine = TorEngine(cfg.socks_port, cfg.control_port)
        self.auto_worker: AutoRotateWorker | None = None
        self.workers: list = []   # keep refs so threads aren't GC'd

        self.setWindowTitle("VUNJA LUTI")
        self.resize(960, 720)

        root = QWidget(); root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 16, 18, 12)
        layout.setSpacing(14)

        layout.addLayout(self._build_header())
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_dashboard(), "  Dashboard  ")
        self.tabs.addTab(self._build_toolbox(), "  Toolbox  ")
        self.tabs.addTab(self._build_sessions(), "  Sessions  ")
        self.tabs.addTab(self._build_settings(), "  Settings  ")
        layout.addWidget(self.tabs)

        self.statusBar().showMessage("Ready")
        self._build_tray()
        self.apply_theme(cfg.theme)

        # live status polling
        self.status_worker = StatusWorker(self.engine, interval_ms=4000)
        self.status_worker.updated.connect(self.on_status)
        self.status_worker.start()

    # ── header ───────────────────────────────────────────────────
    def _build_header(self) -> QHBoxLayout:
        h = QHBoxLayout()
        title_box = QVBoxLayout(); title_box.setSpacing(0)
        title = QLabel("⚡ VUNJA LUTI"); title.setObjectName("title")
        sub = QLabel(f"Tor Proxy · IP Rotator · Tool Wrapper — v{__version__}")
        sub.setObjectName("subtitle")
        title_box.addWidget(title); title_box.addWidget(sub)
        h.addLayout(title_box); h.addStretch(1)

        h.addWidget(QLabel("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(themes.PALETTES))
        self.theme_combo.setCurrentText(self.cfg.theme)
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        h.addWidget(self.theme_combo)
        return h

    # ── dashboard ────────────────────────────────────────────────
    def _build_dashboard(self) -> QWidget:
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(14)

        # status card
        card = _card("accentCard"); cl = QVBoxLayout(card)
        top = QHBoxLayout()
        self.lbl_state = QLabel("◌ checking…")
        self.lbl_state.setObjectName("statValue")
        top.addWidget(self.lbl_state); top.addStretch(1)
        self.lbl_ip = QLabel("—"); self.lbl_ip.setObjectName("statValue")
        top.addWidget(self.lbl_ip)
        cl.addLayout(top)

        stats = QHBoxLayout()
        for key, attr in [("Country", "lbl_country"), ("Latency", "lbl_lat"),
                          ("Rotations", "lbl_rots"), ("Uptime", "lbl_up")]:
            box = QVBoxLayout()
            k = QLabel(key); k.setObjectName("statKey")
            val = QLabel("—"); val.setObjectName("statValue")
            setattr(self, attr, val)
            box.addWidget(val); box.addWidget(k)
            stats.addLayout(box)
        cl.addLayout(stats)

        self.boot_bar = QProgressBar(); self.boot_bar.setRange(0, 100)
        self.boot_bar.setValue(0); self.boot_bar.setFormat("Tor bootstrap %p%")
        cl.addWidget(self.boot_bar)
        v.addWidget(card)

        # controls
        controls = QHBoxLayout()
        self.btn_start = QPushButton("▶  START"); self.btn_start.setObjectName("primary")
        self.btn_rotate = QPushButton("⟳  ROTATE")
        self.btn_stop = QPushButton("■  STOP"); self.btn_stop.setObjectName("danger")
        self.btn_start.clicked.connect(self.do_start)
        self.btn_rotate.clicked.connect(self.do_rotate)
        self.btn_stop.clicked.connect(self.do_stop)
        for b in (self.btn_start, self.btn_rotate, self.btn_stop):
            controls.addWidget(b)
        controls.addStretch(1)
        self.chk_auto = QCheckBox("Auto-rotate")
        self.chk_auto.toggled.connect(self.toggle_auto)
        self.chk_ks = QCheckBox("Killswitch")
        self.chk_ks.toggled.connect(self.toggle_killswitch)
        self.chk_leak = QCheckBox("Leak-guard")
        self.chk_leak.toggled.connect(self.toggle_leakguard)
        for c in (self.chk_auto, self.chk_ks, self.chk_leak):
            controls.addWidget(c)
        v.addLayout(controls)

        # circuit map
        cm_card = _card(); cml = QVBoxLayout(cm_card)
        cml.addWidget(self._section("CIRCUIT"))
        self.circuit = CircuitMap(self.cfg.theme)
        cml.addWidget(self.circuit)
        v.addWidget(cm_card)

        # latency sparkline
        sp_card = _card(); spl = QVBoxLayout(sp_card)
        spl.addWidget(self._section("LATENCY"))
        self.spark = Sparkline(self.cfg.theme)
        spl.addWidget(self.spark)
        v.addWidget(sp_card)

        # live feed
        feed_card = _card(); fl = QVBoxLayout(feed_card)
        fl.addWidget(self._section("LIVE FEED"))
        self.feed = QPlainTextEdit(); self.feed.setObjectName("console")
        self.feed.setReadOnly(True); self.feed.setMaximumBlockCount(500)
        fl.addWidget(self.feed)
        v.addWidget(feed_card, 1)
        return w

    # ── toolbox ──────────────────────────────────────────────────
    def _build_toolbox(self) -> QWidget:
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(12)
        v.addWidget(self._section("RUN A TOOL THROUGH TOR"))
        row = QHBoxLayout()
        self.tool_combo = QComboBox()
        self.tool_combo.addItems([*wrap.TOOLBOX.keys(), "custom"])
        self.tool_combo.currentTextChanged.connect(self._rebuild_tool_form)
        row.addWidget(QLabel("Tool")); row.addWidget(self.tool_combo, 1)
        v.addLayout(row)

        self.tool_form_host = QWidget()
        self.tool_form = QFormLayout(self.tool_form_host)
        v.addWidget(self.tool_form_host)
        self._tool_inputs: dict[str, QLineEdit] = {}
        self._rebuild_tool_form(self.tool_combo.currentText())

        run_row = QHBoxLayout()
        self.btn_run = QPushButton("▶  RUN"); self.btn_run.setObjectName("primary")
        self.btn_run.clicked.connect(self.run_tool)
        self.btn_kill = QPushButton("■  STOP"); self.btn_kill.setObjectName("danger")
        self.btn_kill.clicked.connect(self.kill_tool); self.btn_kill.setEnabled(False)
        run_row.addWidget(self.btn_run); run_row.addWidget(self.btn_kill); run_row.addStretch(1)
        v.addLayout(run_row)

        self.console = QPlainTextEdit(); self.console.setObjectName("console")
        self.console.setReadOnly(True); self.console.setMaximumBlockCount(5000)
        v.addWidget(self.console, 1)
        self._wrap_worker: WrapWorker | None = None
        return w

    def _rebuild_tool_form(self, tool: str) -> None:
        while self.tool_form.rowCount():
            self.tool_form.removeRow(0)
        self._tool_inputs.clear()
        if tool == "custom":
            le = QLineEdit(); le.setPlaceholderText("full command, e.g. curl https://example.com")
            self.tool_form.addRow("Command", le)
            self._tool_inputs["__custom__"] = le
            return
        import string
        template = wrap.TOOLBOX[tool]
        defaults = {"wordlist": "/usr/share/wordlists/dirb/common.txt",
                    "ports": "80,443,8080", "service": "ssh"}
        for _, field, _, _ in string.Formatter().parse(template):
            if field and field not in self._tool_inputs:
                le = QLineEdit(); le.setText(defaults.get(field, ""))
                le.setPlaceholderText(field)
                self.tool_form.addRow(field, le)
                self._tool_inputs[field] = le

    def run_tool(self) -> None:
        tool = self.tool_combo.currentText()
        if tool == "custom":
            cmd = self._tool_inputs["__custom__"].text().strip()
            if not cmd:
                return
            command = wrap.to_argv(cmd)
        else:
            template = wrap.TOOLBOX[tool]
            fields = {k: v.text().strip() for k, v in self._tool_inputs.items()}
            if "auth" in template and "auth" not in fields:
                fields["auth"] = ""
            try:
                command = wrap.to_argv(template.format(**fields))
            except KeyError as e:
                QMessageBox.warning(self, "Missing field", f"Fill in {e}")
                return
        if not wrap.has_proxychains():
            QMessageBox.warning(self, "proxychains missing",
                                "Install proxychains4: sudo apt install proxychains4")
            return
        self.console.appendPlainText(f"$ {' '.join(command)}")
        self.btn_run.setEnabled(False); self.btn_kill.setEnabled(True)
        self._wrap_worker = WrapWorker(self.engine, command, self.cfg.rotate_interval)
        self._wrap_worker.line.connect(self.console.appendPlainText)
        self._wrap_worker.finished_code.connect(self._tool_done)
        self._wrap_worker.start()

    def _tool_done(self, rc: int) -> None:
        self.console.appendPlainText(f"[exit code {rc}]")
        self.btn_run.setEnabled(True); self.btn_kill.setEnabled(False)

    def kill_tool(self) -> None:
        if self._wrap_worker and self._wrap_worker.isRunning():
            self._wrap_worker.terminate()
            self.console.appendPlainText("[terminated]")
            self.btn_run.setEnabled(True); self.btn_kill.setEnabled(False)

    # ── sessions ─────────────────────────────────────────────────
    def _build_sessions(self) -> QWidget:
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(12)
        v.addWidget(self._section("SAVED SESSIONS"))
        self.sessions_view = QPlainTextEdit(); self.sessions_view.setReadOnly(True)
        self.sessions_view.setObjectName("console")
        v.addWidget(self.sessions_view, 1)
        btn = QPushButton("↻  Refresh"); btn.clicked.connect(self.refresh_sessions)
        v.addWidget(btn)
        self.refresh_sessions()
        return w

    def refresh_sessions(self) -> None:
        rows = sessions.list_sessions()
        if not rows:
            self.sessions_view.setPlainText("No saved sessions yet.")
            return
        out = []
        for s in rows:
            out.append(f"{s.get('name','?'):<22} "
                       f"{s.get('rotations',0):>4} rotations   started {s.get('started','?')}")
        self.sessions_view.setPlainText("\n".join(out))

    # ── settings ─────────────────────────────────────────────────
    def _build_settings(self) -> QWidget:
        w = QWidget(); form = QFormLayout(w)
        self.spin_interval = QSpinBox(); self.spin_interval.setRange(5, 3600)
        self.spin_interval.setValue(self.cfg.rotate_interval)
        self.spin_interval.setSuffix(" s")
        self.spin_interval.valueChanged.connect(self._save_interval)
        form.addRow("Rotation interval", self.spin_interval)

        self.edit_exit = QLineEdit(self.cfg.exit_filter)
        self.edit_exit.setPlaceholderText("us,nl,de")
        apply_exit = QPushButton("Apply exit filter")
        apply_exit.clicked.connect(self.apply_exit_filter)
        exit_row = QWidget(); er = QHBoxLayout(exit_row); er.setContentsMargins(0, 0, 0, 0)
        er.addWidget(self.edit_exit, 1); er.addWidget(apply_exit)
        form.addRow("Exit countries", exit_row)

        self.chk_sound = QCheckBox(); self.chk_sound.setChecked(self.cfg.sound)
        form.addRow("Sound", self.chk_sound)
        self.chk_notif = QCheckBox(); self.chk_notif.setChecked(self.cfg.notifications)
        form.addRow("Notifications", self.chk_notif)

        doc_btn = QPushButton("🩺  Run doctor (diagnose & fix)")
        doc_btn.clicked.connect(self.run_doctor)
        form.addRow("Setup", doc_btn)

        reset_btn = QPushButton("⟲  Reset all VL changes")
        reset_btn.setObjectName("danger")
        reset_btn.clicked.connect(self.do_reset)
        form.addRow("Cleanup", reset_btn)
        return w

    def _save_interval(self, val: int) -> None:
        self.cfg.rotate_interval = val
        self.cfg.save()

    def apply_exit_filter(self) -> None:
        csv = self.edit_exit.text().strip()
        self.cfg.exit_filter = csv
        self.cfg.save()
        lines = torrc.ensure_control_port(self.cfg.control_port, self.cfg.socks_port)
        lines += torrc.exit_nodes_lines(csv)
        if torrc.write_block(lines) and torrc.reload_tor():
            self.statusBar().showMessage(f"Exit filter applied: {csv or 'any'}")
        else:
            QMessageBox.warning(self, "torrc", "Could not update torrc (need sudo).")

    def run_doctor(self) -> None:
        from ..core import doctor
        lines = []
        fixable = False
        for ch in doctor.run_checks(self.cfg):
            lines.append(f"{'✔' if ch.ok else '✖'}  {ch.name:<18} {ch.detail}")
            fixable |= ch.fixable and not ch.ok
        msg = "\n".join(lines)
        if fixable:
            msg += "\n\nEnable the Tor control port now?"
            if QMessageBox.question(self, "Doctor", msg) == QMessageBox.StandardButton.Yes:
                ok, m = doctor.fix_control_port(self.cfg)
                QMessageBox.information(self, "Doctor", m)
        else:
            QMessageBox.information(self, "Doctor", msg)

    def do_reset(self) -> None:
        if QMessageBox.question(self, "Reset",
                                "Remove VL's torrc block and restore the firewall?") \
                != QMessageBox.StandardButton.Yes:
            return
        torrc.clear_block(); torrc.reload_tor()
        if firewall.is_active():
            firewall.disable()
        firewall.set_ipv6(False)
        self.chk_ks.setChecked(False); self.chk_leak.setChecked(False)
        self.statusBar().showMessage("All VL changes reverted.")

    # ── actions ──────────────────────────────────────────────────
    def do_start(self) -> None:
        self.statusBar().showMessage("Starting Tor…")
        sw = ServiceWorker(self.engine, "start")
        sw.done.connect(lambda ok, a: self.statusBar().showMessage(
            "Tor started" if ok else "Tor failed to start"))
        self.workers.append(sw); sw.start()

    def do_stop(self) -> None:
        if self.auto_worker:
            self.chk_auto.setChecked(False)
        sw = ServiceWorker(self.engine, "stop")
        sw.done.connect(lambda ok, a: self.statusBar().showMessage("Tor stopped"))
        self.workers.append(sw); sw.start()

    def do_rotate(self) -> None:
        self.statusBar().showMessage("Rotating…")
        rw = RotateWorker(self.engine)
        rw.done.connect(self.on_rotated)
        rw.failed.connect(lambda m: self.statusBar().showMessage(f"Rotate failed: {m}"))
        self.workers.append(rw); rw.start()

    def toggle_auto(self, on: bool) -> None:
        if on:
            self.auto_worker = AutoRotateWorker(self.engine, self.cfg.rotate_interval)
            self.auto_worker.rotated.connect(self.on_rotated)
            self.auto_worker.start()
            self.statusBar().showMessage(f"Auto-rotate every {self.cfg.rotate_interval}s")
        elif self.auto_worker:
            self.auto_worker.stop(); self.auto_worker.wait(2000)
            self.auto_worker = None
            self.statusBar().showMessage("Auto-rotate off")

    def toggle_killswitch(self, on: bool) -> None:
        ok, msg = firewall.enable(self.cfg.socks_port) if on else firewall.disable()
        self.statusBar().showMessage(msg)
        if not ok and on:
            self.chk_ks.blockSignals(True); self.chk_ks.setChecked(False)
            self.chk_ks.blockSignals(False)

    def toggle_leakguard(self, on: bool) -> None:
        firewall.set_ipv6(on)
        self.statusBar().showMessage("IPv6 disabled" if on else "IPv6 restored")

    # ── slots ────────────────────────────────────────────────────
    _rotations = 0
    _start_ts = None

    def on_status(self, st) -> None:
        from ..core import geo
        if st.running:
            self.lbl_state.setText("◉ RUNNING")
            if self._start_ts is None:
                self._start_ts = time.monotonic()
        else:
            self.lbl_state.setText("○ STOPPED")
            self._start_ts = None
        self.lbl_ip.setText(st.exit_ip or "—")
        self.lbl_country.setText(f"{st.flag} {st.country}")
        self.lbl_lat.setText(f"{geo.quality(st.latency_ms)} {st.latency_ms} ms")
        self.lbl_rots.setText(str(self._rotations))
        if self._start_ts:
            secs = int(time.monotonic() - self._start_ts)
            self.lbl_up.setText(f"{secs//60}m {secs%60}s")
        if 0 <= st.bootstrapped <= 100:
            self.boot_bar.setValue(st.bootstrapped)
        if st.latency_ms > 0:
            self.spark.push(st.latency_ms)
        # update circuit map (cheap call done in worker would be better; throttle)
        self.circuit.set_hops(self._safe_circuits())

    def _safe_circuits(self):
        try:
            circs = self.engine.circuits()
            return circs[0] if circs else []
        except Exception:
            return []

    def on_rotated(self, ip, cc, flag, ms) -> None:
        self._rotations += 1
        ts = time.strftime("%H:%M:%S")
        self.feed.appendPlainText(f"{ts}  #{self._rotations}  {ip}  {flag} {cc}  {ms}ms")
        self.lbl_ip.setText(ip or "—")
        self.lbl_country.setText(f"{flag} {cc}")
        self.lbl_rots.setText(str(self._rotations))
        if ms > 0:
            self.spark.push(ms)
        if self.cfg.notifications and self.tray:
            self.tray.showMessage("VUNJA LUTI", f"New exit: {ip} {flag} {cc}",
                                  QSystemTrayIcon.MessageIcon.Information, 3000)

    # ── theme + tray ─────────────────────────────────────────────
    def apply_theme(self, name: str) -> None:
        name = themes.resolve(name)
        self.cfg.theme = name
        self.cfg.save()
        QApplication.instance().setStyleSheet(style.qss(name, self.cfg.font_family))
        for wdg in (getattr(self, "spark", None), getattr(self, "circuit", None)):
            if wdg:
                wdg.set_theme(name)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        icon_path = RES / "icons" / "vunja-luti.png"
        self.tray.setIcon(QIcon(str(icon_path)) if icon_path.exists()
                          else self.style().standardIcon(
                              self.style().StandardPixmap.SP_DriveNetIcon))
        menu = QMenu()
        for label, fn in [("Show", self.showNormal), ("Rotate now", self.do_rotate),
                          ("Stop Tor", self.do_stop)]:
            act = QAction(label, self); act.triggered.connect(fn); menu.addAction(act)
        menu.addSeparator()
        quit_act = QAction("Quit", self); quit_act.triggered.connect(self.close)
        menu.addAction(quit_act)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.showNormal() if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        try:
            self.tray.show()
        except Exception:
            self.tray = None

    def closeEvent(self, event) -> None:
        self.status_worker.stop(); self.status_worker.wait(2000)
        if self.auto_worker:
            self.auto_worker.stop(); self.auto_worker.wait(2000)
        super().closeEvent(event)

    @staticmethod
    def _section(text: str) -> QLabel:
        lbl = QLabel(text); lbl.setObjectName("statKey")
        return lbl


def _load_fonts() -> str:
    """Register any bundled .ttf fonts; return a usable family name."""
    fonts_dir = RES / "fonts"
    family = "JetBrainsMono Nerd Font"
    if fonts_dir.exists():
        for ttf in fonts_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(ttf))
    return family


def main() -> int:
    ensure_dirs()
    app = QApplication(sys.argv)
    app.setApplicationName("VUNJA LUTI")
    cfg = Config.load()
    cfg.font_family = _load_fonts()
    win = MainWindow(cfg)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
