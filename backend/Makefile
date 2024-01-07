install-dev:
	@echo "Installing dev dependencies..."
	poetry config virtualenvs.prefer-active-python true
	poetry install --with dev,test,fixers,linters
	poetry run pre-commit install
	poetry run pre-commit autoupdate

install-prod:
	@echo "Installing prod dependencies..."
	poetry config virtualenvs.prefer-active-python true
	poetry install

start-backend:
	@echo "Start development server"
	poetry run uvicorn src.app:app --reload

test:
	@echo "Running tests..."
	poetry run pytest --cov=src

check-all:
	@echo "Checking all files with pre-commit..."
	poetry run pre-commit run --all-files
