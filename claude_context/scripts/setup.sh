#!/bin/bash
# Setup script for Python virtual environment

echo "🔧 Setting up Python environment..."

# Check if venv exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔄 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "❌ Could not find activation script!"
    exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip3 install --upgrade pip

# Install requirements if exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing requirements..."
    pip3 install -r requirements.txt
else
    echo "⚠️  No requirements.txt found"
fi

echo "✅ Setup complete!"
echo ""
echo "💡 To activate virtual environment:"
echo "   source venv/bin/activate  # Linux/Mac"
echo "   venv\\Scripts\\activate     # Windows"
