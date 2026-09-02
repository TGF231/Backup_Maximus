@echo off
REM ============================================================
REM  Backup Maximus - build com MSVC (Visual Studio Build Tools)
REM  Execute a partir de um "x64 Native Tools Command Prompt",
REM  ou deixe o script localizar o vcvars64.bat automaticamente.
REM ============================================================
setlocal

where cl >nul 2>&1
if errorlevel 1 (
  set VSWHERE="%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
  if not exist %VSWHERE% (
    echo [ERRO] MSVC nao encontrado. Instale o "Visual Studio Build Tools"
    echo        com a carga de trabalho "Desenvolvimento para desktop com C++".
    exit /b 1
  )
  for /f "usebackq tokens=*" %%i in (`%VSWHERE% -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set VSPATH=%%i
  if not defined VSPATH (echo [ERRO] Toolset C++ nao instalado. & exit /b 1)
  call "%VSPATH%\VC\Auxiliary\Build\vcvars64.bat" >nul
)

set SRC=src
set OUT=build
if not exist "%OUT%" mkdir "%OUT%"

echo [1/2] Compilando recursos...
rc /nologo /fo "%OUT%\app.res" /i "%SRC%" "%SRC%\app.rc"
if errorlevel 1 (echo [ERRO] rc falhou & exit /b 1)

echo [2/2] Compilando e linkando...
cl /nologo /std:c++17 /EHsc /W4 /O2 /DUNICODE /D_UNICODE /MT ^
  /Fo"%OUT%\\" /Fe"%OUT%\BackupMaximus.exe" ^
  "%SRC%\main.cpp" "%SRC%\common.cpp" "%SRC%\logger.cpp" "%SRC%\config.cpp" ^
  "%SRC%\network.cpp" "%SRC%\sysinfo.cpp" "%SRC%\filecopy.cpp" "%SRC%\zip.cpp" ^
  "%SRC%\dbbackup.cpp" "%SRC%\email.cpp" "%SRC%\engine.cpp" ^
  "%SRC%\ui_progress.cpp" "%SRC%\ui_config.cpp" ^
  "%OUT%\app.res" ^
  /link /SUBSYSTEM:WINDOWS comctl32.lib shlwapi.lib crypt32.lib bcrypt.lib mpr.lib ^
  ole32.lib uuid.lib shell32.lib advapi32.lib user32.lib gdi32.lib
if errorlevel 1 (echo [ERRO] compilacao falhou & exit /b 1)

echo.
echo OK -^> %OUT%\BackupMaximus.exe
endlocal
