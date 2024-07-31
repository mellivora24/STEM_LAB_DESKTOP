; Script Inno Setup

[Setup]
AppName=STEMVN_LAB Desktop
AppVersion=1.0.0
DefaultDirName={pf}\STEMVN_LAB Desktop
DefaultGroupName=STEMVN
OutputDir=.
OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "./assest/icon.ico"; DestDir: "{app}"

[Icons]
Name: "{group}\STEMVN_LAB Desktop"; Filename: "{app}\main.exe"
Name: "{userdesktop}\STEMVN_LAB Desktop"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\main.exe"; Description: "{cm:LaunchProgram,STEMVN_LAB Desktop}"; Flags: nowait postinstall skipifsilent

[Registry]
; Register URI Scheme
Root: HKCR; Subkey: "stemvn_lab"; ValueType: string; ValueName: ""; ValueData: "URL:STEMVN_LAB Protocol"; Flags: uninsdeletekey
Root: HKCR; Subkey: "stemvn_lab"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCR; Subkey: "stemvn_lab\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\icon.ico"; Flags: uninsdeletekey
Root: HKCR; Subkey: "stemvn_lab\shell"; ValueType: string; ValueName: ""; ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "stemvn_lab\shell\open"; ValueType: string; ValueName: ""; ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "stemvn_lab\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\main.exe"" ""%1"""; Flags: uninsdeletekey

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
