r"""Gera o instalador do Backup Maximus com o Inno Setup.

Roda depois do `build_exe.bat`, sobre a build em pasta (`dist\BackupMaximus`).
É essa build que vai para dentro do instalador, e não o executável único: a
LGPLv3 da PySide6/Qt exige que o usuário possa substituir a biblioteca Qt, o
que só é possível com as DLLs soltas.

    python installer/gerar_instalador.py
    python installer/gerar_instalador.py --conferir   só diz se dá para gerar

Sem o Inno Setup instalado o script explica como obtê-lo e sai com erro, em vez
de deixar a release sair sem instalador e ninguém perceber.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(RAIZ, "installer", "BackupMaximus.iss")
PASTA_BUILD = os.path.join(RAIZ, "dist", "BackupMaximus")

#: Onde o Inno Setup 6 costuma se instalar. O `where` cobre quem o pôs no PATH.
_CANDIDATOS = (
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
)


def achar_iscc() -> str:
    """Compilador do Inno Setup, ou string vazia."""
    encontrado = shutil.which("iscc") or shutil.which("ISCC")
    if encontrado:
        return encontrado
    for caminho in _CANDIDATOS:
        if os.path.isfile(caminho):
            return caminho
    return ""


def versao() -> str:
    """A mesma versão do aplicativo — nunca uma cópia digitada aqui."""
    sys.path.insert(0, RAIZ)
    import release_info
    return release_info.versao()


def conferir() -> list[str]:
    """O que impede de gerar o instalador. Vazio = pode gerar."""
    problemas = []
    if not achar_iscc():
        problemas.append(
            "Inno Setup 6 não encontrado. Instale com "
            "'winget install JRSoftware.InnoSetup' ou baixe em "
            "https://jrsoftware.org/isdl.php")
    if not os.path.isdir(PASTA_BUILD):
        problemas.append(
            f"A build em pasta não existe: {PASTA_BUILD}. "
            f"Rode o build_exe.bat antes.")
    elif not os.path.isfile(os.path.join(PASTA_BUILD, "BackupMaximus.exe")):
        problemas.append(f"{PASTA_BUILD} existe mas não tem BackupMaximus.exe.")
    if not os.path.isfile(SCRIPT):
        problemas.append(f"Script do instalador ausente: {SCRIPT}")
    return problemas


def gerar() -> int:
    problemas = conferir()
    if problemas:
        for p in problemas:
            print(f"  [!] {p}")
        return 1

    v = versao()
    iscc = achar_iscc()
    print(f"  Inno Setup : {iscc}")
    print(f"  Versão     : {v}")
    print(f"  Payload    : {PASTA_BUILD}")
    print()

    resultado = subprocess.run(
        [iscc, f"/DAppVersion={v}", SCRIPT],
        cwd=os.path.join(RAIZ, "installer"),
        capture_output=True, text=True, encoding="utf-8", errors="replace")

    if resultado.returncode != 0:
        print(resultado.stdout[-3000:])
        print(resultado.stderr[-2000:])
        print(f"\n  [!] o Inno Setup falhou (código {resultado.returncode})")
        return resultado.returncode

    saida = os.path.join(RAIZ, "dist", f"BackupMaximus-{v}-instalador.exe")
    if not os.path.isfile(saida):
        print("  [!] o Inno Setup terminou bem mas o arquivo não apareceu:")
        print(f"      {saida}")
        return 1

    mb = os.path.getsize(saida) / 1024 / 1024
    print(f"  OK -> {saida}  ({mb:,.1f} MB)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conferir", action="store_true",
                    help="apenas verifica se dá para gerar")
    args = ap.parse_args()

    print("=" * 66)
    print(" Backup Maximus — instalador")
    print("=" * 66)

    if args.conferir:
        problemas = conferir()
        for p in problemas:
            print(f"  [!] {p}")
        if not problemas:
            print(f"  OK — pronto para gerar a versão {versao()}.")
        return 1 if problemas else 0

    return gerar()


if __name__ == "__main__":
    sys.exit(main())
