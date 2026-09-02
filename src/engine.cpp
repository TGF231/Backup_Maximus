#include "engine.h"
#include "logger.h"
#include "network.h"
#include "dbbackup.h"
#include "filecopy.h"
#include "zip.h"
#include "sysinfo.h"
#include "email.h"
#include <fstream>
#include <sstream>

namespace bm {

static std::wstring Fmt1(double v) {
    wchar_t buf[32];
    swprintf(buf, 32, L"%.1f", v);
    std::wstring s = buf;
    size_t dot = s.find(L'.');
    if (dot != std::wstring::npos) s[dot] = L',';
    return s;
}

std::wstring StagingDirFor(const BackupSet& s) {
    if (!s.staging.empty()) return s.staging;
    return PathJoin(PathJoin(ExeDir(), L"staging"), s.name);
}

// ---------------- relatorio ----------------
static std::wstring BuildReport(const Config& cfg, const RunResult& run, const DeviceInfo& dev) {
    std::wostringstream o;
    o << L"==========================================\n";
    o << L"  RELATORIO DE BACKUP - Backup Maximus\n";
    o << L"==========================================\n";
    o << L"Empresa:      " << (cfg.companyName.empty() ? L"(nao configurada)" : cfg.companyName) << L"\n";
    o << L"Data/hora:    " << NowIso() << L"\n";
    o << L"Computador:   " << dev.computerName << L"\n";
    o << L"\n--- Dispositivo ---\n";
    o << L"CPU:           " << Fmt1(dev.cpuUsagePct) << L"% em uso\n";
    o << L"Memoria:       " << Fmt1(dev.memUsagePct) << L"% (" << dev.memUsedMB << L" MB de "
      << dev.memTotalMB << L" MB)\n";
    o << L"Armazenamento: " << Fmt1(dev.diskUsagePct) << L"% usado ("
      << dev.diskFreeGB << L" GB livres de " << dev.diskTotalGB << L" GB)\n";
    o << L"\n--- Resultado ---\n";
    o << L"Conjuntos: " << run.totalSets << L" | Sucesso: " << run.succeededSets
      << L" | Falhas: " << (run.totalSets - run.succeededSets) << L"\n";
    o << L"Tempo total: " << Fmt1(run.elapsedSec) << L" s\n";

    for (const auto& s : run.sets) {
        o << L"\n" << (s.ok ? L"[OK]    " : L"[FALHA] ") << L"Conjunto: " << s.setName
          << L"  (" << Fmt1(s.elapsedSec) << L" s)\n";
        if (!s.zipPath.empty())
            o << L"        Arquivo: " << s.zipPath << L"  (" << FormatBytes(s.zipBytes) << L")\n";
        if (!s.message.empty())
            o << L"        " << s.message << L"\n";
        for (const auto& it : s.items) {
            o << L"          " << (it.ok ? L"ok   " : L"FALHA") << L"  " << it.itemName;
            if (!it.detail.empty()) o << L"  -  " << it.detail;
            o << L"\n";
        }
    }
    o << L"\nLog completo: " << Logger::CurrentLogPath() << L"\n";
    return o.str();
}

static std::wstring WriteReportFile(const std::wstring& dir, const std::wstring& text) {
    EnsureDir(dir);
    std::wstring path = PathJoin(dir, L"relatorio_backup_" + NowTimestamp() + L".txt");
    std::string utf8 = "\xEF\xBB\xBF" + WideToUtf8(text);
    std::ofstream f(path.c_str(), std::ios::binary);
    if (!f) return L"";
    f.write(utf8.data(), utf8.size());
    return path;
}

// ---------------- um conjunto ----------------
static SetResult RunOneSet(BackupSet& set, const Config& cfg, Zipper& zipper,
                           int baseProgress, int progressSpan, const ProgressFn& progress) {
    SetResult res;
    res.setName = set.name;
    ULONGLONG t0 = GetTickCount64();

    // Reporta progresso dentro da faixa reservada para este conjunto.
    auto report = [&](int localPct, const std::wstring& msg, Phase ph = Phase::Working) -> bool {
        if (!progress) return true;
        return progress(ph, baseProgress + (localPct * progressSpan) / 100, msg);
    };

    std::wstring staging = StagingDirFor(set);
    Logger::Info(L"--- Conjunto '" + set.name + L"' (" + SetModeName(set.mode) +
                 L") | staging=" + staging + L" | destino=" + set.destination + L" ---");

    do {
        std::wstring err;

        // 1) aguarda a unidade removivel, se configurado
        if (!set.waitForPath.empty() && !DirExists(set.waitForPath)) {
            Logger::Info(L"Aguardando unidade " + set.waitForPath + L"...");
            bool cancelled = false;
            bool ready = WaitForPath(set.waitForPath, set.waitTimeoutSec,
                [&](int elapsed) -> bool {
                    std::wstring m = L"Aguardando unidade " + set.waitForPath +
                                     L" — insira o pen drive ou HD externo (" +
                                     std::to_wstring(elapsed) + L"s)";
                    if (!report(2, m, Phase::WaitingDrive)) { cancelled = true; return false; }
                    return true;
                });
            if (!ready) {
                res.message = cancelled
                    ? L"Espera pela unidade " + set.waitForPath + L" cancelada pelo usuario."
                    : L"Unidade " + set.waitForPath + L" nao ficou disponivel em " +
                      std::to_wstring(set.waitTimeoutSec) + L" s.";
                break;
            }
            Logger::Info(L"Unidade " + set.waitForPath + L" detectada.");
        }

        // 2) acesso de rede ao destino, se for UNC
        if (!EnsureNetworkAccess(set.destination, cfg.netCreds, err)) {
            res.message = err;
            break;
        }
        if (!EnsureDir(set.destination)) {
            res.message = L"Nao foi possivel criar/acessar o destino: " + set.destination;
            break;
        }

        // 3) monta a arvore
        if (!set.keepStaging) RemoveTree(staging);
        if (!EnsureDir(staging)) {
            res.message = L"Nao foi possivel criar a arvore de montagem: " + staging;
            break;
        }

        // 4) cada item na sua subpasta
        std::vector<const BackupItem*> active;
        for (const auto& it : set.items)
            if (it.enabled) active.push_back(&it);

        if (active.empty()) {
            res.message = L"Conjunto sem itens habilitados.";
            break;
        }

        int itemFailures = 0;
        for (size_t i = 0; i < active.size(); ++i) {
            const BackupItem& item = *active[i];
            ItemResult ir;
            ir.itemName = item.name;
            ULONGLONG it0 = GetTickCount64();

            // 10%..75% da faixa do conjunto e a fase de itens
            int pct = 10 + (int)((i * 65) / active.size());
            report(pct, L"[" + set.name + L"] " + item.name + L"...");

            std::wstring target = item.subfolder.empty() ? staging
                                                         : PathJoin(staging, item.subfolder);
            std::wstring ierr;

            if (item.type == ItemType::Firebird || item.type == ItemType::SqlServer ||
                item.type == ItemType::MySql) {
                std::wstring dumpFile;
                if (DumpDatabase(item, target, dumpFile, ierr)) {
                    ir.ok = true;
                    WIN32_FILE_ATTRIBUTE_DATA fa;
                    if (GetFileAttributesExW(dumpFile.c_str(), GetFileExInfoStandard, &fa)) {
                        uint64_t sz = ((uint64_t)fa.nFileSizeHigh << 32) | fa.nFileSizeLow;
                        ir.detail = L"dump " + FormatBytes(sz);
                    }
                } else {
                    ir.detail = ierr;
                }
            } else {
                // Dbf / Files: arquivo unico ou pasta inteira
                std::wstring srcErr;
                if (!EnsureNetworkAccess(item.source, cfg.netCreds, srcErr) && !srcErr.empty()) {
                    ir.detail = srcErr;
                } else if (FileExists(item.source)) {
                    CopyStats st;
                    ir.ok = CopyOneFile(item.source, target, st);
                    ir.detail = ir.ok ? (st.filesCopied ? L"copiado" : L"ja atualizado")
                                      : st.lastError;
                } else if (DirExists(item.source)) {
                    CopyStats st;
                    ir.ok = MirrorDirectory(item.source, target, item.mirror, st);
                    if (ir.ok) {
                        ir.detail = std::to_wstring(st.filesCopied) + L" copiados, " +
                                    std::to_wstring(st.filesSkipped) + L" iguais";
                        if (st.filesDeleted) ir.detail += L", " + std::to_wstring(st.filesDeleted) + L" removidos";
                        if (st.errors)       ir.detail += L", " + std::to_wstring(st.errors) + L" com erro";
                        if (st.bytesCopied)  ir.detail += L" (" + FormatBytes(st.bytesCopied) + L")";
                    } else {
                        ir.detail = st.lastError;
                    }
                } else {
                    ir.detail = L"Origem nao encontrada: " + item.source;
                }
            }

            ir.elapsedSec = (GetTickCount64() - it0) / 1000.0;
            if (ir.ok) {
                Logger::Info(L"  item '" + item.name + L"': " + ir.detail);
            } else {
                itemFailures++;
                Logger::Error(L"  item '" + item.name + L"' FALHOU: " + ir.detail);
            }
            res.items.push_back(ir);
        }

        // 5) compacta a arvore inteira em UM zip
        bool maxComp = (set.mode == SetMode::Full);
        if (set.mode == SetMode::Full) {
            res.zipPath = PathJoin(set.destination, set.name + NowStampBR() + L".zip");
        } else {
            res.zipPath = PathJoin(set.destination, set.name + L".zip");
        }

        uint64_t treeSize = DirectorySize(staging);
        uint64_t freeSpace = FreeSpaceBytes(set.destination);
        if (freeSpace > 0 && treeSize > 0 && freeSpace < treeSize / 3) {
            // O zip dificilmente passa de 1/3 do original; abaixo disso e risco real.
            Logger::Warn(L"Espaco livre em " + set.destination + L" (" + FormatBytes(freeSpace) +
                         L") pode ser insuficiente para " + FormatBytes(treeSize) + L" de dados.");
        }

        report(78, L"[" + set.name + L"] compactando " + FormatBytes(treeSize) +
                   (maxComp ? L" (maxima)..." : L" (rapida)..."));

        bool update = (set.mode == SetMode::Incremental);
        if (!zipper.ArchiveTree(staging, res.zipPath, maxComp, update, err)) {
            res.message = err;
            break;
        }

        WIN32_FILE_ATTRIBUTE_DATA fa;
        if (GetFileAttributesExW(res.zipPath.c_str(), GetFileExInfoStandard, &fa))
            res.zipBytes = ((uint64_t)fa.nFileSizeHigh << 32) | fa.nFileSizeLow;

        res.ok = (itemFailures == 0);
        if (itemFailures)
            res.message = std::to_wstring(itemFailures) + L" de " +
                          std::to_wstring(active.size()) + L" itens falharam (o zip foi gerado com o restante).";
    } while (false);

    res.elapsedSec = (GetTickCount64() - t0) / 1000.0;
    if (res.ok)
        Logger::Info(L"Conjunto '" + set.name + L"' OK em " + Fmt1(res.elapsedSec) +
                     L" s -> " + res.zipPath + L" (" + FormatBytes(res.zipBytes) + L")");
    else
        Logger::Error(L"Conjunto '" + set.name + L"' FALHOU: " + res.message);
    return res;
}

// ---------------- execucao geral ----------------
RunResult RunBackups(Config& cfg, const std::wstring& cfgPath, ProgressFn progress) {
    RunResult run;
    ULONGLONG t0 = GetTickCount64();
    auto report = [&](int pct, const std::wstring& msg) {
        if (progress) progress(Phase::Working, pct, msg);
    };

    Zipper zipper(cfg.sevenZipPath);
    Logger::Info(L"=== Iniciando execucao de backup (" + zipper.ToolDescription() + L") ===");

    std::vector<BackupSet*> active;
    for (auto& s : cfg.sets)
        if (s.enabled) active.push_back(&s);
    run.totalSets = (int)active.size();

    if (active.empty()) {
        run.summary = L"Nenhum conjunto de backup habilitado. Abra as configuracoes.";
        Logger::Warn(run.summary);
        report(100, run.summary);
        return run;
    }

    // Reserva 92% da barra para os conjuntos; o resto e relatorio/email.
    int span = 92 / run.totalSets;
    for (int i = 0; i < run.totalSets; ++i) {
        SetResult sr = RunOneSet(*active[i], cfg, zipper, i * span, span, progress);
        if (sr.ok) run.succeededSets++;
        run.sets.push_back(sr);
    }

    run.elapsedSec = (GetTickCount64() - t0) / 1000.0;
    run.allOk = (run.succeededSets == run.totalSets);

    // Relatorio (coleta apos o backup, para nao competir por CPU e disco).
    report(94, L"Gerando relatorio do dispositivo...");
    DeviceInfo dev = CollectDeviceInfo(400);
    std::wstring reportText = BuildReport(cfg, run, dev);
    run.reportPath = WriteReportFile(PathJoin(ExeDir(), L"reports"), reportText);
    if (run.reportPath.empty())
        Logger::Warn(L"Nao foi possivel gravar o arquivo de relatorio.");

    // Config + relatorio dentro de cada zip gerado (persistencia).
    cfg.lastRunUnix = NowUnix();
    cfg.lastRunStatus = run.allOk ? L"ok" : L"error";
    cfg.Save(cfgPath);

    report(96, L"Anexando configuracao e relatorio aos arquivos...");
    for (const auto& s : run.sets) {
        if (s.zipPath.empty() || !FileExists(s.zipPath)) continue;
        std::wstring err;
        if (FileExists(cfgPath) && !zipper.AddFile(s.zipPath, cfgPath, err))
            Logger::Warn(L"Nao foi possivel embutir a config em " + s.zipPath + L": " + err);
        if (!run.reportPath.empty())
            zipper.AddFile(s.zipPath, run.reportPath, err);
    }

    if (cfg.sendReportEmail && !cfg.notifyEmail.empty() && !cfg.smtp.host.empty()) {
        report(98, L"Enviando relatorio por email...");
        std::wstring subj = L"[Backup Maximus] " + cfg.companyName + L" - " +
                            (run.allOk ? L"Backup OK" : L"Backup com FALHAS") +
                            L" (" + std::to_wstring(run.succeededSets) + L"/" +
                            std::to_wstring(run.totalSets) + L")";
        std::wstring err;
        if (!SendEmail(cfg.smtp, cfg.notifyEmail, subj, reportText, run.reportPath, err))
            Logger::Warn(L"Envio de email falhou: " + err);
        else
            Logger::Info(L"Relatorio enviado para " + cfg.notifyEmail);
    }

    DisconnectNetworkShares();

    run.summary = (run.allOk ? L"Backup concluido com sucesso" : L"Backup concluido com falhas") +
                  std::wstring(L" (") + std::to_wstring(run.succeededSets) + L"/" +
                  std::to_wstring(run.totalSets) + L" conjuntos, " + Fmt1(run.elapsedSec) + L" s)";
    Logger::Info(L"=== " + run.summary + L" ===");
    report(100, run.summary);
    return run;
}

// ---------------- watchdog ----------------
bool CheckOverdueAndAlert(const Config& cfg, std::wstring& msgOut) {
    msgOut.clear();
    if (cfg.alertTimeoutHours <= 0) return false;
    int64_t age = NowUnix() - cfg.lastRunUnix;
    int64_t limit = (int64_t)cfg.alertTimeoutHours * 3600;
    bool overdue = (cfg.lastRunUnix == 0) || (age > limit) || (cfg.lastRunStatus == L"error");
    if (!overdue) {
        msgOut = L"Ultimo backup OK ha " + std::to_wstring(age / 3600) + L" h (limite " +
                 std::to_wstring(cfg.alertTimeoutHours) + L" h).";
        return false;
    }

    std::wstring reason;
    if (cfg.lastRunUnix == 0)
        reason = L"Nenhum backup foi executado ate agora.";
    else if (cfg.lastRunStatus == L"error")
        reason = L"A ultima execucao terminou com FALHAS.";
    else
        reason = L"Ultimo backup concluido ha " + std::to_wstring(age / 3600) +
                 L" horas — acima do limite de " + std::to_wstring(cfg.alertTimeoutHours) + L" horas.";

    msgOut = L"ALERTA: " + reason;
    Logger::Error(msgOut);

    if (!cfg.notifyEmail.empty() && !cfg.smtp.host.empty()) {
        std::wstring body = L"Empresa: " + cfg.companyName + L"\nComputador: " +
                            CollectDeviceInfo(100).computerName + L"\n\n" + reason +
                            L"\n\nVerifique a aplicacao Backup Maximus nesta maquina.";
        std::wstring err;
        if (SendEmail(cfg.smtp, cfg.notifyEmail,
                      L"[Backup Maximus] ALERTA - backup atrasado (" + cfg.companyName + L")",
                      body, L"", err))
            Logger::Info(L"Alerta enviado para " + cfg.notifyEmail);
        else
            Logger::Warn(L"Falha ao enviar alerta: " + err);
    }
    return true;
}

// ---------------- recuperacao de config ----------------
bool TryRecoverConfigFromZip(const std::wstring& searchDir, const std::wstring& cfgPath) {
    if (FileExists(cfgPath) || searchDir.empty() || !DirExists(searchDir)) return false;

    std::wstring newest;
    FILETIME newestTime{};
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(PathJoin(searchDir, L"*.zip").c_str(), &fd);
    if (h == INVALID_HANDLE_VALUE) return false;
    do {
        if (!(fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) &&
            CompareFileTime(&fd.ftLastWriteTime, &newestTime) > 0) {
            newestTime = fd.ftLastWriteTime;
            newest = PathJoin(searchDir, fd.cFileName);
        }
    } while (FindNextFileW(h, &fd));
    FindClose(h);
    if (newest.empty()) return false;

    Zipper zipper(L"");
    std::wstring err;
    std::wstring destDir = cfgPath.substr(0, cfgPath.find_last_of(L'\\'));
    if (!zipper.ExtractFile(newest, L"backup_maximus.ini", destDir, err)) {
        Logger::Warn(L"Recuperacao de config a partir de " + newest + L" falhou: " + err);
        return false;
    }
    Logger::Info(L"Configuracao recuperada de " + newest);
    return FileExists(cfgPath);
}

} // namespace bm
