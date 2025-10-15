#!/bin/bash
# Run all tests with pytest

set -e

echo "Running tests..."
cd backend && uv run pytest

echo "✓ Tests complete!"
