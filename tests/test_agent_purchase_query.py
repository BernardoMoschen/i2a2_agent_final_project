"""Test agent's ability to answer questions about purchase invoices."""

import logging
import os

from src.agent.agent_core import create_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_agent_purchase_query():
    """Test agent answering 'quantas notas de compra temos?'"""
    
    # Check if API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("⚠️ GEMINI_API_KEY not set. Set it to test the agent:")
        logger.warning("  export GEMINI_API_KEY='your-key-here'")
        logger.warning("  python test_agent_purchase_query.py")
        return
    
    # Create agent
    logger.info("Creating agent...")
    agent = create_agent(api_key=api_key)
    
    # Test questions
    questions = [
        "quantas notas de compra temos no sistema?",
        "quantas notas de venda existem?",
        "qual o total de documentos processados?",
    ]
    
    for question in questions:
        logger.info(f"\n{'='*60}")
        logger.info(f"❓ Pergunta: {question}")
        logger.info(f"{'='*60}")
        
        try:
            response = agent.chat(question)
            logger.info(f"\n🤖 Resposta:\n{response}\n")
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
    
    logger.info("\n✅ Test completed!")


if __name__ == "__main__":
    test_agent_purchase_query()
