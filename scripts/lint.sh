#!/bin/bash
# Run linting checks with flake8 and mypy

set -e

echo "Running flake8..."
uv run flake8 backend/ || echo "⚠ Flake8 found issues"

echo ""
echo "Running mypy..."
uv run mypy backend/ || echo "⚠ Mypy found issues"

echo ""
echo "✓ Linting checks complete!"
