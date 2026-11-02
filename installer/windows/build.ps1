param(
    [string]$Compiler = 'C:\Program Files\Inno Setup 7\ISCC.exe',
    [Parameter(Mandatory = $true)][string]$V7Profile,
    [Parameter(Mandatory = $true)][string]$ReviewedPayload,
    [Parameter(Mandatory = $true)][string]$GameContract
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$v7 = (Resolve-Path -LiteralPath $V7Profile).Path
$payload = (Resolve-Path -LiteralPath $ReviewedPayload).Path
$contractPath = (Resolve-Path -LiteralPath $GameContract).Path
if (-not (Test-Path -LiteralPath $Compiler -PathType Leaf)) { throw 'Inno Setup compiler not found.' }
$manifest = Join-Path $v7 'manifest.json'
$manifestHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
$sidecar = (Get-Content -LiteralPath (Join-Path $v7 'manifest.sha256') -Raw).Trim().Split(' ')[0].ToLowerInvariant()
$contract = Get-Content -LiteralPath $contractPath -Raw | ConvertFrom-Json
if (($manifestHash -ne $sidecar) -or ($manifestHash -ne $contract.sourceManifestSha256.ToLowerInvariant())) { throw 'The V7 manifest, sidecar and game contract do not match.' }
if (@($contract.requiredFiles).Count -ne 79) { throw 'Unexpected game contract size.' }
& python -B (Join-Path $PSScriptRoot 'verify_payload.py') $v7 $payload
if ($LASTEXITCODE -ne 0) { throw 'Payload freshness or privacy verification failed.' }
$inputDir = Join-Path $root 'build\inno-v7\input'
$outputDir = Join-Path $root 'build\inno-v7\release'
New-Item -ItemType Directory -Path $inputDir,$outputDir -Force | Out-Null
$lines = @($contract.requiredFiles | ForEach-Object { $_.sha256.ToLowerInvariant() + '|' + $_.relative.Replace('/', '\') })
[IO.File]::WriteAllLines((Join-Path $inputDir 'game-contract.txt'), [string[]]$lines, [Text.Encoding]::ASCII)
Add-Type -AssemblyName System.Drawing
$icon = [Drawing.Icon]::ExtractAssociatedIcon((Join-Path $payload 'VCMI_client.exe'))
if ($null -eq $icon) { throw 'Could not read the game icon.' }
$stream = [IO.File]::Create((Join-Path $inputDir 'paths.ico'))
try { $icon.Save($stream) } finally { $stream.Dispose(); $icon.Dispose() }
$creditNames = @('runeterra-demacia\CREDITS.md', 'runeterra-ixtal\docs\CREDITS.md', 'runeterra-piltover\docs\CREDITS.md')
foreach ($name in $creditNames) {
    $source = Join-Path (Join-Path $v7 'app\Mods') $name
    $content = Get-Content -LiteralPath $source -Raw
    if ($content -match '(?i)([a-z]:[\\/]users[\\/]|[a-z]:[\\/]runeterra|matcy|[a-z]:[\\/]e2e)') { throw "Private path found in credit document: $name" }
    $destination = Join-Path (Join-Path $inputDir 'credits') $name
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
}
& $Compiler '/Qp' "/DPayloadDir=$payload" "/DInputDir=$inputDir" "/DOutputDir=$outputDir" (Join-Path $PSScriptRoot 'paths-v7.iss')
if ($LASTEXITCODE -ne 0) { throw "Inno compiler failed: $LASTEXITCODE" }
$exe = Join-Path $outputDir 'Paths-of-Runeterra-V7-Setup.exe'
$sha = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $outputDir 'SHA256SUMS.txt'), "$sha  Paths-of-Runeterra-V7-Setup.exe`n", [Text.Encoding]::ASCII)
Write-Host "Built $exe"
Write-Host "SHA-256: $sha"
