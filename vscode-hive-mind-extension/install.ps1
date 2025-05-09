# PowerShell script to install the Hive Mind VS Code extension

# Determine VS Code extensions directory
$extensionsDir = "$env:USERPROFILE\.vscode\extensions"
$extensionName = "vscode-hive-mind-extension"
$extensionDir = "$extensionsDir\$extensionName"

# Determine current script directory
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path -Parent $scriptPath
$sourceDir = $scriptDir

Write-Host "Installing Hive Mind extension to VS Code..." -ForegroundColor Cyan

# Check if VS Code extensions directory exists
if (-not (Test-Path $extensionsDir)) {
    Write-Host "Creating VS Code extensions directory..." -ForegroundColor Yellow
    New-Item -Path $extensionsDir -ItemType Directory -Force | Out-Null
}

# Remove existing extension if it exists
if (Test-Path $extensionDir) {
    Write-Host "Removing existing Hive Mind extension..." -ForegroundColor Yellow
    Remove-Item -Path $extensionDir -Recurse -Force
}

# Create extension directory
Write-Host "Creating extension directory..." -ForegroundColor Yellow
New-Item -Path $extensionDir -ItemType Directory -Force | Out-Null

# Copy extension files
Write-Host "Copying extension files..." -ForegroundColor Yellow
Copy-Item -Path "$sourceDir\*" -Destination $extensionDir -Recurse -Exclude "install.ps1", "node_modules"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Set-Location -Path $extensionDir
npm install

Write-Host "`nHive Mind extension has been installed successfully!" -ForegroundColor Green
Write-Host "Please reload VS Code to activate the extension." -ForegroundColor Green
Write-Host "You can do this by pressing Ctrl+Shift+P and running 'Developer: Reload Window'" -ForegroundColor Cyan

# Return to the original directory
Set-Location -Path $scriptDir 