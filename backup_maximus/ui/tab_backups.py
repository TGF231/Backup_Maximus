"""Aba Backups: conjuntos, itens e campos no mesmo plano.

O layout vive em `designer/tab_backups.ui` — abra no Qt Designer para mexer em
posição, tamanho ou rótulo. Este módulo cuida só do comportamento: ligar sinais,
sincronizar com o modelo e manter as listas em dia.
"""

from __future__ import annotations

import copy
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QListWidgetItem, QWidget,
)

from .. import cloud, dbdump
from ..config import BackupItem, BackupSet, Config, ItemType, SetMode
from . import (
    alias_dialog, cloud_dialog, forms, password, preview, widgets,
)
from .pathedit import PathKind, PathState

_TYPE_ORDER = [ItemType.FIREBIRD, ItemType.SQLSERVER, ItemType.MYSQL,
               ItemType.DBF, ItemType.FILES]
_MODE_ORDER = [SetMode.INCREMENTAL, SetMode.FULL]

#: Servidor, porta e usuário sugeridos por tipo de banco. Preenchidos ao trocar
#: o tipo, nunca sobrescrevendo o que o usuário já digitou.
_DEFAULT_CONNECTION = {
    ItemType.FIREBIRD: ("LOCALHOST", "3050", "SYSDBA"),
    ItemType.SQLSERVER: ("localhost", "1433", ""),
    ItemType.MYSQL: ("localhost", "3306", "root"),
}

_SOURCE_HINTS = {
    ItemType.FIREBIRD: "Origem: alias ou caminho do .fdb (ex.: PDVEXPRESSO)",
    ItemType.SQLSERVER: "Origem: nome do banco no SQL Server",
    ItemType.MYSQL: "Origem: nome do banco no MySQL",
    ItemType.DBF: "Origem: arquivo .dbf ou pasta que os contém",
    ItemType.FILES: "Origem: arquivo ou pasta (aceita \\\\servidor\\pasta) — "
                    "também aceita arrastar do Explorer",
}

#: Que tipo de caminho o campo Origem espera, por tipo de item. SQL Server e
#: MySQL recebem nome de banco, não caminho — validar como caminho acusaria
#: erro em toda configuração correta.
_SOURCE_KIND = {
    ItemType.FIREBIRD: PathKind.PATH_OR_NAME,   # alias ou caminho do .fdb
    ItemType.SQLSERVER: PathKind.NONE,
    ItemType.MYSQL: PathKind.NONE,
    ItemType.DBF: PathKind.ANY,
    ItemType.FILES: PathKind.ANY,
}

_TOOL_NAMES = {
    ItemType.FIREBIRD: "gbak.exe",
    ItemType.SQLSERVER: "sqlcmd.exe",
    ItemType.MYSQL: "mysqldump.exe",
}


class BackupsTab(QWidget):
    dirty_changed = Signal()
    run_requested = Signal()

    def __init__(self, cfg: Config, app_dir: str):
        super().__init__()
        self.cfg = cfg
        self.app_dir = app_dir
        self.cur_set = -1
        self.cur_item = -1
        self._loading = False

        self.ui = forms.load("tab_backups")()
        self.ui.setupUi(self)
        self._adopt_widgets()
        self._prepare()
        self._wire_signals()
        self.refresh_all()

    # ------------------------------------------------------------------
    # Nomes curtos para os widgets do formulário. Sem isso o comportamento
    # ficaria coberto de `self.ui.` e o diff com o layout viraria ruído.
    def _adopt_widgets(self) -> None:
        ui = self.ui
        # listas e botões
        self.list_sets = ui.listSets
        self.list_items = ui.listItems
        self.btn_set_new = ui.btnSetNew
        self.btn_set_dup = ui.btnSetDup
        self.btn_set_del = ui.btnSetDel
        self.btn_item_new = ui.btnItemNew
        self.btn_item_dup = ui.btnItemDup
        self.btn_item_del = ui.btnItemDel
        self.btn_item_up = ui.btnItemUp
        self.btn_item_down = ui.btnItemDown
        self.btn_run = ui.btnRun
        self.btn_preview = ui.btnPreview
        self.btn_dest_info = ui.btnDestInfo
        self.btn_test = ui.btnTest
        # campos do conjunto
        self.set_name = ui.editSetName
        self.set_dest = ui.editSetDest
        self.set_mode = ui.comboSetMode
        self.set_staging = ui.editSetStaging
        self.set_wait = ui.comboSetWait
        self.set_wait_secs = ui.spinWaitSecs
        self.set_keep_last = ui.spinKeepLast
        self.set_keep = ui.chkKeepStaging
        self.set_enabled = ui.chkSetEnabled
        self.set_hint = ui.lblSetHint
        self.set_dest_hint = ui.lblSetDestHint
        # campos do item
        self.item_name = ui.editItemName
        self.item_type = ui.comboItemType
        self.item_mirror = ui.chkMirror
        self.item_source = ui.editItemSource
        self.item_subfolder = ui.editItemSubfolder
        self.item_output = ui.editItemOutput
        self.item_host = ui.editItemHost
        self.item_port = ui.editItemPort
        self.item_user = ui.editItemUser
        self.item_pass = ui.editItemPass
        self.item_tool = ui.editItemTool
        self.item_enabled = ui.chkItemEnabled
        self.item_hint = ui.lblItemHint
        self.item_source_hint = ui.lblItemSourceHint

    def _prepare(self) -> None:
        """Ajustes que dependem do modelo e não cabem no .ui."""
        self.set_mode.addItems([m.label for m in _MODE_ORDER])
        self.item_type.addItems([t.label for t in _TYPE_ORDER])

        for listing in (self.list_sets, self.list_items):
            listing.setSelectionMode(QAbstractItemView.SingleSelection)
            # Rolar de lado para ler uma linha é pior do que perder o meio dela:
            # o que interessa (nome no começo, subpasta no fim) já cabe.
            listing.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            listing.setTextElideMode(Qt.ElideRight)

        # Os UNC vêm da aba Rede, onde já têm credencial cadastrada; sem isso
        # o conjunto esperaria por um caminho que não conseguiria acessar.
        # É uma função, não uma cópia da lista: um compartilhamento cadastrado
        # depois desta tela existir precisa aparecer sem reabrir o programa.
        self.set_wait.set_network_source(
            lambda: [nc.unc_root for nc in self.cfg.net_creds])

        self.set_dest.kind = PathKind.DESTINATION
        self.set_staging.kind = PathKind.DESTINATION
        self.item_source.kind = PathKind.ANY
        self.item_tool.kind = PathKind.FILE

        self.ui.btnBrowseDest.clicked.connect(
            lambda: self._browse(self.set_dest, folder=True))
        self.ui.btnBrowseStaging.clicked.connect(
            lambda: self._browse(self.set_staging, folder=True))
        self.ui.btnBrowseSource.clicked.connect(self._browse_source)
        self.ui.btnBrowseTool.clicked.connect(
            lambda: self._browse(self.item_tool, folder=False))

        self.ui.btnCloud.clicked.connect(self.configure_cloud)
        self.ui.btnDetectAliases.clicked.connect(self.detect_aliases)

    # ---------------------------------------------------------- navegação
    def _browse(self, edit, folder: bool) -> None:
        start = edit.text().strip() or self.app_dir
        if folder:
            chosen = QFileDialog.getExistingDirectory(self, "Escolher pasta", start)
        else:
            chosen, _ = QFileDialog.getOpenFileName(self, "Escolher arquivo", start)
        if chosen:
            edit.setText(os.path.normpath(chosen))

    def _browse_source(self) -> None:
        """Origem pode ser arquivo ou pasta; o tipo do item decide o diálogo."""
        item_type = _TYPE_ORDER[self.item_type.currentIndex()]
        start = self.item_source.text().strip() or self.app_dir
        if item_type is ItemType.FIREBIRD:
            chosen, _ = QFileDialog.getOpenFileName(
                self, "Escolher banco Firebird", start,
                "Banco Firebird (*.fdb *.gdb);;Todos os arquivos (*.*)")
        elif item_type is ItemType.DBF:
            chosen = QFileDialog.getExistingDirectory(
                self, "Escolher pasta com os arquivos DBF", start)
        elif item_type.is_database:
            # SQL Server e MySQL recebem nome de banco, não caminho.
            password.info(self, "Este tipo não usa caminho.",
                          f"Em {item_type.label}, o campo Origem recebe o nome "
                          f"do banco de dados.")
            return
        else:
            chosen = QFileDialog.getExistingDirectory(self, "Escolher pasta", start)
            if not chosen:
                chosen, _ = QFileDialog.getOpenFileName(
                    self, "Ou escolher um arquivo", start)
        if chosen:
            self.item_source.setText(os.path.normpath(chosen))

    # ---------------------------------------------------------- sinais
    def _wire_signals(self) -> None:
        self.list_sets.currentRowChanged.connect(self._on_set_selected)
        self.list_items.currentRowChanged.connect(self._on_item_selected)

        self.btn_set_new.clicked.connect(self.new_set)
        self.btn_set_dup.clicked.connect(self.duplicate_set)
        self.btn_set_del.clicked.connect(self._delete_set)
        self.btn_item_new.clicked.connect(self.new_item)
        self.btn_item_dup.clicked.connect(self.duplicate_item)
        self.btn_item_del.clicked.connect(self._delete_item)
        self.btn_item_up.clicked.connect(lambda: self.move_item(-1))
        self.btn_item_down.clicked.connect(lambda: self.move_item(1))
        self.btn_run.clicked.connect(self.run_requested.emit)
        self.btn_preview.clicked.connect(self.show_preview)
        self.btn_dest_info.clicked.connect(self.show_destination)
        self.btn_test.clicked.connect(self._test_connection)

        for edit in (self.set_name, self.set_dest, self.set_staging):
            edit.textChanged.connect(self._set_field_changed)
        self.set_wait.currentIndexChanged.connect(self._set_field_changed)
        self.set_mode.currentIndexChanged.connect(self._set_field_changed)
        self.set_wait_secs.valueChanged.connect(self._set_field_changed)
        self.set_keep_last.valueChanged.connect(self._set_field_changed)
        self.set_keep.toggled.connect(self._set_field_changed)
        self.set_enabled.toggled.connect(self._set_field_changed)

        for edit in (self.item_name, self.item_source, self.item_subfolder,
                     self.item_output, self.item_host, self.item_port,
                     self.item_user, self.item_pass, self.item_tool):
            edit.textChanged.connect(self._item_field_changed)
        self.item_type.currentIndexChanged.connect(self._on_type_changed)
        self.item_mirror.toggled.connect(self._item_field_changed)
        self.item_enabled.toggled.connect(self._item_field_changed)

        # A validação de caminho só reporta depois que a digitação para.
        self.set_dest.validated.connect(
            lambda st, msg: self._show_validation(self.set_dest_hint, st, msg))
        self.item_source.validated.connect(
            lambda st, msg: self._show_validation(self.item_source_hint, st, msg))
        self.item_tool.validated.connect(
            lambda st, msg: self._show_validation(self.item_source_hint, st, msg))

    # ------------------------------------------------------ modelo <-> UI
    def _current_set(self) -> BackupSet | None:
        if 0 <= self.cur_set < len(self.cfg.sets):
            return self.cfg.sets[self.cur_set]
        return None

    def _current_item(self) -> BackupItem | None:
        bset = self._current_set()
        if bset and 0 <= self.cur_item < len(bset.items):
            return bset.items[self.cur_item]
        return None

    def refresh_all(self) -> None:
        if self.cfg.sets and self.cur_set < 0:
            self.cur_set = 0
            self.cur_item = 0 if self.cfg.sets[0].items else -1
        self._refresh_sets()
        self._refresh_items()
        self._load_set()
        self._load_item()

    def _refresh_sets(self) -> None:
        self._loading = True
        self.list_sets.clear()
        for bset in self.cfg.sets:
            count = len(bset.items)
            entry = QListWidgetItem(
                f"{bset.name}    {count} {'item' if count == 1 else 'itens'}"
            )
            entry.setIcon(widgets.dot_icon(
                widgets.DOT_MUTED if not bset.enabled else
                (widgets.DOT_BAD if self.cfg.last_run_status == "error"
                 else widgets.DOT_OK)
            ))
            if not bset.enabled:
                entry.setForeground(Qt.gray)
            self.list_sets.addItem(entry)
        if 0 <= self.cur_set < self.list_sets.count():
            self.list_sets.setCurrentRow(self.cur_set)
        self._loading = False
        self._update_buttons()

    def _refresh_items(self) -> None:
        self._loading = True
        self.list_items.clear()
        bset = self._current_set()
        if bset:
            for item in bset.items:
                where = widgets.elide_left(item.subfolder or "(raiz)", 26)
                entry = QListWidgetItem(f"{item.name}  →  {where}")
                entry.setIcon(widgets.dot_icon(
                    widgets.DOT_MUTED if not item.enabled else widgets.DOT_OK
                ))
                if not item.enabled:
                    entry.setForeground(Qt.gray)
                entry.setToolTip(
                    f"{item.type.label}\nOrigem: {item.source}\n"
                    f"Vai para: {item.subfolder or '(raiz do zip)'}"
                )
                self.list_items.addItem(entry)
        if 0 <= self.cur_item < self.list_items.count():
            self.list_items.setCurrentRow(self.cur_item)
        self._loading = False
        self._update_buttons()

    def _load_set(self) -> None:
        self._loading = True
        bset = self._current_set() or BackupSet()
        self.set_name.setText(bset.name)
        self.set_dest.setText(bset.destination)
        self.set_mode.setCurrentIndex(_MODE_ORDER.index(bset.mode))
        self.set_staging.setText(bset.staging)
        self.set_wait.setValue(bset.wait_for_path)
        self.set_wait_secs.setValue(bset.wait_timeout_sec)
        self.set_keep_last.setValue(bset.keep_last)
        self.set_keep.setChecked(bset.keep_staging)
        self.set_enabled.setChecked(bset.enabled)
        self._loading = False
        self._update_set_hint()
        self._set_panel_enabled(self._current_set() is not None)
        self.set_dest_hint.setText("")
        self.set_dest.validate_now()

    def _load_item(self) -> None:
        self._loading = True
        item = self._current_item() or BackupItem()
        self.item_name.setText(item.name)
        self.item_type.setCurrentIndex(_TYPE_ORDER.index(item.type))
        self.item_mirror.setChecked(item.mirror)
        self.item_source.setText(item.source)
        self.item_subfolder.setText(item.subfolder)
        self.item_output.setText(item.output_name)
        self.item_host.setText(item.host)
        self.item_port.setText(item.port)
        self.item_user.setText(item.user)
        # Senha nunca volta para a tela em claro: campo vazio mantém a gravada.
        self.item_pass.setText("")
        self.item_pass.setPlaceholderText(
            "•••••• (gravada)" if item.password_enc else ""
        )
        self.item_tool.setText(item.tool_path)
        self.item_enabled.setChecked(item.enabled)
        self._loading = False
        self._apply_type_hints()
        self._item_panel_enabled(self._current_item() is not None)
        self.item_source_hint.setText("")
        self.item_source.validate_now()

    def _show_validation(self, label, state: PathState, message: str) -> None:
        label.setText(message)
        widgets.set_role(label, {
            PathState.OK: "hintOk",
            PathState.WARN: "hintWarn",
            PathState.BAD: "hintBad",
        }.get(state, "hint"))

    def _set_panel_enabled(self, on: bool) -> None:
        for w in (self.set_name, self.set_dest, self.set_mode, self.set_staging,
                  self.set_wait, self.set_wait_secs, self.set_keep_last,
                  self.set_keep, self.set_enabled):
            w.setEnabled(on)
        self.ui.btnCloud.setEnabled(on)
        self.ui.btnDetectAliases.setEnabled(on)
        self.btn_preview.setEnabled(on)
        self.btn_dest_info.setEnabled(on)

    def _item_panel_enabled(self, on: bool) -> None:
        """Sem item selecionado nada é editável; com item, tudo é.

        Os campos que não se aplicam ao tipo continuam habilitados — só o
        texto-fantasma e a dica de rodapé mudam. Bloquear o campo atrapalha
        quem tem um caso fora do padrão e não ganha nada em troca.
        """
        for w in (self.item_name, self.item_type, self.item_source,
                  self.item_subfolder, self.item_output, self.item_mirror,
                  self.item_host, self.item_port, self.item_user,
                  self.item_pass, self.item_tool, self.item_enabled):
            w.setEnabled(on)
        item_type = _TYPE_ORDER[self.item_type.currentIndex()]
        self.btn_test.setEnabled(on and item_type.is_database)

    def _apply_type_hints(self) -> None:
        """Ajusta textos-fantasma e a dica conforme o tipo, sem desabilitar nada."""
        item_type = _TYPE_ORDER[self.item_type.currentIndex()]
        is_db = item_type.is_database
        has_item = self._current_item() is not None

        self.item_hint.setText(_SOURCE_HINTS[item_type])
        self.btn_test.setEnabled(has_item and is_db)
        # O campo Origem muda de significado com o tipo, então muda de regra.
        self.item_source.set_kind(_SOURCE_KIND[item_type])

        if is_db:
            tool = _TOOL_NAMES.get(item_type, "")
            self.item_tool.setPlaceholderText(
                f"{tool} detectado automaticamente" if tool else ""
            )
            self.item_output.setPlaceholderText(
                f"vazio = <nome do item>{item_type.dump_ext}"
            )
            host, port, user = _DEFAULT_CONNECTION.get(item_type, ("", "", ""))
            self.item_host.setPlaceholderText(host)
            self.item_port.setPlaceholderText(port)
            self.item_user.setPlaceholderText(user)
        else:
            self.item_tool.setPlaceholderText("não se aplica a arquivos/pastas")
            self.item_output.setPlaceholderText("não se aplica a arquivos/pastas")
            self.item_host.setPlaceholderText("não se aplica")
            self.item_port.setPlaceholderText("")
            self.item_user.setPlaceholderText("")

    def _fill_connection_defaults(self, item_type: ItemType) -> None:
        """Sugere servidor, porta e usuário ao escolher um tipo de banco.

        Só preenche campo vazio: o que já foi digitado nunca é sobrescrito, para
        trocar o tipo por engano não apagar uma configuração pronta.
        """
        host, port, user = _DEFAULT_CONNECTION.get(item_type, ("", "", ""))
        for value, field in ((host, self.item_host), (port, self.item_port),
                             (user, self.item_user)):
            if value and not field.text().strip():
                field.setText(value)

    def _update_set_hint(self) -> None:
        bset = self._current_set()
        if not bset:
            self.set_hint.setText("")
            return
        name = self.set_name.text().strip() or "CONJUNTO"
        mode = _MODE_ORDER[self.set_mode.currentIndex()]
        dest = self.set_dest.text().strip() or "<destino>"
        if mode is SetMode.FULL:
            example = os.path.join(dest, f"{name}26082026170516.zip")
            self.set_hint.setText(
                f"Gera {example} — um arquivo novo por execução, "
                f"mesmo padrão do WinRAR -ag."
            )
        else:
            example = os.path.join(dest, f"{name}.zip")
            self.set_hint.setText(
                f"Mantém {example} — um único arquivo, atualizado a cada execução."
            )
        # O destino em nuvem fica num diálogo, mas o que ele faz continua
        # visível aqui: esconder o mecanismo é aceitável, esconder o efeito não.
        self.set_hint.setText(
            f"{self.set_hint.text()}  {cloud_dialog.summary(bset)}")
        self._sync_campos_dependentes(bset, mode)

    def _sync_campos_dependentes(self, bset, mode) -> None:
        """Liga cada campo só quando ele muda alguma coisa — e explica quando não.

        Um campo editável que não produz efeito e um campo desligado sem
        motivo visível dão o mesmo resultado prático: o usuário conclui que
        está quebrado. Os dois casos existiam aqui.
        """
        # Retenção só faz sentido quando há vários arquivos para reter: no
        # modo incremental existe um zip fixo, que é sobrescrito.
        retem = bset is not None and mode is SetMode.FULL
        self.set_keep_last.setEnabled(retem)
        self.set_keep_last.setToolTip(
            "Quantos .zip manter no destino, apagando os mais antigos."
            if retem else
            "Só no modo Completo. No Incremental existe um único zip, "
            "atualizado a cada execução — não há cópias antigas a manter.")

        # O prazo só conta quando há unidade a esperar. Sem ela, o backup
        # começa imediatamente e o número aqui nunca é consultado.
        espera = bset is not None and bool(bset.wait_for_path)
        self.set_wait_secs.setEnabled(espera)
        self.set_wait_secs.setToolTip(
            "Quanto esperar a unidade aparecer. 0 = espera sem limite."
            if espera else
            "Escolha uma unidade em 'Aguardar unidade' para este prazo "
            "valer. Sem unidade, o backup começa na hora.")

    def _update_buttons(self) -> None:
        has_set = self._current_set() is not None
        has_item = self._current_item() is not None
        self.btn_set_del.setEnabled(has_set)
        self.btn_set_dup.setEnabled(has_set)
        self.btn_item_new.setEnabled(has_set)
        self.btn_item_dup.setEnabled(has_item)
        self.btn_item_del.setEnabled(has_item)
        bset = self._current_set()
        self.btn_item_up.setEnabled(has_item and self.cur_item > 0)
        self.btn_item_down.setEnabled(
            has_item and bset is not None and self.cur_item < len(bset.items) - 1
        )
        self.btn_run.setEnabled(bool(self.cfg.sets))

    # ------------------------------------------------------------ edição
    def _set_field_changed(self, *_args) -> None:
        if self._loading:
            return
        bset = self._current_set()
        if not bset:
            return
        bset.name = self.set_name.text().strip()
        bset.destination = self.set_dest.text().strip()
        bset.mode = _MODE_ORDER[self.set_mode.currentIndex()]
        bset.staging = self.set_staging.text().strip()
        bset.wait_for_path = self.set_wait.value()
        bset.wait_timeout_sec = self.set_wait_secs.value()
        bset.keep_last = self.set_keep_last.value()
        bset.keep_staging = self.set_keep.isChecked()
        bset.enabled = self.set_enabled.isChecked()
        self._update_set_hint()
        self._refresh_sets()
        self.dirty_changed.emit()

    def _item_field_changed(self, *_args) -> None:
        if self._loading:
            return
        item = self._current_item()
        if not item:
            return
        item.name = self.item_name.text().strip()
        item.type = _TYPE_ORDER[self.item_type.currentIndex()]
        item.source = self.item_source.text().strip()
        item.subfolder = self.item_subfolder.text().strip().strip("\\/")
        item.output_name = self.item_output.text().strip()
        item.mirror = self.item_mirror.isChecked()
        item.host = self.item_host.text().strip()
        item.port = self.item_port.text().strip()
        item.user = self.item_user.text().strip()
        if self.item_pass.text():
            item.set_password(self.item_pass.text())
        item.tool_path = self.item_tool.text().strip()
        item.enabled = self.item_enabled.isChecked()
        self._refresh_items()
        self.dirty_changed.emit()

    def _on_type_changed(self) -> None:
        if not self._loading and self._current_item() is not None:
            self._fill_connection_defaults(_TYPE_ORDER[self.item_type.currentIndex()])
        self._apply_type_hints()
        self._item_field_changed()

    def _on_set_selected(self, row: int) -> None:
        if self._loading or row == self.cur_set:
            return
        self.cur_set = row
        bset = self._current_set()
        self.cur_item = 0 if (bset and bset.items) else -1
        self._load_set()
        self._refresh_items()
        self._load_item()

    def _on_item_selected(self, row: int) -> None:
        if self._loading or row == self.cur_item:
            return
        self.cur_item = row
        self._load_item()
        self._update_buttons()

    # ------------------------------------------------------------ comandos
    def new_set(self) -> None:
        bset = BackupSet(
            name="BKP_MAXIMUS" if not self.cfg.sets
            else f"CONJUNTO_{len(self.cfg.sets) + 1}"
        )
        self.cfg.sets.append(bset)
        self.cur_set = len(self.cfg.sets) - 1
        self.cur_item = -1
        self._reload_all_and_focus(self.set_name)

    def duplicate_set(self) -> None:
        bset = self._current_set()
        if not bset:
            return
        clone = copy.deepcopy(bset)
        clone.name = f"{bset.name}_COPIA"
        self.cfg.sets.insert(self.cur_set + 1, clone)
        self.cur_set += 1
        self.cur_item = 0 if clone.items else -1
        self._reload_all_and_focus(self.set_name)

    def _delete_set(self) -> None:
        bset = self._current_set()
        if not bset:
            return
        if not password.confirm(
            self, f"Excluir o conjunto '{bset.name}'?",
            f"Os {len(bset.items)} itens dele também serão removidos. "
            f"Os arquivos .zip já gerados não são afetados."
        ):
            return
        del self.cfg.sets[self.cur_set]
        self.cur_set = 0 if self.cfg.sets else -1
        bset = self._current_set()
        self.cur_item = 0 if (bset and bset.items) else -1
        self._reload_all_and_focus(None)

    def new_item(self) -> None:
        bset = self._current_set()
        if not bset:
            return
        bset.items.append(BackupItem(name=f"item_{len(bset.items) + 1}"))
        self.cur_item = len(bset.items) - 1
        self._reload_all_and_focus(self.item_name)

    def duplicate_item(self) -> None:
        """O padrão real de uso é 'igual ao anterior, com outro alias'."""
        bset = self._current_set()
        item = self._current_item()
        if not bset or not item:
            return
        clone = copy.deepcopy(item)
        clone.name = f"{item.name} (cópia)"
        bset.items.insert(self.cur_item + 1, clone)
        self.cur_item += 1
        self._reload_all_and_focus(self.item_name)

    def _delete_item(self) -> None:
        bset = self._current_set()
        item = self._current_item()
        if not bset or not item:
            return
        if not password.confirm(self, f"Excluir o item '{item.name}'?",
                                "Ele deixa de entrar no zip deste conjunto."):
            return
        del bset.items[self.cur_item]
        self.cur_item = 0 if bset.items else -1
        self._reload_all_and_focus(None)

    def move_item(self, delta: int) -> None:
        bset = self._current_set()
        if not bset or self.cur_item < 0:
            return
        target = self.cur_item + delta
        if not 0 <= target < len(bset.items):
            return
        bset.items[self.cur_item], bset.items[target] = (
            bset.items[target], bset.items[self.cur_item]
        )
        self.cur_item = target
        self._refresh_items()
        self._load_item()
        self.dirty_changed.emit()

    def _reload_all_and_focus(self, field) -> None:
        self._refresh_sets()
        self._refresh_items()
        self._load_set()
        self._load_item()
        if field is not None:
            field.setFocus()
            field.selectAll()
        self.dirty_changed.emit()

    # ------------------------------------------------------------------
    # Nomes públicos: é o que os atalhos de teclado da janela principal
    # acionam, para o teclado e o clique passarem pelo mesmo caminho.
    def show_preview(self) -> None:
        bset = self._current_set()
        if bset:
            preview.show_tree(bset, self)

    def show_destination(self) -> None:
        bset = self._current_set()
        if bset:
            preview.show_destination(bset, self)

    def new_backup_run(self) -> None:
        if self.btn_run.isEnabled():
            self.run_requested.emit()

    def focus_name(self) -> None:
        """F2 renomeia o que estiver selecionado: item se houver, senão conjunto."""
        target = self.item_name if self._current_item() else self.set_name
        target.setFocus()
        target.selectAll()

    # ------------------------------------------------------------- nuvem
    def configure_cloud(self) -> None:
        bset = self._current_set()
        if not bset:
            return
        if cloud_dialog.configure(bset, self.cfg, self):
            self._update_set_hint()
            self.dirty_changed.emit()

    # ------------------------------------------------- detecção de bancos
    def detect_aliases(self) -> None:
        """Cria itens a partir dos bancos registrados no Firebird."""
        bset = self._current_set()
        if not bset:
            password.error(self, "Crie um conjunto antes de adicionar bancos.")
            return

        found = alias_dialog.pick(self)
        if not found:
            return

        existing = {i.source.strip().lower() for i in bset.items}
        added = [i for i in found if i.source.strip().lower() not in existing]
        skipped = len(found) - len(added)

        bset.items.extend(added)
        if added:
            self.cur_item = len(bset.items) - 1
        self._refresh_items()
        self._refresh_sets()
        self._load_item()
        self.dirty_changed.emit()

        detail = f"{len(added)} item(ns) criado(s) no conjunto '{bset.name}'."
        if skipped:
            detail += f" {skipped} já estava(m) na lista e foi(ram) ignorado(s)."
        detail += " Preencha a senha do SYSDBA em cada item antes de rodar."
        password.info(self, "Bancos adicionados.", detail)

    def _test_connection(self) -> None:
        """Descobre senha errada em dois segundos, não na primeira madrugada."""
        item = self._current_item()
        if not item:
            return
        self.btn_test.setEnabled(False)
        self.btn_test.setText("Testando…")
        try:
            ok, detail = dbdump.test_connection(item)
        finally:
            self.btn_test.setText("Testar conexão")
            self.btn_test.setEnabled(True)
        if ok:
            password.info(self, "Conexão bem-sucedida.", detail)
        else:
            password.error(self, "Não foi possível conectar.", detail)
