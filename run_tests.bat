@echo off
REM ============================================================
REM  Backup Maximus - suite de testes do nucleo (sem interface)
REM ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python nao encontrado no PATH.
  echo        Instale o Python 3.11 ou superior e reabra o terminal.
  exit /b 1
)

python -m unittest discover -s tests -p "test_*.py" -v
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (echo TODOS OS TESTES PASSARAM) else (echo HOUVE FALHAS NOS TESTES)
exit /b %RC%
