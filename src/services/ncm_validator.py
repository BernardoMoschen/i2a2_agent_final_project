"""NCM validator using IBGE/TIPI table."""

import csv
import logging
from pathlib import Path
from typing import Set

import httpx

logger = logging.getLogger(__name__)


class NCMValidator:
    """
    Validate NCM codes against IBGE/TIPI table.
    
    NCM (Nomenclatura Comum do Mercosul) is an 8-digit code used to classify
    products for tax and customs purposes.
    """
    
    # Simplified NCM table URL (we'll use a hardcoded subset for now)
    # In production, download from: https://www.gov.br/receitafederal/
    VALID_NCM_FILE = Path(__file__).parent.parent.parent / "data" / "ncm_codes.csv"
    
    def __init__(self):
        """Initialize NCM validator."""
        self._valid_ncms: Set[str] = set()
        self._load_ncm_table()
    
    def _load_ncm_table(self):
        """Load NCM codes from local file or create default table."""
        if self.VALID_NCM_FILE.exists():
            try:
                with open(self.VALID_NCM_FILE, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ncm = row.get("ncm", "").strip()
                        if ncm and len(ncm) == 8 and ncm.isdigit():
                            self._valid_ncms.add(ncm)
                
                logger.info(f"Loaded {len(self._valid_ncms)} NCM codes from {self.VALID_NCM_FILE}")
            except Exception as e:
                logger.error(f"Error loading NCM table: {e}")
                self._create_default_table()
        else:
            logger.warning(f"NCM table not found at {self.VALID_NCM_FILE} - creating default table")
            self._create_default_table()
    
    def _create_default_table(self):
        """
        Create a default NCM table with common codes.
        
        In production, this should download the full table from Receita Federal.
        For now, we'll use a subset of common NCMs.
        """
        # Common NCMs from various sectors
        common_ncms = [
            # Food & Beverages
            "19059090",  # Pães, bolos, etc
            "22030000",  # Cerveja
            "22021000",  # Água mineral
            "04022110",  # Leite em pó
            "02013000",  # Carne bovina fresca/refrigerada
            
            # Electronics
            "85171231",  # Telefones celulares
            "84713012",  # Notebooks
            "85176255",  # Adaptadores/carregadores
            "84717012",  # Unidades de disco rígido
            
            # Clothing
            "61091000",  # Camisetas de algodão
            "62034200",  # Calças jeans
            "64039900",  # Calçados
            
            # Automotive
            "87032310",  # Automóveis 1.0-1.5
            "40111000",  # Pneus novos
            "87089900",  # Peças para veículos
            
            # Pharmaceuticals
            "30049099",  # Medicamentos
            "30051010",  # Curativos
            
            # Construction
            "68109900",  # Materiais de construção
            "25232900",  # Cimento portland
            "44111390",  # Painéis de fibra
            
            # Office supplies
            "48201000",  # Cadernos
            "96081099",  # Canetas
            "84433210",  # Impressoras
        ]
        
        self._valid_ncms = set(common_ncms)
        
        # Create data directory if doesn't exist
        self.VALID_NCM_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save default table
        try:
            with open(self.VALID_NCM_FILE, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["ncm", "description"])
                writer.writeheader()
                for ncm in sorted(self._valid_ncms):
                    writer.writerow({"ncm": ncm, "description": f"NCM {ncm}"})
            
            logger.info(f"Created default NCM table with {len(self._valid_ncms)} codes at {self.VALID_NCM_FILE}")
        except Exception as e:
            logger.error(f"Error creating default NCM table: {e}")
    
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
    
    def get_table_size(self) -> int:
        """Get number of NCM codes in table."""
        return len(self._valid_ncms)
    
    async def download_full_ncm_table(self, url: str | None = None) -> bool:
        """
        Download full NCM table from official source.
        
        This is a placeholder - in production, implement download from:
        https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/
        
        Args:
            url: Optional custom URL for NCM table
        
        Returns:
            True if download successful
        """
        logger.warning("Full NCM table download not yet implemented")
        logger.warning("Using default subset of common NCM codes")
        return False


# Global instance (lazy loading)
_ncm_validator: NCMValidator | None = None


def get_ncm_validator() -> NCMValidator:
    """Get global NCM validator instance (singleton)."""
    global _ncm_validator
    if _ncm_validator is None:
        _ncm_validator = NCMValidator()
    return _ncm_validator
