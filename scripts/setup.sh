#!/bin/bash
set -e

echo "🚀 Setting up CivicNavigator Backend..."

# Check if Python 3.9+ is installed
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python 3.9+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "📁 Creating directories..."
mkdir -p uploads models logs data

# Copy environment file
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Initialize database
echo "🗄️ Initializing database..."
python -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"

# Load sample data
echo "📊 Loading sample data..."
python scripts/load_sample_data.py

echo "✅ Setup complete!"
echo ""
echo "🌟 Next steps:"
echo "1. Edit .env file with your API keys and configuration"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python main.py"
echo ""
echo "🌐 The API will be available at: http://localhost:8000"
echo "📚 API documentation: http://localhost:8000/docs"