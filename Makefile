.PHONY: help install dev test lint format build push clean

help:
	@echo "OllamaRama - Ollama API Failover Proxy"
	@echo ""
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make dev         - Run in development mode"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Check code style (flake8)"
	@echo "  make format      - Format code (black)"
	@echo "  make typecheck   - Check types (mypy)"
	@echo "  make build       - Build Docker image"
	@echo "  make push        - Push Docker image to registry"
	@echo "  make run         - Run Docker container"
	@echo "  make clean       - Clean up generated files"
	@echo "  make docker-test - Run tests in Docker"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "Installing dev dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-mock black flake8 mypy

dev:
	@echo "Starting development server..."
	export OLLAMA_PORTS=11434-11436 && \
	export DEBUG=True && \
	python app.py

test:
	@echo "Running tests..."
	pytest tests/ -v --cov=. --cov-report=term-missing

test-coverage:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Checking code style..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

format:
	@echo "Formatting code with black..."
	black .

format-check:
	@echo "Checking code format..."
	black --check .

typecheck:
	@echo "Checking types with mypy..."
	mypy app.py

build:
	@echo "Building Docker image..."
	docker build -t ollamarama:latest .
	docker tag ollamarama:latest ollamarama:dev

push: build
	@echo "Pushing to registry..."
	@echo "Configure your registry first!"
	docker push ollamarama:latest

run:
	@echo "Running Docker container..."
	docker run -d \
		--name OllamaRama \
		-p 8000:8000 \
		-e OLLAMA_PORTS=11434-11436 \
		--network host \
		ollamarama:latest
	@echo "Container started. Check health: curl http://localhost:8000/health"

run-compose:
	@echo "Starting with docker-compose..."
	docker-compose up -d
	@echo "Waiting for service to be ready..."
	sleep 2
	curl http://localhost:8000/health || echo "Service not yet ready"

stop:
	@echo "Stopping containers..."
	docker-compose down

logs:
	@echo "Showing logs..."
	docker logs -f OllamaRama

docker-test:
	@echo "Running tests in Docker..."
	docker run --rm \
		-e OLLAMA_PORTS=11434-11436 \
		ollamarama:latest \
		pytest tests/ -v

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	@echo "Clean complete"

venv:
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

setup: venv install-dev
	@echo "Development environment setup complete!"
	@echo "Run: source venv/bin/activate"

full-test: format typecheck lint test
	@echo "All checks passed!"

docker-build-test:
	@echo "Testing Docker build..."
	docker build -t ollamarama:test . --progress=plain

all: clean install-dev format typecheck lint test
	@echo "All tasks completed successfully!"
