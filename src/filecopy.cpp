#include "filecopy.h"
#include "logger.h"
#include <set>

namespace bm {

// Prefixo \\?\ remove o limite de 260 caracteres do MAX_PATH.
static std::wstring LongPath(const std::wstring& p) {
    if (StartsWith(p, L"\\\\?\\")) return p;
    if (p.size() < 240) return p;
    if (StartsWith(p, L"\\\\")) return L"\\\\?\\UNC\\" + p.substr(2);
    return L"\\\\?\\" + p;
}

// Dois arquivos sao considerados iguais quando tamanho e hora de escrita batem.
// E o mesmo criterio do robocopy sem /FFT, e evita reler conteudo.
static bool SameFile(const WIN32_FIND_DATAW& src, const std::wstring& destPath) {
    WIN32_FILE_ATTRIBUTE_DATA d;
    if (!GetFileAttributesExW(LongPath(destPath).c_str(), GetFileExInfoStandard, &d))
        return false;
    if (d.nFileSizeLow != src.nFileSizeLow || d.nFileSizeHigh != src.nFileSizeHigh)
        return false;
    // Tolerancia de 2 s: FAT32 (pen drives) grava a hora com resolucao de 2 segundos.
    ULARGE_INTEGER a{}, b{};
    a.LowPart = src.ftLastWriteTime.dwLowDateTime;
    a.HighPart = src.ftLastWriteTime.dwHighDateTime;
    b.LowPart = d.ftLastWriteTime.dwLowDateTime;
    b.HighPart = d.ftLastWriteTime.dwHighDateTime;
    uint64_t diff = a.QuadPart > b.QuadPart ? a.QuadPart - b.QuadPart : b.QuadPart - a.QuadPart;
    return diff <= 20000000ull;   // 2 s em unidades de 100 ns
}

uint64_t DirectorySize(const std::wstring& dir) {
    uint64_t total = 0;
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(LongPath(PathJoin(dir, L"*")).c_str(), &fd);
    if (h == INVALID_HANDLE_VALUE) return 0;
    do {
        if (!wcscmp(fd.cFileName, L".") || !wcscmp(fd.cFileName, L"..")) continue;
        if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            total += DirectorySize(PathJoin(dir, fd.cFileName));
        } else {
            total += ((uint64_t)fd.nFileSizeHigh << 32) | fd.nFileSizeLow;
        }
    } while (FindNextFileW(h, &fd));
    FindClose(h);
    return total;
}

bool RemoveTree(const std::wstring& dir) {
    if (!DirExists(dir)) return true;
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(LongPath(PathJoin(dir, L"*")).c_str(), &fd);
    if (h != INVALID_HANDLE_VALUE) {
        do {
            if (!wcscmp(fd.cFileName, L".") || !wcscmp(fd.cFileName, L"..")) continue;
            std::wstring child = PathJoin(dir, fd.cFileName);
            if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
                RemoveTree(child);
            } else {
                if (fd.dwFileAttributes & FILE_ATTRIBUTE_READONLY)
                    SetFileAttributesW(LongPath(child).c_str(), FILE_ATTRIBUTE_NORMAL);
                DeleteFileW(LongPath(child).c_str());
            }
        } while (FindNextFileW(h, &fd));
        FindClose(h);
    }
    return RemoveDirectoryW(LongPath(dir).c_str()) != 0;
}

bool CopyOneFile(const std::wstring& srcFile, const std::wstring& destDir, CopyStats& stats) {
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(LongPath(srcFile).c_str(), &fd);
    if (h == INVALID_HANDLE_VALUE) {
        stats.errors++;
        stats.lastError = L"Origem nao encontrada: " + srcFile;
        return false;
    }
    FindClose(h);

    if (!EnsureDir(destDir)) {
        stats.errors++;
        stats.lastError = L"Nao foi possivel criar: " + destDir;
        return false;
    }
    std::wstring dest = PathJoin(destDir, fd.cFileName);

    if (SameFile(fd, dest)) { stats.filesSkipped++; return true; }

    // Destino somente-leitura precisa ser liberado antes de sobrescrever.
    DWORD attr = GetFileAttributesW(LongPath(dest).c_str());
    if (attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_READONLY))
        SetFileAttributesW(LongPath(dest).c_str(), FILE_ATTRIBUTE_NORMAL);

    if (!CopyFileW(LongPath(srcFile).c_str(), LongPath(dest).c_str(), FALSE)) {
        stats.errors++;
        stats.lastError = L"Falha ao copiar " + srcFile + L" (erro " +
                          std::to_wstring(GetLastError()) + L")";
        return false;
    }
    stats.filesCopied++;
    stats.bytesCopied += ((uint64_t)fd.nFileSizeHigh << 32) | fd.nFileSizeLow;
    return true;
}

bool MirrorDirectory(const std::wstring& srcDir, const std::wstring& destDir,
                     bool mirror, CopyStats& stats) {
    if (!DirExists(srcDir)) {
        stats.errors++;
        stats.lastError = L"Pasta de origem nao encontrada: " + srcDir;
        return false;
    }
    if (!EnsureDir(destDir)) {
        stats.errors++;
        stats.lastError = L"Nao foi possivel criar: " + destDir;
        return false;
    }

    std::set<std::wstring> srcNames;   // nomes vistos na origem (para o espelhamento)

    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(LongPath(PathJoin(srcDir, L"*")).c_str(), &fd);
    if (h != INVALID_HANDLE_VALUE) {
        do {
            if (!wcscmp(fd.cFileName, L".") || !wcscmp(fd.cFileName, L"..")) continue;
            srcNames.insert(ToLower(fd.cFileName));
            std::wstring src = PathJoin(srcDir, fd.cFileName);
            std::wstring dst = PathJoin(destDir, fd.cFileName);

            if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
                if (fd.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)
                    continue;               // nao segue junction/symlink: evita laco infinito
                MirrorDirectory(src, dst, mirror, stats);
            } else {
                if (SameFile(fd, dst)) { stats.filesSkipped++; continue; }
                DWORD attr = GetFileAttributesW(LongPath(dst).c_str());
                if (attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_READONLY))
                    SetFileAttributesW(LongPath(dst).c_str(), FILE_ATTRIBUTE_NORMAL);
                if (CopyFileW(LongPath(src).c_str(), LongPath(dst).c_str(), FALSE)) {
                    stats.filesCopied++;
                    stats.bytesCopied += ((uint64_t)fd.nFileSizeHigh << 32) | fd.nFileSizeLow;
                } else {
                    // Arquivo em uso nao aborta o backup — registra e segue.
                    stats.errors++;
                    stats.lastError = L"Falha ao copiar " + src + L" (erro " +
                                      std::to_wstring(GetLastError()) + L")";
                    Logger::Warn(stats.lastError);
                }
            }
        } while (FindNextFileW(h, &fd));
        FindClose(h);
    }

    if (!mirror) return true;

    // Espelhamento: remove do destino o que nao existe mais na origem.
    HANDLE hd = FindFirstFileW(LongPath(PathJoin(destDir, L"*")).c_str(), &fd);
    if (hd != INVALID_HANDLE_VALUE) {
        std::vector<std::wstring> toDeleteFiles, toDeleteDirs;
        do {
            if (!wcscmp(fd.cFileName, L".") || !wcscmp(fd.cFileName, L"..")) continue;
            if (srcNames.count(ToLower(fd.cFileName))) continue;
            std::wstring victim = PathJoin(destDir, fd.cFileName);
            if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) toDeleteDirs.push_back(victim);
            else toDeleteFiles.push_back(victim);
        } while (FindNextFileW(hd, &fd));
        FindClose(hd);

        // Deleta apos fechar o handle de busca, senao a enumeracao fica instavel.
        for (const auto& f : toDeleteFiles) {
            SetFileAttributesW(LongPath(f).c_str(), FILE_ATTRIBUTE_NORMAL);
            if (DeleteFileW(LongPath(f).c_str())) stats.filesDeleted++;
        }
        for (const auto& d : toDeleteDirs) {
            if (RemoveTree(d)) stats.filesDeleted++;
        }
    }
    return true;
}

} // namespace bm
