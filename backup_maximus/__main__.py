"""Ponto de entrada e despacho dos modos de execução.

  BackupMaximus            abre as configurações (pede senha)
  BackupMaximus /run       Quick Run: executa com janela de progresso
  BackupMaximus /silent    executa sem interface (Agendador de Tarefas)
  BackupMaximus /check     verifica atraso e dispara alerta
  BackupMaximus /check /quiet   idem, sem caixa de mensagem
  BackupMaximus /remind    mostra o lembrete de backup (usado pelo Agendador)
  BackupMaximus /version   imprime a versão e sai

Códigos de saída: 0 = tudo certo · 1 = houve falha · 2 = alerta disparado.
"""

from __future__ import annotations

import os
import sys

from . import __version__, engine, logger
from .config import Config


def app_dir() -> str:
    """Pasta onde ficam config, logs e relatórios (ver backup_maximus.paths)."""
    from .paths import app_data_dir
    return app_data_dir()


def _load_config(cfg_path: str, directory: str) -> tuple[Config, bool]:
    """Devolve (config, é_primeira_execução)."""
    cfg = Config.load(cfg_path)
    if cfg is None:
        # Persistência: se o INI sumiu, tenta recuperar de dentro do .zip de
        # backup mais recente que esteja ao lado do executável.
        if engine.recover_config_from_zip(directory, cfg_path):
            cfg = Config.load(cfg_path)
    if cfg is None:
        cfg = Config()
    return cfg, not cfg.has_password


def parse_flags(argv: list[str]) -> set[str]:
    """Normaliza os argumentos em nomes de flag.

    Aceita /silent, -silent e --silent, em qualquer caixa. Também tolera o
    argumento chegar como caminho: shells POSIX no Windows (Git Bash, MSYS)
    convertem '/silent' em algo como 'C:/Git/silent' antes de entregar ao
    programa, e ficar refém disso já custou depuração.
    """
    flags: set[str] = set()
    for raw in argv:
        token = raw.strip().lower().replace("\\", "/")
        token = token.rsplit("/", 1)[-1]
        token = token.lstrip("-")
        if token:
            flags.add(token)
    return flags


def main(argv: list[str] | None = None) -> int:
    flags = parse_flags(argv if argv is not None else sys.argv[1:])
    directory = app_dir()
    logger.init(directory)

    cfg_path = Config.default_path(directory)
    cfg, first_run = _load_config(cfg_path, directory)

    # ---------------------------------------------------------- watchdog
    if "version" in flags:
        # Sem interface e sem log: serve para o instalador e para o suporte
        # conferirem o que está na máquina do cliente.
        print(f"Backup Maximus {__version__}")
        return 0

    if "check" in flags:
        alerted, message = engine.check_overdue(cfg)
        if alerted and "quiet" not in flags:
            _message_box(message, warning=True)
        return 2 if alerted else 0

    # ---------------------------------------------------------- lembrete
    if "remind" in flags:
        from . import reminder
        return reminder.notify(cfg)

    # ------------------------------------------------- execução silenciosa
    if "silent" in flags:
        if not cfg.sets:
            logger.error("Execucao silenciosa abortada: nenhum conjunto configurado.")
            return 1
        result = engine.run_backups(cfg, cfg_path, directory)
        return 0 if result.all_ok else 1

    # ------------------------------------------------------------ Quick Run
    if "run" in flags:
        if not cfg.sets:
            _message_box(
                "Nenhum backup foi configurado ainda.\n\n"
                "Abra o Backup Maximus sem parâmetros para configurar."
            )
            return 1
        from .ui import progress
        return progress.run(cfg, cfg_path, directory)

    # ------------------------------------------------ configuração (padrão)
    from .ui import app as ui_app
    return ui_app.run(cfg, cfg_path, directory, first_run)


def _message_box(text: str, warning: bool = False) -> None:
    """Aviso avulso sem exigir que a interface completa esteja carregada."""
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        instance = QApplication.instance() or QApplication([])
        box = QMessageBox()
        box.setWindowTitle("Backup Maximus")
        box.setIcon(QMessageBox.Warning if warning else QMessageBox.Information)
        box.setText(text)
        box.exec()
        del instance
    except Exception:
        print(text)


if __name__ == "__main__":
    sys.exit(main())
