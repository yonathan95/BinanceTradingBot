.PHONY: install install-dev format lint test run clean docker-build docker-up docker-down

# Install main dependencies
install:
	pip install -e .

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Format code using black and isort
format:
	black hive_mind tests
	isort hive_mind tests

# Run linting
lint:
	flake8 hive_mind tests
	mypy hive_mind

# Run tests
test:
	pytest tests/

# Run tests with coverage
test-cov:
	pytest --cov=hive_mind tests/

# Run the API server
run:
	uvicorn hive_mind.control_plane.app:app --reload

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Move docker-compose.yml to the correct location
setup-docker:
	cp docker-compose.yml ../docker-compose.yml

# Create virtual environment
venv:
	python -m venv venv
	@echo "Virtual environment created. Activate it with 'source venv/bin/activate' (Linux/macOS) or 'venv\\Scripts\\activate' (Windows)"

# Help command
help:
	@echo "Available targets:"
	@echo "  install      - Install main dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  format       - Format code using black and isort"
	@echo "  lint         - Run linting"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  run          - Run the API server"
	@echo "  clean        - Clean build artifacts"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start Docker containers"
	@echo "  docker-down  - Stop Docker containers"
	@echo "  setup-docker - Move docker-compose.yml to the correct location"
	@echo "  venv         - Create virtual environment" 