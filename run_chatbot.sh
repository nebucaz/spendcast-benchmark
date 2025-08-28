#!/bin/bash

# Spendcast Benchmark Chatbot Runner
echo "🤖 Starting Spendcast Benchmark Chatbot..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'uv sync' first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Run the chatbot
python -m src.main

