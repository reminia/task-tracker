#!/bin/bash

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create virtual environment
uv venv

# Install dependencies from pyproject.toml
uv pip install -e . 