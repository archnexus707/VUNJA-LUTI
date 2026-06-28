"""Custom-painted widgets: latency sparkline and circuit map."""

from __future__ import annotations

from collections import deque

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF, QBrush, QFont
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QWidget

from .. import themes


class Sparkline(QWidget):
    """Live latency sparkline."""

    def __init__(self, theme: str, maxlen: int = 60, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.data: deque[int] = deque(maxlen=maxlen)
        self.setMinimumHeight(60)

    def set_theme(self, theme: str) -> None:
        self.theme = theme
        self.update()

    def push(self, value: int) -> None:
        self.data.append(max(0, value))
        self.update()

    def paintEvent(self, _event) -> None:
        p = themes.palette(self.theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if len(self.data) < 2:
            painter.setPen(QColor(p["subtext"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "collecting latency…")
            return
        vals = list(self.data)
        lo, hi = min(vals), max(vals)
        rng = max(1, hi - lo)
        pad = 6
        step = (w - 2 * pad) / max(1, len(vals) - 1)
        pts = [QPointF(pad + i * step, h - pad - (v - lo) / rng * (h - 2 * pad))
               for i, v in enumerate(vals)]
        # area fill
        poly = QPolygonF([QPointF(pts[0].x(), h - pad), *pts, QPointF(pts[-1].x(), h - pad)])
        fill = QColor(p["accent"]); fill.setAlpha(40)
        painter.setBrush(QBrush(fill)); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(poly)
        # line
        pen = QPen(QColor(p["accent"]), 2)
        painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolyline(QPolygonF(pts))
        # last point
        painter.setBrush(QColor(p["good"]))
        painter.drawEllipse(pts[-1], 3, 3)
        # label
        painter.setPen(QColor(p["subtext"]))
        painter.drawText(QRectF(pad, 2, w, 16), Qt.AlignmentFlag.AlignLeft,
                         f"{vals[-1]} ms  (min {lo} / max {hi})")


class CircuitMap(QWidget):
    """Draws guard → middle → exit hops with country flags."""

    def __init__(self, theme: str, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.hops: list = []   # list of engine.Hop
        self.setMinimumHeight(90)

    def set_theme(self, theme: str) -> None:
        self.theme = theme
        self.update()

    def set_hops(self, hops: list) -> None:
        self.hops = hops or []
        self.update()

    def paintEvent(self, _event) -> None:
        p = themes.palette(self.theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cy = h / 2

        nodes = [("You", "🖥")]
        labels = ["guard", "middle", "exit"]
        for i, hop in enumerate(self.hops[:3]):
            nodes.append((labels[i] if i < 3 else "relay",
                          f"{hop.flag} {hop.country}"))
        nodes.append(("Internet", "🌐"))
        if len(nodes) == 2:
            painter.setPen(QColor(p["subtext"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "no circuit yet — start Tor")
            return

        n = len(nodes)
        gap = w / n
        radius = 16
        colours = [p["text"], p["accent3"], p["accent"], p["mauve"], p["good"]]
        centers = [QPointF(gap * (i + 0.5), cy - 4) for i in range(n)]

        # links
        painter.setPen(QPen(QColor(p["overlay"]), 2, Qt.PenStyle.DashLine))
        for i in range(n - 1):
            painter.drawLine(centers[i], centers[i + 1])

        font = QFont(); font.setPointSize(13)
        small = QFont(); small.setPointSize(8)
        for i, (label, glyph) in enumerate(nodes):
            col = QColor(colours[i % len(colours)])
            painter.setBrush(QColor(p["surface"]))
            painter.setPen(QPen(col, 2))
            painter.drawEllipse(centers[i], radius, radius)
            painter.setPen(QColor(p["text"]))
            painter.setFont(font)
            painter.drawText(QRectF(centers[i].x() - radius, centers[i].y() - radius,
                                    radius * 2, radius * 2),
                             Qt.AlignmentFlag.AlignCenter, glyph)
            painter.setPen(QColor(p["subtext"]))
            painter.setFont(small)
            painter.drawText(QRectF(centers[i].x() - gap / 2, cy + radius - 2, gap, 16),
                             Qt.AlignmentFlag.AlignCenter, label)
