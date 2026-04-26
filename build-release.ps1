[CmdletBinding()]
param(
  [switch]$SkipTests,
  [switch]$ForceFrontendInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot 'schedule_backend'
$FrontendDir = Join-Path $ProjectRoot 'schedule_frontend'
$ReleaseDir = Join-Path $ProjectRoot 'release'
$BuildDir = Join-Path $ProjectRoot '.release-build'
$BackendVenvDir = Join-Path $BuildDir 'backend-venv'
$BackendPython = Join-Path $BackendVenvDir 'Scripts\python.exe'
$BackendDistDir = Join-Path $BuildDir 'backend-dist'
$BackendWorkDir = Join-Path $BuildDir 'backend-work'
$BackendSpecDir = Join-Path $BuildDir 'backend-spec'
$SidecarDir = Join-Path $FrontendDir 'src-tauri\binaries'
$BackendExe = Join-Path $BackendDistDir 'schedule-backend.exe'
$BackendRequirements = Join-Path $BackendDir 'requirements.txt'
$FrontendPackageJson = Join-Path $FrontendDir 'package.json'
$FrontendNodeModules = Join-Path $FrontendDir 'node_modules'

function Write-Step([string]$Message) {
  Write-Host "[STEP] $Message" -ForegroundColor Cyan
}

function Write-Success([string]$Message) {
  Write-Host "[ OK ] $Message" -ForegroundColor Green
}

function Fail([string]$Message) {
  Write-Host "[FAIL] $Message" -ForegroundColor Red
  exit 1
}

function Assert-Path([string]$Path, [string]$Label) {
  if (-not (Test-Path -LiteralPath $Path)) {
    Fail "$Label not found: $Path"
  }
}

function Get-CommandPath([string]$Name, [string]$InstallHint) {
  $command = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $command) {
    Fail "$Name was not found. $InstallHint"
  }
  return $command.Source
}

function Invoke-Checked([string]$FilePath, [string[]]$Arguments, [string]$WorkingDirectory) {
  Push-Location $WorkingDirectory
  try {
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
      Fail "Command failed: $FilePath $($Arguments -join ' ')"
    }
  } finally {
    Pop-Location
  }
}

function Get-PythonLauncher {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    return [pscustomobject]@{ Path = $py.Source; Args = @('-3') }
  }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return [pscustomobject]@{ Path = $python.Source; Args = @() }
  }
  Fail 'Python 3.11+ was not found. Install Python only on the build machine.'
}

function Get-RustHostTriple {
  $rustc = Get-CommandPath -Name 'rustc' -InstallHint 'Install Rust/MSVC on the build machine.'
  $info = & $rustc -vV
  $hostLine = $info | Where-Object { $_ -match '^host:\s+' } | Select-Object -First 1
  if (-not $hostLine) {
    return 'x86_64-pc-windows-msvc'
  }
  return ($hostLine -replace '^host:\s+', '').Trim()
}

Assert-Path -Path $BackendDir -Label 'Backend directory'
Assert-Path -Path $FrontendDir -Label 'Frontend directory'
Assert-Path -Path $BackendRequirements -Label 'Backend requirements.txt'
Assert-Path -Path $FrontendPackageJson -Label 'Frontend package.json'

Write-Step 'Checking build machine tools'
$pythonLauncher = Get-PythonLauncher
$npm = Get-CommandPath -Name 'npm' -InstallHint 'Install Node.js on the build machine.'
Get-CommandPath -Name 'node' -InstallHint 'Install Node.js on the build machine.' | Out-Null
Get-CommandPath -Name 'cargo' -InstallHint 'Install Rust/MSVC on the build machine.' | Out-Null
$rustHost = Get-RustHostTriple
Write-Success "Rust host: $rustHost"

New-Item -ItemType Directory -Force -Path $ReleaseDir, $BuildDir, $SidecarDir | Out-Null

if (-not $SkipTests.IsPresent) {
  Write-Step 'Running backend tests'
  Invoke-Checked -FilePath $pythonLauncher.Path -Arguments @($pythonLauncher.Args + @('-m', 'pytest', '-q')) -WorkingDirectory $BackendDir

  Write-Step 'Checking backend import'
  Invoke-Checked -FilePath $pythonLauncher.Path -Arguments @($pythonLauncher.Args + @('-c', 'from app.main import app; print(app.title)')) -WorkingDirectory $BackendDir
}

Write-Step 'Preparing backend PyInstaller environment'
if (-not (Test-Path -LiteralPath $BackendPython)) {
  Invoke-Checked -FilePath $pythonLauncher.Path -Arguments @($pythonLauncher.Args + @('-m', 'venv', $BackendVenvDir)) -WorkingDirectory $ProjectRoot
}

Invoke-Checked -FilePath $BackendPython -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip') -WorkingDirectory $BackendDir
Invoke-Checked -FilePath $BackendPython -Arguments @('-m', 'pip', 'install', '-r', $BackendRequirements, 'pyinstaller>=6,<7') -WorkingDirectory $BackendDir

Write-Step 'Building backend sidecar executable'
Invoke-Checked -FilePath $BackendPython -Arguments @(
  '-m', 'PyInstaller',
  '--noconfirm',
  '--clean',
  '--onefile',
  '--noconsole',
  '--name', 'schedule-backend',
  '--distpath', $BackendDistDir,
  '--workpath', $BackendWorkDir,
  '--specpath', $BackendSpecDir,
  '--paths', $BackendDir,
  (Join-Path $BackendDir 'run.py')
) -WorkingDirectory $BackendDir

Assert-Path -Path $BackendExe -Label 'PyInstaller backend executable'
$sidecarName = "schedule-backend-$rustHost.exe"
$sidecarPath = Join-Path $SidecarDir $sidecarName
Copy-Item -LiteralPath $BackendExe -Destination $sidecarPath -Force
Write-Success "Backend sidecar ready: $sidecarPath"

Write-Step 'Preparing frontend dependencies'
if ($ForceFrontendInstall.IsPresent -or -not (Test-Path -LiteralPath $FrontendNodeModules)) {
  Invoke-Checked -FilePath $npm -Arguments @('install') -WorkingDirectory $FrontendDir
}

if (-not $SkipTests.IsPresent) {
  Write-Step 'Running frontend tests'
  Invoke-Checked -FilePath $npm -Arguments @('test', '--', '--run') -WorkingDirectory $FrontendDir
}

Write-Step 'Building desktop frontend'
Invoke-Checked -FilePath $npm -Arguments @('run', 'build:desktop') -WorkingDirectory $FrontendDir

Write-Step 'Building Tauri NSIS installer'
Invoke-Checked -FilePath $npm -Arguments @('run', 'tauri:build') -WorkingDirectory $FrontendDir

$packageJson = Get-Content -LiteralPath $FrontendPackageJson -Raw | ConvertFrom-Json
$version = [string]$packageJson.version
$nsisDir = Join-Path $FrontendDir 'src-tauri\target\release\bundle\nsis'
$installer = Get-ChildItem -LiteralPath $nsisDir -Filter '*.exe' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $installer) {
  Fail "NSIS installer was not found in $nsisDir"
}

$releaseName = "Schedule_${version}_x64_setup.exe"
$releasePath = Join-Path $ReleaseDir $releaseName
Copy-Item -LiteralPath $installer.FullName -Destination $releasePath -Force

Write-Success "Release installer created: $releasePath"
Write-Host ''
Write-Host 'End users only need this installer. Python / Node.js / Rust are not required on user machines.' -ForegroundColor Green
