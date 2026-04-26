[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$ProjectRoot,

  [Parameter(Mandatory = $true)]
  [ValidateSet('Tauri', 'Web')]
  [string]$FrontendMode,

  [Parameter(Mandatory = $true)]
  [string]$NpmCommand
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$FrontendDir = Join-Path $ProjectRoot 'schedule_frontend'
$windowTitle = if ($FrontendMode -eq 'Tauri') {
  'Schedule Frontend (Tauri)'
} else {
  'Schedule Frontend (Web Fallback)'
}

try {
  $Host.UI.RawUI.WindowTitle = $windowTitle
} catch {
}

Set-Location $FrontendDir
Write-Host "$windowTitle is starting..." -ForegroundColor Cyan
Write-Host "Workdir: $FrontendDir" -ForegroundColor Gray
Write-Host "npm:     $NpmCommand" -ForegroundColor Gray

if ($FrontendMode -eq 'Tauri') {
  $cargoBin = Join-Path $env:USERPROFILE '.cargo\bin'
  if ((Test-Path -LiteralPath $cargoBin) -and -not ($env:PATH -split ';' | Where-Object { $_ -eq $cargoBin })) {
    $env:PATH = "$cargoBin;$env:PATH"
    Write-Host "cargo:   $cargoBin" -ForegroundColor Gray
  }
}

Write-Host ''

$scriptName = if ($FrontendMode -eq 'Tauri') { 'tauri:dev' } else { 'dev' }
$exitCode = 0

try {
  & $NpmCommand 'run' $scriptName
  $exitCode = $LASTEXITCODE
} catch {
  $exitCode = 1
  Write-Host ''
  Write-Host "Frontend start failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ''
if ($exitCode -eq 0) {
  Write-Host 'Frontend process exited.' -ForegroundColor Yellow
} else {
  Write-Host "Frontend exited with code $exitCode" -ForegroundColor Red
}

Write-Host 'Press Enter to close this window.' -ForegroundColor Yellow
Read-Host | Out-Null
exit $exitCode
