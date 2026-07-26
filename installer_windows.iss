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
Name: "indonesian"; MessagesFile: "compiler:Languages\Indonesian.isl"

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
