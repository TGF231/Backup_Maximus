"""Compacta a árvore de montagem inteira em UM arquivo .zip.

Usa 7-Zip quando disponível (mais rápido em árvores grandes e com controle real
do nível de compressão). Sem ele, cai no módulo zipfile da biblioteca padrão —
que, ao contrário do fallback por PowerShell da versão C++, não depende de nada
externo e permite acompanhar o progresso arquivo a arquivo.
"""

from __future__ import annotations

import os
import shutil
import zipfile
from typing import Callable

from . import logger, util

ProgressCb = Callable[[int, str], None] | None


def find_sevenzip(hint: str = "") -> str:
    """Procura o 7-Zip: informado, empacotado com o app, ou instalado no sistema.

    A cópia empacotada vem primeiro de propósito: numa máquina de cliente sem
    7-Zip instalado, é ela que garante compactação rápida sem depender de o
    técnico lembrar de instalar nada.
    """
    if hint and os.path.isfile(hint):
        return hint

    from .paths import find_vendor_tool
    bundled = find_vendor_tool("7za.exe", "7z.exe")
    if bundled:
        return bundled

    for candidate in (
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ):
        if os.path.isfile(candidate):
            return candidate
    return shutil.which("7z") or shutil.which("7za") or ""


class Archiver:
    def __init__(self, sevenzip_hint: str = ""):
        self.sevenzip = find_sevenzip(sevenzip_hint)

    @property
    def tool_description(self) -> str:
        return f"7-Zip: {self.sevenzip}" if self.sevenzip else "zipfile (biblioteca padrao do Python)"

    # ------------------------------------------------------------------ 7-Zip
    def _run_7z(self, args: list[str]) -> tuple[bool, str]:
        code, out = util.run_process([self.sevenzip] + args + ["-y", "-bd"])
        if code == 0:
            return True, ""
        if code == 1:  # avisos: algum arquivo estava em uso e foi pulado
            logger.warn(f"7-Zip terminou com avisos: {util.truncate(out, 300)}")
            return True, ""
        return False, f"7z retornou {code}: {util.truncate(out)}"

    # ---------------------------------------------------------------- zipfile
    @staticmethod
    def _archive_with_zipfile(
        tree_dir: str,
        zip_path: str,
        max_compression: bool,
        progress: ProgressCb,
    ) -> tuple[bool, str]:
        root_name = os.path.basename(os.path.normpath(tree_dir)) or "BACKUP"
        level = 9 if max_compression else 1

        files: list[tuple[str, str]] = []
        for root, _dirs, names in os.walk(tree_dir):
            for name in names:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, tree_dir)
                # Mantém a pasta raiz dentro do zip, como o WinRAR fazia com C:\BACKUP
                files.append((full, os.path.join(root_name, rel)))

        if not files:
            return False, f"Nada para compactar em {tree_dir}"

        try:
            with zipfile.ZipFile(
                zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=level
            ) as zf:
                for index, (full, arcname) in enumerate(files, 1):
                    try:
                        zf.write(full, arcname)
                    except OSError as exc:
                        # Arquivo em uso não invalida o zip inteiro.
                        logger.warn(f"Arquivo pulado na compactacao: {full} ({exc})")
                    if progress is not None:
                        pct = int(index * 100 / len(files))
                        progress(pct, arcname)
        except OSError as exc:
            return False, f"Falha ao gravar {zip_path}: {exc}"
        return True, ""

    # ------------------------------------------------------------------ API
    def archive_tree(
        self,
        tree_dir: str,
        zip_path: str,
        max_compression: bool,
        update: bool,
        progress: ProgressCb = None,
    ) -> tuple[bool, str]:
        """Compacta todo o conteúdo de tree_dir preservando a hierarquia."""
        if not os.path.isdir(tree_dir):
            return False, f"Arvore de montagem nao encontrada: {tree_dir}"

        if not update and os.path.isfile(zip_path):
            try:
                os.unlink(zip_path)
            except OSError as exc:
                return False, f"Nao foi possivel substituir {zip_path}: {exc}"

        if self.sevenzip:
            level = "-mx9" if max_compression else "-mx1"
            verb = "u" if update else "a"
            # -ssw inclui arquivos abertos para escrita (bancos e logs em uso).
            return self._run_7z([verb, "-tzip", level, "-ssw", "-r", zip_path, tree_dir])

        # O zipfile não sabe atualizar no lugar; para o modo incremental,
        # regravar o zip a partir da árvore dá o mesmo resultado — e a árvore
        # já é incremental, que é onde o tempo realmente é economizado.
        return self._archive_with_zipfile(tree_dir, zip_path, max_compression, progress)

    def add_file(self, zip_path: str, file_path: str) -> tuple[bool, str]:
        """Acrescenta/substitui um arquivo na raiz do zip."""
        if not os.path.isfile(file_path):
            return False, f"Arquivo nao encontrado: {file_path}"

        if self.sevenzip:
            return self._run_7z(["u", "-tzip", "-mx1", zip_path, file_path])

        try:
            with zipfile.ZipFile(zip_path, "a", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(file_path, os.path.basename(file_path))
        except OSError as exc:
            return False, f"Falha ao anexar em {zip_path}: {exc}"
        return True, ""

    def extract_file(self, zip_path: str, entry_name: str, dest_dir: str) -> tuple[bool, str]:
        """Extrai uma entrada (pelo nome do arquivo) para dest_dir."""
        os.makedirs(dest_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                match = next(
                    (n for n in zf.namelist()
                     if os.path.basename(n).lower() == entry_name.lower()),
                    None,
                )
                if match is None:
                    return False, f"'{entry_name}' nao encontrado em {zip_path}"
                target = os.path.join(dest_dir, os.path.basename(match))
                with zf.open(match) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        except (OSError, zipfile.BadZipFile) as exc:
            return False, f"Falha ao extrair de {zip_path}: {exc}"
        return True, ""
