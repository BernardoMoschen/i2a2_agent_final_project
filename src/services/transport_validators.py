"""External validators for CTe and MDFe transport documents."""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ===== MODAL DE TRANSPORTE (Transport Mode) =====
VALID_MODALS = {
    "01": "Rodoviário",
    "02": "Aéreo",
    "03": "Aquaviário",
    "04": "Ferroviário",
    "05": "Dutoviário",
    "06": "Multimodal"
}


def validate_modal(modal: Optional[str]) -> bool:
    """
    Validate transport modal code.
    
    Valid modals (as per SEFAZ specification):
    - 01: Rodoviário (Road)
    - 02: Aéreo (Air)
    - 03: Aquaviário (Water)
    - 04: Ferroviário (Rail)
    - 05: Dutoviário (Pipeline)
    - 06: Multimodal
    
    Args:
        modal: Modal code (2 digits)
    
    Returns:
        True if modal is valid
    """
    if not modal:
        return True  # Skip if missing (caught by other rule)
    
    return modal.strip() in VALID_MODALS


def get_modal_description(modal: str) -> str:
    """Get human-readable modal description."""
    return VALID_MODALS.get(modal, "Desconhecido")


# ===== RNTRC (Registro Nacional de Transportadores Rodoviários de Carga) =====
def validate_rntrc_format(rntrc: Optional[str]) -> bool:
    """
    Validate RNTRC format (8 digits).
    
    RNTRC is the national registration for road cargo carriers.
    Format: 8 numeric digits (XXXXXXXX)
    
    Args:
        rntrc: RNTRC code
    
    Returns:
        True if format is valid
    """
    if not rntrc:
        return True  # Skip if missing (optional in some cases)
    
    # Remove formatting
    rntrc_clean = rntrc.replace(".", "").replace("-", "").replace("/", "").strip()
    
    # Must be exactly 8 digits
    return rntrc_clean.isdigit() and len(rntrc_clean) == 8


# ===== PLACA DE VEÍCULO (Vehicle Plate) =====
def validate_vehicle_plate(plate: Optional[str]) -> bool:
    """
    Validate Brazilian vehicle plate format.
    
    Supports both formats:
    - Old format: ABC1234 (3 letters + 4 digits)
    - Mercosul format: ABC1D23 (3 letters + 1 digit + 1 letter + 2 digits)
    
    Args:
        plate: Vehicle plate
    
    Returns:
        True if format is valid
    """
    if not plate:
        return True  # Skip if missing (optional in some cases)
    
    plate_clean = plate.replace("-", "").replace(" ", "").upper().strip()
    
    # Old format: ABC1234
    old_pattern = r'^[A-Z]{3}\d{4}$'
    
    # Mercosul format: ABC1D23
    mercosul_pattern = r'^[A-Z]{3}\d[A-Z]\d{2}$'
    
    return bool(re.match(old_pattern, plate_clean) or re.match(mercosul_pattern, plate_clean))


# ===== CFOP ESPECÍFICOS PARA TRANSPORTE =====
TRANSPORT_CFOP_RANGES = {
    # Entry (Inbound transport)
    "1": ["1351", "1352", "1353", "1354", "1355", "1356", "1357", "1359"],
    "2": ["2351", "2352", "2353", "2354", "2355", "2356", "2357", "2359"],
    # Exit (Outbound transport)
    "5": ["5351", "5352", "5353", "5354", "5355", "5356", "5357", "5359"],
    "6": ["6351", "6352", "6353", "6354", "6355", "6356", "6357", "6359"],
}


def validate_cfop_for_transport(cfop: Optional[str]) -> bool:
    """
    Validate CFOP is appropriate for transport services (CTe).
    
    Valid CFOPs for transport services:
    - 1351-1359: Entry (within state)
    - 2351-2359: Entry (outside state)
    - 5351-5359: Exit (within state)
    - 6351-6359: Exit (outside state)
    
    Args:
        cfop: CFOP code (4 digits)
    
    Returns:
        True if CFOP is valid for transport
    """
    if not cfop or len(cfop) != 4:
        return True  # Skip if invalid format (caught by other rule)
    
    # Check if CFOP is in transport ranges
    first_digit = cfop[0]
    if first_digit in TRANSPORT_CFOP_RANGES:
        return cfop in TRANSPORT_CFOP_RANGES[first_digit]
    
    return False


# ===== UF (ESTADO) VALIDATIONS =====
VALID_UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]


def validate_uf(uf: Optional[str]) -> bool:
    """Validate Brazilian state (UF) code."""
    if not uf:
        return True  # Skip if missing
    
    return uf.strip().upper() in VALID_UFS


def validate_uf_route(route_ufs: List[str]) -> bool:
    """
    Validate UF route for MDFe (no duplicates, valid states).
    
    Args:
        route_ufs: List of UF codes in route order
    
    Returns:
        True if route is valid
    """
    if not route_ufs:
        return True  # Skip if missing
    
    # All UFs must be valid
    if not all(validate_uf(uf) for uf in route_ufs):
        return False
    
    # No duplicate UFs in route
    if len(route_ufs) != len(set(route_ufs)):
        return False
    
    return True


# ===== TOMADOR DO SERVIÇO (Service Payer) =====
VALID_TOMADOR_TYPES = {
    "0": "Remetente",
    "1": "Expedidor",
    "2": "Recebedor",
    "3": "Destinatário",
    "4": "Outros"
}


def validate_tomador_type(tomador: Optional[str]) -> bool:
    """
    Validate tomador (service payer) type for CTe.
    
    Valid types:
    - 0: Remetente (Sender)
    - 1: Expedidor (Shipper)
    - 2: Recebedor (Receiver)
    - 3: Destinatário (Recipient)
    - 4: Outros (Other)
    
    Args:
        tomador: Tomador type code
    
    Returns:
        True if valid
    """
    if not tomador:
        return True  # Skip if missing
    
    return tomador.strip() in VALID_TOMADOR_TYPES


# ===== PESO (WEIGHT) VALIDATIONS =====
def validate_weight(weight: Optional[float], min_weight: float = 0.001) -> bool:
    """
    Validate weight value (must be positive and reasonable).
    
    Args:
        weight: Weight in kg
        min_weight: Minimum acceptable weight
    
    Returns:
        True if weight is valid
    """
    if weight is None:
        return True  # Skip if missing
    
    # Weight must be positive and above minimum
    return weight >= min_weight


# ===== TIPO DE EMISSÃO (Emission Type) =====
VALID_EMISSION_TYPES = {
    "1": "Normal",
    "4": "EPEC (Evento Prévio de Emissão em Contingência)",
    "5": "Contingência FS-DA",
    "7": "Autorização pela SVC (SEFAZ Virtual de Contingência)",
    "8": "Contingência SVC-RS"
}


def validate_emission_type(tp_emis: Optional[str]) -> bool:
    """
    Validate emission type (tpEmis) for CTe/MDFe.
    
    Args:
        tp_emis: Emission type code
    
    Returns:
        True if valid
    """
    if not tp_emis:
        return True  # Skip if missing
    
    return tp_emis.strip() in VALID_EMISSION_TYPES


# ===== ONLINE VALIDATION (ANTT - Agência Nacional de Transportes Terrestres) =====
class ANTTValidator:
    """Validator for ANTT (transport agency) registrations."""
    
    def __init__(self, timeout: float = 5.0, enable_cache: bool = True):
        """
        Initialize ANTT validator.
        
        Args:
            timeout: Request timeout in seconds
            enable_cache: Enable caching of validation results
        """
        self.timeout = timeout
        self.enable_cache = enable_cache
        self._cache: Dict[str, bool] = {}
    
    def validate_rntrc_active(self, rntrc: str) -> bool:
        """
        Validate if RNTRC is active with ANTT (online check).
        
        Note: This is a placeholder for future implementation.
        The actual ANTT API requires authentication and has usage limits.
        
        Args:
            rntrc: RNTRC code to validate
        
        Returns:
            True if RNTRC is active (or validation cannot be performed - fail-safe)
        """
        # Check cache first
        if self.enable_cache and rntrc in self._cache:
            logger.debug(f"RNTRC {rntrc} validation from cache: {self._cache[rntrc]}")
            return self._cache[rntrc]
        
        try:
            # TODO: Implement actual ANTT API call
            # For now, we perform only format validation
            logger.info(f"ANTT online validation for RNTRC {rntrc} not implemented - using format validation only")
            
            is_valid = validate_rntrc_format(rntrc)
            
            # Cache result
            if self.enable_cache:
                self._cache[rntrc] = is_valid
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Error validating RNTRC {rntrc} with ANTT: {e}")
            return True  # Fail-safe: don't block on API errors


# ===== SEFAZ PORTAL VALIDATION (Access Key Verification) =====
class SEFAZTransportValidator:
    """Validator for CTe/MDFe using SEFAZ web services."""
    
    def __init__(self, timeout: float = 10.0, enable_cache: bool = True):
        """
        Initialize SEFAZ transport validator.
        
        Args:
            timeout: Request timeout in seconds
            enable_cache: Enable caching of validation results
        """
        self.timeout = timeout
        self.enable_cache = enable_cache
        self._cache: Dict[str, Dict] = {}
    
    def validate_cte_key_online(self, access_key: str) -> bool:
        """
        Validate CTe access key with SEFAZ (online check).
        
        Uses SEFAZ public consultation service to verify if CTe exists
        and is authorized.
        
        Note: This is a placeholder for future implementation.
        Actual implementation would use SOAP/REST APIs from SEFAZ.
        
        Args:
            access_key: 44-digit CTe access key
        
        Returns:
            True if CTe is authorized (or validation cannot be performed - fail-safe)
        """
        # Check cache first
        if self.enable_cache and access_key in self._cache:
            cached = self._cache[access_key]
            logger.debug(f"CTe {access_key} validation from cache: {cached.get('authorized', False)}")
            return cached.get('authorized', True)
        
        try:
            # TODO: Implement SEFAZ CTe consultation
            # URL pattern: https://www.cte.fazenda.gov.br/portal/consulta.aspx?chCTe={access_key}
            
            logger.info(f"SEFAZ online CTe validation for {access_key} not implemented - skipping")
            
            # For now, assume valid if format is correct
            is_valid = len(access_key) == 44 and access_key.isdigit()
            
            # Cache result
            if self.enable_cache:
                self._cache[access_key] = {'authorized': is_valid}
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Error validating CTe key {access_key} with SEFAZ: {e}")
            return True  # Fail-safe
    
    def validate_mdfe_key_online(self, access_key: str) -> bool:
        """
        Validate MDFe access key with SEFAZ (online check).
        
        Similar to CTe validation but for MDFe documents.
        
        Args:
            access_key: 44-digit MDFe access key
        
        Returns:
            True if MDFe is authorized (or validation cannot be performed - fail-safe)
        """
        # Check cache first
        if self.enable_cache and access_key in self._cache:
            cached = self._cache[access_key]
            logger.debug(f"MDFe {access_key} validation from cache: {cached.get('authorized', False)}")
            return cached.get('authorized', True)
        
        try:
            # TODO: Implement SEFAZ MDFe consultation
            # URL pattern: https://mdfe-portal.sefaz.rs.gov.br/Site/Consulta
            
            logger.info(f"SEFAZ online MDFe validation for {access_key} not implemented - skipping")
            
            # For now, assume valid if format is correct
            is_valid = len(access_key) == 44 and access_key.isdigit()
            
            # Cache result
            if self.enable_cache:
                self._cache[access_key] = {'authorized': is_valid}
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Error validating MDFe key {access_key} with SEFAZ: {e}")
            return True  # Fail-safe


# ===== CONVENIENCE FUNCTIONS =====
def get_antt_validator(timeout: float = 5.0, enable_cache: bool = True) -> ANTTValidator:
    """Get singleton ANTT validator instance."""
    return ANTTValidator(timeout=timeout, enable_cache=enable_cache)


def get_sefaz_transport_validator(timeout: float = 10.0, enable_cache: bool = True) -> SEFAZTransportValidator:
    """Get singleton SEFAZ transport validator instance."""
    return SEFAZTransportValidator(timeout=timeout, enable_cache=enable_cache)
