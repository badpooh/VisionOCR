; Inno Setup Script - OCR Vision App
; Embedded Python + PySide6 배포용

#define MyAppName "OCR Vision App"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Rootech"
#define MyAppExeName "run.bat"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=OCRVisionApp_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
SetupIconFile=
PrivilegesRequired=lowest

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Embedded Python 환경 전체
Source: "python_env\*"; DestDir: "{app}\python_env"; Flags: ignoreversion recursesubdirs createallsubdirs

; Python 스크립트 전체
Source: "python_scripts\*"; DestDir: "{app}\python_scripts"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,*.pyc"

; 런처
Source: "run.bat"; DestDir: "{app}"; Flags: ignoreversion

; 기존 설정 DB (있을 경우)
Source: "settings.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec
