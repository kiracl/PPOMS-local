Param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = "python"

if (!(Test-Path "$repoRoot\venv\Scripts\Activate.ps1")) {
    & $python -m venv venv
}

. "$repoRoot\venv\Scripts\Activate.ps1"

pip install -U pip

if (Test-Path "$repoRoot\requirements.txt") {
    pip install -r requirements.txt
}

pip install pyinstaller

$mainPath = "$repoRoot\main.py"
$content = Get-Content $mainPath -Raw
$version = ""
if ($content -match 'V([0-9\.]+)') { $version = $Matches[1] } else { $version = Get-Date -Format "yyyyMMdd" }

$exeName = "PPOMS_V$version"

if ($Clean) {
    if (Test-Path "$repoRoot\build") { Remove-Item -Recurse -Force "$repoRoot\build" }
    if (Test-Path "$repoRoot\dist") { Remove-Item -Recurse -Force "$repoRoot\dist" }
}

$addDataArgs = @()
if (Test-Path "$repoRoot\purchase.db") { $addDataArgs += @("--add-data", "purchase.db;.") }

pyinstaller --onefile --noconsole --name $exeName @addDataArgs "$mainPath"

$distExe = Join-Path "$repoRoot\dist" "$exeName.exe"
if (!(Test-Path $distExe)) { throw "Build failed: $distExe not found" }

$releaseDir = Join-Path $repoRoot "release_v$version"
$releaseDocs = Join-Path $releaseDir "docs"
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
New-Item -ItemType Directory -Force -Path $releaseDocs | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $releaseDir "backups") | Out-Null

Copy-Item $distExe $releaseDir -Force
if (Test-Path "$repoRoot\dist\purchase.db") {
    Copy-Item "$repoRoot\dist\purchase.db" $releaseDir -Force
} elseif (Test-Path "$repoRoot\purchase.db") {
    Copy-Item "$repoRoot\purchase.db" $releaseDir -Force
}

Get-ChildItem "$repoRoot\docs" -Filter "*.md" | Copy-Item -Destination $releaseDocs -Force

if (Test-Path "$repoRoot\export.py") {
    python -c "import export; export.write_detail_import_template(r'$releaseDocs\detail_import_template.xlsx')"
} elseif (Test-Path "$repoRoot\docs\detail_import_template.xlsx") {
    Copy-Item "$repoRoot\docs\detail_import_template.xlsx" $releaseDocs -Force
}

$notePath = Join-Path $releaseDir "RELEASE_NOTE.md"
@(
    "# 发布说明",
    "",
    "版本: $version",
    "时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
    "可执行文件: $exeName.exe"
) | Set-Content -Path $notePath -Encoding UTF8

Write-Host "Release assembled at $releaseDir"
