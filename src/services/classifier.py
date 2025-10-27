"""
Automatic document classifier for operation type and cost center.

Uses rule-based logic with LLM fallback for complex cases.
Includes intelligent caching to reduce LLM costs.
"""

import hashlib
import logging
from typing import Optional

from src.models import ClassificationResult, InvoiceModel

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """
    Classify fiscal documents by operation type and cost center.
    
    Classification logic:
    1. Operation Type: Based on CFOP (purchase/sale/service/transfer)
    2. Cost Center: Based on issuer, NCM, and business rules
    3. Intelligent caching to reduce LLM costs
    """

    # CFOP ranges for operation type classification
    CFOP_RANGES = {
        "purchase": [  # Compras/Entradas
            (1000, 1999),  # Entradas ou aquisições de serviços do estado
            (2000, 2999),  # Entradas ou aquisições de serviços de outros estados
            (3000, 3999),  # Entradas ou aquisições de serviços do exterior
        ],
        "sale": [  # Vendas/Saídas
            (5000, 5999),  # Saídas ou prestações de serviços para o estado
            (6000, 6999),  # Saídas ou prestações de serviços para outros estados
            (7000, 7999),  # Saídas ou prestações de serviços para o exterior
        ],
        "transfer": [  # Transferências
            (5151, 5152),  # Transferências
            (5155, 5156),
            (6151, 6152),
            (6155, 6156),
        ],
        "return": [  # Devoluções
            (1201, 1202),  # Devolução de venda
            (1410, 1411),
            (2201, 2202),
            (5201, 5202),  # Devolução de compra
            (5410, 5411),
            (6201, 6202),
        ],
    }

    # Default cost centers by NCM range (can be customized per company)
    NCM_COST_CENTERS = {
        # Technology/Electronics
        ("8471", "8473"): "TI - Equipamentos",
        ("8517", "8518"): "TI - Telecomunicações",
        
        # Office supplies
        ("4820", "4823"): "Administrativo - Material Escritório",
        ("9608", "9609"): "Administrativo - Material Escritório",
        
        # Services
        ("9999",): "Serviços Gerais",
        
        # Fuel/Energy
        ("2710", "2711"): "Operações - Combustível",
        ("2716",): "Operações - Energia",
    }

    def __init__(self, llm_client: Optional[object] = None, database_manager: Optional[object] = None):
        """
        Initialize classifier.
        
        Args:
            llm_client: Optional LLM client for complex classifications
            database_manager: Database manager for caching
        """
        self.llm_client = llm_client
        self.db = database_manager
        
        # Create instance copy of NCM mappings to avoid cross-test contamination
        self.ncm_cost_centers = self.NCM_COST_CENTERS.copy()
        
        logger.info("DocumentClassifier initialized with caching support")

    def _create_cache_key(self, invoice: InvoiceModel) -> str:
        """
        Create cache key from invoice characteristics.
        
        Key based on: issuer_cnpj + primary NCM + primary CFOP
        This ensures similar documents get same classification.
        """
        issuer = invoice.issuer_cnpj or "unknown"
        
        # Get primary item (first item, or could be highest value)
        if invoice.items and len(invoice.items) > 0:
            ncm = invoice.items[0].ncm or "unknown"
            cfop = invoice.items[0].cfop or "unknown"
        else:
            ncm = "unknown"
            cfop = "unknown"
        
        # Create hash
        key_string = f"{issuer}_{ncm}_{cfop}"
        return hashlib.sha256(key_string.encode()).hexdigest()
        
        logger.info("DocumentClassifier initialized with caching support")

    def _create_cache_key(self, invoice: InvoiceModel) -> str:
        """
        Create cache key from invoice characteristics.
        
        Key based on: issuer_cnpj + primary NCM + primary CFOP
        This ensures similar documents get same classification.
        """
        issuer = invoice.issuer_cnpj or "unknown"
        
        # Get primary item (first item, or could be highest value)
        if invoice.items and len(invoice.items) > 0:
            ncm = invoice.items[0].ncm or "unknown"
            cfop = invoice.items[0].cfop or "unknown"
        else:
            ncm = "unknown"
            cfop = "unknown"
        
        # Create hash
        key_string = f"{issuer}_{ncm}_{cfop}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def classify(self, invoice: InvoiceModel) -> ClassificationResult:
        """
        Classify document by operation type and cost center with caching.
        
        Args:
            invoice: Parsed invoice model
            
        Returns:
            ClassificationResult with operation type, cost center, and confidence
        """
        # Check cache first if database available
        if self.db:
            cache_key = self._create_cache_key(invoice)
            cached_result = self.db.get_classification_from_cache(cache_key)
            
            if cached_result:
                logger.info(f"Using cached classification for {invoice.document_key[:16]}...")
                return ClassificationResult(
                    operation_type=cached_result["operation_type"],
                    cost_center=cached_result["cost_center"],
                    confidence=cached_result["confidence"],
                    reasoning=cached_result.get("reasoning", "From cache"),
                    used_llm_fallback=cached_result.get("used_llm_fallback", False),
                )
        
        # Step 1: Classify operation type (rule-based)
        operation_type = self._classify_operation_type(invoice)
        
        # Step 2: Classify cost center (rule-based with LLM fallback)
        cost_center, confidence, reasoning, fallback = self._classify_cost_center(invoice)
        
        result = ClassificationResult(
            operation_type=operation_type,
            cost_center=cost_center,
            confidence=confidence,
            reasoning=reasoning,
            used_llm_fallback=fallback,
        )
        
        # Save to cache if database available
        if self.db:
            cache_key = self._create_cache_key(invoice)
            issuer_cnpj = invoice.issuer_cnpj or "unknown"
            ncm = invoice.items[0].ncm if invoice.items else None
            cfop = invoice.items[0].cfop if invoice.items else "unknown"
            
            self.db.save_classification_to_cache(
                cache_key=cache_key,
                issuer_cnpj=issuer_cnpj,
                ncm=ncm,
                cfop=cfop,
                classification={
                    "operation_type": operation_type,
                    "cost_center": cost_center,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "used_llm_fallback": fallback,
                },
            )
        
        return result

    def _classify_operation_type(self, invoice: InvoiceModel) -> str:
        """
        Classify operation type based on CFOP.
        
        Args:
            invoice: Invoice model
            
        Returns:
            Operation type: purchase, sale, transfer, return, or unknown
        """
        if not invoice.items:
            return "unknown"
        
        # Get most common CFOP from items
        cfops = [item.cfop for item in invoice.items if item.cfop]
        if not cfops:
            return "unknown"
        
        # Use first item's CFOP (could be enhanced to use majority vote)
        cfop = cfops[0]
        
        try:
            cfop_int = int(cfop)
        except (ValueError, TypeError):
            return "unknown"
        
        # Check against ranges
        for op_type, ranges in self.CFOP_RANGES.items():
            for min_cfop, max_cfop in ranges:
                if min_cfop <= cfop_int <= max_cfop:
                    logger.info(f"Classified as {op_type} based on CFOP {cfop}")
                    return op_type
        
        return "unknown"

    def _classify_cost_center(
        self, invoice: InvoiceModel
    ) -> tuple[str, float, str, bool]:
        """
        Classify cost center using rules and optionally LLM.
        
        Priority order:
        1. Issuer name patterns (high specificity)
        2. NCM code ranges
        3. LLM classification (if available)
        4. Generic fallback
        
        Args:
            invoice: Invoice model
            
        Returns:
            Tuple of (cost_center, confidence, reasoning, fallback_used)
        """
        # Priority 1: Rule-based by issuer name patterns (most specific)
        issuer_lower = invoice.issuer_name.lower()
        
        if any(word in issuer_lower for word in ["energia", "light", "cemig", "copel", "elektro"]):
            return "Operações - Energia", 0.9, "Issuer name indicates energy supplier", False
        
        if any(word in issuer_lower for word in ["telecom", "telefone", "internet", "vivo", "claro", "tim", "oi"]):
            return "TI - Telecomunicações", 0.9, "Issuer name indicates telecom", False
        
        if any(word in issuer_lower for word in ["papelaria", "office", "kalunga", "escritório"]):
            return "Administrativo - Material Escritório", 0.9, "Issuer name indicates office supplies", False
        
        # Priority 2: Rule-based classification by NCM
        if invoice.items:
            for item in invoice.items:
                if item.ncm:
                    ncm_prefix = item.ncm[:4] if len(item.ncm) >= 4 else item.ncm
                    
                    # Check NCM ranges
                    for ncm_range, cost_center in self.ncm_cost_centers.items():
                        for ncm_start in ncm_range:
                            if ncm_prefix.startswith(ncm_start):
                                reasoning = f"NCM {item.ncm} matched to {cost_center}"
                                logger.info(reasoning)
                                return cost_center, 0.85, reasoning, False
        
        # Priority 3: Fallback - Use LLM if available
        if self.llm_client:
            try:
                cost_center, reasoning = self._llm_classify(invoice)
                return cost_center, 0.7, reasoning, True
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}")
        
        # Priority 4: Final fallback - Generic
        return "Não Classificado", 0.3, "No matching rules found", True

    def _llm_classify(self, invoice: InvoiceModel) -> tuple[str, str]:
        """
        Use LLM to classify cost center for complex cases.
        
        Args:
            invoice: Invoice model
            
        Returns:
            Tuple of (cost_center, reasoning)
        """
        # Build context for LLM
        items_desc = ", ".join([
            f"{item.description[:30]} (NCM: {item.ncm or 'N/A'})"
            for item in invoice.items[:5]  # Limit to first 5 items
        ])
        
        prompt = f"""
Classifique o centro de custo para esta nota fiscal:

**Emitente:** {invoice.issuer_name}
**Itens:** {items_desc}
**Total:** R$ {invoice.total_invoice}

Centros de custo disponíveis:
- TI - Equipamentos
- TI - Telecomunicações
- Administrativo - Material Escritório
- Operações - Combustível
- Operações - Energia
- Serviços Gerais
- Não Classificado

Responda APENAS com o nome do centro de custo mais apropriado, seguido de "|" e uma breve justificativa.
Exemplo: "TI - Equipamentos|Compra de computadores e periféricos"
"""
        
        # Call LLM (implementation depends on LLM client interface)
        response = self._call_llm(prompt)
        
        # Parse response
        if "|" in response:
            cost_center, reasoning = response.split("|", 1)
            return cost_center.strip(), reasoning.strip()
        
        return "Não Classificado", "LLM response could not be parsed"

    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM client with prompt.
        
        Args:
            prompt: Classification prompt
            
        Returns:
            LLM response text
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured")
        
        # This is a placeholder - actual implementation depends on LLM client
        # For Gemini (langchain):
        # response = self.llm_client.invoke(prompt)
        # return response.content
        
        # For now, raise to indicate LLM is not configured
        raise NotImplementedError("LLM classification not yet implemented")

    def update_ncm_mappings(self, mappings: dict[tuple[str, ...], str]) -> None:
        """
        Update NCM to cost center mappings.
        
        Args:
            mappings: Dictionary of NCM prefixes to cost centers
        """
        self.ncm_cost_centers.update(mappings)
        logger.info(f"Updated NCM mappings: {len(mappings)} entries")

    def get_available_cost_centers(self) -> list[str]:
        """
        Get list of available cost centers.
        
        Returns:
            List of unique cost center names
        """
        return sorted(set(self.ncm_cost_centers.values()))
