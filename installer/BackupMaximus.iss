; Instalador do Backup Maximus — Inno Setup 6
;
; Gerado a partir da build EM PASTA (dist\BackupMaximus), não do executável
; único. A escolha resolve dois problemas de uma vez:
;
;   1. LGPLv3 da PySide6/Qt: a licença assegura ao usuário o direito de
;      substituir a biblioteca Qt. Na build em pasta as DLLs ficam soltas e
;      substituíveis; no --onefile elas estão fundidas e isso é impossível.
;   2. Partida mais rápida: o --onefile extrai ~130 MB para uma pasta
;      temporária a cada execução, e este programa é chamado toda madrugada
;      pelo Agendador de Tarefas.
;
; Compilar:
;   iscc /DAppVersion=2.2.0 installer\BackupMaximus.iss

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName        "Backup Maximus"
#define AppPublisher   "WALYTECH SOLUCOES TECNOLOGICAS LTDA"
#define AppURL         "https://tgf231.github.io/backup-maximus-docs/"
#define AppExe         "BackupMaximus.exe"

[Setup]
AppId={{8B4F2C91-6D3A-4E57-9F18-2A7C5E0B4D63}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName} {#AppVersion}

; Program Files exige elevação. É de propósito: o programa aparece em
; "Aplicativos instalados" da máquina e não some se outro usuário entrar.
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

; LZMA2 no máximo — mesma família de compressão do 7-Zip, que é o que faz o
; instalador caber num tamanho copiável por rede apesar dos ~130 MB de payload.
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4

OutputDir=..\dist
OutputBaseFilename=BackupMaximus-{#AppVersion}-instalador
SetupIconFile=..\Logo_backup_maximus.ico
WizardStyle=modern
ShowLanguageDialog=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; \
  GroupDescription: "Atalhos:"

[Files]
; A build em pasta inteira, incluindo as DLLs do Qt, o 7-Zip, o rclone e os
; textos das licenças que precisam acompanhar a distribuição.
Source: "..\dist\BackupMaximus\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; Marcador que leva a configuração para %LOCALAPPDATA%. Sem ele o programa
; tentaria gravar em Program Files e abriria como primeira execução.
Source: "instalado.flag"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Executar backup agora"; Filename: "{app}\{#AppExe}"; \
  Parameters: "/run"; IconFilename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir o Backup Maximus agora"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; O programa cria esta tarefa para o lembrete diário. Deixá-la para trás faria
; o Windows tentar executar um caminho que não existe mais, todo dia.
Filename: "schtasks.exe"; Parameters: "/Delete /TN ""Backup Maximus - Lembrete"" /F"; \
  Flags: runhidden; RunOnceId: "RemoverLembrete"

[UninstallDelete]
Type: files; Name: "{app}\instalado.flag"

[Code]
// A configuração NÃO é removida na desinstalação. Ela guarda os conjuntos de
// backup do cliente e as senhas dos bancos; apagá-la ao atualizar o programa
// seria destruir o trabalho de configuração sem pedir. Quem quiser limpar de
// vez apaga %LOCALAPPDATA%\Backup Maximus à mão — e o desinstalador avisa onde.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    MsgBox('As configurações, os logs e os relatórios foram mantidos em:' + #13#10 + #13#10 +
           ExpandConstant('{localappdata}\Backup Maximus') + #13#10 + #13#10 +
           'Apague essa pasta se quiser remover tudo, inclusive os conjuntos ' +
           'de backup configurados.', mbInformation, MB_OK);
end;
