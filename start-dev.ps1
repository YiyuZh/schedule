[CmdletBinding()]
param(
  [switch]$ForceBackendInstall,
  [switch]$ForceFrontendInstall,
  [switch]$ForceWeb
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot 'schedule_backend'
$FrontendDir = Join-Path $ProjectRoot 'schedule_frontend'
$ScriptsDir = Join-Path $ProjectRoot 'scripts'
$BackendVenvDir = Join-Path $BackendDir '.venv'
$BackendPython = Join-Path $BackendVenvDir 'Scripts\python.exe'
$BackendRequirements = Join-Path $BackendDir 'requirements.txt'
$BackendRequirementStamp = Join-Path $BackendVenvDir '.requirements.sha256'
$FrontendPackageJson = Join-Path $FrontendDir 'package.json'
$FrontendPackageLock = Join-Path $FrontendDir 'package-lock.json'
$FrontendInstallStamp = Join-Path $FrontendDir '.npm-install.sha256'
$HealthUrl = 'http://127.0.0.1:8000/api/health'
$ProcessStatePath = Join-Path $ProjectRoot '.schedule-dev-processes.json'
$BackendLauncherScript = Join-Path $ScriptsDir 'start-backend.ps1'
$FrontendLauncherScript = Join-Path $ScriptsDir 'start-frontend.ps1'
$StopScript = Join-Path $ProjectRoot 'stop-dev.ps1'

function Write-Step([string]$Message) {
  Write-Host "[STEP] $Message" -ForegroundColor Cyan
}

function Write-Info([string]$Message) {
  Write-Host "[INFO] $Message" -ForegroundColor Gray
}

function Write-Success([string]$Message) {
  Write-Host "[ OK ] $Message" -ForegroundColor Green
}

function Write-WarnMessage([string]$Message) {
  Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Fail([string]$Message) {
  Write-Host "[FAIL] $Message" -ForegroundColor Red
  exit 1
}

function Assert-PathExists([string]$Path, [string]$Description) {
  if (-not (Test-Path -LiteralPath $Path)) {
    Fail "$Description not found: $Path"
  }
}

function Get-FileSha256([string]$Path) {
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Get-CombinedFrontendHash {
  $parts = @()

  if (Test-Path -LiteralPath $FrontendPackageJson) {
    $parts += Get-FileSha256 -Path $FrontendPackageJson
  }

  if (Test-Path -LiteralPath $FrontendPackageLock) {
    $parts += Get-FileSha256 -Path $FrontendPackageLock
  }

  return ($parts -join '|')
}

function Get-PythonLauncher {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    return [pscustomobject]@{
      Path = $py.Source
      Args = @('-3')
      Label = 'py -3'
    }
  }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return [pscustomobject]@{
      Path = $python.Source
      Args = @()
      Label = 'python'
    }
  }

  Fail 'Python was not found. Please install Python 3.11+ first.'
}

function Get-NodeAndNpm {
  $node = Get-Command node -ErrorAction SilentlyContinue
  if (-not $node) {
    Fail 'Node.js was not found. Please install Node.js 18+ first.'
  }

  $npm = Get-Command npm -ErrorAction SilentlyContinue
  if (-not $npm) {
    Fail 'npm was not found. Please check your Node.js installation.'
  }

  return [pscustomobject]@{
    Node = $node.Source
    Npm = $npm.Source
  }
}

function Ensure-BackendEnvironment {
  Write-Step 'Checking Python'
  $pythonLauncher = Get-PythonLauncher
  Write-Info "Using $($pythonLauncher.Label)"

  if (-not (Test-Path -LiteralPath $BackendPython)) {
    Write-Step 'Creating backend virtual environment'
    & $pythonLauncher.Path @($pythonLauncher.Args + @('-m', 'venv', $BackendVenvDir))
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $BackendPython)) {
      Fail 'Failed to create backend virtual environment.'
    }
    Write-Success 'Backend virtual environment created'
  } else {
    Write-Success 'Backend virtual environment already exists'
  }

  $needInstall = $ForceBackendInstall.IsPresent
  $requirementHash = Get-FileSha256 -Path $BackendRequirements

  if (-not $needInstall) {
    if (-not (Test-Path -LiteralPath $BackendRequirementStamp)) {
      $needInstall = $true
    } else {
      $savedHash = (Get-Content -LiteralPath $BackendRequirementStamp -Raw).Trim()
      if ($savedHash -ne $requirementHash) {
        $needInstall = $true
      }
    }
  }

  if (-not $needInstall) {
    & $BackendPython -c "import fastapi, uvicorn, sqlalchemy, pydantic, jsonschema" *> $null
    if ($LASTEXITCODE -ne 0) {
      $needInstall = $true
    }
  }

  if ($needInstall) {
    Write-Step 'Installing backend dependencies'
    Push-Location $BackendDir
    try {
      & $BackendPython -m pip install --upgrade pip | Out-Host
      if ($LASTEXITCODE -ne 0) {
        Fail 'Failed to upgrade pip.'
      }

      & $BackendPython -m pip install -r $BackendRequirements | Out-Host
      if ($LASTEXITCODE -ne 0) {
        Fail 'Failed to install backend dependencies.'
      }
    } finally {
      Pop-Location
    }

    Set-Content -LiteralPath $BackendRequirementStamp -Value $requirementHash -Encoding UTF8
    Write-Success 'Backend dependencies are ready'
  } else {
    Write-Success 'Backend dependencies are already installed'
  }
}

function Ensure-FrontendEnvironment {
  Write-Step 'Checking Node.js'
  $nodeTools = Get-NodeAndNpm
  Write-Info "Node: $($nodeTools.Node)"
  Write-Info "npm:  $($nodeTools.Npm)"

  $needInstall = $ForceFrontendInstall.IsPresent
  $frontendHash = Get-CombinedFrontendHash
  $nodeModulesDir = Join-Path $FrontendDir 'node_modules'

  if (-not $needInstall) {
    if (-not (Test-Path -LiteralPath $nodeModulesDir)) {
      $needInstall = $true
    } elseif (-not (Test-Path -LiteralPath (Join-Path $nodeModulesDir 'vue'))) {
      $needInstall = $true
    } elseif (-not (Test-Path -LiteralPath $FrontendInstallStamp)) {
      $needInstall = $true
    } else {
      $savedHash = (Get-Content -LiteralPath $FrontendInstallStamp -Raw).Trim()
      if ($savedHash -ne $frontendHash) {
        $needInstall = $true
      }
    }
  }

  if ($needInstall) {
    Write-Step 'Installing frontend dependencies with npm install'
    Push-Location $FrontendDir
    try {
      & $nodeTools.Npm 'install' | Out-Host
      if ($LASTEXITCODE -ne 0) {
        Fail 'Failed to install frontend dependencies.'
      }
    } finally {
      Pop-Location
    }

    Set-Content -LiteralPath $FrontendInstallStamp -Value $frontendHash -Encoding UTF8
    Write-Success 'Frontend dependencies are ready'
  } else {
    Write-Success 'Frontend dependencies are already installed'
  }

  return $nodeTools
}

function Get-FrontendMode([string]$FrontendPath, [bool]$PreferWeb) {
  if ($PreferWeb) {
    return @{
      Mode = 'Web'
      Reason = 'Web mode was forced by parameter.'
    }
  }

  $reasons = New-Object System.Collections.Generic.List[string]
  $cargo = Get-Command cargo -ErrorAction SilentlyContinue
  $rustc = Get-Command rustc -ErrorAction SilentlyContinue
  $cargoFallback = Join-Path $env:USERPROFILE '.cargo\bin\cargo.exe'
  $rustcFallback = Join-Path $env:USERPROFILE '.cargo\bin\rustc.exe'
  $tauriCli = Join-Path $FrontendPath 'node_modules\.bin\tauri.cmd'
  $tauriConfig = Join-Path $FrontendPath 'src-tauri\tauri.conf.json'

  if (-not $cargo -and -not (Test-Path -LiteralPath $cargoFallback)) {
    $reasons.Add('cargo was not found')
  }
  if (-not $rustc -and -not (Test-Path -LiteralPath $rustcFallback)) {
    $reasons.Add('rustc was not found')
  }
  if (-not (Test-Path -LiteralPath $tauriCli)) {
    $reasons.Add('local Tauri CLI was not found')
  }
  if (-not (Test-Path -LiteralPath $tauriConfig)) {
    $reasons.Add('src-tauri\\tauri.conf.json is missing')
  }

  if ($reasons.Count -eq 0) {
    return @{
      Mode = 'Tauri'
      Reason = 'Rust and Tauri development requirements were detected.'
    }
  }

  return @{
    Mode = 'Web'
    Reason = ($reasons -join '; ')
  }
}

function Wait-BackendHealthy([string]$Url, [int]$TimeoutSeconds, [int]$BackendShellPid) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

  while ((Get-Date) -lt $deadline) {
    $backendShell = Get-Process -Id $BackendShellPid -ErrorAction SilentlyContinue
    if (-not $backendShell) {
      Fail 'The backend window exited before the health check succeeded. Check the Schedule Backend window.'
    }

    try {
      $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
        Write-Success 'Backend health check passed'
        return
      }
    } catch {
      Start-Sleep -Seconds 1
    }
  }

  & $StopScript -Quiet | Out-Null
  Fail "Backend health check timed out: $Url"
}

function Save-ProcessState([hashtable]$State) {
  $json = $State | ConvertTo-Json -Depth 4
  Set-Content -LiteralPath $ProcessStatePath -Value $json -Encoding UTF8
}

Assert-PathExists -Path $BackendDir -Description 'Backend directory schedule_backend'
Assert-PathExists -Path $FrontendDir -Description 'Frontend directory schedule_frontend'
Assert-PathExists -Path $ScriptsDir -Description 'Scripts directory'
Assert-PathExists -Path $BackendLauncherScript -Description 'Backend launcher script'
Assert-PathExists -Path $FrontendLauncherScript -Description 'Frontend launcher script'
Assert-PathExists -Path $BackendRequirements -Description 'Backend requirements.txt'
Assert-PathExists -Path $FrontendPackageJson -Description 'Frontend package.json'

Write-Step 'Cleaning previous development processes'
& $StopScript -Quiet | Out-Null

Ensure-BackendEnvironment
$nodeTools = Ensure-FrontendEnvironment
$frontendMode = Get-FrontendMode -FrontendPath $FrontendDir -PreferWeb:$ForceWeb.IsPresent

if ($frontendMode.Mode -eq 'Tauri') {
  Write-Step 'Starting frontend in Tauri mode'
  Write-Info $frontendMode.Reason
} else {
  Write-Step 'Starting frontend in Web fallback mode'
  Write-WarnMessage $frontendMode.Reason
}

Write-Step 'Starting backend'
$backendShell = Start-Process -FilePath 'powershell.exe' `
  -WorkingDirectory $BackendDir `
  -ArgumentList @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $BackendLauncherScript,
    '-ProjectRoot', $ProjectRoot,
    '-VenvPython', $BackendPython
  ) `
  -PassThru

Write-Info "Backend window PID: $($backendShell.Id)"
Write-Step 'Waiting for backend health check'
Wait-BackendHealthy -Url $HealthUrl -TimeoutSeconds 60 -BackendShellPid $backendShell.Id

Write-Step 'Starting frontend'
$frontendShell = Start-Process -FilePath 'powershell.exe' `
  -WorkingDirectory $FrontendDir `
  -ArgumentList @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $FrontendLauncherScript,
    '-ProjectRoot', $ProjectRoot,
    '-FrontendMode', $frontendMode.Mode,
    '-NpmCommand', $nodeTools.Npm
  ) `
  -PassThru

Write-Info "Frontend window PID: $($frontendShell.Id)"

Save-ProcessState @{
  started_at = (Get-Date).ToString('s')
  project_root = $ProjectRoot
  backend_shell_pid = $backendShell.Id
  frontend_shell_pid = $frontendShell.Id
  frontend_mode = $frontendMode.Mode
  backend_url = 'http://127.0.0.1:8000'
  frontend_url = if ($frontendMode.Mode -eq 'Tauri') { 'Tauri Desktop Window' } else { 'http://127.0.0.1:1420' }
}

Write-Success 'Development environment started'
Write-Host ''
Write-Host 'Windows started:' -ForegroundColor Green
Write-Host '  - Schedule Backend' -ForegroundColor Green
Write-Host "  - Schedule Frontend ($($frontendMode.Mode))" -ForegroundColor Green
Write-Host ''
Write-Host 'Use stop-dev.bat or stop-dev.ps1 to stop the environment.' -ForegroundColor Yellow
