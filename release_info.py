"""Versão e notas de lançamento, lidas das fontes que já existem.

O fluxo de release não pode ter a versão digitada num terceiro lugar: já são
duas (`__init__.py` e o `CHANGELOG.md`), e uma terceira dentro do YAML do
GitHub Actions divergiria na primeira pressa.

    python release_info.py --versao    imprime 2.1.0
    python release_info.py --tag       imprime v2.1.0
    python release_info.py --notas     imprime a seção do CHANGELOG dessa versão
    python release_info.py --notas --saida ARQ   grava a seção em UTF-8
    python release_info.py --conferir  valida que as duas fontes concordam

O `--conferir` é o que roda antes de publicar: se o `__version__` subiu e
ninguém escreveu a seção correspondente no CHANGELOG, a release sairia sem
notas, e é justamente na release que alguém procura o que mudou.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
INIT = os.path.join(RAIZ, "backup_maximus", "__init__.py")
CHANGELOG = os.path.join(RAIZ, "CHANGELOG.md")

_VERSAO_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.M)
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def versao() -> str:
    """A versão declarada no código — a fonte única."""
    with open(INIT, encoding="utf-8") as fh:
        achado = _VERSAO_RE.search(fh.read())
    if not achado:
        raise SystemExit("__version__ não encontrado em backup_maximus/__init__.py")
    return achado.group(1)


def notas(alvo: str = "") -> str:
    """A seção do CHANGELOG daquela versão, sem o cabeçalho dela.

    Vazio se não houver seção — o chamador decide se isso é erro.
    """
    alvo = alvo or versao()
    with open(CHANGELOG, encoding="utf-8") as fh:
        texto = fh.read()

    # Casa "## [2.1.0] — 2026-09-01" e para no próximo "## " de mesmo nível.
    padrao = re.compile(
        r"^##\s*\[" + re.escape(alvo) + r"\][^\n]*\n(.*?)(?=^##\s|\Z)",
        re.M | re.S)
    achado = padrao.search(texto)
    if not achado:
        return ""
    corpo = achado.group(1)
    # A régua que separa as seções não faz sentido solta nas notas.
    corpo = re.sub(r"^---\s*$", "", corpo, flags=re.M)
    return corpo.strip()


def conferir() -> list[str]:
    """Problemas que impediriam uma release honesta. Vazio = pode publicar."""
    problemas = []
    v = versao()

    if not _SEMVER_RE.match(v):
        problemas.append(
            f"versão '{v}' não é MAIOR.MENOR.CORREÇÃO — a tag e as propriedades "
            f"do .exe dependem desse formato")

    corpo = notas(v)
    if not corpo:
        problemas.append(
            f"o CHANGELOG.md não tem seção '## [{v}]'. A release sairia sem "
            f"notas, e é nelas que alguém procura o que mudou")
    elif len(corpo) < 40:
        problemas.append(f"a seção '## [{v}]' do CHANGELOG está quase vazia")

    with open(CHANGELOG, encoding="utf-8") as fh:
        changelog = fh.read()
    nao_lancado = re.search(r"^##\s*\[Não lançado\][^\n]*\n(.*?)(?=^##\s|\Z)",
                            changelog, re.M | re.S)
    # A régua que separa as seções entra na captura e não é conteúdo. Sem
    # descontá-la, "Nada ainda." nunca casaria e a verificação reprovaria
    # sempre — um guarda que grita toda vez deixa de ser lido.
    sobrou = (re.sub(r"^---\s*$", "", nao_lancado.group(1), flags=re.M).strip()
              if nao_lancado else "")
    if sobrou not in ("", "Nada ainda."):
        problemas.append(
            "há conteúdo em '## [Não lançado]' no CHANGELOG. Mova-o para a "
            f"seção da versão {v} antes de publicar, ou ele não aparecerá "
            f"nas notas da release")

    return problemas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--versao", action="store_true")
    grupo.add_argument("--tag", action="store_true")
    grupo.add_argument("--notas", action="store_true")
    grupo.add_argument("--conferir", action="store_true")
    # Redirecionar a saída no Windows grava em cp1252, e os acentos chegam
    # corrompidos às notas da release. Gravando aqui, a codificação é nossa.
    ap.add_argument("--saida", default="",
                    help="grava a saída neste arquivo, em UTF-8")
    args = ap.parse_args()

    def emitir(texto: str) -> None:
        if args.saida:
            with open(args.saida, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(texto + "\n")
        else:
            print(texto)

    if args.versao:
        emitir(versao())
    elif args.tag:
        emitir(f"v{versao()}")
    elif args.notas:
        emitir(notas() or f"Versão {versao()}.")
    else:
        problemas = conferir()
        for p in problemas:
            print(f"  [!] {p}")
        if problemas:
            return 1
        print(f"  OK — versão {versao()} com notas no CHANGELOG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
