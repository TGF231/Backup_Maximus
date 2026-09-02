"""Prévia da árvore e inspeção do destino.

Layouts em `designer/dialog_preview_tree.ui` e `designer/dialog_destination.ui`.

São as duas perguntas que o operador faria olhando a pasta antes de confiar no
agendamento: *o que exatamente vai para dentro do zip* e *quanto ainda cabe no
destino*. Ambas são inspeção, não configuração — por isso podem ser diálogo sem
violar a regra de que nada que se configure passa por modal.
"""

from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHeaderView, QTreeWidgetItem

from .. import retention, util
from ..config import BackupSet, SetMode
from . import forms, password, theme, widgets


# ============================================================ prévia da árvore
def _is_file_source(source: str) -> bool:
    """Arquivo ou pasta?

    A prévia costuma ser aberta antes de o caminho existir (configurando numa
    máquina, para rodar em outra), então quando o disco não responde a decisão
    vai pela extensão — que é o que o usuário digitou querendo dizer.
    """
    if not source:
        return False
    if os.path.isdir(source):
        return False
    if os.path.isfile(source):
        return True
    return bool(os.path.splitext(source)[1])


def _expected_entries(bset: BackupSet) -> list[tuple[str, str, bool]]:
    """(caminho relativo, rótulo da origem, é_pasta) de cada item habilitado."""
    entries: list[tuple[str, str, bool]] = []
    for item in bset.items:
        if not item.enabled:
            continue
        subfolder = item.subfolder.strip().strip("\\/")

        if item.type.is_database:
            rel = os.path.join(subfolder, item.dump_filename()) if subfolder \
                else item.dump_filename()
            entries.append((rel, f"{item.name} · {item.type.label}", False))
            continue

        source = item.source.strip()
        if _is_file_source(source):
            rel = os.path.join(subfolder, os.path.basename(source)) if subfolder \
                else os.path.basename(source)
            entries.append((rel, item.name, False))
        else:
            # Pasta: a prévia mostra o nó, não o conteúdo — o conteúdo muda a
            # cada execução e listar milhares de XMLs não ajudaria ninguém.
            rel = subfolder or os.path.basename(os.path.normpath(source) or "?")
            entries.append((rel, item.name, True))
    return entries


class TreePreviewDialog(QDialog):
    def __init__(self, bset: BackupSet, parent=None):
        super().__init__(parent)
        self.ui = forms.load("dialog_preview_tree")()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Prévia da árvore — {bset.name}")
        self.ui.buttonBox.rejected.connect(self.reject)

        zip_name = (f"{bset.name}{util.now_stamp_br()}.zip"
                    if bset.mode is SetMode.FULL else f"{bset.name}.zip")
        self.ui.lblIntro.setText(
            f"Estrutura que os itens habilitados produzem dentro de "
            f"<b>{zip_name}</b>. Pastas aparecem como um nó só: o conteúdo é "
            f"copiado inteiro e muda a cada execução."
        )

        tree = self.ui.tree
        tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # A raiz do zip é a pasta de montagem, igual ao que o WinRAR fazia.
        staging_name = os.path.basename(
            os.path.normpath(bset.staging)) if bset.staging.strip() else bset.name
        root = QTreeWidgetItem([staging_name or "BACKUP", ""])
        root.setIcon(0, widgets.dot_icon(widgets.DOT_OK))
        tree.addTopLevelItem(root)

        entries = _expected_entries(bset)
        nodes: dict[str, QTreeWidgetItem] = {"": root}

        for rel, origin, is_dir in sorted(entries):
            parts = [p for p in rel.replace("/", "\\").split("\\") if p]
            parent_node = root
            walked = ""
            for depth, part in enumerate(parts):
                walked = f"{walked}\\{part}" if walked else part
                last = depth == len(parts) - 1
                if walked in nodes:
                    parent_node = nodes[walked]
                    if last:
                        # Dois itens caindo no mesmo lugar: soma as origens em
                        # vez de sobrescrever, porque isso é legítimo e comum.
                        existing = parent_node.text(1)
                        parent_node.setText(
                            1, f"{existing} + {origin}" if existing else origin)
                    continue
                node = QTreeWidgetItem([part + ("\\" if (is_dir and last) else ""),
                                        origin if last else ""])
                parent_node.addChild(node)
                nodes[walked] = node
                parent_node = node

        tree.expandAll()

        if not entries:
            self.ui.lblSummary.setText(
                "Nenhum item habilitado neste conjunto — o backup não geraria nada."
            )
        else:
            self.ui.lblSummary.setText(
                f"{len(entries)} item(ns) habilitado(s). O arquivo de configuração "
                f"e o relatório da execução são acrescentados na raiz do zip."
            )


def show_tree(bset: BackupSet, parent=None) -> None:
    TreePreviewDialog(bset, parent).exec()


# ======================================================= espaço e retenção
class DestinationDialog(QDialog):
    """Espaço livre no destino e limpeza dos backups antigos."""

    def __init__(self, bset: BackupSet, parent=None):
        super().__init__(parent)
        self.bset = bset
        self.ui = forms.load("dialog_destination")()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Destino — {bset.name}")

        listing = self.ui.listing
        listing.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1, 2, 3):
            listing.header().setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.ui.btnPrune.clicked.connect(self._prune)
        self.ui.btnClose.clicked.connect(self.accept)
        self._reload()

    def _reload(self) -> None:
        report = retention.inspect(self.bset)
        self.ui.listing.clear()
        palette = theme.current()

        if not report.reachable:
            self.ui.lblSummary.setText("Destino indisponível")
            self.ui.lblSummary.setStyleSheet(
                f"color: {palette.warn}; font-weight: 600;")
            self.ui.lblDetail.setText(report.message)
            self.ui.lblPolicy.setText("")
            self.ui.btnPrune.setEnabled(False)
            return

        pct_free = (100.0 * report.free_bytes / report.total_bytes
                    if report.total_bytes else 0.0)
        self.ui.lblSummary.setText(
            f"{util.format_bytes(report.free_bytes)} livres de "
            f"{util.format_bytes(report.total_bytes)}  ({pct_free:.0f}% livre)"
        )
        color = (palette.ok if pct_free > 15
                 else palette.warn if pct_free > 5 else palette.bad)
        self.ui.lblSummary.setStyleSheet(f"color: {color}; font-weight: 600;")
        self.ui.lblDetail.setText(
            f"{report.destination} · {len(report.backups)} backup(s) deste conjunto "
            f"ocupando {util.format_bytes(report.used_bytes)}"
        )

        prunable_paths = {b.path for b in report.prunable}
        for backup in report.backups:
            doomed = backup.path in prunable_paths
            node = QTreeWidgetItem([
                backup.name,
                util.format_bytes(backup.size),
                datetime.fromtimestamp(backup.mtime).strftime("%d/%m/%Y %H:%M"),
                "será removido" if doomed else "mantido",
            ])
            node.setIcon(0, widgets.dot_icon(
                widgets.DOT_BAD if doomed else widgets.DOT_OK))
            if doomed:
                node.setForeground(3, Qt.gray)
            self.ui.listing.addTopLevelItem(node)

        if self.bset.mode is not SetMode.FULL:
            self.ui.lblPolicy.setText(
                "Modo Incremental: existe um arquivo só, que é atualizado a cada "
                "execução. Não há backups antigos para remover."
            )
            self.ui.btnPrune.setEnabled(False)
        elif self.bset.keep_last <= 0:
            self.ui.lblPolicy.setText(
                "Retenção desligada: todos os arquivos são mantidos. Defina "
                "'Manter últimos' no conjunto para o expurgo rodar sozinho a "
                "cada backup."
            )
            self.ui.btnPrune.setEnabled(False)
        else:
            self.ui.lblPolicy.setText(
                f"Retenção: manter os {self.bset.keep_last} mais recentes. "
                f"{len(report.prunable)} arquivo(s) sobram, "
                f"{util.format_bytes(report.prunable_bytes)} a liberar."
            )
            self.ui.btnPrune.setEnabled(bool(report.prunable))

    def _prune(self) -> None:
        count, freed, _errors = retention.prune(self.bset, dry_run=True)
        if not count:
            password.info(self, "Nada a remover.")
            return
        if not password.confirm(
            self, f"Remover {count} backup(s) antigo(s)?",
            f"Libera {util.format_bytes(freed)}. Os {self.bset.keep_last} mais "
            f"recentes são preservados. A remoção é definitiva."
        ):
            return
        removed, freed, errors = retention.prune(self.bset)
        self._reload()
        if errors:
            password.error(self, f"{removed} removido(s), {len(errors)} com erro.",
                           "\n".join(errors[:5]))
        else:
            password.info(self, f"{removed} backup(s) removido(s).",
                          f"{util.format_bytes(freed)} liberados.")


def show_destination(bset: BackupSet, parent=None) -> None:
    DestinationDialog(bset, parent).exec()
