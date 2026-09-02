@echo off
REM ============================================================
REM  Backup Maximus - gera BackupMaximus.exe com PyInstaller
REM
REM  O executavel resultante nao exige Python instalado na maquina
REM  do cliente. Copie o .exe para C:\BackupMaximus\ e pronto.
REM
REM  Antes de gerar, para embutir 7-Zip e rclone:
REM      python vendor\baixar_ferramentas.py
REM ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python nao encontrado no PATH.
  exit /b 1
)

python -c "import PySide6" >nul 2>&1
if errorlevel 1 (echo [ERRO] PySide6 nao instalado. Rode: pip install PySide6 & exit /b 1)

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
  echo Instalando PyInstaller...
  python -m pip install --quiet pyinstaller
  if errorlevel 1 (echo [ERRO] falha ao instalar o PyInstaller & exit /b 1)
)

echo [1/3] Compilando formularios do Qt Designer...
call "%~dp0build_ui.bat" >nul
if errorlevel 1 (echo [ERRO] falha ao compilar os .ui & exit /b 1)

echo [2/3] Verificando ferramentas de terceiros...
REM O conferir.py aceita qualquer arrumacao de pasta dentro de vendor/ e escolhe
REM o binario da arquitetura desta maquina. Embutimos so os arquivos
REM necessarios: o pacote do 7-Zip traz tres arquiteturas, e o rclone pesa 80 MB.
python vendor\conferir.py
set "VENDOR_ARGS="
for /f "usebackq delims=" %%A in (`python vendor\conferir.py --pyinstaller`) do (
  set "VENDOR_ARGS=%%A"
)

echo [3/3] Empacotando...
REM --noconsole: sem janela preta ao rodar pelo atalho.
REM --onefile:   um unico .exe para copiar na maquina do cliente.
REM Os modulos Qt nao usados sao excluidos para o .exe nao passar de ~45 MB.
python -m PyInstaller ^
  --noconfirm --clean --onefile --noconsole ^
  --name BackupMaximus ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.QtMultimedia ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.QtDataVisualization ^
  --exclude-module tkinter ^
  --exclude-module unittest ^
  %VENDOR_ARGS% ^
  BackupMaximus.pyw
if errorlevel 1 (echo [ERRO] compilacao falhou & exit /b 1)

echo.
echo OK -^> dist\BackupMaximus.exe
echo.
echo Proximos passos:
echo   1. Copie dist\BackupMaximus.exe para a pasta definitiva (ex.: C:\BackupMaximus\)
echo   2. Execute uma vez para definir a senha e configurar os conjuntos
echo   3. Na aba Configuracoes, clique em "Criar atalho na area de trabalho"
endlocal
