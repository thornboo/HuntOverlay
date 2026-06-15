param(
    [ValidateSet("onedir", "onefile", "both")]
    [string]$Mode = "onedir",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

# Python minor versions PyInstaller is known to support for this project.
$SupportedMinors = @(10, 11, 12, 13)

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
        if ($SupportedMinors -notcontains $minor) {
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

    # Prefer newer interpreters first.
    $preferred = $SupportedMinors | Sort-Object -Descending

    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        foreach ($minor in $preferred) {
            try {
                $candidate = (& py "-3.$minor" -c "import sys; print(sys.executable)").Trim()
                if (Test-PythonForBuild $candidate) {
                    return $candidate
                }
            } catch {
                # Version not installed under the launcher; try the next one.
            }
        }
    }

    $miseRoot = Join-Path $env:LOCALAPPDATA "mise\installs\python"
    if (Test-Path $miseRoot) {
        foreach ($minor in $preferred) {
            $miseCandidate = Get-ChildItem $miseRoot -Directory -Filter "3.$minor*" |
                Sort-Object Name -Descending |
                ForEach-Object { Join-Path $_.FullName "python.exe" } |
                Where-Object { Test-PythonForBuild $_ } |
                Select-Object -First 1
            if ($miseCandidate) {
                return $miseCandidate
            }
        }
    }

    $pythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCmd -and (Test-PythonForBuild $pythonCmd.Source)) {
        return $pythonCmd.Source
    }

    Fail "未找到适合打包的 Python（需要 3.10 - 3.13）。建议安装 Python 3.12，或设置 HUNTOVERLAY_PYTHON 指向 python.exe。"
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
if ($LASTEXITCODE -ne 0) { Fail "升级 pip 失败（退出码 $LASTEXITCODE）。请检查网络或代理设置。" }
& $VenvPython -m pip install "PySide6>=6.6,<6.9" "pyinstaller>=6.3,<7"
if ($LASTEXITCODE -ne 0) { Fail "安装 PySide6 / PyInstaller 失败（退出码 $LASTEXITCODE）。请检查网络或代理设置。" }

Write-Step "确认 PyInstaller"
& $VenvPython -m PyInstaller --version

if ($Clean) {
    Write-Step "清理旧的构建缓存"
    foreach ($dir in @("build", "dist")) {
        $target = Join-Path $Root $dir
        if (Test-Path $target) {
            Remove-Item $target -Recurse -Force
            Write-Host "已删除 $dir\"
        }
    }
    Get-ChildItem $Root -Filter "*.spec" | Remove-Item -Force -ErrorAction SilentlyContinue
}

$commonArgs = @(
    "--noconfirm",
    "--windowed",
    "--icon", "myicon.ico",
    "--add-data", "data.json;.",
    "--add-data", "poiData.json;.",
    "--add-data", "myicon.ico;.",
    "HuntOverlay.py"
)

function Invoke-Build {
    param([ValidateSet("onedir", "onefile")][string]$BuildMode)

    # Distinct names so onedir and onefile products never collide under dist\.
    $name = if ($BuildMode -eq "onefile") { "HuntOverlay-portable" } else { "HuntOverlay" }
    $modeArg = if ($BuildMode -eq "onefile") { "--onefile" } else { "--onedir" }

    Write-Step "开始构建 $BuildMode（$name）"
    & $VenvPython -m PyInstaller $modeArg "--name" $name @commonArgs
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller 构建失败（$BuildMode，退出码 $LASTEXITCODE）。" }
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
    Write-Host "单文件版：dist\HuntOverlay-portable.exe" -ForegroundColor Green
} else {
    Write-Host "目录版：dist\HuntOverlay\HuntOverlay.exe" -ForegroundColor Green
    Write-Host "单文件版：dist\HuntOverlay-portable.exe" -ForegroundColor Green
}

Write-Host ""
Write-Host "建议先不开游戏，直接运行目录版确认中文界面和配置目录生成正常。" -ForegroundColor Yellow
