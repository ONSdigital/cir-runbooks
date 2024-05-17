lint:
	python -m black . --check
	python -m isort . --check-only --profile black
	python -m flake8 src --max-line-length=127
lint-fix:
	black .
	isort . --profile black
lint-check:
	python -m black . --check --line-length 127
	python -m flake8 --max-line-length=127 --exclude=./scripts,env,.venv
	python -m isort . --check-only --profile black --skip env --skip .venv