#!/bin/bash
# Run Belot Calculator

# Check if calibration is needed
if [ ! -d "templates" ]; then
    echo "Card templates not found. Running calibration first..."
    python3 belot_calibrator.py
else
    # Run the calculator
    python3 belot_calculator.py
fi