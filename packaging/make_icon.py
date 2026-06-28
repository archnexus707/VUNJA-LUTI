#!/usr/bin/env python3
"""Render the VUNJA LUTI app icon with QPainter — a neon Pac-Man.

Pac-Man chomping a row of pellets is the IP-rotation motif: keep eating exits.
Crisp at every size, no SVG-filter dependencies. Run:
    python3 packaging/make_icon.py OUTDIR
"""

from __future__ import annotations

import os
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import QApplication

PAC = "#ffe600"        # pac-man yellow
PAC_EDGE = "#ffb300"
PELLET = "#05d9e8"     # neon cyan pellets
GHOST = "#ff2a6d"      # neon pink ghost
BG0 = "#0b0e14"
BG1 = "#161b27"
BORDER_A = "#ffe600"
BORDER_B = "#05d9e8"


def _glow_dot(p: QPainter, cx: float, cy: float, r: float, colour: str):
    for rr, a in ((r * 2.4, 50), (r * 1.5, 110), (r, 255)):
        c = QColor(colour); c.setAlpha(a)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(c)
        p.drawEllipse(QPointF(cx, cy), rr, rr)


def render(size: int) -> "object":
    from PyQt6.QtGui import QImage
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    u = s / 128.0

    # rounded tile
    margin = 5 * u
    radius = 26 * u
    tile = QRectF(margin, margin, s - 2 * margin, s - 2 * margin)
    path = QPainterPath(); path.addRoundedRect(tile, radius, radius)
    bg = QLinearGradient(tile.topLeft(), tile.bottomRight())
    bg.setColorAt(0, QColor(BG1)); bg.setColorAt(1, QColor(BG0))
    p.fillPath(path, QBrush(bg))
    vig = QRadialGradient(QPointF(s / 2, s * 0.42), s * 0.65)
    vig.setColorAt(0, QColor(255, 255, 255, 12)); vig.setColorAt(1, QColor(0, 0, 0, 0))
    p.fillPath(path, QBrush(vig))
    # neon border
    bgrad = QLinearGradient(tile.topLeft(), tile.bottomRight())
    bgrad.setColorAt(0, QColor(BORDER_A)); bgrad.setColorAt(1, QColor(BORDER_B))
    p.setPen(QPen(QBrush(bgrad), 3 * u)); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(tile, radius, radius)

    p.save()
    p.setClipPath(path)

    # pellets being eaten (right -> mouth)
    cy = s * 0.5
    for i, x in enumerate((0.86, 0.72, 0.60)):
        _glow_dot(p, s * x, cy, (3.0 - i * 0.3) * u, PELLET)

    # Pac-Man (left, mouth opening to the right)
    pac_c = QPointF(s * 0.40, cy)
    pac_r = 30 * u
    pac_rect = QRectF(pac_c.x() - pac_r, pac_c.y() - pac_r, pac_r * 2, pac_r * 2)
    mouth = 60  # degrees of open mouth
    # glow halo
    halo = QColor(PAC); halo.setAlpha(45)
    p.setPen(Qt.PenStyle.NoPen); p.setBrush(halo)
    p.drawEllipse(pac_c, pac_r * 1.18, pac_r * 1.18)
    # body as a pie with a radial shade
    body = QRadialGradient(pac_c, pac_r)
    body.setColorAt(0, QColor(PAC)); body.setColorAt(1, QColor(PAC_EDGE))
    p.setBrush(QBrush(body)); p.setPen(Qt.PenStyle.NoPen)
    start = int(mouth / 2)
    span = 360 - mouth
    p.drawPie(pac_rect, start * 16, span * 16)
    # eye
    p.setBrush(QColor("#101018"))
    p.drawEllipse(QPointF(pac_c.x() + 2 * u, pac_c.y() - pac_r * 0.45), 3.2 * u, 3.2 * u)

    p.restore()
    p.end()
    return img


def render_transparent(size: int) -> "object":
    """Pac-Man only (no tile) — for the GUI header logo."""
    from PyQt6.QtGui import QImage
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size; u = s / 128.0
    cy = s * 0.5
    for i, x in enumerate((0.88, 0.72)):
        _glow_dot(p, s * x, cy, (3.2 - i * 0.4) * u, PELLET)
    pac_c = QPointF(s * 0.42, cy); pac_r = 42 * u
    pac_rect = QRectF(pac_c.x() - pac_r, pac_c.y() - pac_r, pac_r * 2, pac_r * 2)
    halo = QColor(PAC); halo.setAlpha(55)
    p.setPen(Qt.PenStyle.NoPen); p.setBrush(halo)
    p.drawEllipse(pac_c, pac_r * 1.15, pac_r * 1.15)
    body = QRadialGradient(pac_c, pac_r)
    body.setColorAt(0, QColor(PAC)); body.setColorAt(1, QColor(PAC_EDGE))
    p.setBrush(QBrush(body))
    p.drawPie(pac_rect, 30 * 16, 300 * 16)
    p.setBrush(QColor("#101018"))
    p.drawEllipse(QPointF(pac_c.x() + 2 * u, pac_c.y() - pac_r * 0.45), 4.4 * u, 4.4 * u)
    p.end()
    return img


def main() -> int:
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    app = QApplication([])  # noqa: F841 — needed for the raster engine
    os.makedirs(outdir, exist_ok=True)
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        render(size).save(os.path.join(outdir, f"vunja-luti-{size}.png"), "PNG")
        print(f"  wrote {outdir}/vunja-luti-{size}.png")
    # transparent header logo
    render_transparent(256).save(os.path.join(outdir, "vunja-luti-logo.png"), "PNG")
    print(f"  wrote {outdir}/vunja-luti-logo.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
