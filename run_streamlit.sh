#!/bin/bash
# Script para iniciar a aplicação Streamlit

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Fiscal Document Agent - Streamlit${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Verifica se o venv existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment não encontrado!${NC}"
    echo "Criando ambiente virtual..."
    python -m venv venv
    source venv/bin/activate
    echo "Instalando dependências..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Verifica se GEMINI_API_KEY está definida
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  GEMINI_API_KEY não está definida${NC}"
    echo ""
    echo "Você pode:"
    echo "1. Defini-la agora: export GEMINI_API_KEY='sua-chave'"
    echo "2. Inserir na interface do Streamlit (recomendado)"
    echo ""
    echo "Obtenha sua chave em: https://aistudio.google.com/app/apikey"
    echo ""
else
    echo -e "${GREEN}✓${NC} GEMINI_API_KEY configurada"
fi

# Inicia Streamlit
echo ""
echo -e "${GREEN}🚀 Iniciando Streamlit...${NC}"
echo ""

streamlit run src/ui/app.py
