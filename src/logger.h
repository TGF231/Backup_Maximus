// Backup Maximus - logger.h
// Log em arquivo (logs\backup_YYYY-MM-DD.log) com niveis INFO/WARN/ERROR.
#pragma once
#include "common.h"

namespace bm {

enum class LogLevel { Info, Warn, Error };

class Logger {
public:
    // Inicializa apontando para <exeDir>\logs. Cria a pasta se preciso.
    static void Init();
    static void Log(LogLevel level, const std::wstring& msg);
    static void Info(const std::wstring& msg)  { Log(LogLevel::Info, msg); }
    static void Warn(const std::wstring& msg)  { Log(LogLevel::Warn, msg); }
    static void Error(const std::wstring& msg) { Log(LogLevel::Error, msg); }
    static std::wstring CurrentLogPath();
};

} // namespace bm
