@echo off
REM ============================================================
REM  Abre o Qt Designer nos layouts do Backup Maximus.
REM
REM  Uso:  abrir_designer.bat                 (abre todas as telas)
REM        abrir_designer.bat tab_backups     (abre so uma)
REM
REM  Depois de salvar no Designer, basta rodar a aplicacao: ela
REM  recompila sozinha o .ui que mudou.
REM
REM  Telas disponiveis:
REM    main_window          janela principal (abas e rodape)
REM    tab_backups          aba Backups (conjuntos e itens)
REM    tab_settings         aba Configuracoes
REM    tab_network          aba Rede
REM    dialog_password      trava de senha
REM    dialog_preview_tree  previa da arvore
REM    dialog_destination   espaco e limpeza
REM    window_progress      janela do Quick Run
REM ============================================================
setlocal
cd /d "%~dp0"

where pyside6-designer >nul 2>&1
if errorlevel 1 (
  echo [ERRO] pyside6-designer nao encontrado.
  echo        Rode: pip install PySide6
  exit /b 1
)

if "%~1"=="" (
  echo Abrindo todas as telas no Qt Designer...
  start "" pyside6-designer designer\main_window.ui designer\tab_backups.ui ^
    designer\tab_settings.ui designer\tab_network.ui designer\dialog_password.ui ^
    designer\dialog_preview_tree.ui designer\dialog_destination.ui ^
    designer\window_progress.ui
) else (
  if not exist "designer\%~1.ui" (
    echo [ERRO] designer\%~1.ui nao existe.
    echo        Veja a lista de telas no topo deste arquivo.
    exit /b 1
  )
  echo Abrindo designer\%~1.ui...
  start "" pyside6-designer "designer\%~1.ui"
)
endlocal
