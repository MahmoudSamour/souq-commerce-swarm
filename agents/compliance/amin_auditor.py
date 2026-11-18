"""
SOUQ // Chief Compliance & Legal Gatekeeper (Amin Auditor)
Enforces CFAA, DMCA §1201, Copyright Fact Doctrine, GDPR Zero-PII,
and pre-flight cryptographic clearance before any product or tool goes live.
"""

import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional, Tuple


class AminAuditor:
    """
    The non-negotiable compliance gatekeeper.
    Every product or dataset requires an Amin cryptographic clearance signature.
    """

    @staticmethod
    def _get_signing_key() -> str:
        return (
            os.getenv("SOUQ_RECEIPT_SIGNING_KEY")
            or os.getenv("SOUQ_API_KEY_PEPPER")
            or "souq_sovereign_pepper_2026"
        )

    @staticmethod
    def _strict_bool(
        product_metadata: Dict[str, Any],
        key: str,
        default: Optional[bool] = None,
    ) -> Optional[bool]:
        """Returns strict bool value when present, default when absent, or None if non-bool."""
        if key not in product_metadata:
            return default
        value = product_metadata[key]
        return value if isinstance(value, bool) else None

    def _sign_clearance(self, product_metadata: Dict[str, Any]) -> str:
        """Signs canonical product metadata using keyed HMAC-SHA256."""
        material = f"AMIN_APPROVED:{json.dumps(product_metadata, sort_keys=True, default=str)}"
        return hmac.new(
            self._get_signing_key().encode("utf-8"),
            material.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_clearance_token(self, product_metadata: Dict[str, Any], token: str) -> bool:
        """Constant-time verification of an Amin clearance HMAC-SHA256 token."""
        if (
            not isinstance(product_metadata, dict)
            or not isinstance(product_metadata.get("concept_id"), str)
            or not product_metadata.get("concept_id", "").strip()
            or not isinstance(token, str)
            or not token
        ):
            return False
        expected = self._sign_clearance(product_metadata)
        return hmac.compare_digest(expected, token)

    def audit_product_concept(self, product_metadata: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        if (
            not isinstance(product_metadata, dict)
            or not isinstance(product_metadata.get("concept_id"), str)
            or not product_metadata.get("concept_id", "").strip()
        ):
            return False, {
                "status": "REJECTED_COMPLIANCE_FAILURE",
                "checks": {"valid_metadata": False},
                "clearance_token": None,
                "auditor": "Amin Chief Compliance Sentinel (SOUQ-DIV-5)",
            }

        checks: Dict[str, bool] = {"valid_metadata": True}

        # 1. CFAA Safe Harbor Check (requires explicit boolean True for public data)
        is_public_data = self._strict_bool(product_metadata, "uses_public_data_only", default=False) is True
        no_login_bypass = self._strict_bool(product_metadata, "bypasses_login", default=False) is False
        checks["cfaa_safe_harbor"] = is_public_data and no_login_bypass

        # 2. DMCA §1201 Non-Circumvention Check
        no_captcha_bypass = self._strict_bool(product_metadata, "bypasses_captcha", default=False) is False
        no_tpm_bypass = self._strict_bool(product_metadata, "bypasses_bot_protection", default=False) is False
        checks["dmca_non_circumvention"] = no_captcha_bypass and no_tpm_bypass

        # 3. GDPR / CCPA Zero-PII Guarantee
        checks["zero_pii_compliance"] = self._strict_bool(product_metadata, "contains_pii", default=False) is False

        # 4. Copyright Fact Doctrine (Feist Doctrine)
        checks["copyright_cleared"] = (
            self._strict_bool(product_metadata, "is_factual_or_original", default=False) is True
        )

        # 5. Financial Regulatory Safe Harbor (Pure Descriptive Analytics)
        checks["sec_safe_harbor"] = (
            self._strict_bool(product_metadata, "claims_guaranteed_profit", default=False) is False
        )

        # 6. AML / Sanctions & Restricted Source Quarantine (Binance Terms of Use Compliance)
        not_restricted = self._strict_bool(product_metadata, "is_restricted_source", default=False) is False
        not_unverified_p2p = (
            self._strict_bool(product_metadata, "unverified_third_party_funding", default=False) is False
        )
        checks["aml_sanctions_clearance"] = not_restricted and not_unverified_p2p

        all_passed = all(checks.values())

        clearance_token = self._sign_clearance(product_metadata) if all_passed else None

        return all_passed, {
            "status": "APPROVED" if all_passed else "REJECTED_COMPLIANCE_FAILURE",
            "checks": checks,
            "clearance_token": clearance_token,
            "auditor": "Amin Chief Compliance Sentinel (SOUQ-DIV-5)"
        }

