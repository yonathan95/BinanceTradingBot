# PowerShell script to test VS Code control

Write-Host "Testing if the Hive Mind backend can control VS Code..." -ForegroundColor Cyan

# Check if backend is running
try {
    $backendCheck = Invoke-RestMethod -Uri "http://localhost:5000/" -Method Get -ErrorAction Stop
    Write-Host "Backend is running at http://localhost:5000" -ForegroundColor Green
} catch {
    Write-Host "Backend is not running. Starting the backend..." -ForegroundColor Yellow
    
    # Try to start the backend
    Start-Process -FilePath "docker-compose" -ArgumentList "up -d hive-mind-backend" -NoNewWindow -Wait
    
    # Wait for backend to start
    Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Run the Python test script
Write-Host "`nRunning VS Code control test..." -ForegroundColor Cyan
python test-vscode-control.py

Write-Host "`nTest completed!" -ForegroundColor Cyan
Write-Host "If the test was successful, your VS Code branch should have changed." -ForegroundColor Cyan
Write-Host "If not, make sure:" -ForegroundColor Yellow
Write-Host "1. VS Code is running with the Hive Mind extension installed" -ForegroundColor Yellow
Write-Host "2. The extension is connected to the backend" -ForegroundColor Yellow
Write-Host "3. Your Git repository has the target branches (main and develop)" -ForegroundColor Yellow 