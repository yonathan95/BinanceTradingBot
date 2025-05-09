# PowerShell script to run Hive Mind backend in Docker

# Build and start the backend services
docker-compose up -d hive-mind-backend

Write-Host "Hive Mind backend is running on http://localhost:5000" -ForegroundColor Green
Write-Host "To view logs: docker-compose logs -f hive-mind-backend" -ForegroundColor Cyan
Write-Host "To stop: docker-compose down" -ForegroundColor Cyan 