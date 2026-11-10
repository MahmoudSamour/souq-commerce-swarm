"""
SOUQ // Chief Compliance & Legal Gatekeeper (Amin Auditor)
Enforces CFAA, DMCA §1201, Copyright Fact Doctrine, GDPR Zero-PII,
and pre-flight cryptographic clearance before any product or tool goes live.
"""

import hashlib
import json
from typing import Dict, Any, List, Tuple


class AminAuditor:
    """
    The non-negotiable compliance gatekeeper.
    Every product or dataset requires an Amin cryptographic clearance signature.
    """

    def audit_product_concept(self, product_metadata: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        checks = {}

        # 1. CFAA Safe Harbor Check
        is_public_data = product_metadata.get("uses_public_data_only", True)
        requires_login_bypass = product_metadata.get("bypasses_login", False)
        checks["cfaa_safe_harbor"] = is_public_data and not requires_login_bypass

        # 2. DMCA §1201 Non-Circumvention Check
        bypasses_captcha = product_metadata.get("bypasses_captcha", False)
        bypasses_tpm = product_metadata.get("bypasses_bot_protection", False)
        checks["dmca_non_circumvention"] = not (bypasses_captcha or bypasses_tpm)

        # 3. GDPR / CCPA Zero-PII Guarantee
        contains_pii = product_metadata.get("contains_pii", False)
        checks["zero_pii_compliance"] = not contains_pii

        # 4. Copyright Fact Doctrine (Feist Doctrine)
        is_raw_math_or_clean_code = product_metadata.get("is_factual_or_original", True)
        checks["copyright_cleared"] = is_raw_math_or_clean_code

        # 5. Financial Regulatory Safe Harbor (Pure Descriptive Analytics)
        provides_trade_signals = product_metadata.get("claims_guaranteed_profit", False)
        checks["sec_safe_harbor"] = not provides_trade_signals

        all_passed = all(checks.values())

        clearance_token = None
        if all_passed:
            material = f"AMIN_APPROVED:{json.dumps(product_metadata, sort_keys=True)}"
            clearance_token = hashlib.sha256(material.encode("utf-8")).hexdigest()

        return all_passed, {
            "status": "APPROVED" if all_passed else "REJECTED_COMPLIANCE_FAILURE",
            "checks": checks,
            "clearance_token": clearance_token,
            "auditor": "Amin Chief Compliance Sentinel (SOUQ-DIV-5)"
        }
