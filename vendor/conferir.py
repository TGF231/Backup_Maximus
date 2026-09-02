"""Mostra que ferramentas de terceiros o programa vai usar, e de onde.

    python vendor\\conferir.py                relatório legível
    python vendor\\conferir.py --pyinstaller  argumentos --add-data para o build

O relatório existe porque "não achou o 7-Zip" é um problema chato de diagnosticar
no escuro: a busca aceita várias arrumações de pasta, e é bom poder ver qual
arquivo, exatamente, foi escolhido.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backup_maximus import paths  # noqa: E402
from backup_maximus.archive import find_sevenzip  # noqa: E402
from backup_maximus.cloud import find_rclone, version as rclone_version  # noqa: E402
from backup_maximus.util import format_bytes, run_process  # noqa: E402


def _size(path: str) -> str:
    try:
        return format_bytes(os.path.getsize(path))
    except OSError:
        return "?"


def _seven_version(exe: str) -> str:
    code, out = run_process([exe], timeout=20)
    # O 7za sem argumentos imprime o cabeçalho e sai com código 0 ou 7.
    for line in (out or "").splitlines():
        if line.strip().startswith("7-Zip"):
            return line.strip()
    return "versão não identificada"


def pyinstaller_args() -> str:
    """Argumentos --add-data para o build_exe.bat consumir."""
    parts = []
    for source, target in paths.bundle_files():
        parts.append(f'--add-data "{source};{target}"')
    return " ".join(parts)


def report() -> int:
    print("=" * 66)
    print(" Backup Maximus — ferramentas de terceiros")
    print("=" * 66)
    print(f"Pasta vendor : {paths.vendor_dir()}")
    print(f"Arquitetura  : {paths.arch_order()[0] or 'x86'}")
    print()

    ok = True

    seven = find_sevenzip()
    if seven:
        origem = "vendor/" if paths.vendor_dir().lower() in seven.lower() else "sistema"
        print(f"7-Zip    ENCONTRADO  ({origem}, {_size(seven)})")
        print(f"         {seven}")
        print(f"         {_seven_version(seven)}")
    else:
        ok = False
        print("7-Zip    AUSENTE")
        print("         Sem ele a compactação usa o zipfile do Python: funciona,")
        print("         mas é mais lenta em árvores grandes.")
        print("         Baixe o pacote '7-Zip Extra' em https://www.7-zip.org/download.html")
        print("         e extraia em vendor/ (qualquer subpasta serve).")
    print()

    rclone = find_rclone()
    if rclone:
        origem = "vendor/" if paths.vendor_dir().lower() in rclone.lower() else "sistema"
        print(f"rclone   ENCONTRADO  ({origem}, {_size(rclone)})")
        print(f"         {rclone}")
        print(f"         {rclone_version() or 'versão não identificada'}")
    else:
        ok = False
        print("rclone   AUSENTE")
        print("         Sem ele não há envio à nuvem (Drive, OneDrive, MEGA).")
        print("         winget install Rclone.Rclone   ou   python vendor\\baixar_ferramentas.py")
    print()

    bundle = paths.bundle_files()
    if bundle:
        total = sum(os.path.getsize(s) for s, _t in bundle if os.path.isfile(s))
        print("-" * 66)
        print(f"O build_exe.bat vai embutir {len(bundle)} arquivo(s), "
              f"{format_bytes(total)} no total:")
        for source, target in bundle:
            print(f"   {target}/{os.path.basename(source)}  ({_size(source)})")

        # Distribuir binário de terceiro sem o texto da licença é problema
        # jurídico de quem distribui, e passa despercebido facilmente.
        faltando = _missing_licenses(bundle)
        if faltando:
            ok = False
            print()
            print("   ATENÇÃO — licença ausente:")
            for tool, obrigacao in faltando:
                print(f"     {tool}: {obrigacao}")
            print("     Baixe o arquivo de licença do projeto e coloque junto do")
            print("     executável em vendor/, para ele entrar no pacote.")

        if total > 50 * 1024 * 1024:
            print()
            print("   O rclone sozinho passa de 80 MB. Se o executável ficar grande")
            print("   demais para copiar por rede, uma alternativa é distribuir a")
            print("   pasta vendor/ ao lado do .exe: o programa procura ali primeiro.")
    return 0 if ok else 1


#: O que cada ferramenta exige de quem redistribui.
_LICENSE_DUTY = {
    "vendor/7zip": ("7-Zip", "LGPL 2.1+ — o texto da licença deve acompanhar o binário"),
    "vendor/rclone": ("rclone", "MIT — o aviso de copyright deve acompanhar o binário"),
}


def _missing_licenses(bundle: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Ferramentas no pacote que vão sem o arquivo de licença."""
    por_pasta: dict[str, list[str]] = {}
    for source, target in bundle:
        por_pasta.setdefault(target, []).append(os.path.basename(source).lower())

    faltando = []
    for target, arquivos in por_pasta.items():
        tem_licenca = any(
            nome.startswith(("license", "copying")) for nome in arquivos
        )
        if not tem_licenca and target in _LICENSE_DUTY:
            faltando.append(_LICENSE_DUTY[target])
    return faltando


if __name__ == "__main__":
    if "--pyinstaller" in sys.argv:
        print(pyinstaller_args())
        sys.exit(0)
    sys.exit(report())
