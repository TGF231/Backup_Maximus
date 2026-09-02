#include "network.h"
#include "logger.h"
#include <winnetwk.h>
#include <set>

#pragma comment(lib, "mpr.lib")

namespace bm {

static std::set<std::wstring> g_connected;

// Extrai \\servidor\share de um caminho UNC completo.
static std::wstring UncRootOf(const std::wstring& path) {
    if (!StartsWith(path, L"\\\\")) return L"";
    size_t p = path.find(L'\\', 2);
    if (p == std::wstring::npos) return path;
    size_t q = path.find(L'\\', p + 1);
    return q == std::wstring::npos ? path : path.substr(0, q);
}

bool EnsureNetworkAccess(const std::wstring& path,
                         const std::vector<NetCredential>& creds,
                         std::wstring& errOut) {
    errOut.clear();
    std::wstring root = UncRootOf(path);
    if (root.empty()) return true;                      // caminho local
    if (g_connected.count(ToLower(root))) return true;  // ja conectado nesta execucao

    // Procura credencial configurada para esta raiz.
    const NetCredential* cred = nullptr;
    for (const auto& c : creds) {
        if (ToLower(UncRootOf(c.uncRoot)) == ToLower(root)) { cred = &c; break; }
    }

    // Primeiro tenta acesso direto (sessao ja pode existir / share sem senha).
    if (DirExists(root) || FileExists(path)) {
        g_connected.insert(ToLower(root));
        return true;
    }

    if (!cred) {
        errOut = L"Sem acesso a " + root + L" e nenhuma credencial configurada para este compartilhamento.";
        return false;
    }

    NETRESOURCEW nr{};
    nr.dwType = RESOURCETYPE_DISK;
    std::wstring remote = root;
    nr.lpRemoteName = &remote[0];

    std::wstring pass = UnprotectSecret(cred->passEnc);
    DWORD rc = WNetAddConnection2W(&nr, pass.c_str(), cred->user.c_str(), 0);
    SecureZeroMemory(&pass[0], pass.size() * sizeof(wchar_t));

    if (rc == NO_ERROR || rc == ERROR_SESSION_CREDENTIAL_CONFLICT) {
        // Conflito de credencial significa que ja ha sessao valida com o servidor.
        g_connected.insert(ToLower(root));
        Logger::Info(L"Conectado ao compartilhamento " + root);
        return true;
    }
    errOut = L"Falha ao conectar em " + root + L" (WNetAddConnection2 erro " + std::to_wstring(rc) + L")";
    return false;
}

void DisconnectNetworkShares() {
    for (const auto& root : g_connected) {
        WNetCancelConnection2W(root.c_str(), 0, FALSE);
    }
    g_connected.clear();
}

} // namespace bm
