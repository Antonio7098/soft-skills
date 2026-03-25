.PHONY: smoke test lint typecheck

smoke:
	PYTHONPATH=src python -m soft_skills_backend.smoke

test:
	PYTHONPATH=src python -m pytest -q

lint:
	PYTHONPATH=src python -m ruff check src tests

typecheck:
	PYTHONPATH=src python -m mypy src
