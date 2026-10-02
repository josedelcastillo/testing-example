PY ?= .venv/bin/python

.PHONY: install lint format test-unit test-integration test db-up db-down run

install:
	python3 -m venv .venv
	$(PY) -m pip install -r requirements-dev.txt

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

db-down:
	docker compose down -v

test-integration: db-up
	$(PY) -m pytest tests/integration -m integration \
		--cov=app --cov-fail-under=80 \
		--cov-report=term-missing --cov-report=xml:reports/coverage.xml \
		--junitxml=reports/integration.xml

test: lint test-unit test-integration

run: db-up
	$(PY) -m uvicorn app.main:app --reload
