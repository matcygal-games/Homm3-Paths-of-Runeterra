#ifndef PayloadDir
  #error PayloadDir must point to the reviewed V7 app payload
#endif
#ifndef InputDir
  #error InputDir must contain the compatibility contract, credits and icon
#endif
#ifndef OutputDir
  #error OutputDir must name the installer output directory
#endif

[Setup]
AppId={{5EDE5FD2-5B6E-4A75-A177-E8B127178E71}
AppName=Heroes III: Paths of Runeterra
AppVersion=V7
AppPublisher=Paths of Runeterra community project
DefaultDirName={localappdata}\Programs\Paths of Runeterra
DefaultGroupName=Paths of Runeterra
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=Paths-of-Runeterra-V7-Setup
SetupIconFile={#InputDir}\paths.ico
UninstallDisplayIcon={app}\app\VCMI_client.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=no

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\manual\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#InputDir}\credits\runeterra-demacia\CREDITS.md"; DestDir: "{app}\app\Mods\runeterra-demacia"; Flags: ignoreversion
Source: "{#InputDir}\credits\runeterra-ixtal\docs\CREDITS.md"; DestDir: "{app}\app\Mods\runeterra-ixtal\docs"; Flags: ignoreversion
Source: "{#InputDir}\credits\runeterra-piltover\docs\CREDITS.md"; DestDir: "{app}\app\Mods\runeterra-piltover\docs"; Flags: ignoreversion
Source: "{#InputDir}\game-contract.txt"; Flags: dontcopy
Source: "launch.cmd"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Paths of Runeterra"; Filename: "{app}\launch.cmd"; WorkingDir: "{app}\app"; IconFilename: "{app}\app\VCMI_client.exe"
Name: "{group}\Uninstall Paths of Runeterra"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Paths of Runeterra"; Filename: "{app}\launch.cmd"; WorkingDir: "{app}\app"; IconFilename: "{app}\app\VCMI_client.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\launch.cmd"; Description: "Launch Paths of Runeterra"; Flags: postinstall nowait skipifsilent unchecked

[Code]
var
  GamePage: TInputDirWizardPage;

function GetFileAttributesW(lpFileName: String): LongWord;
  external 'GetFileAttributesW@kernel32.dll stdcall';
function RemoveDirectoryW(lpPathName: String): Boolean;
  external 'RemoveDirectoryW@kernel32.dll stdcall';

function LooksLikeGame(const P: String): Boolean;
begin
  Result := FileExists(AddBackslash(P) + 'Data\H3bitmap.lod') and DirExists(AddBackslash(P) + 'Mp3');
end;

function FindFromUninstall(const Root: Integer): String;
var Names: TArrayOfString; I: Integer; Key, Name, P: String;
begin
  Result := '';
  Key := 'Software\Microsoft\Windows\CurrentVersion\Uninstall';
  if RegGetSubkeyNames(Root, Key, Names) then
    for I := 0 to GetArrayLength(Names) - 1 do begin
      if RegQueryStringValue(Root, Key + '\' + Names[I], 'DisplayName', Name) and
         (Pos('heroes', Lowercase(Name)) > 0) and (Pos('might', Lowercase(Name)) > 0) and
         RegQueryStringValue(Root, Key + '\' + Names[I], 'InstallLocation', P) and LooksLikeGame(P) then begin
        Result := P;
        Exit;
      end;
    end;
end;

function FindGame: String;
var P: String;
begin
  Result := ExpandConstant('{param:GAME|}');
  if Result <> '' then Exit;
  P := FindFromUninstall(HKCU); if P <> '' then begin Result := P; Exit; end;
  P := FindFromUninstall(HKLM32); if P <> '' then begin Result := P; Exit; end;
  P := FindFromUninstall(HKLM64); if P <> '' then begin Result := P; Exit; end;
  P := ExpandConstant('{commonpf32}\Steam\steamapps\common\Heroes of Might and Magic 3 Complete');
  if LooksLikeGame(P) then Result := P;
end;

procedure InitializeWizard;
begin
  ExtractTemporaryFile('game-contract.txt');
  GamePage := CreateInputDirPage(wpSelectDir, 'Locate Heroes III',
    'Choose your existing Heroes III installation',
    'Select the folder containing Data and Mp3. Setup checks that it matches the V7 game data. Your original installation is required separately.',
    False, '');
  GamePage.Add('Heroes III folder:');
  GamePage.Values[0] := FindGame;
end;

function EmptyDirectory(const P: String): Boolean;
var F: TFindRec;
begin
  Result := True;
  if FindFirst(AddBackslash(P) + '*', F) then begin
    try
      repeat
        if (F.Name <> '.') and (F.Name <> '..') then begin Result := False; Exit; end;
      until not FindNext(F);
    finally FindClose(F); end;
  end;
end;

function HasReparseAncestor(const Path: String): Boolean;
var P, Parent: String; A: LongWord;
begin
  Result := False;
  P := RemoveBackslashUnlessRoot(ExpandFileName(Path));
  while P <> '' do begin
    A := GetFileAttributesW(P);
    if (A <> $FFFFFFFF) and ((A and $400) <> 0) then begin Result := True; Exit; end;
    Parent := RemoveBackslashUnlessRoot(ExtractFileDir(P));
    if (Parent = P) or (Parent = '') then Exit;
    P := Parent;
  end;
end;

procedure ReportError(const MessageText: String);
begin
  if WizardSilent then Log(MessageText)
  else MsgBox(MessageText, mbError, MB_OK);
end;

function ValidatePaths: Boolean;
var Game, Dest: String;
begin
  Result := False;
  Game := RemoveBackslashUnlessRoot(ExpandFileName(GamePage.Values[0]));
  Dest := RemoveBackslashUnlessRoot(ExpandFileName(WizardDirValue));
  if not LooksLikeGame(Game) then begin ReportError('Select a Heroes III folder containing Data and Mp3.'); Exit; end;
  if (Pos('%', Game) > 0) or (Pos('%', Dest) > 0) then begin ReportError('Paths containing percent signs are not supported.'); Exit; end;
  if (CompareText(Game, Dest) = 0) or (Pos(Lowercase(AddBackslash(Game)), Lowercase(AddBackslash(Dest))) = 1) or
     (Pos(Lowercase(AddBackslash(Dest)), Lowercase(AddBackslash(Game))) = 1) then begin
    ReportError('Choose a separate installation folder outside the original Heroes III folder.'); Exit;
  end;
  if HasReparseAncestor(Game) or HasReparseAncestor(Dest) then begin
    ReportError('Choose paths without symbolic links or junctions in their parent folders.'); Exit;
  end;
  if DirExists(Dest) and not EmptyDirectory(Dest) then begin ReportError('Choose a new or empty installation folder.'); Exit; end;
  Result := True;
end;

function ValidateGame: Boolean;
var Lines: TArrayOfString; I, Separator: Integer; Hash, Relative, P: String;
begin
  Result := False;
  if not LoadStringsFromFile(ExpandConstant('{tmp}\game-contract.txt'), Lines) then begin ReportError('The game compatibility list could not be read.'); Exit; end;
  if GetArrayLength(Lines) <> 79 then begin ReportError('The game compatibility list is incomplete.'); Exit; end;
  WizardForm.StatusLabel.Caption := 'Checking Heroes III game files...';
  WizardForm.Update;
  for I := 0 to GetArrayLength(Lines) - 1 do begin
    Separator := Pos('|', Lines[I]);
    if Separator <> 65 then begin ReportError('The game compatibility list is invalid.'); Exit; end;
    Hash := Copy(Lines[I], 1, 64);
    Relative := Copy(Lines[I], 66, Length(Lines[I]));
    P := AddBackslash(GamePage.Values[0]) + Relative;
    if not FileExists(P) then begin ReportError('Missing required Heroes III file: ' + Relative); Exit; end;
    if CompareText(GetSHA256OfFile(P), Hash) <> 0 then begin ReportError('The selected Heroes III version differs from V7: ' + Relative); Exit; end;
  end;
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = GamePage.ID then Result := ValidatePaths and ValidateGame;
end;

function JsonPath(S: String): String;
begin
  StringChangeEx(S, '\', '\\', True);
  StringChangeEx(S, '"', '\"', True);
  Result := S;
end;

procedure MakeJunction(const Link, Target: String);
var Code: Integer; Params: String;
begin
  Params := '/D /C mklink /J "' + Link + '" "' + Target + '"';
  if not Exec(ExpandConstant('{cmd}'), Params, '', SW_HIDE, ewWaitUntilTerminated, Code) then RaiseException('Unable to start junction creation.');
  if Code <> 0 then RaiseException('Unable to link original game data. Choose an NTFS installation drive.');
end;

procedure RemoveJunction(const P: String);
var A: LongWord;
begin
  A := GetFileAttributesW(P);
  if (A <> $FFFFFFFF) and ((A and $400) <> 0) then RemoveDirectoryW(P);
end;

procedure WriteUtf8(const P, Content: String);
begin
  if not SaveStringToFile(P, Utf8Encode(Content), False) then RaiseException('Cannot write configuration: ' + P);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var App, UserDir, Config, S: String;
begin
  if CurStep <> ssPostInstall then Exit;
  App := ExpandConstant('{app}\app');
  UserDir := ExpandConstant('{app}\user');
  Config := UserDir + '\config';
  try
    MakeJunction(App + '\Data', AddBackslash(GamePage.Values[0]) + 'Data');
    MakeJunction(App + '\Mp3', AddBackslash(GamePage.Values[0]) + 'Mp3');
    if not ForceDirectories(Config) then RaiseException('Cannot create the user profile.');
    S := '{"userDataPath":"' + JsonPath(UserDir) + '","userConfigPath":"' + JsonPath(Config) + '","userCachePath":"' + JsonPath(UserDir + '\cache') + '","userLogsPath":"' + JsonPath(UserDir + '\logs') + '","userSavePath":"' + JsonPath(UserDir + '\Saves') + '"}';
    WriteUtf8(App + '\config\dirs.json', S);
    WriteUtf8(Config + '\settings.json', '{"battle":{"enableQuickSpellPanel":false,"stickyHeroInfoWindows":false,"showQueue":false},"mods":{"validation":"full"}}');
    WriteUtf8(Config + '\modSettings.json', '{"activePreset":"paths-of-runeterra","presets":{"paths-of-runeterra":{"mods":["vcmi","runeterra-demacia","runeterra-noxus","runeterra-freljord","runeterra-zaun","runeterra-bandlecity","runeterra-ionia","runeterra-piltover","runeterra-ixtal","runeterra-bilgewater","runeterra-targon","runeterra-shurima","runeterra-world","runeterra-world-systems","paths-of-runeterra","core"],"settings":{}}}}');
  except
    RemoveJunction(App + '\Data');
    RemoveJunction(App + '\Mp3');
    RaiseException(GetExceptionMessage);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then begin
    RemoveJunction(ExpandConstant('{app}\app\Data'));
    RemoveJunction(ExpandConstant('{app}\app\Mp3'));
  end;
end;
