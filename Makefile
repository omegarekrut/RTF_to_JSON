# RTF to JSON Converter - Development Commands
# Run with: make <command>

.PHONY: help convert test clean cleanall install format lint sample bigtest status

# Use uv run with clean environment (unset conflicting VIRTUAL_ENV)
UV_RUN := unset VIRTUAL_ENV && uv run

# Default target
help:
	@echo "RTF to JSON Converter - Available Commands:"
	@echo ""
	@echo "  convert FILE=<rtf_file>  Convert RTF file to JSON (optional: OUTPUT=<path>)"
	@echo "  sample                   Convert main sample file (rtf/r.rtf)"
	@echo "  bigtest                  Convert big test file (rtf/bigrttest.rtf)"
	@echo "  test                     Run test suite"
	@echo "  clean                    Clean generated files (preserve reference outputs)"
	@echo "  cleanall                 Clean all files including reference outputs"
	@echo "  install                  Install dependencies"
	@echo "  format                   Format code using project environment"
	@echo "  lint                     Lint code using project environment"
	@echo "  status                   Show project status"
	@echo ""
	@echo "Examples:"
	@echo "  make convert FILE=rtf/bigrttest.rtf"
	@echo "  make convert FILE=rtf/r.rtf OUTPUT=custom/output.json"
	@echo "  make sample"
	@echo "  make bigtest"
	@echo "  make test"
	@echo "  make clean"

# Convert RTF file to JSON
convert:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=<rtf_file>"; \
		echo "Example: make convert FILE=rtf/r.rtf"; \
		echo "         make convert FILE=rtf/r.rtf OUTPUT=custom/output.json"; \
		exit 1; \
	fi
	@echo "Converting $(FILE) to JSON..."
	@if [ -n "$(OUTPUT)" ]; then \
		$(UV_RUN) python -m rtf_to_json "$(FILE)" --output "$(OUTPUT)"; \
	else \
		$(UV_RUN) python -m rtf_to_json "$(FILE)"; \
	fi

# Run test suite
test:
	@echo "Running test suite..."
	@$(UV_RUN) pytest "tests/" -v

# Clean generated files (preserve reference outputs)
clean:
	@echo "Cleaning generated files..."
	@rm -rf ".pytest_cache"
	@rm -rf "__pycache__"
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

# Clean all including reference outputs (use with caution)
cleanall:
	@echo "Cleaning all files including reference outputs..."
	@rm -rf "json/"*.json
	@rm -rf ".pytest_cache"
	@rm -rf "__pycache__"
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean all complete."

# Install dependencies (using uv)
install:
	@echo "Installing dependencies..."
	@uv sync
	@echo "Dependencies installed."

# Format code using project environment
format:
	@echo "Formatting code with black..."
	@$(UV_RUN) black "rtf_to_json/" "tests/" || echo "black not available in environment"

# Lint code using project environment
lint:
	@echo "Linting code with ruff..."
	@$(UV_RUN) ruff check "rtf_to_json/" "tests/" || echo "ruff not available in environment"

# Quick convert shortcut for the main sample file
sample:
	@echo "Converting sample file rtf/r.rtf..."
	@$(UV_RUN) python -m rtf_to_json "rtf/r.rtf"

# Quick convert shortcut for the big test file
bigtest:
	@echo "Converting big test file rtf/bigrttest.rtf..."
	@$(UV_RUN) python -m rtf_to_json "rtf/bigrttest.rtf"

# Show project status
status:
	@echo "RTF to JSON Converter - Project Status"
	@echo "======================================"
	@echo "Virtual environment: .venv/"
	@echo "Python: $(shell python3 --version 2>/dev/null || echo "Python 3.x")"
	@echo "RTF files: $$(ls "rtf/" 2>/dev/null | wc -l) files in rtf/"
	@echo "JSON files: $$(ls "json/" 2>/dev/null | wc -l) files in json/"
	@echo "Tests: $$(ls "tests/"test_*.py 2>/dev/null | wc -l) test files"