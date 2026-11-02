#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$GameDirectory,
    [switch]$ValidateOnly,
    [switch]$NonInteractive,
    [switch]$LaunchCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$scopeName = 'paths-of-runeterra-v7-manual'
$utf8 = New-Object System.Text.UTF8Encoding($false)
# Resolve existing paths through Windows itself, rejecting DOS short-name and
# SUBST aliases which could otherwise disguise overlapping source/output paths.
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
public static class PathsManualCanonicalPath {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr CreateFileW(string path, uint access, uint sharing, IntPtr security, uint creation, uint flags, IntPtr template);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern uint GetFinalPathNameByHandleW(IntPtr file, StringBuilder path, uint length, uint flags);
    [DllImport("kernel32.dll")]
    static extern bool CloseHandle(IntPtr file);
    public static string Get(string path) {
        IntPtr handle = CreateFileW(path, 0, 7, IntPtr.Zero, 3, 0x02000000, IntPtr.Zero);
        if (handle == new IntPtr(-1)) throw new Win32Exception(Marshal.GetLastWin32Error());
        try {
            var buffer = new StringBuilder(4096);
            uint length = GetFinalPathNameByHandleW(handle, buffer, (uint)buffer.Capacity, 0);
            if (length == 0 || length >= buffer.Capacity) throw new Win32Exception(Marshal.GetLastWin32Error());
            string result = buffer.ToString();
            if (result.StartsWith(@"\\?\")) result = result.Substring(4);
            return result;
        } finally { CloseHandle(handle); }
    }
}
'@

function Full-LocalPath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path) -or $Path -ne $Path.Trim() -or
        $Path -notmatch '^[A-Za-z]:[\\/]' -or $Path -match '[%!*?"<>|\x00-\x1f]') {
        throw 'Use an unambiguous absolute local drive path without percent signs or wildcard characters.'
    }
    $parts = $Path.Substring(3) -split '[\\/]'
    foreach ($part in $parts) {
        if ($part -eq '.' -or $part -eq '..' -or $part -match '[ .]$' -or $part.Contains(':')) {
            throw 'Paths with relative components, trailing dots/spaces or alternate streams are not supported.'
        }
    }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    if ($full.Length -lt 3 -or $full.Length -gt 210) { throw 'Choose a shorter, non-root installation folder.' }
    return $full
}

function Item-Exists([string]$Path) {
    return $null -ne (Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue)
}

function Assert-NoReparse([string]$Path) {
    $cursor = [IO.Path]::GetFullPath($Path)
    $physicalChecked = $false
    while ($cursor) {
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction SilentlyContinue
        if ($null -ne $item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "A symbolic link or junction is not allowed here: $cursor"
        }
        if ($null -ne $item -and -not $physicalChecked) {
            $physical = [PathsManualCanonicalPath]::Get($cursor)
            if ($physical.TrimEnd('\') -ine $cursor.TrimEnd('\')) {
                throw "Use the actual local path instead of a drive alias or short filename: $cursor"
            }
            $physicalChecked = $true
        }
        $parent = [IO.Directory]::GetParent($cursor)
        if ($null -eq $parent) { break }
        $cursor = $parent.FullName
    }
}

function Assert-UserTree([string]$Path) {
    Assert-NoReparse $Path
    if (-not (Item-Exists $Path)) { return }
    $pending = New-Object 'System.Collections.Generic.Stack[string]'
    $pending.Push($Path)
    while ($pending.Count -gt 0) {
        foreach ($item in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "The isolated user profile contains a symbolic link or junction: $($item.FullName)"
            }
            if ($item.PSIsContainer) { $pending.Push($item.FullName) }
        }
    }
}

function Read-Json([string]$Path) {
    Assert-NoReparse $Path
    return ([IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8) | ConvertFrom-Json)
}

function Write-Json([string]$Path, $Value) {
    Assert-NoReparse $Path
    [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 20), $utf8)
}

function Looks-LikeGame([string]$Path) {
    return (Test-Path -LiteralPath (Join-Path $Path 'Data\H3bitmap.lod') -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $Path 'Mp3') -PathType Container)
}

function Find-GameCandidates {
    $found = New-Object 'System.Collections.Generic.List[string]'
    $possible = New-Object 'System.Collections.Generic.List[string]'
    foreach ($hive in @([Microsoft.Win32.RegistryHive]::CurrentUser, [Microsoft.Win32.RegistryHive]::LocalMachine)) {
        foreach ($view in @([Microsoft.Win32.RegistryView]::Registry32, [Microsoft.Win32.RegistryView]::Registry64)) {
            $base = $null; $key = $null
            try {
                $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey($hive, $view)
                $key = $base.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Uninstall')
                if ($null -ne $key) {
                    foreach ($name in $key.GetSubKeyNames()) {
                        $entry = $key.OpenSubKey($name)
                        try {
                            $display = [string]$entry.GetValue('DisplayName', '')
                            $location = [string]$entry.GetValue('InstallLocation', '')
                            if ($display -match '(?i)heroes' -and $display -match '(?i)might' -and $location) { $possible.Add($location) }
                        } finally { if ($null -ne $entry) { $entry.Dispose() } }
                    }
                }
            } catch { Write-Verbose 'One registry discovery view is unavailable.' }
            finally { if ($null -ne $key) { $key.Dispose() }; if ($null -ne $base) { $base.Dispose() } }
        }
    }
    foreach ($drive in Get-PSDrive -PSProvider FileSystem) {
        if ($drive.Root -match '^[A-Za-z]:\\$') {
            foreach ($relative in @('GOG Games\Heroes of Might and Magic 3 Complete', 'Games\Heroes of Might and Magic 3 Complete')) {
                $possible.Add((Join-Path $drive.Root $relative))
            }
        }
    }
    foreach ($programs in @(${env:ProgramFiles(x86)}, $env:ProgramFiles)) {
        if ($programs) {
            foreach ($relative in @('Steam\steamapps\common\Heroes of Might and Magic 3 Complete', 'GOG.com\Heroes of Might and Magic 3 Complete', 'GOG Galaxy\Games\Heroes of Might and Magic 3 Complete')) {
                $possible.Add((Join-Path $programs $relative))
            }
        }
    }
    foreach ($candidate in $possible) {
        try {
            $candidate = Full-LocalPath $candidate
            Assert-NoReparse $candidate
            if ((Looks-LikeGame $candidate) -and -not $found.Contains($candidate)) { $found.Add($candidate) }
        } catch { Write-Verbose 'Ignoring an unsafe or unavailable discovery candidate.' }
    }
    return @($found | Sort-Object -Unique)
}

function Select-GameFolder {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    try {
        $dialog.Description = 'Select your existing Heroes III folder containing Data and Mp3.'
        $dialog.ShowNewFolderButton = $false
        if ($dialog.ShowDialog() -ne [Windows.Forms.DialogResult]::OK) { throw 'Setup cancelled. No game files were changed.' }
        return $dialog.SelectedPath
    } finally { $dialog.Dispose() }
}

function Directory-Bindings([string]$PackageDirectory) {
    $profile = Join-Path $PackageDirectory 'user'
    return [ordered]@{
        userDataPath = $profile
        userConfigPath = Join-Path $profile 'config'
        userCachePath = Join-Path $profile 'cache'
        userLogsPath = Join-Path $profile 'logs'
        userSavePath = Join-Path $profile 'Saves'
    }
}

function Assert-Bindings([string]$Path, $Expected) {
    $observed = Read-Json $Path
    if (@($observed.PSObject.Properties).Count -ne $Expected.Count) { throw 'Existing dirs.json is not owned by this setup.' }
    foreach ($key in $Expected.Keys) {
        if ($observed.PSObject.Properties.Name -notcontains $key -or $observed.$key -cne $Expected[$key]) {
            throw 'Existing dirs.json has unexpected directory bindings. Refusing to overwrite it.'
        }
    }
}

function Assert-Junction([string]$Link, [string]$Target) {
    $item = Get-Item -LiteralPath $Link -Force -ErrorAction Stop
    if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.LinkType -ne 'Junction') {
        throw "Refusing to overwrite a foreign game-data directory: $Link"
    }
    $targets = @($item.Target)
    if ($targets.Count -ne 1 -or (Full-LocalPath ([string]$targets[0])) -ine $Target) {
        throw "An existing game-data junction has an unexpected target: $Link"
    }
}

try {
    $root = Full-LocalPath $PSScriptRoot
    Assert-NoReparse $root
    $app = Join-Path $root 'app'
    $user = Join-Path $root 'user'
    $contractPath = Join-Path $root 'game-contract.json'
    $receiptPath = Join-Path $root '.manual-setup-receipt.json'
    $dirsPath = Join-Path $app 'config\dirs.json'
    foreach ($path in @($app, (Join-Path $app 'config'), (Join-Path $app 'VCMI_client.exe'), $receiptPath, $dirsPath, $contractPath)) {
        Assert-NoReparse $path
    }
    if (-not (Test-Path -LiteralPath (Join-Path $app 'VCMI_client.exe') -PathType Leaf)) {
        throw 'The bundled VCMI client is missing. Extract the entire ZIP before running setup.'
    }
    $contract = Read-Json $contractPath
    if ($contract.build -ne 'Paths of Runeterra V7' -or @($contract.requiredFiles).Count -ne 79) {
        throw 'The V7 compatibility contract is invalid or incomplete.'
    }
    $contractHash = (Get-FileHash -LiteralPath $contractPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $receipt = $null
    if (Item-Exists $receiptPath) {
        $receipt = Read-Json $receiptPath
        if ($receipt.scope -ne $scopeName -or $receipt.version -ne 1 -or $receipt.contractSha256 -ne $contractHash -or
            $receipt.state -notin @('preparing', 'complete')) { throw 'The existing setup receipt does not belong to this package.' }
        $oldRoot = Full-LocalPath ([string]$receipt.packageDirectory)
        $recordedGame = Full-LocalPath ([string]$receipt.gameDirectory)
        if (-not $GameDirectory) { $GameDirectory = $recordedGame }
        if ((Full-LocalPath $GameDirectory) -ine $recordedGame) { throw 'This extraction is already bound to another Heroes III installation. Extract a fresh copy to change it.' }
        if (Item-Exists $dirsPath) { Assert-Bindings $dirsPath (Directory-Bindings $oldRoot) }
    } else {
        if ($LaunchCheck) { throw 'Run setup.cmd before launching the game.' }
        foreach ($path in @($user, $dirsPath, (Join-Path $app 'Data'), (Join-Path $app 'Mp3'))) {
            if (Item-Exists $path) { throw "Existing data or configuration has no setup receipt. Use a fresh extraction: $path" }
        }
    }
    Assert-UserTree $user
    if (-not $GameDirectory -and $env:HOMM3_PATH) { $GameDirectory = $env:HOMM3_PATH }
    if (-not $GameDirectory) {
        $candidates = @(Find-GameCandidates)
        if ($candidates.Count -eq 1) { $GameDirectory = $candidates[0] }
        elseif ($NonInteractive) { throw 'No unique Heroes III installation was found. Supply -GameDirectory or HOMM3_PATH.' }
        else { $GameDirectory = Select-GameFolder }
    }
    $game = Full-LocalPath $GameDirectory
    Assert-NoReparse $game
    if ($game -ieq $root -or $game.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $root.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'The extracted package and original Heroes III installation must be separate, non-overlapping folders.'
    }
    if (-not (Looks-LikeGame $game)) { throw 'Select the Heroes III installation folder containing Data\H3bitmap.lod and Mp3.' }
    foreach ($name in @('Data', 'Mp3')) {
        $target = Join-Path $game $name
        Assert-NoReparse $target
        $link = Join-Path $app $name
        if (Item-Exists $link) {
            if ($null -eq $receipt) { throw "An unowned game-data directory already exists: $link" }
            Assert-Junction $link $target
        } elseif ($LaunchCheck) { throw 'An original game-data junction is missing. Run setup.cmd again.' }
    }
    # Validate every relative name before reading any original files.
    $seen = @{}
    foreach ($entry in $contract.requiredFiles) {
        $relative = [string]$entry.relative
        if ($relative -notmatch '^(Data|Mp3)/[^/\\:*?"<>|%]+$' -or $relative -match '[ .]$' -or
            $entry.sha256 -notmatch '^[a-fA-F0-9]{64}$' -or $seen.ContainsKey($relative)) {
            throw 'The compatibility contract contains an unsafe or duplicate file entry.'
        }
        $seen[$relative] = $true
        $source = Join-Path $game $relative
        Assert-NoReparse $source
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Required original game file is missing: $relative" }
    }
    if ($LaunchCheck) {
        if ($null -eq $receipt -or $receipt.state -ne 'complete' -or $oldRoot -ine $root) {
            throw 'Setup is incomplete or the extraction was moved. Run setup.cmd again.'
        }
        Assert-Bindings $dirsPath (Directory-Bindings $root)
        foreach ($relative in @('config', 'cache', 'logs', 'Saves', 'temp')) {
            if (-not (Test-Path -LiteralPath (Join-Path $user $relative) -PathType Container)) { throw 'An isolated user directory is missing. Run setup.cmd again.' }
        }
        Write-Host 'Paths of Runeterra setup is ready.'
        exit 0
    }
    Write-Host 'Checking 79 original Heroes III files (SHA-256)...'
    foreach ($entry in $contract.requiredFiles) {
        $source = Join-Path $game ([string]$entry.relative)
        if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ine $entry.sha256) {
            throw "This Heroes III data differs from the V7 compatibility version: $($entry.relative)"
        }
    }
    if ($ValidateOnly) {
        Write-Host 'Validation passed. No files, links or settings were changed.'
        exit 0
    }
    # Record ownership before creating anything so interrupted setup can resume safely.
    $record = [ordered]@{ scope = $scopeName; version = 1; state = 'preparing'; contractSha256 = $contractHash; packageDirectory = $root; gameDirectory = $game }
    Write-Json $receiptPath $record
    foreach ($relative in @('', 'config', 'cache', 'cache\extracted', 'logs', 'Saves', 'temp', 'screenshots')) {
        $path = if ($relative) { Join-Path $user $relative } else { $user }
        Assert-NoReparse $path
        if (-not (Item-Exists $path)) { $null = New-Item -ItemType Directory -Path $path }
        elseif (-not (Test-Path -LiteralPath $path -PathType Container)) { throw "A user directory is occupied by a file: $path" }
    }
    Write-Json $dirsPath (Directory-Bindings $root)
    $settingsPath = Join-Path $user 'config\settings.json'
    if (-not (Item-Exists $settingsPath)) {
        Write-Json $settingsPath ([ordered]@{ battle = [ordered]@{ enableQuickSpellPanel = $false; stickyHeroInfoWindows = $false; showQueue = $false }; mods = @{ validation = 'full' } })
    }
    $modsPath = Join-Path $user 'config\modSettings.json'
    if (-not (Item-Exists $modsPath)) {
        $mods = @('vcmi', 'runeterra-demacia', 'runeterra-noxus', 'runeterra-freljord', 'runeterra-zaun', 'runeterra-bandlecity', 'runeterra-ionia', 'runeterra-piltover', 'runeterra-ixtal', 'runeterra-bilgewater', 'runeterra-targon', 'runeterra-shurima', 'runeterra-world', 'runeterra-world-systems', 'paths-of-runeterra', 'core')
        Write-Json $modsPath ([ordered]@{ activePreset = 'paths-of-runeterra'; presets = @{ 'paths-of-runeterra' = @{ mods = $mods; settings = @{} } } })
    }
    foreach ($name in @('Data', 'Mp3')) {
        $link = Join-Path $app $name
        if (-not (Item-Exists $link)) { $null = New-Item -ItemType Junction -Path $link -Target (Join-Path $game $name) }
        Assert-Junction $link (Join-Path $game $name)
    }
    $record.state = 'complete'
    Write-Json $receiptPath $record
    Write-Host 'Setup complete. Double-click launch.cmd when you want to play.'
    Write-Host 'Your original Heroes III files were only read; settings and saves belong to this extraction.'
    exit 0
} catch {
    Write-Host ('Setup stopped: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
