
.PHONY: format
format:
	uv run ruff format
	uv run ruff check

.PHONY: lint
lint: 
	uv run ruff check --exit-non-zero-on-fix
	uv run ruff format --check --diff

.PHONY: check-types
check-types:
	uv run mypy ./src/fastapi_silk/

.PHONY: test
test:
	uv run pytest -q

.PHONY: test-watch
test-watch:
	uv run ptw

.PHONY: ci
ci: lint check-types test

