lint:
	python -m black . --check
	python -m isort . --check-only --profile black
	python -m flake8 src --max-line-length=127
lint-fix:
	black .
	isort . --profile black