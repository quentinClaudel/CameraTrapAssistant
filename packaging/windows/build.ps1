param(
    [switch]$SkipDependencyInstall,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$AppDir = Join-Path $ProjectRoot "CameraTrapAssistant"
$BuildVenv = Join-Path $ProjectRoot ".build-venv"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
$SpecFile = Join-Path $PSScriptRoot "CameraTrapAssistant.spec"
$InnoScript = Join-Path $PSScriptRoot "CameraTrapAssistant.iss"
$ArtifactsDir = Join-Path $PSScriptRoot "artifacts"

function Remove-GeneratedDirectory {
    param([Parameter(Mandatory)][string]$Path)

    $RootPrefix = [System.IO.Path]::GetFullPath($ProjectRoot).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar
    ) + [System.IO.Path]::DirectorySeparatorChar
    $Target = [System.IO.Path]::GetFullPath($Path)
    if (-not $Target.StartsWith($RootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a directory outside the project: $Target"
    }
    if (Test-Path -LiteralPath $Target) {
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
}

Push-Location $ProjectRoot
try {
    if (-not (Test-Path $BuildPython)) {
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
        if ($LASTEXITCODE -ne 0) {
            throw "Python 3.10 or newer is required to build the application."
        }
        python -m venv $BuildVenv
    }

    if (-not $SkipDependencyInstall) {
        & $BuildPython -m pip install --upgrade pip
        & $BuildPython -m pip install -r (Join-Path $AppDir "requirements.txt")
        & $BuildPython -m pip install "pyinstaller>=6,<7"
    }

    & $BuildPython -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed."
    }

    & $BuildPython -c "import sys; sys.path.insert(0, r'$($AppDir)\src'); from utils.model_manager import validate_models, format_model_problems; problems = validate_models(); print(format_model_problems(problems)) if problems else print('Model integrity checks passed.'); raise SystemExit(bool(problems))"
    if ($LASTEXITCODE -ne 0) {
        throw "Model integrity checks failed."
    }

    Remove-GeneratedDirectory (Join-Path $ProjectRoot "build")
    Remove-GeneratedDirectory (Join-Path $ProjectRoot "dist")
    & $BuildPython -m PyInstaller --clean --noconfirm $SpecFile
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed."
    }

    & $BuildPython -m pip freeze |
        Set-Content -Encoding ASCII (Join-Path $ProjectRoot "dist\CameraTrapAssistant\DEPENDENCIES.txt")

    $PackagedExe = Join-Path $ProjectRoot "dist\CameraTrapAssistant\CameraTrapAssistant.exe"
    $SmokeTest = Start-Process -FilePath $PackagedExe -ArgumentList "--smoke-test" -Wait -PassThru
    if ($SmokeTest.ExitCode -ne 0) {
        throw "The packaged application smoke test failed."
    }

    if (-not $SkipInstaller) {
        $Iscc = (Get-Command iscc.exe -ErrorAction SilentlyContinue).Source
        if (-not $Iscc) {
            $DefaultIscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
            if (Test-Path $DefaultIscc) {
                $Iscc = $DefaultIscc
            }
        }
        if (-not $Iscc) {
            throw "Inno Setup 6 was not found. Install it or use -SkipInstaller."
        }
        & $Iscc $InnoScript
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup failed."
        }

        $Installer = Get-ChildItem $ArtifactsDir -Filter "*.exe" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        $Hash = Get-FileHash -Algorithm SHA256 $Installer.FullName
        "$($Hash.Hash.ToLowerInvariant())  $($Installer.Name)" |
            Set-Content -Encoding ASCII (Join-Path $ArtifactsDir "SHA256SUMS.txt")
        Write-Host "Release installer: $($Installer.FullName)"
    }
}
finally {
    Pop-Location
}
