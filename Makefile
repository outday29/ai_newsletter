.PHONY: format lint test tests

format:
	black .
	ruff check --select I --select E --select F --fix .

lint:
	black . --check
	ruff .

test tests:
	pytest -s ./tests
