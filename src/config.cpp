#include "config.h"
#include "logger.h"
#include <wincrypt.h>
#include <bcrypt.h>
#include <fstream>
#include <sstream>
#include <map>

#pragma comment(lib, "crypt32.lib")
#pragma comment(lib, "bcrypt.lib")

namespace bm {

// ---------------- enums ----------------
std::wstring ItemTypeName(ItemType t) {
    switch (t) {
        case ItemType::Firebird:  return L"firebird";
        case ItemType::SqlServer: return L"sqlserver";
        case ItemType::MySql:     return L"mysql";
        case ItemType::Dbf:       return L"dbf";
        default:                  return L"files";
    }
}
bool ParseItemType(const std::wstring& s, ItemType& out) {
    std::wstring v = ToLower(Trim(s));
    if (v == L"firebird")  { out = ItemType::Firebird;  return true; }
    if (v == L"sqlserver") { out = ItemType::SqlServer; return true; }
    if (v == L"mysql")     { out = ItemType::MySql;     return true; }
    if (v == L"dbf")       { out = ItemType::Dbf;       return true; }
    if (v == L"files")     { out = ItemType::Files;     return true; }
    return false;
}
std::wstring SetModeName(SetMode m) {
    return m == SetMode::Incremental ? L"incremental" : L"full";
}
bool ParseSetMode(const std::wstring& s, SetMode& out) {
    std::wstring v = ToLower(Trim(s));
    if (v == L"incremental") { out = SetMode::Incremental; return true; }
    if (v == L"full")        { out = SetMode::Full;        return true; }
    return false;
}

int Config::TotalItems() const {
    int n = 0;
    for (const auto& s : sets) n += (int)s.items.size();
    return n;
}

// ---------------- base64 ----------------
static std::wstring B64Encode(const std::vector<BYTE>& data) {
    if (data.empty()) return L"";
    DWORD len = 0;
    CryptBinaryToStringW(data.data(), (DWORD)data.size(),
                         CRYPT_STRING_BASE64 | CRYPT_STRING_NOCRLF, nullptr, &len);
    std::wstring out(len, 0);
    CryptBinaryToStringW(data.data(), (DWORD)data.size(),
                         CRYPT_STRING_BASE64 | CRYPT_STRING_NOCRLF, &out[0], &len);
    while (!out.empty() && (out.back() == 0 || out.back() == L'\r' || out.back() == L'\n'))
        out.pop_back();
    return out;
}
static std::vector<BYTE> B64Decode(const std::wstring& s) {
    std::vector<BYTE> out;
    if (s.empty()) return out;
    DWORD len = 0;
    if (!CryptStringToBinaryW(s.c_str(), (DWORD)s.size(), CRYPT_STRING_BASE64, nullptr, &len, nullptr, nullptr))
        return out;
    out.resize(len);
    CryptStringToBinaryW(s.c_str(), (DWORD)s.size(), CRYPT_STRING_BASE64, out.data(), &len, nullptr, nullptr);
    out.resize(len);
    return out;
}

// ---------------- DPAPI ----------------
std::wstring ProtectSecret(const std::wstring& plain) {
    if (plain.empty()) return L"";
    std::string utf8 = WideToUtf8(plain);
    DATA_BLOB in{ (DWORD)utf8.size(), (BYTE*)utf8.data() };
    DATA_BLOB out{};
    if (!CryptProtectData(&in, L"BackupMaximus", nullptr, nullptr, nullptr,
                          CRYPTPROTECT_UI_FORBIDDEN, &out))
        return L"";
    std::vector<BYTE> enc(out.pbData, out.pbData + out.cbData);
    LocalFree(out.pbData);
    return B64Encode(enc);
}

std::wstring UnprotectSecret(const std::wstring& enc) {
    if (enc.empty()) return L"";
    std::vector<BYTE> data = B64Decode(enc);
    if (data.empty()) return L"";
    DATA_BLOB in{ (DWORD)data.size(), data.data() };
    DATA_BLOB out{};
    if (!CryptUnprotectData(&in, nullptr, nullptr, nullptr, nullptr,
                            CRYPTPROTECT_UI_FORBIDDEN, &out))
        return L"";
    std::string utf8((char*)out.pbData, out.cbData);
    LocalFree(out.pbData);
    return Utf8ToWide(utf8);
}

// ---------------- SHA-256 ----------------
std::wstring Sha256Hex(const std::wstring& data) {
    std::string utf8 = WideToUtf8(data);
    BCRYPT_ALG_HANDLE alg = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    std::wstring result;
    if (BCryptOpenAlgorithmProvider(&alg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) == 0) {
        if (BCryptCreateHash(alg, &hash, nullptr, 0, nullptr, 0, 0) == 0) {
            BCryptHashData(hash, (PUCHAR)utf8.data(), (ULONG)utf8.size(), 0);
            UCHAR digest[32];
            if (BCryptFinishHash(hash, digest, 32, 0) == 0) {
                wchar_t hex[65];
                for (int i = 0; i < 32; ++i)
                    swprintf(hex + i * 2, 3, L"%02x", digest[i]);
                result = hex;
            }
            BCryptDestroyHash(hash);
        }
        BCryptCloseAlgorithmProvider(alg, 0);
    }
    return result;
}

void Config::SetPassword(const std::wstring& plain) {
    UCHAR salt[16];
    BCryptGenRandom(nullptr, salt, 16, BCRYPT_USE_SYSTEM_PREFERRED_RNG);
    wchar_t hex[33];
    for (int i = 0; i < 16; ++i) swprintf(hex + i * 2, 3, L"%02x", salt[i]);
    uiPasswordSalt = hex;
    uiPasswordHash = Sha256Hex(uiPasswordSalt + plain);
}

bool Config::CheckPassword(const std::wstring& plain) const {
    if (uiPasswordHash.empty()) return true;
    return Sha256Hex(uiPasswordSalt + plain) == uiPasswordHash;
}

// ---------------- INI ----------------
std::wstring Config::DefaultPath() {
    return PathJoin(ExeDir(), L"backup_maximus.ini");
}

bool Config::Load(const std::wstring& path) {
    std::ifstream f(path.c_str(), std::ios::binary);
    if (!f) return false;
    std::string raw((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    if (raw.size() >= 3 && (BYTE)raw[0] == 0xEF && (BYTE)raw[1] == 0xBB && (BYTE)raw[2] == 0xBF)
        raw.erase(0, 3);
    std::wstring text = Utf8ToWide(raw);

    std::map<std::wstring, std::map<std::wstring, std::wstring>> ini;
    std::wstring section;
    for (auto& line : Split(text, L'\n')) {
        std::wstring l = Trim(line);
        if (l.empty() || l[0] == L';' || l[0] == L'#') continue;
        if (l.front() == L'[' && l.back() == L']') {
            section = ToLower(l.substr(1, l.size() - 2));
            continue;
        }
        size_t eq = l.find(L'=');
        if (eq == std::wstring::npos) continue;
        ini[section][ToLower(Trim(l.substr(0, eq)))] = Trim(l.substr(eq + 1));
    }

    auto has = [&](const std::wstring& sec) { return ini.find(sec) != ini.end(); };
    auto get = [&](const std::wstring& sec, const std::wstring& key, const std::wstring& def = L"") {
        auto s = ini.find(sec);
        if (s == ini.end()) return def;
        auto k = s->second.find(key);
        return k == s->second.end() ? def : k->second;
    };
    auto getInt = [&](const std::wstring& sec, const std::wstring& key, int def) {
        std::wstring v = get(sec, key);
        return v.empty() ? def : _wtoi(v.c_str());
    };
    auto getBool = [&](const std::wstring& sec, const std::wstring& key, bool def) {
        std::wstring v = get(sec, key);
        return v.empty() ? def : (v == L"1");
    };

    companyName       = get(L"general", L"company");
    notifyEmail       = get(L"general", L"notify_email");
    alertTimeoutHours = getInt(L"general", L"alert_timeout_hours", 26);
    sendReportEmail   = getBool(L"general", L"send_report_email", false);
    uiPasswordHash    = get(L"general", L"ui_password_hash");
    uiPasswordSalt    = get(L"general", L"ui_password_salt");
    sevenZipPath      = get(L"general", L"sevenzip_path");

    smtp.host    = get(L"smtp", L"host");
    smtp.port    = getInt(L"smtp", L"port", 587);
    smtp.useSsl  = getBool(L"smtp", L"ssl", true);
    smtp.user    = get(L"smtp", L"user");
    smtp.passEnc = get(L"smtp", L"password_enc");
    smtp.from    = get(L"smtp", L"from");

    lastRunUnix   = _wtoi64(get(L"state", L"last_run_unix", L"0").c_str());
    lastRunStatus = get(L"state", L"last_run_status");

    netCreds.clear();
    for (int i = 1; ; ++i) {
        std::wstring sec = L"netcred." + std::to_wstring(i);
        if (!has(sec)) break;
        NetCredential nc;
        nc.uncRoot = get(sec, L"unc");
        nc.user    = get(sec, L"user");
        nc.passEnc = get(sec, L"password_enc");
        if (!nc.uncRoot.empty()) netCreds.push_back(nc);
    }

    sets.clear();
    for (int s = 1; ; ++s) {
        std::wstring ssec = L"set." + std::to_wstring(s);
        if (!has(ssec)) break;
        BackupSet bs;
        bs.name           = get(ssec, L"name", L"conjunto" + std::to_wstring(s));
        bs.staging        = get(ssec, L"staging");
        bs.destination    = get(ssec, L"destination");
        ParseSetMode(get(ssec, L"mode", L"full"), bs.mode);
        bs.waitForPath    = get(ssec, L"wait_for_path");
        bs.waitTimeoutSec = getInt(ssec, L"wait_timeout_sec", 300);
        bs.keepStaging    = getBool(ssec, L"keep_staging", true);
        bs.enabled        = getBool(ssec, L"enabled", true);

        for (int i = 1; ; ++i) {
            std::wstring isec = L"item." + std::to_wstring(s) + L"." + std::to_wstring(i);
            if (!has(isec)) break;
            BackupItem it;
            it.name = get(isec, L"name", L"item" + std::to_wstring(i));
            ParseItemType(get(isec, L"type", L"files"), it.type);
            it.source     = get(isec, L"source");
            it.subfolder  = get(isec, L"subfolder");
            it.outputName = get(isec, L"output_name");
            it.mirror     = getBool(isec, L"mirror", true);
            it.host       = get(isec, L"host");
            it.port       = get(isec, L"port");
            it.user       = get(isec, L"user");
            it.passEnc    = get(isec, L"password_enc");
            it.toolPath   = get(isec, L"tool_path");
            it.enabled    = getBool(isec, L"enabled", true);
            bs.items.push_back(it);
        }
        sets.push_back(bs);
    }
    return true;
}

bool Config::Save(const std::wstring& path) const {
    std::wostringstream o;
    o << L"; Backup Maximus - arquivo de configuracao\n";
    o << L"; Um [set.N] produz UM arquivo .zip. Cada [item.N.M] coloca seu conteudo\n";
    o << L"; na subpasta indicada dentro da arvore de montagem, e a arvore inteira\n";
    o << L"; vira esse zip. Senhas sao cifradas com DPAPI (validas so nesta maquina).\n\n";

    o << L"[general]\n";
    o << L"company=" << companyName << L"\n";
    o << L"notify_email=" << notifyEmail << L"\n";
    o << L"alert_timeout_hours=" << alertTimeoutHours << L"\n";
    o << L"send_report_email=" << (sendReportEmail ? 1 : 0) << L"\n";
    o << L"ui_password_hash=" << uiPasswordHash << L"\n";
    o << L"ui_password_salt=" << uiPasswordSalt << L"\n";
    o << L"sevenzip_path=" << sevenZipPath << L"\n\n";

    o << L"[smtp]\n";
    o << L"host=" << smtp.host << L"\n";
    o << L"port=" << smtp.port << L"\n";
    o << L"ssl=" << (smtp.useSsl ? 1 : 0) << L"\n";
    o << L"user=" << smtp.user << L"\n";
    o << L"password_enc=" << smtp.passEnc << L"\n";
    o << L"from=" << smtp.from << L"\n\n";

    o << L"[state]\n";
    o << L"last_run_unix=" << lastRunUnix << L"\n";
    o << L"last_run_status=" << lastRunStatus << L"\n\n";

    for (size_t i = 0; i < netCreds.size(); ++i) {
        o << L"[netcred." << (i + 1) << L"]\n";
        o << L"unc=" << netCreds[i].uncRoot << L"\n";
        o << L"user=" << netCreds[i].user << L"\n";
        o << L"password_enc=" << netCreds[i].passEnc << L"\n\n";
    }

    for (size_t s = 0; s < sets.size(); ++s) {
        const BackupSet& bs = sets[s];
        o << L"[set." << (s + 1) << L"]\n";
        o << L"name=" << bs.name << L"\n";
        o << L"staging=" << bs.staging << L"\n";
        o << L"destination=" << bs.destination << L"\n";
        o << L"mode=" << SetModeName(bs.mode) << L"\n";
        o << L"wait_for_path=" << bs.waitForPath << L"\n";
        o << L"wait_timeout_sec=" << bs.waitTimeoutSec << L"\n";
        o << L"keep_staging=" << (bs.keepStaging ? 1 : 0) << L"\n";
        o << L"enabled=" << (bs.enabled ? 1 : 0) << L"\n\n";

        for (size_t i = 0; i < bs.items.size(); ++i) {
            const BackupItem& it = bs.items[i];
            o << L"[item." << (s + 1) << L"." << (i + 1) << L"]\n";
            o << L"name=" << it.name << L"\n";
            o << L"type=" << ItemTypeName(it.type) << L"\n";
            o << L"source=" << it.source << L"\n";
            o << L"subfolder=" << it.subfolder << L"\n";
            o << L"output_name=" << it.outputName << L"\n";
            o << L"mirror=" << (it.mirror ? 1 : 0) << L"\n";
            o << L"host=" << it.host << L"\n";
            o << L"port=" << it.port << L"\n";
            o << L"user=" << it.user << L"\n";
            o << L"password_enc=" << it.passEnc << L"\n";
            o << L"tool_path=" << it.toolPath << L"\n";
            o << L"enabled=" << (it.enabled ? 1 : 0) << L"\n\n";
        }
    }

    std::string utf8 = "\xEF\xBB\xBF" + WideToUtf8(o.str());
    std::wstring tmp = path + L".tmp";
    {
        std::ofstream f(tmp.c_str(), std::ios::binary | std::ios::trunc);
        if (!f) return false;
        f.write(utf8.data(), utf8.size());
    }
    if (!MoveFileExW(tmp.c_str(), path.c_str(), MOVEFILE_REPLACE_EXISTING)) {
        DeleteFileW(tmp.c_str());
        return false;
    }
    return true;
}

} // namespace bm
