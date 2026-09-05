r"""Backup na nuvem pela pasta de um cliente de sincronização.

O envio direto pela API está suspenso — ver `cloud.ENVIO_POR_API`, que explica
o porquê e é o único interruptor. Enquanto isso, a via para a nuvem é a que
sempre funcionou sem depender de nada: gravar o zip numa pasta que o OneDrive,
o Google Drive, o Dropbox ou o MEGA já sincronizam.

Esta janela existe para tornar esse caminho **descobrível**. Sem ela, o botão
"Nuvem…" viraria um beco sem saída anunciando um recurso futuro, e o operador
teria de saber por conta própria que colar `C:\Users\fulano\OneDrive\...`
no campo de destino faz o backup ir para a nuvem.

A diferença em relação ao envio por API é honesta e está dita na tela: aqui o
backup conclui quando o zip toca o disco, e quem envia é o cliente de
sincronização, depois — sem ninguém conferir se chegou.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHeaderView, QTreeWidgetItem

from .. import cloud, util
from ..config import BackupSet, Config
from . import forms, password, widgets
from .pathedit import PathState

#: Subpasta criada dentro da pasta sincronizada. Separar por conjunto evita que
#: dois conjuntos disputem o mesmo lugar e que o expurgo de um apague o zip do
#: outro — a retenção casa os arquivos pelo prefixo do nome.
SUBPASTA = "Backup Maximus"


class CloudDialog(QDialog):
    def __init__(self, bset: BackupSet, cfg: Config, parent=None):
        super().__init__(parent)
        self.bset = bset
        self.cfg = cfg
        self.escolhido = False

        self.ui = forms.load("dialog_cloud")()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Nuvem — {bset.name}")

        self.ui.lblSoon.setText(cloud.MOTIVO_INDISPONIVEL)

        cabecalho = self.ui.listing.header()
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(1, QHeaderView.Stretch)
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.ui.btnUse.clicked.connect(self._usar)
        self.ui.btnRefresh.clicked.connect(self._carregar)
        self.ui.btnClose.clicked.connect(self.reject)
        self.ui.listing.itemSelectionChanged.connect(self._atualizar_botao)
        self.ui.listing.itemDoubleClicked.connect(lambda *_: self._usar())

        self._carregar()

    # ------------------------------------------------------------- listagem
    def _carregar(self) -> None:
        listing = self.ui.listing
        listing.clear()

        pastas = util.cloud_folders()
        atual = os.path.normpath(self.bset.destination or "").lower()

        for caminho, servico in sorted(pastas.items(), key=lambda kv: kv[1]):
            livre = util.free_space(caminho)
            no = QTreeWidgetItem([
                servico,
                caminho,
                util.format_bytes(livre) if livre else "—",
            ])
            no.setData(0, Qt.UserRole, caminho)
            usada = atual.startswith(caminho.rstrip("\\") + "\\") or atual == caminho
            no.setIcon(0, widgets.dot_icon(
                widgets.DOT_OK if usada else widgets.DOT_MUTED))
            if usada:
                no.setToolTip(0, "É o destino atual deste conjunto.")
            listing.addTopLevelItem(no)

        if not pastas:
            self._status(
                PathState.WARN,
                "Nenhum cliente de sincronização encontrado nesta máquina. "
                "Instale o OneDrive, o Google Drive para Desktop, o Dropbox ou "
                "o MEGA, faça login, e clique em 'Procurar de novo'.")
        elif util.cloud_provider(self.bset.destination):
            self._status(
                PathState.OK,
                f"O destino deste conjunto já está numa pasta do "
                f"{util.cloud_provider(self.bset.destination)}.")
        else:
            self._status(
                PathState.NEUTRAL,
                f"Escolha uma pasta para gravar o zip deste conjunto nela. "
                f"O destino atual é: {self.bset.destination or '(nenhum)'}")
        self._atualizar_botao()

    def _status(self, estado: PathState, mensagem: str) -> None:
        self.ui.lblStatus.setText(mensagem)
        widgets.set_role(self.ui.lblStatus, {
            PathState.OK: "hintOk",
            PathState.WARN: "hintWarn",
            PathState.BAD: "hintBad",
        }.get(estado, "hint"))

    def _atualizar_botao(self) -> None:
        self.ui.btnUse.setEnabled(bool(self.ui.listing.selectedItems()))

    def _selecionado(self) -> str:
        itens = self.ui.listing.selectedItems()
        return itens[0].data(0, Qt.UserRole) if itens else ""

    # ---------------------------------------------------------------- ação
    def _usar(self) -> None:
        raiz = self._selecionado()
        if not raiz:
            return

        destino = os.path.join(raiz, SUBPASTA, self.bset.name)
        servico = util.cloud_provider(raiz) or "serviço de nuvem"

        if not password.confirm(
                self, f"Gravar os backups de '{self.bset.name}' aqui?",
                f"{destino}\n\n"
                f"O {servico} sincroniza essa pasta, então o zip sobe sozinho "
                f"depois de gravado.\n\n"
                f"Atenção: o backup é dado como concluído quando o arquivo "
                f"toca o disco. O envio acontece em seguida, e quem confirma "
                f"que chegou é o {servico} — não este programa."):
            return

        self.bset.destination = destino
        self.escolhido = True
        self.accept()


def configure(bset: BackupSet, cfg: Config, parent=None) -> bool:
    """Abre o diálogo. True se o conjunto foi alterado."""
    dialogo = CloudDialog(bset, cfg, parent)
    return dialogo.exec() == QDialog.Accepted and dialogo.escolhido


def summary(bset: BackupSet) -> str:
    """Uma linha para a aba, sem gastar espaço com os campos."""
    servico = util.cloud_provider(bset.destination)
    if servico:
        return f"Destino sincronizado pelo {servico}."
    return "Sem envio à nuvem."
