# Obsidian Vault Server - Task Runner

# Default recipe
default:
    @just --list

# Install dependencies
install:
    uv sync

# Install with dev dependencies
install-dev:
    uv sync --all-extras

# Run the development server
dev:
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run the MCP server
mcp:
    uv run python -m app.mcp_server

# Run database migrations
migrate:
    uv run alembic upgrade head

# Create a new migration
migration name:
    uv run alembic revision --autogenerate -m "{{name}}"

# Rollback last migration
rollback:
    uv run alembic downgrade -1

# Run all tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=app --cov-report=term-missing --cov-report=html

# Run unit tests only
test-unit:
    uv run pytest tests/unit -v

# Run integration tests only
test-integration:
    uv run pytest tests/integration -v

# Run BDD tests only
test-bdd:
    uv run pytest tests/bdd -v

# Run API tests only (requires database)
test-api:
    uv run pytest tests/api -v

# Run all tests that don't require database
test-no-db:
    uv run pytest tests/unit tests/bdd -v

# Run all tests with database (start db first with: just db-up && just migrate)
test-with-db:
    uv run pytest tests/ -v --ignore=tests/integration

# Full test cycle: start db, migrate, test, stop db
test-full:
    #!/usr/bin/env bash
    set -e
    echo "Starting database..."
    just db-up
    echo "Running migrations..."
    just migrate
    echo "Running unit and BDD tests..."
    uv run pytest tests/unit tests/bdd -v
    echo "Running API tests..."
    uv run pytest tests/api -v
    echo "Running integration tests..."
    uv run pytest tests/integration -v
    echo "Stopping database..."
    just db-down
    echo "All tests completed!"

# Run all tests (may have event loop issues - prefer test-full)
test-all:
    uv run pytest tests/unit tests/bdd -v && \
    uv run pytest tests/api tests/integration -v

# Run linting
lint:
    uv run ruff check .

# Run linting with fixes
lint-fix:
    uv run ruff check . --fix

# Run formatting
fmt:
    uv run ruff format .

# Run type checking
typecheck:
    uv run mypy app

# Run all checks (lint, format, typecheck)
check: lint typecheck
    @echo "All checks passed!"

# Start database only (PostgreSQL with pgvector + AGE)
db-up:
    docker-compose up -d db
    @echo "Waiting for database to be ready..."
    @sleep 3
    @until docker-compose exec -T db pg_isready -U obsidian -d obsidian > /dev/null 2>&1; do sleep 1; done
    @echo "Database is ready!"

# Stop database
db-down:
    docker-compose down

# View database logs
db-logs:
    docker-compose logs -f db

# Start full stack (database + app)
stack-up:
    docker-compose --profile full up -d

# Stop full stack
stack-down:
    docker-compose --profile full down

# View all logs
stack-logs:
    docker-compose --profile full logs -f

# Reset database (drop and recreate)
db-reset:
    docker-compose down -v
    just db-up
    just migrate

# Check database connection
db-check:
    @docker-compose exec -T db psql -U obsidian -d obsidian -c "SELECT 1 as connected;" || echo "Database not running"

# Show database extensions
db-extensions:
    @docker-compose exec -T db psql -U obsidian -d obsidian -c "SELECT extname, extversion FROM pg_extension;"

# Legacy aliases for compatibility
infra-up: db-up
infra-down: db-down
infra-logs: db-logs

# Generate TypeScript types from OpenAPI schema
gen-types:
    uv run python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > openapi.json

# Clean build artifacts
clean:
    rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Build Docker image
docker-build:
    docker build -t obsidian-vault-server .

# Run Docker container
docker-run:
    docker run -p 8000:8000 --env-file .env obsidian-vault-server
