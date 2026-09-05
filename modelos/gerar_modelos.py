r"""Gera os conjuntos modelo distribuídos com o programa.

Os modelos são perfis comuns — mesmos arquivos `.ini`, mesma leitura, mesma
importação. Gerá-los por código em vez de escrevê-los à mão garante que sempre
casem com o formato que o `Config.save` produz hoje: um modelo escrito à mão
envelhece calado quando um campo novo aparece.

    python modelos/gerar_modelos.py

Rode isto depois de mexer em `config.py` e confira o `git diff`.
"""

from __future__ import annotations

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from backup_maximus.config import (          # noqa: E402
    BackupItem, BackupSet, Config, ItemType, SetMode,
)

DESTINO = os.path.join(RAIZ, "modelos")


def _perfil(bset: BackupSet) -> Config:
    """Um modelo carrega conjuntos e nada mais.

    Empresa, e-mail e SMTP são da loja onde o programa está sendo instalado,
    não do modelo — trazê-los sobrescreveria o que o técnico acabou de digitar.
    """
    cfg = Config()
    cfg.sets = [bset]
    return cfg


def pdv_expresso() -> Config:
    return _perfil(BackupSet(
        name="PDV_EXPRESSO",
        destination=r"U:\ ".strip(),
        staging=r"C:\BACKUP",
        mode=SetMode.FULL,
        wait_for_path=r"U:\ ".strip(),
        wait_timeout_sec=600,
        keep_staging=True,
        keep_last=7,
        items=[
            BackupItem(
                name="Banco PDV Expresso", type=ItemType.FIREBIRD,
                source="PDVEXPRESSO", subfolder="PDVEXPRESSO",
                output_name="PDVEXPRESSO.FBK",
                host="LOCALHOST", port="3050", user="SYSDBA"),
            BackupItem(
                name="Configuracao NFC-e", type=ItemType.FILES,
                source=r"C:\Program Files (x86)\Eagle\PDVExpresso\nfceConfig.ini",
                subfolder="PDVEXPRESSO"),
            BackupItem(
                name="XMLs do destinatario", type=ItemType.FILES,
                source=r"C:\Program Files (x86)\Eagle\PDVExpresso\Arquivos\XmlDestinatario",
                subfolder=r"PDVEXPRESSO\Arquivos\XmlDestinatario", mirror=True),
            BackupItem(
                name="Logs de transmissao", type=ItemType.FILES,
                source=r"C:\Program Files (x86)\Eagle\PDVExpresso\Arquivos\Log",
                subfolder=r"PDVEXPRESSO\Arquivos\Log", mirror=True),
        ],
    ))


def servidor_firebird() -> Config:
    return _perfil(BackupSet(
        name="FIREBIRD",
        destination=r"D:\Backups",
        mode=SetMode.FULL,
        wait_timeout_sec=300,
        keep_staging=True,
        keep_last=14,
        items=[
            BackupItem(
                name="Banco principal", type=ItemType.FIREBIRD,
                source="MEUBANCO", subfolder="BANCO",
                output_name="MEUBANCO.FBK",
                host="LOCALHOST", port="3050", user="SYSDBA"),
            BackupItem(
                name="Configuracao do Firebird", type=ItemType.FILES,
                source=r"C:\Program Files\Firebird\Firebird_2_5\firebird.conf",
                subfolder="BANCO"),
        ],
    ))


def arquivos_e_pastas() -> Config:
    return _perfil(BackupSet(
        name="ARQUIVOS",
        destination=r"D:\Backups",
        mode=SetMode.INCREMENTAL,
        wait_timeout_sec=300,
        keep_staging=True,
        keep_last=30,
        items=[
            BackupItem(
                name="Documentos", type=ItemType.FILES,
                source=r"C:\Users\Publico\Documentos",
                subfolder="Documentos", mirror=True),
            BackupItem(
                name="Pasta na rede", type=ItemType.FILES,
                source=r"\\SERVIDOR\Compartilhada",
                subfolder="Rede", mirror=True),
        ],
    ))


MODELOS = {
    "pdv_expresso.ini": pdv_expresso,
    "servidor_firebird.ini": servidor_firebird,
    "arquivos_e_pastas.ini": arquivos_e_pastas,
}


def main() -> int:
    os.makedirs(DESTINO, exist_ok=True)
    print("=" * 60)
    print(" Backup Maximus — conjuntos modelo")
    print("=" * 60)
    for nome, construir in MODELOS.items():
        caminho = os.path.join(DESTINO, nome)
        cfg = construir()
        if not cfg.save(caminho):
            print(f"  [!] falhou: {nome}")
            return 1
        itens = sum(len(s.items) for s in cfg.sets)
        print(f"  + {nome:26} {len(cfg.sets)} conjunto, {itens} itens")
    print("\n  Confira o git diff antes de commitar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
