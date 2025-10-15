# Development Scripts

This directory contains scripts for maintaining code quality in the project.

## Available Scripts

### `format.sh`
Automatically formats Python code using black and isort.

```bash
./scripts/format.sh
```

This will:
- Sort imports with isort (configured to work with black)
- Format code with black (88 character line length)

### `lint.sh`
Runs linting checks on the codebase.

```bash
./scripts/lint.sh
```

This will:
- Run flake8 for style checking
- Run mypy for static type checking

### `test.sh`
Runs the test suite.

```bash
./scripts/test.sh
```

This will:
- Run all pytest tests in the backend/tests directory

### `quality.sh`
Runs all quality checks in sequence.

```bash
./scripts/quality.sh
```

This will:
1. Format code (format.sh)
2. Run linting (lint.sh)
3. Run tests (test.sh)

## Pre-commit Workflow

Before committing code, run:
```bash
./scripts/quality.sh
```

This ensures your code is properly formatted, passes all linting checks, and all tests pass.
