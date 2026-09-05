@echo off
REM ============================================================
REM  Backup Maximus - gera os dois formatos de distribuicao
REM
REM    dist\BackupMaximus.exe        arquivo unico, para copiar
REM    dist\BackupMaximus\           pasta com as DLLs do Qt a vista
REM
REM  A pasta nao e opcional: a LGPLv3 da PySide6/Qt exige que o
REM  usuario possa substituir a biblioteca Qt, o que o executavel
REM  unico impede. Publique as duas nas releases.
REM
REM  Toda a configuracao esta em BackupMaximus.spec - este arquivo
REM  so o invoca. Nao acrescente flags aqui: duas listas de opcao
REM  divergindo foi como a PyQt6 quase entrou no pacote.
REM
REM  Antes de gerar, para embutir 7-Zip e rclone:
REM      python vendor\baixar_ferramentas.py
REM ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (echo [ERRO] Python nao encontrado no PATH. & exit /b 1)

python -c "import PySide6" >nul 2>&1
if errorlevel 1 (echo [ERRO] PySide6 nao instalado. Rode: pip install PySide6 & exit /b 1)

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
  echo Instalando PyInstaller...
  python -m pip install --quiet pyinstaller
  if errorlevel 1 (echo [ERRO] falha ao instalar o PyInstaller & exit /b 1)
)

echo [1/6] Compilando formularios do Qt Designer...
call "%~dp0build_ui.bat" >nul
if errorlevel 1 (echo [ERRO] falha ao compilar os .ui & exit /b 1)

echo [2/6] Verificando ferramentas de terceiros...
python vendor\conferir.py
if errorlevel 1 (echo [ERRO] falha ao conferir vendor & exit /b 1)

echo [3/6] Empacotando arquivo unico...
set "BM_ONEDIR="
python -m PyInstaller --noconfirm --clean BackupMaximus.spec
if errorlevel 1 (echo [ERRO] compilacao falhou & exit /b 1)

echo [4/6] Empacotando pasta (exigencia da LGPL do Qt)...
set "BM_ONEDIR=1"
python -m PyInstaller --noconfirm --distpath dist BackupMaximus.spec
if errorlevel 1 (echo [ERRO] compilacao em pasta falhou & exit /b 1)
set "BM_ONEDIR="

echo [5/6] Auditando o pacote...
python vendor\auditar_pacote.py
if errorlevel 1 (echo [ERRO] auditoria reprovou o pacote & exit /b 1)

echo [6/6] Gerando o instalador...
REM Nao e fatal aqui: a maquina de desenvolvimento pode nao ter o Inno Setup.
REM No GitHub Actions o passo e obrigatorio e a release falha sem ele.
python installer\gerar_instalador.py
if errorlevel 1 (
  echo   [aviso] instalador nao gerado; veja a mensagem acima.
)

echo.
echo OK
echo   dist\BackupMaximus.exe    para instalar na maquina do cliente
echo   dist\BackupMaximus\       publique junto, para cumprir a LGPL
echo.
echo Proximos passos:
echo   1. Copie dist\BackupMaximus.exe para a pasta definitiva (ex.: C:\BackupMaximus\)
echo   2. Execute uma vez para definir a senha e configurar os conjuntos
echo   3. Na aba Configuracoes, clique em "Criar atalho na area de trabalho"
endlocal
