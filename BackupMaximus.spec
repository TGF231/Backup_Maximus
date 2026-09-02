# -*- mode: python ; coding: utf-8 -*-
import re
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct,
    VarFileInfo, VarStruct,
)

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
            StringStruct("CompanyName", "«EMPRESA»"),
            StringStruct("FileDescription", "Backup Maximus — agente de backup"),
            StringStruct("FileVersion", VERSAO),
            StringStruct("InternalName", "BackupMaximus"),
            StringStruct("LegalCopyright", "© «EMPRESA»"),
            StringStruct("OriginalFilename", "BackupMaximus.exe"),
            StringStruct("ProductName", "Backup Maximus"),
            StringStruct("ProductVersion", VERSAO),
        ])]),
        VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
    ],
)


a = Analysis(
    ['BackupMaximus.pyw'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.Qt3DCore', 'PySide6.QtMultimedia', 'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'tkinter', 'unittest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BackupMaximus',
    version=VERSION_INFO,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
