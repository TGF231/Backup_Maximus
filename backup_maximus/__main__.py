"""Ponto de entrada e despacho dos modos de execução.

  BackupMaximus            abre as configurações (pede senha)
  BackupMaximus /run       Quick Run: executa com janela de progresso
  BackupMaximus /silent    executa sem interface (Agendador de Tarefas)
  BackupMaximus /check     verifica atraso e dispara alerta
  BackupMaximus /check /quiet   idem, sem caixa de mensagem
  BackupMaximus /remind    mostra o lembrete de backup (usado pelo Agendador)
  BackupMaximus /version   imprime a versão e sai
  BackupMaximus /autoteste carrega os formulários e sai (usado no build)

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


def _autoteste() -> int:
    """Carrega todos os formulários e sai. Sem janela, sem configuração.

    Existe para o build conseguir responder "o programa abre?" antes de
    publicar. Os formulários são importados por `importlib` a partir do nome
    do `.ui`, e import dinâmico é invisível para o PyInstaller: na 2.2.0 o
    pacote `generated` ficou de fora, o executável foi empacotado, auditado e
    instalado, e só falhou na primeira tela — na máquina do cliente.
    """
    try:
        from PySide6.QtWidgets import QApplication
        from .ui import forms
    except ImportError as exc:
        print(f"FALHOU: interface indisponivel: {exc}")
        return 1

    # Precisa de uma QApplication viva: as classes geradas sao widgets.
    QApplication.instance() or QApplication([])

    faltando = []
    for nome in sorted(forms.FORMS):
        try:
            forms.load(nome)
        except Exception as exc:
            faltando.append(f"{nome}: {type(exc).__name__}: {exc}")

    if faltando:
        print("FALHOU: formularios que nao carregam:")
        for linha in faltando:
            print(f"  - {linha}")
        return 1

    # As fontes vao como dado, fora do import: o PyInstaller nao as acha
    # sozinho. Sem elas a janela abre, mas com um substituto mais largo que
    # corta campos medidos no Designer.
    from .ui import theme
    if not theme.carregar_fontes():
        print(f"FALHOU: fontes do MegUI ausentes em {theme.FONTES_DIR}")
        return 1

    print(f"FORMULARIOS OK ({len(forms.FORMS)}) - FONTES OK")
    return 0


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
        #
        # Imprime também ONDE os dados moram. Descobrir isso exigia abrir o
        # programa e ler a tela Sobre, e quando a configuração "some" o que
        # se precisa saber é exatamente qual arquivo ele está lendo — foi o
        # que faltou para diagnosticar uma senha perdida num cliente.
        from .paths import (INSTALLED_MARKER, PORTABLE_MARKER, app_data_dir,
                            install_dir)
        casa = install_dir()
        dados = app_data_dir()
        if os.environ.get("BM_HOME", "").strip():
            motivo = "BM_HOME"
        elif os.path.isfile(os.path.join(casa, PORTABLE_MARKER)):
            motivo = PORTABLE_MARKER
        elif os.path.isfile(os.path.join(casa, INSTALLED_MARKER)):
            motivo = INSTALLED_MARKER
        elif dados == casa:
            motivo = "pasta do programa (gravavel)"
        else:
            motivo = "pasta do programa nao aceita gravacao"

        ini = Config.default_path(dados)
        print(f"Backup Maximus {__version__}")
        print(f"Programa : {casa}")
        print(f"Dados    : {dados}  ({motivo})")
        print(f"Config   : {ini}  "
              f"{'existe' if os.path.isfile(ini) else 'AUSENTE'}")
        return 0

    if "autoteste" in flags:
        return _autoteste()

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
