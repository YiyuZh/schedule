[CmdletBinding()]
param(
  [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot 'schedule_backend'
$FrontendDir = Join-Path $ProjectRoot 'schedule_frontend'
$ProcessStatePath = Join-Path $ProjectRoot '.schedule-dev-processes.json'

function Write-Step([string]$Message) {
  if (-not $Quiet) {
    Write-Host "[STEP] $Message" -ForegroundColor Cyan
  }
}

function Write-Info([string]$Message) {
  if (-not $Quiet) {
    Write-Host "[INFO] $Message" -ForegroundColor Gray
  }
}

function Write-WarnMessage([string]$Message) {
  if (-not $Quiet) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
  }
}

function Write-Success([string]$Message) {
  if (-not $Quiet) {
    Write-Host "[ OK ] $Message" -ForegroundColor Green
  }
}

function Stop-ProcessTree([int]$ProcessId, [string]$Label) {
  $existing = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  if (-not $existing) {
    return $false
  }

  Write-Info "Stopping $Label (PID=$ProcessId)"
  & taskkill.exe /PID $ProcessId /T /F *> $null
  Start-Sleep -Milliseconds 300
  return $true
}

function Get-MatchingProjectProcesses {
  $backendLower = $BackendDir.ToLowerInvariant()
  $frontendLower = $FrontendDir.ToLowerInvariant()

  $processes = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.ProcessId -ne $PID
  }

  foreach ($process in $processes) {
    $commandLine = $process.CommandLine.ToLowerInvariant()
    $processName = $process.Name.ToLowerInvariant()

    $isBackendMatch =
      $commandLine.Contains($backendLower) -and (
        $commandLine.Contains('run.py') -or
        $commandLine.Contains('uvicorn') -or
        $commandLine.Contains('start-backend.ps1') -or
        $processName -eq 'python.exe' -or
        $processName -eq 'uvicorn.exe' -or
        $processName -eq 'powershell.exe' -or
        $processName -eq 'pwsh.exe' -or
        $processName -eq 'cmd.exe'
      )

    $isFrontendMatch =
      $commandLine.Contains($frontendLower) -and (
        $commandLine.Contains('npm run dev') -or
        $commandLine.Contains('npm run tauri:dev') -or
        $commandLine.Contains('vite') -or
        $commandLine.Contains('tauri') -or
        $commandLine.Contains('start-frontend.ps1') -or
        $processName -eq 'node.exe' -or
        $processName -eq 'powershell.exe' -or
        $processName -eq 'pwsh.exe' -or
        $processName -eq 'cmd.exe'
      )

    if ($isBackendMatch -or $isFrontendMatch) {
      $process
    }
  }
}

Write-Step 'Stopping development environment processes'

$stoppedAny = $false
$trackedPids = New-Object System.Collections.Generic.List[int]

if (Test-Path -LiteralPath $ProcessStatePath) {
  try {
    $state = Get-Content -LiteralPath $ProcessStatePath -Raw | ConvertFrom-Json
    foreach ($field in @('backend_shell_pid', 'frontend_shell_pid')) {
      if ($null -ne $state.$field) {
        [void]$trackedPids.Add([int]$state.$field)
      }
    }
  } catch {
    Write-WarnMessage 'Could not read the process state file. Falling back to process scan.'
  }
}

foreach ($pidValue in $trackedPids | Select-Object -Unique) {
  if ($pidValue -eq $PID) {
    continue
  }

  if (Stop-ProcessTree -ProcessId $pidValue -Label 'tracked launcher window') {
    $stoppedAny = $true
  }
}

$matchedProcesses = Get-MatchingProjectProcesses | Sort-Object ProcessId -Unique
foreach ($process in $matchedProcesses) {
  if ($process.ProcessId -eq $PID) {
    continue
  }

  if (Stop-ProcessTree -ProcessId ([int]$process.ProcessId) -Label $process.Name) {
    $stoppedAny = $true
  }
}

if (Test-Path -LiteralPath $ProcessStatePath) {
  Remove-Item -LiteralPath $ProcessStatePath -Force
}

if ($stoppedAny) {
  Write-Success 'Development environment processes were stopped'
} elseif (-not $Quiet) {
  Write-Info 'No matching development processes were found'
}
