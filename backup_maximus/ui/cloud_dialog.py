"""Configuração do envio à nuvem de um conjunto.

Ficou num diálogo próprio, e não na aba, por uma razão prática: é configurado
uma vez e revisado raramente, ao contrário dos campos do item, que se editam o
tempo todo. Deixá-lo sempre na tela empurrava o formulário do item para fora da
área visível — e ver o item importa mais, todos os dias.
"""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QHeaderView, QTreeWidgetItem

from .. import cloud, cloud_setup, util
from ..config import BackupSet, Config
from . import cloud_setup_dialog, forms, password, widgets
from .pathedit import PathState

#: Primeira opção da lista. Escolhê-la desliga o envio do conjunto.
NO_CLOUD = "— não enviar —"


class CloudDialog(QDialog):
    def __init__(self, bset: BackupSet, cfg: Config, parent=None):
        super().__init__(parent)
        self.bset = bset
        self.cfg = cfg

        self.ui = forms.load("dialog_cloud")()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Envio à nuvem — {bset.name}")

        listing = self.ui.listing
        listing.header().setSectionResizeMode(0, QHeaderView.Stretch)
        listing.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        listing.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.ui.btnConfigure.clicked.connect(self._configure)
        self.ui.btnRemove.clicked.connect(self._remove_remote)
        self.ui.btnTest.clicked.connect(self._test)
        self.ui.btnOk.clicked.connect(self._apply)
        self.ui.btnCancel.clicked.connect(self.reject)
        self.ui.comboRemote.currentIndexChanged.connect(self._update_status)

        self._reload_remotes()
        self.ui.editPath.setText(bset.cloud_path)
        self.ui.spinKeep.setValue(bset.cloud_keep_last)
        self._update_status()

    # ------------------------------------------------------------- remotes
    def _reload_remotes(self) -> None:
        combo = self.ui.comboRemote
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(NO_CLOUD)
        for name in cloud.list_remotes(self.cfg.rclone_path):
            combo.addItem(name)

        wanted = self.bset.cloud_remote
        if wanted:
            index = combo.findText(wanted)
            if index < 0:
                # Um remote que sumiu (rclone reinstalado, perfil trocado) não
                # pode desaparecer calado da configuração.
                combo.addItem(wanted)
                index = combo.count() - 1
            combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _chosen(self) -> str:
        text = self.ui.comboRemote.currentText()
        return "" if text == NO_CLOUD else text

    def _set_status(self, state: PathState, message: str) -> None:
        self.ui.lblStatus.setText(message)
        widgets.set_role(self.ui.lblStatus, {
            PathState.OK: "hintOk",
            PathState.WARN: "hintWarn",
            PathState.BAD: "hintBad",
        }.get(state, "hint"))

    def _update_status(self) -> None:
        self.ui.listing.clear()

        if not cloud.available(self.cfg.rclone_path):
            self._set_status(PathState.WARN,
                             "rclone não encontrado — sem ele não há envio à "
                             "nuvem. Instale com 'winget install Rclone.Rclone' "
                             "ou coloque o rclone.exe em vendor\\rclone\\.")
            self.ui.btnTest.setEnabled(False)
            return

        self.ui.btnTest.setEnabled(True)
        remotes = cloud.list_remotes(self.cfg.rclone_path)
        chosen = self._chosen()

        if not chosen:
            if remotes:
                self._set_status(
                    PathState.NEUTRAL,
                    f"{len(remotes)} serviço(s) cadastrado(s). Enquanto nenhum "
                    f"estiver escolhido, o zip fica só no destino local.")
            else:
                self._set_status(
                    PathState.WARN,
                    "Nenhum serviço cadastrado. Use 'Adicionar…' para entrar no "
                    "Google Drive, OneDrive ou MEGA — o login é no navegador.")
            return

        # Um remote que a configuração guarda mas o rclone não conhece mais
        # (perfil trocado, rclone reinstalado) não pode aparecer como válido:
        # o backup falharia na primeira execução noturna sem ninguém saber.
        if chosen not in remotes:
            self._set_status(
                PathState.BAD,
                f"'{chosen}' não está cadastrado neste rclone. Escolha outro "
                f"serviço ou recadastre com 'Adicionar…' — do jeito que está, "
                f"o envio falharia.")
            return

        kind = cloud.describe_remote(chosen, self.cfg.rclone_path)
        self._set_status(PathState.OK, f"{chosen} — {kind}. O envio é confirmado: "
                                       f"o backup só conclui depois que o "
                                       f"arquivo chega.")

    # -------------------------------------------------------------- ações
    def _configure(self) -> None:
        """Cadastra um serviço pela nossa janela, sem console."""
        if not cloud.available(self.cfg.rclone_path):
            password.error(
                self, "rclone não encontrado.",
                r"Instale com 'winget install Rclone.Rclone' ou coloque o "
                r"rclone.exe em vendor\rclone\ ao lado do programa.")
            return

        novo = cloud_setup_dialog.add_remote(self.cfg, self)
        self._reload_remotes()
        if novo:
            index = self.ui.comboRemote.findText(novo)
            if index >= 0:
                self.ui.comboRemote.setCurrentIndex(index)
        self._update_status()

    def _remove_remote(self) -> None:
        """Remove um serviço cadastrado no rclone."""
        chosen = self._chosen()
        if not chosen:
            password.info(self, "Nenhum serviço escolhido.")
            return
        usado = [s.name for s in self.cfg.sets
                 if s.cloud_remote == chosen and s is not self.bset]
        detalhe = ("A credencial guardada pelo rclone é apagada. "
                   "Os arquivos já enviados permanecem na nuvem.")
        if usado:
            detalhe += (f" Atenção: também é usado por "
                        f"{', '.join(usado)} — esses conjuntos deixariam de enviar.")
        if not password.confirm(self, f"Remover o serviço '{chosen}'?", detalhe):
            return

        ok, message = cloud_setup.delete_remote(chosen, self.cfg.rclone_path)
        if not ok:
            password.error(self, "Não foi possível remover.", message)
            return
        if self.bset.cloud_remote == chosen:
            self.bset.cloud_remote = ""
        self._reload_remotes()
        self._update_status()
        password.info(self, message)

    def _test(self) -> None:
        """Confere que o serviço responde antes de confiar nele à noite."""
        chosen = self._chosen()
        if not chosen:
            self._reload_remotes()
            password.info(self, "Nenhum serviço escolhido.",
                          "A lista foi recarregada com os remotes do rclone.")
            return

        self.ui.btnTest.setEnabled(False)
        self.ui.btnTest.setText("Testando…")
        try:
            path = self.ui.editPath.text().strip()
            files = cloud.list_files(chosen, path, self.cfg.rclone_path)
            kind = cloud.describe_remote(chosen, self.cfg.rclone_path)
        finally:
            self.ui.btnTest.setText("Testar conexão")
            self.ui.btnTest.setEnabled(True)

        self._fill_listing(files)
        zips = [f for f in files if f.name.lower().endswith(".zip")]
        password.info(
            self, f"{kind} respondeu.",
            f"A pasta '{path or '(raiz)'}' tem {len(files)} arquivo(s), "
            f"sendo {len(zips)} zip(s)."
        )

    def _fill_listing(self, files) -> None:
        listing = self.ui.listing
        listing.clear()
        prefix = self.bset.name.lower()
        for entry in files:
            node = QTreeWidgetItem([
                entry.name,
                util.format_bytes(entry.size),
                entry.modified[:16].replace("T", " "),
            ])
            ours = entry.name.lower().startswith(prefix)
            node.setIcon(0, widgets.dot_icon(
                widgets.DOT_OK if ours else widgets.DOT_MUTED))
            if not ours:
                node.setToolTip(0, "Não é deste conjunto — o expurgo não toca "
                                   "neste arquivo.")
            listing.addTopLevelItem(node)

    def _apply(self) -> None:
        self.bset.cloud_remote = self._chosen()
        self.bset.cloud_path = self.ui.editPath.text().strip()
        self.bset.cloud_keep_last = self.ui.spinKeep.value()
        self.accept()


def configure(bset: BackupSet, cfg: Config, parent=None) -> bool:
    """Abre o diálogo. True se o conjunto foi alterado."""
    return CloudDialog(bset, cfg, parent).exec() == QDialog.Accepted


def summary(bset: BackupSet) -> str:
    """Uma linha para a aba mostrar sem gastar espaço com os campos."""
    if not bset.cloud_remote:
        return "Sem envio à nuvem."
    destination = f"{bset.cloud_remote}:{bset.cloud_path or ''}".rstrip(":")
    keep = (f" · mantém {bset.cloud_keep_last} lá"
            if bset.cloud_keep_last > 0 else "")
    return f"Envia para {destination}{keep}."
