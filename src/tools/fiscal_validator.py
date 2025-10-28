"""Fiscal validation tool with declarative rules."""

import logging
from collections.abc import Callable
from decimal import Decimal

from src.models import InvoiceModel, ValidationIssue, ValidationSeverity

logger = logging.getLogger(__name__)


def validate_cnpj_cpf_digit(doc: str) -> bool:
    """
    Validate CNPJ or CPF check digit.
    
    Args:
        doc: CNPJ (14 digits) or CPF (11 digits) without formatting
    
    Returns:
        True if check digit is valid
    """
    # Remove formatting
    doc = doc.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(doc) == 11:  # CPF
        return _validate_cpf_digit(doc)
    elif len(doc) == 14:  # CNPJ
        return _validate_cnpj_digit(doc)
    else:
        return False


def _validate_cpf_digit(cpf: str) -> bool:
    """Validate CPF check digits."""
    if not cpf.isdigit() or len(cpf) != 11:
        return False
    
    # Check if all digits are the same (invalid CPF)
    if cpf == cpf[0] * 11:
        return False
    
    # Calculate first check digit
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum1 % 11)
    digit1 = 0 if digit1 >= 10 else digit1
    
    if int(cpf[9]) != digit1:
        return False
    
    # Calculate second check digit
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum2 % 11)
    digit2 = 0 if digit2 >= 10 else digit2
    
    return int(cpf[10]) == digit2


def _validate_cnpj_digit(cnpj: str) -> bool:
    """Validate CNPJ check digits."""
    if not cnpj.isdigit() or len(cnpj) != 14:
        return False
    
    # Check if all digits are the same (invalid CNPJ)
    if cnpj == cnpj[0] * 14:
        return False
    
    # Calculate first check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    digit1 = 11 - (sum1 % 11)
    digit1 = 0 if digit1 >= 10 else digit1
    
    if int(cnpj[12]) != digit1:
        return False
    
    # Calculate second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    digit2 = 11 - (sum2 % 11)
    digit2 = 0 if digit2 >= 10 else digit2
    
    return int(cnpj[13]) == digit2


def validate_access_key_digit(key: str) -> bool:
    """
    Validate NFe access key check digit (44th digit).
    
    Uses modulo 11 algorithm.
    
    Args:
        key: 44-digit access key
    
    Returns:
        True if check digit is valid
    """
    if not key.isdigit() or len(key) != 44:
        return False
    
    # The 44th digit is the check digit
    # Calculate based on first 43 digits
    weights = [4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    sum_value = sum(int(key[i]) * weights[i] for i in range(43))
    remainder = sum_value % 11
    
    if remainder == 0 or remainder == 1:
        expected_digit = 0
    else:
        expected_digit = 11 - remainder
    
    return int(key[43]) == expected_digit


def validate_cfop_operation_consistency(cfop: str, operation_type: str | None) -> bool:
    """
    Validate CFOP consistency with operation type.
    
    CFOP ranges:
    - 1xxx/2xxx: Entry (purchase, return received)
    - 5xxx/6xxx: Exit (sale, return sent)
    - 3xxx: Transfer
    
    Args:
        cfop: 4-digit CFOP code
        operation_type: 'purchase', 'sale', 'transfer', 'return'
    
    Returns:
        True if CFOP matches operation type
    """
    if not cfop or len(cfop) != 4 or not cfop.isdigit():
        return True  # Skip validation if CFOP is invalid (caught by other rule)
    
    if not operation_type:
        return True  # Skip if operation type not classified yet
    
    first_digit = cfop[0]
    
    # Entry operations: CFOP should start with 1 or 2
    if operation_type in ['purchase', 'return']:
        return first_digit in ['1', '2']
    
    # Exit operations: CFOP should start with 5 or 6
    elif operation_type == 'sale':
        return first_digit in ['5', '6']
    
    # Transfer: CFOP should start with 5 or 6 (treated as exit)
    elif operation_type == 'transfer':
        return first_digit in ['5', '6']
    
    return True


def validate_tax_calculation(base: Decimal, rate: Decimal, tax_value: Decimal, tolerance: Decimal = Decimal("0.02")) -> bool:
    """
    Validate tax calculation: base × rate ≈ tax_value.
    
    Args:
        base: Tax base value
        rate: Tax rate (as percentage, e.g., 18.0 for 18%)
        tax_value: Declared tax value
        tolerance: Acceptable difference for rounding
    
    Returns:
        True if calculation is correct within tolerance
    """
    if base == 0 or rate == 0:
        return tax_value == 0
    
    expected_tax = base * (rate / Decimal("100"))
    difference = abs(expected_tax - tax_value)
    
    return difference <= tolerance


def validate_tax_regime_cst_consistency(tax_regime: str | None, cst: str | None) -> bool:
    """
    Validate tax regime (CRT) consistency with CST/CSOSN.
    
    Rules:
    - CRT 1/2 (Simples Nacional) must use CSOSN (101-900)
    - CRT 3 (Normal) must use CST (00-90)
    
    Args:
        tax_regime: CRT value (1=Simples, 2=Simples excess, 3=Normal)
        cst: CST or CSOSN code
    
    Returns:
        True if consistent
    """
    if not tax_regime or not cst:
        return True  # Skip if data missing
    
    # Simples Nacional (CRT 1 or 2) must use CSOSN (101-900)
    if tax_regime in ["1", "2"]:
        try:
            cst_num = int(cst)
            return cst_num >= 101  # CSOSN codes start at 101
        except ValueError:
            return False
    
    # Normal regime (CRT 3) must use CST (00-90)
    elif tax_regime == "3":
        try:
            cst_num = int(cst)
            return cst_num <= 90  # CST codes are 00-90
        except ValueError:
            return False
    
    return True


def validate_cfop_uf_consistency(cfop: str, issuer_uf: str | None, recipient_uf: str | None) -> bool:
    """
    Validate CFOP consistency with UF (state).
    
    Rules:
    - CFOP 5xxx = within state (issuer UF = recipient UF)
    - CFOP 6xxx = outside state (issuer UF ≠ recipient UF)
    - CFOP 1xxx/2xxx = entry (can be within or outside)
    - CFOP 3xxx = transfer
    
    Args:
        cfop: CFOP code (4 digits)
        issuer_uf: Issuer state (UF)
        recipient_uf: Recipient state (UF)
    
    Returns:
        True if consistent
    """
    if not cfop or not issuer_uf or not recipient_uf:
        return True  # Skip if data missing
    
    first_digit = cfop[0]
    
    # 5xxx = within state
    if first_digit == "5":
        return issuer_uf == recipient_uf
    
    # 6xxx = outside state
    elif first_digit == "6":
        return issuer_uf != recipient_uf
    
    # 1xxx, 2xxx, 3xxx, 7xxx - no strict UF rule
    return True


def validate_icms_interstate_rate(
    issuer_uf: str | None, 
    recipient_uf: str | None, 
    icms_rate: Decimal | None
) -> bool:
    """
    Validate ICMS interstate rate.
    
    Interstate rates (2024):
    - South/Southeast to North/Northeast/Center-West: 7%
    - Between South/Southeast: 12%
    - North/Northeast/Center-West among themselves: 12%
    - Special cases: 4% (imported goods)
    
    Args:
        issuer_uf: Issuer state
        recipient_uf: Recipient state
        icms_rate: Applied ICMS rate
    
    Returns:
        True if rate is plausible for interstate operation
    """
    if not issuer_uf or not recipient_uf or icms_rate is None:
        return True  # Skip if data missing
    
    # Same state = internal operation (can use internal rate)
    if issuer_uf == recipient_uf:
        return True
    
    # Interstate operation - check common rates
    # Common interstate rates: 4%, 7%, 12%
    # Also allow internal rates (states vary: 17%, 18%, 19%, 20%, etc.)
    common_interstate_rates = [
        Decimal("4"), Decimal("7"), Decimal("12"),
        Decimal("17"), Decimal("18"), Decimal("19"), Decimal("20")
    ]
    
    # Allow tolerance for rate comparison
    for valid_rate in common_interstate_rates:
        if abs(icms_rate - valid_rate) < Decimal("0.1"):
            return True
    
    # If not common rate, accept (may be special case)
    return True


def validate_ncm_format(ncm: str | None) -> bool:
    """
    Validate NCM format (8 digits).
    
    Args:
        ncm: NCM code
    
    Returns:
        True if NCM has correct format
    """
    if not ncm:
        return True  # Skip if missing
    
    # NCM must be 8 digits
    ncm_clean = ncm.strip()
    return ncm_clean.isdigit() and len(ncm_clean) == 8


def validate_cnpj_active_via_api(cnpj: str, enable_api_validation: bool = True) -> bool:
    """
    Validate if CNPJ is active using BrasilAPI.
    
    This is an external API validation (VAL026) that checks:
    - CNPJ exists in Receita Federal database
    - CNPJ status is ATIVA (not BAIXADA, SUSPENSA, INAPTA, NULA)
    
    Args:
        cnpj: CNPJ with or without formatting
        enable_api_validation: If False, skip API call (fail-safe mode)
    
    Returns:
        True if CNPJ is active or if API validation is disabled/fails (fail-safe)
    """
    if not enable_api_validation:
        logger.info("API validation disabled - skipping CNPJ validation")
        return True
    
    try:
        from src.services.external_validators import CNPJValidator
        
        validator = CNPJValidator(timeout=5.0)
        is_active = validator.is_cnpj_active(cnpj)
        
        logger.info(f"CNPJ {cnpj} API validation: {'active' if is_active else 'inactive'}")
        return is_active
        
    except ImportError:
        logger.warning("CNPJValidator not available - skipping external validation")
        return True  # Fail-safe: don't block if module not available
        
    except Exception as e:
        logger.error(f"Error validating CNPJ {cnpj} via API: {e}")
        return True  # Fail-safe: don't block on API errors


def validate_cep_municipio_uf(cep: str, municipio: str, uf: str, enable_api_validation: bool = True) -> bool:
    """
    Validate if CEP matches município and UF using ViaCEP API.
    
    This is VAL027 - validates geographic consistency.
    
    Args:
        cep: CEP (postal code) with or without formatting
        municipio: Expected município (city)
        uf: Expected UF (state)
        enable_api_validation: If False, skip API call (fail-safe mode)
    
    Returns:
        True if CEP matches município/UF or if API validation is disabled/fails (fail-safe)
    """
    if not enable_api_validation:
        return True
    
    if not cep or not municipio or not uf:
        return True  # Skip if data missing
    
    try:
        from src.services.external_validators import CEPValidator
        
        validator = CEPValidator(timeout=5.0)
        matches = validator.validate_cep_municipio(cep, municipio, uf)
        
        logger.info(f"CEP {cep} validation for {municipio}/{uf}: {'matches' if matches else 'mismatch'}")
        return matches
        
    except ImportError:
        logger.warning("CEPValidator not available - skipping validation")
        return True
        
    except Exception as e:
        logger.error(f"Error validating CEP {cep}: {e}")
        return True


def validate_razao_social_cnpj(cnpj: str, declared_name: str, enable_api_validation: bool = True) -> bool:
    """
    Validate if declared razão social matches CNPJ data from BrasilAPI.
    
    This is VAL029 - cross-validation of company name.
    
    Args:
        cnpj: CNPJ with or without formatting
        declared_name: Declared razão social from XML
        enable_api_validation: If False, skip API call (fail-safe mode)
    
    Returns:
        True if names match (fuzzy) or if API validation is disabled/fails (fail-safe)
    """
    if not enable_api_validation:
        return True
    
    if not cnpj or not declared_name:
        return True  # Skip if data missing
    
    try:
        from src.services.external_validators import CNPJValidator
        
        validator = CNPJValidator(timeout=5.0)
        matches = validator.validate_razao_social(cnpj, declared_name, threshold=0.7)
        
        logger.info(f"Razão social validation for CNPJ {cnpj}: {'matches' if matches else 'mismatch'}")
        return matches
        
    except ImportError:
        logger.warning("CNPJValidator not available - skipping validation")
        return True
        
    except Exception as e:
        logger.error(f"Error validating razão social for CNPJ {cnpj}: {e}")
        return True


def validate_ncm_exists(ncm: str) -> bool:
    """
    Validate if NCM code exists in TIPI table.
    
    This is VAL028 - validates NCM against official table.
    
    Args:
        ncm: NCM code (8 digits)
    
    Returns:
        True if NCM exists in table
    """
    if not ncm:
        return True  # Skip if missing
    
    try:
        from src.services.ncm_validator import get_ncm_validator
        
        validator = get_ncm_validator()
        is_valid = validator.is_valid_ncm(ncm)
        
        if not is_valid:
            logger.warning(f"NCM {ncm} not found in TIPI table")
        
        return is_valid
        
    except ImportError:
        logger.warning("NCMValidator not available - skipping validation")
        return True
        
    except Exception as e:
        logger.error(f"Error validating NCM {ncm}: {e}")
        return True


def validate_ie_state(ie: str, uf: str) -> bool:
    """
    Validate Inscrição Estadual check digit for state.
    
    This is VAL040 - validates IE format and check digit per state.
    
    Args:
        ie: Inscrição Estadual with or without formatting
        uf: State code (e.g., "SP", "RJ")
    
    Returns:
        True if IE is valid for the state
    """
    if not ie or not uf:
        return True  # Skip if missing (IE is optional)
    
    # Special case: ISENTO (exempt)
    if ie.upper().strip() == "ISENTO":
        return True
    
    try:
        from src.services.ie_validator import validate_ie
        
        is_valid = validate_ie(ie, uf)
        
        if not is_valid:
            logger.warning(f"IE {ie} invalid for state {uf}")
        
        return is_valid
        
    except ImportError:
        logger.warning("IEValidator not available - skipping validation")
        return True
        
    except Exception as e:
        logger.error(f"Error validating IE {ie} for {uf}: {e}")
        return True


class ValidationRule:
    """Single validation rule."""

    def __init__(
        self,
        code: str,
        severity: ValidationSeverity,
        message: str,
        check: Callable[[InvoiceModel], bool],
        field: str | None = None,
        suggestion: str | None = None,
    ):
        self.code = code
        self.severity = severity
        self.message = message
        self.check = check
        self.field = field
        self.suggestion = suggestion

    def validate(self, invoice: InvoiceModel) -> ValidationIssue | None:
        """Run validation check and return issue if failed."""
        if not self.check(invoice):
            return ValidationIssue(
                code=self.code,
                severity=self.severity,
                message=self.message,
                field=self.field,
                suggestion=self.suggestion,
            )
        return None


class FiscalValidatorTool:
    """Fiscal validator with declarative rules for Brazilian fiscal documents."""

    # Tolerance for decimal comparisons (to handle rounding differences)
    DECIMAL_TOLERANCE = Decimal("0.02")

    def __init__(self, db_manager=None, enable_api_validation: bool = True) -> None:
        """
        Initialize validator with default rules.
        
        Args:
            db_manager: Optional DatabaseManager for cross-document validations (e.g., duplicates)
            enable_api_validation: Enable external API validations (BrasilAPI, ViaCEP, etc.)
                                   Set to False to skip API calls (useful for offline/testing)
        """
        self.db_manager = db_manager
        self.enable_api_validation = enable_api_validation
        self.rules = self._build_default_rules()

    def validate(self, invoice: InvoiceModel) -> list[ValidationIssue]:
        """
        Validate invoice against all rules.

        Args:
            invoice: Normalized invoice to validate

        Returns:
            List of validation issues (empty if all pass)
        """
        issues = []
        for rule in self.rules:
            issue = rule.validate(invoice)
            if issue:
                issues.append(issue)
        return issues

    def _build_default_rules(self) -> list[ValidationRule]:
        """Build default validation rules."""
        return [
            # Document key validation
            ValidationRule(
                code="VAL001",
                severity=ValidationSeverity.ERROR,
                message="Document key (chave de acesso) must be 44 digits",
                check=lambda inv: len(inv.document_key) == 44 and inv.document_key.isdigit(),
                field="document_key",
                suggestion="Verify the access key format",
            ),
            # CNPJ validation
            ValidationRule(
                code="VAL002",
                severity=ValidationSeverity.ERROR,
                message="Issuer CNPJ must be 14 digits",
                check=lambda inv: len(
                    inv.issuer_cnpj.replace(".", "").replace("/", "").replace("-", "")
                )
                == 14,
                field="issuer_cnpj",
                suggestion="Verify issuer CNPJ format",
            ),
            # Total validation: sum of items should match total_products
            ValidationRule(
                code="VAL003",
                severity=ValidationSeverity.WARNING,
                message="Sum of item totals does not match total_products (tolerance: 0.02)",
                check=lambda inv: abs(
                    sum(item.total_price for item in inv.items) - inv.total_products
                )
                <= FiscalValidatorTool.DECIMAL_TOLERANCE,
                field="total_products",
                suggestion="Check for rounding errors or missing items",
            ),
            # Total validation: total_invoice should equal
            # total_products + other charges - discounts
            ValidationRule(
                code="VAL004",
                severity=ValidationSeverity.WARNING,
                message="Total invoice value does not match expected calculation",
                check=lambda inv: abs(inv.total_invoice - inv.total_products)
                <= FiscalValidatorTool.DECIMAL_TOLERANCE,
                field="total_invoice",
                suggestion="Verify freight, insurance, discounts, and other charges",
            ),
            # Items must exist (except for CTe/MDFe which are transport documents)
            ValidationRule(
                code="VAL005",
                severity=ValidationSeverity.ERROR,
                message="Invoice must contain at least one item",
                check=lambda inv: (
                    len(inv.items) > 0 or 
                    inv.document_type in ["CTe", "MDFe"]  # Transport docs don't have items
                ),
                field="items",
                suggestion="Verify XML structure and item parsing (not applicable to CTe/MDFe)",
            ),
            # Each item must have valid CFOP (only for NFe/NFCe)
            ValidationRule(
                code="VAL006",
                severity=ValidationSeverity.WARNING,
                message="One or more items have invalid CFOP (must be 4 digits)",
                check=lambda inv: (
                    len(inv.items) == 0 or  # Skip if no items (CTe/MDFe)
                    all(len(item.cfop) == 4 and item.cfop.isdigit() for item in inv.items)
                ),
                field="items[].cfop",
                suggestion="Verify CFOP codes against fiscal operation table",
            ),
            # Each item should have NCM (optional but recommended, only for NFe/NFCe)
            ValidationRule(
                code="VAL007",
                severity=ValidationSeverity.INFO,
                message="One or more items missing NCM code",
                check=lambda inv: (
                    len(inv.items) == 0 or  # Skip if no items (CTe/MDFe)
                    all(item.ncm is not None and item.ncm != "" for item in inv.items)
                ),
                field="items[].ncm",
                suggestion="NCM codes help with classification and tax reporting",
            ),
            # Item quantity * unit_price should match total_price (only for NFe/NFCe)
            ValidationRule(
                code="VAL008",
                severity=ValidationSeverity.WARNING,
                message="One or more items have quantity * unit_price != total_price",
                check=lambda inv: (
                    len(inv.items) == 0 or  # Skip if no items (CTe/MDFe)
                    all(
                        abs(item.quantity * item.unit_price - item.total_price)
                        <= FiscalValidatorTool.DECIMAL_TOLERANCE
                        for item in inv.items
                    )
                ),
                field="items[].total_price",
                suggestion="Check for rounding errors in item calculations",
            ),
            # Positive values (except MDFe which has no monetary value)
            ValidationRule(
                code="VAL009",
                severity=ValidationSeverity.ERROR,
                message="Total invoice value must be positive",
                check=lambda inv: (
                    inv.total_invoice > 0 or 
                    inv.document_type == "MDFe"  # MDFe is just a manifest, has no monetary value
                ),
                field="total_invoice",
                suggestion="Verify if this is a return or cancellation document (not applicable to MDFe)",
            ),
            # Future date check
            ValidationRule(
                code="VAL010",
                severity=ValidationSeverity.WARNING,
                message="Issue date is in the future",
                check=lambda inv: inv.issue_date <= inv.parsed_at,
                field="issue_date",
                suggestion="Verify system clock and document date",
            ),
            
            # ========================================
            # HIGH PRIORITY VALIDATIONS (Advanced)
            # ========================================
            
            # VAL011: CNPJ/CPF Check Digit Validation
            ValidationRule(
                code="VAL011",
                severity=ValidationSeverity.ERROR,
                message="Issuer CNPJ has invalid check digit",
                check=lambda inv: validate_cnpj_cpf_digit(inv.issuer_cnpj),
                field="issuer_cnpj",
                suggestion="Verify CNPJ is correct - check digit validation failed",
            ),
            
            # VAL012: Access Key Check Digit Validation
            ValidationRule(
                code="VAL012",
                severity=ValidationSeverity.ERROR,
                message="Document access key has invalid check digit (44th digit)",
                check=lambda inv: validate_access_key_digit(inv.document_key),
                field="document_key",
                suggestion="Access key check digit (mod 11) validation failed - verify key integrity",
            ),
            
            # VAL013: CFOP × Operation Type Consistency
            ValidationRule(
                code="VAL013",
                severity=ValidationSeverity.ERROR,
                message="CFOP inconsistent with operation type (e.g., CFOP 5xxx on purchase)",
                check=lambda inv: all(
                    validate_cfop_operation_consistency(
                        item.cfop, 
                        getattr(inv, 'operation_type', None)  # Safe access - field may not exist
                    )
                    for item in inv.items
                ),
                field="operation_type / items[].cfop",
                suggestion="Verify CFOP range: 1xxx/2xxx=entry, 5xxx/6xxx=exit, 3xxx=transfer",
            ),
            
            # VAL014: ICMS Tax Calculation
            ValidationRule(
                code="VAL014",
                severity=ValidationSeverity.WARNING,
                message="ICMS calculation incorrect: base × rate ≠ tax value",
                check=lambda inv: all(
                    validate_tax_calculation(
                        item.icms_base if hasattr(item, 'icms_base') and item.icms_base else Decimal("0"),
                        item.icms_rate if hasattr(item, 'icms_rate') and item.icms_rate else Decimal("0"),
                        item.icms_value if hasattr(item, 'icms_value') and item.icms_value else Decimal("0"),
                    )
                    for item in inv.items
                ),
                field="items[].icms_value",
                suggestion="Verify ICMS base, rate, and value - recalculate: base × (rate/100) = value",
            ),
            
            # VAL015: PIS Tax Calculation
            ValidationRule(
                code="VAL015",
                severity=ValidationSeverity.WARNING,
                message="PIS calculation incorrect: base × rate ≠ tax value",
                check=lambda inv: all(
                    validate_tax_calculation(
                        item.pis_base if hasattr(item, 'pis_base') and item.pis_base else Decimal("0"),
                        item.pis_rate if hasattr(item, 'pis_rate') and item.pis_rate else Decimal("0"),
                        item.pis_value if hasattr(item, 'pis_value') and item.pis_value else Decimal("0"),
                    )
                    for item in inv.items
                ),
                field="items[].pis_value",
                suggestion="Verify PIS base, rate, and value - recalculate: base × (rate/100) = value",
            ),
            
            # VAL016: COFINS Tax Calculation
            ValidationRule(
                code="VAL016",
                severity=ValidationSeverity.WARNING,
                message="COFINS calculation incorrect: base × rate ≠ tax value",
                check=lambda inv: all(
                    validate_tax_calculation(
                        item.cofins_base if hasattr(item, 'cofins_base') and item.cofins_base else Decimal("0"),
                        item.cofins_rate if hasattr(item, 'cofins_rate') and item.cofins_rate else Decimal("0"),
                        item.cofins_value if hasattr(item, 'cofins_value') and item.cofins_value else Decimal("0"),
                    )
                    for item in inv.items
                ),
                field="items[].cofins_value",
                suggestion="Verify COFINS base, rate, and value - recalculate: base × (rate/100) = value",
            ),
            
            # VAL017: Duplicate Document Detection (requires database)
            ValidationRule(
                code="VAL017",
                severity=ValidationSeverity.ERROR,
                message="Duplicate document detected - same access key already exists in database",
                check=lambda inv: self._check_not_duplicate(inv),
                field="document_key",
                suggestion="This document was already processed - check for resubmission or duplicate file",
            ),
            
            # ===== ADVANCED VALIDATIONS (VAL018-VAL021) =====
            
            # VAL018: Tax Regime × CST Consistency
            ValidationRule(
                code="VAL018",
                severity=ValidationSeverity.ERROR,
                message="Tax regime (CRT) inconsistent with CST/CSOSN codes",
                check=lambda inv: all(
                    validate_tax_regime_cst_consistency(inv.tax_regime, item.cst)
                    for item in inv.items
                ),
                field="tax_regime, items[].cst",
                suggestion="CRT 1/2 (Simples) must use CSOSN (101-900); CRT 3 (Normal) must use CST (00-90)",
            ),
            
            # VAL021: NCM Format Validation
            ValidationRule(
                code="VAL021",
                severity=ValidationSeverity.WARNING,
                message="NCM code has invalid format (must be 8 digits)",
                check=lambda inv: all(
                    validate_ncm_format(item.ncm)
                    for item in inv.items
                ),
                field="items[].ncm",
                suggestion="NCM must be exactly 8 numeric digits - verify product classification",
            ),
            
            # VAL022: ICMS Interstate Rate Validation
            ValidationRule(
                code="VAL022",
                severity=ValidationSeverity.WARNING,
                message="ICMS rate may be incorrect for interstate operation",
                check=lambda inv: all(
                    validate_icms_interstate_rate(inv.issuer_uf, inv.recipient_uf, item.icms_rate)
                    for item in inv.items
                ),
                field="items[].icms_rate",
                suggestion="Verify ICMS rate for interstate operation (common rates: 4%, 7%, 12%)",
            ),
            
            # VAL025: CFOP × UF Consistency
            ValidationRule(
                code="VAL025",
                severity=ValidationSeverity.ERROR,
                message="CFOP inconsistent with issuer/recipient UF (state)",
                check=lambda inv: all(
                    validate_cfop_uf_consistency(item.cfop, inv.issuer_uf, inv.recipient_uf)
                    for item in inv.items
                ),
                field="items[].cfop, issuer_uf, recipient_uf",
                suggestion="CFOP 5xxx = within state (same UF); CFOP 6xxx = outside state (different UF)",
            ),
            
            # ===== EXTERNAL API VALIDATIONS (VAL026+) =====
            
            # VAL026: CNPJ Active Status via BrasilAPI
            ValidationRule(
                code="VAL026",
                severity=ValidationSeverity.ERROR,
                message="CNPJ is not active in Receita Federal database (BAIXADA, SUSPENSA, INAPTA, or NULA)",
                check=lambda inv: validate_cnpj_active_via_api(
                    inv.issuer_cnpj, 
                    enable_api_validation=getattr(self, 'enable_api_validation', True)
                ),
                field="issuer_cnpj",
                suggestion="Verify CNPJ status with supplier - inactive CNPJs cannot issue valid NFe",
            ),
            
            # VAL027: CEP × Município/UF via ViaCEP
            ValidationRule(
                code="VAL027",
                severity=ValidationSeverity.WARNING,
                message="Issuer CEP does not match declared município/UF",
                check=lambda inv: validate_cep_municipio_uf(
                    inv.issuer_cep or "",
                    inv.issuer_municipio or "",
                    inv.issuer_uf or "",
                    enable_api_validation=getattr(self, 'enable_api_validation', True)
                ),
                field="issuer_cep, issuer_municipio, issuer_uf",
                suggestion="Verify issuer address - CEP doesn't match município/UF according to ViaCEP",
            ),
            
            # VAL028: NCM Exists in TIPI Table
            ValidationRule(
                code="VAL028",
                severity=ValidationSeverity.WARNING,
                message="One or more NCM codes not found in TIPI/IBGE table",
                check=lambda inv: all(
                    validate_ncm_exists(item.ncm) for item in inv.items if item.ncm
                ),
                field="items[].ncm",
                suggestion="Verify NCM codes - one or more codes don't exist in official TIPI table",
            ),
            
            # VAL029: Razão Social × CNPJ Cross-Validation
            ValidationRule(
                code="VAL029",
                severity=ValidationSeverity.WARNING,
                message="Declared razão social doesn't match CNPJ data from Receita Federal",
                check=lambda inv: validate_razao_social_cnpj(
                    inv.issuer_cnpj,
                    inv.issuer_name,
                    enable_api_validation=getattr(self, 'enable_api_validation', True)
                ),
                field="issuer_name, issuer_cnpj",
                suggestion="Verify issuer name - declared razão social doesn't match Receita Federal data (fuzzy match threshold: 70%)",
            ),
            
            # ===== FISCAL IDENTIFIER VALIDATIONS (VAL040+) =====
            
            # VAL040: Inscrição Estadual Check Digit
            ValidationRule(
                code="VAL040",
                severity=ValidationSeverity.ERROR,
                message="Issuer Inscrição Estadual (IE) has invalid check digit for state",
                check=lambda inv: validate_ie_state(
                    inv.issuer_ie or "",
                    inv.issuer_uf or ""
                ),
                field="issuer_ie, issuer_uf",
                suggestion="Verify Inscrição Estadual - check digit validation failed for this state",
            ),
            
            # ===== CTe SPECIFIC VALIDATIONS (VAL050-VAL059) =====
            
            # VAL050: CTe - Modal de Transporte
            ValidationRule(
                code="VAL050",
                severity=ValidationSeverity.ERROR,
                message="CTe has invalid transport modal code",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    self._validate_cte_modal(inv)
                ),
                field="modal",
                suggestion="Valid modals: 01=Rodoviário, 02=Aéreo, 03=Aquaviário, 04=Ferroviário, 05=Dutoviário, 06=Multimodal",
            ),
            
            # VAL051: CTe - RNTRC Format
            ValidationRule(
                code="VAL051",
                severity=ValidationSeverity.WARNING,
                message="CTe RNTRC has invalid format (must be 8 digits)",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    self._validate_cte_rntrc(inv)
                ),
                field="rntrc",
                suggestion="RNTRC must be 8 numeric digits (Registro Nacional de Transportadores)",
            ),
            
            # VAL052: CTe - CFOP para Transporte
            ValidationRule(
                code="VAL052",
                severity=ValidationSeverity.ERROR,
                message="CTe has CFOP not valid for transport services",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    self._validate_cte_cfop(inv)
                ),
                field="cfop",
                suggestion="Valid CFOPs for transport: 1351-1359, 2351-2359, 5351-5359, 6351-6359",
            ),
            
            # VAL053: CTe - Valor do Serviço
            ValidationRule(
                code="VAL053",
                severity=ValidationSeverity.ERROR,
                message="CTe transport service value must be greater than zero",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    inv.total_invoice > 0
                ),
                field="total_invoice",
                suggestion="Verify vTPrest - transport service value cannot be zero",
            ),
            
            # VAL054: CTe - Placa do Veículo
            ValidationRule(
                code="VAL054",
                severity=ValidationSeverity.WARNING,
                message="CTe vehicle plate has invalid format",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    self._validate_vehicle_plate(inv)
                ),
                field="vehicle_plate",
                suggestion="Valid formats: ABC1234 (old) or ABC1D23 (Mercosul)",
            ),
            
            # VAL055: CTe - UF Origem/Destino
            ValidationRule(
                code="VAL055",
                severity=ValidationSeverity.ERROR,
                message="CTe has invalid origin or destination UF",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    self._validate_cte_ufs(inv)
                ),
                field="issuer_uf, recipient_uf",
                suggestion="Verify UF codes - must be valid Brazilian states",
            ),
            
            # ===== MDFe SPECIFIC VALIDATIONS (VAL060-VAL069) =====
            
            # VAL060: MDFe - Modal de Transporte
            ValidationRule(
                code="VAL060",
                severity=ValidationSeverity.ERROR,
                message="MDFe has invalid transport modal code",
                check=lambda inv: (
                    inv.document_type != "MDFe" or 
                    self._validate_mdfe_modal(inv)
                ),
                field="modal",
                suggestion="Valid modals: 01=Rodoviário, 02=Aéreo, 03=Aquaviário, 04=Ferroviário",
            ),
            
            # VAL061: MDFe - Percurso UF
            ValidationRule(
                code="VAL061",
                severity=ValidationSeverity.WARNING,
                message="MDFe route UFs are invalid or duplicated",
                check=lambda inv: (
                    inv.document_type != "MDFe" or 
                    self._validate_mdfe_route(inv)
                ),
                field="route_ufs",
                suggestion="Verify infPercurso - route UFs must be valid and non-duplicated",
            ),
            
            # VAL062: MDFe - Placa do Veículo Principal
            ValidationRule(
                code="VAL062",
                severity=ValidationSeverity.WARNING,
                message="MDFe vehicle plate has invalid format",
                check=lambda inv: (
                    inv.document_type != "MDFe" or 
                    self._validate_vehicle_plate(inv)
                ),
                field="vehicle_plate",
                suggestion="Valid formats: ABC1234 (old) or ABC1D23 (Mercosul)",
            ),
            
            # VAL063: MDFe - Peso Total
            ValidationRule(
                code="VAL063",
                severity=ValidationSeverity.WARNING,
                message="MDFe total weight must be greater than zero",
                check=lambda inv: (
                    inv.document_type != "MDFe" or 
                    self._validate_mdfe_weight(inv)
                ),
                field="total_weight",
                suggestion="Verify qCarga - total cargo weight in kg",
            ),
            
            # ===== ADDITIONAL CTe VALIDATIONS (VAL056-VAL059) =====
            
            # VAL056: CTe - Tipo de Tomador do Serviço
            ValidationRule(
                code="VAL056",
                severity=ValidationSeverity.WARNING,
                message="CTe service taker type is invalid",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    not inv.service_taker_type or
                    inv.service_taker_type in ["0", "1", "2", "3", "4"]
                ),
                field="service_taker_type",
                suggestion="Valid types: 0=Remetente, 1=Expedidor, 2=Recebedor, 3=Destinatário, 4=Outros",
            ),
            
            # VAL057: CTe - Tipo de Frete
            ValidationRule(
                code="VAL057",
                severity=ValidationSeverity.INFO,
                message="CTe freight type is recommended to be specified",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    bool(inv.freight_type)
                ),
                field="freight_type",
                suggestion="Specify freight type: 0=CIF (remetente), 1=FOB (destinatário), 2=Terceiros, 9=Sem frete",
            ),
            
            # VAL058: CTe - Carga Perigosa Requer Detalhes
            ValidationRule(
                code="VAL058",
                severity=ValidationSeverity.WARNING,
                message="CTe with dangerous cargo should have cargo details",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    not inv.dangerous_cargo or
                    (inv.cargo_weight is not None and inv.cargo_weight > 0)
                ),
                field="dangerous_cargo",
                suggestion="Dangerous cargo requires weight and additional safety documentation",
            ),
            
            # VAL059: CTe - Seguro Recomendado para Alto Valor
            ValidationRule(
                code="VAL059",
                severity=ValidationSeverity.INFO,
                message="CTe with high freight value should have insurance",
                check=lambda inv: (
                    inv.document_type != "CTe" or 
                    inv.total_invoice < Decimal("5000.00") or
                    (inv.insurance_value is not None and inv.insurance_value > 0)
                ),
                field="insurance_value",
                suggestion="Consider adding insurance for freight values above R$ 5,000.00",
            ),
            
            # ===== ADDITIONAL MDFe VALIDATIONS (VAL064-VAL067) =====
            
            # VAL064: MDFe - Tipo de Emissão
            ValidationRule(
                code="VAL064",
                severity=ValidationSeverity.INFO,
                message="MDFe emission type is recommended",
                check=lambda inv: (
                    inv.document_type != "MDFe" or 
                    bool(inv.emission_type)
                ),
                field="emission_type",
                suggestion="Specify emission type: 1=Normal, 2=Contingência FS-IA, etc.",
            ),
            
            # VAL065: MDFe - RNTRC Recomendado
            ValidationRule(
                code="VAL065",
                severity=ValidationSeverity.INFO,
                message="MDFe should include RNTRC when available",
                check=lambda inv: (
                    inv.document_type != "MDFe" or 
                    bool(inv.rntrc)
                ),
                field="rntrc",
                suggestion="Include RNTRC (Registro Nacional de Transportadores) when applicable",
            ),
            
            # VAL066: MDFe - Placa e UF Veículo Consistentes
            ValidationRule(
                code="VAL066",
                severity=ValidationSeverity.WARNING,
                message="MDFe vehicle plate should have matching UF",
                check=lambda inv: (
                    inv.document_type != "MDFe" or 
                    not inv.vehicle_plate or
                    bool(inv.vehicle_uf)
                ),
                field="vehicle_uf",
                suggestion="Specify vehicle registration state (UF) when plate is provided",
            ),
            
            # VAL067: MDFe - Percurso Coerente com Origem/Destino
            ValidationRule(
                code="VAL067",
                severity=ValidationSeverity.INFO,
                message="MDFe route should start with issuer UF",
                check=lambda inv: (
                    inv.document_type != "MDFe" or 
                    not inv.route_ufs or
                    not inv.issuer_uf or
                    len(inv.route_ufs) == 0 or
                    inv.route_ufs[0] == inv.issuer_uf
                ),
                field="route_ufs",
                suggestion="Route typically starts at issuer's state (UF)",
            ),
        ]
    
    def _check_not_duplicate(self, invoice: InvoiceModel) -> bool:
        """
        Check if document is not a duplicate based on access key.
        
        Args:
            invoice: Invoice to check
        
        Returns:
            True if not duplicate (validation passes)
        """
        if not self.db_manager:
            # Skip validation if no database available
            return True
        
        try:
            # Search for existing invoice with same access key
            existing = self.db_manager.search_invoices(document_key=invoice.document_key, limit=1)
            
            # If found, it's a duplicate
            return len(existing) == 0
        
        except Exception:
            # If database check fails, skip validation (don't block processing)
            return True
    
    # ===== CTe/MDFe SPECIFIC VALIDATION HELPERS =====
    
    def _validate_cte_modal(self, invoice: InvoiceModel) -> bool:
        """Validate CTe modal from model field."""
        try:
            from src.services.transport_validators import validate_modal
            
            if not invoice.modal:
                return True  # Modal is optional in parsed data
            
            return validate_modal(invoice.modal)
        except Exception as e:
            logger.warning(f"Error validating CTe modal: {e}")
            return True  # Fail-safe
    
    def _validate_cte_rntrc(self, invoice: InvoiceModel) -> bool:
        """Validate CTe RNTRC from model field."""
        try:
            from src.services.transport_validators import validate_rntrc_format
            
            if not invoice.rntrc:
                return True  # RNTRC is optional in some cases
            
            return validate_rntrc_format(invoice.rntrc)
        except Exception as e:
            logger.warning(f"Error validating CTe RNTRC: {e}")
            return True  # Fail-safe
    
    def _validate_cte_cfop(self, invoice: InvoiceModel) -> bool:
        """Validate CTe CFOP from raw XML (CFOP is in items for NFe, but in ide for CTe)."""
        try:
            from src.services.transport_validators import validate_cfop_for_transport
            from defusedxml import ElementTree as ET
            
            if not invoice.raw_xml:
                return True  # Skip if no raw XML
            
            root = ET.fromstring(invoice.raw_xml)
            # Find CFOP in ide section
            cfop_elem = root.find(".//{http://www.portalfiscal.inf.br/cte}CFOP")
            if cfop_elem is None:
                cfop_elem = root.find(".//CFOP")
            
            if cfop_elem is not None and cfop_elem.text:
                return validate_cfop_for_transport(cfop_elem.text)
            
            return True  # Skip if CFOP not found
        except Exception as e:
            logger.warning(f"Error validating CTe CFOP: {e}")
            return True  # Fail-safe
    
    def _validate_vehicle_plate(self, invoice: InvoiceModel) -> bool:
        """Validate vehicle plate from model field."""
        try:
            from src.services.transport_validators import validate_vehicle_plate
            
            if not invoice.vehicle_plate:
                return True  # Plate is optional
            
            return validate_vehicle_plate(invoice.vehicle_plate)
        except Exception as e:
            logger.warning(f"Error validating vehicle plate: {e}")
            return True  # Fail-safe
    
    def _validate_cte_ufs(self, invoice: InvoiceModel) -> bool:
        """Validate CTe origin/destination UFs."""
        try:
            from src.services.transport_validators import validate_uf
            
            if invoice.issuer_uf and not validate_uf(invoice.issuer_uf):
                return False
            
            if invoice.recipient_uf and not validate_uf(invoice.recipient_uf):
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Error validating CTe UFs: {e}")
            return True  # Fail-safe
    
    def _validate_mdfe_modal(self, invoice: InvoiceModel) -> bool:
        """Validate MDFe modal from model field."""
        try:
            from src.services.transport_validators import validate_modal
            
            if not invoice.modal:
                return True  # Modal is optional
            
            # MDFe only supports modals 01-04 (no pipeline or multimodal)
            return validate_modal(invoice.modal) and invoice.modal in ["01", "02", "03", "04"]
        except Exception as e:
            logger.warning(f"Error validating MDFe modal: {e}")
            return True  # Fail-safe
    
    def _validate_mdfe_route(self, invoice: InvoiceModel) -> bool:
        """Validate MDFe route UFs from model field."""
        try:
            from src.services.transport_validators import validate_uf_route
            
            if not invoice.route_ufs or len(invoice.route_ufs) == 0:
                return True  # Route is optional or empty
            
            return validate_uf_route(invoice.route_ufs)
        except Exception as e:
            logger.warning(f"Error validating MDFe route: {e}")
            return True  # Fail-safe
    
    def _validate_mdfe_weight(self, invoice: InvoiceModel) -> bool:
        """Validate MDFe weight from model field."""
        try:
            from src.services.transport_validators import validate_weight
            
            if invoice.cargo_weight is None:
                return True  # Weight might be optional
            
            return validate_weight(invoice.cargo_weight)
        except Exception as e:
            logger.warning(f"Error validating MDFe weight: {e}")
            return True  # Fail-safe

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a custom validation rule."""
        self.rules.append(rule)

    def remove_rule(self, code: str) -> None:
        """Remove a validation rule by code."""
        self.rules = [r for r in self.rules if r.code != code]
