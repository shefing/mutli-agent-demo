#!/bin/bash

# Setup and Run Script for AlignmentCheck Tester
echo "🚀 Setting up AlignmentCheck Testing Environment"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install minimal dependencies for CLI tester
echo "Installing dependencies (this may take a moment)..."
pip install -q llamafirewall python-dotenv colorama 2>/dev/null || {
    echo "⚠️  Installing with user flag due to system restrictions..."
    pip install -q --user llamafirewall python-dotenv colorama
}

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your API keys:"
    echo "  OPENAI_API_KEY=your_key_here"
    echo "  TOGETHER_API_KEY=your_key_here"
    exit 1
fi

# Check for required API keys
if ! grep -q "OPENAI_API_KEY=" .env || ! grep -q "TOGETHER_API_KEY=" .env; then
    echo "⚠️  Warning: Make sure your .env file contains:"
    echo "  - OPENAI_API_KEY"
    echo "  - TOGETHER_API_KEY"
fi

echo ""
echo "✅ Setup complete! Running AlignmentCheck Tester..."
echo "================================================"
echo ""

# Run the alignment check tester
python3 multi_agent_demo/alignment_check_tester.py