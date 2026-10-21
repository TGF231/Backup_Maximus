r"""Confere que o executável empacotado ABRE, e não só que foi gerado.

A auditoria de licenças (`auditar_pacote.py`) olha o conteúdo do pacote; esta
olha o comportamento. A distinção custou uma release: a 2.2.0 foi empacotada,
auditada, assinada e instalada, e não abria — os formulários da interface são
carregados por `importlib` a partir do nome do `.ui`, o PyInstaller não segue
import dinâmico, e o pacote `backup_maximus.ui.generated` ficou de fora. Nada
no build percebeu, porque nada tentou executar o programa.

    python vendor/testar_pacote.py

`/version` é o alvo certo para isso: não abre janela, não toca na configuração
do usuário, e para imprimir a versão o interpretador embutido já precisou
carregar o pacote inteiro. Em seguida a importação dos formulários é exercida
diretamente, que é onde a 2.2.0 quebrava.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(RAIZ, "dist")

#: Os dois formatos entregues. Ambos precisam abrir: o instalador leva a
#: pasta, e o arquivo unico e a versao portatil.
ALVOS = (
    ("executavel unico", os.path.join(DIST, "BackupMaximus.exe")),
    ("build em pasta", os.path.join(DIST, "BackupMaximus", "BackupMaximus.exe")),
)

TIMEOUT = 120.0


def _versao_esperada() -> str:
    sys.path.insert(0, RAIZ)
    import release_info
    return release_info.versao()


def _rodar(exe: str, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return 1, f"nao respondeu em {TIMEOUT:.0f}s"
    except OSError as exc:
        return 1, str(exc)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def testar(nome: str, exe: str, versao: str) -> list[str]:
    """Problemas encontrados neste executável. Vazio = passou."""
    if not os.path.isfile(exe):
        return [f"{nome}: nao existe ({exe})"]

    problemas = []

    # 1) O programa carrega e responde.
    codigo, saida = _rodar(exe, "/version")
    if codigo != 0:
        problemas.append(f"{nome}: /version saiu com {codigo} — {saida.strip()[:300]}")
    elif versao not in saida:
        problemas.append(
            f"{nome}: /version nao imprimiu {versao}; veio {saida.strip()[:200]!r}")

    # 2) Os formularios da interface importam. E o passo que a 2.2.0 pulava:
    #    o /version sozinho nao toca neles, e o erro so aparecia na primeira
    #    janela — ou seja, na maquina do cliente.
    codigo, saida = _rodar(exe, "/autoteste")
    if codigo != 0:
        problemas.append(
            f"{nome}: /autoteste falhou ({codigo}) — {saida.strip()[:400]}")
    elif "FORMULARIOS OK" not in saida:
        problemas.append(
            f"{nome}: /autoteste nao confirmou os formularios — "
            f"{saida.strip()[:200]!r}")

    return problemas


def main() -> int:
    versao = _versao_esperada()
    print("=" * 66)
    print(f" Backup Maximus — o pacote abre? (versao {versao})")
    print("=" * 66)

    todos = []
    for nome, exe in ALVOS:
        problemas = testar(nome, exe, versao)
        marca = "FALHOU" if problemas else "ok"
        tamanho = (f"{os.path.getsize(exe) / 1024 / 1024:,.1f} MB"
                   if os.path.isfile(exe) else "ausente")
        print(f"  {marca:7} {nome:20} {tamanho}")
        todos += problemas

    if todos:
        print("\nREPROVADO:")
        for p in todos:
            print(f"  - {p}")
        return 1

    print("\nAPROVADO — os dois formatos abrem e carregam a interface.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
