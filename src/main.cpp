// Backup Maximus - main.cpp
// Modos de execucao:
//   BackupMaximus.exe            -> abre configuracoes (pede senha)
//   BackupMaximus.exe /run       -> Quick Run: executa backup com barra de progresso
//   BackupMaximus.exe /silent    -> executa sem interface (para Agendador de Tarefas)
//   BackupMaximus.exe /check     -> verifica atraso e dispara alerta se preciso
//   BackupMaximus.exe /config    -> igual ao modo padrao
#include "common.h"
#include "config.h"
#include "logger.h"
#include "engine.h"
#include "ui.h"

using namespace bm;

static int RunSilent(Config& cfg, const std::wstring& cfgPath) {
    RunResult r = RunBackups(cfg, cfgPath, nullptr);
    return r.allOk ? 0 : 1;
}

int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE, LPWSTR lpCmdLine, int) {
    Logger::Init();

    std::wstring args = ToLower(Trim(lpCmdLine ? lpCmdLine : L""));
    std::wstring cfgPath = Config::DefaultPath();

    Config cfg;
    if (!cfg.Load(cfgPath)) {
        // Requisito de persistencia: se o INI sumiu, tenta recuperar de dentro
        // do zip de backup mais recente ao lado do executavel.
        if (TryRecoverConfigFromZip(ExeDir(), cfgPath))
            cfg.Load(cfgPath);
    }

    // ---- modo /check (watchdog) ----
    if (args.find(L"/check") != std::wstring::npos) {
        std::wstring msg;
        bool alerted = CheckOverdueAndAlert(cfg, msg);
        if (args.find(L"/quiet") == std::wstring::npos && alerted)
            MessageBoxW(nullptr, msg.c_str(), L"Backup Maximus", MB_ICONWARNING | MB_TOPMOST);
        return alerted ? 2 : 0;
    }

    // ---- modo silencioso (agendador) ----
    if (args.find(L"/silent") != std::wstring::npos) {
        if (cfg.sets.empty()) {
            Logger::Error(L"Execucao silenciosa abortada: nenhum conjunto configurado.");
            return 1;
        }
        return RunSilent(cfg, cfgPath);
    }

    // ---- Quick Run (atalho da area de trabalho) ----
    if (args.find(L"/run") != std::wstring::npos) {
        if (cfg.sets.empty()) {
            MessageBoxW(nullptr,
                L"Nenhum backup foi configurado ainda.\n\n"
                L"Abra o Backup Maximus (sem parametros) para configurar.",
                L"Backup Maximus", MB_ICONINFORMATION);
            return 1;
        }
        return ShowProgressRunner(hInst, cfg, cfgPath);
    }

    // ---- modo configuracao (padrao) ----
    bool firstRun = !cfg.HasPassword();
    if (!PasswordGate(hInst, cfg, firstRun)) {
        if (firstRun) Logger::Info(L"Definicao de senha cancelada na primeira execucao.");
        return 1;
    }
    if (firstRun) {
        cfg.Save(cfgPath);
        Logger::Info(L"Primeira execucao: senha de configuracao definida.");
    }
    return ShowConfigWindow(hInst, cfg, cfgPath);
}
