#!/bin/bash

echo "Starting AI-Powered Web Scraping Platform..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Please create a .env file with your GEMINI_API_KEY"
    echo "See SETUP.md for instructions"
    echo ""
    read -p "Press enter to continue anyway..."
fi

# Run the application
python app.py

