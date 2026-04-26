[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$ProjectRoot,

  [Parameter(Mandatory = $true)]
  [string]$VenvPython
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$BackendDir = Join-Path $ProjectRoot 'schedule_backend'

try {
  $Host.UI.RawUI.WindowTitle = 'Schedule Backend'
} catch {
}

Set-Location $BackendDir
Write-Host 'Schedule Backend is starting...' -ForegroundColor Cyan
Write-Host "Workdir: $BackendDir" -ForegroundColor Gray
Write-Host "Python:  $VenvPython" -ForegroundColor Gray
Write-Host ''

$exitCode = 0

try {
  & $VenvPython 'run.py'
  $exitCode = $LASTEXITCODE
} catch {
  $exitCode = 1
  Write-Host ''
  Write-Host "Backend start failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ''
if ($exitCode -eq 0) {
  Write-Host 'Backend process exited.' -ForegroundColor Yellow
} else {
  Write-Host "Backend exited with code $exitCode" -ForegroundColor Red
}

Write-Host 'Press Enter to close this window.' -ForegroundColor Yellow
Read-Host | Out-Null
exit $exitCode
