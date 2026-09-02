"""Trava de senha da tela de configuração.

O layout vive em `designer/dialog_password.ui`. É um dos três modais que o
design admite (senha, confirmação de exclusão, resultado de teste). Nada que se
configure passa por diálogo.
"""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox

from .. import logger
from ..config import Config
from . import forms

MIN_LENGTH = 4


class PasswordDialog(QDialog):
    def __init__(self, cfg: Config, first_run: bool, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.first_run = first_run

        self.ui = forms.load("dialog_password")()
        self.ui.setupUi(self)

        self.setWindowTitle(
            "Backup Maximus — Definir senha" if first_run
            else "Backup Maximus — Acesso restrito"
        )

        # O .ui traz o formulário completo; o modo "já tem senha" esconde o que
        # só faz sentido na primeira execução.
        if first_run:
            self.ui.lblIntro.setText(
                "Primeira execução: defina a senha de acesso às configurações."
            )
        else:
            self.ui.lblIntroHint.hide()
            self.ui.lblConfirm.hide()
            self.ui.editConfirm.hide()

        self.ui.buttonBox.button(QDialogButtonBox.Ok).setText("OK")
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setProperty("role", "accent")
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.ui.buttonBox.accepted.connect(self._submit)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.ui.editPass.returnPressed.connect(self._submit)
        self.ui.editConfirm.returnPressed.connect(self._submit)
        self.ui.editPass.setFocus()
        self.adjustSize()

    def _fail(self, message: str) -> None:
        self.ui.lblError.setText(message)

    def _submit(self) -> None:
        entered = self.ui.editPass.text()

        if self.first_run:
            if len(entered) < MIN_LENGTH:
                self._fail(f"A senha deve ter pelo menos {MIN_LENGTH} caracteres.")
                return
            if entered != self.ui.editConfirm.text():
                self._fail("As senhas não conferem.")
                self.ui.editConfirm.selectAll()
                self.ui.editConfirm.setFocus()
                return
            self.cfg.set_password(entered)
            self.accept()
            return

        if self.cfg.check_password(entered):
            self.accept()
        else:
            logger.warn("Tentativa de acesso as configuracoes com senha incorreta.")
            self._fail("Senha incorreta.")
            self.ui.editPass.selectAll()
            self.ui.editPass.setFocus()


def prompt(cfg: Config, first_run: bool, parent=None) -> bool:
    """Mostra a trava. True se autenticou (ou definiu a senha)."""
    dialog = PasswordDialog(cfg, first_run, parent)
    return dialog.exec() == QDialog.Accepted


def confirm(parent, title: str, text: str) -> bool:
    box = QMessageBox(parent)
    box.setWindowTitle("Backup Maximus")
    box.setIcon(QMessageBox.Question)
    box.setText(title)
    box.setInformativeText(text)
    yes = box.addButton("Excluir", QMessageBox.YesRole)
    box.addButton("Cancelar", QMessageBox.RejectRole)
    box.setDefaultButton(yes)
    box.exec()
    return box.clickedButton() is yes


def info(parent, text: str, detail: str = "") -> None:
    box = QMessageBox(parent)
    box.setWindowTitle("Backup Maximus")
    box.setIcon(QMessageBox.Information)
    box.setText(text)
    if detail:
        box.setInformativeText(detail)
    box.exec()


def error(parent, text: str, detail: str = "") -> None:
    box = QMessageBox(parent)
    box.setWindowTitle("Backup Maximus")
    box.setIcon(QMessageBox.Warning)
    box.setText(text)
    if detail:
        box.setInformativeText(detail)
    box.exec()
