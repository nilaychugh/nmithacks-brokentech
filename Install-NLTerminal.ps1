# Installation script for Natural Language Terminal

# Ensure we have administrator rights
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "You need to run this script as an Administrator!"
    break
}

$ModuleName = "NLTerminal"
$ModulePath = "$env:ProgramFiles\WindowsPowerShell\Modules\$ModuleName"

# Create module directory if it doesn't exist
if (!(Test-Path -Path $ModulePath)) {
    New-Item -ItemType Directory -Path $ModulePath -Force
    Write-Host "Created module directory: $ModulePath" -ForegroundColor Green
}

# Copy module files
Copy-Item -Path ".\NLTerminal.psm1" -Destination "$ModulePath\$ModuleName.psm1" -Force
Copy-Item -Path ".\terminal_controller.py" -Destination "$ModulePath\terminal_controller.py" -Force

# Create module manifest
$ManifestParams = @{
    Path              = "$ModulePath\$ModuleName.psd1"
    RootModule        = "$ModuleName.psm1"
    ModuleVersion     = "1.0.0"
    Author            = "Your Name"
    Description       = "Natural Language Terminal Controller for PowerShell"
    PowerShellVersion = "5.1"
    FunctionsToExport = @(
        "Start-TerminalServer", 
        "Stop-TerminalServer", 
        "Invoke-TerminalCommand", 
        "Invoke-NaturalLanguageCommand", 
        "Start-NaturalLanguageShell"
    )
    RequiredModules   = @()
}

New-ModuleManifest @ManifestParams

# Install required Python packages
Write-Host "Installing required Python packages..." -ForegroundColor Cyan
python -m pip install fastapi uvicorn psutil requests

Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "To use the module, run:" -ForegroundColor Yellow
Write-Host "Import-Module $ModuleName" -ForegroundColor Yellow
Write-Host "Start-NaturalLanguageShell" -ForegroundColor Yellow