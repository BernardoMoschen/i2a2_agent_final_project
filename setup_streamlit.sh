#!/bin/bash
# Setup script for Streamlit Cloud deployment
# This runs automatically on Streamlit Cloud

set -e

echo "🚀 Setting up Fiscal Document Agent for Streamlit Cloud..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/cache
mkdir -p data/archives
mkdir -p logs

# Set permissions
chmod -R 755 data

echo "✅ Setup complete!"
echo "📊 System ready for deployment"
