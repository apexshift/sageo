.PHONY: test lint contract-lint ci

# Prefer an editable install (CI: pip install -e ".[dev]"). PYTHONPATH keeps
# local `make contract-lint` working without reinstalling after src edits.
export PYTHONPATH := src$(if $(PYTHONPATH),:$(PYTHONPATH))

test:
	pytest

lint:
	ruff check src tests

contract-lint:
	python -m sageo.contract_lint

# Hermetic local mirror of GitHub Actions CI (no secrets, no live vendors).
ci: lint contract-lint test
