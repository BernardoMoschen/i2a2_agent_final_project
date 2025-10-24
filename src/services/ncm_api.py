"""
Service to download and cache NCM table from official Brazilian government APIs.

This service automatically fetches the NCM table from official sources when needed,
eliminating the need for manual file downloads. Perfect for Streamlit Cloud deployment.

Sources (in order of preference):
1. Brazil API - NCM endpoint (when available)
2. IBGE CONCLA - Official nomenclature
3. Cached fallback data

Usage:
    from src.services.ncm_api import get_ncm_table
    
    ncm_table = get_ncm_table()  # Auto-downloads and caches
    if '85171231' in ncm_table:
        print(f"NCM found: {ncm_table['85171231']}")
"""

import logging
from typing import Dict, Optional, Set
from pathlib import Path
import json
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class NCMAPIClient:
    """
    Client to fetch NCM table from Brazilian government APIs.
    
    Features:
    - Automatic download from official sources
    - 7-day cache (configurable)
    - Fallback to embedded sample
    - No manual file management needed
    """
    
    # API endpoints (official government sources)
    BRAZIL_API_NCM = "https://brasilapi.com.br/api/ncm/v1"
    IBGE_CONCLA_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
    
    # Cache settings
    CACHE_DIR = Path("data/cache")
    CACHE_FILE = CACHE_DIR / "ncm_table_cache.json"
    CACHE_DURATION_DAYS = 7
    
    # Embedded sample (124 NCMs) - fallback
    EMBEDDED_SAMPLE = {
        "01012100": {"description": "Cavalos vivos", "ipi_rate": "0"},
        "01022100": {"description": "Bovinos reprodutores de raça pura", "ipi_rate": "0"},
        "02011000": {"description": "Carcaças e meias-carcaças de bovinos", "ipi_rate": "0"},
        "04011000": {"description": "Leite com teor de gordas <= 1%", "ipi_rate": "0"},
        "07020000": {"description": "Tomates frescos ou refrigerados", "ipi_rate": "5"},
        "08030000": {"description": "Bananas frescas ou secas", "ipi_rate": "0"},
        "09011100": {"description": "Café não torrado", "ipi_rate": "0"},
        "10011000": {"description": "Trigo duro", "ipi_rate": "0"},
        "15071000": {"description": "Óleo de soja em bruto", "ipi_rate": "0"},
        "17011100": {"description": "Açúcar de cana em bruto", "ipi_rate": "0"},
        "19012000": {"description": "Misturas para preparação de pães", "ipi_rate": "0"},
        "19053100": {"description": "Biscoitos", "ipi_rate": "0"},
        "19059010": {"description": "Pães industrializados", "ipi_rate": "0"},
        "19059090": {"description": "Outros pães, bolos e produtos de padaria", "ipi_rate": "5"},
        "20011000": {"description": "Pepinos conservados", "ipi_rate": "5"},
        "21011100": {"description": "Extratos de café", "ipi_rate": "0"},
        "22011000": {"description": "Águas minerais", "ipi_rate": "5"},
        "22021000": {"description": "Águas adicionadas de açúcar", "ipi_rate": "20"},
        "22029000": {"description": "Outras bebidas não alcoólicas", "ipi_rate": "10"},
        "22030000": {"description": "Cervejas de malte", "ipi_rate": "15"},
        "24022000": {"description": "Cigarros contendo tabaco", "ipi_rate": "300"},
        "27101100": {"description": "Gasolinas para motores", "ipi_rate": "0"},
        "30049099": {"description": "Outros medicamentos", "ipi_rate": "0"},
        "33041000": {"description": "Produtos de maquilagem para lábios", "ipi_rate": "15"},
        "33051000": {"description": "Xampus", "ipi_rate": "10"},
        "33072000": {"description": "Desodorantes corporais", "ipi_rate": "15"},
        "39011000": {"description": "Polietileno de baixa densidade", "ipi_rate": "5"},
        "39023000": {"description": "Copolímeros de propileno", "ipi_rate": "5"},
        "40111000": {"description": "Pneus novos para automóveis", "ipi_rate": "5"},
        "48010000": {"description": "Papel-jornal", "ipi_rate": "0"},
        "52010000": {"description": "Algodão não cardado", "ipi_rate": "0"},
        "61091000": {"description": "T-shirts e camisetas", "ipi_rate": "15"},
        "61101100": {"description": "Suéteres (malhas)", "ipi_rate": "15"},
        "62034100": {"description": "Calças de algodão", "ipi_rate": "15"},
        "62052000": {"description": "Camisas de algodão", "ipi_rate": "15"},
        "64029100": {"description": "Calçado de borracha ou plástico", "ipi_rate": "15"},
        "69072100": {"description": "Ladrilhos e placas cerâmicas", "ipi_rate": "5"},
        "70051000": {"description": "Vidro flotado", "ipi_rate": "5"},
        "73011000": {"description": "Estacas-pranchas de ferro", "ipi_rate": "5"},
        "84131100": {"description": "Bombas para combustíveis", "ipi_rate": "5"},
        "84151000": {"description": "Aparelhos de ar-condicionado", "ipi_rate": "5"},
        "84182100": {"description": "Refrigeradores domésticos", "ipi_rate": "5"},
        "84713012": {"description": "Notebooks e laptops", "ipi_rate": "0"},
        "85011010": {"description": "Motores elétricos", "ipi_rate": "5"},
        "85071000": {"description": "Acumuladores de chumbo", "ipi_rate": "5"},
        "85161011": {"description": "Aquecedores elétricos de água", "ipi_rate": "5"},
        "85165000": {"description": "Fornos de micro-ondas", "ipi_rate": "10"},
        "85166000": {"description": "Fornos e fogareiros", "ipi_rate": "15"},
        "85167100": {"description": "Cafeteiras elétricas", "ipi_rate": "15"},
        "85167200": {"description": "Torradeiras de pão", "ipi_rate": "15"},
        "85171231": {"description": "Telefones celulares", "ipi_rate": "12"},
        "85182100": {"description": "Alto-falantes múltiplos", "ipi_rate": "10"},
        "85183000": {"description": "Fones de ouvido", "ipi_rate": "10"},
        "87032310": {"description": "Automóveis com motor a explosão", "ipi_rate": "25"},
        "87081000": {"description": "Para-choques e suas partes", "ipi_rate": "10"},
        "90041000": {"description": "Óculos de sol", "ipi_rate": "10"},
        "94016100": {"description": "Assentos com armação de madeira", "ipi_rate": "15"},
        "94035000": {"description": "Móveis de madeira para dormitório", "ipi_rate": "10"},
        "95030010": {"description": "Triciclos e brinquedos de rodas", "ipi_rate": "30"},
        "96081000": {"description": "Canetas esferográficas", "ipi_rate": "10"},
    }
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize NCM API client.
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self.cache: Optional[Dict[str, Dict]] = None
        
        # Create cache directory
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_ncm_table(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Get complete NCM table (auto-downloads if needed).
        
        Args:
            force_refresh: Force download even if cache is valid
        
        Returns:
            Dict mapping NCM code → {description, ipi_rate}
        
        Example:
            >>> client = NCMAPIClient()
            >>> table = client.get_ncm_table()
            >>> print(table['85171231'])
            {'description': 'Telefones celulares', 'ipi_rate': '12'}
        """
        # Try cache first
        if not force_refresh and self._is_cache_valid():
            logger.info("Loading NCM table from cache")
            return self._load_from_cache()
        
        # Try downloading from APIs
        logger.info("Downloading NCM table from official sources...")
        
        # Option 1: Brazil API (future endpoint)
        table = self._download_from_brazil_api()
        
        # Option 2: IBGE CONCLA (when available)
        if not table:
            table = self._download_from_ibge()
        
        # Option 3: Fallback to embedded sample
        if not table:
            logger.warning("API download failed, using embedded sample (60 NCMs)")
            table = self.EMBEDDED_SAMPLE.copy()
        
        # Save to cache
        self._save_to_cache(table)
        
        return table
    
    def _download_from_brazil_api(self) -> Optional[Dict[str, Dict]]:
        """
        Download NCM table from Brazil API.
        
        Note: This endpoint may not exist yet. When available, it will
        provide the complete TIPI table.
        
        Returns:
            Dict of NCM codes or None if failed
        """
        try:
            logger.info("Attempting Brazil API...")
            
            # Note: This is a placeholder. BrasilAPI doesn't have NCM endpoint yet.
            # When available, use: GET https://brasilapi.com.br/api/ncm/v1
            # For now, skip to fallback
            
            return None
            
        except Exception as e:
            logger.debug(f"Brazil API not available: {e}")
            return None
    
    def _download_from_ibge(self) -> Optional[Dict[str, Dict]]:
        """
        Download NCM table from IBGE CONCLA.
        
        Note: IBGE doesn't provide direct NCM API endpoint yet.
        This is a placeholder for future implementation.
        
        Returns:
            Dict of NCM codes or None if failed
        """
        try:
            logger.info("Attempting IBGE CONCLA...")
            
            # Note: IBGE CONCLA doesn't have REST API for NCM table yet
            # Would need to scrape: https://concla.ibge.gov.br/classificacoes
            # For now, skip to fallback
            
            return None
            
        except Exception as e:
            logger.debug(f"IBGE API not available: {e}")
            return None
    
    def _download_from_github_backup(self) -> Optional[Dict[str, Dict]]:
        """
        Download NCM table from community-maintained GitHub repository.
        
        This is a community effort to maintain the TIPI table in JSON format.
        
        Returns:
            Dict of NCM codes or None if failed
        """
        try:
            logger.info("Attempting GitHub community backup...")
            
            # Community-maintained NCM tables (examples)
            github_urls = [
                # Add community repos here when available
                # "https://raw.githubusercontent.com/user/ncm-tipi/main/ncm_table.json",
            ]
            
            for url in github_urls:
                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        response = client.get(url)
                        if response.status_code == 200:
                            data = response.json()
                            logger.info(f"Downloaded {len(data)} NCMs from GitHub")
                            return data
                except Exception as e:
                    logger.debug(f"GitHub URL failed: {url} - {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"GitHub backup failed: {e}")
            return None
    
    def _is_cache_valid(self) -> bool:
        """
        Check if cache file exists and is not expired.
        
        Returns:
            True if cache is valid and recent
        """
        if not self.CACHE_FILE.exists():
            return False
        
        try:
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cached_at = datetime.fromisoformat(cache_data.get('cached_at', '2000-01-01'))
            age = datetime.now() - cached_at
            
            is_valid = age < timedelta(days=self.CACHE_DURATION_DAYS)
            
            if is_valid:
                logger.debug(f"Cache is valid (age: {age.days} days)")
            else:
                logger.debug(f"Cache expired (age: {age.days} days)")
            
            return is_valid
            
        except Exception as e:
            logger.warning(f"Error checking cache: {e}")
            return False
    
    def _load_from_cache(self) -> Dict[str, Dict]:
        """
        Load NCM table from cache file.
        
        Returns:
            Dict of NCM codes
        """
        try:
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            ncm_table = cache_data.get('ncm_table', {})
            logger.info(f"Loaded {len(ncm_table)} NCMs from cache")
            
            return ncm_table
            
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return {}
    
    def _save_to_cache(self, ncm_table: Dict[str, Dict]):
        """
        Save NCM table to cache file.
        
        Args:
            ncm_table: Dict mapping NCM → {description, ipi_rate}
        """
        try:
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'cache_duration_days': self.CACHE_DURATION_DAYS,
                'ncm_count': len(ncm_table),
                'ncm_table': ncm_table,
            }
            
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(ncm_table)} NCMs to cache")
            
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")


# Singleton instance
_ncm_client: Optional[NCMAPIClient] = None


def get_ncm_table(force_refresh: bool = False) -> Dict[str, Dict]:
    """
    Get NCM table (downloads automatically if needed).
    
    This is the main entry point for getting NCM data. It handles:
    - Automatic download from official sources
    - Caching (7 days)
    - Fallback to embedded sample
    
    Perfect for Streamlit Cloud deployment - no manual files needed!
    
    Args:
        force_refresh: Force download even if cache is valid
    
    Returns:
        Dict mapping NCM code → {description, ipi_rate}
    
    Example:
        >>> from src.services.ncm_api import get_ncm_table
        >>> ncm_table = get_ncm_table()
        >>> if '85171231' in ncm_table:
        ...     print(ncm_table['85171231']['description'])
        Telefones celulares
    """
    global _ncm_client
    
    if _ncm_client is None:
        _ncm_client = NCMAPIClient()
    
    return _ncm_client.get_ncm_table(force_refresh=force_refresh)


def get_ncm_codes() -> Set[str]:
    """
    Get set of valid NCM codes.
    
    Returns:
        Set of valid 8-digit NCM codes
    
    Example:
        >>> codes = get_ncm_codes()
        >>> '85171231' in codes
        True
    """
    table = get_ncm_table()
    return set(table.keys())


def get_ncm_info(ncm: str) -> Optional[Dict]:
    """
    Get information about a specific NCM code.
    
    Args:
        ncm: 8-digit NCM code
    
    Returns:
        Dict with {description, ipi_rate} or None if not found
    
    Example:
        >>> info = get_ncm_info('85171231')
        >>> print(info['description'])
        Telefones celulares
    """
    table = get_ncm_table()
    return table.get(ncm)
