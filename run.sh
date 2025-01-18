#!/bin/bash

# Set the virtual environment path
VENV_DIR="venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Function to check if a Python package is installed
check_package() {
    python3 -c "import $1" 2>/dev/null
    return $?
}

# Check and install required packages
required_packages=("PySide6" "requests" "markdown2" "PyQt5")

for package in "${required_packages[@]}"; do
    if ! check_package "$package"; then
        echo "Installing $package..."
        pip install "$package"  # Removed --user flag since we're in venv
    fi
done

# Run the application
cd "$(dirname "$0")"
python3 main.py

# Deactivate virtual environment when done
deactivate
