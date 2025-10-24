"""
NCM validator using official Brazilian government APIs.

Auto-downloads NCM table from official sources. Perfect for Streamlit Cloud deployment.
"""

import logging
from typing import Set, Optional, Dict

logger = logging.getLogger(__name__)


class NCMValidator:
    """
    Validate NCM codes against IBGE/TIPI table (auto-downloaded from APIs).
    
    NCM (Nomenclatura Comum do Mercosul) is an 8-digit code used to classify
    products for tax and customs purposes.
    
    Features:
    - Auto-downloads from official government APIs
    - 7-day cache (configurable)
    - No manual file management needed
    - Perfect for Streamlit Cloud deployment
    """
    
    def __init__(self):
        """Initialize NCM validator with auto-download from API."""
        self._valid_ncms: Set[str] = set()
        self._ncm_table: Dict[str, Dict] = {}
        self._load_ncm_table()
    
    def _load_ncm_table(self):
        """Load NCM codes from API (auto-downloads and caches)."""
        try:
            # Import here to avoid circular dependency
            from src.services.ncm_api import get_ncm_table
            
            # Auto-download from API (uses cache if valid)
            self._ncm_table = get_ncm_table()
            self._valid_ncms = set(self._ncm_table.keys())
            
            logger.info(f"Loaded {len(self._valid_ncms)} NCM codes from API/cache")
            
        except Exception as e:
            logger.error(f"Error loading NCM table from API: {e}")
            self._create_fallback_table()
    
    def _create_fallback_table(self):
        """
        Create minimal fallback table if API fails.
        
        This should rarely be needed - only if API is down AND cache expired.
        """
        logger.warning("Creating minimal fallback NCM table")
        
        # Minimal NCM subset (most common codes)
        fallback_ncms = {
            "19059090": {"description": "Pães, bolos, etc", "ipi_rate": "5"},
            "22030000": {"description": "Cerveja", "ipi_rate": "15"},
            "85171231": {"description": "Telefones celulares", "ipi_rate": "12"},
            "84713012": {"description": "Notebooks", "ipi_rate": "0"},
            "61091000": {"description": "Camisetas", "ipi_rate": "15"},
            "87032310": {"description": "Automóveis", "ipi_rate": "25"},
            "30049099": {"description": "Medicamentos", "ipi_rate": "0"},
        }
        
        self._ncm_table = fallback_ncms
        self._valid_ncms = set(fallback_ncms.keys())
        
        logger.info(f"Fallback table created with {len(self._valid_ncms)} NCM codes")
    
    def is_valid_ncm(self, ncm: str) -> bool:
        """
        Check if NCM code exists in the table.
        
        Args:
            ncm: NCM code (8 digits)
        
        Returns:
            True if NCM exists in table
        """
        if not ncm:
            return False
        
        ncm_clean = ncm.strip()
        
        # Basic format validation
        if not ncm_clean.isdigit() or len(ncm_clean) != 8:
            return False
        
        # If table is empty (error loading), be permissive (fail-safe)
        if not self._valid_ncms:
            logger.warning("NCM table is empty - validation skipped (fail-safe)")
            return True
        
        # Check if NCM exists in table
        return ncm_clean in self._valid_ncms
    
    def get_ncm_info(self, ncm: str) -> Optional[Dict]:
        """
        Get information about a specific NCM code.
        
        Args:
            ncm: NCM code (8 digits)
        
        Returns:
            Dict with {description, ipi_rate} or None if not found
        """
        if not ncm:
            return None
        
        ncm_clean = ncm.strip()
        return self._ncm_table.get(ncm_clean)
    
    def get_table_size(self) -> int:
        """Get number of NCM codes in table."""
        return len(self._valid_ncms)
    
    def refresh_table(self, force: bool = False):
        """
        Refresh NCM table from API.
        
        Args:
            force: Force download even if cache is valid
        """
        try:
            from src.services.ncm_api import get_ncm_table
            
            self._ncm_table = get_ncm_table(force_refresh=force)
            self._valid_ncms = set(self._ncm_table.keys())
            
            logger.info(f"Refreshed NCM table: {len(self._valid_ncms)} codes loaded")
            
        except Exception as e:
            logger.error(f"Error refreshing NCM table: {e}")


# Global instance (lazy loading)
_ncm_validator: Optional[NCMValidator] = None


def get_ncm_validator() -> NCMValidator:
    """
    Get global NCM validator instance (singleton).
    
    Returns:
        NCMValidator: Global validator instance
    """
    global _ncm_validator
    if _ncm_validator is None:
        _ncm_validator = NCMValidator()
    return _ncm_validator
