; -- setup.iss --
[Setup]
; Basic application settings
AppName=OptimiseApp
AppVersion=1.0.0
DefaultDirName={pf}\OptimiseApp
DefaultGroupName=OptimiseApp
OutputBaseFilename=OptimiseApp_Installer
Compression=lzma2
SolidCompression=yes
LZMANumBlockThreads=2

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Add all required files
Source: "OptimiseApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.ini"; DestDir: "{app}"; Flags: ignoreversion
Source: "styles.qss"; DestDir: "{app}"; Flags: ignoreversion
Source: "appIcon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\OptimiseApp"; Filename: "{app}\OptimiseApp.exe"; IconFilename: "{app}\appIcon.ico"
Name: "{commondesktop}\OptimiseApp"; Filename: "{app}\OptimiseApp.exe"; IconFilename: "{app}\appIcon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; Ensure the installer launches the correct application
Filename: "{app}\OptimiseApp.exe"; Description: "Launch OptimiseApp"; Flags: nowait postinstall skipifsilent
