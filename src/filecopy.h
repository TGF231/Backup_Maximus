// Backup Maximus - filecopy.h
// Copia incremental para a arvore de montagem, com semantica equivalente ao
// ROBOCOPY /MIR: so recopia o que mudou (tamanho ou data de modificacao) e,
// quando espelhando, apaga do destino o que sumiu da origem.
#pragma once
#include "common.h"

namespace bm {

struct CopyStats {
    int filesCopied = 0;
    int filesSkipped = 0;      // ja identicos no destino
    int filesDeleted = 0;      // removidos por espelhamento
    int errors = 0;
    uint64_t bytesCopied = 0;
    std::wstring lastError;
};

// Copia srcDir (recursivo) para destDir. Se mirror=true, remove do destino
// arquivos e pastas que nao existem mais na origem.
bool MirrorDirectory(const std::wstring& srcDir, const std::wstring& destDir,
                     bool mirror, CopyStats& stats);

// Copia um unico arquivo para destDir (preservando o nome), pulando se identico.
bool CopyOneFile(const std::wstring& srcFile, const std::wstring& destDir, CopyStats& stats);

// Remove uma arvore de diretorios inteira.
bool RemoveTree(const std::wstring& dir);

// Soma o tamanho de todos os arquivos sob dir.
uint64_t DirectorySize(const std::wstring& dir);

} // namespace bm
