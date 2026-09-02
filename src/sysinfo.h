// Backup Maximus - sysinfo.h
// Coleta leve de metricas do dispositivo para o relatorio de backup.
#pragma once
#include "common.h"

namespace bm {

struct DeviceInfo {
    std::wstring computerName;
    double cpuUsagePct = 0;         // amostrado via GetSystemTimes (2 leituras)
    double memUsagePct = 0;
    uint64_t memTotalMB = 0;
    uint64_t memUsedMB = 0;
    uint64_t diskTotalGB = 0;       // unidade do sistema
    uint64_t diskFreeGB = 0;
    double diskUsagePct = 0;
};

// Coleta as metricas. sampleMs = intervalo da amostragem de CPU (padrao 500ms).
DeviceInfo CollectDeviceInfo(DWORD sampleMs = 500);

} // namespace bm
