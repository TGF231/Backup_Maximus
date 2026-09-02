"""Confere o que foi realmente empacotado, antes de distribuir.

Excluir a PyQt6 no `.spec` é uma intenção; o que vale é o que saiu em `dist/`.
Um hook novo do PyInstaller, uma dependência que passe a importá-la, ou alguém
que edite o spec sem entender o porquê, e a GPL entra no produto sem aviso.

Este script roda no fim do `build_exe.bat` e reprova o build se encontrar
problema. Uso avulso:

    python vendor/auditar_pacote.py
"""

from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(RAIZ, "dist")

#: Nomes que, dentro do pacote, indicam biblioteca copyleft forte. A PyQt é
#: GPLv3: num produto distribuído fechado, ela contamina tudo.
PROIBIDOS = ("pyqt5", "pyqt6", "qt5core", "sip.")

#: Licenças que a distribuição precisa carregar, e de quem.
LICENCAS = {
    "licenses/LGPL-3.0.txt": "PySide6/Qt (LGPLv3)",
    "licenses/GPL-3.0.txt": "referida pela LGPLv3",
    "vendor/rclone/License.txt": "rclone (MIT)",
    "vendor/7zip/License.txt": "7-Zip (LGPL)",
}


def _arquivos(raiz: str) -> list[str]:
    encontrados = []
    for base, _dirs, arqs in os.walk(raiz):
        for a in arqs:
            caminho = os.path.join(base, a)
            encontrados.append(os.path.relpath(caminho, raiz).replace("\\", "/"))
    return encontrados


def auditar_pasta(pasta: str) -> list[str]:
    """Problemas encontrados na build em pasta. Lista vazia = aprovado."""
    problemas = []
    arquivos = _arquivos(pasta)
    minusculas = [a.lower() for a in arquivos]

    for proibido in PROIBIDOS:
        achados = [a for a, m in zip(arquivos, minusculas) if proibido in m]
        if achados:
            problemas.append(
                f"biblioteca copyleft no pacote ({proibido}): "
                + ", ".join(achados[:3])
                + (f" e mais {len(achados) - 3}" if len(achados) > 3 else ""))

    for relativo, dono in LICENCAS.items():
        alvo = relativo.lower()
        # A ferramenta pode não ter sido embutida; a licença só é exigida
        # quando o binário correspondente está lá.
        binario = os.path.dirname(alvo)
        tem_binario = any(m.startswith(binario) and m.endswith(".exe")
                          for m in minusculas)
        if binario.startswith("vendor") and not tem_binario:
            continue
        if not any(m.endswith(alvo) for m in minusculas):
            problemas.append(f"falta a licença de {dono}: {relativo}")

    return problemas


def main() -> int:
    pasta = os.path.join(DIST, "BackupMaximus")
    unico = os.path.join(DIST, "BackupMaximus.exe")

    print("=" * 66)
    print(" Backup Maximus — auditoria do pacote")
    print("=" * 66)

    if not os.path.isdir(pasta):
        print("A build em pasta não existe — gere com build_exe.bat.")
        print("Sem ela não há como conferir o conteúdo nem cumprir a LGPL do Qt.")
        return 1

    arquivos = _arquivos(pasta)
    tamanho = sum(os.path.getsize(os.path.join(pasta, a)) for a in arquivos)
    print(f"Pasta   : {len(arquivos)} arquivo(s), {tamanho / 1024 / 1024:,.1f} MB")
    if os.path.isfile(unico):
        print(f"Unico   : {os.path.getsize(unico) / 1024 / 1024:,.1f} MB")
    else:
        print("Unico   : ausente")

    problemas = auditar_pasta(pasta)
    print()
    if problemas:
        print("REPROVADO:")
        for p in problemas:
            print(f"  - {p}")
        print()
        print("A PyQt6 é GPLv3: se ela estiver no pacote, o produto distribuído")
        print("teria de ser GPLv3 também. Confira os excludes do .spec.")
        return 1

    print("APROVADO — nenhuma biblioteca copyleft forte, licenças presentes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
