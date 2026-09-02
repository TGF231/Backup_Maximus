// Backup Maximus - common.h
// Tipos e utilitarios compartilhados por todos os modulos.
#pragma once

#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include <windows.h>
#include <string>
#include <vector>
#include <cstdint>
#include <functional>

namespace bm {

// ---------- conversao UTF-8 <-> UTF-16 ----------
std::wstring Utf8ToWide(const std::string& s);
std::string  WideToUtf8(const std::wstring& w);

// ---------- strings ----------
std::wstring Trim(const std::wstring& s);
std::wstring ToLower(std::wstring s);
bool StartsWith(const std::wstring& s, const std::wstring& prefix);
std::vector<std::wstring> Split(const std::wstring& s, wchar_t sep);
std::wstring Join(const std::vector<std::wstring>& parts, const std::wstring& sep);
std::wstring ReplaceAll(std::wstring s, const std::wstring& from, const std::wstring& to);

// ---------- caminho / arquivos ----------
std::wstring ExeDir();                       // pasta do executavel
std::wstring PathJoin(const std::wstring& a, const std::wstring& b);
bool FileExists(const std::wstring& path);
bool DirExists(const std::wstring& path);
bool EnsureDir(const std::wstring& path);    // cria recursivamente
std::wstring TempFilePath(const std::wstring& prefix, const std::wstring& ext);

// ---------- tempo ----------
std::wstring NowTimestamp();                 // 2026-08-26_143000 (para nomes de arquivo)
std::wstring NowStampBR();                   // 26082026143000 (DDMMYYYYHHMMSS, como o -ag do WinRAR)
std::wstring NowIso();                       // 2026-08-26 14:30:00
int64_t NowUnix();                           // epoch em segundos

// ---------- unidades removiveis ----------
// Aguarda o caminho (ex.: "U:\\") ficar acessivel. Chama onWait(segundosDecorridos)
// a cada segundo para dar feedback; se onWait devolver false, cancela a espera.
// timeoutSec = 0 espera indefinidamente. Retorna true se o caminho ficou disponivel.
bool WaitForPath(const std::wstring& path, int timeoutSec,
                 const std::function<bool(int)>& onWait);

// Espaco livre em bytes no volume do caminho (0 se indeterminado).
uint64_t FreeSpaceBytes(const std::wstring& path);

// Formata bytes de forma legivel: "1,4 GB", "820 MB".
std::wstring FormatBytes(uint64_t bytes);

// ---------- processos ----------
// Executa um comando (linha completa), captura stdout+stderr combinados,
// retorna exit code (-1 em falha de criacao). Timeout em ms (0 = infinito).
int RunProcessCapture(const std::wstring& cmdLine, std::wstring& output,
                      DWORD timeoutMs = 0, const std::wstring& workDir = L"");

// Escapa um argumento para linha de comando do Windows.
std::wstring QuoteArg(const std::wstring& arg);

} // namespace bm
