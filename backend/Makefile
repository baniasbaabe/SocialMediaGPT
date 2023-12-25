install_dev:
	@echo "Installing dev dependencies..."
	poetry config virtualenvs.prefer-active-python true
	poetry install --with dev,test,fixers,linters
	poetry run pre-commit install
	poetry run pre-commit autoupdate

install_prod:
	@echo "Installing prod dependencies..."
	poetry config virtualenvs.prefer-active-python true
	poetry install

test:
	@echo "Running tests..."
	poetry run pytest --cov=src

check_all:
	@echo "Checking all files with pre-commit..."
	poetry run pre-commit run --all-files

build:
	@echo "Building docker image..."
	docker image build -t socialmediagpt-backend:latest ./backend/
