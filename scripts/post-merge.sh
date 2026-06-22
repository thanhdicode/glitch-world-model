#!/bin/bash
set -e

echo "Running post-merge setup..."

if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    pip install -e . --quiet --no-input 2>/dev/null || true
fi

echo "Post-merge setup complete."
