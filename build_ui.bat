@echo off
REM ============================================================
REM  Backup Maximus - compila designer\*.ui -> backup_maximus\ui\generated
REM
REM  Normalmente voce NAO precisa rodar isto: a aplicacao recompila
REM  sozinha o que estiver desatualizado ao iniciar. Use quando quiser
REM  forcar a regeracao, ou antes de empacotar o .exe.
REM ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python nao encontrado no PATH.
  exit /b 1
)

python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
  echo [ERRO] PySide6 nao instalado.  Rode: pip install PySide6
  exit /b 1
)

echo Compilando formularios...
python -c "import sys; sys.path.insert(0,'.'); from backup_maximus import logger; logger.init('.'); from backup_maximus.ui import forms; nomes = forms.compile_all(force=True); print('\n'.join('  ok  ' + n + '.ui' for n in nomes)); print(len(nomes), 'formulario(s) compilado(s)')"
if errorlevel 1 (echo [ERRO] falha na compilacao & exit /b 1)

echo.
echo OK -^> backup_maximus\ui\generated\
endlocal
