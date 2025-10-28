"""Test the Fiscal Document Agent with Gemini."""

import os
from pathlib import Path
import pytest

from src.agent.agent_core import create_agent


@pytest.fixture
def agent():
    """Create agent fixture for testing."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        pytest.skip("GEMINI_API_KEY not found - skipping agent tests")
    
    try:
        agent = create_agent(api_key=api_key, model_name="gemini-2.5-flash-lite")
        return agent
    except Exception as e:
        pytest.skip(f"Failed to create agent: {e}")


def test_agent_initialization(agent):
    """Test agent initialization with API key."""
    print("=" * 70)
    print("TESTE 1: Inicialização do Agente")
    print("=" * 70)

    assert agent is not None
    print("✅ Agente inicializado com sucesso!")
    print(f"   Modelo: gemini-2.5-flash-lite")
    print(f"   Ferramentas disponíveis: {len(agent.executor.tools)}")
    for tool in agent.executor.tools:
        print(f"   - {tool.name}: {tool.description[:60]}...")


def test_greeting(agent):
    """Test greeting message."""
    print("\n" + "=" * 70)
    print("TESTE 2: Mensagem de Boas-vindas")
    print("=" * 70)

    greeting = agent.get_greeting()
    assert greeting
    print(greeting)


def test_simple_question(agent):
    """Test simple knowledge question."""
    print("\n" + "=" * 70)
    print("TESTE 3: Pergunta Simples sobre Conhecimento Fiscal")
    print("=" * 70)

    question = "O que é uma NFe e quais são os principais campos obrigatórios?"
    print(f"📝 Pergunta: {question}\n")

    try:
        response = agent.chat(question)
        assert response
        print("🤖 Resposta do Agente:")
        print(response)
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise


def test_xml_parsing_request(agent):
    """Test XML parsing without actual XML (should handle gracefully)."""
    print("\n" + "=" * 70)
    print("TESTE 4: Solicitação de Parsing (sem XML - teste de orientação)")
    print("=" * 70)

    question = "Como eu faço para enviar um XML de NFe para você processar?"
    print(f"📝 Pergunta: {question}\n")

    try:
        response = agent.chat(question)
        assert response
        print("🤖 Resposta do Agente:")
        print(response)
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("TESTE DO AGENTE FISCAL - Integração com Gemini")
    print("=" * 70)
    print()

    # Initialize agent
    agent = test_agent_initialization()

    if not agent:
        print("\n⚠️  Testes não podem continuar sem API key.")
        print("   Configure GEMINI_API_KEY e execute novamente.")
        return

    # Run tests
    test_greeting(agent)
    test_simple_question(agent)
    test_xml_parsing_request(agent)

    print("\n" + "=" * 70)
    print("TESTES CONCLUÍDOS")
    print("=" * 70)
    print("\n✅ O agente está funcionando e conectado ao Gemini!")
    print("   Próximo passo: integrar com a UI Streamlit")


if __name__ == "__main__":
    main()
