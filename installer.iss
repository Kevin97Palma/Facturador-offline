; ── Inno Setup Script ─────────────────────────────────────────────────────────
; Generates: Facturador_Setup_v1.0.0.exe
; Requires:  Inno Setup 6  (https://jrsoftware.org/isdl.php)
; ─────────────────────────────────────────────────────────────────────────────

#define AppName      "Facturador Electrónico"
#define AppVersion   "1.0.0"
#define AppPublisher "Sistema de Facturación SRI Ecuador"
#define AppURL       "https://sri.gob.ec"
#define AppExeName   "Facturador.exe"
#define AppId        "{{A7B3C2D1-E4F5-6789-ABCD-EF0123456789}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Install to Program Files
DefaultDirName={autopf}\Facturador
DefaultGroupName={#AppName}
AllowNoIcons=no

; Output
OutputDir=dist
OutputBaseFilename=Facturador_Setup_v{#AppVersion}
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
CompressionThreads=auto

; Require admin rights for Program Files install
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Windows 10+ only
MinVersion=10.0

; Installer appearance
WizardStyle=modern
WizardSizePercent=110
DisableWelcomePage=no
DisableDirPage=no
DisableReadyPage=no

; Uninstall
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} v{#AppVersion}
CreateUninstallRegKey=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon";  Description: "Crear icono en el {cm:DesktopName}"; GroupDescription: "Iconos adicionales:"
Name: "startupicon";  Description: "Iniciar con Windows (solo servidor)"; GroupDescription: "Opciones:"; Flags: unchecked

[Files]
; Main application (PyInstaller one-dir output)
Source: "dist\Facturador\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Default config if not present
Source: "config.example.json"; DestDir: "{app}"; DestName: "config.json"; Flags: onlyifdoesntexist

[Icons]
; Start menu
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar";          Filename: "{uninstallexe}"

; Desktop
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Startup (optional task)
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "Facturador"; \
  ValueData: """{app}\{#AppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startupicon

; App info for Add/Remove Programs
Root: HKLM; Subkey: "SOFTWARE\{#AppPublisher}\{#AppName}"; \
  ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"

[Dirs]
; Data directories (persist on uninstall)
Name: "{app}\data";         Flags: uninsneveruninstall
Name: "{app}\data\xml";     Flags: uninsneveruninstall
Name: "{app}\data\firmas";  Flags: uninsneveruninstall
Name: "{app}\data\logos";   Flags: uninsneveruninstall

[Run]
; Launch after install
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName}"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Nothing destructive on uninstall — keep data dir

[Messages]
WelcomeLabel1=Bienvenido al instalador de [name]
WelcomeLabel2=Este asistente instalará [name/ver] en su computadora.%n%nSe recomienda cerrar todas las demás aplicaciones antes de continuar.
FinishedHeadingLabel=Instalación completada
FinishedLabel=[name] se ha instalado correctamente.%n%nCredenciales iniciales:%n  Usuario: admin@sistema.com%n  Contraseña: Admin2024#
