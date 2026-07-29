#!/bin/bash
set -e

# --- Art Style Analyzer Launcher ---
# Auto-creates venv, installs deps, starts the app.
# Just double-click or run from terminal.

cd "$(dirname "$0")"
DIR="$(pwd)"

# 1. Find Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌  Python not found. Install Python 3.9+ from https://python.org"
    echo "   Or run: xcode-select --install"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✓  Using $($PYTHON --version)"

# 2. Create virtual environment if missing
if [ ! -d "venv" ]; then
    echo "📦  Creating virtual environment..."
    $PYTHON -m venv venv
fi

# 3. Activate
source venv/bin/activate

# 4. Install dependencies if missing
if [ ! -f "venv/.deps_installed" ]; then
    echo "📥  Installing dependencies (one-time)..."
    pip install -q -r requirements.txt
    touch venv/.deps_installed
    echo "✓  Dependencies installed"
fi

# 5. Launch
echo ""
echo "🚀  Starting Art Style Analyzer..."
echo "    Open http://localhost:5001 in your browser"
echo ""

# Open browser after a brief delay (server needs a moment)
(sleep 2 && open http://localhost:5001) &

python app.py
