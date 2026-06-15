param(
    [ValidateSet("onedir", "onefile", "both")]
    [string]$Mode = "onedir"
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    throw $Message
}

function Get-PythonVersion {
    param([string]$PythonExe)
    $code = "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
    return (& $PythonExe -c $code).Trim()
}

function Test-PythonForBuild {
    param([string]$PythonExe)

    if (-not (Test-Path $PythonExe)) {
        return $false
    }

    try {
        $version = Get-PythonVersion $PythonExe
        $parts = $version.Split(".")
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        if ($major -ne 3) {
            return $false
        }
        if ($minor -lt 10 -or $minor -gt 13) {
            return $false
        }
        return $true
    } catch {
        return $false
    }
}

function Find-BasePython {
    if ($env:HUNTOVERLAY_PYTHON -and (Test-PythonForBuild $env:HUNTOVERLAY_PYTHON)) {
        return $env:HUNTOVERLAY_PYTHON
    }

    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            $candidate = (& py -3.12 -c "import sys; print(sys.executable)").Trim()
            if (Test-PythonForBuild $candidate) {
                return $candidate
            }
        } catch {
            # Continue to other discovery paths.
        }
    }

    $miseRoot = Join-Path $env:LOCALAPPDATA "mise\installs\python"
    if (Test-Path $miseRoot) {
        $miseCandidate = Get-ChildItem $miseRoot -Directory -Filter "3.12*" |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "python.exe" } |
            Where-Object { Test-PythonForBuild $_ } |
            Select-Object -First 1
        if ($miseCandidate) {
            return $miseCandidate
        }
    }

    $pythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCmd -and (Test-PythonForBuild $pythonCmd.Source)) {
        return $pythonCmd.Source
    }

    Fail "未找到适合打包的 Python。建议安装 Python 3.12，或设置 HUNTOVERLAY_PYTHON 指向 python.exe。"
}

if ($env:OS -ne "Windows_NT") {
    Fail "这个脚本只能在 Windows 环境中使用。"
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Step "检查项目文件"
$requiredFiles = @("HuntOverlay.py", "data.json", "poiData.json", "myicon.ico")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path (Join-Path $Root $file))) {
        Fail "缺少必要文件：$file"
    }
}

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-PythonForBuild $VenvPython)) {
    Write-Step "创建虚拟环境"
    $BasePython = Find-BasePython
    $BaseVersion = Get-PythonVersion $BasePython
    Write-Host "使用 Python：$BasePython ($BaseVersion)"
    & $BasePython -m venv (Join-Path $Root ".venv")
} else {
    $VenvVersion = Get-PythonVersion $VenvPython
    Write-Step "复用虚拟环境 Python $VenvVersion"
}

if (-not (Test-PythonForBuild $VenvPython)) {
    Fail "虚拟环境创建失败：$VenvPython"
}

Write-Step "安装/更新打包依赖"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install PySide6 pyinstaller

Write-Step "确认 PyInstaller"
& $VenvPython -m PyInstaller --version

$commonArgs = @(
    "--noconfirm",
    "--windowed",
    "--name", "HuntOverlay",
    "--icon", "myicon.ico",
    "--add-data", "data.json;.",
    "--add-data", "poiData.json;.",
    "--add-data", "myicon.ico;.",
    "HuntOverlay.py"
)

function Invoke-Build {
    param([ValidateSet("onedir", "onefile")][string]$BuildMode)

    Write-Step "开始构建 $BuildMode"
    $modeArg = if ($BuildMode -eq "onefile") { "--onefile" } else { "--onedir" }
    & $VenvPython -m PyInstaller $modeArg @commonArgs
}

if ($Mode -eq "both") {
    Invoke-Build "onedir"
    Invoke-Build "onefile"
} else {
    Invoke-Build $Mode
}

Write-Step "构建产物"
if ($Mode -eq "onedir") {
    Write-Host "目录版：dist\HuntOverlay\HuntOverlay.exe" -ForegroundColor Green
} elseif ($Mode -eq "onefile") {
    Write-Host "单文件版：dist\HuntOverlay.exe" -ForegroundColor Green
} else {
    Write-Host "目录版：dist\HuntOverlay\HuntOverlay.exe" -ForegroundColor Green
    Write-Host "单文件版：dist\HuntOverlay.exe" -ForegroundColor Green
}

Write-Host ""
Write-Host "建议先不开游戏，直接运行目录版确认中文界面和配置目录生成正常。" -ForegroundColor Yellow
