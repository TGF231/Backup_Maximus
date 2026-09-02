#include "logger.h"
#include <fstream>
#include <mutex>

namespace bm {

static std::mutex g_logMutex;
static std::wstring g_logDir;

void Logger::Init() {
    g_logDir = PathJoin(ExeDir(), L"logs");
    EnsureDir(g_logDir);
}

std::wstring Logger::CurrentLogPath() {
    time_t t = time(nullptr);
    tm local;
    localtime_s(&local, &t);
    wchar_t day[32];
    wcsftime(day, 32, L"%Y-%m-%d", &local);
    return PathJoin(g_logDir, std::wstring(L"backup_") + day + L".log");
}

void Logger::Log(LogLevel level, const std::wstring& msg) {
    if (g_logDir.empty()) Init();
    const wchar_t* tag = level == LogLevel::Info ? L"INFO " :
                         level == LogLevel::Warn ? L"WARN " : L"ERROR";
    std::wstring line = L"[" + NowIso() + L"] [" + tag + L"] " + msg + L"\r\n";
    std::string utf8 = WideToUtf8(line);

    std::lock_guard<std::mutex> lock(g_logMutex);
    std::ofstream f(CurrentLogPath().c_str(), std::ios::binary | std::ios::app);
    f.write(utf8.data(), utf8.size());
}

} // namespace bm
