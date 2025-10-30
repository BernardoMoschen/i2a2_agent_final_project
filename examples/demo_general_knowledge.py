#!/usr/bin/env python3
"""
Quick demonstration of the agent's general knowledge capabilities.

This script shows how the agent can seamlessly handle both:
1. Specific fiscal document queries
2. General knowledge questions
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def demonstrate_capabilities():
    """Show visual examples of different question types."""
    
    print("=" * 80)
    print("🤖 FISCAL DOCUMENT AGENT - GENERAL KNOWLEDGE DEMONSTRATION")
    print("=" * 80)
    print()
    
    print("The agent can now answer ANY question!\n")
    
    # Example questions organized by category
    examples = {
        "📄 Questions About Documents in Your System": [
            "Quantas notas de compra temos em 2024?",
            "Mostre vendas do último mês",
            "Qual fornecedor tem mais documentos?",
            "Gerar gráfico de impostos mensais",
        ],
        "📚 Fiscal & Accounting Knowledge": [
            "O que é ICMS e como é calculado?",
            "Qual a diferença entre NFe e NFCe?",
            "O que significa CFOP 5102?",
            "Como funciona o Simples Nacional?",
            "Explique o que é NCM",
        ],
        "🧮 Calculations & Practical Examples": [
            "Se um produto custa R$ 100 com IPI de 10%, qual o valor final?",
            "Como calcular o lucro líquido de uma empresa?",
            "Calcular ICMS por dentro de R$ 1000 a 18%",
        ],
        "⚖️ Brazilian Legislation & Tax Regimes": [
            "O que é regime de competência?",
            "Diferença entre Lucro Real e Lucro Presumido",
            "Quais são as obrigações do Simples Nacional?",
        ],
        "🌍 General Knowledge (Non-Fiscal)": [
            "Quem foi Albert Einstein?",
            "Como funciona a fotossíntese?",
            "O que é um arquivo XML?",
            "Explique o que é uma API REST",
            "Como funciona o GPS?",
        ],
        "💻 Technology & Technical Concepts": [
            "O que é um banco de dados SQLite?",
            "Como funciona a criptografia?",
            "O que é cloud computing?",
        ],
    }
    
    for category, questions in examples.items():
        print(f"\n{category}")
        print("─" * 80)
        for i, question in enumerate(questions, 1):
            print(f"  {i}. {question}")
    
    print("\n" + "=" * 80)
    print("HOW IT WORKS")
    print("=" * 80)
    print()
    print("The agent intelligently decides what to do:")
    print()
    print("  User Question")
    print("       ↓")
    print("  ┌─────────────────────────────────────┐")
    print("  │ Agent Analyzes Intent               │")
    print("  ├─────────────────────────────────────┤")
    print("  │ • Database query? → Use search tool │")
    print("  │ • XML processing? → Use parser      │")
    print("  │ • Report needed?  → Generate chart  │")
    print("  │ • Fiscal concept? → Explain         │")
    print("  │ • General topic?  → Answer directly │")
    print("  └─────────────────────────────────────┘")
    print("       ↓")
    print("  Response to User")
    print()
    
    print("=" * 80)
    print("FEATURES")
    print("=" * 80)
    print()
    print("✅ Natural Language Understanding")
    print("   → Ask in Portuguese or English, formal or casual")
    print()
    print("✅ Context-Aware Responses")
    print("   → Remembers conversation history")
    print()
    print("✅ Multi-Domain Expertise")
    print("   → Fiscal documents + Accounting + General knowledge")
    print()
    print("✅ Smart Tool Selection")
    print("   → Uses tools when needed, answers directly when possible")
    print()
    print("✅ Educational & Helpful")
    print("   → Explains concepts, shows calculations, provides examples")
    print()
    
    print("=" * 80)
    print("TO TEST THIS FEATURE")
    print("=" * 80)
    print()
    print("1. Set your API key:")
    print("   export GEMINI_API_KEY='your-key-here'")
    print()
    print("2. Run the Streamlit app:")
    print("   streamlit run src/ui/app.py")
    print()
    print("3. Or run automated tests:")
    print("   python test_general_questions.py")
    print()
    print("4. Try asking ANY question in the chat!")
    print()
    
    print("=" * 80)
    print("EXAMPLE INTERACTION")
    print("=" * 80)
    print()
    print("👤 User: Quantas notas de compra temos?")
    print()
    print("🤖 Agent:")
    print("   [Uses search_invoices_database tool]")
    print("   📊 Encontrei 234 notas fiscais de compra no sistema")
    print("   💰 Valor total: R$ 1.245.678,90")
    print("   📅 Período: 01/01/2024 a 30/10/2024")
    print()
    print("👤 User: O que é ICMS?")
    print()
    print("🤖 Agent:")
    print("   [Answers directly using knowledge]")
    print("   📚 ICMS é o Imposto sobre Circulação de Mercadorias e Serviços,")
    print("   um imposto estadual que incide sobre a movimentação de produtos...")
    print("   [Provides detailed explanation]")
    print()
    print("👤 User: Quem foi Albert Einstein?")
    print()
    print("🤖 Agent:")
    print("   [Answers using general knowledge]")
    print("   👨‍🔬 Albert Einstein foi um físico teórico alemão, um dos")
    print("   cientistas mais influentes de todos os tempos...")
    print("   [Provides biography and contributions]")
    print()
    
    print("=" * 80)
    print("DOCUMENTATION")
    print("=" * 80)
    print()
    print("📖 Full guide:      docs/GENERAL_KNOWLEDGE_CAPABILITY.md")
    print("📝 Examples:        QUESTION_EXAMPLES_EXTENDED.md")
    print("📋 Summary:         GENERAL_KNOWLEDGE_SUMMARY.md")
    print("🚀 Quick Start:     QUICK_START_ASK_ANYTHING.md")
    print()
    
    print("=" * 80)
    print("✨ THE AGENT IS READY - ASK ANYTHING! ✨")
    print("=" * 80)
    print()


if __name__ == "__main__":
    demonstrate_capabilities()
