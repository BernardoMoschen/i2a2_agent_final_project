"""Hybrid agent combining specialized fiscal tools with native LLM capabilities.

This agent acts like ChatGPT/Claude but with access to:
1. Native LLM reasoning (answer questions, write code, explain concepts)
2. Specialized fiscal tools (database, reports, validation)
3. Dynamic capabilities (web search, code execution)
"""

import logging
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.language_models import BaseChatModel
from langchain_experimental.tools import PythonREPLTool
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


# ========== ENHANCED SYSTEM PROMPT ==========
HYBRID_SYSTEM_PROMPT = """You are a highly capable AI assistant specializing in fiscal document processing, but with UNRESTRICTED general intelligence.

🎯 YOUR CAPABILITIES (3 TIERS):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 1: NATIVE INTELLIGENCE (always available)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You have FULL ACCESS to your training data and reasoning capabilities:

✅ Answer general questions (math, history, coding, etc.)
✅ Explain fiscal/tax concepts without needing tools
✅ Perform calculations and logical reasoning
✅ Write code examples and tutorials
✅ Provide advice and recommendations
✅ Translate between languages
✅ Summarize and analyze text

**EXAMPLE QUERIES YOU CAN ANSWER DIRECTLY:**
- "What is ICMS?" → Explain from your knowledge
- "Calculate 18% of R$ 1000" → Do the math directly (R$ 180,00)
- "Write Python code to parse CSV" → Generate code
- "What's the difference between NFe and NFCe?" → Explain
- "How does depreciation work?" → Use accounting knowledge
- "Translate this to English: ..." → Translate directly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 2: SPECIALIZED TOOLS (fiscal domain)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use these tools ONLY when you need to:
- Access the fiscal documents database
- Generate reports/exports
- Validate specific documents
- Classify invoices
- Archive files

**WHEN TO USE TOOLS:**
- User asks: "How many invoices do we have?" → Use search_invoices_database
- User asks: "Generate tax report" → Use fiscal_report_export
- User asks: "Validate this CNPJ: 12345678000190" → Use validate_cnpj

**WHEN NOT TO USE TOOLS:**
- User asks: "What is a CNPJ?" → Answer directly from knowledge
- User asks: "How to calculate ICMS?" → Explain the formula
- User asks: "Write code to validate CNPJ" → Generate Python code

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 3: DYNAMIC CAPABILITIES (when tools aren't enough)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You have access to:

🌐 **web_search**: Search the internet for current information
   - Use when: user asks about current events, recent laws, external data
   - Example: "What are the new 2024 SPED fiscal changes?"
   - Example: "What's the current SELIC rate?"

🐍 **python_repl**: Execute Python code in a safe sandbox
   - Use when: complex calculations, data manipulation, visualization
   - Example: "Calculate compound interest for 10 years at 5%"
   - Example: "Parse this JSON and extract supplier names"
   - Example: "Find outliers in this data: [1, 2, 3, 100, 2, 3]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 DECISION TREE (follow this logic):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **CAN I ANSWER FROM MY KNOWLEDGE?**
   → YES: Answer directly (no tools needed)
   → NO: Go to step 2

2. **DOES IT REQUIRE DATABASE/FILES ACCESS?**
   → YES: Use fiscal tools (search_invoices, generate_report, etc.)
   → NO: Go to step 3

3. **DOES IT REQUIRE EXTERNAL DATA?**
   → Current events/laws: Use web_search
   → Complex computation: Use python_repl
   → Both: Chain tools as needed

4. **STILL CAN'T SOLVE?**
   → Explain what you CAN do
   → Suggest how user can rephrase
   → Offer partial solutions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ IMPORTANT RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:
- Answer conceptual questions directly (no tool needed)
- Use tools ONLY when accessing data/performing actions
- Combine multiple tools when needed
- Execute Python for complex math/data manipulation
- Search web for current/external information
- Be transparent about what you're doing
- Show your reasoning process

❌ DON'T:
- Say "I can't help" when you CAN answer from knowledge
- Use tools for questions you can answer directly
- Refuse to write code/do math/explain concepts
- Limit yourself to just fiscal domain
- Use tools unnecessarily

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 RESPONSE STYLE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Be conversational and helpful
- Show reasoning steps for complex problems
- Format code with syntax highlighting using ```python blocks
- Use emojis for clarity (✅❌🎯📊 etc.)
- Cite sources when using web search
- Explain tool usage when you use them ("I'm searching the database...")
- When you can't find exact data, offer alternatives

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 LANGUAGE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Respond in the same language as the user
- Support both Portuguese and English
- Be natural and conversational

You are ChatGPT-level capable, but with specialized fiscal tools. Act accordingly!
"""


class HybridFiscalAgent:
    """
    Hybrid agent with fiscal tools + native LLM capabilities.
    
    This agent combines:
    - Native LLM reasoning (explanations, calculations, code generation)
    - Specialized fiscal tools (database, reports, validation)
    - Dynamic capabilities (web search, code execution)
    """
    
    def __init__(
        self,
        gemini_api_key: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        enable_web_search: bool = False,  # Disabled by default (requires setup)
        enable_code_execution: bool = True,
    ):
        """
        Initialize hybrid agent.
        
        Args:
            gemini_api_key: Google Gemini API key
            model_name: Gemini model to use (default: gemini-2.0-flash-exp)
            temperature: LLM temperature (0.0-1.0, higher = more creative)
            enable_web_search: Enable internet search capability
            enable_code_execution: Enable Python code execution
        """
        self.model_name = model_name
        self.temperature = temperature
        self.llm = self._create_llm(gemini_api_key, model_name, temperature)
        self.tools = self._build_tool_list(enable_web_search, enable_code_execution)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=4000,  # Prevent memory overflow
        )
        self.agent_executor = self._create_agent_executor()
        
        logger.info(
            f"✅ Initialized hybrid agent: model={model_name}, "
            f"tools={len(self.tools)}, web_search={enable_web_search}, "
            f"code_exec={enable_code_execution}"
        )
    
    def _create_llm(
        self,
        api_key: str,
        model_name: str,
        temperature: float,
    ) -> BaseChatModel:
        """Create Gemini LLM instance."""
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            convert_system_message_to_human=True,
        )
    
    def _build_tool_list(
        self,
        enable_web_search: bool,
        enable_code_execution: bool,
    ) -> List:
        """Build complete tool list (fiscal + dynamic)."""
        tools = list(ALL_TOOLS)  # Start with fiscal tools
        
        # Add web search capability
        if enable_web_search:
            try:
                web_search = DuckDuckGoSearchRun(
                    name="web_search",
                    description=(
                        "🌐 Search the internet for current information. "
                        "Use this when:\n"
                        "- User asks about recent laws/regulations\n"
                        "- Need current tax rates or external data\n"
                        "- Questions about events after your training cutoff\n"
                        "- Validating information with official sources\n\n"
                        "Input: search query as string\n"
                        "Returns: search results with sources"
                    ),
                )
                tools.append(web_search)
                logger.info("✅ Web search enabled (DuckDuckGo)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to enable web search: {e}")
        
        # Add Python code execution
        if enable_code_execution:
            try:
                python_repl = PythonREPLTool(
                    name="python_repl",
                    description=(
                        "🐍 Execute Python code in a safe sandbox. "
                        "Use this when:\n"
                        "- Complex calculations (compound interest, statistics)\n"
                        "- Data manipulation (parsing, filtering, aggregating)\n"
                        "- String processing, regex, date arithmetic\n"
                        "- Mathematical operations beyond simple arithmetic\n\n"
                        "⚠️ SECURITY: Only standard library + common packages available.\n"
                        "❌ NO: file I/O, network requests, subprocess, eval\n\n"
                        "Input: valid Python code as string\n"
                        "Returns: execution result or error message\n\n"
                        "Example:\n"
                        "```python\n"
                        "# Calculate compound interest\n"
                        "principal = 10000\n"
                        "rate = 0.05\n"
                        "years = 10\n"
                        "result = principal * (1 + rate) ** years\n"
                        "print(f'Final value: R$ {result:,.2f}')\n"
                        "```"
                    ),
                )
                tools.append(python_repl)
                logger.info("✅ Python code execution enabled (safe sandbox)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to enable code execution: {e}")
        
        logger.info(f"📦 Total tools available: {len(tools)}")
        return tools
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create LangChain agent executor with ReAct pattern."""
        
        # Create prompt with system message
        prompt = ChatPromptTemplate.from_messages([
            ("system", HYBRID_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        
        # Create ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        # Create executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,  # Show reasoning steps in logs
            handle_parsing_errors=True,
            max_iterations=10,  # Allow complex multi-step reasoning
            early_stopping_method="generate",
        )
    
    def chat(self, message: str) -> str:
        """
        Process user message and return response.
        
        This method handles:
        - Native LLM responses (no tools)
        - Tool-based responses (database, reports, etc.)
        - Hybrid responses (combining multiple tools)
        
        Args:
            message: User's input message
            
        Returns:
            Agent's response (may include tool outputs)
        """
        try:
            logger.info(f"🗣️ Processing query: {message[:100]}...")
            
            result = self.agent_executor.invoke({"input": message})
            
            response = result.get("output", "")
            
            # Log tool usage for analytics
            intermediate_steps = result.get("intermediate_steps", [])
            if intermediate_steps:
                tools_used = [step[0].tool for step in intermediate_steps]
                logger.info(f"🔧 Tools used: {tools_used}")
            else:
                logger.info("🧠 Native LLM response (no tools used)")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in chat: {e}", exc_info=True)
            return self._graceful_error_response(message, str(e))
    
    async def achat(self, message: str) -> str:
        """
        Async version of chat.
        
        Args:
            message: User's input message
            
        Returns:
            Agent's response
        """
        # TODO: Implement true async with ainvoke
        return self.chat(message)
    
    def _graceful_error_response(self, query: str, error: str) -> str:
        """Provide helpful response even when errors occur."""
        return f"""😔 I encountered an error while processing your request: **"{query}"**

❌ **Error:** {error}

But I'm still here to help! Here's what you can do:

1️⃣ **Try rephrasing** - Break your question into smaller parts
2️⃣ **Simplify** - Remove complex filters or conditions
3️⃣ **Ask differently** - Use alternative wording

💡 **Things I can definitely help with:**
- Explain fiscal concepts (ICMS, CFOP, NFe, etc.)
- Answer general questions (math, programming, etc.)
- Search the database for documents
- Generate reports and exports
- Validate documents and data

🆘 **Need ideas?** Try asking:
- "What can you do?"
- "Show me example queries"
- "Explain [concept]"
"""
    
    def clear_memory(self):
        """Clear conversation history."""
        self.memory.clear()
        logger.info("🧹 Conversation memory cleared")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about agent's capabilities.
        
        Returns:
            Dictionary with capabilities information
        """
        tool_names = [tool.name for tool in self.tools]
        
        has_web_search = "web_search" in tool_names
        has_code_exec = "python_repl" in tool_names
        
        fiscal_tools = [
            name for name in tool_names
            if name not in ["web_search", "python_repl"]
        ]
        
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "total_tools": len(self.tools),
            "fiscal_tools": len(fiscal_tools),
            "fiscal_tool_names": fiscal_tools,
            "web_search_enabled": has_web_search,
            "code_execution_enabled": has_code_exec,
            "capabilities": {
                "native_intelligence": {
                    "enabled": True,
                    "features": [
                        "Answer general questions",
                        "Explain concepts",
                        "Perform calculations",
                        "Write code examples",
                        "Translate languages",
                    ],
                },
                "specialized_tools": {
                    "enabled": True,
                    "count": len(fiscal_tools),
                    "features": [
                        "Database access",
                        "Report generation",
                        "Document validation",
                        "Classification",
                        "Archiving",
                    ],
                },
                "dynamic_capabilities": {
                    "web_search": has_web_search,
                    "code_execution": has_code_exec,
                },
            },
        }


def create_hybrid_agent(
    api_key: str,
    model_name: str = "gemini-2.0-flash-exp",
    temperature: float = 0.7,
    enable_web_search: bool = False,
    enable_code_execution: bool = True,
) -> HybridFiscalAgent:
    """
    Factory function to create a hybrid fiscal agent.
    
    Args:
        api_key: Google Gemini API key
        model_name: Model to use (default: gemini-2.0-flash-exp)
        temperature: Temperature for LLM responses (0.0-1.0)
        enable_web_search: Enable web search capability
        enable_code_execution: Enable Python code execution
        
    Returns:
        Initialized HybridFiscalAgent instance
    """
    return HybridFiscalAgent(
        gemini_api_key=api_key,
        model_name=model_name,
        temperature=temperature,
        enable_web_search=enable_web_search,
        enable_code_execution=enable_code_execution,
    )
