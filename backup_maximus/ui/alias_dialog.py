"""Escolha de bancos a partir dos aliases registrados no Firebird.

Digitar o caminho de um .fdb à mão é a parte mais chata e mais sujeita a erro de
configurar um backup. O servidor já sabe onde os bancos estão — este diálogo
lê essa lista e transforma o que você marcar em itens do conjunto.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHeaderView, QTreeWidgetItem

from .. import firebird_aliases as fbal
from .. import util
from ..config import BackupItem, ItemType
from . import forms, password, widgets

_ROLE_ALIAS = Qt.UserRole + 1


class AliasDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chosen: list[BackupItem] = []

        self.ui = forms.load("dialog_aliases")()
        self.ui.setupUi(self)

        tree = self.ui.tree
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tree.header().setSectionResizeMode(3, QHeaderView.Stretch)
        tree.itemChanged.connect(lambda *_a: self._update_count())

        self.ui.btnRescan.clicked.connect(self._scan)
        self.ui.btnAll.clicked.connect(lambda: self._set_all(True))
        self.ui.btnNone.clicked.connect(lambda: self._set_all(False))
        self.ui.btnAdd.clicked.connect(self._accept)
        self.ui.btnCancel.clicked.connect(self.reject)

        self._scan()

    # ------------------------------------------------------------- varredura
    def _scan(self) -> None:
        tree = self.ui.tree
        tree.clear()
        aliases = fbal.discover()

        if not aliases:
            self.ui.lblIntro.setText(
                "Nenhum alias encontrado. Ou o Firebird não está instalado nesta "
                "máquina, ou o <b>aliases.conf</b> (2.5) / <b>databases.conf</b> "
                "(3 ou superior) ainda não tem bancos registrados. Você pode "
                "adicionar o banco manualmente informando o caminho do .fdb."
            )
            self.ui.btnAdd.setEnabled(False)
            self._update_count()
            return

        instances = {a.instance.root for a in aliases}
        self.ui.lblIntro.setText(
            f"{len(aliases)} banco(s) registrado(s) em "
            f"{len(instances)} instalação(ões) do Firebird. Marque os que devem "
            f"entrar neste conjunto."
        )
        self.ui.btnAdd.setEnabled(True)

        for alias in aliases:
            node = QTreeWidgetItem([
                alias.name,
                alias.instance.label,
                alias.status,
                alias.path,
            ])
            node.setFlags(node.flags() | Qt.ItemIsUserCheckable)
            # Um alias cujo arquivo não existe agora pode ser um banco em outra
            # máquina; entra na lista, mas desmarcado, para não ser incluído
            # sem alguém decidir.
            node.setCheckState(0, Qt.Checked if alias.exists else Qt.Unchecked)
            node.setIcon(0, widgets.dot_icon(
                widgets.DOT_OK if alias.exists else widgets.DOT_BAD))
            if not alias.exists:
                node.setForeground(2, Qt.gray)
                node.setToolTip(0, "O arquivo não foi encontrado neste computador. "
                                   "Pode ser um banco em outro servidor.")
            node.setData(0, _ROLE_ALIAS, alias)
            tree.addTopLevelItem(node)

        self._update_count()

    def _set_all(self, checked: bool) -> None:
        tree = self.ui.tree
        for index in range(tree.topLevelItemCount()):
            tree.topLevelItem(index).setCheckState(
                0, Qt.Checked if checked else Qt.Unchecked)

    def _checked_aliases(self) -> list[fbal.FirebirdAlias]:
        tree = self.ui.tree
        result = []
        for index in range(tree.topLevelItemCount()):
            node = tree.topLevelItem(index)
            if node.checkState(0) == Qt.Checked:
                result.append(node.data(0, _ROLE_ALIAS))
        return result

    def _update_count(self) -> None:
        chosen = self._checked_aliases()
        total = sum(a.size for a in chosen if a.exists)
        if chosen:
            self.ui.lblCount.setText(
                f"{len(chosen)} marcado(s) · {util.format_bytes(total)} de bancos"
            )
        else:
            self.ui.lblCount.setText("nenhum marcado")
        self.ui.btnAdd.setEnabled(bool(chosen))

    # ------------------------------------------------------------- resultado
    def _accept(self) -> None:
        chosen = self._checked_aliases()
        if not chosen:
            return

        per_folder = self.ui.chkSubfolder.isChecked()
        for alias in chosen:
            # A origem é o alias, não o caminho: é assim que o gbak resolve pelo
            # servidor, e continua valendo se o banco mudar de pasta.
            item = BackupItem(
                name=alias.name,
                type=ItemType.FIREBIRD,
                source=alias.name,
                subfolder=_safe_folder(alias.name) if per_folder else "",
                output_name=f"{_safe_folder(alias.name)}.fbk",
                host="LOCALHOST",
                port="3050",
                user="SYSDBA",
                tool_path=alias.instance.gbak,
            )
            self.chosen.append(item)
        self.accept()


def _safe_folder(name: str) -> str:
    """Nome de alias vira nome de pasta/arquivo: tira o que o Windows recusa."""
    cleaned = "".join("_" if ch in '<>:"/\\|?*' else ch for ch in name).strip()
    return cleaned.rstrip(". ") or "banco"


def pick(parent=None) -> list[BackupItem]:
    """Abre o diálogo e devolve os itens escolhidos (vazio se cancelou)."""
    dialog = AliasDialog(parent)
    if dialog.exec() != QDialog.Accepted:
        return []
    return dialog.chosen
