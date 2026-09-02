"""Lançador do Backup Maximus.

A extensão .pyw abre sem janela de console — é este arquivo que o atalho da
área de trabalho aponta quando a aplicação roda direto do código-fonte.

    BackupMaximus.pyw            configurações
    BackupMaximus.pyw /run       execução com janela de progresso
    BackupMaximus.pyw /silent    execução sem interface
    BackupMaximus.pyw /check     verificação de atraso
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backup_maximus.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
