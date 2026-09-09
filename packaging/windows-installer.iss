; Inno Setup script for the Windows build of Resolved Layers.
;
; Produces one Setup.exe that installs per-user, so it never asks for an
; administrator. That matches the Linux installer, which deliberately needs no
; root: an operator should be able to install this on a machine they do not
; administer, which at a competition or in a laboratory is the normal case.
;
; The uninstaller removes only what it installed. Settings and the Run Archive
; live under the user's own AppData and are left alone, exactly as
; uninstall-appimage.sh preserves the Linux Run Archive: a completed Verified
; Run is evidence, and removing the application is not a decision to destroy it.
;
; Built by the Windows build workflow, which passes the version and the
; PyInstaller output directory:
;
;   ISCC /DAppVersion=0.2.1 /DSourceDir=dist\resolved-layers packaging\windows-installer.iss

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\dist\resolved-layers"
#endif

#define AppName "Resolved Layers"
#define AppPublisher "Computational Health Lab"
#define AppExeName "resolved-layers.exe"
#define AppUrl "https://github.com/Abdourahman1909/resolved-layers"

[Setup]
; Stable across versions, so installing 0.2.2 replaces 0.2.1 rather than
; leaving two entries in Add/Remove Programs.
AppId={{8F3A1C42-6D5B-4E77-9A20-1C4E7B2F9D31}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}
VersionInfoVersion={#AppVersion}

; Per-user: installs under %LOCALAPPDATA%\Programs and raises no UAC prompt.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; The build is 64-bit only, like the Linux one.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

LicenseFile=..\LICENSE
InfoAfterFile=WINDOWS.md
OutputBaseFilename=Resolved_Layers-{#AppVersion}-windows-x86_64-Setup
SetupIconFile=..\src\variant_inference\assets\icons\resolved-layers.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
; The payload is already close to a gigabyte; refuse early rather than failing
; part-way through writing it.
ExtraDiskSpaceRequired=0
DirExistsWarning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
; The whole PyInstaller output. The executable loads Qt, CatBoost and LightGBM
; from the files beside it, so the tree travels intact.
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD-PARTY-NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "WINDOWS.md"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Open {#AppName}"; Flags: nowait postinstall skipifsilent

; No [UninstallDelete] section, deliberately. Settings live in
; %APPDATA%\Computational Health Lab and the Run Archive in
; %LOCALAPPDATA%\Computational Health Lab; neither was installed here and
; neither is removed. An archived Verified Run outlives the application that
; produced it.
