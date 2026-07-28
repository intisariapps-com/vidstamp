; =======================================================
;  Inno Setup Script - VidStamp (Video Timestamp & Marker)
; =======================================================

[Setup]
AppName=VidStamp
AppVersion=1.0.0
AppPublisher=Intisari Apps
AppPublisherURL=https://intisariapps.com/vidstamp
DefaultDirName={autopf}\VidStamp
DefaultGroupName=VidStamp
OutputDir=.
OutputBaseFilename=VidStamp_Setup
Compression=lzma2/max
SolidCompression=yes
SetupIconFile=vidstamp\ui\assets\icon.ico
WizardImageFile=vidstamp\ui\assets\installer_banner.bmp
WizardSmallImageFile=vidstamp\ui\assets\installer_small.bmp
DisableWelcomePage=no
DisableFinishedPage=no
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Menyertakan seluruh folder dist hasil kompilasi PyInstaller
Source: "dist\VidStamp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\VidStamp"; Filename: "{app}\VidStamp.exe"
Name: "{group}\{cm:UninstallProgram,VidStamp}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\VidStamp"; Filename: "{app}\VidStamp.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VidStamp.exe"; Description: "{cm:LaunchProgram,VidStamp}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKA; Subkey: "Software\Classes\.mp4\OpenWithProgids"; ValueType: string; ValueName: "VidStamp.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mkv\OpenWithProgids"; ValueType: string; ValueName: "VidStamp.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.avi\OpenWithProgids"; ValueType: string; ValueName: "VidStamp.Video"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mov\OpenWithProgids"; ValueType: string; ValueName: "VidStamp.Video"; ValueData: ""; Flags: uninsdeletevalue

Root: HKA; Subkey: "Software\Classes\VidStamp.Video"; ValueType: string; ValueName: ""; ValueData: "VidStamp Video File"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\VidStamp.Video\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\VidStamp.exe,0"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\VidStamp.Video\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VidStamp.exe"" ""%1"""; Flags: uninsdeletekey

Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "VidStamp"; ValueData: "Software\VidStamp\Capabilities"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\VidStamp\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "VidStamp"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\VidStamp\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "VidStamp Video Timestamp & Marker App"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\VidStamp\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mp4"; ValueData: "VidStamp.Video"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\VidStamp\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mkv"; ValueData: "VidStamp.Video"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\VidStamp\Capabilities\FileAssociations"; ValueType: string; ValueName: ".avi"; ValueData: "VidStamp.Video"; Flags: uninsdeletekey

