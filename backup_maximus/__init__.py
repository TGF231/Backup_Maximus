"""Backup Maximus — agente de backup para Windows.

Modelo Conjunto -> Itens: um conjunto produz exatamente um .zip; cada item
coloca seu conteúdo numa subpasta da árvore de montagem, e a árvore inteira
vira esse zip.
"""

#: Versão do aplicativo. Fonte única: o .spec, o relatório, o log e a janela
#: leem daqui. Semântico — MAIOR.MENOR.CORREÇÃO:
#:   MAIOR    muda o formato do .ini de um jeito que a versão anterior não lê
#:   MENOR    recurso novo, configuração antiga continua válida
#:   CORREÇÃO só conserto, sem recurso novo
#: O procedimento de lançamento está no CHANGELOG.md.
__version__ = "2.2.1"
