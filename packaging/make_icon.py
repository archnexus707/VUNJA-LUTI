#!/usr/bin/env python3
"""Render the VUNJA LUTI app icon with QPainter (crisp neon, no SVG-filter deps).

Draws a dark rounded tile with glowing concentric Tor "onion" rings, a rotation
arc + arrowhead (the IP-rotator motif) and a VL monogram. Exports PNGs at the
standard hicolor sizes. Run: python3 packaging/make_icon.py OUTDIR
"""

from __future__ import annotations

import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush, QColor, QConicalGradient, QFont, QImage, QLinearGradient, QPainter,
    QPainterPath, QPen, QRadialGradient,
)
from PyQt6.QtWidgets import QApplication

NEON_PINK = "#ff2a6d"
NEON_MAGENTA = "#d300c5"
NEON_CYAN = "#05d9e8"
BG0 = "#0b0e14"
BG1 = "#161b27"


def _glow_circle(p: QPainter, cx: float, cy: float, r: float, colour: QColor, width: float):
    """Fake a neon glow by stacking translucent wide strokes under a bright core."""
    for w, a in ((width * 3.2, 28), (width * 2.0, 55), (width * 1.0, 255)):
        c = QColor(colour); c.setAlpha(a)
        pen = QPen(c, w); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)


def _glow_arc(p: QPainter, rect: QRectF, start: int, span: int, colour: QColor, width: float):
    for w, a in ((width * 3.0, 30), (width * 1.8, 60), (width * 1.0, 255)):
        c = QColor(colour); c.setAlpha(a)
        pen = QPen(c, w); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(rect, start * 16, span * 16)


def render(size: int) -> QImage:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    s = size
    u = s / 128.0  # unit scale relative to a 128px design

    # ── rounded background tile ──
    margin = 5 * u
    radius = 26 * u
    tile = QRectF(margin, margin, s - 2 * margin, s - 2 * margin)
    path = QPainterPath(); path.addRoundedRect(tile, radius, radius)
    grad = QLinearGradient(tile.topLeft(), tile.bottomRight())
    grad.setColorAt(0, QColor(BG1)); grad.setColorAt(1, QColor(BG0))
    p.fillPath(path, QBrush(grad))

    # subtle inner vignette
    vig = QRadialGradient(QPointF(s / 2, s * 0.44), s * 0.6)
    vig.setColorAt(0, QColor(255, 255, 255, 14))
    vig.setColorAt(1, QColor(0, 0, 0, 0))
    p.fillPath(path, QBrush(vig))

    # neon border (gradient stroke)
    bgrad = QLinearGradient(tile.topLeft(), tile.bottomRight())
    bgrad.setColorAt(0, QColor(NEON_PINK))
    bgrad.setColorAt(0.5, QColor(NEON_MAGENTA))
    bgrad.setColorAt(1, QColor(NEON_CYAN))
    p.setPen(QPen(QBrush(bgrad), 3 * u)); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(tile, radius, radius)

    cx, cy = s / 2, s * 0.45

    # ── onion rings (gradient per ring) ──
    p.save()
    p.setClipPath(path)
    _glow_circle(p, cx, cy, 30 * u, QColor(NEON_PINK), 3.0 * u)
    _glow_circle(p, cx, cy, 20 * u, QColor(NEON_MAGENTA), 2.6 * u)
    _glow_circle(p, cx, cy, 10 * u, QColor(NEON_CYAN), 2.2 * u)

    # ── rotation arc + arrowhead ──
    arc_rect = QRectF(cx - 38 * u, cy - 38 * u, 76 * u, 76 * u)
    _glow_arc(p, arc_rect, 60, 250, QColor(NEON_CYAN), 3.5 * u)
    # arrowhead at arc start (top)
    ah = QPainterPath()
    ah.moveTo(cx + 2 * u, cy - 44 * u)
    ah.lineTo(cx + 16 * u, cy - 36 * u)
    ah.lineTo(cx + 2 * u, cy - 28 * u)
    ah.closeSubpath()
    glow = QColor(NEON_CYAN); glow.setAlpha(70)
    p.setPen(Qt.PenStyle.NoPen); p.setBrush(glow)
    p.drawPath(ah)
    p.setBrush(QColor(NEON_CYAN))
    p.drawPath(ah)
    p.restore()

    # ── VL monogram ──
    f = QFont("JetBrains Mono, monospace"); f.setBold(True)
    f.setPixelSize(int(20 * u))
    p.setFont(f)
    tgrad = QLinearGradient(0, s * 0.8, s, s * 0.95)
    tgrad.setColorAt(0, QColor(NEON_PINK)); tgrad.setColorAt(1, QColor(NEON_CYAN))
    p.setPen(QPen(QBrush(tgrad), 1))
    p.drawText(QRectF(0, s * 0.74, s, s * 0.2), Qt.AlignmentFlag.AlignCenter, "VL")

    p.end()
    return img


def main() -> int:
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    app = QApplication([])  # noqa: F841 — needed for font/raster engine
    import os
    os.makedirs(outdir, exist_ok=True)
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        img = render(size)
        path = os.path.join(outdir, f"vunja-luti-{size}.png")
        img.save(path, "PNG")
        print(f"  wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
