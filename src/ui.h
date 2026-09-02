// Backup Maximus - ui.h
#pragma once
#include "common.h"
#include "config.h"

namespace bm {

// Janela de execucao rapida (/run): barra de progresso + status + tempo.
// Retorna 0 se todos os jobs OK, 1 caso contrario.
int ShowProgressRunner(HINSTANCE hInst, Config& cfg, const std::wstring& cfgPath);

// Tela de configuracao (com trava de senha). Retorna 0.
int ShowConfigWindow(HINSTANCE hInst, Config& cfg, const std::wstring& cfgPath);

// Prompt modal de senha. firstRun=true pede criacao (2 campos).
// Retorna true se autenticado/definido; senha definida ja e aplicada em cfg.
bool PasswordGate(HINSTANCE hInst, Config& cfg, bool firstRun);

} // namespace bm
