#include "zip.h"
#include "logger.h"

namespace bm {

static std::wstring FindSevenZip(const std::wstring& hint) {
    if (!hint.empty() && FileExists(hint)) return hint;
    const wchar_t* candidates[] = {
        L"C:\\Program Files\\7-Zip\\7z.exe",
        L"C:\\Program Files (x86)\\7-Zip\\7z.exe",
    };
    for (auto c : candidates)
        if (FileExists(c)) return c;
    wchar_t found[MAX_PATH];
    if (SearchPathW(nullptr, L"7z.exe", nullptr, MAX_PATH, found, nullptr))
        return found;
    return L"";
}

Zipper::Zipper(const std::wstring& sevenZipHint) : m_7z(FindSevenZip(sevenZipHint)) {}

std::wstring Zipper::ToolDescription() const {
    return m_7z.empty() ? L"PowerShell Compress-Archive (fallback)" : L"7-Zip: " + m_7z;
}

bool Zipper::Run7z(const std::wstring& args, std::wstring& errOut) {
    std::wstring out;
    std::wstring cmd = QuoteArg(m_7z) + L" " + args + L" -y -bd";
    int rc = RunProcessCapture(cmd, out);
    if (rc == 0) return true;
    if (rc == 1) {   // avisos: algum arquivo estava em uso e foi pulado
        Logger::Warn(L"7-Zip terminou com avisos: " + Trim(out).substr(0, 400));
        return true;
    }
    errOut = L"7z retornou " + std::to_wstring(rc) + L": " + Trim(out).substr(0, 800);
    return false;
}

bool Zipper::RunPs(const std::wstring& script, std::wstring& errOut) {
    std::wstring out;
    std::wstring cmd = L"powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command " +
                       QuoteArg(L"$ErrorActionPreference='Stop'; " + script);
    int rc = RunProcessCapture(cmd, out);
    if (rc == 0) return true;
    errOut = L"PowerShell retornou " + std::to_wstring(rc) + L": " + Trim(out).substr(0, 800);
    return false;
}

static std::wstring PsQuote(const std::wstring& s) {
    return L"'" + ReplaceAll(s, L"'", L"''") + L"'";
}

bool Zipper::ArchiveTree(const std::wstring& treeDir, const std::wstring& zipPath,
                         bool maxCompression, bool update, std::wstring& errOut) {
    if (!DirExists(treeDir)) {
        errOut = L"Arvore de montagem nao encontrada: " + treeDir;
        return false;
    }
    if (!update && FileExists(zipPath)) DeleteFileW(zipPath.c_str());

    if (!m_7z.empty()) {
        // Passar a PASTA (nao pasta\*) faz o 7-Zip preservar a raiz dentro do zip,
        // reproduzindo o que o WinRAR faz ao receber "C:\BACKUP".
        std::wstring lvl = maxCompression ? L"-mx9" : L"-mx1";
        std::wstring verb = update ? L"u" : L"a";
        // -ssw inclui arquivos abertos para escrita (bancos e logs em uso).
        return Run7z(verb + L" -tzip " + lvl + L" -ssw -r " +
                     QuoteArg(zipPath) + L" " + QuoteArg(treeDir), errOut);
    }

    // Fallback: Compress-Archive compacta o CONTEUDO da pasta quando recebe
    // pasta\* e a propria pasta quando recebe a pasta. Usamos a pasta para
    // manter a raiz, igual ao caminho do 7-Zip.
    std::wstring level = maxCompression ? L"Optimal" : L"Fastest";
    std::wstring script = L"Compress-Archive -Path " + PsQuote(treeDir) +
                          L" -DestinationPath " + PsQuote(zipPath) +
                          L" -CompressionLevel " + level +
                          (update && FileExists(zipPath) ? L" -Update" : L" -Force");
    return RunPs(script, errOut);
}

bool Zipper::AddFile(const std::wstring& zipPath, const std::wstring& filePath,
                     std::wstring& errOut) {
    if (!FileExists(filePath)) {
        errOut = L"Arquivo nao encontrado: " + filePath;
        return false;
    }
    if (!m_7z.empty())
        return Run7z(L"u -tzip -mx1 " + QuoteArg(zipPath) + L" " + QuoteArg(filePath), errOut);

    return RunPs(L"Compress-Archive -Path " + PsQuote(filePath) +
                 L" -DestinationPath " + PsQuote(zipPath) +
                 L" -CompressionLevel Fastest -Update", errOut);
}

bool Zipper::ExtractFile(const std::wstring& zipPath, const std::wstring& entryName,
                         const std::wstring& destDir, std::wstring& errOut) {
    EnsureDir(destDir);
    if (!m_7z.empty()) {
        // 'e' extrai sem recriar a estrutura; -r acha a entrada em qualquer nivel.
        return Run7z(L"e -r " + QuoteArg(zipPath) + L" -o" + QuoteArg(destDir) + L" " +
                     QuoteArg(entryName), errOut);
    }
    std::wstring script =
        L"Add-Type -AssemblyName System.IO.Compression.FileSystem; "
        L"$z=[System.IO.Compression.ZipFile]::OpenRead(" + PsQuote(zipPath) + L"); "
        L"try { $e=$z.Entries | Where-Object { $_.Name -eq " + PsQuote(entryName) + L" } | Select-Object -First 1; "
        L"if (-not $e) { throw 'entrada nao encontrada no zip' }; "
        L"[System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, (Join-Path " +
        PsQuote(destDir) + L" $e.Name), $true) } finally { $z.Dispose() }";
    return RunPs(script, errOut);
}

} // namespace bm
