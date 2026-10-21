r"""Seletor de horário em mostrador de relógio.

Dois passos, como nos seletores de hora do Android e do Material: o primeiro
clique escolhe a hora, o mostrador troca para os minutos, o segundo clique
fecha. Quem errou volta clicando na parte correspondente do cabeçalho.

As 24 horas cabem em dois anéis concêntricos, que é como se resolve mostrar 24
posições num mostrador de 12: o anel de fora leva `00` e `13`–`23`, o de
dentro leva `12` e `1`–`11`. Assim o ponteiro aponta para o mesmo lugar do
relógio de parede, e a volta da tarde fica por fora.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from . import theme

HORA, MINUTO = "hora", "minuto"

#: Minutos marcados com número; os demais só aceitam o clique.
PASSO_ROTULO = 5


def _valor_hora(posicao: int, externo: bool) -> int:
    """Hora no mostrador. `posicao` 0..11 a partir do topo, sentido horário."""
    if externo:
        return 0 if posicao == 0 else 12 + posicao
    return 12 if posicao == 0 else posicao


def _posicao_da_hora(hora: int) -> tuple[int, bool]:
    """Inverso de `_valor_hora`: (posição, está no anel de fora)."""
    if hora == 0:
        return 0, True
    if hora == 12:
        return 0, False
    if hora > 12:
        return hora - 12, True
    return hora, False


class Relogio(QWidget):
    """Mostrador de horas e minutos. Emite `concluido` ao fechar a escolha."""

    #: (hora, minuto) a cada clique, para o cabeçalho acompanhar.
    mudou = Signal(int, int)
    #: Emitido quando o minuto foi escolhido — o chamador fecha o popup.
    concluido = Signal()
    #: Modo atual, para o cabeçalho destacar a parte certa.
    modo_mudou = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hora = 22
        self.minuto = 0
        self.modo = HORA
        self.setMinimumSize(QSize(210, 210))
        self.setMouseTracking(True)
        self._sob_cursor: tuple[int, bool] | None = None

    # ---------------------------------------------------------------- valor
    def definir(self, hora: int, minuto: int) -> None:
        self.hora = max(0, min(23, hora))
        self.minuto = max(0, min(59, minuto))
        self.update()

    def definir_modo(self, modo: str) -> None:
        if modo == self.modo:
            return
        self.modo = modo
        self._sob_cursor = None
        self.modo_mudou.emit(modo)
        self.update()

    # -------------------------------------------------------------- desenho
    def _geometria(self) -> tuple[QPoint, float, float, float]:
        lado = min(self.width(), self.height())
        centro = QPoint(self.width() // 2, self.height() // 2)
        raio = lado / 2 - 6
        # O anel interno só existe nas horas; nos minutos o mostrador é um só.
        externo = raio - 16
        interno = externo - 30 if self.modo is HORA else externo
        return centro, raio, externo, interno

    def _ponto(self, centro: QPoint, raio: float, posicao: float,
               total: int) -> QPoint:
        angulo = math.radians(posicao * (360 / total) - 90)
        return QPoint(int(centro.x() + raio * math.cos(angulo)),
                      int(centro.y() + raio * math.sin(angulo)))

    def paintEvent(self, _evento) -> None:
        p = theme.current()
        centro, raio, r_ext, r_int = self._geometria()

        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)

        # Mostrador
        pintor.setPen(Qt.NoPen)
        pintor.setBrush(QColor(p.sunken))
        pintor.drawEllipse(centro, int(raio), int(raio))

        if self.modo is HORA:
            selecionado = _posicao_da_hora(self.hora)
            self._desenhar_ponteiro(pintor, centro,
                                    r_ext if selecionado[1] else r_int,
                                    selecionado[0], 12)
            for posicao in range(12):
                for externo in (True, False):
                    valor = _valor_hora(posicao, externo)
                    # O anel de dentro e o mostrador comum: "3", nao "03".
                    # Dois digitos ficam so no de fora, onde todos tem dois.
                    texto = f"{valor:02d}" if externo else str(valor)
                    self._desenhar_numero(
                        pintor, centro, r_ext if externo else r_int, posicao, 12,
                        texto, valor == self.hora, pequeno=not externo)
        else:
            self._desenhar_ponteiro(pintor, centro, r_ext, self.minuto, 60)
            for minuto in range(0, 60, PASSO_ROTULO):
                self._desenhar_numero(
                    pintor, centro, r_ext, minuto, 60, f"{minuto:02d}",
                    minuto == self.minuto)
            if self.minuto % PASSO_ROTULO:
                # Minuto fora das marcas: só o disco, sem número sobreposto.
                self._desenhar_numero(pintor, centro, r_ext, self.minuto, 60,
                                      "", True)

        pintor.end()

    def _desenhar_ponteiro(self, pintor, centro, raio, posicao, total) -> None:
        p = theme.current()
        destino = self._ponto(centro, raio, posicao, total)
        caneta = QPen(QColor(p.accent))
        caneta.setWidth(2)
        pintor.setPen(caneta)
        pintor.drawLine(centro, destino)
        pintor.setPen(Qt.NoPen)
        pintor.setBrush(QColor(p.accent))
        pintor.drawEllipse(centro, 3, 3)

    def _desenhar_numero(self, pintor, centro, raio, posicao, total,
                         texto: str, ativo: bool, pequeno: bool = False) -> None:
        p = theme.current()
        meio = self._ponto(centro, raio, posicao, total)
        caixa = QRect(meio.x() - 13, meio.y() - 13, 26, 26)

        if ativo:
            pintor.setPen(Qt.NoPen)
            pintor.setBrush(QColor(p.accent))
            pintor.drawEllipse(caixa)
        elif self._sob_cursor == (posicao, pequeno is False):
            pintor.setPen(Qt.NoPen)
            pintor.setBrush(QColor(p.accent_soft))
            pintor.drawEllipse(caixa)

        if not texto:
            return
        fonte = QFont(self.font())
        fonte.setPointSize(8 if pequeno else 9)
        pintor.setFont(fonte)
        pintor.setPen(QColor(p.on_accent if ativo
                             else (p.ink_3 if pequeno else p.ink)))
        pintor.drawText(caixa, Qt.AlignCenter, texto)

    # --------------------------------------------------------------- mouse
    def _alvo(self, ponto: QPoint) -> tuple[int, bool] | None:
        centro, raio, r_ext, r_int = self._geometria()
        dx, dy = ponto.x() - centro.x(), ponto.y() - centro.y()
        distancia = math.hypot(dx, dy)
        if distancia > raio + 4:
            return None

        total = 12 if self.modo is HORA else 60
        angulo = (math.degrees(math.atan2(dy, dx)) + 90) % 360
        posicao = round(angulo / (360 / total)) % total

        if self.modo is MINUTO:
            return posicao, True
        # O ponto médio entre os anéis decide a qual deles o clique pertence.
        return posicao, distancia > (r_ext + r_int) / 2

    def mouseMoveEvent(self, evento) -> None:
        alvo = self._alvo(evento.position().toPoint())
        if alvo != self._sob_cursor:
            self._sob_cursor = alvo
            self.setCursor(Qt.PointingHandCursor if alvo else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, _evento) -> None:
        self._sob_cursor = None
        self.update()

    def mouseReleaseEvent(self, evento) -> None:
        alvo = self._alvo(evento.position().toPoint())
        if alvo is None:
            return
        posicao, externo = alvo

        if self.modo is HORA:
            self.hora = _valor_hora(posicao, externo)
            self.mudou.emit(self.hora, self.minuto)
            # Trocar para os minutos é o que faz o seletor avançar sozinho;
            # sem isso o usuário teria de descobrir onde clicar em seguida.
            self.definir_modo(MINUTO)
        else:
            self.minuto = posicao
            self.mudou.emit(self.hora, self.minuto)
            self.update()
            self.concluido.emit()
