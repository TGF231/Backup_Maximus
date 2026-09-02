// Backup Maximus - ui_config.cpp
// Tela de configuracao protegida por senha, em 3 abas:
//   [Backups]        conjuntos (1 zip cada) + itens do conjunto, tudo numa tela
//   [Configuracoes]  empresa, email, timeout de alerta, SMTP, senha da UI
//   [Rede]           credenciais para compartilhamentos UNC
#include "ui.h"
#include "engine.h"
#include "logger.h"
#include "email.h"
#include "dbbackup.h"
#include <commctrl.h>
#include <shlobj.h>
#include <shobjidl.h>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "uuid.lib")

namespace bm {

// Sentinela em campos de senha ja gravados: se nao mudar, mantem o valor cifrado.
static const wchar_t* kPassSentinel = L"\x2022\x2022\x2022\x2022\x2022\x2022";

// ============================================================
//  Prompt de senha
// ============================================================
namespace {

struct GateCtx {
    bool firstRun = false;
    bool ok = false;
    Config* cfg = nullptr;
    HWND hEdit1 = nullptr, hEdit2 = nullptr;
};

LRESULT CALLBACK GateProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    GateCtx* c = (GateCtx*)GetWindowLongPtrW(hwnd, GWLP_USERDATA);
    switch (msg) {
    case WM_CREATE: {
        c = (GateCtx*)((CREATESTRUCTW*)lp)->lpCreateParams;
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, (LONG_PTR)c);
        HINSTANCE hi = ((CREATESTRUCTW*)lp)->hInstance;
        HFONT font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        auto mk = [&](const wchar_t* cls, const wchar_t* text, DWORD style,
                      int x, int y, int w, int h, int id) {
            HWND ctl = CreateWindowW(cls, text, WS_CHILD | WS_VISIBLE | style,
                                     x, y, w, h, hwnd, (HMENU)(INT_PTR)id, hi, nullptr);
            SendMessageW(ctl, WM_SETFONT, (WPARAM)font, TRUE);
            return ctl;
        };
        if (c->firstRun) {
            mk(L"STATIC", L"Primeira execucao: defina a senha de acesso as configuracoes.",
               0, 16, 12, 360, 32, 0);
            mk(L"STATIC", L"Senha:", 0, 16, 52, 110, 20, 0);
            c->hEdit1 = mk(L"EDIT", L"", WS_BORDER | ES_PASSWORD | WS_TABSTOP, 130, 50, 230, 22, 100);
            mk(L"STATIC", L"Confirmar:", 0, 16, 82, 110, 20, 0);
            c->hEdit2 = mk(L"EDIT", L"", WS_BORDER | ES_PASSWORD | WS_TABSTOP, 130, 80, 230, 22, 101);
        } else {
            mk(L"STATIC", L"Digite a senha para abrir as configuracoes:", 0, 16, 16, 360, 20, 0);
            c->hEdit1 = mk(L"EDIT", L"", WS_BORDER | ES_PASSWORD | WS_TABSTOP, 16, 44, 344, 22, 100);
        }
        mk(L"BUTTON", L"OK", BS_DEFPUSHBUTTON | WS_TABSTOP, 180, c->firstRun ? 116 : 80, 85, 26, IDOK);
        mk(L"BUTTON", L"Cancelar", WS_TABSTOP, 275, c->firstRun ? 116 : 80, 85, 26, IDCANCEL);
        SetFocus(c->hEdit1);
        return 0;
    }
    case WM_COMMAND:
        if (LOWORD(wp) == IDOK && c) {
            wchar_t p1[256] = L"", p2[256] = L"";
            GetWindowTextW(c->hEdit1, p1, 256);
            if (c->firstRun) {
                GetWindowTextW(c->hEdit2, p2, 256);
                if (wcslen(p1) < 4) {
                    MessageBoxW(hwnd, L"A senha deve ter pelo menos 4 caracteres.",
                                L"Backup Maximus", MB_ICONWARNING);
                    return 0;
                }
                if (wcscmp(p1, p2) != 0) {
                    MessageBoxW(hwnd, L"As senhas nao conferem.", L"Backup Maximus", MB_ICONWARNING);
                    return 0;
                }
                c->cfg->SetPassword(p1);
                c->ok = true;
                DestroyWindow(hwnd);
            } else {
                if (c->cfg->CheckPassword(p1)) {
                    c->ok = true;
                    DestroyWindow(hwnd);
                } else {
                    Logger::Warn(L"Tentativa de acesso as configuracoes com senha incorreta.");
                    MessageBoxW(hwnd, L"Senha incorreta.", L"Backup Maximus", MB_ICONERROR);
                    SetWindowTextW(c->hEdit1, L"");
                    SetFocus(c->hEdit1);
                }
            }
            SecureZeroMemory(p1, sizeof(p1));
            SecureZeroMemory(p2, sizeof(p2));
        } else if (LOWORD(wp) == IDCANCEL) {
            DestroyWindow(hwnd);
        }
        return 0;
    case WM_CLOSE:   DestroyWindow(hwnd); return 0;
    case WM_DESTROY: PostQuitMessage(0);  return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

} // namespace

bool PasswordGate(HINSTANCE hInst, Config& cfg, bool firstRun) {
    GateCtx ctx;
    ctx.firstRun = firstRun;
    ctx.cfg = &cfg;

    WNDCLASSW wc{};
    wc.lpfnWndProc = GateProc;
    wc.hInstance = hInst;
    wc.lpszClassName = L"BackupMaximusGate";
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassW(&wc);

    int sw = GetSystemMetrics(SM_CXSCREEN), sh = GetSystemMetrics(SM_CYSCREEN);
    int w = 400, h = firstRun ? 190 : 155;
    HWND hwnd = CreateWindowW(wc.lpszClassName,
        firstRun ? L"Backup Maximus - Definir senha" : L"Backup Maximus - Acesso restrito",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU,
        (sw - w) / 2, (sh - h) / 2, w, h, nullptr, nullptr, hInst, &ctx);
    ShowWindow(hwnd, SW_SHOW);

    MSG msg;
    while (GetMessageW(&msg, nullptr, 0, 0) > 0) {
        if (msg.message == WM_KEYDOWN && msg.wParam == VK_RETURN) {
            SendMessageW(hwnd, WM_COMMAND, IDOK, 0);
            continue;
        }
        if (!IsDialogMessageW(hwnd, &msg)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }
    return ctx.ok;
}

// ============================================================
//  Atalho da area de trabalho
// ============================================================
static bool CreateDesktopShortcut(std::wstring& errOut) {
    wchar_t exe[MAX_PATH];
    GetModuleFileNameW(nullptr, exe, MAX_PATH);
    wchar_t desktop[MAX_PATH];
    if (FAILED(SHGetFolderPathW(nullptr, CSIDL_DESKTOPDIRECTORY, nullptr, 0, desktop))) {
        errOut = L"Nao foi possivel localizar a area de trabalho.";
        return false;
    }
    std::wstring lnk = PathJoin(desktop, L"Backup Maximus - Executar.lnk");

    bool ok = false;
    if (SUCCEEDED(CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED))) {
        IShellLinkW* link = nullptr;
        if (SUCCEEDED(CoCreateInstance(CLSID_ShellLink, nullptr, CLSCTX_INPROC_SERVER,
                                       IID_IShellLinkW, (void**)&link))) {
            link->SetPath(exe);
            link->SetArguments(L"/run");
            link->SetDescription(L"Executa o backup imediatamente (sem abrir configuracoes)");
            IPersistFile* pf = nullptr;
            if (SUCCEEDED(link->QueryInterface(IID_IPersistFile, (void**)&pf))) {
                ok = SUCCEEDED(pf->Save(lnk.c_str(), TRUE));
                pf->Release();
            }
            link->Release();
        }
        CoUninitialize();
    }
    if (!ok) errOut = L"Falha ao criar o atalho.";
    return ok;
}

// ============================================================
//  Janela principal de configuracao
// ============================================================
namespace {

enum : int {
    ID_TAB = 500,
    // aba Backups — conjuntos
    ID_SETLIST = 510, ID_SET_NEW, ID_SET_DEL, ID_RUN_NOW,
    ID_S_NAME = 515, ID_S_DEST, ID_S_MODE, ID_S_STAGING, ID_S_WAIT, ID_S_WAITSEC,
    ID_S_KEEP, ID_S_ENABLED, ID_SET_SAVE,
    // aba Backups — itens
    ID_ITEMLIST = 528, ID_ITEM_NEW, ID_ITEM_DEL, ID_ITEM_UP, ID_ITEM_DOWN, ID_ITEM_SAVE,
    ID_I_NAME = 534, ID_I_TYPE, ID_I_SOURCE, ID_I_SUBFOLDER, ID_I_OUTNAME, ID_I_MIRROR,
    ID_I_HOST, ID_I_PORT, ID_I_USER, ID_I_PASS, ID_I_TOOL, ID_I_ENABLED,
    // aba Configuracoes
    ID_C_COMPANY = 550, ID_C_EMAIL, ID_C_TIMEOUT, ID_C_SENDMAIL,
    ID_C_SMTPHOST, ID_C_SMTPPORT, ID_C_SMTPSSL, ID_C_SMTPUSER, ID_C_SMTPPASS, ID_C_SMTPFROM,
    ID_C_7ZPATH, ID_C_CHPASS, ID_C_TESTMAIL, ID_C_SHORTCUT,
    // aba Rede
    ID_N_LIST = 570, ID_N_UNC, ID_N_USER, ID_N_PASS, ID_N_ADD, ID_N_DEL,
    // rodape
    ID_SAVEALL = 590, ID_CLOSE, ID_FOOT,
};

struct CfgCtx {
    Config* cfg = nullptr;
    std::wstring cfgPath;
    HINSTANCE hInst = nullptr;
    HWND hwnd = nullptr;
    HFONT font = nullptr, fontBold = nullptr;
    HWND hTab = nullptr;
    std::vector<HWND> page0, page1, page2;
    int curSet = -1;
    int curItem = -1;
    bool dirty = false;
};

HWND Ctl(CfgCtx* c, int id) { return GetDlgItem(c->hwnd, id); }

std::wstring GetText(CfgCtx* c, int id) {
    HWND h = Ctl(c, id);
    int n = GetWindowTextLengthW(h);
    std::wstring s(n, 0);
    if (n) GetWindowTextW(h, &s[0], n + 1);
    return s;
}
void SetText(CfgCtx* c, int id, const std::wstring& s) { SetWindowTextW(Ctl(c, id), s.c_str()); }
bool GetCheck(CfgCtx* c, int id) { return SendMessageW(Ctl(c, id), BM_GETCHECK, 0, 0) == BST_CHECKED; }
void SetCheck(CfgCtx* c, int id, bool v) { SendMessageW(Ctl(c, id), BM_SETCHECK, v ? BST_CHECKED : BST_UNCHECKED, 0); }

HWND Make(CfgCtx* c, const wchar_t* cls, const wchar_t* text, DWORD style,
          int x, int y, int w, int h, int id, std::vector<HWND>* page, bool bold = false) {
    HWND ctl = CreateWindowW(cls, text, WS_CHILD | style, x, y, w, h,
                             c->hwnd, (HMENU)(INT_PTR)id, c->hInst, nullptr);
    SendMessageW(ctl, WM_SETFONT, (WPARAM)(bold ? c->fontBold : c->font), TRUE);
    if (page) page->push_back(ctl);
    return ctl;
}
HWND Label(CfgCtx* c, const wchar_t* t, int x, int y, int w, std::vector<HWND>* p, bool bold = false) {
    return Make(c, L"STATIC", t, 0, x, y, w, 16, 0, p, bold);
}
HWND EditBox(CfgCtx* c, int id, int x, int y, int w, std::vector<HWND>* p, DWORD extra = 0) {
    return Make(c, L"EDIT", L"", WS_BORDER | WS_TABSTOP | ES_AUTOHSCROLL | extra, x, y, w, 21, id, p);
}

BackupSet* CurSet(CfgCtx* c) {
    if (c->curSet < 0 || c->curSet >= (int)c->cfg->sets.size()) return nullptr;
    return &c->cfg->sets[c->curSet];
}
BackupItem* CurItem(CfgCtx* c) {
    BackupSet* s = CurSet(c);
    if (!s || c->curItem < 0 || c->curItem >= (int)s->items.size()) return nullptr;
    return &s->items[c->curItem];
}

// ---------- listas ----------
void RefreshSetList(CfgCtx* c) {
    HWND lb = Ctl(c, ID_SETLIST);
    SendMessageW(lb, LB_RESETCONTENT, 0, 0);
    for (const auto& s : c->cfg->sets) {
        std::wstring item = (s.enabled ? L"" : L"(off) ") + s.name +
                            L"  [" + std::to_wstring(s.items.size()) + L" itens]";
        SendMessageW(lb, LB_ADDSTRING, 0, (LPARAM)item.c_str());
    }
    if (c->curSet >= 0) SendMessageW(lb, LB_SETCURSEL, c->curSet, 0);
}

void RefreshItemList(CfgCtx* c) {
    HWND lb = Ctl(c, ID_ITEMLIST);
    SendMessageW(lb, LB_RESETCONTENT, 0, 0);
    BackupSet* s = CurSet(c);
    if (s) {
        for (const auto& it : s->items) {
            std::wstring line = (it.enabled ? L"" : L"(off) ") + it.name +
                                L"  \x2192 " + (it.subfolder.empty() ? L"(raiz)" : it.subfolder);
            SendMessageW(lb, LB_ADDSTRING, 0, (LPARAM)line.c_str());
        }
    }
    if (c->curItem >= 0) SendMessageW(lb, LB_SETCURSEL, c->curItem, 0);
}

// ---------- campos ----------
void LoadSetFields(CfgCtx* c) {
    BackupSet empty;
    BackupSet* s = CurSet(c);
    const BackupSet& v = s ? *s : empty;
    SetText(c, ID_S_NAME, v.name);
    SetText(c, ID_S_DEST, v.destination);
    SendMessageW(Ctl(c, ID_S_MODE), CB_SETCURSEL, (int)v.mode, 0);
    SetText(c, ID_S_STAGING, v.staging);
    SetText(c, ID_S_WAIT, v.waitForPath);
    SetText(c, ID_S_WAITSEC, std::to_wstring(v.waitTimeoutSec));
    SetCheck(c, ID_S_KEEP, v.keepStaging);
    SetCheck(c, ID_S_ENABLED, v.enabled);
}

bool SaveSetFields(CfgCtx* c) {
    BackupSet* s = CurSet(c);
    if (!s) return true;
    std::wstring name = Trim(GetText(c, ID_S_NAME));
    if (name.empty()) {
        MessageBoxW(c->hwnd, L"Informe um nome para o conjunto (ele vira o nome do arquivo .zip).",
                    L"Backup Maximus", MB_ICONWARNING);
        return false;
    }
    s->name = name;
    s->destination = Trim(GetText(c, ID_S_DEST));
    s->mode = (SetMode)SendMessageW(Ctl(c, ID_S_MODE), CB_GETCURSEL, 0, 0);
    s->staging = Trim(GetText(c, ID_S_STAGING));
    s->waitForPath = Trim(GetText(c, ID_S_WAIT));
    int ws = _wtoi(GetText(c, ID_S_WAITSEC).c_str());
    s->waitTimeoutSec = ws >= 0 ? ws : 300;
    s->keepStaging = GetCheck(c, ID_S_KEEP);
    s->enabled = GetCheck(c, ID_S_ENABLED);

    if (s->destination.empty()) {
        MessageBoxW(c->hwnd, L"Informe o destino do conjunto (onde o .zip sera gravado).",
                    L"Backup Maximus", MB_ICONWARNING);
        return false;
    }
    c->dirty = true;
    RefreshSetList(c);
    return true;
}

// Campos de conexao so fazem sentido para bancos: esmaeca quando for arquivo/pasta.
void UpdateItemFieldStates(CfgCtx* c) {
    int type = (int)SendMessageW(Ctl(c, ID_I_TYPE), CB_GETCURSEL, 0, 0);
    bool isDb = (type == (int)ItemType::Firebird || type == (int)ItemType::SqlServer ||
                 type == (int)ItemType::MySql);
    for (int id : { ID_I_HOST, ID_I_PORT, ID_I_USER, ID_I_PASS, ID_I_TOOL, ID_I_OUTNAME })
        EnableWindow(Ctl(c, id), isDb);
    EnableWindow(Ctl(c, ID_I_MIRROR), !isDb);

    // O rotulo de Origem muda de significado conforme o tipo.
    const wchar_t* srcHint =
        type == (int)ItemType::Firebird  ? L"Origem: alias ou caminho do .fdb (ex.: PDVEXPRESSO)" :
        type == (int)ItemType::SqlServer ? L"Origem: nome do banco no SQL Server" :
        type == (int)ItemType::MySql     ? L"Origem: nome do banco no MySQL" :
                                           L"Origem: arquivo ou pasta (aceita \\\\servidor\\pasta)";
    SetText(c, ID_FOOT, srcHint);
}

void LoadItemFields(CfgCtx* c) {
    BackupItem empty;
    BackupItem* it = CurItem(c);
    const BackupItem& v = it ? *it : empty;
    SetText(c, ID_I_NAME, v.name);
    SendMessageW(Ctl(c, ID_I_TYPE), CB_SETCURSEL, (int)v.type, 0);
    SetText(c, ID_I_SOURCE, v.source);
    SetText(c, ID_I_SUBFOLDER, v.subfolder);
    SetText(c, ID_I_OUTNAME, v.outputName);
    SetCheck(c, ID_I_MIRROR, v.mirror);
    SetText(c, ID_I_HOST, v.host);
    SetText(c, ID_I_PORT, v.port);
    SetText(c, ID_I_USER, v.user);
    SetText(c, ID_I_PASS, v.passEnc.empty() ? L"" : kPassSentinel);
    SetText(c, ID_I_TOOL, v.toolPath);
    SetCheck(c, ID_I_ENABLED, v.enabled);
    UpdateItemFieldStates(c);
}

bool SaveItemFields(CfgCtx* c) {
    BackupItem* it = CurItem(c);
    if (!it) return true;
    std::wstring name = Trim(GetText(c, ID_I_NAME));
    if (name.empty()) {
        MessageBoxW(c->hwnd, L"Informe um nome para o item.", L"Backup Maximus", MB_ICONWARNING);
        return false;
    }
    it->name = name;
    it->type = (ItemType)SendMessageW(Ctl(c, ID_I_TYPE), CB_GETCURSEL, 0, 0);
    it->source = Trim(GetText(c, ID_I_SOURCE));
    // Normaliza a subpasta: sem barra no inicio/fim.
    std::wstring sub = Trim(GetText(c, ID_I_SUBFOLDER));
    while (!sub.empty() && (sub.front() == L'\\' || sub.front() == L'/')) sub.erase(0, 1);
    while (!sub.empty() && (sub.back()  == L'\\' || sub.back()  == L'/')) sub.pop_back();
    it->subfolder = sub;
    it->outputName = Trim(GetText(c, ID_I_OUTNAME));
    it->mirror = GetCheck(c, ID_I_MIRROR);
    it->host = Trim(GetText(c, ID_I_HOST));
    it->port = Trim(GetText(c, ID_I_PORT));
    it->user = Trim(GetText(c, ID_I_USER));
    std::wstring pass = GetText(c, ID_I_PASS);
    if (pass != kPassSentinel) it->passEnc = ProtectSecret(pass);
    it->toolPath = Trim(GetText(c, ID_I_TOOL));
    it->enabled = GetCheck(c, ID_I_ENABLED);

    if (it->source.empty()) {
        MessageBoxW(c->hwnd, L"Informe a origem do item.", L"Backup Maximus", MB_ICONWARNING);
        return false;
    }
    c->dirty = true;
    RefreshItemList(c);
    RefreshSetList(c);
    return true;
}

void RefreshNetList(CfgCtx* c) {
    HWND lb = Ctl(c, ID_N_LIST);
    SendMessageW(lb, LB_RESETCONTENT, 0, 0);
    for (const auto& n : c->cfg->netCreds)
        SendMessageW(lb, LB_ADDSTRING, 0, (LPARAM)(n.uncRoot + L"  (" + n.user + L")").c_str());
}

void LoadGeneralFields(CfgCtx* c) {
    Config& g = *c->cfg;
    SetText(c, ID_C_COMPANY, g.companyName);
    SetText(c, ID_C_EMAIL, g.notifyEmail);
    SetText(c, ID_C_TIMEOUT, std::to_wstring(g.alertTimeoutHours));
    SetCheck(c, ID_C_SENDMAIL, g.sendReportEmail);
    SetText(c, ID_C_SMTPHOST, g.smtp.host);
    SetText(c, ID_C_SMTPPORT, std::to_wstring(g.smtp.port));
    SetCheck(c, ID_C_SMTPSSL, g.smtp.useSsl);
    SetText(c, ID_C_SMTPUSER, g.smtp.user);
    SetText(c, ID_C_SMTPPASS, g.smtp.passEnc.empty() ? L"" : kPassSentinel);
    SetText(c, ID_C_SMTPFROM, g.smtp.from);
    SetText(c, ID_C_7ZPATH, g.sevenZipPath);
}

void SaveGeneralFields(CfgCtx* c) {
    Config& g = *c->cfg;
    g.companyName = Trim(GetText(c, ID_C_COMPANY));
    g.notifyEmail = Trim(GetText(c, ID_C_EMAIL));
    int t = _wtoi(GetText(c, ID_C_TIMEOUT).c_str());
    g.alertTimeoutHours = t > 0 ? t : 26;
    g.sendReportEmail = GetCheck(c, ID_C_SENDMAIL);
    g.smtp.host = Trim(GetText(c, ID_C_SMTPHOST));
    int p = _wtoi(GetText(c, ID_C_SMTPPORT).c_str());
    g.smtp.port = p > 0 ? p : 587;
    g.smtp.useSsl = GetCheck(c, ID_C_SMTPSSL);
    g.smtp.user = Trim(GetText(c, ID_C_SMTPUSER));
    std::wstring pass = GetText(c, ID_C_SMTPPASS);
    if (pass != kPassSentinel) g.smtp.passEnc = ProtectSecret(pass);
    g.smtp.from = Trim(GetText(c, ID_C_SMTPFROM));
    g.sevenZipPath = Trim(GetText(c, ID_C_7ZPATH));
    c->dirty = true;
}

void ShowPage(CfgCtx* c, int page) {
    auto setVis = [](std::vector<HWND>& v, bool show) {
        for (HWND h : v) ShowWindow(h, show ? SW_SHOW : SW_HIDE);
    };
    setVis(c->page0, page == 0);
    setVis(c->page1, page == 1);
    setVis(c->page2, page == 2);
}

// ---------- construcao da UI ----------
void BuildUi(CfgCtx* c) {
    c->font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
    LOGFONTW lf{};
    GetObjectW(c->font, sizeof(lf), &lf);
    lf.lfWeight = FW_BOLD;
    c->fontBold = CreateFontIndirectW(&lf);

    c->hTab = CreateWindowW(WC_TABCONTROLW, L"", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS,
                            8, 8, 890, 560, c->hwnd, (HMENU)ID_TAB, c->hInst, nullptr);
    SendMessageW(c->hTab, WM_SETFONT, (WPARAM)c->font, TRUE);
    TCITEMW ti{ TCIF_TEXT };
    wchar_t t0[] = L"Backups";       ti.pszText = t0; TabCtrl_InsertItem(c->hTab, 0, &ti);
    wchar_t t1[] = L"Configuracoes"; ti.pszText = t1; TabCtrl_InsertItem(c->hTab, 1, &ti);
    wchar_t t2[] = L"Rede";          ti.pszText = t2; TabCtrl_InsertItem(c->hTab, 2, &ti);

    const int X0 = 20, Y0 = 42;

    // ---------- aba 0: Backups ----------
    {
        auto* P = &c->page0;
        // coluna esquerda: conjuntos + itens
        Label(c, L"Conjuntos  (cada um gera 1 arquivo .zip)", X0, Y0, 250, P, true);
        Make(c, L"LISTBOX", L"", WS_BORDER | WS_TABSTOP | WS_VSCROLL | LBS_NOTIFY,
             X0, Y0 + 18, 262, 116, ID_SETLIST, P);
        Make(c, L"BUTTON", L"+ Conjunto", WS_TABSTOP, X0, Y0 + 138, 128, 24, ID_SET_NEW, P);
        Make(c, L"BUTTON", L"Excluir", WS_TABSTOP, X0 + 134, Y0 + 138, 128, 24, ID_SET_DEL, P);

        Label(c, L"Itens do conjunto  (cada um vai para sua subpasta)", X0, Y0 + 172, 262, P, true);
        Make(c, L"LISTBOX", L"", WS_BORDER | WS_TABSTOP | WS_VSCROLL | LBS_NOTIFY,
             X0, Y0 + 190, 262, 180, ID_ITEMLIST, P);
        Make(c, L"BUTTON", L"+ Item", WS_TABSTOP, X0, Y0 + 374, 84, 24, ID_ITEM_NEW, P);
        Make(c, L"BUTTON", L"Excluir", WS_TABSTOP, X0 + 89, Y0 + 374, 84, 24, ID_ITEM_DEL, P);
        Make(c, L"BUTTON", L"\x2191", WS_TABSTOP, X0 + 178, Y0 + 374, 40, 24, ID_ITEM_UP, P);
        Make(c, L"BUTTON", L"\x2193", WS_TABSTOP, X0 + 222, Y0 + 374, 40, 24, ID_ITEM_DOWN, P);
        Make(c, L"BUTTON", L"\x25B6 Executar backup agora", WS_TABSTOP | BS_DEFPUSHBUTTON,
             X0, Y0 + 406, 262, 30, ID_RUN_NOW, P);

        // coluna direita: dados do conjunto
        int fx = X0 + 285, lw = 118, ex = fx + lw + 6, ew = 300, y = Y0;
        Label(c, L"DADOS DO CONJUNTO", fx, y, 300, P, true);
        y += 22;
        auto rowS = [&](const wchar_t* lbl, int id, int w, DWORD extra = 0) {
            Label(c, lbl, fx, y + 3, lw, P);
            EditBox(c, id, ex, y, w, P, extra);
            y += 26;
        };
        rowS(L"Nome (do zip):", ID_S_NAME, ew);
        rowS(L"Destino do zip:", ID_S_DEST, ew);

        Label(c, L"Modo:", fx, y + 3, lw, P);
        HWND cbMode = Make(c, L"COMBOBOX", L"", WS_TABSTOP | CBS_DROPDOWNLIST | WS_VSCROLL,
                           ex, y, 150, 200, ID_S_MODE, P);
        SendMessageW(cbMode, CB_ADDSTRING, 0, (LPARAM)L"Incremental (1 zip fixo)");
        SendMessageW(cbMode, CB_ADDSTRING, 0, (LPARAM)L"Completo (zip por execucao)");
        y += 26;

        rowS(L"Pasta de montagem:", ID_S_STAGING, ew);
        Label(c, L"Vazio = <pasta do exe>\\staging\\<nome>. Ex. do .bat antigo: C:\\BACKUP",
              ex, y - 4, 320, P);
        y += 16;

        Label(c, L"Aguardar unidade:", fx, y + 3, lw, P);
        EditBox(c, ID_S_WAIT, ex, y, 90, P);
        Label(c, L"por ate", ex + 96, y + 3, 44, P);
        EditBox(c, ID_S_WAITSEC, ex + 142, y, 54, P, ES_NUMBER);
        Label(c, L"seg", ex + 200, y + 3, 30, P);
        y += 24;
        Label(c, L"Ex.: U:\\ para esperar o pen drive. Vazio = nao espera. 0 seg = espera sem limite.",
              ex, y, 340, P);
        y += 20;

        Make(c, L"BUTTON", L"Manter a pasta de montagem entre execucoes (mais rapido)",
             WS_TABSTOP | BS_AUTOCHECKBOX, ex, y, 360, 18, ID_S_KEEP, P);
        y += 22;
        Make(c, L"BUTTON", L"Conjunto habilitado", WS_TABSTOP | BS_AUTOCHECKBOX,
             ex, y, 200, 18, ID_S_ENABLED, P);
        Make(c, L"BUTTON", L"Salvar conjunto", WS_TABSTOP, ex + 210, y - 4, 130, 26, ID_SET_SAVE, P);
        y += 30;

        // separador
        Make(c, L"STATIC", L"", SS_ETCHEDHORZ, fx, y, 500, 2, 0, P);
        y += 12;

        // dados do item
        Label(c, L"DADOS DO ITEM SELECIONADO", fx, y, 300, P, true);
        y += 22;
        auto rowI = [&](const wchar_t* lbl, int id, int w, DWORD extra = 0) {
            Label(c, lbl, fx, y + 3, lw, P);
            EditBox(c, id, ex, y, w, P, extra);
            y += 26;
        };
        rowI(L"Nome:", ID_I_NAME, ew);

        Label(c, L"Tipo:", fx, y + 3, lw, P);
        HWND cbType = Make(c, L"COMBOBOX", L"", WS_TABSTOP | CBS_DROPDOWNLIST | WS_VSCROLL,
                           ex, y, 170, 220, ID_I_TYPE, P);
        for (auto s : { L"Firebird", L"SQL Server", L"MySQL", L"DBF", L"Arquivo/Pasta" })
            SendMessageW(cbType, CB_ADDSTRING, 0, (LPARAM)s);
        Make(c, L"BUTTON", L"Espelhar (/MIR)", WS_TABSTOP | BS_AUTOCHECKBOX,
             ex + 180, y + 2, 130, 18, ID_I_MIRROR, P);
        y += 26;

        rowI(L"Origem:", ID_I_SOURCE, ew);
        rowI(L"Subpasta no zip:", ID_I_SUBFOLDER, ew);
        Label(c, L"Ex.: PDVEXPRESSO\\Arquivos\\XmlDestinatario   (vazio = raiz)", ex, y - 4, 340, P);
        y += 16;
        rowI(L"Arquivo gerado:", ID_I_OUTNAME, ew);

        Label(c, L"Servidor / porta:", fx, y + 3, lw, P);
        EditBox(c, ID_I_HOST, ex, y, 200, P);
        EditBox(c, ID_I_PORT, ex + 206, y, 94, P);
        y += 26;
        Label(c, L"Usuario / senha:", fx, y + 3, lw, P);
        EditBox(c, ID_I_USER, ex, y, 145, P);
        EditBox(c, ID_I_PASS, ex + 151, y, 149, P, ES_PASSWORD);
        y += 26;
        rowI(L"Ferramenta:", ID_I_TOOL, ew);

        Make(c, L"BUTTON", L"Item habilitado", WS_TABSTOP | BS_AUTOCHECKBOX,
             ex, y, 150, 18, ID_I_ENABLED, P);
        Make(c, L"BUTTON", L"Salvar item", WS_TABSTOP | BS_DEFPUSHBUTTON,
             ex + 160, y - 4, 140, 26, ID_ITEM_SAVE, P);
        y += 28;
        Make(c, L"STATIC", L"", 0, fx, y, 500, 16, ID_FOOT, P);
    }

    // ---------- aba 1: Configuracoes ----------
    {
        auto* P = &c->page1;
        int lw = 200, ex = X0 + lw + 6, ew = 300, y = Y0;
        auto row = [&](const wchar_t* lbl, int id, DWORD extra = 0, int w = 0) {
            Label(c, lbl, X0, y + 3, lw, P);
            EditBox(c, id, ex, y, w ? w : ew, P, extra);
            y += 28;
        };
        Label(c, L"IDENTIFICACAO E ALERTAS", X0, y, 300, P, true);
        y += 22;
        row(L"Nome da empresa:", ID_C_COMPANY);
        row(L"Email para notificacoes:", ID_C_EMAIL);
        row(L"Alertar se sem backup ha (horas):", ID_C_TIMEOUT, ES_NUMBER, 70);
        Make(c, L"BUTTON", L"Enviar relatorio por email a cada backup",
             WS_TABSTOP | BS_AUTOCHECKBOX, ex, y, 340, 18, ID_C_SENDMAIL, P);
        y += 34;

        Label(c, L"SERVIDOR SMTP (relatorios e alertas)", X0, y, 340, P, true);
        y += 22;
        row(L"Servidor SMTP:", ID_C_SMTPHOST);
        row(L"Porta:", ID_C_SMTPPORT, ES_NUMBER, 70);
        Make(c, L"BUTTON", L"Usar SSL/TLS", WS_TABSTOP | BS_AUTOCHECKBOX,
             ex, y, 200, 18, ID_C_SMTPSSL, P);
        y += 28;
        row(L"Usuario SMTP:", ID_C_SMTPUSER);
        row(L"Senha SMTP:", ID_C_SMTPPASS, ES_PASSWORD);
        row(L"Remetente (De):", ID_C_SMTPFROM);
        y += 8;

        Label(c, L"COMPACTACAO", X0, y, 300, P, true);
        y += 22;
        row(L"Caminho do 7z.exe (opcional):", ID_C_7ZPATH);
        Label(c, L"Sem 7-Zip a aplicacao usa o Compress-Archive do PowerShell (mais lento).",
              ex, y - 6, 400, P);
        y += 20;

        Make(c, L"BUTTON", L"Testar email", WS_TABSTOP, X0, y, 130, 27, ID_C_TESTMAIL, P);
        Make(c, L"BUTTON", L"Alterar senha da UI", WS_TABSTOP, X0 + 140, y, 160, 27, ID_C_CHPASS, P);
        Make(c, L"BUTTON", L"Criar atalho na area de trabalho", WS_TABSTOP,
             X0 + 310, y, 250, 27, ID_C_SHORTCUT, P);
    }

    // ---------- aba 2: Rede ----------
    {
        auto* P = &c->page2;
        Label(c, L"Credenciais para compartilhamentos de rede (UNC)", X0, Y0, 400, P, true);
        Make(c, L"LISTBOX", L"", WS_BORDER | WS_TABSTOP | WS_VSCROLL | LBS_NOTIFY,
             X0, Y0 + 22, 340, 240, ID_N_LIST, P);
        int fx = X0 + 360, lw = 140, ex = fx + lw + 6, ew = 210, y = Y0 + 22;
        Label(c, L"Compartilhamento:", fx, y + 3, lw, P);
        EditBox(c, ID_N_UNC, ex, y, ew, P); y += 28;
        Label(c, L"Usuario (DOM\\user):", fx, y + 3, lw, P);
        EditBox(c, ID_N_USER, ex, y, ew, P); y += 28;
        Label(c, L"Senha:", fx, y + 3, lw, P);
        EditBox(c, ID_N_PASS, ex, y, ew, P, ES_PASSWORD); y += 34;
        Make(c, L"BUTTON", L"Adicionar", WS_TABSTOP, fx, y, 120, 26, ID_N_ADD, P);
        Make(c, L"BUTTON", L"Remover selecionada", WS_TABSTOP, fx + 130, y, 180, 26, ID_N_DEL, P);
        Label(c, L"Ex.: \\\\servidor\\backups \x2014 usada automaticamente quando a origem de um item "
                 L"ou o destino de um conjunto estiver nesse compartilhamento.",
              X0, Y0 + 280, 700, P);
    }

    // rodape fixo
    Make(c, L"BUTTON", L"Salvar tudo", WS_VISIBLE | WS_TABSTOP,
         600, 576, 140, 30, ID_SAVEALL, nullptr);
    Make(c, L"BUTTON", L"Fechar", WS_VISIBLE | WS_TABSTOP, 750, 576, 130, 30, ID_CLOSE, nullptr);
}

bool SaveAll(CfgCtx* c) {
    if (!SaveSetFields(c)) return false;
    if (!SaveItemFields(c)) return false;
    SaveGeneralFields(c);
    if (!c->cfg->Save(c->cfgPath)) {
        MessageBoxW(c->hwnd, L"Falha ao gravar o arquivo de configuracao.",
                    L"Backup Maximus", MB_ICONERROR);
        return false;
    }
    c->dirty = false;
    Logger::Info(L"Configuracoes salvas.");
    return true;
}

LRESULT CALLBACK CfgProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    CfgCtx* c = (CfgCtx*)GetWindowLongPtrW(hwnd, GWLP_USERDATA);
    switch (msg) {
    case WM_CREATE: {
        c = (CfgCtx*)((CREATESTRUCTW*)lp)->lpCreateParams;
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, (LONG_PTR)c);
        c->hwnd = hwnd;
        BuildUi(c);
        if (!c->cfg->sets.empty()) {
            c->curSet = 0;
            if (!c->cfg->sets[0].items.empty()) c->curItem = 0;
        }
        RefreshSetList(c);
        RefreshItemList(c);
        LoadSetFields(c);
        LoadItemFields(c);
        LoadGeneralFields(c);
        RefreshNetList(c);
        ShowPage(c, 0);
        return 0;
    }
    case WM_NOTIFY: {
        NMHDR* nm = (NMHDR*)lp;
        if (nm->idFrom == ID_TAB && nm->code == TCN_SELCHANGE && c)
            ShowPage(c, TabCtrl_GetCurSel(c->hTab));
        return 0;
    }
    case WM_COMMAND: {
        if (!c) return 0;
        int id = LOWORD(wp), code = HIWORD(wp);
        switch (id) {

        case ID_SETLIST:
            if (code == LBN_SELCHANGE) {
                int sel = (int)SendMessageW(Ctl(c, ID_SETLIST), LB_GETCURSEL, 0, 0);
                if (sel != LB_ERR && sel != c->curSet) {
                    c->curSet = sel;
                    c->curItem = c->cfg->sets[sel].items.empty() ? -1 : 0;
                    LoadSetFields(c);
                    RefreshItemList(c);
                    LoadItemFields(c);
                }
            }
            break;

        case ID_ITEMLIST:
            if (code == LBN_SELCHANGE) {
                int sel = (int)SendMessageW(Ctl(c, ID_ITEMLIST), LB_GETCURSEL, 0, 0);
                if (sel != LB_ERR && sel != c->curItem) {
                    c->curItem = sel;
                    LoadItemFields(c);
                }
            }
            break;

        case ID_I_TYPE:
            if (code == CBN_SELCHANGE) UpdateItemFieldStates(c);
            break;

        case ID_SET_NEW: {
            BackupSet s;
            s.name = c->cfg->sets.empty() ? L"BKP_MAXIMUS"
                                          : L"CONJUNTO_" + std::to_wstring(c->cfg->sets.size() + 1);
            c->cfg->sets.push_back(s);
            c->curSet = (int)c->cfg->sets.size() - 1;
            c->curItem = -1;
            c->dirty = true;
            RefreshSetList(c);
            RefreshItemList(c);
            LoadSetFields(c);
            LoadItemFields(c);
            SetFocus(Ctl(c, ID_S_NAME));
            break;
        }
        case ID_SET_DEL:
            if (BackupSet* s = CurSet(c)) {
                std::wstring q = L"Excluir o conjunto '" + s->name + L"' e seus " +
                                 std::to_wstring(s->items.size()) + L" itens?";
                if (MessageBoxW(hwnd, q.c_str(), L"Backup Maximus",
                                MB_YESNO | MB_ICONQUESTION) == IDYES) {
                    c->cfg->sets.erase(c->cfg->sets.begin() + c->curSet);
                    c->curSet = c->cfg->sets.empty() ? -1 : 0;
                    c->curItem = (c->curSet >= 0 && !c->cfg->sets[0].items.empty()) ? 0 : -1;
                    c->dirty = true;
                    RefreshSetList(c);
                    RefreshItemList(c);
                    LoadSetFields(c);
                    LoadItemFields(c);
                }
            }
            break;
        case ID_SET_SAVE:
            if (SaveSetFields(c)) SaveAll(c);
            break;

        case ID_ITEM_NEW: {
            BackupSet* s = CurSet(c);
            if (!s) {
                MessageBoxW(hwnd, L"Crie um conjunto antes de adicionar itens.",
                            L"Backup Maximus", MB_ICONINFORMATION);
                break;
            }
            BackupItem it;
            it.name = L"item_" + std::to_wstring(s->items.size() + 1);
            s->items.push_back(it);
            c->curItem = (int)s->items.size() - 1;
            c->dirty = true;
            RefreshItemList(c);
            RefreshSetList(c);
            LoadItemFields(c);
            SetFocus(Ctl(c, ID_I_NAME));
            break;
        }
        case ID_ITEM_DEL: {
            BackupSet* s = CurSet(c);
            BackupItem* it = CurItem(c);
            if (s && it) {
                std::wstring q = L"Excluir o item '" + it->name + L"'?";
                if (MessageBoxW(hwnd, q.c_str(), L"Backup Maximus",
                                MB_YESNO | MB_ICONQUESTION) == IDYES) {
                    s->items.erase(s->items.begin() + c->curItem);
                    c->curItem = s->items.empty() ? -1 : 0;
                    c->dirty = true;
                    RefreshItemList(c);
                    RefreshSetList(c);
                    LoadItemFields(c);
                }
            }
            break;
        }
        case ID_ITEM_UP:
        case ID_ITEM_DOWN: {
            BackupSet* s = CurSet(c);
            if (!s || c->curItem < 0) break;
            int to = c->curItem + (id == ID_ITEM_UP ? -1 : 1);
            if (to < 0 || to >= (int)s->items.size()) break;
            if (!SaveItemFields(c)) break;
            std::swap(s->items[c->curItem], s->items[to]);
            c->curItem = to;
            c->dirty = true;
            RefreshItemList(c);
            LoadItemFields(c);
            break;
        }
        case ID_ITEM_SAVE:
            if (SaveItemFields(c)) SaveAll(c);
            break;

        case ID_RUN_NOW:
            if (SaveAll(c)) {
                wchar_t exe[MAX_PATH];
                GetModuleFileNameW(nullptr, exe, MAX_PATH);
                std::wstring cmd = QuoteArg(exe) + L" /run";
                STARTUPINFOW si{}; si.cb = sizeof(si);
                PROCESS_INFORMATION pi{};
                std::wstring mcmd = cmd;
                if (CreateProcessW(nullptr, &mcmd[0], nullptr, nullptr, FALSE, 0,
                                   nullptr, nullptr, &si, &pi)) {
                    CloseHandle(pi.hProcess);
                    CloseHandle(pi.hThread);
                }
            }
            break;

        case ID_N_ADD: {
            NetCredential n;
            n.uncRoot = Trim(GetText(c, ID_N_UNC));
            n.user = Trim(GetText(c, ID_N_USER));
            if (n.uncRoot.empty() || !StartsWith(n.uncRoot, L"\\\\")) {
                MessageBoxW(hwnd, L"Informe o compartilhamento no formato \\\\servidor\\pasta.",
                            L"Backup Maximus", MB_ICONWARNING);
                break;
            }
            n.passEnc = ProtectSecret(GetText(c, ID_N_PASS));
            c->cfg->netCreds.push_back(n);
            c->dirty = true;
            SetText(c, ID_N_UNC, L""); SetText(c, ID_N_USER, L""); SetText(c, ID_N_PASS, L"");
            RefreshNetList(c);
            break;
        }
        case ID_N_DEL: {
            int sel = (int)SendMessageW(Ctl(c, ID_N_LIST), LB_GETCURSEL, 0, 0);
            if (sel != LB_ERR) {
                c->cfg->netCreds.erase(c->cfg->netCreds.begin() + sel);
                c->dirty = true;
                RefreshNetList(c);
            }
            break;
        }

        case ID_C_TESTMAIL: {
            SaveGeneralFields(c);
            std::wstring err;
            HCURSOR old = SetCursor(LoadCursorW(nullptr, IDC_WAIT));
            bool ok = SendEmail(c->cfg->smtp, c->cfg->notifyEmail,
                                L"[Backup Maximus] Teste de email",
                                L"Este e um email de teste do Backup Maximus.\nEmpresa: " +
                                c->cfg->companyName, L"", err);
            SetCursor(old);
            MessageBoxW(hwnd, ok ? L"Email de teste enviado com sucesso!"
                                 : (L"Falha no envio:\n" + err).c_str(),
                        L"Backup Maximus", ok ? MB_ICONINFORMATION : MB_ICONERROR);
            break;
        }
        case ID_C_CHPASS:
            if (PasswordGate(c->hInst, *c->cfg, true)) {
                c->dirty = true;
                if (SaveAll(c))
                    MessageBoxW(hwnd, L"Senha alterada.", L"Backup Maximus", MB_ICONINFORMATION);
            }
            break;
        case ID_C_SHORTCUT: {
            std::wstring err;
            if (CreateDesktopShortcut(err))
                MessageBoxW(hwnd, L"Atalho 'Backup Maximus - Executar' criado na area de trabalho.",
                            L"Backup Maximus", MB_ICONINFORMATION);
            else
                MessageBoxW(hwnd, err.c_str(), L"Backup Maximus", MB_ICONERROR);
            break;
        }

        case ID_SAVEALL:
            if (SaveAll(c))
                MessageBoxW(hwnd, L"Configuracoes salvas.", L"Backup Maximus", MB_ICONINFORMATION);
            break;
        case ID_CLOSE:
            SendMessageW(hwnd, WM_CLOSE, 0, 0);
            break;
        }
        return 0;
    }
    case WM_CLOSE:
        if (c && c->dirty) {
            int r = MessageBoxW(hwnd, L"Ha alteracoes nao salvas. Salvar antes de sair?",
                                L"Backup Maximus", MB_YESNOCANCEL | MB_ICONQUESTION);
            if (r == IDCANCEL) return 0;
            if (r == IDYES && !SaveAll(c)) return 0;
        }
        DestroyWindow(hwnd);
        return 0;
    case WM_DESTROY:
        if (c && c->fontBold) DeleteObject(c->fontBold);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

} // namespace

int ShowConfigWindow(HINSTANCE hInst, Config& cfg, const std::wstring& cfgPath) {
    INITCOMMONCONTROLSEX icc{ sizeof(icc), ICC_TAB_CLASSES | ICC_STANDARD_CLASSES };
    InitCommonControlsEx(&icc);

    CfgCtx ctx;
    ctx.cfg = &cfg;
    ctx.cfgPath = cfgPath;
    ctx.hInst = hInst;

    WNDCLASSW wc{};
    wc.lpfnWndProc = CfgProc;
    wc.hInstance = hInst;
    wc.lpszClassName = L"BackupMaximusConfig";
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.hIcon = LoadIconW(nullptr, IDI_APPLICATION);
    RegisterClassW(&wc);

    int sw = GetSystemMetrics(SM_CXSCREEN), sh = GetSystemMetrics(SM_CYSCREEN);
    int w = 922, h = 655;
    HWND hwnd = CreateWindowW(wc.lpszClassName, L"Backup Maximus - Configuracoes",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        (sw - w) / 2, (sh - h) / 2, w, h, nullptr, nullptr, hInst, &ctx);
    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessageW(&msg, nullptr, 0, 0) > 0) {
        if (!IsDialogMessageW(hwnd, &msg)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }
    return 0;
}

} // namespace bm
