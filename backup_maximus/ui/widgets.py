"""Peças visuais que os arquivos .ui não conseguem descrever.

Tudo que é geometria — posição, largura de rótulo, altura de campo, margem —
vive em `designer/*.ui` e se edita no Qt Designer. O que sobra aqui é o que
precisa ser calculado em tempo de execução: ícones desenhados na cor da paleta
ativa, troca de papel visual e truncamento de texto.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from . import theme

# Estado codificado em forma E em cor: quem enxerga mal cor lê pelo símbolo e
# pelo texto esmaecido da linha, não só pelo tom do ponto.
DOT_OK = "ok"
DOT_BAD = "bad"
DOT_MUTED = "muted"


def _dot_color(kind: str) -> str:
    p = theme.current()
    return {DOT_OK: p.ok, DOT_BAD: p.bad}.get(kind, p.ink_3)


def dot_icon(kind: str, size: int = 10) -> QIcon:
    """Ponto colorido das listas de conjuntos e itens.

    Desenhado em vez de carregado de arquivo porque a cor vem da paleta ativa —
    trocar de tema regera os ícones na cor nova.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    color = QColor(_dot_color(kind))
    if kind == DOT_MUTED:
        color.setAlpha(140)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.end()
    return QIcon(pixmap)


def set_role(widget: QWidget, role: str) -> QWidget:
    """Troca o papel visual de um widget e repinta.

    O estilo vem de uma propriedade dinâmica em vez do objectName porque o Qt
    Designer exige objectName único por widget, e dezenas de rótulos dividem o
    mesmo estilo. Trocar a propriedade em tempo de execução exige o
    unpolish/polish — o Qt não reavalia a folha de estilo sozinho.
    """
    if widget.property("role") == role:
        return widget
    widget.setProperty("role", role)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    return widget


# ------------------------------------------------- formulários em runtime
# Estes três existem só para o assistente de nuvem, que monta os campos a partir
# do que o rclone informa sobre cada serviço — não há .ui possível para uma
# lista de campos que muda com a versão da ferramenta. Todo formulário estático
# continua nos arquivos do Designer.
def field_label(text: str) -> QLabel:
    """Rótulo com a mesma largura que os .ui usam, para as telas alinharem."""
    label = QLabel(text)
    label.setProperty("role", "field")
    label.setFixedWidth(theme.LABEL_WIDTH)
    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return label


def hint_label(text: str = "", warn: bool = False) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", "hintWarn" if warn else "hint")
    label.setWordWrap(True)
    return label


def elide_left(text: str, limit: int = 44) -> str:
    """Trunca pela ESQUERDA.

    O fim de um caminho é o que distingue os itens; o começo é o que eles têm
    em comum. Cortar pela direita esconderia justamente a parte informativa.
    """
    return text if len(text) <= limit else "…" + text[-(limit - 1):]
