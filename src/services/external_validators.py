"""External API validators for fiscal document validation."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CNPJData:
    """CNPJ data from external API."""

    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str]
    situacao: str  # ATIVA | BAIXADA | SUSPENSA | INAPTA | NULA
    uf: str
    municipio: str
    cep: str
    logradouro: str
    numero: str
    bairro: str
    complemento: Optional[str]
    email: Optional[str]
    telefone: Optional[str]
    data_abertura: str
    natureza_juridica: str
    porte: str  # ME | EPP | DEMAIS
    capital_social: float
    cnae_fiscal: str
    cnae_fiscal_descricao: str
    
    # Regime tributário (quando disponível)
    simples_nacional: Optional[bool] = None
    mei: Optional[bool] = None


class CNPJValidator:
    """
    Validate CNPJ using BrasilAPI.
    
    Free API with no rate limits for reasonable use.
    https://brasilapi.com.br/docs#tag/CNPJ
    """
    
    BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"
    CACHE_TTL = timedelta(hours=24)
    
    def __init__(self, timeout: float = 10.0):
        """
        Initialize CNPJ validator.
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self._cache = {}
        self._cache_timestamps = {}
    
    @lru_cache(maxsize=500)
    def _format_cnpj(self, cnpj: str) -> str:
        """Format CNPJ to digits only."""
        return cnpj.replace(".", "").replace("/", "").replace("-", "").strip()
    
    def _is_cache_valid(self, cnpj: str) -> bool:
        """Check if cached data is still valid."""
        if cnpj not in self._cache_timestamps:
            return False
        
        age = datetime.now() - self._cache_timestamps[cnpj]
        return age < self.CACHE_TTL
    
    async def validate_cnpj_async(self, cnpj: str) -> Optional[CNPJData]:
        """
        Validate CNPJ asynchronously using BrasilAPI.
        
        Args:
            cnpj: CNPJ with or without formatting
            
        Returns:
            CNPJData if valid, None if invalid or API error
        """
        cnpj_clean = self._format_cnpj(cnpj)
        
        # Check cache
        if self._is_cache_valid(cnpj_clean):
            logger.info(f"Using cached CNPJ data for {cnpj_clean}")
            return self._cache[cnpj_clean]
        
        url = f"{self.BASE_URL}/{cnpj_clean}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    cnpj_data = self._parse_response(data)
                    
                    # Cache result
                    self._cache[cnpj_clean] = cnpj_data
                    self._cache_timestamps[cnpj_clean] = datetime.now()
                    
                    logger.info(f"CNPJ {cnpj_clean} validated: {cnpj_data.situacao}")
                    return cnpj_data
                    
                elif response.status_code == 404:
                    logger.warning(f"CNPJ {cnpj_clean} not found in Receita Federal database")
                    return None
                    
                else:
                    logger.error(f"BrasilAPI error for CNPJ {cnpj_clean}: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.warning(f"BrasilAPI timeout for CNPJ {cnpj_clean}")
            return None
            
        except httpx.RequestError as e:
            logger.error(f"BrasilAPI request error for CNPJ {cnpj_clean}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error validating CNPJ {cnpj_clean}: {e}")
            return None
    
    def validate_cnpj(self, cnpj: str) -> Optional[CNPJData]:
        """
        Validate CNPJ synchronously (wrapper for async method).
        
        Args:
            cnpj: CNPJ with or without formatting
            
        Returns:
            CNPJData if valid, None if invalid or API error
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.validate_cnpj_async(cnpj))
    
    def _parse_response(self, data: dict) -> CNPJData:
        """Parse BrasilAPI response into CNPJData."""
        return CNPJData(
            cnpj=data.get("cnpj", ""),
            razao_social=data.get("razao_social", ""),
            nome_fantasia=data.get("nome_fantasia"),
            situacao=data.get("descricao_situacao_cadastral", "DESCONHECIDA"),
            uf=data.get("uf", ""),
            municipio=data.get("municipio", ""),
            cep=data.get("cep", ""),
            logradouro=data.get("logradouro", ""),
            numero=data.get("numero", ""),
            bairro=data.get("bairro", ""),
            complemento=data.get("complemento"),
            email=data.get("email"),
            telefone=data.get("ddd_telefone_1"),
            data_abertura=data.get("data_inicio_atividade", ""),
            natureza_juridica=data.get("natureza_juridica", ""),
            porte=data.get("porte", ""),
            capital_social=float(data.get("capital_social", 0)),
            cnae_fiscal=data.get("cnae_fiscal", ""),
            cnae_fiscal_descricao=data.get("cnae_fiscal_descricao", ""),
            simples_nacional=data.get("opcao_pelo_simples"),
            mei=data.get("opcao_pelo_mei"),
        )
    
    def is_cnpj_active(self, cnpj: str) -> bool:
        """
        Check if CNPJ is active (quick check).
        
        Args:
            cnpj: CNPJ with or without formatting
            
        Returns:
            True if active, False if not or if API error (fail-safe)
        """
        cnpj_data = self.validate_cnpj(cnpj)
        
        if cnpj_data is None:
            # Fail-safe: if API is down, don't block processing
            logger.warning(f"Could not validate CNPJ {cnpj} - assuming valid")
            return True
        
        return cnpj_data.situacao == "ATIVA"
    
    def validate_razao_social(self, cnpj: str, declared_name: str, threshold: float = 0.8) -> bool:
        """
        Validate if declared razão social matches official data.
        
        Uses fuzzy matching to handle minor variations.
        
        Args:
            cnpj: CNPJ with or without formatting
            declared_name: Declared razão social from invoice
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if names match within threshold
        """
        cnpj_data = self.validate_cnpj(cnpj)
        
        if cnpj_data is None:
            # Fail-safe: if API is down, don't block processing
            return True
        
        # Normalize for comparison
        official_name = cnpj_data.razao_social.upper().strip()
        declared_name = declared_name.upper().strip()
        
        # Exact match
        if official_name == declared_name:
            return True
        
        # Fuzzy match using simple similarity
        similarity = self._calculate_similarity(official_name, declared_name)
        
        logger.info(f"Razão social similarity for CNPJ {cnpj}: {similarity:.2%}")
        logger.info(f"  Official: {official_name}")
        logger.info(f"  Declared: {declared_name}")
        
        return similarity >= threshold
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein-like metric.
        
        Simple implementation without external dependencies.
        """
        # Remove common business terms for better matching
        common_terms = [
            "LTDA", "EIRELI", "S/A", "S.A.", "ME", "EPP", "CIA", "& CIA",
            "EMPRESA", "INDIVIDUAL", "DE RESPONSABILIDADE", "LIMITADA"
        ]
        
        for term in common_terms:
            str1 = str1.replace(term, "").strip()
            str2 = str2.replace(term, "").strip()
        
        # Simple character-level similarity
        if not str1 or not str2:
            return 0.0
        
        # Count matching characters in order
        matches = sum(c1 == c2 for c1, c2 in zip(str1, str2))
        max_len = max(len(str1), len(str2))
        
        return matches / max_len if max_len > 0 else 0.0
    
    def validate_uf(self, cnpj: str, declared_uf: str) -> bool:
        """
        Validate if declared UF matches CNPJ registration.
        
        Args:
            cnpj: CNPJ with or without formatting
            declared_uf: Declared UF from invoice
            
        Returns:
            True if UF matches
        """
        cnpj_data = self.validate_cnpj(cnpj)
        
        if cnpj_data is None:
            return True  # Fail-safe
        
        return cnpj_data.uf.upper() == declared_uf.upper()


class CEPValidator:
    """
    Validate CEP using ViaCEP API.
    
    Free API with reasonable rate limits.
    https://viacep.com.br/
    """
    
    BASE_URL = "https://viacep.com.br/ws"
    
    def __init__(self, timeout: float = 5.0):
        """Initialize CEP validator."""
        self.timeout = timeout
    
    async def validate_cep_async(self, cep: str) -> Optional[dict]:
        """
        Validate CEP asynchronously.
        
        Args:
            cep: CEP with or without formatting
            
        Returns:
            CEP data if valid, None if invalid
        """
        cep_clean = cep.replace("-", "").strip()
        url = f"{self.BASE_URL}/{cep_clean}/json/"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # ViaCEP returns {"erro": true} for invalid CEPs
                    if "erro" in data:
                        logger.warning(f"CEP {cep_clean} not found")
                        return None
                    
                    logger.info(f"CEP {cep_clean} validated: {data.get('localidade')}/{data.get('uf')}")
                    return data
                    
                else:
                    logger.error(f"ViaCEP error for CEP {cep_clean}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error validating CEP {cep_clean}: {e}")
            return None
    
    def validate_cep(self, cep: str) -> Optional[dict]:
        """Validate CEP synchronously."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.validate_cep_async(cep))
    
    def validate_cep_municipio(self, cep: str, municipio: str, uf: str) -> bool:
        """
        Validate if CEP matches município and UF.
        
        Args:
            cep: CEP with or without formatting
            municipio: Expected município
            uf: Expected UF
            
        Returns:
            True if matches
        """
        cep_data = self.validate_cep(cep)
        
        if cep_data is None:
            return True  # Fail-safe
        
        # Normalize for comparison
        cep_municipio = cep_data.get("localidade", "").upper().strip()
        cep_uf = cep_data.get("uf", "").upper().strip()
        
        municipio = municipio.upper().strip()
        uf = uf.upper().strip()
        
        return cep_municipio == municipio and cep_uf == uf
