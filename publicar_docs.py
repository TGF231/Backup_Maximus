"""Monta o repositório público de documentos a partir de docs/.

O código do Backup Maximus é privado, mas a política de privacidade e os termos
precisam de URL pública: o Google confere esses endereços para liberar o
branding do aplicativo, e um cliente tem direito de ler os termos sem pedir
acesso a ninguém.

Duas cópias do mesmo documento divergem — sempre. Por isso a fonte é uma só,
`docs/` neste repositório, e o repositório público é **gerado**. Editar
diretamente lá é o começo do problema que este script existe para evitar.

    python publicar_docs.py                 monta em ../backup-maximus-docs
    python publicar_docs.py --destino PASTA  monta em outro lugar
    python publicar_docs.py --conferir       só relata o que mudaria

Depois de rodar, revise o `git diff` na pasta gerada e publique de lá.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
DESTINO_PADRAO = os.path.join(os.path.dirname(RAIZ), "backup-maximus-docs")

#: O que vai para o repositório público: origem -> (arquivo, título, URL).
#: A URL é fixada aqui porque ela vai colada no console do Google Cloud —
#: deixá-la a cargo do padrão do Jekyll faria o endereço mudar sozinho numa
#: atualização da plataforma, e um link de política de privacidade quebrado
#: derruba o consentimento do aplicativo.
ARQUIVOS = {
    "docs/privacidade.md": ("privacidade.md", "Política de Privacidade",
                            "/privacidade/"),
    "docs/termos.md": ("termos.md", "Termos de Serviço", "/termos/"),
    "THIRD_PARTY_NOTICES.md": ("avisos-de-terceiros.md",
                               "Avisos de componentes de terceiros",
                               "/avisos-de-terceiros/"),
}

#: Links relativos que só fazem sentido dentro do repositório privado. Apontar
#: para lá deixaria o leitor diante de um 404 ou de um pedido de acesso.
REESCRITAS = {
    "../THIRD_PARTY_NOTICES.md": "../avisos-de-terceiros/",
    "privacidade.md": "../privacidade/",
    "../CHANGELOG.md": "",          # vazio = remove o link, mantém o texto
    "backup_maximus/oauth_app.py": "",
    "vendor/conferir.py": "",
}

INDICE = """# Backup Maximus — documentos

Documentos oficiais do **Backup Maximus**, aplicativo de backup para Windows da
WALYTECH SOLUÇÕES TECNOLÓGICAS LTDA.

- [Política de Privacidade](privacidade/)
- [Termos de Serviço](termos/)
- [Avisos de componentes de terceiros](avisos-de-terceiros/)

Este repositório contém apenas os documentos. O código-fonte do aplicativo não
é público.

## Resumo da privacidade

O Backup Maximus funciona inteiramente no computador do usuário. Não há
telemetria, não operamos servidor e não recebemos dados de uso. Quando o
usuário envia backups para um serviço de nuvem, o envio vai direto do
computador dele para a conta dele.

No Google Drive, o aplicativo pede apenas o escopo
`https://www.googleapis.com/auth/drive.file`, que dá acesso somente aos
arquivos criados por ele — nenhum outro arquivo do Drive fica visível.

## Contato

WALYTECH SOLUÇÕES TECNOLÓGICAS LTDA — CNPJ 50.449.577/0001-53
tgf231.dev@gmail.com

<!-- Gerado por publicar_docs.py; edite os originais em docs/, não aqui. -->
"""

#: Front matter do Jekyll. Precisa ser a primeira coisa do arquivo, antes de
#: qualquer comentário, senão o GitHub Pages o trata como texto comum.
CABECALHO = ("---\n"
             "title: {titulo}\n"
             "permalink: {url}\n"
             "---\n\n"
             "<!-- Gerado a partir de {origem} pelo publicar_docs.py.\n"
             "     Edite o original, nunca este arquivo. -->\n\n")

#: Configuração do site. O tema é um dos que o GitHub Pages já hospeda, então
#: não há dependência a instalar nem build a manter.
CONFIG = """title: Backup Maximus
description: >-
  Documentos oficiais do Backup Maximus —
  WALYTECH SOLUÇÕES TECNOLÓGICAS LTDA
theme: jekyll-theme-cayman
lang: pt-BR

# Nada neste repositório é escrito à mão: tudo vem de publicar_docs.py.
"""


def _reescrever_links(texto: str) -> str:
    """Ajusta os links que apontavam para dentro do repositório privado."""
    for alvo, novo in REESCRITAS.items():
        if novo:
            texto = texto.replace(f"]({alvo})", f"]({novo})")
        else:
            # Sem destino público: preserva o texto e descarta o link, em vez
            # de mandar o leitor para um 404.
            texto = re.sub(r"\[([^\]]+)\]\(" + re.escape(alvo) + r"\)",
                           r"\1", texto)
    return texto


def _links_quebrados(saidas: dict[str, str]) -> list[str]:
    """Links internos que não chegam a nenhuma página deste site.

    A verificação é por destino, não por formato: um link que sobreviva
    apontando para `../THIRD_PARTY_NOTICES.md` levaria o leitor a um 404 —
    e é justamente na política de privacidade que um 404 custa caro, porque
    o Google confere esse endereço para liberar o aplicativo.
    """
    validos = {"", "index"}
    for _, (_nome, _titulo, url) in ARQUIVOS.items():
        validos.add(url.strip("/"))

    quebrados = []
    for pagina, conteudo in saidas.items():
        if not pagina.endswith(".md"):
            continue
        for alvo in re.findall(r"\]\(([^)]+)\)", conteudo):
            if alvo.startswith(("http://", "https://", "mailto:", "#")):
                continue
            # O caminho é relativo à página; o que interessa é onde ele para.
            destino = alvo.split("#")[0].strip()
            destino = re.sub(r"^(\.\./|\./)+", "", destino).strip("/")
            if destino not in validos:
                quebrados.append(f"{pagina} -> {alvo}")
    return quebrados


def montar(destino: str, conferir: bool = False, dominio: str = "") -> int:
    if not conferir:
        os.makedirs(destino, exist_ok=True)

    mudancas = 0
    saidas = {"README.md": INDICE, "_config.yml": CONFIG}
    if dominio:
        # O CNAME é o que faz o GitHub Pages atender por um domínio próprio.
        # Sem ele, o site responde só em <usuário>.github.io.
        saidas["CNAME"] = dominio.strip() + "\n"

    for origem_rel, (nome, titulo, url) in ARQUIVOS.items():
        origem = os.path.join(RAIZ, origem_rel.replace("/", os.sep))
        if not os.path.isfile(origem):
            print(f"  [!] falta {origem_rel}")
            return 1
        with open(origem, encoding="utf-8") as fh:
            texto = fh.read()
        saidas[nome] = (CABECALHO.format(titulo=titulo, url=url,
                                         origem=origem_rel)
                        + _reescrever_links(texto))

    for nome, conteudo in saidas.items():
        alvo = os.path.join(destino, nome)
        atual = ""
        if os.path.isfile(alvo):
            with open(alvo, encoding="utf-8") as fh:
                atual = fh.read()
        if atual == conteudo:
            print(f"  = {nome}")
            continue
        mudancas += 1
        print(f"  {'~' if atual else '+'} {nome}")
        if not conferir:
            with open(alvo, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(conteudo)

    pendentes = _links_quebrados(saidas)
    if pendentes:
        print("\n  [!] links que não resolvem no site público:")
        for p in pendentes:
            print(f"      {p}")
        return 1

    print(f"\n  {mudancas} arquivo(s) a atualizar" if mudancas
          else "\n  nada a fazer: já está em dia")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--destino", default=DESTINO_PADRAO)
    ap.add_argument("--conferir", action="store_true",
                    help="apenas relata, sem escrever")
    ap.add_argument("--dominio", default="",
                    help="domínio próprio do site (grava o CNAME); "
                         "sem isso o site responde em <usuário>.github.io")
    args = ap.parse_args()

    print("=" * 66)
    print(" Backup Maximus — documentos públicos")
    print("=" * 66)
    print(f"Origem : {RAIZ}")
    print(f"Destino: {args.destino}\n")
    return montar(args.destino, args.conferir, args.dominio)


if __name__ == "__main__":
    sys.exit(main())
