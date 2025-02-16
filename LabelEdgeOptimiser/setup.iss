; -- setup.iss --
[Setup]
; Basic application settings
AppName=LabelEdgeOptimiser
AppVersion=1.0.0
DefaultDirName={pf}\LabelEdgeOptimiser
DefaultGroupName=LabelEdgeOptimiser
OutputBaseFilename=LabelEdgeOptimiser_Installer
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; The first parameter is the source path relative to the script file.
; The second parameter is the destination folder within the installation directory.
; The Flags: "ignoreversion" ignores the file version.
Source: "InstallerFiles\OptimiseApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "InstallerFiles\config.ini"; DestDir: "{app}"; Flags: ignoreversion
Source: "InstallerFiles\styles.qss"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Create a Start Menu shortcut.
Name: "{group}\LabelEdgeOptimiser"; Filename: "{app}\main.exe"
; Optionally create a desktop shortcut.
Name: "{commondesktop}\LabelEdgeOptimiser"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; After installation, run the application or display a message.
Filename: "{app}\main.exe"; Description: "Launch LabelEdgeOptimiser"; Flags: nowait postinstall skipifsilent
