# PowerShell script to test connection to the Hive Mind backend

param (
    [Parameter(Mandatory=$false)]
    [string]$Url = "http://localhost:5000"
)

Write-Host "Testing connection to Hive Mind backend..." -ForegroundColor Cyan

# Run the Python script
python test-connection.py --url $Url

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nConnection successful!" -ForegroundColor Green
    Write-Host "You can now connect VS Code to this backend using:" -ForegroundColor Green
    Write-Host "  1. Open VS Code with a Git repository" -ForegroundColor Cyan
    Write-Host "  2. Press Ctrl+Shift+P and type 'Hive Mind: Connect to Custom Backend URL'" -ForegroundColor Cyan
    Write-Host "  3. Enter the URL: $Url" -ForegroundColor Cyan
} else {
    Write-Host "`nConnection failed!" -ForegroundColor Red
    Write-Host "Please check that:" -ForegroundColor Yellow
    Write-Host "  • The backend is running: docker-compose up -d hive-mind-backend" -ForegroundColor Yellow
    Write-Host "  • The URL is correct: $Url" -ForegroundColor Yellow
    Write-Host "  • No firewall is blocking the connection" -ForegroundColor Yellow
    Write-Host "  • If using a remote server, ensure it's listening on 0.0.0.0 (all interfaces)" -ForegroundColor Yellow
} 