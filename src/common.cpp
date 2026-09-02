#include "common.h"
#include <shlwapi.h>
#include <ctime>
#include <algorithm>

#pragma comment(lib, "shlwapi.lib")

namespace bm {

std::wstring Utf8ToWide(const std::string& s) {
    if (s.empty()) return L"";
    int n = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), (int)s.size(), nullptr, 0);
    std::wstring w(n, 0);
    MultiByteToWideChar(CP_UTF8, 0, s.c_str(), (int)s.size(), &w[0], n);
    return w;
}

std::string WideToUtf8(const std::wstring& w) {
    if (w.empty()) return "";
    int n = WideCharToMultiByte(CP_UTF8, 0, w.c_str(), (int)w.size(), nullptr, 0, nullptr, nullptr);
    std::string s(n, 0);
    WideCharToMultiByte(CP_UTF8, 0, w.c_str(), (int)w.size(), &s[0], n, nullptr, nullptr);
    return s;
}

std::wstring Trim(const std::wstring& s) {
    size_t a = s.find_first_not_of(L" \t\r\n");
    if (a == std::wstring::npos) return L"";
    size_t b = s.find_last_not_of(L" \t\r\n");
    return s.substr(a, b - a + 1);
}

std::wstring ToLower(std::wstring s) {
    std::transform(s.begin(), s.end(), s.begin(), ::towlower);
    return s;
}

bool StartsWith(const std::wstring& s, const std::wstring& prefix) {
    return s.size() >= prefix.size() && s.compare(0, prefix.size(), prefix) == 0;
}

std::vector<std::wstring> Split(const std::wstring& s, wchar_t sep) {
    std::vector<std::wstring> out;
    size_t start = 0;
    for (size_t i = 0; i <= s.size(); ++i) {
        if (i == s.size() || s[i] == sep) {
            out.push_back(s.substr(start, i - start));
            start = i + 1;
        }
    }
    return out;
}

std::wstring Join(const std::vector<std::wstring>& parts, const std::wstring& sep) {
    std::wstring out;
    for (size_t i = 0; i < parts.size(); ++i) {
        if (i) out += sep;
        out += parts[i];
    }
    return out;
}

std::wstring ReplaceAll(std::wstring s, const std::wstring& from, const std::wstring& to) {
    if (from.empty()) return s;
    size_t pos = 0;
    while ((pos = s.find(from, pos)) != std::wstring::npos) {
        s.replace(pos, from.size(), to);
        pos += to.size();
    }
    return s;
}

std::wstring ExeDir() {
    wchar_t buf[MAX_PATH];
    GetModuleFileNameW(nullptr, buf, MAX_PATH);
    PathRemoveFileSpecW(buf);
    return buf;
}

std::wstring PathJoin(const std::wstring& a, const std::wstring& b) {
    if (a.empty()) return b;
    if (b.empty()) return a;
    std::wstring out = a;
    if (out.back() != L'\\' && out.back() != L'/') out += L'\\';
    return out + b;
}

bool FileExists(const std::wstring& path) {
    DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY);
}

bool DirExists(const std::wstring& path) {
    DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY);
}

bool EnsureDir(const std::wstring& path) {
    if (DirExists(path)) return true;
    // Cria recursivamente componente a componente (suporta UNC).
    std::wstring accum;
    size_t i = 0;
    if (StartsWith(path, L"\\\\")) {
        // pular \\servidor\share
        size_t p = path.find(L'\\', 2);
        if (p == std::wstring::npos) return false;
        p = path.find(L'\\', p + 1);
        if (p == std::wstring::npos) return DirExists(path);
        accum = path.substr(0, p);
        i = p + 1;
    }
    for (; i <= path.size(); ++i) {
        if (i == path.size() || path[i] == L'\\' || path[i] == L'/') {
            if (!accum.empty() && accum.back() != L':') {
                CreateDirectoryW(accum.c_str(), nullptr);
            }
            if (i < path.size()) accum += L'\\';
        } else {
            accum += path[i];
        }
    }
    return DirExists(path);
}

std::wstring TempFilePath(const std::wstring& prefix, const std::wstring& ext) {
    wchar_t tmp[MAX_PATH];
    GetTempPathW(MAX_PATH, tmp);
    return std::wstring(tmp) + prefix + L"_" + NowTimestamp() + L"_" +
           std::to_wstring(GetCurrentProcessId()) + ext;
}

static std::wstring FormatNow(const wchar_t* fmt) {
    time_t t = time(nullptr);
    tm local;
    localtime_s(&local, &t);
    wchar_t buf[64];
    wcsftime(buf, 64, fmt, &local);
    return buf;
}

std::wstring NowTimestamp() { return FormatNow(L"%Y-%m-%d_%H%M%S"); }
std::wstring NowStampBR()   { return FormatNow(L"%d%m%Y%H%M%S"); }
std::wstring NowIso()       { return FormatNow(L"%Y-%m-%d %H:%M:%S"); }
int64_t NowUnix()           { return (int64_t)time(nullptr); }

bool WaitForPath(const std::wstring& path, int timeoutSec,
                 const std::function<bool(int)>& onWait) {
    if (path.empty()) return true;
    ULONGLONG start = GetTickCount64();
    for (int elapsed = 0; ; ) {
        if (DirExists(path) || FileExists(path)) return true;
        if (timeoutSec > 0 && elapsed >= timeoutSec) return false;
        if (onWait && !onWait(elapsed)) return false;   // cancelado pela UI
        Sleep(1000);
        elapsed = (int)((GetTickCount64() - start) / 1000);
    }
}

uint64_t FreeSpaceBytes(const std::wstring& path) {
    ULARGE_INTEGER freeBytes{};
    // GetDiskFreeSpaceEx aceita tanto raiz de unidade quanto pasta.
    if (!GetDiskFreeSpaceExW(path.c_str(), &freeBytes, nullptr, nullptr))
        return 0;
    return freeBytes.QuadPart;
}

std::wstring FormatBytes(uint64_t bytes) {
    const wchar_t* units[] = { L"B", L"KB", L"MB", L"GB", L"TB" };
    double v = (double)bytes;
    int u = 0;
    while (v >= 1024.0 && u < 4) { v /= 1024.0; ++u; }
    // %ls (nao %s): no MinGW, %s em printf wide significa string estreita.
    wchar_t buf[48];
    swprintf(buf, 48, u == 0 ? L"%.0f %ls" : L"%.1f %ls", v, units[u]);
    // Padrao brasileiro: virgula decimal.
    std::wstring s = buf;
    size_t dot = s.find(L'.');
    if (dot != std::wstring::npos) s[dot] = L',';
    return s;
}

std::wstring QuoteArg(const std::wstring& arg) {
    if (arg.find_first_of(L" \t\"") == std::wstring::npos) return arg;
    std::wstring out = L"\"";
    for (wchar_t c : arg) {
        if (c == L'"') out += L"\\\"";
        else out += c;
    }
    out += L"\"";
    return out;
}

int RunProcessCapture(const std::wstring& cmdLine, std::wstring& output,
                      DWORD timeoutMs, const std::wstring& workDir) {
    output.clear();

    SECURITY_ATTRIBUTES sa{ sizeof(sa), nullptr, TRUE };
    HANDLE readPipe = nullptr, writePipe = nullptr;
    if (!CreatePipe(&readPipe, &writePipe, &sa, 0)) return -1;
    SetHandleInformation(readPipe, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOW si{};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    si.hStdOutput = writePipe;
    si.hStdError = writePipe;
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);

    PROCESS_INFORMATION pi{};
    std::wstring mutableCmd = cmdLine; // CreateProcessW pode modificar o buffer
    BOOL ok = CreateProcessW(nullptr, &mutableCmd[0], nullptr, nullptr, TRUE,
                             CREATE_NO_WINDOW, nullptr,
                             workDir.empty() ? nullptr : workDir.c_str(), &si, &pi);
    CloseHandle(writePipe);
    if (!ok) {
        CloseHandle(readPipe);
        return -1;
    }

    // Le a saida enquanto o processo roda (evita deadlock de pipe cheio).
    std::string raw;
    char buf[4096];
    DWORD n;
    while (ReadFile(readPipe, buf, sizeof(buf), &n, nullptr) && n > 0) {
        raw.append(buf, n);
    }
    CloseHandle(readPipe);

    DWORD wait = WaitForSingleObject(pi.hProcess, timeoutMs ? timeoutMs : INFINITE);
    DWORD exitCode = (DWORD)-1;
    if (wait == WAIT_TIMEOUT) {
        TerminateProcess(pi.hProcess, 1);
        exitCode = (DWORD)-2;
    } else {
        GetExitCodeProcess(pi.hProcess, &exitCode);
    }
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    // Ferramentas de console geralmente emitem na codepage OEM; tenta UTF-8 primeiro.
    int wn = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, raw.c_str(), (int)raw.size(), nullptr, 0);
    UINT cp = (wn > 0) ? CP_UTF8 : CP_OEMCP;
    wn = MultiByteToWideChar(cp, 0, raw.c_str(), (int)raw.size(), nullptr, 0);
    output.resize(wn);
    if (wn) MultiByteToWideChar(cp, 0, raw.c_str(), (int)raw.size(), &output[0], wn);

    return (int)exitCode;
}

} // namespace bm
