#requires -Version 5.1

[CmdletBinding()]
param(
    [switch]$InstallSystemDependencies,
    [switch]$RunDev
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$NodeTool = "node@24"
$RustTool = "rust@stable"
$PnpmTool = "npm:pnpm@11.17.0"
$RustToolchain = "stable-x86_64-pc-windows-msvc"
$WebView2ClientId = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
$WebView2BootstrapperUrl = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
$VsCodeSigningPcaUrl = "https://www.microsoft.com/pkiops/certs/Microsoft%20Windows%20Code%20Signing%20PCA%202024.crt"
$VsCodeSigningPcaSha256 = "FE229EFC927F6D77B738896752A21803A59736BAA17BF5BE9A50C72E219CBCD2"
$VsCodeSigningPcaThumbprint = "D30F05F637E605239C0070D1EA9860D434AC2A94"

function Write-Step {
    param([Parameter(Mandatory = $true)][string]$Message)

    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$Arguments = @()
    )

    Write-Step $Label
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable failed with exit code $LASTEXITCODE."
    }
}

function Invoke-CapturedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$Arguments = @()
    )

    $output = & $Executable @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        $output | ForEach-Object { Write-Host $_ }
        throw "$Executable failed with exit code $exitCode."
    }

    return ($output | Out-String).Trim()
}

function Get-VsCppInstallationPath {
    $programFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    if ([string]::IsNullOrWhiteSpace($programFilesX86)) {
        return $null
    }

    $vswhere = Join-Path $programFilesX86 "Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path -LiteralPath $vswhere)) {
        return $null
    }

    $installationPath = & $vswhere `
        -latest `
        -products "*" `
        -requires "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" `
        -property installationPath 2>$null

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($installationPath | Out-String))) {
        return $null
    }

    return (($installationPath | Select-Object -Last 1) | Out-String).Trim()
}

function Test-VsCodeSigningPca {
    $certificatePath = "Cert:\LocalMachine\CA\$VsCodeSigningPcaThumbprint"
    $certificate = Get-Item -LiteralPath $certificatePath -ErrorAction SilentlyContinue

    return (
        $null -ne $certificate -and
        $certificate.Subject -match "CN=Microsoft Windows Code Signing PCA 2024"
    )
}

function Install-VsCodeSigningPca {
    $certificatePath = Join-Path ([IO.Path]::GetTempPath()) "Microsoft-Windows-Code-Signing-PCA-2024.crt"

    try {
        Write-Step "Download the Microsoft Windows Code Signing PCA 2024 certificate"
        Invoke-WebRequest -Uri $VsCodeSigningPcaUrl -OutFile $certificatePath

        $fileHash = (Get-FileHash -LiteralPath $certificatePath -Algorithm SHA256).Hash
        $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($certificatePath)
        if (
            $fileHash -ne $VsCodeSigningPcaSha256 -or
            $certificate.Thumbprint -ne $VsCodeSigningPcaThumbprint -or
            $certificate.Subject -notmatch "CN=Microsoft Windows Code Signing PCA 2024"
        ) {
            throw "The downloaded Visual Studio code-signing certificate failed validation."
        }

        Invoke-CheckedCommand `
            -Label "Trust the Microsoft Windows Code Signing PCA 2024 certificate" `
            -Executable "certutil.exe" `
            -Arguments @("-addstore", "CA", $certificatePath)

        if (-not (Test-VsCodeSigningPca)) {
            throw "The Visual Studio code-signing certificate was not found after import."
        }
    }
    finally {
        if (Test-Path -LiteralPath $certificatePath) {
            Remove-Item -LiteralPath $certificatePath -Force
        }
    }
}

function Install-VsCppBuildTools {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        throw "winget.exe is required to install Visual Studio Build Tools automatically."
    }

    $override = "--wait --passive --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
    Invoke-CheckedCommand `
        -Label "Install Visual Studio 2022 Build Tools with Desktop development with C++" `
        -Executable $winget.Source `
        -Arguments @(
            "install",
            "--id", "Microsoft.VisualStudio.2022.BuildTools",
            "--exact",
            "--source", "winget",
            "--override", $override,
            "--accept-package-agreements",
            "--accept-source-agreements"
        )
}

function Get-WebView2Version {
    $registryPaths = @(
        "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$WebView2ClientId",
        "Registry::HKEY_CURRENT_USER\Software\Microsoft\EdgeUpdate\Clients\$WebView2ClientId"
    )

    foreach ($registryPath in $registryPaths) {
        $client = Get-ItemProperty -LiteralPath $registryPath -Name "pv" -ErrorAction SilentlyContinue
        if ($null -ne $client) {
            $version = [string]$client.pv
            if (-not [string]::IsNullOrWhiteSpace($version) -and $version -ne "0.0.0.0") {
                return $version
            }
        }
    }

    return $null
}

function Install-WebView2Runtime {
    $bootstrapper = Join-Path ([IO.Path]::GetTempPath()) "HuntOverlay-WebView2Setup.exe"

    try {
        Write-Step "Download the Microsoft WebView2 Evergreen Bootstrapper"
        Invoke-WebRequest -Uri $WebView2BootstrapperUrl -OutFile $bootstrapper

        $signature = Get-AuthenticodeSignature -FilePath $bootstrapper
        if (
            $signature.Status -ne "Valid" -or
            $null -eq $signature.SignerCertificate -or
            $signature.SignerCertificate.Subject -notmatch "O=Microsoft Corporation"
        ) {
            throw "The downloaded WebView2 bootstrapper does not have a valid Microsoft signature."
        }

        Write-Step "Install the Microsoft WebView2 Runtime"
        $process = Start-Process `
            -FilePath $bootstrapper `
            -ArgumentList @("/silent", "/install") `
            -Wait `
            -PassThru

        if ($process.ExitCode -ne 0) {
            throw "WebView2 installer failed with exit code $($process.ExitCode)."
        }
    }
    finally {
        if (Test-Path -LiteralPath $bootstrapper) {
            Remove-Item -LiteralPath $bootstrapper -Force
        }
    }
}

function Invoke-WithMiseNode {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $miseArguments = @("--no-config", "x", $NodeTool, $PnpmTool, "--") + $Arguments
    Invoke-CheckedCommand -Label $Label -Executable "mise" -Arguments $miseArguments
}

try {
    if ($env:OS -ne "Windows_NT") {
        throw "This script must run on the Windows test machine."
    }

    $architecture = if ([string]::IsNullOrWhiteSpace($env:PROCESSOR_ARCHITEW6432)) {
        $env:PROCESSOR_ARCHITECTURE
    }
    else {
        $env:PROCESSOR_ARCHITEW6432
    }

    if ($architecture -ne "AMD64") {
        throw "This validation script currently supports x64 Windows only. Detected: $architecture"
    }

    $mise = Get-Command mise.exe -ErrorAction SilentlyContinue
    if ($null -eq $mise) {
        throw "mise.exe was not found in PATH. Install or expose mise before running this script."
    }

    $projectRoot = $PSScriptRoot
    $packageJson = Join-Path $projectRoot "package.json"
    $cargoManifest = Join-Path $projectRoot "src-tauri\Cargo.toml"

    if (-not (Test-Path -LiteralPath $packageJson) -or -not (Test-Path -LiteralPath $cargoManifest)) {
        throw "The script is not inside a complete Tauri-PoC checkout: $projectRoot"
    }

    Write-Host "HuntOverlay Tauri PoC Windows bootstrap and build validation" -ForegroundColor Green
    Write-Host "Project: $projectRoot"
    Write-Host "Architecture: $architecture"
    Write-Host "mise: $($mise.Source)"

    $vsInstallationPath = Get-VsCppInstallationPath
    if ([string]::IsNullOrWhiteSpace($vsInstallationPath)) {
        if (-not $InstallSystemDependencies) {
            throw "Visual Studio C++ Build Tools were not detected. Re-run with -InstallSystemDependencies."
        }

        if (-not (Test-VsCodeSigningPca)) {
            Install-VsCodeSigningPca
        }

        Install-VsCppBuildTools
        $vsInstallationPath = Get-VsCppInstallationPath
        if ([string]::IsNullOrWhiteSpace($vsInstallationPath)) {
            throw "The C++ workload is still unavailable. Open Visual Studio Installer and add Desktop development with C++, then re-run this script."
        }
    }

    Write-Host "Visual Studio C++ tools: $vsInstallationPath"

    $webView2Version = Get-WebView2Version
    if ([string]::IsNullOrWhiteSpace($webView2Version)) {
        if (-not $InstallSystemDependencies) {
            throw "WebView2 Runtime was not detected. Re-run with -InstallSystemDependencies."
        }

        Install-WebView2Runtime
        $webView2Version = Get-WebView2Version
        if ([string]::IsNullOrWhiteSpace($webView2Version)) {
            throw "WebView2 installation finished, but its runtime registry entry is still unavailable."
        }
    }

    Write-Host "WebView2 Runtime: $webView2Version"

    $env:MISE_RUST_DEFAULT_HOST = "x86_64-pc-windows-msvc"
    Invoke-CheckedCommand `
        -Label "Install the temporary Node, Rust, and pnpm toolchain with mise" `
        -Executable $mise.Source `
        -Arguments @("--no-config", "-y", "install", $NodeTool, $RustTool, $PnpmTool)

    $cargoHome = if (-not [string]::IsNullOrWhiteSpace($env:CARGO_HOME)) {
        $env:CARGO_HOME
    }
    elseif (-not [string]::IsNullOrWhiteSpace($env:MISE_CARGO_HOME)) {
        $env:MISE_CARGO_HOME
    }
    else {
        Join-Path $env:USERPROFILE ".cargo"
    }

    $cargoBin = Join-Path $cargoHome "bin"
    if (-not (Test-Path -LiteralPath $cargoBin)) {
        throw "Rust was installed, but Cargo's bin directory was not found: $cargoBin"
    }

    $env:PATH = "$cargoBin;$env:PATH"
    $rustup = Join-Path $cargoBin "rustup.exe"
    if (-not (Test-Path -LiteralPath $rustup)) {
        throw "rustup.exe was not found after the mise Rust installation: $rustup"
    }

    Invoke-CheckedCommand `
        -Label "Ensure the x64 MSVC Rust toolchain is installed" `
        -Executable $rustup `
        -Arguments @("toolchain", "install", $RustToolchain, "--profile", "default")

    $env:RUSTUP_TOOLCHAIN = $RustToolchain

    $nodeVersion = Invoke-CapturedCommand `
        -Executable $mise.Source `
        -Arguments @("--no-config", "x", $NodeTool, $PnpmTool, "--", "node", "--version")
    if ($nodeVersion -notmatch "^v24\.") {
        throw "Expected Node 24, but mise returned: $nodeVersion"
    }

    $pnpmVersion = Invoke-CapturedCommand `
        -Executable $mise.Source `
        -Arguments @("--no-config", "x", $NodeTool, $PnpmTool, "--", "pnpm", "--version")
    if ($pnpmVersion -ne "11.17.0") {
        throw "Expected pnpm 11.17.0, but mise returned: $pnpmVersion"
    }

    $rustc = Join-Path $cargoBin "rustc.exe"
    $cargo = Join-Path $cargoBin "cargo.exe"
    $rustcDetails = Invoke-CapturedCommand -Executable $rustc -Arguments @("-vV")
    if ($rustcDetails -notmatch "(?m)^host: x86_64-pc-windows-msvc\r?$") {
        throw "Rust is not using the required MSVC host.`n$rustcDetails"
    }

    $cargoVersion = Invoke-CapturedCommand -Executable $cargo -Arguments @("--version")

    Write-Step "Validated toolchain"
    Write-Host "Node: $nodeVersion"
    Write-Host "pnpm: $pnpmVersion"
    Write-Host (($rustcDetails -split "\r?\n" | Where-Object { $_ -match "^(rustc|host:)" }) -join "`n")
    Write-Host "Cargo: $cargoVersion"

    Push-Location $projectRoot
    try {
        Invoke-WithMiseNode `
            -Label "Install frontend dependencies from pnpm-lock.yaml" `
            -Arguments @("pnpm", "install", "--frozen-lockfile")

        Invoke-WithMiseNode `
            -Label "Run the TypeScript check" `
            -Arguments @("pnpm", "check")

        Invoke-WithMiseNode `
            -Label "Verify overlay geometry against the current HuntOverlay defaults" `
            -Arguments @("pnpm", "check:geometry")

        Invoke-WithMiseNode `
            -Label "Build the Vite frontend" `
            -Arguments @("pnpm", "build")

        Invoke-CheckedCommand `
            -Label "Run Cargo check with Cargo.lock" `
            -Executable $cargo `
            -Arguments @("check", "--manifest-path", $cargoManifest, "--locked")

        Invoke-WithMiseNode `
            -Label "Build the Windows release executable without an installer bundle" `
            -Arguments @("pnpm", "tauri", "build", "--no-bundle", "--ci")

        $releaseExecutable = Join-Path $projectRoot "src-tauri\target\release\huntoverlay-tauri-poc.exe"
        if (-not (Test-Path -LiteralPath $releaseExecutable)) {
            throw "The release build completed, but the expected executable was not found: $releaseExecutable"
        }

        Write-Step "Windows compile validation passed"
        Write-Host "Executable: $releaseExecutable" -ForegroundColor Green

        if ($RunDev) {
            Invoke-WithMiseNode `
                -Label "Launch the Tauri development build; close the app to finish the script" `
                -Arguments @("pnpm", "tauri", "dev")
        }
        else {
            Write-Host "Run this script again with -RunDev for the interactive window validation."
        }
    }
    finally {
        Pop-Location
    }
}
catch {
    Write-Host ""
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
