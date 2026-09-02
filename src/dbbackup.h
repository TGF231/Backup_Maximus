// Backup Maximus - dbbackup.h
// Dumps de banco usando as ferramentas nativas de cada SGBD:
//   Firebird  -> gbak -b -g
//   SQLServer -> sqlcmd + BACKUP DATABASE ... WITH COPY_ONLY
//   MySQL     -> mysqldump --single-transaction
// O dump e gravado diretamente na pasta de destino dentro da arvore de montagem.
#pragma once
#include "common.h"
#include "config.h"

namespace bm {

// Gera o dump do item em targetDir (ja criado). O nome do arquivo vem de
// item.outputName, ou <item.name>.<ext padrao do tipo> quando vazio.
// outFile recebe o caminho do arquivo gerado.
bool DumpDatabase(const BackupItem& item, const std::wstring& targetDir,
                  std::wstring& outFile, std::wstring& errOut);

// Localiza a ferramenta nativa do tipo (respeitando item.toolPath).
std::wstring FindDbTool(const BackupItem& item);

// Extensao padrao do dump por tipo: .fbk / .bak / .sql
std::wstring DefaultDumpExt(ItemType t);

} // namespace bm
