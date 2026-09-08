.PHONY: help install dev test test-v docker-up docker-down docker-build clean

help:
	@echo "EV Backend Developer Commands:"
	@echo "  make install       Install dependencies using uv"
	@echo "  make dev           Run development server with auto-reload"
	@echo "  make test          Run pytest suite"
	@echo "  make docker-up     Start Docker Compose stack"
	@echo "  make docker-down   Stop Docker Compose stack"
	@echo "  make docker-build  Rebuild Docker images"
	@echo "  make clean         Clean build & cache artifacts"

install:
	uv venv
	uv pip install -e ".[dev]"

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest

test-v:
	uv run pytest -v -s

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build --no-cache

clean:
	rm -rf .venv __pycache__ .pytest_cache .coverage *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
