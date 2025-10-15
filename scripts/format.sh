#!/bin/bash
# Format Python code with black and isort

set -e

echo "Running isort..."
uv run isort backend/

echo "Running black..."
uv run black backend/

echo "✓ Code formatting complete!"
