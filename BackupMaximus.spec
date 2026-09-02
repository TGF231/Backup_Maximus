# -*- mode: python ; coding: utf-8 -*-
"""Receita de empacotamento do Backup Maximus.

Fonte única do build: o `build_exe.bat` chama este arquivo em vez de repetir as
opções na linha de comando. Duas listas de exclusão divergindo é como a PyQt6
acabaria dentro de um produto fechado sem ninguém perceber.

Dois formatos, pelo mesmo spec:

    BM_ONEDIR ausente   dist/BackupMaximus.exe        um arquivo só
    BM_ONEDIR=1         dist/BackupMaximus/           pasta com as DLLs à vista

A build em pasta não é conveniência: a LGPLv3 da PySide6/Qt exige que o usuário
possa **substituir** a biblioteca Qt por outra versão. No executável único as
DLLs ficam fundidas e isso é impossível, então a build em pasta é o que cumpre
a licença. Distribua as duas e diga onde obter a segunda.
"""
import os
import re
import sys

from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct,
    VarFileInfo, VarStruct,
)

sys.path.insert(0, os.path.abspath("."))
from backup_maximus import paths          # noqa: E402  (só usa os e sys)

ONEDIR = bool(os.environ.get("BM_ONEDIR"))

# A versão é lida do código, não repetida aqui: duas cópias divergem na
# primeira pressa. Lida por regex para não importar o pacote (e com ele o
# PySide6) durante o build.
_fonte = open("backup_maximus/__init__.py", encoding="utf-8").read()
VERSAO = re.search(r'__version__ = "([^"]+)"', _fonte).group(1)
_n = tuple(int(x) for x in VERSAO.split(".")) + (0,)

# Sem isto o Windows mostra o .exe sem versão nas Propriedades, e o suporte
# fica sem saber o que está instalado na máquina do cliente.
VERSION_INFO = VSVersionInfo(
    ffi=FixedFileInfo(filevers=_n[:4], prodvers=_n[:4]),
    kids=[
        StringFileInfo([StringTable("040904B0", [
            StringStruct("CompanyName", "WalyTech Soluções Tecnológicas"),
            StringStruct("FileDescription", "Backup Maximus — agente de backup"),
            StringStruct("FileVersion", VERSAO),
            StringStruct("InternalName", "BackupMaximus"),
            StringStruct("LegalCopyright", "© WalyTech Soluções Tecnológicas"),
            StringStruct("OriginalFilename", "BackupMaximus.exe"),
            StringStruct("ProductName", "Backup Maximus"),
            StringStruct("ProductVersion", VERSAO),
        ])]),
        VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
    ],
)

# Ferramentas de terceiros (só o binário da arquitetura certa) e as licenças
# que precisam acompanhar a distribuição.
DATAS = list(paths.bundle_files())
DATAS += [(os.path.join("licenses", nome), "licenses")
          for nome in sorted(os.listdir("licenses"))
          if nome.lower().endswith(".txt")]

a = Analysis(
    ['BackupMaximus.pyw'],
    pathex=[],
    binaries=[],
    datas=DATAS,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # A PyQt6 é GPLv3 e costuma estar instalada na mesma máquina que a
        # PySide6. Se o PyInstaller a arrastasse para o pacote, o executável
        # distribuído herdaria a GPL — e um produto fechado não pode conter
        # GPL. Excluir é barato; descobrir numa auditoria, não.
        'PyQt5', 'PyQt6', 'PyQt6.sip', 'sip',
        # Módulos Qt que não usamos, para o executável não passar de ~45 MB.
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
        'PySide6.Qt3DCore', 'PySide6.QtMultimedia', 'PySide6.QtQuick',
        'PySide6.QtQml', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
        'tkinter', 'unittest',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

_comuns = dict(
    name='BackupMaximus',
    version=VERSION_INFO,
    icon='Logo_backup_maximus.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,          # sem janela preta ao rodar pelo atalho
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if ONEDIR:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, **_comuns)
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True,
                   upx_exclude=[], name='BackupMaximus')
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
              runtime_tmpdir=None, **_comuns)
