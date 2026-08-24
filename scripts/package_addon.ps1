$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$addonRoot = Join-Path $projectRoot 'addon\EasyStats'
$toc = Get-Content -LiteralPath (Join-Path $addonRoot 'EasyStats.toc')
$version = ($toc | Where-Object { $_ -like '## Version:*' }) -replace '^## Version:\s*', ''
$distRoot = Join-Path $projectRoot 'dist'
$stageRoot = Join-Path $distRoot '.stage'
$stageAddon = Join-Path $stageRoot 'EasyStats'
$zip = Join-Path $distRoot "EasyStats-$version.zip"

New-Item -ItemType Directory -Force -Path $distRoot | Out-Null
if (Test-Path -LiteralPath $stageRoot) {
    $resolvedStage = (Resolve-Path -LiteralPath $stageRoot).Path
    if (-not $resolvedStage.StartsWith($distRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe staging path' }
    Remove-Item -Recurse -Force -LiteralPath $resolvedStage
}
Copy-Item -Recurse -LiteralPath $addonRoot -Destination $stageAddon
if (Test-Path -LiteralPath $zip) { Remove-Item -Force -LiteralPath $zip }
Compress-Archive -Path $stageAddon -DestinationPath $zip -CompressionLevel Optimal
Remove-Item -Recurse -Force -LiteralPath $stageRoot
Write-Output $zip
