"""Consolidated validators module - re-exports all validators from specialized files.

This module provides a single import point for all validation functions.
Specialized validators are kept in separate files for maintainability.
"""

# Import all IE validators
from src.services.ie_validator import (
    validate_ie,
    validate_ie_ac,
    validate_ie_al,
    validate_ie_ap,
    validate_ie_am,
    validate_ie_ba,
    validate_ie_ce,
    validate_ie_df,
    validate_ie_es,
    validate_ie_go,
    validate_ie_ma,
    validate_ie_mt,
    validate_ie_ms,
    validate_ie_mg,
    validate_ie_pa,
    validate_ie_pb,
    validate_ie_pr,
    validate_ie_pe,
    validate_ie_pi,
    validate_ie_rj,
    validate_ie_rn,
    validate_ie_rs,
    validate_ie_ro,
    validate_ie_rr,
    validate_ie_sc,
    validate_ie_sp,
    validate_ie_se,
    validate_ie_to,
)

# Import all NCM validators
from src.services.ncm_validator import (
    validate_ncm,
    get_ncm_info,
    lookup_ncm_description,
)

# Import all transport validators
from src.services.transport_validators import (
    validate_cte_fields,
    validate_mdfe_fields,
    validate_modal,
    validate_transport_document,
)

# Import all external validators
from src.services.external_validators import (
    validate_cnpj_format,
    validate_cpf_format,
    lookup_cnpj_data,
)

__all__ = [
    # IE validators
    "validate_ie",
    "validate_ie_ac",
    "validate_ie_al",
    "validate_ie_ap",
    "validate_ie_am",
    "validate_ie_ba",
    "validate_ie_ce",
    "validate_ie_df",
    "validate_ie_es",
    "validate_ie_go",
    "validate_ie_ma",
    "validate_ie_mt",
    "validate_ie_ms",
    "validate_ie_mg",
    "validate_ie_pa",
    "validate_ie_pb",
    "validate_ie_pr",
    "validate_ie_pe",
    "validate_ie_pi",
    "validate_ie_rj",
    "validate_ie_rn",
    "validate_ie_rs",
    "validate_ie_ro",
    "validate_ie_rr",
    "validate_ie_sc",
    "validate_ie_sp",
    "validate_ie_se",
    "validate_ie_to",
    # NCM validators
    "validate_ncm",
    "get_ncm_info",
    "lookup_ncm_description",
    # Transport validators
    "validate_cte_fields",
    "validate_mdfe_fields",
    "validate_modal",
    "validate_transport_document",
    # External validators
    "validate_cnpj_format",
    "validate_cpf_format",
    "lookup_cnpj_data",
]
