# Common developer tasks. Run `make help` to see them.

.PHONY: help install test lint security run docker-build up down

help:
	@echo "install       Install dev dependencies"
	@echo "test          Run the test suite"
	@echo "lint          Run the linter"
	@echo "security      Run the source security scan"
	@echo "run           Run the app locally with hot reload"
	@echo "docker-build  Build the Docker image"
	@echo "up            Start the full stack (app + Prometheus + Grafana)"
	@echo "down          Stop the stack"

install:
	pip install -r requirements-dev.txt

test:
	pytest -v

lint:
	ruff check .

security:
	bandit -r app -c pyproject.toml

run:
	uvicorn app.main:app --reload

docker-build:
	docker build -t uptime-monitor:local .

up:
	docker compose up --build

down:
	docker compose down
