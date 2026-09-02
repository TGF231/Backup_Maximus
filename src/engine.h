// Backup Maximus - engine.h
// Orquestracao por CONJUNTO:
//   aguarda unidade -> monta a arvore de staging -> cada item na sua subpasta
//   -> compacta a arvore inteira em UM zip -> relatorio -> email.
#pragma once
#include "common.h"
#include "config.h"
#include <functional>

namespace bm {

struct ItemResult {
    std::wstring itemName;
    std::wstring detail;        // "12 copiados, 340 iguais" ou o erro
    bool ok = false;
    double elapsedSec = 0;
};

struct SetResult {
    std::wstring setName;
    bool ok = false;
    std::wstring zipPath;
    uint64_t zipBytes = 0;
    std::wstring message;       // erro do conjunto (falha de unidade, de zip, etc.)
    double elapsedSec = 0;
    std::vector<ItemResult> items;
};

struct RunResult {
    bool allOk = false;
    int totalSets = 0;
    int succeededSets = 0;
    double elapsedSec = 0;
    std::vector<SetResult> sets;
    std::wstring reportPath;
    std::wstring summary;
};

// Fase atual, para a UI reagir sem precisar interpretar o texto da mensagem.
enum class Phase {
    Working,        // executando: barra determinada, sem cancelar
    WaitingDrive,   // aguardando unidade removivel: barra indeterminada, cancelar disponivel
};

// callback(fase, percentual 0-100, mensagem).
// Devolver false cancela — hoje so tem efeito durante WaitingDrive.
using ProgressFn = std::function<bool(Phase, int, const std::wstring&)>;

RunResult RunBackups(Config& cfg, const std::wstring& cfgPath, ProgressFn progress);

// Watchdog: alerta se o backup nao rodou dentro do prazo configurado.
bool CheckOverdueAndAlert(const Config& cfg, std::wstring& msgOut);

// Recupera backup_maximus.ini de dentro do .zip mais recente em searchDir.
bool TryRecoverConfigFromZip(const std::wstring& searchDir, const std::wstring& cfgPath);

// Caminho efetivo da arvore de montagem de um conjunto.
std::wstring StagingDirFor(const BackupSet& s);

} // namespace bm
