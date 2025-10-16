"""
Demo simples do Fiscal Document Agent.

Este script mostra como:
1. Inicializar o agente com sua chave Gemini
2. Fazer perguntas sobre documentos fiscais
3. Processar XMLs (quando fornecidos)

COMO USAR:
1. Defina sua chave API: export GEMINI_API_KEY='sua-chave-aqui'
2. Execute: python examples/demo_agent.py
3. Digite suas perguntas ou 'sair' para terminar
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent_core import create_agent


def main():
    """Run interactive agent demo."""
    print("=" * 70)
    print("🤖 DEMO: Agente de Documentos Fiscais com Gemini")
    print("=" * 70)
    print()

    # Get API key
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        print("❌ ERRO: GEMINI_API_KEY não encontrada!")
        print()
        print("Para usar este demo, você precisa:")
        print("1. Obter uma chave API do Google AI Studio:")
        print("   https://aistudio.google.com/app/apikey")
        print()
        print("2. Definir a variável de ambiente:")
        print("   export GEMINI_API_KEY='sua-chave-aqui'")
        print()
        print("3. Executar novamente este script")
        return

    # Initialize agent
    print("⏳ Inicializando agente...")
    try:
        agent = create_agent(api_key=api_key, model_name="gemini-2.5-flash-lite")
        print("✅ Agente inicializado com sucesso!\n")
    except Exception as e:
        print(f"❌ Erro ao inicializar agente: {e}")
        return

    # Show greeting
    print(agent.get_greeting())
    print()

    # Interactive loop
    print("💬 Modo interativo (digite 'sair' para terminar)")
    print("=" * 70)
    print()

    while True:
        try:
            # Get user input
            user_input = input("Você: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["sair", "exit", "quit"]:
                print("\n👋 Até logo!")
                break

            # Get agent response
            print()
            response = agent.chat(user_input)
            print(f"Agente: {response}")
            print()

        except KeyboardInterrupt:
            print("\n\n👋 Até logo!")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")


if __name__ == "__main__":
    main()
