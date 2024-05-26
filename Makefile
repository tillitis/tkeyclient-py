# Variables for targets related to pipenv
PIPENV_INSTALL = pipenv install

# Variables for targets related to testing
PYTEST = python -m pytest
PYTEST_LIBRARY = tkeyclient
PYTEST_COVERAGE_JUNIT = junit.xml
PYTEST_COVERAGE_HTML = htmlcov

# Default targets
all: install test

# Install packages required by runtime
install:
	$(PIPENV_INSTALL)

# Install packages required for development and testing
install_dev:
	$(PIPENV_INSTALL) -d -e .

# Install packages required for building documentation
install_docs:
	$(PIPENV_INSTALL) --categories docs

# Install git hooks for the pre-commit framework
install_hooks: install_dev
	pre-commit install

# Uninstall git hooks for the pre-commit framework
uninstall_hooks:
	pre-commit uninstall

# Run linter against entire codebase
lint:
	ruff check .

# Run test suite
test:
	$(PYTEST)

# Run test suite and generate coverage report in JUnit XML
coverage_junit:
	$(PYTEST) --cov=$(PYTEST_LIBRARY) --junit-xml=$(PYTEST_COVERAGE_JUNIT)

# Run test suite and generate coverage report in HTML
coverage_html:
	$(PYTEST) --cov=$(PYTEST_LIBRARY) --cov-report=html:$(PYTEST_COVERAGE_HTML)

# Build HTML documentation from source
docs: install_docs
	mkdocs build -d site
