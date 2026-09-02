"""Ícones desenhados em runtime para o QSS.

O Qt Style Sheets não aceita data URI, e substituir o fundo de um indicador de
QCheckBox descarta o desenho nativo do "✓". Em vez de arrastar arquivos .png
pelo projeto, desenhamos os poucos ícones necessários e gravamos numa pasta
temporária, referenciada pela folha de estilo.

Os arquivos são nomeados pela paleta, para que trocar de tema não reaproveite
um ícone com a cor do tema anterior.
"""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPolygonF

if TYPE_CHECKING:
    from .theme import Palette

_cache: dict[str, dict[str, str]] = {}


def _icon_dir() -> str:
    directory = os.path.join(tempfile.gettempdir(), "backup_maximus_icons")
    os.makedirs(directory, exist_ok=True)
    return directory


def _save(name: str, pixmap: QPixmap) -> str:
    """Devolve o caminho no formato que o QSS entende (barras normais)."""
    path = os.path.join(_icon_dir(), name)
    pixmap.save(path, "PNG")
    return path.replace("\\", "/")


def _checkmark(size: int, color: str) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(size * 0.16)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    # Traço do "✓" em coordenadas proporcionais ao tamanho.
    painter.drawPolyline(QPolygonF([
        QPointF(size * 0.22, size * 0.52),
        QPointF(size * 0.42, size * 0.72),
        QPointF(size * 0.78, size * 0.28),
    ]))
    painter.end()
    return pixmap


def _chevron(width: int, height: int, color: str) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.drawPolyline(QPolygonF([
        QPointF(width * 0.22, height * 0.38),
        QPointF(width * 0.50, height * 0.66),
        QPointF(width * 0.78, height * 0.38),
    ]))
    painter.end()
    return pixmap


def paths(palette: "Palette") -> dict[str, str]:
    """Gera (uma vez por paleta) e devolve os caminhos dos ícones."""
    cached = _cache.get(palette.name)
    if cached is not None:
        return cached

    suffix = palette.name
    art = {
        "check": _save(f"check_{suffix}.png", _checkmark(14, palette.on_accent)),
        "chevron": _save(f"chevron_{suffix}.png", _chevron(12, 12, palette.ink_2)),
        "chevron_off": _save(f"chevron_off_{suffix}.png",
                             _chevron(12, 12, palette.ink_3)),
    }
    _cache[palette.name] = art
    return art
