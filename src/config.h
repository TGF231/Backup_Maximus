// Backup Maximus - config.h
// Modelo de configuracao + persistencia em INI (UTF-8) + criptografia de segredos.
//
// MODELO: Conjunto -> Itens
//   Um CONJUNTO (BackupSet) produz exatamente UM arquivo .zip final.
//   Cada ITEM (BackupItem) coloca seu conteudo numa SUBPASTA dentro da arvore
//   de montagem (staging); ao final a arvore inteira vira um unico zip.
//
//   Exemplo equivalente ao BKP.bat:
//     Conjunto "BKP_MAXIMUS", staging "C:\BACKUP", destino "U:"
//       item firebird PDVEXPRESSO    -> subpasta "PDVEXPRESSO" (gera PDVEXPRESSO.FBK)
//       item arquivo  nfceConfig.ini -> subpasta "PDVEXPRESSO"
//       item pasta    XmlDestinatario-> subpasta "PDVEXPRESSO\Arquivos\XmlDestinatario"
//       item pasta    Log            -> subpasta "PDVEXPRESSO\Arquivos\Log"
//     Resultado: um unico U:\BKP_MAXIMUS26082026170000.zip com a arvore inteira.
//
// Segredos (senhas de banco, SMTP, rede) sao gravados cifrados com DPAPI
// (CryptProtectData) e codificados em Base64. A senha da interface de
// configuracao e gravada apenas como hash SHA-256 com salt.
#pragma once
#include "common.h"

namespace bm {

enum class ItemType { Firebird, SqlServer, MySql, Dbf, Files };
enum class SetMode  { Incremental, Full };

std::wstring ItemTypeName(ItemType t);
bool ParseItemType(const std::wstring& s, ItemType& out);
std::wstring SetModeName(SetMode m);
bool ParseSetMode(const std::wstring& s, SetMode& out);

// Um item que contribui com conteudo para o zip do conjunto.
struct BackupItem {
    std::wstring name;              // rotulo amigavel, exibido no progresso e no relatorio
    ItemType type = ItemType::Files;

    // Firebird : alias ou caminho do .fdb   | SqlServer/MySql : nome do banco
    // Dbf/Files: arquivo OU pasta (aceita UNC)
    std::wstring source;

    // Caminho relativo DENTRO da arvore/zip. Vazio = raiz da arvore.
    // Ex.: "PDVEXPRESSO\\Arquivos\\XmlDestinatario"
    std::wstring subfolder;

    // Nome do arquivo gerado pelo dump (bancos). Vazio = <name>.<ext padrao>.
    std::wstring outputName;

    // Somente para Dbf/Files com origem = pasta:
    // espelha a origem (remove do staging o que foi apagado na origem) — equivale a ROBOCOPY /MIR.
    bool mirror = true;

    // Conexao (bancos)
    std::wstring host;
    std::wstring port;
    std::wstring user;
    std::wstring passEnc;           // DPAPI+Base64
    std::wstring toolPath;          // gbak/sqlcmd/mysqldump (vazio = autodetectar)

    bool enabled = true;
};

// Um conjunto produz UM zip.
struct BackupSet {
    std::wstring name = L"BKP_MAXIMUS";   // vira o prefixo do nome do zip
    std::wstring staging;                 // arvore de montagem (ex.: C:\BACKUP). Vazio = <exeDir>\staging\<name>
    std::wstring destination;             // onde o zip final e gravado (ex.: U:\ ou \\srv\backups)
    SetMode mode = SetMode::Full;

    // Aguarda a unidade/pasta ficar disponivel antes de comecar (pen drive, HD externo).
    // Ex.: "U:\\". Vazio = nao aguarda.
    std::wstring waitForPath;
    int waitTimeoutSec = 300;             // 0 = espera indefinidamente

    // Mantem a arvore de montagem entre execucoes. Deixar ligado acelera muito
    // as execucoes seguintes (so o que mudou e recopiado).
    bool keepStaging = true;

    bool enabled = true;
    std::vector<BackupItem> items;
};

struct NetCredential {
    std::wstring uncRoot;           // \\servidor\compartilhamento
    std::wstring user;              // DOMINIO\usuario
    std::wstring passEnc;
};

struct SmtpConfig {
    std::wstring host;
    int port = 587;
    bool useSsl = true;
    std::wstring user;
    std::wstring passEnc;
    std::wstring from;
};

struct Config {
    // [general]
    std::wstring companyName;
    std::wstring notifyEmail;
    int alertTimeoutHours = 26;
    bool sendReportEmail = false;
    std::wstring uiPasswordHash;
    std::wstring uiPasswordSalt;
    std::wstring sevenZipPath;

    SmtpConfig smtp;
    std::vector<NetCredential> netCreds;
    std::vector<BackupSet> sets;

    // [state]
    int64_t lastRunUnix = 0;
    std::wstring lastRunStatus;     // "ok" | "error" | ""

    static std::wstring DefaultPath();          // <exeDir>\backup_maximus.ini
    bool Load(const std::wstring& path);
    bool Save(const std::wstring& path) const;

    bool HasPassword() const { return !uiPasswordHash.empty(); }
    void SetPassword(const std::wstring& plain);
    bool CheckPassword(const std::wstring& plain) const;

    int TotalItems() const;
};

// Segredos
std::wstring ProtectSecret(const std::wstring& plain);
std::wstring UnprotectSecret(const std::wstring& enc);
std::wstring Sha256Hex(const std::wstring& data);

} // namespace bm
