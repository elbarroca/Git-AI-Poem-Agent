#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Activate virtual environment (adjust path if needed)
source venv/bin/activate

# Run the daily automation script
python3 daily_automation.py >> logs/daily_automation.log 2>&1 