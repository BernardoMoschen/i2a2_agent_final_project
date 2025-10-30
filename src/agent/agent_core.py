"""Fiscal Document Agent core with LangChain and Gemini."""

import logging
from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.prompts import SYSTEM_PROMPT, USER_GREETING
from src.agent.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


class FiscalDocumentAgent:
    """
    LLM-powered agent for processing Brazilian fiscal documents.

    Uses Google Gemini with LangChain tools for parsing, validation,
    and answering questions about fiscal documents.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite", temperature: float = 0.3):
        """
        Initialize the agent.

        Args:
            api_key: Google Gemini API key
            model_name: Gemini model to use (default: gemini-2.5-flash-lite)
            temperature: Model temperature (0.0-1.0, lower = more deterministic)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            convert_system_message_to_human=True,  # Gemini requires this
        )

        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
        )

        # Create prompt template with system prompt embedded
        prompt_text = f"""
{SYSTEM_PROMPT}

FERRAMENTAS:
{{tools}}

FORMATO DE USO DAS FERRAMENTAS:
Para usar uma ferramenta, use este formato EXATO:

Thought: [seu raciocínio sobre o que fazer]
Action: [nome da ferramenta]
Action Input: [entrada para a ferramenta]
Observation: [resultado da ferramenta]

Quando tiver a resposta final:
Thought: Tenho a resposta final
Final Answer: [sua resposta ao usuário]

HISTÓRICO DA CONVERSA:
{{chat_history}}

PERGUNTA DO USUÁRIO: {{input}}

SEUS NOMES DE FERRAMENTAS: {{tool_names}}

{{agent_scratchpad}}
"""
        self.prompt = PromptTemplate.from_template(prompt_text)

        # Create agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=ALL_TOOLS,
            prompt=self.prompt,
        )

        # Create executor with better configuration for general questions
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=ALL_TOOLS,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,  # Increased to allow more tool usage
            early_stopping_method="generate",
            return_intermediate_steps=False,  # Cleaner output
        )

        logger.info(f"Agent initialized with model {model_name}")

    def chat(self, message: str) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User message

        Returns:
            Agent response
        """
        try:
            logger.info(f"Processing message: {message[:100]}...")

            # Pass only 'input' to avoid memory key conflict
            response = self.executor.invoke({"input": message})

            output = response.get("output", "")
            logger.info(f"Response generated: {output[:100]}...")

            return output

        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return f"❌ Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
            return f"❌ Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"

    def reset_memory(self) -> None:
        """Clear conversation history."""
        self.memory.clear()
        logger.info("Memory cleared")

    def get_greeting(self) -> str:
        """Get initial greeting message."""
        return USER_GREETING


def create_agent(api_key: str, model_name: str = "gemini-2.5-flash-lite") -> FiscalDocumentAgent:
    """
    Factory function to create a fiscal document agent.

    Args:
        api_key: Google Gemini API key
        model_name: Gemini model to use

    Returns:
        Configured FiscalDocumentAgent instance
    """
    return FiscalDocumentAgent(api_key=api_key, model_name=model_name)
