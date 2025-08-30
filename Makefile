# Automation utilities for Scrabbot

VENV=.venv
PY_BIN=$(VENV)/bin/python
PIP_BIN=$(VENV)/bin/pip
PYTEST=$(VENV)/bin/pytest
FLAKE8=$(VENV)/bin/flake8
BLACK=$(VENV)/bin/black
ISORT=$(VENV)/bin/isort

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  setup           - Create venv and install Python dependencies"
	@echo "  test            - Run test suite (pytest)"
	@echo "  lint            - Linting (flake8)"
	@echo "  format          - Formatting (isort + black)"
	@echo "  export-linux    - Export Godot preset 'Linux/X11'"
	@echo "  export-windows  - Export Godot preset 'Windows Desktop'"
	@echo "  export-web      - Export Godot preset 'Web'"
	@echo "  build-all       - Export all platforms"

.PHONY: setup
setup:
	@test -d $(VENV) || python -m venv $(VENV)
	$(PIP_BIN) install --upgrade pip
	@if [ -f bot/requirements.txt ]; then \
		$(PIP_BIN) install -r bot/requirements.txt; \
	fi

.PHONY: test
test:
	$(PYTEST) -q tests

.PHONY: lint
lint:
	$(FLAKE8) .

.PHONY: format
format:
	$(ISORT) .
	$(BLACK) .

.PHONY: export-linux
export-linux:
	bash scripts/export_godot.sh "Linux/X11" "godot" "build/linux/scrabbot.x86_64"

.PHONY: export-windows
export-windows:
	bash scripts/export_godot.sh "Windows Desktop" "godot" "build/windows/Scrabbot.exe"

.PHONY: export-web
export-web:
	bash scripts/export_godot.sh "Web" "godot" "build/web/index.html"

.PHONY: build-all
build-all: export-linux export-windows export-web
