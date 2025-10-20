#!/bin/bash
# Orchestrator Environment Setup Script

echo "🚀 Setting up Orchestrator Conversational System Environment"
echo "=========================================================="

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed or not in PATH"
    exit 1
fi

# Activate the orchestrator environment
echo "📦 Activating conda environment: orchestrator"
eval "$(conda shell.bash hook)"
conda activate orchestrator

if [ $? -eq 0 ]; then
    echo "✅ Environment activated successfully"
    echo "🐍 Python version: $(python --version)"
    echo "📍 Working directory: $(pwd)"
    echo ""
    echo "🎯 Available commands:"
    echo "  python run.py          # Start the Orchestrator server"
    echo "  python -m app.main    # Alternative start method"
    echo "  pip list              # Show installed packages"
    echo "  conda deactivate      # Exit the environment"
    echo ""
    echo "🌐 Once running, visit:"
    echo "  http://localhost:8004/test    # Test client"
    echo "  http://localhost:8004/docs   # API documentation"
    echo "  http://localhost:8004/health  # Health check"
    echo ""
else
    echo "❌ Failed to activate environment"
    exit 1
fi
