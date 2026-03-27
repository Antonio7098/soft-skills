.PHONY: \
	smoke \
	smoke-list \
	smoke-provider \
	smoke-auth \
	smoke-marking-quick \
	smoke-marking-interview \
	smoke-marking-scenario \
	smoke-session-flow \
	smoke-run-lifecycle \
	smoke-suite \
	test \
	test-unit \
	test-integration \
	test-unit-file \
	test-integration-file \
	test-unit-k \
	test-integration-k \
	lint \
	typecheck

PYTHONPATH_SRC = PYTHONPATH=src
PYTEST = $(PYTHONPATH_SRC) python -m pytest -q

smoke:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke

smoke-list:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke --list

smoke-provider:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke provider-baseline

smoke-auth:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke auth-flows

smoke-marking-quick:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke marking-quick-practice

smoke-marking-interview:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke marking-interview

smoke-marking-scenario:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke marking-scenario

smoke-session-flow:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke practice-session-flow

smoke-run-lifecycle:
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke practice-run-lifecycle

smoke-suite:
	@if [ -z "$(SUITE)" ]; then echo "Usage: make smoke-suite SUITE=<smoke-name>"; exit 1; fi
	$(PYTHONPATH_SRC) python -m soft_skills_backend.smoke $(SUITE)

test:
	$(PYTEST)

test-unit:
	$(PYTEST) tests/unit

test-integration:
	$(PYTEST) tests/integration

test-unit-file:
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-unit-file FILE=tests/unit/test_foo.py"; exit 1; fi
	$(PYTEST) $(FILE)

test-integration-file:
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-integration-file FILE=tests/integration/test_bar.py"; exit 1; fi
	$(PYTEST) $(FILE)

test-unit-k:
	@if [ -z "$(K)" ]; then echo "Usage: make test-unit-k K=<pytest-expression>"; exit 1; fi
	$(PYTEST) tests/unit -k "$(K)"

test-integration-k:
	@if [ -z "$(K)" ]; then echo "Usage: make test-integration-k K=<pytest-expression>"; exit 1; fi
	$(PYTEST) tests/integration -k "$(K)"

lint:
	$(PYTHONPATH_SRC) python -m ruff check src tests

typecheck:
	$(PYTHONPATH_SRC) python -m mypy src
