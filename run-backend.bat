@echo off
echo Building and starting Hive Mind backend services...

REM Check if Docker is running
docker info > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Docker is not running. Please start Docker Desktop and try again.
    goto :end
)

REM Clean up existing containers and volumes
echo Cleaning up any existing containers...
docker-compose down
docker volume prune -f

REM Check if required directories exist
if not exist "hive-mind\docker" (
    echo Error: Required directory "hive-mind\docker" not found.
    echo Please make sure you are running this script from the correct location.
    goto :end
)

if not exist "hive-mind\control-plane" (
    echo Error: Required directory "hive-mind\control-plane" not found.
    echo Please make sure you are running this script from the correct location.
    goto :end
)

if not exist "hive-mind\cost-domain" (
    echo Error: Required directory "hive-mind\cost-domain" not found.
    echo Creating directory...
    mkdir "hive-mind\cost-domain"
)

if not exist "hive-mind\docker\Dockerfile.backend" (
    echo Creating Dockerfile.backend...
    echo FROM python:3.9-slim > "hive-mind\docker\Dockerfile.backend"
    echo. >> "hive-mind\docker\Dockerfile.backend"
    echo WORKDIR /app >> "hive-mind\docker\Dockerfile.backend"
    echo. >> "hive-mind\docker\Dockerfile.backend"
    echo # Install dependencies >> "hive-mind\docker\Dockerfile.backend"
    echo COPY control-plane/requirements.txt . >> "hive-mind\docker\Dockerfile.backend"
    echo RUN pip install --no-cache-dir -r requirements.txt >> "hive-mind\docker\Dockerfile.backend"
    echo. >> "hive-mind\docker\Dockerfile.backend"
    echo # Copy application code >> "hive-mind\docker\Dockerfile.backend"
    echo COPY . . >> "hive-mind\docker\Dockerfile.backend"
    echo. >> "hive-mind\docker\Dockerfile.backend"
    echo # Expose the port for external access >> "hive-mind\docker\Dockerfile.backend"
    echo EXPOSE 5000 >> "hive-mind\docker\Dockerfile.backend"
    echo. >> "hive-mind\docker\Dockerfile.backend"
    echo # Command to run the application >> "hive-mind\docker\Dockerfile.backend"
    echo CMD ["python", "control-plane/main.py"] >> "hive-mind\docker\Dockerfile.backend"
)

REM Create a properly encoded .env file
echo # API Configuration > .env
echo DATABASE_URL=postgresql+asyncpg://hivemind:hivemindpass@db:5432/hivemind >> .env
echo SECRET_KEY=hive_mind_super_secret_key_change_in_production >> .env
echo DEBUG=true >> .env
echo PYTHONPATH=/app >> .env
echo COST_DOMAIN_URL=http://cost-domain:8081 >> .env
echo # Docker Configuration >> .env
echo COMPOSE_CONVERT_WINDOWS_PATHS=1 >> .env

REM Make sure necessary files exist in cost-domain
if not exist "hive-mind\cost-domain\requirements.txt" (
    echo Creating requirements.txt in cost-domain...
    echo fastapi==0.95.0 > "hive-mind\cost-domain\requirements.txt"
    echo uvicorn==0.21.1 >> "hive-mind\cost-domain\requirements.txt"
    echo pydantic==1.10.7 >> "hive-mind\cost-domain\requirements.txt"
    echo prometheus-client==0.16.0 >> "hive-mind\cost-domain\requirements.txt"
    echo python-dotenv==1.0.0 >> "hive-mind\cost-domain\requirements.txt"
    echo httpx==0.24.1 >> "hive-mind\cost-domain\requirements.txt"
    echo aiofiles==23.1.0 >> "hive-mind\cost-domain\requirements.txt"
    echo orjson==3.8.12 >> "hive-mind\cost-domain\requirements.txt"
    echo tenacity==8.2.2 >> "hive-mind\cost-domain\requirements.txt"
)

if not exist "hive-mind\cost-domain\Dockerfile" (
    echo Creating Dockerfile in cost-domain...
    echo FROM python:3.9-slim > "hive-mind\cost-domain\Dockerfile"
    echo. >> "hive-mind\cost-domain\Dockerfile"
    echo WORKDIR /app >> "hive-mind\cost-domain\Dockerfile"
    echo. >> "hive-mind\cost-domain\Dockerfile"
    echo # Install dependencies >> "hive-mind\cost-domain\Dockerfile"
    echo COPY requirements.txt . >> "hive-mind\cost-domain\Dockerfile"
    echo RUN pip install --no-cache-dir -r requirements.txt >> "hive-mind\cost-domain\Dockerfile"
    echo. >> "hive-mind\cost-domain\Dockerfile"
    echo # Copy application code >> "hive-mind\cost-domain\Dockerfile"
    echo COPY . . >> "hive-mind\cost-domain\Dockerfile"
    echo. >> "hive-mind\cost-domain\Dockerfile"
    echo # Expose the port for external access >> "hive-mind\cost-domain\Dockerfile"
    echo EXPOSE 8081 >> "hive-mind\cost-domain\Dockerfile"
    echo. >> "hive-mind\cost-domain\Dockerfile"
    echo # Command to run the application >> "hive-mind\cost-domain\Dockerfile"
    echo CMD ["python", "app.py"] >> "hive-mind\cost-domain\Dockerfile"
)

if not exist "hive-mind\cost-domain\app.py" (
    echo Creating app.py in cost-domain...
    echo #!/usr/bin/env python3 > "hive-mind\cost-domain\app.py"
    echo """Cost Domain Service for Hive Mind""" >> "hive-mind\cost-domain\app.py"
    echo. >> "hive-mind\cost-domain\app.py"
    echo from fastapi import FastAPI >> "hive-mind\cost-domain\app.py"
    echo from fastapi.middleware.cors import CORSMiddleware >> "hive-mind\cost-domain\app.py"
    echo from prometheus_client import start_http_server >> "hive-mind\cost-domain\app.py"
    echo import logging >> "hive-mind\cost-domain\app.py"
    echo import os >> "hive-mind\cost-domain\app.py"
    echo. >> "hive-mind\cost-domain\app.py"
    echo # Configure logging >> "hive-mind\cost-domain\app.py"
    echo logging.basicConfig^( >> "hive-mind\cost-domain\app.py"
    echo     level=logging.INFO, >> "hive-mind\cost-domain\app.py"
    echo     format="%%^(asctime^)s [%%^(levelname^)s] %%^(message^)s", >> "hive-mind\cost-domain\app.py"
    echo     handlers=[logging.StreamHandler^(^)] >> "hive-mind\cost-domain\app.py"
    echo ^) >> "hive-mind\cost-domain\app.py"
    echo logger = logging.getLogger^(__name__^) >> "hive-mind\cost-domain\app.py"
    echo. >> "hive-mind\cost-domain\app.py"
    echo # Get port from environment variable or use default >> "hive-mind\cost-domain\app.py"
    echo PORT = int^(os.environ.get^("PORT", 8081^)^) >> "hive-mind\cost-domain\app.py"
    echo. >> "hive-mind\cost-domain\app.py"
    echo # FastAPI app >> "hive-mind\cost-domain\app.py"
    echo app = FastAPI^(title="Hive Mind Cost Domain Service"^) >> "hive-mind\cost-domain\app.py"
    echo. >> "hive-mind\cost-domain\app.py"
    echo # Add CORS middleware >> "hive-mind\cost-domain\app.py"
    echo app.add_middleware^( >> "hive-mind\cost-domain\app.py"
    echo     CORSMiddleware, >> "hive-mind\cost-domain\app.py"
    echo     allow_origins=["*"], >> "hive-mind\cost-domain\app.py"
    echo     allow_credentials=True, >> "hive-mind\cost-domain\app.py"
    echo     allow_methods=["*"], >> "hive-mind\cost-domain\app.py"
    echo     allow_headers=["*"], >> "hive-mind\cost-domain\app.py"
    echo ^) >> "hive-mind\cost-domain\app.py"
    echo. >> "hive-mind\cost-domain\app.py"
    echo @app.on_event^("startup"^) >> "hive-mind\cost-domain\app.py"
    echo async def startup_event^(^): >> "hive-mind\cost-domain\app.py"
    echo     # Start Prometheus metrics server on a different port to avoid conflicts >> "hive-mind\cost-domain\app.py"
    echo     metrics_port = PORT + 100  # Use PORT + 100 for metrics >> "hive-mind\cost-domain\app.py"
    echo     start_http_server^(metrics_port^) >> "hive-mind\cost-domain\app.py"
    echo     logger.info^(f"Started Prometheus metrics server on port {metrics_port}"^) >> "hive-mind\cost-domain\app.py"
    echo     logger.info^(f"API running on port {PORT}"^) >> "hive-mind\cost-domain\app.py"
    echo. >> "hive-mind\cost-domain\app.py"
    echo @app.get^("/"^) >> "hive-mind\cost-domain\app.py"
    echo async def root^(^): >> "hive-mind\cost-domain\app.py"
    echo     return {"status": "ok", "service": "cost-domain", "port": PORT} >> "hive-mind\cost-domain\app.py"
    echo. >> "hive-mind\cost-domain\app.py"
    echo if __name__ == "__main__": >> "hive-mind\cost-domain\app.py"
    echo     import uvicorn >> "hive-mind\cost-domain\app.py"
    echo     uvicorn.run^(app, host="0.0.0.0", port=PORT^) >> "hive-mind\cost-domain\app.py"
)

REM Make sure prometheus.yml exists
if not exist "hive-mind\docker\prometheus" (
    echo Creating prometheus directory...
    mkdir "hive-mind\docker\prometheus"
)

if not exist "hive-mind\docker\prometheus\prometheus.yml" (
    echo Creating prometheus.yml...
    echo global: > "hive-mind\docker\prometheus\prometheus.yml"
    echo   scrape_interval: 15s >> "hive-mind\docker\prometheus\prometheus.yml"
    echo   evaluation_interval: 15s >> "hive-mind\docker\prometheus\prometheus.yml"
    echo. >> "hive-mind\docker\prometheus\prometheus.yml"
    echo scrape_configs: >> "hive-mind\docker\prometheus\prometheus.yml"
    echo   - job_name: 'prometheus' >> "hive-mind\docker\prometheus\prometheus.yml"
    echo     static_configs: >> "hive-mind\docker\prometheus\prometheus.yml"
    echo       - targets: ['localhost:9090'] >> "hive-mind\docker\prometheus\prometheus.yml"
    echo. >> "hive-mind\docker\prometheus\prometheus.yml"
    echo   - job_name: 'control-plane' >> "hive-mind\docker\prometheus\prometheus.yml"
    echo     static_configs: >> "hive-mind\docker\prometheus\prometheus.yml"
    echo       - targets: ['control-plane:8000'] >> "hive-mind\docker\prometheus\prometheus.yml"
    echo. >> "hive-mind\docker\prometheus\prometheus.yml"
    echo   - job_name: 'cost-domain' >> "hive-mind\docker\prometheus\prometheus.yml"
    echo     static_configs: >> "hive-mind\docker\prometheus\prometheus.yml"
    echo       - targets: ['cost-domain:8181'] >> "hive-mind\docker\prometheus\prometheus.yml"
    echo. >> "hive-mind\docker\prometheus\prometheus.yml"
    echo   - job_name: 'hivemind-api' >> "hive-mind\docker\prometheus\prometheus.yml"
    echo     metrics_path: /metrics >> "hive-mind\docker\prometheus\prometheus.yml"
    echo     static_configs: >> "hive-mind\docker\prometheus\prometheus.yml"
    echo       - targets: ['api:5000'] >> "hive-mind\docker\prometheus\prometheus.yml"
)

REM Build the Docker images
echo Building Docker images...
docker-compose build

REM Start the services
echo Starting services...
docker-compose up -d

REM Check if containers started successfully
docker ps | findstr "hivemind-api" > nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to start containers. Check Docker logs:
    docker-compose logs
    goto :end
)

REM Wait for the database to be ready
echo Waiting for database to be ready...
timeout /t 30 /nobreak

REM Initialize the database (using non-interactive mode)
echo Initializing the database...
docker exec hivemind-api python control-plane/init_db.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to initialize database. Check container logs:
    docker logs hivemind-api
    goto :end
)

REM Populate the database with mock data (using non-interactive mode)
echo Populating the database with mock data...
docker exec hivemind-api python control-plane/init_mock_data.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to populate database. Container might be missing or having issues.
    docker logs hivemind-api --tail 50
    goto :end
)

:success
echo Hive Mind backend services are now running!
echo API available at: http://localhost:5000
echo Cost Domain API available at: http://localhost:8081
echo Grafana dashboard at: http://localhost:3000
echo Prometheus metrics at: http://localhost:9090

:end 