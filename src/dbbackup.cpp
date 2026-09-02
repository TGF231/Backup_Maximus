#include "dbbackup.h"
#include "logger.h"

namespace bm {

std::wstring DefaultDumpExt(ItemType t) {
    switch (t) {
        case ItemType::Firebird:  return L".fbk";
        case ItemType::SqlServer: return L".bak";
        case ItemType::MySql:     return L".sql";
        default:                  return L"";
    }
}

static std::wstring SearchTool(const wchar_t* exe, const std::vector<std::wstring>& extraDirs) {
    for (const auto& d : extraDirs) {
        std::wstring p = PathJoin(d, exe);
        if (FileExists(p)) return p;
    }
    wchar_t found[MAX_PATH];
    if (SearchPathW(nullptr, exe, nullptr, MAX_PATH, found, nullptr))
        return found;
    return L"";
}

static void GlobDirs(const std::wstring& pattern, std::vector<std::wstring>& out) {
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(pattern.c_str(), &fd);
    if (h == INVALID_HANDLE_VALUE) return;
    std::wstring base = pattern.substr(0, pattern.find_last_of(L'\\'));
    do {
        if ((fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) &&
            wcscmp(fd.cFileName, L".") && wcscmp(fd.cFileName, L".."))
            out.push_back(PathJoin(base, fd.cFileName));
    } while (FindNextFileW(h, &fd));
    FindClose(h);
}

std::wstring FindDbTool(const BackupItem& item) {
    if (!item.toolPath.empty() && FileExists(item.toolPath)) return item.toolPath;

    std::vector<std::wstring> dirs;
    switch (item.type) {
    case ItemType::Firebird: {
        // Firebird 2.5 usa Firebird_2_5\bin; 3.0+ mantem gbak na raiz da instalacao.
        GlobDirs(L"C:\\Program Files\\Firebird\\*", dirs);
        GlobDirs(L"C:\\Program Files (x86)\\Firebird\\*", dirs);
        std::vector<std::wstring> binDirs;
        for (auto& d : dirs) binDirs.push_back(PathJoin(d, L"bin"));
        for (auto& d : dirs) binDirs.push_back(d);
        return SearchTool(L"gbak.exe", binDirs);
    }
    case ItemType::SqlServer: {
        std::vector<std::wstring> binDirs;
        GlobDirs(L"C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\*", dirs);
        for (auto& d : dirs) binDirs.push_back(PathJoin(d, L"Tools\\Binn"));
        dirs.clear();
        GlobDirs(L"C:\\Program Files\\Microsoft SQL Server\\*", dirs);
        for (auto& d : dirs) binDirs.push_back(PathJoin(d, L"Tools\\Binn"));
        return SearchTool(L"sqlcmd.exe", binDirs);
    }
    case ItemType::MySql: {
        GlobDirs(L"C:\\Program Files\\MySQL\\*", dirs);
        GlobDirs(L"C:\\Program Files\\MariaDB*", dirs);
        std::vector<std::wstring> binDirs;
        for (auto& d : dirs) binDirs.push_back(PathJoin(d, L"bin"));
        return SearchTool(L"mysqldump.exe", binDirs);
    }
    default:
        return L"";
    }
}

static std::wstring TargetFile(const BackupItem& item, const std::wstring& targetDir) {
    std::wstring name = Trim(item.outputName);
    if (name.empty()) name = item.name + DefaultDumpExt(item.type);
    return PathJoin(targetDir, name);
}

static bool DumpFirebird(const BackupItem& item, const std::wstring& targetDir,
                         std::wstring& outFile, std::wstring& errOut) {
    std::wstring gbak = FindDbTool(item);
    if (gbak.empty()) {
        errOut = L"gbak.exe nao encontrado. Informe o caminho no campo 'Ferramenta' do item.";
        return false;
    }

    // Conexao: HOST[/porta]:ALIAS_OU_CAMINHO  (igual ao LOCALHOST:PDVEXPRESSO do .bat)
    std::wstring conn = item.source;
    if (!item.host.empty()) {
        conn = item.host;
        if (!item.port.empty()) conn += L"/" + item.port;
        conn += L":" + item.source;
    }

    outFile = TargetFile(item, targetDir);
    if (FileExists(outFile)) DeleteFileW(outFile.c_str());

    std::wstring pass = UnprotectSecret(item.passEnc);
    std::wstring user = item.user.empty() ? L"SYSDBA" : item.user;

    // -b backup | -g nao dispara garbage collection | -t transportavel
    std::wstring cmd = QuoteArg(gbak) + L" -b -g -t " + QuoteArg(conn) + L" " + QuoteArg(outFile) +
                       L" -user " + QuoteArg(user);
    if (!pass.empty()) cmd += L" -password " + QuoteArg(pass);

    std::wstring out;
    int rc = RunProcessCapture(cmd, out);
    if (!pass.empty()) SecureZeroMemory(&pass[0], pass.size() * sizeof(wchar_t));

    if (rc != 0 || !FileExists(outFile)) {
        errOut = L"gbak falhou (rc=" + std::to_wstring(rc) + L"): " + Trim(out).substr(0, 800);
        return false;
    }
    return true;
}

static bool DumpSqlServer(const BackupItem& item, const std::wstring& targetDir,
                          std::wstring& outFile, std::wstring& errOut) {
    std::wstring sqlcmd = FindDbTool(item);
    if (sqlcmd.empty()) {
        errOut = L"sqlcmd.exe nao encontrado. Instale as SQL Server Command Line Utilities "
                 L"ou informe o caminho no item.";
        return false;
    }

    // O BACKUP roda dentro do servico do SQL Server: a conta de servico precisa
    // enxergar e escrever em targetDir. Para instancia local isso e o caso normal.
    outFile = TargetFile(item, targetDir);
    std::wstring db = ReplaceAll(item.source, L"]", L"]]");
    std::wstring query = L"BACKUP DATABASE [" + db + L"] TO DISK=N'" +
                         ReplaceAll(outFile, L"'", L"''") + L"' WITH COPY_ONLY, INIT, CHECKSUM";

    std::wstring server = item.host.empty() ? L"localhost" : item.host;
    if (!item.port.empty()) server += L"," + item.port;

    std::wstring cmd = QuoteArg(sqlcmd) + L" -S " + QuoteArg(server) + L" -b -Q " + QuoteArg(query);
    std::wstring pass = UnprotectSecret(item.passEnc);
    if (!item.user.empty()) cmd += L" -U " + QuoteArg(item.user) + L" -P " + QuoteArg(pass);
    else                    cmd += L" -E";      // autenticacao Windows

    std::wstring out;
    int rc = RunProcessCapture(cmd, out);
    if (!pass.empty()) SecureZeroMemory(&pass[0], pass.size() * sizeof(wchar_t));

    if (rc != 0 || !FileExists(outFile)) {
        errOut = L"sqlcmd/BACKUP DATABASE falhou (rc=" + std::to_wstring(rc) + L"): " +
                 Trim(out).substr(0, 800);
        return false;
    }
    return true;
}

static bool DumpMySql(const BackupItem& item, const std::wstring& targetDir,
                      std::wstring& outFile, std::wstring& errOut) {
    std::wstring mysqldump = FindDbTool(item);
    if (mysqldump.empty()) {
        errOut = L"mysqldump.exe nao encontrado. Informe o caminho no item.";
        return false;
    }

    outFile = TargetFile(item, targetDir);
    std::wstring pass = UnprotectSecret(item.passEnc);

    std::wstring cmd = QuoteArg(mysqldump) +
                       L" --single-transaction --routines --triggers --events" +
                       L" --result-file=" + QuoteArg(outFile);
    if (!item.host.empty()) cmd += L" -h " + QuoteArg(item.host);
    if (!item.port.empty()) cmd += L" -P " + item.port;
    if (!item.user.empty()) cmd += L" -u " + QuoteArg(item.user);
    if (!pass.empty())      cmd += L" --password=" + QuoteArg(pass);
    cmd += L" " + QuoteArg(item.source);

    std::wstring out;
    int rc = RunProcessCapture(cmd, out);
    if (!pass.empty()) SecureZeroMemory(&pass[0], pass.size() * sizeof(wchar_t));

    if (rc != 0 || !FileExists(outFile)) {
        errOut = L"mysqldump falhou (rc=" + std::to_wstring(rc) + L"): " + Trim(out).substr(0, 800);
        return false;
    }
    return true;
}

bool DumpDatabase(const BackupItem& item, const std::wstring& targetDir,
                  std::wstring& outFile, std::wstring& errOut) {
    errOut.clear();
    if (!EnsureDir(targetDir)) {
        errOut = L"Nao foi possivel criar a pasta de destino: " + targetDir;
        return false;
    }
    switch (item.type) {
    case ItemType::Firebird:  return DumpFirebird(item, targetDir, outFile, errOut);
    case ItemType::SqlServer: return DumpSqlServer(item, targetDir, outFile, errOut);
    case ItemType::MySql:     return DumpMySql(item, targetDir, outFile, errOut);
    default:
        errOut = L"DumpDatabase chamado para um tipo que nao e banco de dados.";
        return false;
    }
}

} // namespace bm
