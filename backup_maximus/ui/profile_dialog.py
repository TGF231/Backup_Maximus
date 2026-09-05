r"""Importar configurações prontas: um arquivo exportado ou um modelo.

A tela mostra o conteúdo **antes** de aplicar, e não depois. Importar mexe nos
conjuntos de backup de uma loja em produção; ver "3 conjuntos, 11 itens" com os
nomes à vista é o que separa um atalho útil de uma surpresa desagradável.

A exportação não passa por aqui — ela é um diálogo de salvar arquivo, e o aviso
sobre as senhas que não viajam cabe numa confirmação.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFileDialog, QHeaderView, QTreeWidgetItem

from .. import profiles
from ..config import Config
from . import forms, password, widgets
from .pathedit import PathState

_MODOS = [profiles.ImportMode.MESCLAR,
          profiles.ImportMode.ACRESCENTAR,
          profiles.ImportMode.SUBSTITUIR]


class ProfileDialog(QDialog):
    def __init__(self, cfg: Config, app_dir: str, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.app_dir = app_dir
        self.perfil: Config | None = None
        self.aplicado = False

        self.ui = forms.load("dialog_profile")()
        self.ui.setupUi(self)

        cabecalho = self.ui.listing.header()
        cabecalho.setSectionResizeMode(0, QHeaderView.Stretch)
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(2, QHeaderView.Stretch)

        for modo in _MODOS:
            self.ui.comboModo.addItem(modo.label, modo)

        self.ui.btnBrowse.clicked.connect(self._escolher_arquivo)
        self.ui.btnImport.clicked.connect(self._importar)
        self.ui.btnCancel.clicked.connect(self.reject)
        self.ui.comboOrigem.currentIndexChanged.connect(self._carregar_origem)

        self._montar_origens()

    # ------------------------------------------------------------- origens
    def _montar_origens(self) -> None:
        combo = self.ui.comboOrigem
        combo.blockSignals(True)
        combo.clear()
        for modelo in profiles.listar_modelos():
            combo.addItem(f"Modelo · {modelo.nome}  ({modelo.info.resumo})",
                          modelo.caminho)
        combo.blockSignals(False)

        if combo.count():
            self._carregar_origem()
        else:
            self._status(PathState.NEUTRAL,
                         "Escolha um arquivo exportado de outra máquina.")
            self._atualizar_botao()

    def _escolher_arquivo(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Escolher configurações exportadas", self.app_dir,
            "Configurações do Backup Maximus (*.ini);;Todos os arquivos (*.*)")
        if not caminho:
            return

        combo = self.ui.comboOrigem
        indice = combo.findData(caminho)
        if indice < 0:
            combo.addItem(f"Arquivo · {os.path.basename(caminho)}", caminho)
            indice = combo.count() - 1
        combo.setCurrentIndex(indice)
        self._carregar_origem()

    def _carregar_origem(self) -> None:
        caminho = self.ui.comboOrigem.currentData()
        self.perfil = profiles.ler(caminho) if caminho else None
        self._mostrar()

    # -------------------------------------------------------------- exibição
    def _mostrar(self) -> None:
        listing = self.ui.listing
        listing.clear()

        if self.perfil is None:
            self._status(PathState.BAD,
                         "Este arquivo não é uma configuração do Backup "
                         "Maximus, ou está vazio.")
            self._atualizar_botao()
            return

        conhecidos = {s.name for s in self.cfg.sets}
        for bset in self.perfil.sets:
            no = QTreeWidgetItem([
                bset.name,
                str(len(bset.items)),
                bset.destination or "(sem destino)",
            ])
            repetido = bset.name in conhecidos
            no.setIcon(0, widgets.dot_icon(
                widgets.DOT_BAD if repetido else widgets.DOT_OK))
            if repetido:
                no.setToolTip(0, "Já existe um conjunto com este nome. O modo "
                                 "escolhido decide o que acontece com ele.")
            listing.addTopLevelItem(no)

        info = profiles.descrever(self.perfil)
        self.ui.chkGerais.setEnabled(bool(info.company or info.tem_smtp))
        if not self.ui.chkGerais.isEnabled():
            self.ui.chkGerais.setChecked(False)
            self.ui.chkGerais.setText(
                "Este perfil não traz empresa, e-mail nem servidor de envio")
        else:
            self.ui.chkGerais.setText(
                "Trazer também empresa, e-mail e servidor de envio")

        if info.pendencias:
            # Dizer o que falta é a diferença entre um perfil e uma armadilha:
            # os campos chegam preenchidos, menos as senhas.
            self._status(
                PathState.WARN,
                f"As senhas não viajam num perfil — elas são cifradas para esta "
                f"máquina e não decifrariam em outra. Depois de importar, "
                f"informe de novo: {'; '.join(info.pendencias[:4])}"
                + (f" e mais {len(info.pendencias) - 4}."
                   if len(info.pendencias) > 4 else "."))
        else:
            self._status(PathState.OK,
                         f"{info.resumo}. Nenhuma senha a redigitar.")
        self._atualizar_botao()

    def _status(self, estado: PathState, mensagem: str) -> None:
        self.ui.lblStatus.setText(mensagem)
        widgets.set_role(self.ui.lblStatus, {
            PathState.OK: "hintOk",
            PathState.WARN: "hintWarn",
            PathState.BAD: "hintBad",
        }.get(estado, "hint"))

    def _atualizar_botao(self) -> None:
        self.ui.btnImport.setEnabled(
            self.perfil is not None and bool(self.perfil.sets))

    # ----------------------------------------------------------------- ação
    def _importar(self) -> None:
        if self.perfil is None:
            return
        modo = self.ui.comboModo.currentData()

        if modo is profiles.ImportMode.SUBSTITUIR and self.cfg.sets:
            if not password.confirm(
                    self, f"Descartar os {len(self.cfg.sets)} conjunto(s) atuais?",
                    "Eles serão trocados pelos do perfil. Os arquivos de backup "
                    "já gerados não são apagados, mas a configuração atual se "
                    "perde — exporte-a antes se quiser guardá-la."):
                return

        acrescentados, atualizados = profiles.importar_conjuntos(
            self.cfg, self.perfil, modo)

        mudou: list[str] = []
        if self.ui.chkGerais.isChecked():
            mudou = profiles.importar_gerais(self.cfg, self.perfil)

        self.aplicado = True
        partes = []
        if acrescentados:
            partes.append(f"{acrescentados} conjunto(s) acrescentado(s)")
        if atualizados:
            partes.append(f"{atualizados} atualizado(s)")
        if mudou:
            partes.append("e ".join([", ".join(mudou[:-1]), mudou[-1]])
                          if len(mudou) > 1 else mudou[0])

        detalhe = ""
        pendencias = profiles.campos_pendentes(self.perfil)
        if pendencias:
            detalhe = ("Falta informar as senhas:\n  · "
                       + "\n  · ".join(pendencias))

        password.info(self, ". ".join(partes) + ".", detalhe)
        self.accept()


# ------------------------------------------------------------------ atalhos
def importar(cfg: Config, app_dir: str, parent=None) -> bool:
    """Abre o diálogo. True se a configuração foi alterada."""
    dialogo = ProfileDialog(cfg, app_dir, parent)
    return dialogo.exec() == QDialog.Accepted and dialogo.aplicado


def exportar(cfg: Config, app_dir: str, parent=None) -> bool:
    """Diálogo de salvar. True se um arquivo foi gravado."""
    if not cfg.sets:
        password.info(parent, "Não há conjuntos para exportar.",
                      "Configure ao menos um conjunto antes.")
        return False

    sugerido = os.path.join(
        app_dir,
        f"backup_maximus_{(cfg.company_name or 'perfil').replace(' ', '_')}.ini")
    caminho, _ = QFileDialog.getSaveFileName(
        parent, "Exportar configurações", sugerido,
        "Configurações do Backup Maximus (*.ini)")
    if not caminho:
        return False

    pendencias = profiles.campos_pendentes(cfg)
    aviso = ("As senhas NÃO vão no arquivo. Elas são cifradas com a chave desta "
             "máquina e deste usuário, então não funcionariam em outro "
             "computador de qualquer forma.")
    if pendencias:
        aviso += ("\n\nQuem importar precisará informar:\n  · "
                  + "\n  · ".join(pendencias))
    if not password.confirm(parent, f"Exportar {len(cfg.sets)} conjunto(s)?",
                            aviso):
        return False

    ok, mensagem = profiles.exportar(cfg, caminho)
    if ok:
        password.info(parent, "Configurações exportadas.", mensagem)
    else:
        password.error(parent, "Não foi possível exportar.", mensagem)
    return ok
