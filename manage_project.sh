#!/bin/bash
# Project Management Script for Fiscal Document Agent
# Handles setup, deployment, and running the application

set -e

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
show_banner() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}Fiscal Document Agent${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

show_help() {
    echo "Usage: ./manage_project.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup        - Setup development environment"
    echo "  deploy       - Setup for Streamlit Cloud deployment"
    echo "  run          - Run Streamlit application"
    echo "  help         - Show this help message"
    echo ""
}

setup_dev_environment() {
    show_banner
    echo -e "${BLUE}Setting up development environment...${NC}"
    echo ""
    
    # Create necessary directories
    echo "📁 Creating directories..."
    mkdir -p data/cache
    mkdir -p data/archives
    mkdir -p logs
    
    # Setup Python virtual environment
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi
    
    # Install dependencies
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Set permissions
    chmod -R 755 data
    chmod 755 manage_project.sh
    
    echo -e "${GREEN}✅ Development setup complete!${NC}"
    echo ""
}

setup_cloud_deployment() {
    show_banner
    echo -e "${BLUE}Setting up for Streamlit Cloud deployment...${NC}"
    echo ""
    
    # Create necessary directories
    echo "📁 Creating directories..."
    mkdir -p data/cache
    mkdir -p data/archives
    mkdir -p logs
    
    # Set permissions
    chmod -R 755 data
    
    echo -e "${GREEN}✅ Deployment setup complete!${NC}"
    echo "📊 System ready for Streamlit Cloud"
    echo ""
}

run_streamlit_app() {
    show_banner
    
    # Ensure venv exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}⚠️  Virtual environment not found!${NC}"
        echo "Running setup first..."
        setup_dev_environment
    fi
    
    # Activate venv
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # Check GEMINI_API_KEY
    if [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  GEMINI_API_KEY not configured${NC}"
        echo ""
        echo "You can:"
        echo "1. Set now: export GEMINI_API_KEY='your-key'"
        echo "2. Enter in Streamlit interface (recommended)"
        echo ""
        echo "Get your key at: https://aistudio.google.com/app/apikey"
        echo ""
    else
        echo -e "${GREEN}✓${NC} GEMINI_API_KEY configured"
    fi
    
    # Launch Streamlit
    echo ""
    echo -e "${GREEN}🚀 Launching Streamlit application...${NC}"
    echo ""
    
    streamlit run src/ui/app.py
}

# Main script logic
case "${1:-help}" in
    setup)
        setup_dev_environment
        ;;
    deploy)
        setup_cloud_deployment
        ;;
    run)
        run_streamlit_app
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
