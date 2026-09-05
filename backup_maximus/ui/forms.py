"""Ponte entre os arquivos .ui do Qt Designer e o código.

Os layouts ficam em `designer/*.ui` e são compilados por `pyside6-uic` para
`backup_maximus/ui/generated/ui_*.py`. Os arquivos gerados são versionados, de
modo que a aplicação roda mesmo onde o `uic` não existe (uma máquina só com o
runtime, ou o .exe empacotado).

Em desenvolvimento a compilação é automática: se o `.ui` for mais novo que o
`.py` gerado, este módulo regera antes de importar. Assim você edita a tela no
Qt Designer, roda a aplicação, e a mudança já está lá — sem passo de build
para esquecer.
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
from types import ModuleType

from .. import logger

#: designer/<nome>.ui  ->  backup_maximus/ui/generated/ui_<nome>.py
_UI_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "designer",
)
_GENERATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
_GENERATED_PACKAGE = "backup_maximus.ui.generated"

#: Formulários disponíveis: nome do .ui -> classe gerada.
FORMS = {
    "main_window": "Ui_MainWindow",
    "tab_backups": "Ui_TabBackups",
    "tab_settings": "Ui_TabSettings",
    "tab_network": "Ui_TabNetwork",
    "dialog_password": "Ui_PasswordDialog",
    "dialog_preview_tree": "Ui_TreePreviewDialog",
    "dialog_destination": "Ui_DestinationDialog",
    "window_progress": "Ui_ProgressWindow",
    "dialog_aliases": "Ui_AliasDialog",
    "dialog_cloud": "Ui_CloudDialog",
    "dialog_cloud_setup": "Ui_CloudSetupDialog",
    "dialog_about": "Ui_DialogAbout",
    "dialog_profile": "Ui_ProfileDialog",
}


def _uic_command() -> list[str] | None:
    """Como invocar o compilador de .ui, se ele existir nesta máquina."""
    exe = shutil.which("pyside6-uic")
    if exe:
        return [exe]
    try:
        import PySide6
        candidate = os.path.join(os.path.dirname(PySide6.__file__), "uic.exe")
        if os.path.isfile(candidate):
            return [candidate, "-g", "python"]
    except ImportError:
        pass
    return None


def compile_form(name: str, force: bool = False) -> bool:
    """Compila designer/<name>.ui se estiver desatualizado. True se recompilou."""
    source = os.path.join(_UI_DIR, f"{name}.ui")
    target = os.path.join(_GENERATED_DIR, f"ui_{name}.py")

    if not os.path.isfile(source):
        return False
    if not force and os.path.isfile(target):
        try:
            if os.path.getmtime(target) >= os.path.getmtime(source):
                return False
        except OSError:
            pass

    command = _uic_command()
    if command is None:
        # Sem uic: seguimos com o .py gerado que já existe. Só é um problema
        # se ele também faltar, e aí o import adiante falha com mensagem clara.
        logger.warn(f"pyside6-uic nao encontrado; usando ui_{name}.py existente.")
        return False

    os.makedirs(_GENERATED_DIR, exist_ok=True)
    try:
        result = subprocess.run(
            command + [source, "-o", target],
            capture_output=True, text=True,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
    except OSError as exc:
        logger.warn(f"Falha ao executar o uic para {name}: {exc}")
        return False

    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        logger.error(f"uic falhou em {name}.ui: {message}")
        # Um .ui quebrado não pode derrubar a aplicação em produção se já
        # existe um .py gerado bom; sem ele, não há o que fazer.
        if not os.path.isfile(target):
            raise RuntimeError(f"Nao foi possivel compilar {source}:\n{message}")
        return False

    logger.info(f"Formulario recompilado: {name}.ui")
    return True


def compile_all(force: bool = False) -> list[str]:
    """Compila todos os formulários desatualizados. Devolve os que mudaram."""
    return [name for name in FORMS if compile_form(name, force)]


def load(name: str) -> type:
    """Devolve a classe Ui_* do formulário, recompilando se necessário."""
    if name not in FORMS:
        raise KeyError(f"Formulario desconhecido: {name}")

    recompiled = compile_form(name)
    module_name = f"{_GENERATED_PACKAGE}.ui_{name}"

    module: ModuleType | None = sys.modules.get(module_name)
    if module is not None and recompiled:
        module = importlib.reload(module)
    elif module is None:
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise ImportError(
                f"Formulario '{name}' nao compilado. Rode build_ui.bat "
                f"(ou instale o PySide6 completo para a compilacao automatica)."
            ) from exc

    return getattr(module, FORMS[name])
