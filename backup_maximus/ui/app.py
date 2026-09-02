"""Janela de configuração: três abas, um único plano, sem assistente.

O layout vive em `designer/main_window.ui`. As três páginas de aba chegam
vazias do formulário e recebem aqui o widget de cada aba, para que cada tela
possa ser editada no seu próprio .ui.

O custo de um assistente não é o número de telas — é que ele impede comparação.
Configurando o quarto item você quer olhar o terceiro e copiar o padrão da
subpasta. Um mestre-detalhe deixa isso na tela.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QVBoxLayout

from .. import __version__, logger, util
from ..config import Config
from . import forms, password, theme
from .tab_backups import BackupsTab
from .tab_settings import NetworkTab, SettingsTab


class MainWindow(QMainWindow):
    def __init__(self, cfg: Config, cfg_path: str, app_dir: str):
        super().__init__()
        self.cfg = cfg
        self.cfg_path = cfg_path
        self.app_dir = app_dir
        self.dirty = False

        self.ui = forms.load("main_window")()
        self.ui.setupUi(self)
        # A versão fica na barra de título: é o primeiro dado que o suporte
        # pede, e é onde o cliente consegue lê-la sem abrir menu nenhum.
        self.setWindowTitle(f"{self.windowTitle()} — {__version__}")

        self.tabs = self.ui.tabs
        self.footer_label = self.ui.lblFooter
        self.btn_theme = self.ui.btnTheme
        self.btn_save = self.ui.btnSave

        self.tab_backups = BackupsTab(cfg, app_dir)
        self.tab_settings = SettingsTab(cfg, app_dir)
        self.tab_network = NetworkTab(cfg)
        for page, widget in ((self.ui.pageBackups, self.tab_backups),
                             (self.ui.pageSettings, self.tab_settings),
                             (self.ui.pageNetwork, self.tab_network)):
            layout: QVBoxLayout = page.layout()
            layout.addWidget(widget)

        for tab in (self.tab_backups, self.tab_settings, self.tab_network):
            tab.dirty_changed.connect(self._mark_dirty)
        self.tab_backups.run_requested.connect(self._run_now)
        self.tab_settings.password_change_requested.connect(self._change_password)
        self.tab_settings.shortcut_requested.connect(self._create_shortcut)

        self.btn_theme.clicked.connect(self._toggle_theme)
        self.btn_save.clicked.connect(self._save)
        self.ui.btnClose.clicked.connect(self.close)

        self._sync_theme_button()
        self._update_footer()
        self._install_shortcuts()

    # ------------------------------------------------------------- rodapé
    def _update_footer(self) -> None:
        cfg = self.cfg
        if cfg.last_run_unix:
            when = datetime.fromtimestamp(cfg.last_run_unix).strftime("%d/%m/%Y %H:%M")
            state = "OK" if cfg.last_run_status == "ok" else "COM FALHAS"
            run_text = f"Último backup: {when} · {state}"
        else:
            run_text = "Nenhum backup executado ainda"

        sets = len(cfg.sets)
        items = cfg.total_items()
        counts = (f"{sets} {'conjunto' if sets == 1 else 'conjuntos'} · "
                  f"{items} {'item' if items == 1 else 'itens'}")
        unsaved = "  ·  ALTERAÇÕES NÃO SALVAS" if self.dirty else ""
        self.footer_label.setText(f"{run_text}  ·  {counts}{unsaved}")

    def _mark_dirty(self) -> None:
        self.dirty = True
        self._update_footer()

    # --------------------------------------------------------- atalhos
    def _install_shortcuts(self) -> None:
        """Quem configura dez máquinas não larga o teclado."""
        tab = self.tab_backups
        bindings = [
            ("Ctrl+S", self._save, self.btn_save, "Salvar tudo"),
            ("F5", tab.new_backup_run, tab.btn_run, "Executar backup agora"),
            ("Ctrl+N", tab.new_item, tab.btn_item_new, "Novo item"),
            ("Ctrl+Shift+N", tab.new_set, tab.btn_set_new, "Novo conjunto"),
            ("Ctrl+D", tab.duplicate_item, tab.btn_item_dup, "Duplicar item"),
            ("Ctrl+Shift+D", tab.duplicate_set, tab.btn_set_dup, "Duplicar conjunto"),
            ("Ctrl+P", tab.show_preview, tab.btn_preview, "Prévia da árvore"),
            ("Ctrl+E", tab.show_destination, tab.btn_dest_info, "Espaço e limpeza"),
            ("Ctrl+T", self._toggle_theme, self.btn_theme, "Alternar tema"),
            ("Alt+Up", lambda: tab.move_item(-1), tab.btn_item_up, "Subir item"),
            ("Alt+Down", lambda: tab.move_item(1), tab.btn_item_down, "Descer item"),
        ]
        for keys, handler, button, label in bindings:
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.activated.connect(handler)
            if button is not None:
                # O atalho vive na dica do próprio botão: quem descobre o botão
                # descobre a tecla, sem precisar de uma tela de ajuda.
                button.setToolTip(f"{label}  ({keys})")

        for index, keys in enumerate(("Ctrl+1", "Ctrl+2", "Ctrl+3")):
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.activated.connect(lambda i=index: self.tabs.setCurrentIndex(i))

        QShortcut(QKeySequence("F2"), self).activated.connect(tab.focus_name)
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.close)

    # -------------------------------------------------------------- tema
    def _sync_theme_button(self) -> None:
        # O botão anuncia o destino, não o estado atual.
        self.btn_theme.setText("Tema claro" if theme.is_dark() else "Tema escuro")

    def _toggle_theme(self) -> None:
        self.cfg.dark_theme = not theme.is_dark()
        apply_theme(self.cfg.dark_theme)
        self._sync_theme_button()
        # Os ícones das listas são pixmaps já desenhados: precisam ser
        # regerados na paleta nova, senão ficam com a cor do tema anterior.
        self.tab_backups.refresh_all()
        self.tab_network._refresh()
        # A preferência é da máquina, não da sessão: grava na hora.
        self.cfg.save(self.cfg_path)
        self._update_footer()

    # ------------------------------------------------------------ comandos
    def _validate(self) -> str:
        """Devolve a primeira inconsistência encontrada, ou string vazia."""
        for bset in self.cfg.sets:
            if not bset.name:
                return "Há um conjunto sem nome. O nome vira o arquivo .zip."
            if not bset.destination:
                return f"O conjunto '{bset.name}' está sem destino do zip."
            for item in bset.items:
                if not item.name:
                    return f"Há um item sem nome no conjunto '{bset.name}'."
                if not item.source:
                    return f"O item '{item.name}' está sem origem."
        return ""

    def _save(self, silent: bool = False) -> bool:
        problem = self._validate()
        if problem:
            password.error(self, "Configuração incompleta.", problem)
            return False
        if not self.cfg.save(self.cfg_path):
            password.error(self, "Falha ao gravar o arquivo de configuração.",
                           f"Verifique a permissão de escrita em {self.cfg_path}")
            return False
        self.dirty = False
        self._update_footer()
        logger.info("Configuracoes salvas.")

        # O lembrete só existe de verdade quando a tarefa está no Agendador.
        # Salvar sem sincronizar deixaria a tela dizendo uma coisa e o Windows
        # fazendo outra.
        note = self._sync_reminder()
        if not silent:
            password.info(self, "Configurações salvas.", note)
        return True

    def _sync_reminder(self) -> str:
        """Alinha a tarefa agendada com o que está configurado."""
        from .. import reminder
        wanted = self.cfg.reminder_enabled
        installed = reminder.task_installed()
        if wanted == installed and not wanted:
            return ""

        ok, message = reminder.sync_task(self.cfg)
        if not ok:
            logger.warn(f"Lembrete: {message}")
            # Falhar aqui não invalida o resto: a configuração foi gravada.
            password.error(self, "A configuração foi salva, mas o lembrete "
                                 "não pôde ser agendado.", message)
            return ""
        self.tab_settings._update_reminder_hint()
        return message

    def _run_now(self) -> None:
        if self.dirty and not self._save(silent=True):
            return
        if not self.cfg.sets:
            password.error(self, "Nenhum conjunto configurado.")
            return
        # Reexecuta o próprio programa em modo /run: a janela de progresso é a
        # mesma que o atalho da área de trabalho abre, sem caminho alternativo.
        try:
            if getattr(sys, "frozen", False):
                args = [sys.executable, "/run"]
            else:
                args = [sys.executable, "-m", "backup_maximus", "/run"]
            subprocess.Popen(args, cwd=self.app_dir, close_fds=True)
        except OSError as exc:
            password.error(self, "Não foi possível iniciar o backup.", str(exc))

    def _change_password(self) -> None:
        if not password.prompt(self.cfg, first_run=True, parent=self):
            return
        if self._save(silent=True):
            password.info(self, "Senha alterada.",
                          "Ela passa a valer na próxima abertura das configurações.")

    def _create_shortcut(self) -> None:
        ok, detail = create_desktop_shortcut(self.app_dir)
        if ok:
            password.info(self, "Atalho criado na área de trabalho.", detail)
        else:
            password.error(self, "Não foi possível criar o atalho.", detail)

    def closeEvent(self, event) -> None:
        if self.dirty:
            box = QMessageBox(self)
            box.setWindowTitle("Backup Maximus")
            box.setIcon(QMessageBox.Question)
            box.setText("Há alterações não salvas.")
            box.setInformativeText("Salvar antes de sair?")
            save = box.addButton("Salvar e sair", QMessageBox.AcceptRole)
            discard = box.addButton("Sair sem salvar", QMessageBox.DestructiveRole)
            box.addButton("Cancelar", QMessageBox.RejectRole)
            box.setDefaultButton(save)
            box.exec()
            clicked = box.clickedButton()
            if clicked is save:
                if not self._save(silent=True):
                    event.ignore()
                    return
            elif clicked is not discard:
                event.ignore()
                return
        event.accept()


# ------------------------------------------------------------------ atalho
def create_desktop_shortcut(app_dir: str) -> tuple[bool, str]:
    """Cria 'Backup Maximus - Executar.lnk' apontando para o modo /run."""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        onedrive = os.environ.get("OneDrive", "")
        candidate = os.path.join(onedrive, "Desktop") if onedrive else ""
        if candidate and os.path.isdir(candidate):
            desktop = candidate
        else:
            return False, "Não foi possível localizar a área de trabalho."

    link = os.path.join(desktop, "Backup Maximus - Executar.lnk")

    if getattr(sys, "frozen", False):
        target, arguments = sys.executable, "/run"
    else:
        launcher = os.path.join(app_dir, "BackupMaximus.pyw")
        target = sys.executable.replace("python.exe", "pythonw.exe")
        arguments = (f'"{launcher}" /run' if os.path.isfile(launcher)
                     else "-m backup_maximus /run")

    # WScript.Shell via PowerShell evita depender de pywin32.
    script = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('"
        + link.replace("'", "''") + "'); "
        "$s.TargetPath = '" + target.replace("'", "''") + "'; "
        "$s.Arguments = '" + arguments.replace("'", "''") + "'; "
        "$s.WorkingDirectory = '" + app_dir.replace("'", "''") + "'; "
        "$s.Description = 'Executa o backup imediatamente'; "
        "$s.Save()"
    )
    code, out = util.run_process(
        ["powershell.exe", "-NoProfile", "-NonInteractive",
         "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=60,
    )
    if code != 0 or not os.path.isfile(link):
        return False, util.truncate(out, 300) or "O Windows recusou a criação do atalho."
    return True, link


# --------------------------------------------------------------- entrada
def apply_theme(dark: bool) -> None:
    """Troca a paleta e repinta a aplicação inteira."""
    theme.set_dark(dark)
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(theme.stylesheet())


def run(cfg: Config, cfg_path: str, app_dir: str, first_run: bool) -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("Backup Maximus")
    apply_theme(cfg.dark_theme)

    if not password.prompt(cfg, first_run):
        if first_run:
            logger.info("Definicao de senha cancelada na primeira execucao.")
        return 1

    if first_run:
        cfg.save(cfg_path)
        logger.info("Primeira execucao: senha de configuracao definida.")

    window = MainWindow(cfg, cfg_path, app_dir)
    window.show()
    app.exec()
    return 0
