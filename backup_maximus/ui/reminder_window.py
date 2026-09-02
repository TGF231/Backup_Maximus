"""Janela e notificação do lembrete de backup.

A notificação da bandeja é o caminho principal — é o que o Windows entende por
"notificação" e não rouba o foco de quem está no meio de uma venda. Mas balão de
bandeja é silenciosamente descartado em várias situações (bandeja oculta, modo
foco, política de grupo), e um lembrete que some sem avisar é pior do que não
existir. Por isso há também uma janelinha, que aparece se a bandeja falhar ou se
o balão não for clicado.
"""

from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPushButton, QSystemTrayIcon,
    QVBoxLayout, QWidget,
)

from ..config import Config
from . import theme

#: Quanto a janela espera antes de desistir sozinha. O lembrete não pode virar
#: um diálogo travado numa máquina de PDV sem ninguém por perto.
AUTO_CLOSE_SECONDS = 120


def _app_icon() -> QIcon:
    """Ícone da bandeja, desenhado na cor de acento da paleta ativa."""
    palette = theme.current()
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(palette.accent))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(3, 3, 26, 26, 6, 6)
    painter.setBrush(QColor(palette.on_accent))
    for row in range(3):
        painter.drawRoundedRect(8, 9 + row * 6, 16, 3, 1, 1)
    painter.end()
    return QIcon(pixmap)


def _run_backup_now() -> None:
    """Dispara o mesmo modo /run do atalho da área de trabalho."""
    from ..paths import frozen, install_dir
    try:
        if frozen():
            args = [sys.executable, "/run"]
        else:
            args = [sys.executable.replace("python.exe", "pythonw.exe"),
                    "-m", "backup_maximus", "/run"]
        subprocess.Popen(args, cwd=install_dir(), close_fds=True)
    except OSError:
        pass


class ReminderWindow(QWidget):
    def __init__(self, headline: str, detail: str):
        super().__init__()
        self.ran = False

        self.setWindowTitle("Backup Maximus — Lembrete")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setFixedWidth(430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)

        title = QLabel(headline)
        title.setProperty("role", "bigStatus")
        title.setWordWrap(True)
        title.setStyleSheet(f"color: {theme.current().accent}; font-weight: 600;")
        layout.addWidget(title)

        body = QLabel(detail)
        body.setWordWrap(True)
        layout.addWidget(body)

        self.countdown = QLabel()
        self.countdown.setProperty("role", "hint")
        layout.addWidget(self.countdown)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch(1)

        later = QPushButton("Agora não")
        later.clicked.connect(self.close)
        buttons.addWidget(later)

        run_now = QPushButton("Fazer backup agora")
        run_now.setProperty("role", "accent")
        run_now.setCursor(Qt.PointingHandCursor)
        run_now.clicked.connect(self._run)
        buttons.addWidget(run_now)
        layout.addLayout(buttons)

        run_now.setFocus()

        self._left = AUTO_CLOSE_SECONDS
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

    def _tick(self) -> None:
        self._left -= 1
        if self._left <= 0:
            self.close()
            return
        self.countdown.setText(f"Esta janela fecha sozinha em {self._left}s.")

    def _run(self) -> None:
        self.ran = True
        _run_backup_now()
        self.close()


def show(cfg: Config, headline: str, detail: str) -> int:
    """Mostra o lembrete. Devolve 0 sempre — lembrete não é falha."""
    app = QApplication.instance() or QApplication([])
    theme.set_dark(cfg.dark_theme)
    app.setStyleSheet(theme.stylesheet())

    window = ReminderWindow(headline, detail)
    tray: QSystemTrayIcon | None = None

    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(_app_icon())
        tray.setToolTip("Backup Maximus")
        tray.show()
        tray.showMessage(headline, detail, _app_icon(), 15000)
        # Clicar no balão ou no ícone abre a janela com os botões: o balão
        # informa, mas não dá o que fazer a respeito.
        tray.messageClicked.connect(window.show)
        tray.activated.connect(lambda _r: window.show())
        # A janela aparece junto quando a bandeja não é confiável para agir.
        QTimer.singleShot(1200, window.show)
    else:
        window.show()

    app.exec()
    if tray is not None:
        tray.hide()
    return 0
