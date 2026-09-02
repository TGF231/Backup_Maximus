// Backup Maximus - ui_progress.cpp
// Janela do "Quick Run": executa o backup numa thread de trabalho e mostra
// barra de progresso, status e tempo. Durante a espera por pen drive o botao
// Cancelar fica ativo (so nessa fase — no meio do backup nao da para abortar).
#include "ui.h"
#include "engine.h"
#include "logger.h"
#include <commctrl.h>
#include <thread>
#include <atomic>

#pragma comment(lib, "comctl32.lib")

namespace bm {

namespace {

constexpr UINT WM_BM_PROGRESS = WM_APP + 1;   // wParam=pct, lParam=wchar_t* (heap)
constexpr UINT WM_BM_DONE     = WM_APP + 2;   // wParam=allOk
constexpr UINT WM_BM_WAITING  = WM_APP + 3;   // wParam=1 esperando unidade, 0 nao

struct ProgressCtx {
    Config* cfg = nullptr;
    std::wstring cfgPath;
    HWND hBar = nullptr, hStatus = nullptr, hTime = nullptr, hClose = nullptr, hCancel = nullptr;
    ULONGLONG t0 = 0;
    bool done = false;
    bool allOk = false;
    bool waiting = false;
    int exitCode = 1;
    std::atomic<bool> cancelRequested{ false };
};

void Layout(ProgressCtx* ctx, HWND hwnd) {
    RECT rc; GetClientRect(hwnd, &rc);
    int w = rc.right, pad = 16;
    MoveWindow(ctx->hStatus, pad, 14, w - 2 * pad, 40, TRUE);
    MoveWindow(ctx->hBar,    pad, 60, w - 2 * pad, 24, TRUE);
    MoveWindow(ctx->hTime,   pad, 94, w - 2 * pad - 230, 20, TRUE);
    MoveWindow(ctx->hCancel, w - pad - 210, 90, 100, 28, TRUE);
    MoveWindow(ctx->hClose,  w - pad - 100, 90, 100, 28, TRUE);
}

LRESULT CALLBACK ProgressWndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    ProgressCtx* ctx = (ProgressCtx*)GetWindowLongPtrW(hwnd, GWLP_USERDATA);
    switch (msg) {
    case WM_CREATE: {
        ctx = (ProgressCtx*)((CREATESTRUCTW*)lp)->lpCreateParams;
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, (LONG_PTR)ctx);
        HINSTANCE hi = ((CREATESTRUCTW*)lp)->hInstance;

        ctx->hStatus = CreateWindowW(L"STATIC", L"Iniciando backup...",
            WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwnd, nullptr, hi, nullptr);
        ctx->hBar = CreateWindowW(PROGRESS_CLASSW, nullptr,
            WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwnd, nullptr, hi, nullptr);
        SendMessageW(ctx->hBar, PBM_SETRANGE32, 0, 100);
        ctx->hTime = CreateWindowW(L"STATIC", L"Tempo: 0 s",
            WS_CHILD | WS_VISIBLE, 0, 0, 0, 0, hwnd, nullptr, hi, nullptr);
        ctx->hCancel = CreateWindowW(L"BUTTON", L"Cancelar",
            WS_CHILD, 0, 0, 0, 0, hwnd, (HMENU)2, hi, nullptr);
        ctx->hClose = CreateWindowW(L"BUTTON", L"Fechar",
            WS_CHILD, 0, 0, 0, 0, hwnd, (HMENU)1, hi, nullptr);

        HFONT font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        for (HWND h : { ctx->hStatus, ctx->hTime, ctx->hClose, ctx->hCancel })
            SendMessageW(h, WM_SETFONT, (WPARAM)font, TRUE);

        Layout(ctx, hwnd);
        SetTimer(hwnd, 1, 500, nullptr);
        ctx->t0 = GetTickCount64();

        HWND target = hwnd;
        Config* cfg = ctx->cfg;
        std::wstring cfgPath = ctx->cfgPath;
        ProgressCtx* c = ctx;
        std::thread([target, cfg, cfgPath, c]() {
            RunResult r = RunBackups(*cfg, cfgPath,
                [target, c](Phase ph, int pct, const std::wstring& m) -> bool {
                    PostMessageW(target, WM_BM_WAITING, ph == Phase::WaitingDrive ? 1 : 0, 0);
                    PostMessageW(target, WM_BM_PROGRESS, pct, (LPARAM)_wcsdup(m.c_str()));
                    return !c->cancelRequested.load();
                });
            PostMessageW(target, WM_BM_DONE, r.allOk ? 1 : 0, 0);
        }).detach();
        return 0;
    }
    case WM_SIZE:
        if (ctx) Layout(ctx, hwnd);
        return 0;

    case WM_TIMER:
        if (ctx && !ctx->done) {
            ULONGLONG s = (GetTickCount64() - ctx->t0) / 1000;
            SetWindowTextW(ctx->hTime, (L"Tempo: " + std::to_wstring(s) + L" s").c_str());
        }
        return 0;

    case WM_BM_WAITING:
        if (ctx && !ctx->done) {
            bool w = (wp != 0);
            if (w != ctx->waiting) {
                ctx->waiting = w;
                ShowWindow(ctx->hCancel, w ? SW_SHOW : SW_HIDE);
                // Barra em modo indeterminado ("marquee") enquanto espera a unidade.
                LONG_PTR st = GetWindowLongPtrW(ctx->hBar, GWL_STYLE);
                if (w) {
                    SetWindowLongPtrW(ctx->hBar, GWL_STYLE, st | PBS_MARQUEE);
                    SendMessageW(ctx->hBar, PBM_SETMARQUEE, TRUE, 40);
                    SetWindowTextW(hwnd, L"Backup Maximus - Aguardando unidade de backup");
                } else {
                    SendMessageW(ctx->hBar, PBM_SETMARQUEE, FALSE, 0);
                    SetWindowLongPtrW(ctx->hBar, GWL_STYLE, st & ~PBS_MARQUEE);
                    SetWindowTextW(hwnd, L"Backup Maximus - Executando backup...");
                }
            }
        }
        return 0;

    case WM_BM_PROGRESS: {
        wchar_t* text = (wchar_t*)lp;
        if (ctx) {
            if (!ctx->waiting) SendMessageW(ctx->hBar, PBM_SETPOS, wp, 0);
            if (text) SetWindowTextW(ctx->hStatus, text);
        }
        free(text);
        return 0;
    }

    case WM_BM_DONE:
        if (ctx) {
            ctx->done = true;
            ctx->waiting = false;
            ctx->allOk = (wp != 0);
            ctx->exitCode = ctx->allOk ? 0 : 1;
            KillTimer(hwnd, 1);
            ShowWindow(ctx->hCancel, SW_HIDE);

            LONG_PTR st = GetWindowLongPtrW(ctx->hBar, GWL_STYLE);
            SendMessageW(ctx->hBar, PBM_SETMARQUEE, FALSE, 0);
            SetWindowLongPtrW(ctx->hBar, GWL_STYLE, st & ~PBS_MARQUEE);
            SendMessageW(ctx->hBar, PBM_SETPOS, 100, 0);

            ULONGLONG s = (GetTickCount64() - ctx->t0) / 1000;
            SetWindowTextW(ctx->hTime, (L"Concluido em " + std::to_wstring(s) + L" s").c_str());
            if (!ctx->allOk) {
                SendMessageW(ctx->hBar, PBM_SETSTATE, PBST_ERROR, 0);
                SetWindowTextW(hwnd, L"Backup Maximus - CONCLUIDO COM FALHAS");
            } else {
                SetWindowTextW(hwnd, L"Backup Maximus - SUCESSO");
            }
            ShowWindow(ctx->hClose, SW_SHOW);
            SetFocus(ctx->hClose);
            FlashWindow(hwnd, TRUE);
        }
        return 0;

    case WM_COMMAND:
        if (!ctx) return 0;
        if (LOWORD(wp) == 1 && ctx->done) DestroyWindow(hwnd);
        else if (LOWORD(wp) == 2 && ctx->waiting) {
            ctx->cancelRequested.store(true);
            SetWindowTextW(ctx->hStatus, L"Cancelando...");
            EnableWindow(ctx->hCancel, FALSE);
        }
        return 0;

    case WM_CLOSE:
        if (ctx && !ctx->done) {
            if (ctx->waiting) {
                ctx->cancelRequested.store(true);
                return 0;
            }
            MessageBoxW(hwnd, L"O backup ainda esta em execucao. Aguarde a conclusao.",
                        L"Backup Maximus", MB_ICONINFORMATION);
            return 0;
        }
        DestroyWindow(hwnd);
        return 0;

    case WM_DESTROY:
        PostQuitMessage(ctx ? ctx->exitCode : 1);
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

} // namespace

int ShowProgressRunner(HINSTANCE hInst, Config& cfg, const std::wstring& cfgPath) {
    INITCOMMONCONTROLSEX icc{ sizeof(icc), ICC_PROGRESS_CLASS };
    InitCommonControlsEx(&icc);

    ProgressCtx ctx;
    ctx.cfg = &cfg;
    ctx.cfgPath = cfgPath;

    WNDCLASSW wc{};
    wc.lpfnWndProc = ProgressWndProc;
    wc.hInstance = hInst;
    wc.lpszClassName = L"BackupMaximusProgress";
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.hIcon = LoadIconW(nullptr, IDI_APPLICATION);
    RegisterClassW(&wc);

    int sw = GetSystemMetrics(SM_CXSCREEN), sh = GetSystemMetrics(SM_CYSCREEN);
    int w = 520, h = 175;
    HWND hwnd = CreateWindowExW(WS_EX_TOPMOST, wc.lpszClassName,
        L"Backup Maximus - Executando backup...",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU,
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
    return (int)msg.wParam;
}

} // namespace bm
