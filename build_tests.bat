@echo off
REM ============================================================
REM  Backup Maximus - compila e executa os testes do nucleo
REM ============================================================
setlocal

set SRC=src
set OUT=build
set EXE=%OUT%\bm_tests.exe

if not exist "%OUT%" mkdir "%OUT%"

where g++ >nul 2>&1
if errorlevel 1 (
  echo [ERRO] g++ nao encontrado no PATH.
  exit /b 1
)

echo Compilando testes...
g++ -std=c++17 -municode -O2 -Wall -Wextra -Wno-unused-parameter -Wno-unknown-pragmas ^
    -Wno-missing-field-initializers -static -I"%SRC%" ^
  tests\test_core.cpp ^
  "%SRC%\common.cpp" "%SRC%\logger.cpp" "%SRC%\config.cpp" "%SRC%\sysinfo.cpp" ^
  "%SRC%\filecopy.cpp" "%SRC%\dbbackup.cpp" "%SRC%\zip.cpp" ^
  -o "%EXE%" -lshlwapi -lcrypt32 -lbcrypt -lole32 -lshell32 -ladvapi32
if errorlevel 1 (echo [ERRO] compilacao dos testes falhou & exit /b 1)

echo.
"%EXE%"
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (echo TODOS OS TESTES PASSARAM) else (echo HOUVE FALHAS NOS TESTES)
exit /b %RC%
