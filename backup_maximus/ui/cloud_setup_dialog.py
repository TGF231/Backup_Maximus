"""Assistente de cadastro de serviço de nuvem, sem console.

DORMENTE: nenhuma tela abre este assistente hoje, porque `cloud.ENVIO_POR_API`
está desligado — o Google exige um domínio verificado que a WalyTech ainda não
tem. O código e os testes ficam de pé de propósito: quando o interruptor voltar
a True, basta religar o botão que o abria. Apagar agora custaria refazer tudo.

O formulário é montado a partir do que o rclone diz sobre cada serviço, então
não há lista de campos escrita aqui para envelhecer a cada versão dele.

A única etapa fora desta janela é o consentimento no navegador — e é onde ele
deve acontecer: a senha do Google ou da Microsoft é digitada no site deles, não
num campo nosso.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QLabel, QLineEdit, QWidget,
)

from .. import cloud, cloud_setup, oauth_app
from ..config import Config
from . import forms, password, widgets
from .pathedit import PathState


class _AuthBridge(QObject):
    """Traz os avisos da thread do rclone para a thread da interface.

    A sessão de autorização roda fora da interface e chama os callbacks de lá;
    tocar em widgets a partir de outra thread trava o Qt de formas difíceis de
    diagnosticar. O sinal faz a travessia.
    """
    link_ready = Signal(str)
    finished = Signal(bool, str)


class CloudSetupDialog(QDialog):
    def __init__(self, cfg: Config, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.providers: list[cloud_setup.Provider] = []
        self.session: cloud_setup.AuthorizeSession | None = None
        self.token: str = ""
        self.created_name: str = ""
        self._field_widgets: dict[str, QWidget] = {}
        #: Enquanto falso, o nome interno acompanha o serviço escolhido.
        self._name_touched = False

        self.ui = forms.load("dialog_cloud_setup")()
        self.ui.setupUi(self)

        self.bridge = _AuthBridge()
        self.bridge.link_ready.connect(self._on_link)
        self.bridge.finished.connect(self._on_auth_finished)

        self.ui.comboProvider.currentIndexChanged.connect(self._on_provider_changed)
        self.ui.btnAuthorize.clicked.connect(self._start_authorize)
        self.ui.btnOpenAgain.clicked.connect(self._open_link)
        self.ui.btnCopyLink.clicked.connect(self._copy_link)
        self.ui.btnCancelAuth.clicked.connect(self._cancel_authorize)
        self.ui.btnSave.clicked.connect(self._save)
        self.ui.btnClose.clicked.connect(self.reject)
        self.ui.chkOwnKey.toggled.connect(self._on_own_key_toggled)
        self.ui.editName.textEdited.connect(self._on_name_edited)
        self.ui.editName.textChanged.connect(lambda _t: self._update_save())

        self.ui.keyBox.setVisible(False)
        self._set_link_buttons(False)
        self._load_providers()

    # ------------------------------------------------------------ provedores
    def _load_providers(self) -> None:
        self.providers = cloud_setup.list_providers(self.cfg.rclone_path)
        if not self.providers:
            self._result(PathState.BAD,
                         "Não foi possível ler a lista de serviços do rclone. "
                         "Confira se ele está instalado.")
            self.ui.comboProvider.setEnabled(False)
            self.ui.btnSave.setEnabled(False)
            return

        self.ui.comboProvider.blockSignals(True)
        for provider in self.providers:
            self.ui.comboProvider.addItem(provider.label, provider.name)
        self.ui.comboProvider.blockSignals(False)
        self._on_provider_changed()

    def _on_own_key_toggled(self, marcado: bool) -> None:
        self.ui.keyBox.setVisible(marcado)
        if not marcado:
            self.ui.editClientId.clear()
            self.ui.editClientSecret.clear()
        # A chave vale desde a autorização, então trocá-la invalida o que já
        # foi autorizado: o token pertence ao aplicativo que o pediu.
        self.token = ""
        self._update_save()

    def _own_key(self) -> tuple[str, str]:
        """Chave digitada aqui, se houver — ela vence a embutida."""
        if not self.ui.chkOwnKey.isChecked():
            return "", ""
        return (self.ui.editClientId.text().strip(),
                self.ui.editClientSecret.text().strip())

    def _key_for(self, provider: cloud_setup.Provider) -> tuple[str, str]:
        propria = self._own_key()
        return propria if propria[0] else oauth_app.credentials(provider.name)

    def _update_key_warning(self, provider: cloud_setup.Provider) -> None:
        """Diz a verdade sobre qual chave será usada, antes do login.

        Sem isso, o cadastro pareceria correto e só falharia meses depois,
        quando o Google desligasse a chave compartilhada do rclone.
        """
        if not provider.uses_oauth:
            self.ui.lblKeyWarn.setText("")
            return
        if self._key_for(provider)[0]:
            self.ui.lblKeyWarn.setText("")
            widgets.set_role(self.ui.lblKeyWarn, "hint")
            return
        if oauth_app.needs_own_key(provider.name):
            self.ui.lblKeyWarn.setText(
                "Sem chave de API própria, este serviço usa a chave "
                "compartilhada do rclone — que o Google está desativando. "
                "O cadastro funciona hoje, mas pode parar de funcionar.")
            widgets.set_role(self.ui.lblKeyWarn, "hintWarn")
        else:
            self.ui.lblKeyWarn.setText("")

    def _on_name_edited(self, _text: str) -> None:
        self._name_touched = True

    def _suggest_name(self, provider: cloud_setup.Provider) -> str:
        """Sugere um nome livre: drive, drive2, drive3…"""
        existentes = set(cloud.list_remotes(self.cfg.rclone_path))
        base = provider.name
        if base not in existentes:
            return base
        for n in range(2, 100):
            if f"{base}{n}" not in existentes:
                return f"{base}{n}"
        return base

    def _current_provider(self) -> cloud_setup.Provider | None:
        index = self.ui.comboProvider.currentIndex()
        if 0 <= index < len(self.providers):
            return self.providers[index]
        return None

    def _on_provider_changed(self) -> None:
        self._cancel_authorize(quiet=True)
        self.token = ""
        provider = self._current_provider()
        if provider is None:
            return

        # O nome segue o serviço escolhido até alguém digitar o seu próprio:
        # trocar de serviço não pode deixar para trás um nome que não combina.
        if not self._name_touched:
            self.ui.editName.setText(self._suggest_name(provider))

        if provider.uses_oauth:
            self.ui.lblStepHeader.setText("ACESSO — LOGIN NO NAVEGADOR")
            self.ui.stack.setCurrentWidget(self.ui.pageOauth)
            self.ui.lblOauthStatus.setText("")
            self.ui.btnAuthorize.setEnabled(True)
            self._set_link_buttons(False)
            self._update_key_warning(provider)
        else:
            self.ui.lblStepHeader.setText("ACESSO — DADOS DA CONTA")
            self.ui.stack.setCurrentWidget(self.ui.pageFields)
            self._build_fields(provider)

        self._result(PathState.NEUTRAL, "")
        self._update_save()

    # ---------------------------------------------------- formulário dinâmico
    def _build_fields(self, provider: cloud_setup.Provider) -> None:
        """Monta os campos que o serviço pede, conforme o rclone os descreve."""
        grid = self.ui.gridFields
        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # setParent(None) tira da grade agora; deleteLater só agenda a
                # destruição, e os campos antigos continuariam ocupando as
                # células — os novos apareceriam desenhados por cima.
                widget.setParent(None)
                widget.deleteLater()
        self._field_widgets.clear()

        options = provider.basic_options()
        if not options:
            grid.addWidget(widgets.hint_label(
                f"O {provider.description} não pede nenhum dado obrigatório. "
                f"Clique em Cadastrar."), 0, 0, 1, 2)
            return

        row = 0
        for option in options:
            label = widgets.field_label(option.label)
            grid.addWidget(label, row, 0)

            widget = self._widget_for(option)
            grid.addWidget(widget, row, 1)
            self._field_widgets[option.name] = widget
            row += 1

            hint = option.first_line
            if hint:
                grid.addWidget(widgets.hint_label(hint), row, 1)
                row += 1

        grid.setRowStretch(row, 1)

    def _widget_for(self, option: cloud_setup.ProviderOption) -> QWidget:
        if option.type == "bool":
            box = QCheckBox()
            box.setChecked(option.default.lower() in ("true", "1", "yes"))
            box.toggled.connect(lambda _c: self._update_save())
            return box

        if option.examples and option.type == "string":
            combo = QComboBox()
            combo.setEditable(True)
            for value, help_text in option.examples:
                combo.addItem(f"{value}" + (f"  ({help_text})" if help_text else ""),
                              value)
            combo.setCurrentText(option.default)
            combo.currentTextChanged.connect(lambda _t: self._update_save())
            return combo

        edit = QLineEdit()
        if option.is_password or option.sensitive:
            edit.setEchoMode(QLineEdit.Password)
        if option.default:
            edit.setPlaceholderText(f"padrão: {option.default}")
        edit.textChanged.connect(lambda _t: self._update_save())
        return edit

    def _field_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for name, widget in self._field_widgets.items():
            if isinstance(widget, QCheckBox):
                values[name] = "true" if widget.isChecked() else "false"
            elif isinstance(widget, QComboBox):
                # O texto pode ter vindo do item ("valor  (ajuda)") ou digitado.
                data = widget.currentData()
                text = widget.currentText()
                values[name] = data if data and text.startswith(str(data)) else text
            elif isinstance(widget, QLineEdit):
                values[name] = widget.text().strip()
        return values

    # ------------------------------------------------------------ autorização
    def _start_authorize(self) -> None:
        provider = self._current_provider()
        if provider is None:
            return

        client_id, client_secret = self._key_for(provider)
        if client_id and not client_secret:
            self._auth_status(PathState.BAD,
                              "Informe também o segredo do cliente — o serviço "
                              "recusa a chave pela metade.")
            return

        self.token = ""
        self.session = cloud_setup.AuthorizeSession(
            provider.name, self.cfg.rclone_path, client_id, client_secret)
        self.ui.btnAuthorize.setEnabled(False)
        self.ui.lblOauthStatus.setText("Preparando a autorização…")
        widgets.set_role(self.ui.lblOauthStatus, "hint")

        started = self.session.start(
            on_link=self.bridge.link_ready.emit,
            on_finish=lambda ok, msg: self.bridge.finished.emit(ok, msg),
        )
        if not started:
            self.ui.btnAuthorize.setEnabled(True)
            self._auth_status(PathState.BAD, self.session.error)
            self.session = None

    def _on_link(self, url: str) -> None:
        self._set_link_buttons(True)
        self._auth_status(
            PathState.WARN,
            "Abrimos a página de autorização no seu navegador. Entre na conta e "
            "confirme o acesso — esta janela avisa quando terminar."
        )
        self._open_link()

    def _open_link(self) -> None:
        if self.session and self.session.link:
            QDesktopServices.openUrl(QUrl(self.session.link))

    def _copy_link(self) -> None:
        if self.session and self.session.link:
            QApplication.clipboard().setText(self.session.link)
            password.info(self, "Link copiado.",
                          "Cole no navegador onde você está logado na conta.")

    def _cancel_authorize(self, quiet: bool = False) -> None:
        if self.session is not None:
            self.session.cancel()
            self.session = None
        self._set_link_buttons(False)
        self.ui.btnAuthorize.setEnabled(True)
        if not quiet:
            self._auth_status(PathState.NEUTRAL, "Autorização cancelada.")

    def _on_auth_finished(self, ok: bool, message: str) -> None:
        self._set_link_buttons(False)
        self.ui.btnAuthorize.setEnabled(True)
        if ok and self.session is not None:
            self.token = self.session.token
            self._auth_status(PathState.OK,
                              "Autorizado. Clique em Cadastrar para concluir.")
        else:
            self.token = ""
            self._auth_status(PathState.BAD, message)
        self._update_save()

    def _set_link_buttons(self, visible: bool) -> None:
        for button in (self.ui.btnOpenAgain, self.ui.btnCopyLink,
                       self.ui.btnCancelAuth):
            button.setVisible(visible)

    def _auth_status(self, state: PathState, message: str) -> None:
        self.ui.lblOauthStatus.setText(message)
        widgets.set_role(self.ui.lblOauthStatus, {
            PathState.OK: "hintOk",
            PathState.WARN: "hintWarn",
            PathState.BAD: "hintBad",
        }.get(state, "hint"))

    # ---------------------------------------------------------------- salvar
    def _result(self, state: PathState, message: str) -> None:
        self.ui.lblResult.setText(message)
        widgets.set_role(self.ui.lblResult, {
            PathState.OK: "hintOk",
            PathState.WARN: "hintWarn",
            PathState.BAD: "hintBad",
        }.get(state, "hint"))

    def _update_save(self) -> None:
        provider = self._current_provider()
        if provider is None:
            self.ui.btnSave.setEnabled(False)
            return

        has_name = bool(self.ui.editName.text().strip())
        if provider.uses_oauth:
            self.ui.btnSave.setEnabled(has_name and bool(self.token))
            return

        # Sem OAuth, o botão espera os campos obrigatórios preenchidos.
        values = self._field_values()
        faltando = [o.name for o in provider.basic_options()
                    if not values.get(o.name, "").strip()]
        self.ui.btnSave.setEnabled(has_name and not faltando)

    def _save(self) -> None:
        provider = self._current_provider()
        if provider is None:
            return

        name = self.ui.editName.text().strip()
        values = self._field_values() if not provider.uses_oauth else {}

        # A chave digitada aqui tem de ser gravada no remote: o token só é
        # aceito pelo mesmo aplicativo que pediu o consentimento.
        client_id, client_secret = self._own_key()
        if client_id:
            values["client_id"] = client_id
            values["client_secret"] = client_secret

        self.ui.btnSave.setEnabled(False)
        self.ui.btnSave.setText("Cadastrando…")
        try:
            ok, message = cloud_setup.create_remote(
                name, provider.name, values, self.token, self.cfg.rclone_path)
        finally:
            self.ui.btnSave.setText("Cadastrar")
            self.ui.btnSave.setEnabled(True)

        if not ok:
            self._result(PathState.BAD, message)
            return

        # Confirma que o serviço responde antes de dizer que deu certo: um
        # remote que existe no arquivo mas não conecta não serve para nada.
        self._result(PathState.NEUTRAL, "Cadastrado. Testando o acesso…")
        QApplication.processEvents()
        files = cloud.list_files(name, "", self.cfg.rclone_path)
        kind = cloud.describe_remote(name, self.cfg.rclone_path)

        self.created_name = name
        password.info(
            self, f"{kind} cadastrado como '{name}'.",
            f"A raiz do serviço respondeu com {len(files)} item(ns). "
            f"Agora escolha-o no conjunto e informe a pasta de destino."
        )
        self.accept()

    def closeEvent(self, event) -> None:
        self._cancel_authorize(quiet=True)
        event.accept()


def add_remote(cfg: Config, parent=None) -> str:
    """Abre o assistente. Devolve o nome cadastrado, ou string vazia."""
    dialog = CloudSetupDialog(cfg, parent)
    if dialog.exec() != QDialog.Accepted:
        return ""
    return dialog.created_name
