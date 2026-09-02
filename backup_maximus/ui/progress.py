"""Janela do Quick Run — o que o atalho da área de trabalho abre.

O layout vive em `designer/window_progress.ui`.

Sem senha, sem abas, sem chance de alguém "dar uma olhadinha" na configuração.
Três informações: o que está acontecendo, quanto já andou, há quanto tempo.

O backup roda numa thread de trabalho; o progresso chega por sinal do Qt, então
a janela nunca congela.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import QApplication, QWidget

from ..config import Config
from ..engine import Phase, RunResult, run_backups
from . import forms, theme


class _Worker(QObject):
    """Executa o backup fora da thread da interface."""

    progress = Signal(object, int, str)   # (Phase, pct, mensagem)
    finished = Signal(object)             # RunResult

    def __init__(self, cfg: Config, cfg_path: str, app_dir: str):
        super().__init__()
        self.cfg = cfg
        self.cfg_path = cfg_path
        self.app_dir = app_dir
        self._cancel = False

    def request_cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        def on_progress(phase: Phase, pct: int, message: str) -> bool:
            self.progress.emit(phase, pct, message)
            return not self._cancel

        result = run_backups(self.cfg, self.cfg_path, self.app_dir, on_progress)
        self.finished.emit(result)


class ProgressWindow(QWidget):
    def __init__(self, cfg: Config, cfg_path: str, app_dir: str):
        super().__init__()
        self.result: RunResult | None = None
        self.done = False
        self.waiting = False
        self._started = time.monotonic()

        self.ui = forms.load("window_progress")()
        self.ui.setupUi(self)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.bar = self.ui.bar
        self.label_status = self.ui.lblStatus
        self.label_time = self.ui.lblTime
        self.btn_cancel = self.ui.btnCancel
        self.btn_close = self.ui.btnClose

        # Cancelar só existe enquanto espera a unidade: abortar no meio deixaria
        # um zip pela metade, indistinguível de um backup bom. Fechar só no fim.
        self.btn_cancel.hide()
        self.btn_close.hide()
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_close.clicked.connect(self.close)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(500)

        self.thread = QThread(self)
        self.worker = _Worker(cfg, cfg_path, app_dir)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.thread.start()

    # ------------------------------------------------------------- eventos
    def _tick(self) -> None:
        if not self.done:
            elapsed = int(time.monotonic() - self._started)
            self.label_time.setText(f"Tempo: {elapsed} s")

    def _set_waiting(self, waiting: bool) -> None:
        if waiting == self.waiting:
            return
        self.waiting = waiting
        self.btn_cancel.setVisible(waiting)
        if waiting:
            # Modo indeterminado: não sabemos quanto falta e fingir uma
            # porcentagem seria inventar.
            self.bar.setRange(0, 0)
            self.setWindowTitle("Backup Maximus — Aguardando unidade de backup")
        else:
            self.bar.setRange(0, 100)
            self.setWindowTitle("Backup Maximus — Executando backup…")

    def _on_progress(self, phase: Phase, pct: int, message: str) -> None:
        self._set_waiting(phase is Phase.WAITING_DRIVE)
        if not self.waiting:
            self.bar.setValue(pct)
        self.label_status.setText(message)

    def _on_finished(self, result: RunResult) -> None:
        self.result = result
        self.done = True
        self.timer.stop()
        self._set_waiting(False)
        self.btn_cancel.hide()

        self.bar.setRange(0, 100)
        self.bar.setValue(100)
        self.bar.setProperty("state", "ok" if result.all_ok else "bad")
        self.bar.style().unpolish(self.bar)
        self.bar.style().polish(self.bar)

        elapsed = int(time.monotonic() - self._started)
        self.label_time.setText(f"Concluído em {elapsed} s")
        self.label_status.setText(result.summary)
        palette = theme.current()
        self.label_status.setStyleSheet(
            f"color: {palette.ok if result.all_ok else palette.bad}; font-weight: 600;"
        )

        # A falha se anuncia em três canais: cor da barra, texto e o título da
        # janela — que é o que a pessoa lê com a janela minimizada.
        self.setWindowTitle(
            "Backup Maximus — SUCESSO" if result.all_ok
            else "Backup Maximus — CONCLUÍDO COM FALHAS"
        )

        self.btn_close.show()
        self.btn_close.setFocus()
        QApplication.alert(self)

        self.thread.quit()
        self.thread.wait(5000)

    def _cancel(self) -> None:
        self.worker.request_cancel()
        self.label_status.setText("Cancelando…")
        self.btn_cancel.setEnabled(False)

    def closeEvent(self, event) -> None:
        if not self.done:
            if self.waiting:
                self._cancel()
            event.ignore()
            return
        event.accept()


def run(cfg: Config, cfg_path: str, app_dir: str) -> int:
    """Abre a janela e devolve o código de saída (0 = tudo certo)."""
    app = QApplication.instance() or QApplication([])
    theme.set_dark(cfg.dark_theme)
    app.setStyleSheet(theme.stylesheet())
    window = ProgressWindow(cfg, cfg_path, app_dir)
    window.show()
    app.exec()
    return 0 if (window.result and window.result.all_ok) else 1
