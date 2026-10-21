r"""Campo de horário que se deixa digitar.

O `QTimeEdit` do Qt edita por seção: é preciso clicar em cima da hora ou do
minuto e digitar ali, e selecionar o texto todo não ajuda — a digitação
continua caindo numa seção só. Para um campo preenchido uma vez e esquecido,
isso vira a diferença entre configurar e desistir.

Aqui o horário é um `QLineEdit` com máscara: clicar e digitar `0800` funciona
como em qualquer outro campo. O botão de relógio ao lado abre um seletor com
setas, para quem prefere ajustar sem digitar.
"""

from __future__ import annotations

from PySide6.QtCore import QTime, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QMenu, QToolButton, QVBoxLayout, QWidget,
    QWidgetAction,
)

from . import relogio, theme

#: Usado quando o texto não dá para interpretar de jeito nenhum.
PADRAO = "22:00"


def normalizar(texto: str) -> str:
    """Texto digitado -> 'HH:MM'. Devolve vazio se não der para entender.

    Aceita o que as pessoas realmente digitam: `8`, `800`, `8:0`, `0800`,
    `08:00`. Hora e minuto fora da faixa são limitados em vez de recusados —
    quem digitou `25:70` quis dizer tarde, não quis um erro.
    """
    if ":" in texto:
        # O separador diz onde cada parte começa, e ignorá-lo faria "8:0"
        # virar oitenta horas. A máscara deixa lacunas, daí o `or "0"`.
        esquerda, _, direita = texto.partition(":")
        esquerda = "".join(c for c in esquerda if c.isdigit())
        direita = "".join(c for c in direita if c.isdigit())
        if not esquerda and not direita:
            return ""
        hora, minuto = int(esquerda or "0"), int(direita or "0")
    else:
        digitos = "".join(c for c in texto if c.isdigit())
        if not digitos:
            return ""
        if len(digitos) <= 2:        # "8" ou "19" = hora cheia
            hora, minuto = int(digitos), 0
        else:
            digitos = digitos[:4].rjust(4, "0")
            hora, minuto = int(digitos[:2]), int(digitos[2:])
    return f"{min(hora, 23):02d}:{min(minuto, 59):02d}"


def _icone_relogio(size: int = 14) -> QIcon:
    """Desenhado na cor da paleta ativa, como os pontos das listas."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    caneta = QPen(theme.current().ink_2)
    caneta.setWidthF(1.3)
    painter.setPen(caneta)
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(1, 1, size - 3, size - 3)
    meio = size / 2 - 0.5
    painter.drawLine(int(meio), int(meio), int(meio), 3)          # ponteiro
    painter.drawLine(int(meio), int(meio), size - 4, int(meio))
    painter.end()
    return QIcon(pixmap)


class HoraEdit(QWidget):
    """Horário em 'HH:MM', por digitação ou pelo seletor."""

    valueChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.edit = QLineEdit(self)
        # A máscara guia a digitação sem travá-la: os espaços em branco são
        # preenchidos por `normalizar` quando o campo perde o foco.
        self.edit.setInputMask("99:99")
        self.edit.setMaxLength(5)
        self.edit.setAlignment(Qt.AlignCenter)
        self.edit.setFixedWidth(58)
        self.edit.editingFinished.connect(self._arrumar)

        self.botao = QToolButton(self)
        self.botao.setIcon(_icone_relogio())
        self.botao.setAutoRaise(True)
        self.botao.setToolTip("Escolher o horário")
        self.botao.setPopupMode(QToolButton.InstantPopup)
        self.botao.setCursor(Qt.PointingHandCursor)

        self._menu = QMenu(self)
        self._painel = _PainelRelogio(self._menu)
        self._painel.escolhido.connect(self._do_relogio)
        self._painel.fechou.connect(self._menu.hide)
        acao = QWidgetAction(self._menu)
        acao.setDefaultWidget(self._painel)
        self._menu.addAction(acao)
        self._menu.aboutToShow.connect(self._preparar_painel)
        self.botao.setMenu(self._menu)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.edit)
        layout.addWidget(self.botao)
        layout.addStretch(1)

        self.setFocusProxy(self.edit)
        self.setValue(PADRAO)

    # ---------------------------------------------------------------- valor
    def value(self) -> str:
        return normalizar(self.edit.text()) or PADRAO

    def setValue(self, texto: str) -> None:
        hora = normalizar(texto) or PADRAO
        if hora == self.value() and self.edit.text().strip(":"):
            return
        self.edit.setText(hora)
        self._sincronizar_seletor(hora)

    # --------------------------------------------------------------- ações
    def _arrumar(self) -> None:
        """Completa o que ficou pela metade: '8' vira '08:00'."""
        hora = normalizar(self.edit.text())
        if not hora:
            hora = PADRAO
        if hora != self.edit.text():
            self.edit.setText(hora)
        self._sincronizar_seletor(hora)
        self.valueChanged.emit(hora)

    def _do_relogio(self, hora: str) -> None:
        if hora == normalizar(self.edit.text()):
            return
        self.edit.setText(hora)
        self.valueChanged.emit(hora)

    def _preparar_painel(self) -> None:
        """O mostrador abre sempre nas horas, mostrando o valor atual."""
        self._painel.definir(self.value())

    def _sincronizar_seletor(self, hora: str) -> None:
        self._painel.definir(hora)

    def setEnabled(self, on: bool) -> None:  # noqa: N802 (API do Qt)
        super().setEnabled(on)
        self.edit.setEnabled(on)
        self.botao.setEnabled(on)


class _PainelRelogio(QWidget):
    """Cabeçalho `HH : MM` sobre o mostrador, como no seletor do Android.

    O cabeçalho não é enfeite: é ele que diz qual parte está sendo escolhida e
    permite voltar para a hora depois de passar aos minutos, sem fechar e
    reabrir.
    """

    escolhido = Signal(str)
    fechou = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.relogio = relogio.Relogio(self)
        self.relogio.mudou.connect(self._atualizar)
        self.relogio.modo_mudou.connect(lambda _m: self._pintar_cabecalho())
        self.relogio.concluido.connect(self.fechou)

        self.lbl_hora = QLabel("22", self)
        self.lbl_min = QLabel("00", self)
        for rotulo, modo in ((self.lbl_hora, relogio.HORA),
                             (self.lbl_min, relogio.MINUTO)):
            rotulo.setAlignment(Qt.AlignCenter)
            rotulo.setCursor(Qt.PointingHandCursor)
            rotulo.setFixedWidth(46)
            rotulo.mousePressEvent = (
                lambda _e, m=modo: self.relogio.definir_modo(m))

        separador = QLabel(":", self)
        separador.setAlignment(Qt.AlignCenter)

        topo = QHBoxLayout()
        topo.setContentsMargins(0, 0, 0, 0)
        topo.setSpacing(2)
        topo.addStretch(1)
        topo.addWidget(self.lbl_hora)
        topo.addWidget(separador)
        topo.addWidget(self.lbl_min)
        topo.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)
        layout.addLayout(topo)
        layout.addWidget(self.relogio)
        self.setFixedSize(236, 272)
        self._pintar_cabecalho()

    def definir(self, hora_texto: str) -> None:
        hora, _, minuto = (normalizar(hora_texto) or PADRAO).partition(":")
        self.relogio.definir(int(hora), int(minuto))
        self.relogio.definir_modo(relogio.HORA)
        self._atualizar(int(hora), int(minuto))

    def _atualizar(self, hora: int, minuto: int) -> None:
        self.lbl_hora.setText(f"{hora:02d}")
        self.lbl_min.setText(f"{minuto:02d}")
        self._pintar_cabecalho()
        self.escolhido.emit(f"{hora:02d}:{minuto:02d}")

    def _pintar_cabecalho(self) -> None:
        for rotulo, modo in ((self.lbl_hora, relogio.HORA),
                             (self.lbl_min, relogio.MINUTO)):
            ativo = self.relogio.modo is modo
            rotulo.setProperty("role", "clockOn" if ativo else "clockOff")
            estilo = rotulo.style()
            estilo.unpolish(rotulo)
            estilo.polish(rotulo)
