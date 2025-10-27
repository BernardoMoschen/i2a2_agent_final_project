"""Fiscal Document Agent core with LangChain and Gemini.

This module provides backward compatibility with the old FiscalDocumentAgent
while internally using the new HybridFiscalAgent for enhanced capabilities.
"""

import logging
from typing import Any

from src.agent.hybrid_agent import HybridFiscalAgent, create_hybrid_agent

logger = logging.getLogger(__name__)


# Default greeting message
USER_GREETING = """👋 Olá! Sou seu assistente fiscal inteligente.

🎯 **O que posso fazer:**

**🧠 Inteligência Nativa (sem ferramentas):**
- Responder perguntas gerais (matemática, programação, conceitos)
- Explicar conceitos fiscais (ICMS, CFOP, NFe, etc.)
- Escrever código Python
- Fazer cálculos e raciocínio lógico
- Traduzir entre idiomas

**🛠️ Ferramentas Especializadas:**
- Processar e validar documentos fiscais (XMLs)
- Buscar no banco de dados
- Gerar relatórios (CSV/Excel) e visualizações
- Classificar documentos
- Validar CNPJ, CEP, NCM
- Arquivar documentos

**🚀 Capacidades Dinâmicas:**
- Executar código Python para cálculos complexos
- Buscar informações na internet (se habilitado)

💬 **Como me usar:**
- Pergunte o que quiser! Respondo em Português ou English
- Para dados do banco: "Quantas notas fiscais temos?"
- Para relatórios: "Gere relatório de impostos de janeiro"
- Para conceitos: "O que é ICMS?"
- Para código: "Escreva Python para calcular juros compostos"

Vamos começar! 🚀
"""


class FiscalDocumentAgent:
    """
    LLM-powered agent for processing Brazilian fiscal documents.
    
    This is a wrapper around HybridFiscalAgent for backward compatibility.
    The hybrid agent provides:
    - Native LLM reasoning (answer questions, write code, explain concepts)
    - Specialized fiscal tools (database, reports, validation)
    - Dynamic capabilities (web search, code execution)
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        enable_web_search: bool = False,
        enable_code_execution: bool = True,
    ):
        """
        Initialize the agent.

        Args:
            api_key: Google Gemini API key
            model_name: Gemini model to use (default: gemini-2.0-flash-exp)
            temperature: Model temperature (0.0-1.0, higher = more creative)
            enable_web_search: Enable web search capability (requires setup)
            enable_code_execution: Enable Python code execution in sandbox
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        
        # Use hybrid agent internally
        self._hybrid_agent = create_hybrid_agent(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            enable_web_search=enable_web_search,
            enable_code_execution=enable_code_execution,
        )
        
        logger.info(
            f"✅ FiscalDocumentAgent initialized: model={model_name}, "
            f"temp={temperature}, web={enable_web_search}, code={enable_code_execution}"
        )

    def chat(self, message: str) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User message

        Returns:
            Agent response
        """
        return self._hybrid_agent.chat(message)
    
    async def achat(self, message: str) -> str:
        """
        Async version of chat.

        Args:
            message: User message

        Returns:
            Agent response
        """
        return await self._hybrid_agent.achat(message)

    def reset_memory(self) -> None:
        """Clear conversation history."""
        self._hybrid_agent.clear_memory()
        logger.info("🧹 Conversation memory cleared")

    def get_greeting(self) -> str:
        """Get initial greeting message."""
        return USER_GREETING
    
    def get_capabilities(self) -> dict:
        """Get agent capabilities information."""
        return self._hybrid_agent.get_capabilities()


def create_agent(
    api_key: str,
    model_name: str = "gemini-2.0-flash-exp",
    enable_web_search: bool = False,
    enable_code_execution: bool = True,
) -> FiscalDocumentAgent:
    """
    Factory function to create a fiscal document agent.

    Args:
        api_key: Google Gemini API key
        model_name: Gemini model to use (default: gemini-2.0-flash-exp)
        enable_web_search: Enable web search capability
        enable_code_execution: Enable Python code execution

    Returns:
        Initialized FiscalDocumentAgent
    """
    return FiscalDocumentAgent(
        api_key=api_key,
        model_name=model_name,
        enable_web_search=enable_web_search,
        enable_code_execution=enable_code_execution,
    )
