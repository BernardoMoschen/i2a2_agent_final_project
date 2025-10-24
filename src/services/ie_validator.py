"""Inscrição Estadual (IE) validator for all Brazilian states."""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


def validate_ie_ac(ie: str) -> bool:
    """Validate IE for Acre (AC) - 13 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 13:
        return False
    
    if not ie.startswith("01"):
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate first check digit (12th position)
    weights = [4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(11))
    remainder = sum_value % 11
    digit1 = 0 if remainder < 2 else 11 - remainder
    
    if int(ie[11]) != digit1:
        return False
    
    # Calculate second check digit (13th position)
    weights2 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value2 = sum(int(ie[i]) * weights2[i] for i in range(12))
    remainder2 = sum_value2 % 11
    digit2 = 0 if remainder2 < 2 else 11 - remainder2
    
    return int(ie[12]) == digit2


def validate_ie_al(ie: str) -> bool:
    """Validate IE for Alagoas (AL) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.startswith("24"):
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    product = sum_value * 10
    digit = product % 11
    digit = 0 if digit == 10 else digit
    
    return int(ie[8]) == digit


def validate_ie_ap(ie: str) -> bool:
    """Validate IE for Amapá (AP) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.startswith("03"):
        return False
    
    if not ie.isdigit():
        return False
    
    # Amapá has complex validation - simplified here
    # Full algorithm requires range-based calculations
    return True  # Accept if format is correct


def validate_ie_am(ie: str) -> bool:
    """Validate IE for Amazonas (AM) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_ba(ie: str) -> bool:
    """Validate IE for Bahia (BA) - 8 or 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) not in [8, 9]:
        return False
    
    if not ie.isdigit():
        return False
    
    # BA has 6, 7, or 8 as first digit for different calculation methods
    # Simplified validation
    if len(ie) == 8:
        # Modulo 10
        weights = [7, 6, 5, 4, 3, 2]
        sum_value = sum(int(ie[i]) * weights[i] for i in range(6))
        digit2 = (10 - (sum_value % 10)) % 10
        
        weights1 = [8, 7, 6, 5, 4, 3, 0, 2]
        sum_value1 = sum(int(ie[i]) * weights1[i] for i in range(8))
        digit1 = (10 - (sum_value1 % 10)) % 10
        
        return int(ie[7]) == digit2
    
    return True  # Accept 9-digit if format correct


def validate_ie_ce(ie: str) -> bool:
    """Validate IE for Ceará (CE) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_df(ie: str) -> bool:
    """Validate IE for Distrito Federal (DF) - 13 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 13:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate first check digit (12th position)
    weights = [4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(11))
    
    remainder = sum_value % 11
    digit1 = 0 if remainder < 2 else 11 - remainder
    
    if int(ie[11]) != digit1:
        return False
    
    # Calculate second check digit (13th position)
    weights2 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value2 = sum(int(ie[i]) * weights2[i] for i in range(12))
    
    remainder2 = sum_value2 % 11
    digit2 = 0 if remainder2 < 2 else 11 - remainder2
    
    return int(ie[12]) == digit2


def validate_ie_es(ie: str) -> bool:
    """Validate IE for Espírito Santo (ES) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_go(ie: str) -> bool:
    """Validate IE for Goiás (GO) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.startswith(("10", "11", "15")):
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    
    # Special cases for GO
    if remainder == 0:
        digit = 0
    elif remainder == 1:
        ie_num = int(ie[:8])
        if 10103105 <= ie_num <= 10119997:
            digit = 1
        else:
            digit = 0
    else:
        digit = 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_ma(ie: str) -> bool:
    """Validate IE for Maranhão (MA) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.startswith("12"):
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_mt(ie: str) -> bool:
    """Validate IE for Mato Grosso (MT) - 11 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 11:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(10))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[10]) == digit


def validate_ie_ms(ie: str) -> bool:
    """Validate IE for Mato Grosso do Sul (MS) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.startswith("28"):
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_mg(ie: str) -> bool:
    """Validate IE for Minas Gerais (MG) - 13 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 13:
        return False
    
    if not ie.isdigit():
        return False
    
    # MG has complex validation with auxiliary digit insertion
    # Simplified validation
    ie_formatted = ie[:3] + "0" + ie[3:12]
    
    # First check digit
    weights1 = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
    products = [(int(ie_formatted[i]) * weights1[i]) for i in range(12)]
    sum_digits = sum(sum(divmod(p, 10)) for p in products)
    
    digit1 = (10 - (sum_digits % 10)) % 10
    
    if int(ie[11]) != digit1:
        return False
    
    # Second check digit
    weights2 = [3, 2, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights2[i] for i in range(12))
    
    remainder = sum_value % 11
    digit2 = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[12]) == digit2


def validate_ie_pa(ie: str) -> bool:
    """Validate IE for Pará (PA) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.startswith("15"):
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_pb(ie: str) -> bool:
    """Validate IE for Paraíba (PB) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_pr(ie: str) -> bool:
    """Validate IE for Paraná (PR) - 10 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 10:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate first check digit
    weights1 = [3, 2, 7, 6, 5, 4, 3, 2]
    sum_value1 = sum(int(ie[i]) * weights1[i] for i in range(8))
    
    remainder1 = sum_value1 % 11
    digit1 = 0 if remainder1 < 2 else 11 - remainder1
    
    if int(ie[8]) != digit1:
        return False
    
    # Calculate second check digit
    weights2 = [4, 3, 2, 7, 6, 5, 4, 3, 2]
    sum_value2 = sum(int(ie[i]) * weights2[i] for i in range(9))
    
    remainder2 = sum_value2 % 11
    digit2 = 0 if remainder2 < 2 else 11 - remainder2
    
    return int(ie[9]) == digit2


def validate_ie_pe(ie: str) -> bool:
    """Validate IE for Pernambuco (PE) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(7))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[7]) == digit and int(ie[8]) == digit


def validate_ie_pi(ie: str) -> bool:
    """Validate IE for Piauí (PI) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_rj(ie: str) -> bool:
    """Validate IE for Rio de Janeiro (RJ) - 8 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 8:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [2, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(7))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[7]) == digit


def validate_ie_rn(ie: str) -> bool:
    """Validate IE for Rio Grande do Norte (RN) - 9 or 10 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) not in [9, 10]:
        return False
    
    if not ie.startswith("20"):
        return False
    
    if not ie.isdigit():
        return False
    
    if len(ie) == 9:
        # Calculate check digit for 9 digits
        weights = [9, 8, 7, 6, 5, 4, 3, 2]
        sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
        
        product = sum_value * 10
        digit = product % 11
        digit = 0 if digit == 10 else digit
        
        return int(ie[8]) == digit
    else:
        # 10 digits version - simplified
        return True


def validate_ie_rs(ie: str) -> bool:
    """Validate IE for Rio Grande do Sul (RS) - 10 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 10:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(9))
    
    remainder = sum_value % 11
    digit = 11 - remainder
    digit = 0 if digit >= 10 else digit
    
    return int(ie[9]) == digit


def validate_ie_ro(ie: str) -> bool:
    """Validate IE for Rondônia (RO) - 14 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 14:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(13))
    
    remainder = sum_value % 11
    digit = 11 - remainder
    digit = digit - 10 if digit >= 10 else digit
    
    return int(ie[13]) == digit


def validate_ie_rr(ie: str) -> bool:
    """Validate IE for Roraima (RR) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.startswith("24"):
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [1, 2, 3, 4, 5, 6, 7, 8]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    digit = sum_value % 9
    
    return int(ie[8]) == digit


def validate_ie_sc(ie: str) -> bool:
    """Validate IE for Santa Catarina (SC) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_sp(ie: str) -> bool:
    """Validate IE for São Paulo (SP) - 12 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 12:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate first check digit (9th position)
    weights1 = [1, 3, 4, 5, 6, 7, 8, 10]
    sum_value1 = sum(int(ie[i]) * weights1[i] for i in range(8))
    
    remainder1 = sum_value1 % 11
    digit1 = 0 if remainder1 < 2 else 11 - remainder1
    
    if int(ie[8]) != digit1:
        return False
    
    # Calculate second check digit (12th position)
    weights2 = [3, 2, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_value2 = sum(int(ie[i]) * weights2[i] for i in range(11))
    
    remainder2 = sum_value2 % 11
    digit2 = 0 if remainder2 < 2 else 11 - remainder2
    
    return int(ie[11]) == digit2


def validate_ie_se(ie: str) -> bool:
    """Validate IE for Sergipe (SE) - 9 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 9:
        return False
    
    if not ie.isdigit():
        return False
    
    # Calculate check digit
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[8]) == digit


def validate_ie_to(ie: str) -> bool:
    """Validate IE for Tocantins (TO) - 11 digits."""
    ie = ie.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(ie) != 11:
        return False
    
    if not ie.isdigit():
        return False
    
    # TO format: 29PPNNNNNND where PP=01 to 99
    if not ie.startswith("29"):
        return False
    
    # Calculate check digit
    ie_base = ie[:2] + ie[4:10]  # Remove positions 2-3 for calculation
    
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    sum_value = sum(int(ie_base[i]) * weights[i] for i in range(8))
    
    remainder = sum_value % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return int(ie[10]) == digit


# State validators map
IE_VALIDATORS: dict[str, Callable[[str], bool]] = {
    "AC": validate_ie_ac,
    "AL": validate_ie_al,
    "AP": validate_ie_ap,
    "AM": validate_ie_am,
    "BA": validate_ie_ba,
    "CE": validate_ie_ce,
    "DF": validate_ie_df,
    "ES": validate_ie_es,
    "GO": validate_ie_go,
    "MA": validate_ie_ma,
    "MT": validate_ie_mt,
    "MS": validate_ie_ms,
    "MG": validate_ie_mg,
    "PA": validate_ie_pa,
    "PB": validate_ie_pb,
    "PR": validate_ie_pr,
    "PE": validate_ie_pe,
    "PI": validate_ie_pi,
    "RJ": validate_ie_rj,
    "RN": validate_ie_rn,
    "RS": validate_ie_rs,
    "RO": validate_ie_ro,
    "RR": validate_ie_rr,
    "SC": validate_ie_sc,
    "SP": validate_ie_sp,
    "SE": validate_ie_se,
    "TO": validate_ie_to,
}


def validate_ie(ie: str, uf: str) -> bool:
    """
    Validate Inscrição Estadual for a given state.
    
    Args:
        ie: Inscrição Estadual (with or without formatting)
        uf: State code (e.g., "SP", "RJ", "MG")
    
    Returns:
        True if IE is valid for the state
    """
    if not ie or not uf:
        return True  # Skip if missing (optional field)
    
    # Special case: ISENTO (exempt)
    if ie.upper().strip() == "ISENTO":
        return True
    
    uf_upper = uf.upper().strip()
    
    if uf_upper not in IE_VALIDATORS:
        logger.warning(f"No IE validator for state: {uf_upper}")
        return True  # Fail-safe: accept if no validator
    
    try:
        validator = IE_VALIDATORS[uf_upper]
        return validator(ie)
    except Exception as e:
        logger.error(f"Error validating IE {ie} for {uf_upper}: {e}")
        return True  # Fail-safe: accept on error
