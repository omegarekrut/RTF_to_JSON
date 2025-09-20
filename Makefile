# RTF to JSON Converter - Development Commands
# Run with: make <command>

.PHONY: help convert test clean install format lint

# Python executable in virtual environment
PYTHON := .venv/bin/python
PYTHONPATH := PYTHONPATH=.

# Default target
help:
	@echo "RTF to JSON Converter - Available Commands:"
	@echo ""
	@echo "  convert FILE=<rtf_file>  Convert RTF file to JSON (auto-output to json/)"
	@echo "  test                     Run test suite"
	@echo "  clean                    Clean generated files"
	@echo "  install                  Install dependencies"
	@echo "  format                   Format code (if tools available)"
	@echo "  lint                     Lint code (if tools available)"
	@echo ""
	@echo "Examples:"
	@echo "  make convert FILE=rtf/r.rtf"
	@echo "  make test"
	@echo "  make clean"

# Convert RTF file to JSON
convert:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=<rtf_file>"; \
		echo "Example: make convert FILE=rtf/r.rtf"; \
		exit 1; \
	fi
	@echo "Converting $(FILE) to JSON..."
	@$(PYTHONPATH) $(PYTHON) -m rtf_to_json $(FILE)

# Run test suite
test:
	@echo "Running test suite..."
	@$(PYTHONPATH) $(PYTHON) -m pytest tests/ -v

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf json/*.json
	@rm -rf .pytest_cache
	@rm -rf __pycache__
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

# Install dependencies (using uv)
install:
	@echo "Installing dependencies..."
	@uv sync
	@echo "Dependencies installed."

# Format code (if black is available)
format:
	@if command -v black >/dev/null 2>&1; then \
		echo "Formatting code with black..."; \
		black rtf_to_json/ tests/; \
	else \
		echo "black not available, skipping format"; \
	fi

# Lint code (if ruff is available)
lint:
	@if command -v ruff >/dev/null 2>&1; then \
		echo "Linting code with ruff..."; \
		ruff check rtf_to_json/ tests/; \
	else \
		echo "ruff not available, skipping lint"; \
	fi

# Quick convert shortcut for the main sample file
sample:
	@echo "Converting sample file rtf/r.rtf..."
	@$(PYTHONPATH) $(PYTHON) -m rtf_to_json rtf/r.rtf

# Show project status
status:
	@echo "RTF to JSON Converter - Project Status"
	@echo "======================================"
	@echo "Virtual environment: .venv/"
	@echo "Python: $(PYTHON)"
	@echo "RTF files: $$(ls rtf/ 2>/dev/null | wc -l) files in rtf/"
	@echo "JSON files: $$(ls json/ 2>/dev/null | wc -l) files in json/"
	@echo "Tests: $$(ls tests/test_*.py 2>/dev/null | wc -l) test files"