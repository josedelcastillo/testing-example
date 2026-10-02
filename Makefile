PY ?= .venv/bin/python

.PHONY: install lint format test-unit test-integration test-e2e test-api test db-up db-down app-up down run

install:
	python3 -m venv .venv
	$(PY) -m pip install -r requirements-dev.txt
	$(PY) -m playwright install chromium

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

format:
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

test-unit:
	$(PY) -m pytest tests/unit \
		--cov=app.pricing --cov=app.services --cov-fail-under=90 \
		--cov-report=term-missing --junitxml=reports/unit.xml

db-up:
	docker compose up -d --wait db

app-up:
	docker compose up -d --build --wait

down:
	docker compose down -v

test-integration: db-up
	$(PY) -m pytest tests/integration -m integration \
		--cov=app --cov-fail-under=80 \
		--cov-report=term-missing --cov-report=xml:reports/coverage.xml \
		--junitxml=reports/integration.xml

test-e2e: app-up
	$(PY) -m pytest tests/e2e -m e2e \
		--tracing retain-on-failure --screenshot only-on-failure \
		--output reports/e2e-artifacts --junitxml=reports/e2e.xml

test-api: app-up
	cd tests/karate && mvn -B test -Dkarate.baseUrl=http://localhost:8000

test: lint test-unit test-integration test-api test-e2e

run: db-up
	$(PY) -m uvicorn app.main:app --reload

db-down: down
