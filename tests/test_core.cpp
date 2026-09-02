// Backup Maximus - testes do nucleo (console, sem UI)
// Cobre: utilitarios, criptografia, hash de senha, round-trip do INI no modelo
// Conjunto->Itens, metricas, copia/espelhamento (/MIR) e o ciclo de zip da arvore.
#include "common.h"
#include "config.h"
#include "logger.h"
#include "sysinfo.h"
#include "filecopy.h"
#include "dbbackup.h"
#include "zip.h"
#include <cstdio>
#include <fstream>

using namespace bm;

static int g_pass = 0, g_fail = 0;

static void Check(bool cond, const char* what) {
    if (cond) { ++g_pass; printf("  [ok]   %s\n", what); }
    else      { ++g_fail; printf("  [FALHOU] %s\n", what); }
}
static void Section(const char* name) { printf("\n== %s ==\n", name); }

static std::wstring MakeScratchDir() {
    wchar_t tmp[MAX_PATH];
    GetTempPathW(MAX_PATH, tmp);
    std::wstring dir = PathJoin(tmp, L"bm_test_" + std::to_wstring(GetCurrentProcessId()));
    EnsureDir(dir);
    return dir;
}

static void WriteTextFile(const std::wstring& path, const std::string& text) {
    std::ofstream f(path.c_str(), std::ios::binary | std::ios::trunc);
    f.write(text.data(), text.size());
}

static std::string ReadTextFile(const std::wstring& path) {
    std::ifstream f(path.c_str(), std::ios::binary);
    return std::string((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
}

static void TestStrings() {
    Section("Utilitarios de string");
    Check(Trim(L"  abc \r\n") == L"abc", "Trim remove espacos e quebras");
    Check(Trim(L"   ") == L"", "Trim de string em branco vira vazia");
    Check(ToLower(L"AbC") == L"abc", "ToLower");
    Check(StartsWith(L"\\\\srv\\share", L"\\\\"), "StartsWith detecta UNC");
    Check(!StartsWith(L"C:\\x", L"\\\\"), "StartsWith nao confunde caminho local");
    auto parts = Split(L"a;b;c", L';');
    Check(parts.size() == 3 && parts[1] == L"b", "Split separa corretamente");
    Check(Join({ L"a", L"b" }, L"-") == L"a-b", "Join");
    Check(ReplaceAll(L"a'b'c", L"'", L"''") == L"a''b''c", "ReplaceAll duplica aspas");
    Check(QuoteArg(L"com espaco") == L"\"com espaco\"", "QuoteArg protege espacos");
    std::wstring acc = L"Configuracao Ação Ünï";
    Check(Utf8ToWide(WideToUtf8(acc)) == acc, "Round-trip UTF-8 preserva acentos");

    Check(FormatBytes(500) == L"500 B", "FormatBytes bytes");
    Check(FormatBytes(1536) == L"1,5 KB", "FormatBytes usa virgula decimal");
    Check(FormatBytes(1073741824ull) == L"1,0 GB", "FormatBytes GB");
    Check(NowStampBR().size() == 14, "Carimbo DDMMYYYYHHMMSS tem 14 digitos");
}

static void TestPaths(const std::wstring& scratch) {
    Section("Caminhos e diretorios");
    Check(PathJoin(L"C:\\a", L"b") == L"C:\\a\\b", "PathJoin insere separador");
    Check(PathJoin(L"C:\\a\\", L"b") == L"C:\\a\\b", "PathJoin nao duplica separador");
    std::wstring deep = PathJoin(scratch, L"n1\\n2\\n3");
    Check(EnsureDir(deep), "EnsureDir cria arvore recursivamente");
    Check(DirExists(deep), "DirExists confirma a arvore criada");
    Check(EnsureDir(deep), "EnsureDir e idempotente");
    std::wstring file = PathJoin(deep, L"a.txt");
    WriteTextFile(file, "conteudo");
    Check(FileExists(file), "FileExists localiza arquivo criado");
    Check(!DirExists(file), "DirExists nao confunde arquivo com pasta");
    Check(!FileExists(deep), "FileExists nao confunde pasta com arquivo");
    Check(FreeSpaceBytes(scratch) > 0, "FreeSpaceBytes devolve valor para pasta local");
    Check(WaitForPath(scratch, 5, nullptr), "WaitForPath retorna imediato p/ caminho existente");
    Check(!WaitForPath(PathJoin(scratch, L"ZZZ_inexistente"), 1, nullptr),
          "WaitForPath expira p/ caminho inexistente");
}

static void TestCrypto() {
    Section("Criptografia de segredos");
    std::wstring plain = L"S3nh@-Forte-ção";
    std::wstring enc = ProtectSecret(plain);
    Check(!enc.empty(), "ProtectSecret produz texto cifrado");
    Check(enc != plain, "Cifrado difere do texto plano");
    Check(UnprotectSecret(enc) == plain, "UnprotectSecret recupera o original");
    Check(ProtectSecret(L"").empty(), "ProtectSecret de vazio devolve vazio");
    Check(UnprotectSecret(L"lixo-nao-base64!!").empty(), "Entrada invalida nao quebra");
    Check(Sha256Hex(L"abc") == L"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
          "SHA-256 de 'abc' bate com o vetor conhecido");
}

static void TestPassword() {
    Section("Senha da interface");
    Config c;
    Check(!c.HasPassword(), "Config nova nao tem senha (primeira execucao)");
    Check(c.CheckPassword(L"qualquer"), "Sem senha definida, acesso e liberado");
    c.SetPassword(L"minha-senha");
    Check(c.HasPassword(), "Apos SetPassword, HasPassword e verdadeiro");
    Check(c.uiPasswordHash != L"minha-senha", "Senha nao e guardada em texto plano");
    Check(c.CheckPassword(L"minha-senha"), "Senha correta e aceita");
    Check(!c.CheckPassword(L"minha-senh"), "Senha incorreta e rejeitada");
    Config c2;
    c2.SetPassword(L"minha-senha");
    Check(c2.uiPasswordHash != c.uiPasswordHash, "Mesma senha gera hash diferente (salt)");
}

static void TestEnums() {
    Section("Conversao de enums");
    ItemType t; SetMode m;
    Check(ParseItemType(L"firebird", t) && t == ItemType::Firebird, "Parse 'firebird'");
    Check(ParseItemType(L"  SQLSERVER ", t) && t == ItemType::SqlServer, "Parse tolera caixa/espacos");
    Check(!ParseItemType(L"oracle", t), "Tipo desconhecido e rejeitado");
    Check(ItemTypeName(ItemType::MySql) == L"mysql", "ItemTypeName");
    Check(ParseSetMode(L"incremental", m) && m == SetMode::Incremental, "Parse 'incremental'");
    Check(!ParseSetMode(L"diferencial", m), "Modo desconhecido e rejeitado");
    Check(DefaultDumpExt(ItemType::Firebird) == L".fbk", "Extensao padrao do Firebird e .fbk");
    Check(DefaultDumpExt(ItemType::SqlServer) == L".bak", "Extensao padrao do SQL Server e .bak");
    Check(DefaultDumpExt(ItemType::MySql) == L".sql", "Extensao padrao do MySQL e .sql");
    Check(DefaultDumpExt(ItemType::Files).empty(), "Arquivo/pasta nao tem extensao de dump");
}

static void TestConfigRoundTrip(const std::wstring& scratch) {
    Section("Persistencia do INI (Conjunto -> Itens)");
    std::wstring path = PathJoin(scratch, L"cfg_test.ini");
    DeleteFileW(path.c_str());

    Config a;
    a.companyName = L"Comercio Aurora Ltda";
    a.notifyEmail = L"ti@aurora.com.br";
    a.alertTimeoutHours = 12;
    a.sendReportEmail = true;
    a.SetPassword(L"admin123");
    a.smtp.host = L"smtp.aurora.com.br";
    a.smtp.port = 465;
    a.smtp.passEnc = ProtectSecret(L"smtp-secreta");
    a.lastRunUnix = 1756200000;
    a.lastRunStatus = L"ok";

    NetCredential nc;
    nc.uncRoot = L"\\\\servidor\\backups";
    nc.user = L"DOMINIO\\svc_backup";
    nc.passEnc = ProtectSecret(L"rede-secreta");
    a.netCreds.push_back(nc);

    // Conjunto reproduzindo o BKP.bat
    BackupSet s;
    s.name = L"BKP_MAXIMUS";
    s.staging = L"C:\\BACKUP";
    s.destination = L"U:\\";
    s.mode = SetMode::Full;
    s.waitForPath = L"U:\\";
    s.waitTimeoutSec = 600;
    s.keepStaging = true;

    BackupItem i1;
    i1.name = L"PDV Expresso (banco)";
    i1.type = ItemType::Firebird;
    i1.source = L"PDVEXPRESSO";
    i1.subfolder = L"PDVEXPRESSO";
    i1.outputName = L"PDVEXPRESSO.FBK";
    i1.host = L"LOCALHOST";
    i1.user = L"SYSDBA";
    i1.passEnc = ProtectSecret(L"masterkey");
    s.items.push_back(i1);

    BackupItem i2;
    i2.name = L"Config NFC-e";
    i2.type = ItemType::Files;
    i2.source = L"C:\\Program Files (x86)\\Eagle\\PDVExpresso\\nfceConfig.ini";
    i2.subfolder = L"PDVEXPRESSO";
    s.items.push_back(i2);

    BackupItem i3;
    i3.name = L"XMLs destinatario";
    i3.type = ItemType::Files;
    i3.source = L"C:\\Program Files (x86)\\Eagle\\PDVExpresso\\Arquivos\\XmlDestinatario";
    i3.subfolder = L"PDVEXPRESSO\\Arquivos\\XmlDestinatario";
    i3.mirror = true;
    i3.enabled = false;
    s.items.push_back(i3);

    a.sets.push_back(s);

    Check(a.TotalItems() == 3, "TotalItems conta os itens de todos os conjuntos");
    Check(a.Save(path), "Config.Save grava o arquivo");

    Config b;
    Check(b.Load(path), "Config.Load le o arquivo");
    Check(b.companyName == a.companyName, "Nome da empresa preservado (com acento)");
    Check(b.alertTimeoutHours == 12, "Timeout de alerta preservado");
    Check(b.CheckPassword(L"admin123"), "Senha continua validando apos recarregar");
    Check(UnprotectSecret(b.smtp.passEnc) == L"smtp-secreta", "Senha SMTP decifra corretamente");
    Check(b.lastRunUnix == 1756200000 && b.lastRunStatus == L"ok", "Estado preservado");
    Check(b.netCreds.size() == 1 && UnprotectSecret(b.netCreds[0].passEnc) == L"rede-secreta",
          "Credencial de rede preservada e decifra");

    Check(b.sets.size() == 1, "Conjunto preservado");
    if (b.sets.size() == 1) {
        const BackupSet& g = b.sets[0];
        Check(g.name == L"BKP_MAXIMUS", "Nome do conjunto");
        Check(g.staging == L"C:\\BACKUP", "Pasta de montagem preservada");
        Check(g.destination == L"U:\\", "Destino preservado");
        Check(g.mode == SetMode::Full, "Modo do conjunto");
        Check(g.waitForPath == L"U:\\" && g.waitTimeoutSec == 600, "Espera por unidade preservada");
        Check(g.keepStaging, "keepStaging preservado");
        Check(g.items.size() == 3, "Os 3 itens foram preservados");
        if (g.items.size() == 3) {
            Check(g.items[0].type == ItemType::Firebird, "Tipo do item 1");
            Check(g.items[0].source == L"PDVEXPRESSO", "Origem (alias) do item 1");
            Check(g.items[0].subfolder == L"PDVEXPRESSO", "Subpasta do item 1");
            Check(g.items[0].outputName == L"PDVEXPRESSO.FBK", "Nome do arquivo gerado");
            Check(UnprotectSecret(g.items[0].passEnc) == L"masterkey", "Senha do banco decifra");
            Check(g.items[1].subfolder == L"PDVEXPRESSO", "Subpasta do item 2");
            Check(g.items[2].subfolder == L"PDVEXPRESSO\\Arquivos\\XmlDestinatario",
                  "Subpasta aninhada do item 3 preservada");
            Check(g.items[2].mirror, "Flag de espelhamento preservada");
            Check(!g.items[2].enabled, "Item desabilitado preservado");
        }
    }
    Check(!Config().Load(PathJoin(scratch, L"nao_existe.ini")), "Load de arquivo ausente falha");
}

static void TestSysInfo() {
    Section("Metricas do dispositivo");
    DeviceInfo d = CollectDeviceInfo(200);
    Check(!d.computerName.empty(), "Nome do computador coletado");
    Check(d.cpuUsagePct >= 0.0 && d.cpuUsagePct <= 100.0, "CPU entre 0 e 100%");
    Check(d.memUsagePct > 0.0 && d.memUsagePct <= 100.0, "Memoria entre 0 e 100%");
    Check(d.memUsedMB <= d.memTotalMB, "Memoria usada nao excede o total");
    Check(d.diskFreeGB <= d.diskTotalGB, "Disco livre nao excede o total");
}

static void TestFileCopy(const std::wstring& scratch) {
    Section("Copia incremental e espelhamento (/MIR)");
    std::wstring src = PathJoin(scratch, L"copy_src");
    std::wstring dst = PathJoin(scratch, L"copy_dst");
    EnsureDir(PathJoin(src, L"sub"));

    WriteTextFile(PathJoin(src, L"a.txt"), "conteudo A");
    WriteTextFile(PathJoin(src, L"b.txt"), "conteudo B");
    WriteTextFile(PathJoin(src, L"sub\\c.txt"), "conteudo C");

    CopyStats s1;
    Check(MirrorDirectory(src, dst, true, s1), "Primeira copia executa");
    Check(s1.filesCopied == 3, "3 arquivos copiados na primeira passada");
    Check(s1.errors == 0, "Sem erros na primeira passada");
    Check(FileExists(PathJoin(dst, L"sub\\c.txt")), "Subpasta foi replicada");
    Check(ReadTextFile(PathJoin(dst, L"a.txt")) == "conteudo A", "Conteudo copiado corretamente");

    // Segunda passada sem mudancas: tudo deve ser pulado.
    CopyStats s2;
    Check(MirrorDirectory(src, dst, true, s2), "Segunda copia executa");
    Check(s2.filesCopied == 0, "Nada recopiado quando nada mudou");
    Check(s2.filesSkipped == 3, "3 arquivos identificados como identicos");

    // Muda um arquivo: so ele deve ser recopiado.
    Sleep(1100);
    WriteTextFile(PathJoin(src, L"b.txt"), "conteudo B MODIFICADO e maior");
    CopyStats s3;
    MirrorDirectory(src, dst, true, s3);
    Check(s3.filesCopied == 1, "Somente o arquivo alterado foi recopiado");
    Check(ReadTextFile(PathJoin(dst, L"b.txt")) == "conteudo B MODIFICADO e maior",
          "Conteudo atualizado no destino");

    // Espelhamento: apagar na origem deve apagar no destino.
    DeleteFileW(PathJoin(src, L"a.txt").c_str());
    CopyStats s4;
    MirrorDirectory(src, dst, true, s4);
    Check(s4.filesDeleted == 1, "Espelhamento removeu 1 arquivo do destino");
    Check(!FileExists(PathJoin(dst, L"a.txt")), "Arquivo apagado na origem sumiu do destino");
    Check(FileExists(PathJoin(dst, L"b.txt")), "Arquivos ainda existentes foram mantidos");

    // Sem espelhamento: apagar na origem NAO apaga no destino.
    std::wstring dst2 = PathJoin(scratch, L"copy_dst2");
    CopyStats s5;
    MirrorDirectory(src, dst2, false, s5);
    DeleteFileW(PathJoin(src, L"b.txt").c_str());
    CopyStats s6;
    MirrorDirectory(src, dst2, false, s6);
    Check(s6.filesDeleted == 0, "Sem espelhamento, nada e removido do destino");
    Check(FileExists(PathJoin(dst2, L"b.txt")), "Arquivo removido da origem sobrevive no destino");

    // Arquivo unico
    std::wstring one = PathJoin(scratch, L"one_dst");
    CopyStats s7;
    Check(CopyOneFile(PathJoin(src, L"sub\\c.txt"), one, s7), "CopyOneFile copia arquivo unico");
    Check(FileExists(PathJoin(one, L"c.txt")), "Arquivo unico chegou ao destino");
    CopyStats s8;
    CopyOneFile(PathJoin(src, L"sub\\c.txt"), one, s8);
    Check(s8.filesSkipped == 1, "CopyOneFile pula quando ja esta atualizado");

    // Origem inexistente
    CopyStats s9;
    Check(!MirrorDirectory(PathJoin(scratch, L"NAO_EXISTE"), dst, true, s9),
          "Origem inexistente devolve falha");
    Check(!s9.lastError.empty(), "Erro descreve o problema");

    Check(DirectorySize(dst) > 0, "DirectorySize soma o conteudo");
}

static void TestZipTree(const std::wstring& scratch) {
    Section("Arvore inteira em UM zip");
    Zipper z(L"");
    printf("  (ferramenta: %ls)\n", z.ToolDescription().c_str());

    // Monta uma arvore parecida com a do BKP.bat
    std::wstring tree = PathJoin(scratch, L"BACKUP");
    EnsureDir(PathJoin(tree, L"PDVEXPRESSO\\Arquivos\\XmlDestinatario"));
    EnsureDir(PathJoin(tree, L"PDVEXPRESSO\\Arquivos\\Log"));
    WriteTextFile(PathJoin(tree, L"PDVEXPRESSO\\PDVEXPRESSO.FBK"), std::string(5000, 'F'));
    WriteTextFile(PathJoin(tree, L"PDVEXPRESSO\\nfceConfig.ini"), "[nfce]\nambiente=1\n");
    WriteTextFile(PathJoin(tree, L"PDVEXPRESSO\\Arquivos\\XmlDestinatario\\nota1.xml"), "<nfe>1</nfe>");
    WriteTextFile(PathJoin(tree, L"PDVEXPRESSO\\Arquivos\\Log\\envio.log"), "log de envio");

    std::wstring err;
    std::wstring zipFull = PathJoin(scratch, L"BKP_MAXIMUS26082026170000.zip");
    Check(z.ArchiveTree(tree, zipFull, true, false, err), "ArchiveTree gera o zip completo");
    if (!err.empty()) printf("       detalhe: %ls\n", err.c_str());
    Check(FileExists(zipFull), "Zip do conjunto existe no disco");

    std::wstring zipInc = PathJoin(scratch, L"BKP_MAXIMUS.zip");
    err.clear();
    Check(z.ArchiveTree(tree, zipInc, false, false, err), "ArchiveTree gera o zip incremental");
    if (!err.empty()) printf("       detalhe: %ls\n", err.c_str());

    // Acrescenta arquivo na arvore e atualiza o MESMO zip
    WriteTextFile(PathJoin(tree, L"PDVEXPRESSO\\Arquivos\\XmlDestinatario\\nota2.xml"), "<nfe>2</nfe>");
    err.clear();
    Check(z.ArchiveTree(tree, zipInc, false, true, err), "Incremental atualiza o mesmo zip");
    if (!err.empty()) printf("       detalhe: %ls\n", err.c_str());

    // Config embutida e recuperada
    std::wstring cfgFile = PathJoin(scratch, L"backup_maximus.ini");
    Config c;
    c.companyName = L"Empresa Embutida";
    c.alertTimeoutHours = 33;
    c.Save(cfgFile);
    err.clear();
    Check(z.AddFile(zipFull, cfgFile, err), "AddFile embute o INI no zip do conjunto");
    if (!err.empty()) printf("       detalhe: %ls\n", err.c_str());

    std::wstring outDir = PathJoin(scratch, L"extraido");
    err.clear();
    bool extracted = z.ExtractFile(zipFull, L"backup_maximus.ini", outDir, err);
    Check(extracted, "ExtractFile recupera o INI de dentro do zip");
    if (!err.empty()) printf("       detalhe: %ls\n", err.c_str());
    if (extracted) {
        Config rec;
        Check(rec.Load(PathJoin(outDir, L"backup_maximus.ini")), "INI recuperado e legivel");
        Check(rec.companyName == L"Empresa Embutida" && rec.alertTimeoutHours == 33,
              "Configuracao recuperada confere com a original");
    }
}

static void TestLogger() {
    Section("Log");
    Logger::Init();
    Logger::Info(L"teste de log INFO com acento: ação");
    Logger::Error(L"teste de log ERROR");
    Check(FileExists(Logger::CurrentLogPath()), "Arquivo de log foi criado");
}

static void Cleanup(const std::wstring& scratch) {
    RemoveTree(scratch);
}

int wmain() {
    SetConsoleOutputCP(CP_UTF8);
    printf("=======================================\n");
    printf(" Backup Maximus - testes do nucleo\n");
    printf("=======================================\n");

    std::wstring scratch = MakeScratchDir();
    printf("Pasta de teste: %ls\n", scratch.c_str());

    TestStrings();
    TestPaths(scratch);
    TestCrypto();
    TestPassword();
    TestEnums();
    TestConfigRoundTrip(scratch);
    TestSysInfo();
    TestFileCopy(scratch);
    TestZipTree(scratch);
    TestLogger();

    Cleanup(scratch);

    printf("\n=======================================\n");
    printf(" Resultado: %d passaram, %d falharam\n", g_pass, g_fail);
    printf("=======================================\n");
    return g_fail == 0 ? 0 : 1;
}
