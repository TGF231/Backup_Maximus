"""Abas Configurações e Rede.

Os layouts vivem em `designer/tab_settings.ui` e `designer/tab_network.ui`.
Aqui fica só o comportamento.

Configurações: tudo que vale para a máquina inteira, não para um conjunto
específico. A ordem dos campos conta uma história — quem somos, para quem
avisamos, quando reclamamos, por qual servidor.

Rede: uma credencial por compartilhamento, não por item. Cinco itens que gravam
em \\srv\backups compartilham uma entrada só; quando a senha do serviço muda,
você a troca num lugar.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QListWidgetItem, QWidget,
)

from PySide6.QtCore import QTime

from .. import mailer, reminder
from ..config import Config, NetCredential, protect_secret
from . import forms, password, profile_dialog, widgets
from .pathedit import PathKind, PathState


class SettingsTab(QWidget):
    dirty_changed = Signal()
    password_change_requested = Signal()
    shortcut_requested = Signal()

    def __init__(self, cfg: Config, app_dir: str):
        super().__init__()
        self.cfg = cfg
        self.app_dir = app_dir
        self._loading = False

        self.ui = forms.load("tab_settings")()
        self.ui.setupUi(self)
        self._adopt_widgets()
        self._load()
        self._wire()

    def _adopt_widgets(self) -> None:
        ui = self.ui
        self.company = ui.editCompany
        self.email = ui.editEmail
        self.timeout = ui.spinTimeout
        self.alert_hint = ui.lblAlertHint
        self.send_report = ui.chkSendReport
        self.smtp_host = ui.editSmtpHost
        self.smtp_port = ui.spinSmtpPort
        self.smtp_ssl = ui.chkSmtpSsl
        self.smtp_user = ui.editSmtpUser
        self.smtp_pass = ui.editSmtpPass
        self.smtp_from = ui.editSmtpFrom
        self.sevenzip = ui.editSevenZip
        self.sevenzip_hint = ui.lblSevenZipHint
        self.rclone = ui.editRclone
        self.reminder_time = ui.timeReminder
        self.reminder_on = ui.chkReminder
        self.reminder_hint = ui.lblReminderHint
        self.btn_test_mail = ui.btnTestMail
        self.btn_password = ui.btnChangePassword
        self.btn_shortcut = ui.btnShortcut

    # ---------------------------------------------------------------- dados
    def _load(self) -> None:
        self._loading = True
        cfg = self.cfg
        self.company.setText(cfg.company_name)
        self.email.setText(cfg.notify_email)
        self.timeout.setValue(cfg.alert_timeout_hours)
        self.send_report.setChecked(cfg.send_report_email)
        self.smtp_host.setText(cfg.smtp.host)
        self.smtp_port.setValue(cfg.smtp.port)
        self.smtp_ssl.setChecked(cfg.smtp.use_ssl)
        self.smtp_user.setText(cfg.smtp.user)
        self.smtp_pass.setText("")
        self.smtp_pass.setPlaceholderText(
            "•••••• (gravada)" if cfg.smtp.password_enc else ""
        )
        self.smtp_from.setText(cfg.smtp.sender)
        self.sevenzip.setText(cfg.sevenzip_path)
        self.rclone.setText(cfg.rclone_path)
        self.reminder_on.setChecked(cfg.reminder_enabled)
        hour, _, minute = cfg.reminder_time.partition(":")
        self.reminder_time.setTime(
            QTime(int(hour or 22), int(minute or 0)))
        self._loading = False
        self._update_alert_hint()
        self._update_reminder_hint()
        self.sevenzip.validate_now()
        self.rclone.validate_now()

    def _wire(self) -> None:
        for edit in (self.company, self.email, self.smtp_host, self.smtp_user,
                     self.smtp_pass, self.smtp_from, self.sevenzip, self.rclone):
            edit.textChanged.connect(self._changed)
        self.reminder_time.timeChanged.connect(self._changed)
        self.reminder_on.toggled.connect(self._changed)
        self.timeout.valueChanged.connect(self._changed)
        self.smtp_port.valueChanged.connect(self._changed)
        self.send_report.toggled.connect(self._changed)
        self.smtp_ssl.toggled.connect(self._changed)

        self.sevenzip.validated.connect(self._show_sevenzip_state)
        self.ui.btnBrowseSevenZip.clicked.connect(self._browse_7z)
        self.ui.btnBrowseRclone.clicked.connect(self._browse_rclone)
        self.btn_test_mail.clicked.connect(self._test_email)
        self.btn_password.clicked.connect(self.password_change_requested.emit)
        self.btn_shortcut.clicked.connect(self.shortcut_requested.emit)
        self.ui.btnExportProfile.clicked.connect(self._exportar_perfil)
        self.ui.btnImportProfile.clicked.connect(self._importar_perfil)

    def _changed(self, *_args) -> None:
        if self._loading:
            return
        cfg = self.cfg
        cfg.company_name = self.company.text().strip()
        cfg.notify_email = self.email.text().strip()
        cfg.alert_timeout_hours = self.timeout.value()
        cfg.send_report_email = self.send_report.isChecked()
        cfg.smtp.host = self.smtp_host.text().strip()
        cfg.smtp.port = self.smtp_port.value()
        cfg.smtp.use_ssl = self.smtp_ssl.isChecked()
        cfg.smtp.user = self.smtp_user.text().strip()
        if self.smtp_pass.text():
            cfg.smtp.password_enc = protect_secret(self.smtp_pass.text())
        cfg.smtp.sender = self.smtp_from.text().strip()
        cfg.sevenzip_path = self.sevenzip.text().strip()
        cfg.rclone_path = self.rclone.text().strip()
        cfg.reminder_enabled = self.reminder_on.isChecked()
        cfg.reminder_time = self.reminder_time.time().toString("HH:mm")
        self._update_alert_hint()
        self._update_reminder_hint()
        self.dirty_changed.emit()

    def _update_alert_hint(self) -> None:
        """A dica calcula a folga; não repete o rótulo do campo."""
        hours = self.timeout.value()
        if hours <= 24:
            self.alert_hint.setText(
                f"{hours} h é menor que um dia — uma rotina diária dispararia "
                f"alerta mesmo funcionando. Considere 26 h."
            )
        else:
            self.alert_hint.setText(
                f"Rotina diária às 22:00 → {hours} h dá {hours - 24} h de folga "
                f"antes de reclamar."
            )

    def _show_sevenzip_state(self, state: PathState, message: str) -> None:
        self.sevenzip_hint.setText(message)
        widgets.set_role(self.sevenzip_hint, {
            PathState.OK: "hintOk",
            PathState.WARN: "hintWarn",
            PathState.BAD: "hintBad",
        }.get(state, "hint"))

    def _update_reminder_hint(self) -> None:
        """O lembrete depende de uma tarefa no Agendador; a dica diz o estado."""
        if not self.reminder_on.isChecked():
            self.reminder_hint.setText(
                "Sem lembrete. A tarefa é removida do Agendador ao salvar."
            )
            return
        when = self.reminder_time.time().toString("HH:mm")
        installed = reminder.task_installed()
        self.reminder_hint.setText(
            f"Todo dia às {when} aparece uma notificação — e ela é dispensada "
            f"sozinha se o backup do dia já rodou. "
            + ("A tarefa já está no Agendador; salvar atualiza o horário."
               if installed else
               "A tarefa é registrada no Agendador do Windows ao salvar.")
        )

    def _browse_rclone(self) -> None:
        from PySide6.QtWidgets import QFileDialog as _QFD
        chosen, _ = _QFD.getOpenFileName(
            self, "Localizar rclone.exe", self.app_dir, "rclone.exe;;Todos (*.*)")
        if chosen:
            self.rclone.setText(os.path.normpath(chosen))

    def _browse_7z(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            self, "Localizar 7z.exe", r"C:\Program Files\7-Zip", "7z.exe;;Todos (*.*)"
        )
        if chosen:
            self.sevenzip.setText(os.path.normpath(chosen))

    def _test_email(self) -> None:
        self._changed()
        if not self.cfg.smtp.host:
            password.error(self, "Configure o servidor SMTP primeiro.")
            return
        if not self.cfg.notify_email:
            password.error(self, "Informe o e-mail de notificações primeiro.")
            return

        self.btn_test_mail.setEnabled(False)
        self.btn_test_mail.setText("Enviando…")
        try:
            ok, err = mailer.send_email(
                self.cfg.smtp, self.cfg.notify_email,
                "[Backup Maximus] Teste de e-mail",
                "Este é um e-mail de teste do Backup Maximus.\n"
                f"Empresa: {self.cfg.company_name}",
            )
        finally:
            self.btn_test_mail.setText("Testar e-mail")
            self.btn_test_mail.setEnabled(True)

        if ok:
            password.info(self, "E-mail de teste enviado com sucesso.",
                          f"Verifique a caixa de {self.cfg.notify_email}.")
        else:
            password.error(self, "Falha no envio.", err)

    # ------------------------------------------------ configurações prontas
    def _exportar_perfil(self) -> None:
        """Leva conjuntos e configurações para outra máquina.

        As senhas ficam para trás de propósito: o DPAPI as cifra com a chave
        deste usuário e desta máquina, então não decifrariam no destino.
        """
        profile_dialog.exportar(self.cfg, self.app_dir, self)

    def _importar_perfil(self) -> None:
        if profile_dialog.importar(self.cfg, self.app_dir, self):
            self.dirty_changed.emit()
            # Recarrega os campos: a importação pode ter trocado empresa,
            # e-mail e servidor de envio por baixo da tela aberta.
            self._load()


class NetworkTab(QWidget):
    dirty_changed = Signal()

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg

        self.ui = forms.load("tab_network")()
        self.ui.setupUi(self)

        self.listing = self.ui.listCreds
        self.unc = self.ui.editUnc
        self.user = self.ui.editNetUser
        self.password_field = self.ui.editNetPass
        self.btn_add = self.ui.btnCredAdd
        self.btn_del = self.ui.btnCredDel

        self.listing.setSelectionMode(QAbstractItemView.SingleSelection)
        self.listing.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listing.setTextElideMode(Qt.ElideRight)
        self.listing.currentRowChanged.connect(lambda _r: self._update_buttons())
        self.btn_add.clicked.connect(self._add)
        self.btn_del.clicked.connect(self._remove)

        self._refresh()

    def _refresh(self) -> None:
        self.listing.clear()
        for cred in self.cfg.net_creds:
            entry = QListWidgetItem(f"{cred.unc_root}      {cred.user}")
            entry.setIcon(widgets.dot_icon(widgets.DOT_OK))
            self.listing.addItem(entry)
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.btn_del.setEnabled(self.listing.currentRow() >= 0)

    def _add(self) -> None:
        unc = self.unc.text().strip()
        if not unc.startswith("\\\\"):
            password.error(self, "Informe o compartilhamento no formato "
                                 "\\\\servidor\\pasta.")
            self.unc.setFocus()
            return
        self.cfg.net_creds.append(NetCredential(
            unc_root=unc,
            user=self.user.text().strip(),
            password_enc=protect_secret(self.password_field.text()),
        ))
        self.unc.clear()
        self.user.clear()
        self.password_field.clear()
        self._refresh()
        self.dirty_changed.emit()

    def _remove(self) -> None:
        row = self.listing.currentRow()
        if row < 0:
            return
        cred = self.cfg.net_creds[row]
        if not password.confirm(self, f"Remover a credencial de {cred.unc_root}?",
                                "Backups que usam esse compartilhamento passam a "
                                "depender da sessão de rede já aberta no Windows."):
            return
        del self.cfg.net_creds[row]
        self._refresh()
        self.dirty_changed.emit()
