"""
SOUQ // Chief Compliance & Legal Gatekeeper (Amin Auditor)
Enforces CFAA, DMCA §1201, Copyright Fact Doctrine, GDPR Zero-PII,
and pre-flight cryptographic clearance before any product or tool goes live.
"""

import ast
import hashlib
import hmac
import json
import os
import re
import secrets
from typing import Any, Dict, List, Optional, Tuple

from agents.treasury.db_backend import load_souq_env

load_souq_env()
_EPHEMERAL_SIGNING_PEPPER = secrets.token_hex(32)

FORBIDDEN_ENDPOINT_PATTERNS = (
    "api.binance.com",
    "fapi.binance.com",
    "dapi.binance.com",
    "testnet.binance.vision",
    "binance_api_key",
    "binance_api_secret",
)

UNSAFE_CALL_NAMES = frozenset({"eval", "exec", "__import__", "compile"})

PII_COLLECTION_PATTERNS = (
    re.compile(r"\b(collect_pii|harvest_emails|scrape_ssn|store_raw_ip)\b", re.IGNORECASE),
    re.compile(r"\b(social_security_number|passport_number|credit_card_number|drivers_license_number)\b", re.IGNORECASE),
)


class AminAuditor:
    """
    The non-negotiable compliance gatekeeper.
    Every product or dataset requires an Amin cryptographic clearance signature.
    """

    @staticmethod
    def _get_signing_key() -> str:
        return (
            os.getenv("SOUQ_HASH_PEPPER")
            or os.getenv("SOUQ_RECEIPT_SIGNING_KEY")
            or os.getenv("SOUQ_API_KEY_PEPPER")
            or _EPHEMERAL_SIGNING_PEPPER
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

        # 6. AML / Sanctions & Restricted Source Quarantine
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

    def audit_source_code(
        self,
        source_code: str,
        source_name: str = "<string>",
        concept_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Automated static AST & URL policy verifier for Python tool modules.
        Inspects actual code for:
        1. Forbidden Binance / restricted endpoints & credentials (api.binance.com, fapi.binance.com, BINANCE_API_KEY)
        2. Unsafe dynamic code execution (eval, exec, __import__, compile, os.system, subprocess shell=True)
        3. Prohibited PII collection identifiers/schemas
        """
        violations: List[Dict[str, Any]] = []
        if not isinstance(source_code, str) or not source_code.strip():
            return False, {
                "status": "REJECTED_STATIC_POLICY_VIOLATION",
                "source_path": source_name,
                "checks": {"parseable_ast": False},
                "violations": [{"rule": "empty_source", "detail": "Source code is empty"}],
                "clearance_token": None,
                "auditor": "Amin Chief Compliance Sentinel (SOUQ-DIV-5)",
            }

        try:
            tree = ast.parse(source_code, filename=source_name)
        except SyntaxError as exc:
            return False, {
                "status": "REJECTED_STATIC_POLICY_VIOLATION",
                "source_path": source_name,
                "checks": {"parseable_ast": False},
                "violations": [{"rule": "syntax_error", "line": exc.lineno, "detail": str(exc)}],
                "clearance_token": None,
                "auditor": "Amin Chief Compliance Sentinel (SOUQ-DIV-5)",
            }

        # 1. Inspect AST string constants & source lines for forbidden endpoints/keys
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val_lower = node.value.lower()
                for forbidden in FORBIDDEN_ENDPOINT_PATTERNS:
                    if forbidden in val_lower:
                        violations.append({
                            "rule": "forbidden_endpoint_or_key",
                            "pattern": forbidden,
                            "line": getattr(node, "lineno", None),
                            "detail": f"Forbidden reference '{forbidden}' detected in string literal.",
                        })
                for pii_re in PII_COLLECTION_PATTERNS:
                    m = pii_re.search(node.value)
                    if m:
                        violations.append({
                            "rule": "prohibited_pii_collection",
                            "pattern": m.group(0),
                            "line": getattr(node, "lineno", None),
                            "detail": f"Prohibited PII collection indicator '{m.group(0)}' detected.",
                        })

            # 2. Inspect AST function calls for unsafe eval/exec/shell execution
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in UNSAFE_CALL_NAMES:
                    violations.append({
                        "rule": "unsafe_dynamic_execution",
                        "call": func.id,
                        "line": getattr(node, "lineno", None),
                        "detail": f"Unsafe builtin call '{func.id}()' is prohibited.",
                    })
                elif isinstance(func, ast.Attribute):
                    if (
                        isinstance(func.value, ast.Name)
                        and func.value.id == "os"
                        and func.attr in ("system", "popen")
                    ):
                        violations.append({
                            "rule": "unsafe_shell_execution",
                            "call": f"os.{func.attr}",
                            "line": getattr(node, "lineno", None),
                            "detail": f"Unsafe shell call 'os.{func.attr}()' is prohibited.",
                        })
                    elif (
                        isinstance(func.value, ast.Name)
                        and func.value.id == "subprocess"
                        and func.attr in ("run", "Popen", "call", "check_call", "check_output")
                    ):
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                violations.append({
                                    "rule": "unsafe_shell_execution",
                                    "call": f"subprocess.{func.attr}(shell=True)",
                                    "line": getattr(node, "lineno", None),
                                    "detail": "subprocess call with shell=True is prohibited.",
                                })

            # 3. Inspect function/variable names for explicit PII collection helpers
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for pii_re in PII_COLLECTION_PATTERNS:
                    m = pii_re.search(node.name)
                    if m:
                        violations.append({
                            "rule": "prohibited_pii_collection",
                            "pattern": m.group(0),
                            "line": getattr(node, "lineno", None),
                            "detail": f"Prohibited PII collection function '{node.name}' detected.",
                        })

        has_forbidden_endpoint = any(v["rule"] == "forbidden_endpoint_or_key" for v in violations)
        has_unsafe_exec = any(v["rule"] in ("unsafe_dynamic_execution", "unsafe_shell_execution") for v in violations)
        has_pii = any(v["rule"] == "prohibited_pii_collection" for v in violations)

        checks = {
            "parseable_ast": True,
            "no_forbidden_endpoints": not has_forbidden_endpoint,
            "no_unsafe_exec": not has_unsafe_exec,
            "zero_pii_collection": not has_pii,
        }
        all_passed = all(checks.values())
        source_sha256 = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
        token_payload = {
            "concept_id": concept_id or os.path.basename(source_name),
            "source_path": source_name,
            "source_sha256": source_sha256,
            "checks": checks,
        }
        clearance_token = self._sign_clearance(token_payload) if all_passed else None

        return all_passed, {
            "status": "APPROVED" if all_passed else "REJECTED_STATIC_POLICY_VIOLATION",
            "source_path": source_name,
            "source_sha256": source_sha256,
            "checks": checks,
            "violations": violations,
            "clearance_token": clearance_token,
            "auditor": "Amin Chief Compliance Sentinel (SOUQ-DIV-5)",
        }

    def audit_tool_source(
        self,
        source_path: str,
        concept_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Reads a Python tool module from disk and runs automated static AST/URL policy verification."""
        if not source_path or not isinstance(source_path, str) or not os.path.isfile(source_path):
            return False, {
                "status": "REJECTED_STATIC_POLICY_VIOLATION",
                "source_path": source_path,
                "checks": {"source_exists": False},
                "violations": [{"rule": "missing_source_file", "detail": f"Source file not found: {source_path}"}],
                "clearance_token": None,
                "auditor": "Amin Chief Compliance Sentinel (SOUQ-DIV-5)",
            }
        with open(source_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        return self.audit_source_code(source_code, source_name=source_path, concept_id=concept_id)

