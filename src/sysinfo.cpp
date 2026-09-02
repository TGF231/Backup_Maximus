#include "sysinfo.h"

namespace bm {

static uint64_t FtToU64(const FILETIME& ft) {
    return ((uint64_t)ft.dwHighDateTime << 32) | ft.dwLowDateTime;
}

DeviceInfo CollectDeviceInfo(DWORD sampleMs) {
    DeviceInfo d;

    wchar_t name[MAX_COMPUTERNAME_LENGTH + 1];
    DWORD len = MAX_COMPUTERNAME_LENGTH + 1;
    if (GetComputerNameW(name, &len)) d.computerName = name;

    // CPU: duas amostras de GetSystemTimes.
    FILETIME idle1, kern1, user1, idle2, kern2, user2;
    if (GetSystemTimes(&idle1, &kern1, &user1)) {
        Sleep(sampleMs);
        if (GetSystemTimes(&idle2, &kern2, &user2)) {
            uint64_t idle = FtToU64(idle2) - FtToU64(idle1);
            uint64_t kern = FtToU64(kern2) - FtToU64(kern1);
            uint64_t user = FtToU64(user2) - FtToU64(user1);
            uint64_t total = kern + user; // kernel inclui idle
            if (total > 0)
                d.cpuUsagePct = 100.0 * (double)(total - idle) / (double)total;
        }
    }

    MEMORYSTATUSEX ms{ sizeof(ms) };
    if (GlobalMemoryStatusEx(&ms)) {
        d.memUsagePct = (double)ms.dwMemoryLoad;
        d.memTotalMB = ms.ullTotalPhys / (1024 * 1024);
        d.memUsedMB = (ms.ullTotalPhys - ms.ullAvailPhys) / (1024 * 1024);
    }

    wchar_t sysDrive[8] = L"C:\\";
    wchar_t winDir[MAX_PATH];
    if (GetWindowsDirectoryW(winDir, MAX_PATH) && winDir[1] == L':') {
        sysDrive[0] = winDir[0];
    }
    ULARGE_INTEGER freeBytes, totalBytes;
    if (GetDiskFreeSpaceExW(sysDrive, &freeBytes, &totalBytes, nullptr)) {
        d.diskTotalGB = totalBytes.QuadPart / (1024ull * 1024 * 1024);
        d.diskFreeGB = freeBytes.QuadPart / (1024ull * 1024 * 1024);
        if (totalBytes.QuadPart > 0)
            d.diskUsagePct = 100.0 * (double)(totalBytes.QuadPart - freeBytes.QuadPart)
                                   / (double)totalBytes.QuadPart;
    }
    return d;
}

} // namespace bm
