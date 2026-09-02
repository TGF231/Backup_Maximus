// Backup Maximus - zip.h
// Compacta a arvore de montagem inteira em UM arquivo .zip, preservando a
// estrutura de pastas. Usa 7-Zip quando disponivel (controle real de nivel de
// compressao: -mx1 leve / -mx9 maxima); sem ele, recorre ao Compress-Archive
// do PowerShell, presente em todo Windows 10+.
#pragma once
#include "common.h"

namespace bm {

class Zipper {
public:
    explicit Zipper(const std::wstring& sevenZipHint);

    bool UsingSevenZip() const { return !m_7z.empty(); }
    std::wstring ToolDescription() const;

    // Compacta TODO o conteudo de treeDir em zipPath, mantendo a hierarquia.
    // A pasta raiz da arvore vira a pasta raiz dentro do zip.
    //   maxCompression=true  -> -mx9 (backup completo)
    //   maxCompression=false -> -mx1 (backup incremental, prioriza velocidade)
    //   update=true          -> atualiza o zip existente em vez de recria-lo
    bool ArchiveTree(const std::wstring& treeDir, const std::wstring& zipPath,
                     bool maxCompression, bool update, std::wstring& errOut);

    // Adiciona/substitui um unico arquivo na raiz do zip (config e relatorio).
    bool AddFile(const std::wstring& zipPath, const std::wstring& filePath,
                 std::wstring& errOut);

    // Extrai uma entrada (por nome de arquivo) do zip para destDir.
    bool ExtractFile(const std::wstring& zipPath, const std::wstring& entryName,
                     const std::wstring& destDir, std::wstring& errOut);

private:
    std::wstring m_7z;

    bool Run7z(const std::wstring& args, std::wstring& errOut);
    bool RunPs(const std::wstring& script, std::wstring& errOut);
};

} // namespace bm
