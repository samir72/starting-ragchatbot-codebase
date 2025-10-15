#!/bin/bash
# Run all quality checks: formatting, linting, and tests

set -e

echo "================================"
echo "Running Code Quality Checks"
echo "================================"
echo ""

# Format code
echo "1. Formatting code..."
./scripts/format.sh
echo ""

# Run linting
echo "2. Running linters..."
./scripts/lint.sh
echo ""

# Run tests
echo "3. Running tests..."
./scripts/test.sh
echo ""

echo "================================"
echo "✓ All quality checks complete!"
echo "================================"
