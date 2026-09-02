@echo off
REM ============================================================
REM  Backup Maximus - build com MinGW-w64 (g++)
REM  Uso: build.bat  [ou "build.bat debug" para simbolos]
REM ============================================================
setlocal

set SRC=src
set OUT=build
set EXE=%OUT%\BackupMaximus.exe

set SOURCES=^
 "%SRC%\main.cpp" "%SRC%\common.cpp" "%SRC%\logger.cpp" "%SRC%\config.cpp" ^
 "%SRC%\network.cpp" "%SRC%\sysinfo.cpp" "%SRC%\filecopy.cpp" "%SRC%\zip.cpp" ^
 "%SRC%\dbbackup.cpp" "%SRC%\email.cpp" "%SRC%\engine.cpp" ^
 "%SRC%\ui_progress.cpp" "%SRC%\ui_config.cpp"

set LIBS=-lcomctl32 -lshlwapi -lcrypt32 -lbcrypt -lmpr -lole32 -luuid -lshell32 -ladvapi32 -luser32 -lgdi32

if not exist "%OUT%" mkdir "%OUT%"

where g++ >nul 2>&1
if errorlevel 1 (
  echo [ERRO] g++ nao encontrado no PATH.
  echo        Instale o MinGW-w64: winget install BrechtSanders.WinLibs.POSIX.UCRT
  echo        e reabra o terminal.
  exit /b 1
)

set CXXFLAGS=-std=c++17 -municode -mwindows -Wall -Wextra -Wno-unused-parameter -Wno-unknown-pragmas -Wno-missing-field-initializers -static
if /i "%~1"=="debug" (set CXXFLAGS=%CXXFLAGS% -g -O0) else (set CXXFLAGS=%CXXFLAGS% -O2 -s)

REM O mingw-w64 injeta um default-manifest.o proprio, que conflita com o nosso
REM manifesto (visual styles, DPI, UTF-8). Fornecemos um objeto vazio com esse
REM nome num diretorio -B: o GCC acha o nosso primeiro e o conflito desaparece.
if not exist "%OUT%\nomanifest" mkdir "%OUT%\nomanifest"
if not exist "%OUT%\nomanifest\default-manifest.o" (
  echo. > "%OUT%\empty.c"
  gcc -c "%OUT%\empty.c" -o "%OUT%\nomanifest\default-manifest.o"
  del "%OUT%\empty.c"
)

echo [1/2] Compilando recursos...
windres "%SRC%\app.rc" -O coff -o "%OUT%\app.res" --include-dir "%SRC%"
if errorlevel 1 (echo [ERRO] windres falhou & exit /b 1)

echo [2/2] Compilando e linkando...
g++ %CXXFLAGS% -B "%OUT%\nomanifest" %SOURCES% "%OUT%\app.res" -o "%EXE%" %LIBS%
if errorlevel 1 (echo [ERRO] compilacao falhou & exit /b 1)

echo.
echo OK -^> %EXE%
endlocal
