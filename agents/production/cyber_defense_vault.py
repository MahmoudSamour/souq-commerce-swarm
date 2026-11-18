"""
SOUQ // Autonomous Cyber Defense & Security Vault
Comprehensive, zero-external-dependency security scanning micro-services for AI agents:
1. Prompt Injection & Adversarial Jailbreak Firewall
2. Smart Contract Honeypot & Reentrancy Radar
3. High-Entropy Secret & Private Key Leak Scanner
4. Deep AST Code Vulnerability Auditor
5. API Attack Surface & Defensive Header Linter
"""

import ast
import base64
import bisect
import ipaddress
import json
import math
import re
import socket
import time
import unicodedata
import urllib.parse
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

try:
    from agents.production.cyber_threat_intelligence import CyberThreatIntelligenceRadar
    _THREAT_RADAR = CyberThreatIntelligenceRadar()
except Exception:
    _THREAT_RADAR = None


def _build_line_starts(text: str) -> List[int]:
    """Precomputes 0-based start offsets for every line in text for O(log N) lookups."""
    starts: List[int] = [0]
    pos = text.find("\n")
    while pos != -1:
        starts.append(pos + 1)
        pos = text.find("\n", pos + 1)
    return starts


def _offset_to_line(line_starts: List[int], char_idx: int) -> int:
    """Converts a 0-based character offset to a 1-based line number using bisect."""
    return bisect.bisect_right(line_starts, max(0, char_idx))


def _spans_overlap(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """Returns True if two half-open character spans [start, end) overlap."""
    return a[0] < b[1] and b[0] < a[1]


class PromptInjectionFirewall:
    """
    Deterministic adversarial prompt injection and jailbreak detector.
    Protects autonomous agent LLMs from instruction overrides, system prompt exfiltration,
    and formatting hijack attacks before feeding untrusted content into context.
    """

    OVERRIDE_PATTERNS = [
        r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|directives|rules)",
        r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|directives|rules)",
        r"forget\s+(?:all\s+)?(?:previous|prior)\s+(?:rules|instructions|prompts)",
        r"(?:new|different)\s+(?:instructions|persona|identity)\s*:\s*",
        r"you\s+are\s+now\s+(?:DAN|unrestricted|jailbroken|evil|unfiltered)",
        r"developer\s+mode\s+(?:is\s+)?(?:active|enabled|on)",
        r"system\s*override\s*:\s*",
        r"override\s+safety\s+protocols",
        r"do\s+anything\s+now\s+mode",
    ]

    EXFILTRATION_PATTERNS = [
        r"(?:reveal|output|display|show|print|leak)\s+(?:your\s+)?(?:system\s+prompt|initial\s+prompt|instructions)",
        r"(?:what\s+(?:are|were)\s+your\s+instructions)",
        r"(?:print|output|display|reveal)\s+(?:all\s+)?(?:api\s*keys?|secrets?|tokens?|passwords?)",
        r"(?:what\s+is\s+your\s+private\s+key)",
        r"(?:export|dump)\s+(?:all\s+)?(?:environment\s+variables|env\s+vars)",
    ]

    DELIMITER_PATTERNS = [
        r"<system>",
        r"</system>",
        r"\[INST\]",
        r"\[/INST\]",
        r"<<SYS>>",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"---BEGIN\s+(?:SYSTEM\s+PROMPT|INSTRUCTIONS)---",
    ]

    INJECTION_RULES: List[Dict[str, str]] = [
        {
            "id": "PI-OVERRIDE-GEN",
            "pattern": OVERRIDE_PATTERNS[0],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Attempted to force LLM to disregard or override system instructions.",
        },
        {
            "id": "PI-OVERRIDE-DISREGARD",
            "pattern": OVERRIDE_PATTERNS[1],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Attempted to force LLM to disregard prior system directives.",
        },
        {
            "id": "PI-OVERRIDE-FORGET",
            "pattern": OVERRIDE_PATTERNS[2],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Attempted to wipe prior rules or system instructions.",
        },
        {
            "id": "PI-OVERRIDE-PERSONA",
            "pattern": OVERRIDE_PATTERNS[3],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Attempted unauthorized persona or instruction replacement.",
        },
        {
            "id": "PI-ROLEPLAY-DAN",
            "pattern": OVERRIDE_PATTERNS[4],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Adversarial roleplay jailbreak persona override.",
        },
        {
            "id": "PI-OVERRIDE-DEVMODE",
            "pattern": OVERRIDE_PATTERNS[5],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Attempted developer-mode safety bypass.",
        },
        {
            "id": "PI-OVERRIDE-SYSOVERRIDE",
            "pattern": OVERRIDE_PATTERNS[6],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Explicit system override directive.",
        },
        {
            "id": "PI-OVERRIDE-SAFETY",
            "pattern": OVERRIDE_PATTERNS[7],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Attempted explicit safety protocol override.",
        },
        {
            "id": "PI-OVERRIDE-DAN-MODE",
            "pattern": OVERRIDE_PATTERNS[8],
            "category": "INSTRUCTION_OVERRIDE",
            "severity": "CRITICAL",
            "description": "Attempted Do-Anything-Now jailbreak mode.",
        },
        {
            "id": "PI-EXFIL-SYSTEM",
            "pattern": EXFILTRATION_PATTERNS[0],
            "category": "PROMPT_EXFILTRATION",
            "severity": "HIGH",
            "description": "Attempted to exfiltrate system prompt or initial instructions.",
        },
        {
            "id": "PI-EXFIL-QUERY",
            "pattern": EXFILTRATION_PATTERNS[1],
            "category": "PROMPT_EXFILTRATION",
            "severity": "HIGH",
            "description": "Attempted direct inquiry into hidden system instructions.",
        },
        {
            "id": "PI-EXFIL-SECRETS",
            "pattern": EXFILTRATION_PATTERNS[2],
            "category": "PROMPT_EXFILTRATION",
            "severity": "HIGH",
            "description": "Attempted to exfiltrate API keys, secrets, tokens, or passwords.",
        },
        {
            "id": "PI-EXFIL-PRIVKEY",
            "pattern": EXFILTRATION_PATTERNS[3],
            "category": "PROMPT_EXFILTRATION",
            "severity": "HIGH",
            "description": "Attempted private key exfiltration.",
        },
        {
            "id": "PI-EXFIL-ENV",
            "pattern": EXFILTRATION_PATTERNS[4],
            "category": "PROMPT_EXFILTRATION",
            "severity": "HIGH",
            "description": "Attempted environment variable dump.",
        },
        {
            "id": "PI-DELIM-SYS-OPEN",
            "pattern": DELIMITER_PATTERNS[0],
            "category": "DELIMITER_INJECTION",
            "severity": "HIGH",
            "description": "Attempted delimiter injection mimicking <system> tag.",
        },
        {
            "id": "PI-DELIM-SYS-CLOSE",
            "pattern": DELIMITER_PATTERNS[1],
            "category": "DELIMITER_INJECTION",
            "severity": "HIGH",
            "description": "Attempted delimiter injection mimicking </system> tag.",
        },
        {
            "id": "PI-DELIM-INST-OPEN",
            "pattern": DELIMITER_PATTERNS[2],
            "category": "DELIMITER_INJECTION",
            "severity": "HIGH",
            "description": "Attempted delimiter injection mimicking [INST] marker.",
        },
        {
            "id": "PI-DELIM-INST-CLOSE",
            "pattern": DELIMITER_PATTERNS[3],
            "category": "DELIMITER_INJECTION",
            "severity": "HIGH",
            "description": "Attempted delimiter injection mimicking [/INST] marker.",
        },
        {
            "id": "PI-DELIM-LLAMA-SYS",
            "pattern": DELIMITER_PATTERNS[4],
            "category": "DELIMITER_INJECTION",
            "severity": "HIGH",
            "description": "Attempted delimiter injection mimicking <<SYS>> marker.",
        },
        {
            "id": "PI-DELIM-IM-START",
            "pattern": DELIMITER_PATTERNS[5],
            "category": "DELIMITER_INJECTION",
            "severity": "HIGH",
            "description": "Attempted delimiter injection mimicking ChatML im_start tag.",
        },
        {
            "id": "PI-DELIM-IM-END",
            "pattern": DELIMITER_PATTERNS[6],
            "category": "DELIMITER_INJECTION",
            "severity": "HIGH",
            "description": "Attempted delimiter injection mimicking ChatML im_end tag.",
        },
        {
            "id": "PI-DELIM-BEGIN-BLOCK",
            "pattern": DELIMITER_PATTERNS[7],
            "category": "DELIMITER_INJECTION",
            "severity": "HIGH",
            "description": "Attempted delimiter injection mimicking system prompt header block.",
        },
    ]

    _INVISIBLE_CHARS_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff\u00ad]")
    _BASE64_CHUNK_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/_-]{24,}={0,2}(?![A-Za-z0-9+/=_-])")

    def __init__(self):
        self.dynamic_rules = []
        if _THREAT_RADAR:
            try:
                sigs = _THREAT_RADAR.load_cached_signatures()
                self.dynamic_rules = sigs.get("prompt_injection_rules", [])
            except Exception:
                pass

    @classmethod
    def _strip_invisible_and_tags(cls, text: str) -> Tuple[str, int, str]:
        """
        Strips zero-width / bidi control characters and Unicode Tag characters (U+E0000..U+E007F).
        Also recovers any ASCII payload smuggled inside Unicode Tag blocks.
        """
        cleaned_chars: List[str] = []
        tag_ascii_chars: List[str] = []
        hidden_count = 0

        for ch in text:
            code = ord(ch)
            if 0xE0000 <= code <= 0xE007F:
                hidden_count += 1
                if 0xE0020 <= code <= 0xE007E:
                    tag_ascii_chars.append(chr(code - 0xE0000))
                continue
            if cls._INVISIBLE_CHARS_RE.match(ch):
                hidden_count += 1
                continue
            cleaned_chars.append(ch)

        return "".join(cleaned_chars), hidden_count, "".join(tag_ascii_chars)

    @classmethod
    def _extract_printable_base64_views(cls, text: str) -> List[Tuple[str, str]]:
        """Decodes valid printable UTF-8 Base64 chunks (>= 24 chars) into secondary scan views."""
        views: List[Tuple[str, str]] = []
        for idx, m in enumerate(cls._BASE64_CHUNK_RE.finditer(text)):
            chunk = m.group(0)
            if len(chunk) < 24:
                continue
            padded = chunk + ("=" * ((4 - (len(chunk) % 4)) % 4))
            decoded_bytes: Optional[bytes] = None
            for decoder in (base64.b64decode, base64.urlsafe_b64decode):
                try:
                    raw = decoder(padded)
                    if raw:
                        decoded_bytes = raw
                        break
                except Exception:
                    continue
            if not decoded_bytes:
                continue
            try:
                decoded_str = decoded_bytes.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if len(decoded_str) < 12:
                continue
            printable = sum(1 for c in decoded_str if c.isprintable() or c in "\r\n\t")
            if (printable / len(decoded_str)) >= 0.85 and (" " in decoded_str or ":" in decoded_str or "<" in decoded_str):
                norm_decoded = unicodedata.normalize("NFKC", decoded_str)
                clean_decoded, _, _ = cls._strip_invisible_and_tags(norm_decoded)
                views.append((f"base64_{idx}", clean_decoded))
        return views

    def scan_prompt(self, text: str, strict_mode: bool = False) -> Dict[str, Any]:
        start_t = time.time()
        findings: List[Dict[str, Any]] = []

        if not text or not isinstance(text, str):
            return {
                "status": "success",
                "verdict": "SAFE",
                "risk_score": 0.0,
                "findings": [],
                "sanitized_preview": "",
                "latency_ms": 0
            }

        normalized = unicodedata.normalize("NFKC", text)
        sanitized_view, hidden_count, tag_payload = self._strip_invisible_and_tags(normalized)

        scan_views: List[Tuple[str, str]] = [("sanitized", sanitized_view)]
        if len(tag_payload.strip()) >= 8:
            scan_views.append(("unicode_tags", unicodedata.normalize("NFKC", tag_payload)))
        scan_views.extend(self._extract_printable_base64_views(sanitized_view))

        all_rules: List[Dict[str, Any]] = list(self.INJECTION_RULES)
        for dyn in self.dynamic_rules:
            if isinstance(dyn, dict) and dyn.get("pattern"):
                all_rules.append(dyn)

        seen_rule_ids: Set[str] = set()
        seen_matched_texts: Set[str] = set()
        seen_spans_by_view: Dict[str, List[Tuple[int, int]]] = {}

        for view_name, view_text in scan_views:
            view_spans = seen_spans_by_view.setdefault(view_name, [])
            for rule in all_rules:
                rule_id = str(rule.get("id") or rule.get("pattern") or "")
                pat = rule.get("pattern", "")
                if not pat or (rule_id and rule_id in seen_rule_ids):
                    continue
                match = re.search(pat, view_text, re.IGNORECASE)
                if not match:
                    continue

                span = (match.start(), match.end())
                matched_text = match.group(0)
                matched_norm = matched_text.strip().lower()

                if matched_norm in seen_matched_texts or any(_spans_overlap(span, s) for s in view_spans):
                    continue

                if rule_id:
                    seen_rule_ids.add(rule_id)
                seen_matched_texts.add(matched_norm)
                view_spans.append(span)

                desc = rule.get("description", "Dynamic threat signature match.")
                if view_name.startswith("base64_"):
                    desc = f"{desc} (detected inside Base64-encoded payload)"
                elif view_name == "unicode_tags":
                    desc = f"{desc} (detected inside hidden Unicode Tag characters)"

                findings.append({
                    "rule_id": rule_id,
                    "category": rule.get("category", "ADVERSARIAL_INJECTION"),
                    "severity": rule.get("severity", "HIGH"),
                    "matched_pattern": matched_text,
                    "description": desc,
                })

        # 4. Check for Hidden / Zero-Width / Unicode Tag Characters (Evasion bypasses)
        if hidden_count > 0:
            findings.append({
                "rule_id": "PI-OBFUSCATION-HIDDEN-CHARS",
                "category": "OBFUSCATION_EVASION",
                "severity": "MEDIUM",
                "matched_pattern": f"{hidden_count} hidden/zero-width characters",
                "description": "Hidden zero-width or Unicode Tag characters detected, commonly used to bypass token-level safety filters."
            })

        # Calculate composite risk score [0.0 - 1.0]
        critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
        high_count = sum(1 for f in findings if f["severity"] == "HIGH")
        medium_count = sum(1 for f in findings if f["severity"] == "MEDIUM")

        raw_score = (critical_count * 0.5) + (high_count * 0.3) + (medium_count * 0.15)
        risk_score = round(min(1.0, raw_score), 2)

        verdict = "ATTACK_DETECTED" if risk_score >= (0.3 if strict_mode else 0.4) else "SAFE"
        latency_ms = int((time.time() - start_t) * 1000)

        return {
            "status": "success",
            "verdict": verdict,
            "risk_score": risk_score,
            "findings_count": len(findings),
            "findings": findings,
            "is_safe_to_execute": verdict == "SAFE",
            "tokens_saved_estimate": 10000,
            "latency_ms": latency_ms
        }


class SmartContractHoneypotRadar:
    """
    Solidity source code & bytecode honeypot and vulnerability radar.
    Protects Web3 trading bots from 99% sell taxes, transfer locks, reentrancy traps,
    and hidden owner backdoors on Base and EVM chains.
    """

    BASE_RPC_URLS = [
        "https://mainnet.base.org",
        "https://base-rpc.publicnode.com",
        "https://1rpc.io/base",
    ]
    EIP1967_IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"

    HONEYPOT_PATTERNS = [
        # Transfer Locks & Blacklists
        (r"require\s*\(\s*(?:from|to)\s*==\s*owner", "TRANSFER_LOCKED_TO_OWNER", "CRITICAL", "Only contract owner is permitted to transfer tokens. Guaranteed honeypot."),
        (r"isBlacklisted\s*\[\s*(?:from|to)\s*\]\s*==\s*true", "USER_BLACKLIST_GATE", "HIGH", "Arbitrary blacklist mapping blocks specific addresses from selling."),
        (r"(?:require|assert)\s*\(\s*!\s*isBlacklist(?:ed)?\s*\[", "BLACKLIST_TRANSFER_BLOCK", "HIGH", "Blacklist check blocks token transfers."),
        # Excessive Sell Tax Traps (> 25%)
        (r"(?:sellFee|sellTax|transferTax)\s*=\s*(?:[3-9][0-9]|100)", "EXTREME_SELL_TAX", "CRITICAL", "Sell tax configured at 30% - 100%, causing severe exit liquidity loss."),
        (r"(?:fee|tax)\s*>\s*25", "UNCONSTRAINED_HIGH_TAX", "HIGH", "Fee parameter exceeds safe decentralized trading threshold (> 25%)."),
        # tx.origin authentication bypass
        (r"tx\.origin\s*==\s*owner", "TX_ORIGIN_AUTHENTICATION", "MEDIUM", "Phishing vulnerability: uses tx.origin instead of msg.sender for authorization."),
        # Unchecked delegatecall
        (r"\.delegatecall\s*\(", "ARBITRARY_DELEGATECALL", "HIGH", "Delegatecall execution can allow malicious state mutation if target is variable."),
        # Self-destruct backdoor
        (r"selfdestruct\s*\(", "SELFDESTRUCT_BACKDOOR", "CRITICAL", "Contract contains selfdestruct capability allowing owner to terminate contract and steal funds.")
    ]

    RULE_ALIASES = {
        "PUBLIC_UNPROTECTED_MINT": "HIDDEN_MINT",
        "UNPROTECTED_PUBLIC_MINT": "HIDDEN_MINT",
        "SC-HIDDEN-MINT": "HIDDEN_MINT",
        "EXTREME_SELL_TAX_TRAP": "EXTREME_SELL_TAX",
        "SC-EXTREME-SELL-TAX": "EXTREME_SELL_TAX",
        "ARBITRARY_BLACKLIST_GATE": "USER_BLACKLIST_GATE",
        "SC-DYNAMIC-BLACKLIST": "USER_BLACKLIST_GATE",
        "SELFDESTRUCT_RUG_PULL": "SELFDESTRUCT_BACKDOOR",
        "SC-SELFDESTRUCT": "SELFDESTRUCT_BACKDOOR",
        "SC-TRANSFER-OWNER-LOCK": "TRANSFER_LOCKED_TO_OWNER",
        "SC-DYNAMIC-MAX-TX": "ZERO_MAX_TX_BLOCK",
    }

    _SOL_TOKEN_RE = re.compile(
        r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(/\*[\s\S]*?\*/|//[^\n]*)',
        re.MULTILINE,
    )
    _MINT_DECL_RE = re.compile(
        r"\bfunction\s+mint\s*\([^)]*\)\s*([^{;]*)\{",
        re.IGNORECASE | re.DOTALL,
    )
    _MINT_ACCESS_RE = re.compile(
        r"\b(?:onlyOwner|onlyRole|onlyAdmin|_checkOwner|_checkRole)\b"
        r"|require\s*\(\s*(?:msg\.sender|_msgSender\s*\(\s*\))\s*=="
        r"|if\s*\(\s*(?:msg\.sender|_msgSender\s*\(\s*\))\s*!=",
        re.IGNORECASE,
    )

    def __init__(self):
        self.dynamic_rules = []
        if _THREAT_RADAR:
            try:
                sigs = _THREAT_RADAR.load_cached_signatures()
                self.dynamic_rules = sigs.get("honeypot_rules", [])
            except Exception:
                pass

    @classmethod
    def _canonical_rule_id(cls, raw_id: str) -> str:
        return cls.RULE_ALIASES.get(raw_id, raw_id)

    @classmethod
    def _strip_solidity_comments(cls, source: str) -> str:
        """Strips // and /*...*/ Solidity comments while preserving string literals and line numbers."""
        def _repl(match: re.Match) -> str:
            if match.group(1) is not None:
                return match.group(1)
            comment = match.group(2) or ""
            newline_count = comment.count("\n")
            if newline_count > 0:
                return "\n" * newline_count
            return " " if comment.startswith("/*") else ""

        return cls._SOL_TOKEN_RE.sub(_repl, source)

    @staticmethod
    def _extract_balanced_body(source: str, open_brace_idx: int) -> str:
        """Extracts a Solidity function body starting from its opening '{' index."""
        depth = 0
        for idx in range(open_brace_idx, len(source)):
            ch = source[idx]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[open_brace_idx:idx + 1]
        return source[open_brace_idx:]

    @classmethod
    def _audit_mint_functions(
        cls,
        cleaned_code: str,
        line_starts: List[int],
    ) -> List[Dict[str, Any]]:
        """Inspects public/external mint() declarations for access-control modifiers or owner checks."""
        mint_findings: List[Dict[str, Any]] = []
        for m in cls._MINT_DECL_RE.finditer(cleaned_code):
            qualifiers = m.group(1) or ""
            if not re.search(r"\b(?:public|external)\b", qualifiers, re.IGNORECASE):
                continue
            open_brace_idx = m.end() - 1
            body = cls._extract_balanced_body(cleaned_code, open_brace_idx)
            line_no = _offset_to_line(line_starts, m.start())
            if cls._MINT_ACCESS_RE.search(qualifiers) or cls._MINT_ACCESS_RE.search(body):
                mint_findings.append({
                    "rule_id": "ACCESS_CONTROLLED_MINT",
                    "severity": "LOW",
                    "line": line_no,
                    "matched_code": m.group(0).strip(),
                    "description": "Public/external mint function is gated by an access-control modifier or sender check.",
                })
            else:
                mint_findings.append({
                    "rule_id": "HIDDEN_MINT",
                    "severity": "CRITICAL",
                    "line": line_no,
                    "matched_code": m.group(0).strip(),
                    "description": "Unprotected public/external mint function permits arbitrary token dilution.",
                })
        return mint_findings

    @classmethod
    def _call_base_rpc(cls, method: str, params: List[Any]) -> Tuple[Optional[Any], Optional[str]]:
        """Executes a JSON-RPC call across Base mainnet endpoints with automatic failover."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        headers = {"Content-Type": "application/json", "User-Agent": "SOUQ-Security-Vault/0.3"}
        for rpc_url in cls.BASE_RPC_URLS:
            try:
                resp = requests.post(rpc_url, json=payload, headers=headers, timeout=4.0)
                resp.raise_for_status()
                rpc_data = resp.json()
                if isinstance(rpc_data, dict) and "result" in rpc_data and not rpc_data.get("error"):
                    return rpc_data["result"], rpc_url
            except Exception:
                continue
        return None, None

    @classmethod
    def _inspect_onchain_base_contract(cls, contract_address: str) -> Dict[str, Any]:
        """
        Inspects a live Base EVM contract address via Base RPC (eth_getCode, eth_getStorageAt)
        and Base Blockscout verified-source API (including additional_sources).
        """
        addr = contract_address.strip()
        info: Dict[str, Any] = {
            "contract_address": addr,
            "chain": "base",
            "has_bytecode": False,
            "bytecode_bytes": 0,
            "is_verified_source": False,
            "fetched_source_code": "",
            "contract_name": None,
            "proxy_warning": False,
            "eip1967_implementation": None,
            "rpc_endpoint": None,
        }

        code_result, rpc_used = cls._call_base_rpc("eth_getCode", [addr, "latest"])
        if isinstance(code_result, str):
            code_hex = code_result.replace("0x", "")
            info["rpc_endpoint"] = rpc_used
            info["bytecode_bytes"] = len(code_hex) // 2
            info["has_bytecode"] = len(code_hex) > 2
            # EIP-1167 minimal proxy prefix check (363d3d373d3d3d363d73)
            if "363d3d373d3d3d363d73" in code_hex.lower():
                info["proxy_warning"] = True

        slot_result, _ = cls._call_base_rpc("eth_getStorageAt", [addr, cls.EIP1967_IMPL_SLOT, "latest"])
        if isinstance(slot_result, str):
            slot_hex = slot_result.lower().replace("0x", "").rjust(64, "0")
            if len(slot_hex) >= 40 and slot_hex[-40:] != ("0" * 40):
                info["proxy_warning"] = True
                info["eip1967_implementation"] = "0x" + slot_hex[-40:]

        try:
            bs_url = f"https://base.blockscout.com/api/v2/smart-contracts/{urllib.parse.quote(addr)}"
            resp = requests.get(bs_url, headers={"User-Agent": "SOUQ-Security-Vault/0.3"}, timeout=4.0)
            resp.raise_for_status()
            bs_data = resp.json()
            sources: List[str] = []
            primary_src = bs_data.get("source_code") or ""
            if primary_src:
                sources.append(primary_src)
            for extra in bs_data.get("additional_sources") or []:
                if isinstance(extra, dict) and extra.get("source_code"):
                    file_path = extra.get("file_path") or "additional_source.sol"
                    sources.append(f"// File: {file_path}\n{extra['source_code']}")
            combined_src = "\n\n".join(sources)
            if combined_src:
                info["is_verified_source"] = True
                info["fetched_source_code"] = combined_src
                info["contract_name"] = bs_data.get("name")
                info["source_files_count"] = len(sources)
            if bs_data.get("is_self_destructed"):
                info["self_destructed"] = True
        except Exception:
            pass

        return info

    def audit_contract_code(
        self,
        source_code: str = "",
        token_symbol: str = "TOKEN",
        contract_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_t = time.time()
        findings: List[Dict[str, Any]] = []
        seen_findings: Set[Tuple[str, int]] = set()
        onchain_meta: Optional[Dict[str, Any]] = None

        def _add_finding(item: Dict[str, Any]) -> None:
            canon_id = self._canonical_rule_id(str(item.get("rule_id") or ""))
            line_no = int(item.get("line") or 0)
            key = (canon_id, line_no)
            if key in seen_findings:
                return
            seen_findings.add(key)
            item_copy = dict(item)
            item_copy["rule_id"] = canon_id
            findings.append(item_copy)

        if contract_address and re.match(r"^0x[0-9a-fA-F]{40}$", contract_address.strip()):
            onchain_meta = self._inspect_onchain_base_contract(contract_address)
            if not source_code and onchain_meta.get("fetched_source_code"):
                source_code = onchain_meta["fetched_source_code"]
            if onchain_meta and not onchain_meta.get("has_bytecode") and not source_code:
                return {
                    "status": "error",
                    "contract_address": contract_address,
                    "message": "Address has no deployed EVM bytecode on Base mainnet and no source_code was supplied.",
                    "latency_ms": int((time.time() - start_t) * 1000),
                }
            if onchain_meta and onchain_meta.get("has_bytecode") and not onchain_meta.get("is_verified_source") and not source_code:
                _add_finding({
                    "rule_id": "UNVERIFIED_ONCHAIN_BYTECODE",
                    "severity": "HIGH",
                    "line": 0,
                    "matched_code": f"bytecode_bytes={onchain_meta['bytecode_bytes']}",
                    "description": "Contract bytecode exists on Base but verified Solidity source is not published on Blockscout.",
                })
            if onchain_meta and onchain_meta.get("eip1967_implementation"):
                impl_addr = onchain_meta["eip1967_implementation"]
                is_unverified = not onchain_meta.get("is_verified_source")
                _add_finding({
                    "rule_id": "EIP1967_PROXY_UNVERIFIED" if is_unverified else "EIP1967_UPGRADEABLE_PROXY",
                    "severity": "HIGH" if is_unverified else "MEDIUM",
                    "line": 0,
                    "matched_code": f"eip1967_impl={impl_addr}",
                    "description": f"EIP-1967 upgradeable proxy points to implementation {impl_addr}; verify and audit implementation contract.",
                })
            elif onchain_meta and onchain_meta.get("proxy_warning"):
                _add_finding({
                    "rule_id": "MINIMAL_PROXY_DELEGATECALL",
                    "severity": "MEDIUM",
                    "line": 0,
                    "matched_code": "EIP-1167 proxy pattern",
                    "description": "Upgradeable or minimal delegatecall proxy detected; verify implementation contract.",
                })

        if (not source_code or not isinstance(source_code, str)) and not onchain_meta:
            return {
                "status": "error",
                "message": "Empty or invalid source_code payload",
                "latency_ms": 0
            }

        source_code = source_code or ""
        cleaned_code = self._strip_solidity_comments(source_code)
        line_starts = _build_line_starts(cleaned_code)

        # 1. Access-control-aware mint audit
        for mint_item in self._audit_mint_functions(cleaned_code, line_starts):
            _add_finding(mint_item)

        # 2. Scan for honeypot patterns and backdoors
        for pattern, rule_id, severity, desc in self.HONEYPOT_PATTERNS:
            for m in re.finditer(pattern, cleaned_code, re.IGNORECASE):
                line_no = _offset_to_line(line_starts, m.start())
                _add_finding({
                    "rule_id": rule_id,
                    "severity": severity,
                    "line": line_no,
                    "matched_code": m.group(0),
                    "description": desc,
                })

        # 3. Dynamic Threat Intelligence Honeypot Signatures (deduplicated by canonical (rule_id, line))
        for rule in self.dynamic_rules:
            pat = rule.get("pattern", "")
            raw_rule_id = rule.get("rule_name", rule.get("id", "DYNAMIC_HONEYPOT_RULE"))
            canon_id = self._canonical_rule_id(raw_rule_id)
            if not pat or canon_id == "HIDDEN_MINT":
                continue
            severity = rule.get("severity", "CRITICAL")
            desc = rule.get("description", "Dynamic honeypot threat signature match.")
            for m in re.finditer(pat, cleaned_code, re.IGNORECASE):
                line_no = _offset_to_line(line_starts, m.start())
                _add_finding({
                    "rule_id": canon_id,
                    "severity": severity,
                    "line": line_no,
                    "matched_code": m.group(0),
                    "description": desc,
                })

        # 4. Check for Reentrancy vulnerability (State write after low-level call)
        reentrancy_found = False
        call_matches = list(re.finditer(r"\.call\s*\{[^}]*value\s*:[^}]*\}\s*\([^)]*\)", cleaned_code))
        has_reentrancy_guard = bool(re.search(r"nonReentrant|ReentrancyGuard", cleaned_code))

        if call_matches and not has_reentrancy_guard:
            reentrancy_found = True
            _add_finding({
                "rule_id": "REENTRANCY_WITHOUT_GUARD",
                "severity": "CRITICAL",
                "line": _offset_to_line(line_starts, call_matches[0].start()),
                "matched_code": call_matches[0].group(0),
                "description": "Low-level .call{value: ...}() invoked without ReentrancyGuard modifier.",
            })

        critical_traps = [f for f in findings if f["severity"] == "CRITICAL"]
        is_honeypot = len(critical_traps) > 0

        verdict = "HONEYPOT_HAZARD" if is_honeypot else ("VULNERABILITIES_DETECTED" if findings else "CLEAN_PASS")
        latency_ms = int((time.time() - start_t) * 1000)

        result: Dict[str, Any] = {
            "status": "success",
            "token_symbol": token_symbol,
            "verdict": verdict,
            "is_honeypot": is_honeypot,
            "total_issues": len(findings),
            "critical_count": len(critical_traps),
            "reentrancy_safe": not reentrancy_found,
            "issues": findings,
            "trading_recommendation": "DO_NOT_TRADE_HONEYPOT" if is_honeypot else ("TRADE_WITH_CAUTION" if findings else "SAFE_TO_TRADE"),
            "tokens_saved_estimate": 25000,
            "latency_ms": latency_ms
        }
        if onchain_meta:
            result["onchain_inspection"] = {
                k: v for k, v in onchain_meta.items() if k != "fetched_source_code"
            }
        return result


class SecretLeakScanner:
    """
    High-entropy secret, API key, and crypto private key scanner.
    Prevents autonomous agents from accidentally leaking credentials into prompts,
    git commits, or public memory.
    """

    _PRIVATE_KEY_ASSIGNMENT_RE = (
        r"(?i)(?:priv(?:ate)?[_-]?key|signer[_-]?key|wallet[_-]?key|deployer[_-]?key|"
        r"agent[_-]?key|secret[_-]?key|seed(?:_phrase)?|mnemonic|auth[_-]?key|signing[_-]?key)"
        r"[\"']?\s*[:=]\s*[\"']?(?:0x)?[0-9a-fA-F]{64}\b"
    )

    KEY_PATTERNS = [
        ("OPENAI_KEY", r"sk-proj-[a-zA-Z0-9_\-]{40,}", "CRITICAL", "OpenAI Project API Key"),
        ("OPENAI_LEGACY", r"sk-[a-zA-Z0-9]{32,48}", "CRITICAL", "OpenAI Standard API Key"),
        ("ANTHROPIC_KEY", r"sk-ant-[a-zA-Z0-9_\-]{32,}", "CRITICAL", "Anthropic Claude API Key"),
        ("AWS_ACCESS_KEY", r"AKIA[0-9A-Z]{16}", "CRITICAL", "Amazon Web Services Access Key ID"),
        ("GITHUB_PAT", r"gh[pousr]_[A-Za-z0-9_]{36,}", "CRITICAL", "GitHub Personal Access Token"),
        ("BASE_ETH_PRIVATE_KEY", _PRIVATE_KEY_ASSIGNMENT_RE, "CRITICAL", "Ethereum / Base 256-bit Private Key"),
        ("PEM_PRIVATE_KEY", r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "CRITICAL", "PEM Encoded TLS/SSH Private Key"),
        ("STRIPE_LIVE_KEY", r"sk_live_[0-9a-zA-Z]{24,}", "CRITICAL", "Stripe Production Secret Key"),
        ("SLACK_BOT_TOKEN", r"xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}", "CRITICAL", "Slack Bot User OAuth Token"),
        ("BEARER_AUTH_HEADER", r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", "HIGH", "HTTP Authorization Bearer Token"),
    ]

    SECRET_ID_ALIASES = {
        "OPENAI_API_KEY": "OPENAI_KEY",
        "OPENAI_PROJECT_KEY": "OPENAI_KEY",
        "ANTHROPIC_CLAUDE_KEY": "ANTHROPIC_KEY",
        "BASE_EVM_PRIVATE_KEY": "BASE_ETH_PRIVATE_KEY",
        "EVM_PRIVATE_KEY": "BASE_ETH_PRIVATE_KEY",
        "STRIPE_PROD_KEY": "STRIPE_LIVE_KEY",
    }

    _UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
    _PURE_HEX_HASH_RE = re.compile(r"^(?:0x)?[0-9a-fA-F]{32,128}$")
    _SRI_HASH_RE = re.compile(r"^sha(?:1|256|384|512)-[A-Za-z0-9+/=_-]+$", re.IGNORECASE)
    _URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")

    def __init__(self):
        self.dynamic_rules = []
        if _THREAT_RADAR:
            try:
                sigs = _THREAT_RADAR.load_cached_signatures()
                self.dynamic_rules = sigs.get("secret_rules", [])
            except Exception:
                pass

    @classmethod
    def _canonical_secret_id(cls, raw_id: str) -> str:
        return cls.SECRET_ID_ALIASES.get(raw_id, raw_id)

    @staticmethod
    def _calculate_shannon_entropy(string: str) -> float:
        """Calculates the Shannon entropy of a string."""
        if not string:
            return 0.0
        prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
        entropy = -sum(p * math.log(p) / math.log(2.0) for p in prob)
        return round(entropy, 3)

    @classmethod
    def _is_excluded_entropy_candidate(cls, content: str, start: int, end: int, token: str) -> bool:
        """Excludes URLs, UUIDs, and known hash digests from Shannon entropy leak detection."""
        if cls._UUID_RE.match(token) or cls._PURE_HEX_HASH_RE.match(token) or cls._SRI_HASH_RE.match(token):
            return True
        # Expand to whitespace boundaries to detect URLs cleanly
        ws_left = start
        while ws_left > 0 and not content[ws_left - 1].isspace() and content[ws_left - 1] not in "\"'()<>[]{}":
            ws_left -= 1
        ws_right = end
        while ws_right < len(content) and not content[ws_right].isspace() and content[ws_right] not in "\"'()<>[]{}":
            ws_right += 1
        surrounding = content[ws_left:ws_right]
        if cls._URL_SCHEME_RE.match(surrounding) or "://" in surrounding:
            return True
        return False

    def scan_for_secrets(self, content: str, entropy_threshold: float = 4.2) -> Dict[str, Any]:
        start_t = time.time()
        leaks: List[Dict[str, Any]] = []

        if not content or not isinstance(content, str):
            return {
                "status": "success",
                "verdict": "CLEAN",
                "total_leaks": 0,
                "leaks": [],
                "latency_ms": 0
            }

        line_starts = _build_line_starts(content)

        # 1. Regex pattern matching for known key formats + dynamic threat intel rules
        patterns_to_check: List[Tuple[str, str, str, str]] = list(self.KEY_PATTERNS)
        known_types: Set[str] = {self._canonical_secret_id(p[0]) for p in patterns_to_check}

        for item in self.dynamic_rules:
            if isinstance(item, (list, tuple)) and len(item) >= 4:
                raw_type, pat, sev, desc = str(item[0]), str(item[1]), str(item[2]), str(item[3])
            elif isinstance(item, dict):
                raw_type = str(item.get("id", "CUSTOM_SECRET"))
                pat = str(item.get("pattern", ""))
                sev = str(item.get("severity", "CRITICAL"))
                desc = str(item.get("description", "Dynamic secret token pattern."))
            else:
                continue

            canon_type = self._canonical_secret_id(raw_type)
            # Never reintroduce bare 64-hex matcher from stale signature caches
            if not pat or pat.strip() in (r"(?:0x)?[a-fA-F0-9]{64}", r"(?:0x)?[0-9a-fA-F]{64}"):
                continue
            if canon_type not in known_types:
                patterns_to_check.append((canon_type, pat, sev, desc))
                known_types.add(canon_type)

        matched_spans: List[Tuple[int, int]] = []
        seen_keys: Set[Tuple[str, int, int]] = set()

        for key_type, pattern, severity, desc in patterns_to_check:
            canon_type = self._canonical_secret_id(key_type)
            for match in re.finditer(pattern, content):
                val = match.group(0)
                span = (match.start(), match.end())
                # Ignore zero hashes / zero placeholders
                if val.endswith("0" * 64) or val in ("0x" + "0" * 64, "0" * 64):
                    continue
                line_no = _offset_to_line(line_starts, match.start())
                if (canon_type, line_no, span[0]) in seen_keys or any(_spans_overlap(span, s) for s in matched_spans):
                    continue

                seen_keys.add((canon_type, line_no, span[0]))
                matched_spans.append(span)
                redacted = val[:7] + "..." + val[-4:] if len(val) > 12 else "***REDACTED***"
                leaks.append({
                    "secret_type": canon_type,
                    "severity": severity,
                    "description": desc,
                    "line": line_no,
                    "redacted_sample": redacted
                })

        # 2. High-Entropy token detection in alphanumeric words (trailing Base64 '=' padding only)
        for match in re.finditer(r"[A-Za-z0-9_\-\+/]{22,}={0,2}", content):
            w = match.group(0)
            if len(w) < 24:
                continue
            span = (match.start(), match.end())
            if any(_spans_overlap(span, s) for s in matched_spans):
                continue
            if self._is_excluded_entropy_candidate(content, span[0], span[1], w):
                continue
            entropy = self._calculate_shannon_entropy(w)
            if entropy >= entropy_threshold:
                line_no = _offset_to_line(line_starts, span[0])
                redacted = w[:4] + "..." + w[-4:]
                matched_spans.append(span)
                leaks.append({
                    "secret_type": "HIGH_ENTROPY_CREDENTIAL",
                    "severity": "HIGH",
                    "description": f"High Shannon entropy string ({entropy} bits/symbol), likely a password, API hash, or secret key.",
                    "line": line_no,
                    "redacted_sample": redacted,
                    "entropy": entropy
                })

        verdict = "LEAKS_DETECTED" if leaks else "CLEAN"
        latency_ms = int((time.time() - start_t) * 1000)

        return {
            "status": "success",
            "verdict": verdict,
            "total_leaks": len(leaks),
            "leaks": leaks,
            "safe_to_publish": len(leaks) == 0,
            "tokens_saved_estimate": 15000,
            "latency_ms": latency_ms
        }


class DeepASTVulnerabilityAuditor:
    """
    Advanced Abstract Syntax Tree (AST) code vulnerability scanner for Python.
    Detects SQL injection, command injection, unsafe deserialization, SSRF,
    path traversal, weak cryptography, and dangerous dynamic execution.
    """

    _SQL_EXEC_METHODS = frozenset({"execute", "executemany", "raw", "query", "executescript"})
    _SQL_STMT_RE = re.compile(
        r"\b(?:SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+.+\s+SET|DELETE\s+FROM)\b",
        re.IGNORECASE | re.DOTALL,
    )
    _HTTP_CLIENT_METHODS = frozenset({"get", "post", "put", "delete", "patch", "head", "options", "request"})
    _HANDLER_HINT_RE = re.compile(
        r"(?:route|handler|endpoint|view|api|upload|download|serve|read_file|fetch_file|get_file)",
        re.IGNORECASE,
    )
    _UNTRUSTED_PARAM_RE = re.compile(
        r"(?:request|req|params|query|body|payload|user|file|path|fname|target|input)",
        re.IGNORECASE,
    )

    @staticmethod
    def _collect_import_aliases(tree: ast.AST) -> Dict[str, str]:
        """Maps imported symbol names to canonical dotted module/function paths."""
        aliases: Dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name
                    aliases[local] = alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    aliases[local] = f"{node.module}.{alias.name}"
        return aliases

    @staticmethod
    def _dotted_name(node: ast.AST) -> str:
        """Extracts dotted name for nested ast.Attribute / ast.Name nodes."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = DeepASTVulnerabilityAuditor._dotted_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    @classmethod
    def _resolve_target(cls, func_node: ast.AST, aliases: Dict[str, str]) -> str:
        dotted = cls._dotted_name(func_node)
        if not dotted:
            return ""
        parts = dotted.split(".")
        head = aliases.get(parts[0], parts[0])
        return ".".join([head] + parts[1:])

    @staticmethod
    def _contains_non_constant_concat(node: ast.AST) -> bool:
        """Returns True if an ast.BinOp(Add) expression combines any non-constant value."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return False
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return (
                DeepASTVulnerabilityAuditor._contains_non_constant_concat(node.left)
                or DeepASTVulnerabilityAuditor._contains_non_constant_concat(node.right)
            )
        return True

    @staticmethod
    def _extract_constant_str_parts(node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            return " ".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
        if isinstance(node, ast.BinOp):
            return (
                DeepASTVulnerabilityAuditor._extract_constant_str_parts(node.left)
                + " "
                + DeepASTVulnerabilityAuditor._extract_constant_str_parts(node.right)
            )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            return DeepASTVulnerabilityAuditor._extract_constant_str_parts(node.func.value)
        return ""

    @classmethod
    def _inspect_sql_expr(cls, expr: ast.AST) -> Optional[Tuple[str, str]]:
        """Classifies unsafe SQL query construction expressions."""
        if isinstance(expr, ast.JoinedStr):
            return ("SQL_INJECTION_FORMATTED_STRING", "Formatted string (f-string)")
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Mod):
            return ("SQL_INJECTION_PERCENT_FORMATTING", "Percent string formatting (%)")
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr == "format":
            return ("SQL_INJECTION_FORMAT_METHOD", "str.format() formatting")
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add) and cls._contains_non_constant_concat(expr):
            return ("SQL_INJECTION_STRING_CONCATENATION", "Dynamic string '+' concatenation")
        return None

    @staticmethod
    def _has_true_keyword(call_node: ast.Call, kw_name: str) -> bool:
        return any(
            kw.arg == kw_name and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in getattr(call_node, "keywords", [])
        )

    @staticmethod
    def _has_false_keyword(call_node: ast.Call, kw_name: str) -> bool:
        return any(
            kw.arg == kw_name and isinstance(kw.value, ast.Constant) and kw.value.value is False
            for kw in getattr(call_node, "keywords", [])
        )

    @staticmethod
    def _function_has_path_sanitization(fn_node: ast.AST) -> bool:
        for child in ast.walk(fn_node):
            if isinstance(child, ast.Call):
                name = DeepASTVulnerabilityAuditor._dotted_name(child.func)
                if name.endswith(("basename", "secure_filename", "abspath", "realpath", "commonpath", "resolve")):
                    return True
                if isinstance(child.func, ast.Attribute) and child.func.attr == "startswith":
                    return True
        return False

    @classmethod
    def _is_suspicious_handler(cls, fn_node: Optional[ast.FunctionDef | ast.AsyncFunctionDef]) -> bool:
        if fn_node is None:
            return False
        if cls._HANDLER_HINT_RE.search(fn_node.name):
            return True
        for dec in getattr(fn_node, "decorator_list", []):
            if cls._HANDLER_HINT_RE.search(ast.dump(dec)):
                return True
        for arg in getattr(fn_node.args, "args", []):
            if cls._UNTRUSTED_PARAM_RE.search(arg.arg):
                return True
        return False

    def scan_code(self, source_code: str) -> Dict[str, Any]:
        start_t = time.time()
        findings: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, int]] = set()

        if not isinstance(source_code, str):
            return {
                "status": "error",
                "error_type": "INVALID_INPUT",
                "message": "source_code must be a string.",
                "line": 0,
            }

        try:
            tree = ast.parse(source_code)
        except SyntaxError as se:
            return {
                "status": "error",
                "error_type": "SYNTAX_ERROR",
                "message": f"Syntax error at line {se.lineno}: {se.msg}",
                "line": se.lineno
            }
        except (RecursionError, ValueError) as exc:
            return {
                "status": "error",
                "error_type": type(exc).__name__.upper(),
                "message": str(exc),
                "line": 0,
            }

        aliases = self._collect_import_aliases(tree)

        def _record(rule_id: str, severity: str, message: str, line: int) -> None:
            key = (rule_id, line)
            if key not in seen:
                seen.add(key)
                findings.append({
                    "rule_id": rule_id,
                    "severity": severity,
                    "message": message,
                    "line": line,
                })

        def _visit(node: ast.AST, current_fn: Optional[ast.FunctionDef | ast.AsyncFunctionDef]) -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                current_fn = node

            if isinstance(node, ast.Call):
                lineno = getattr(node, "lineno", 1)
                resolved = self._resolve_target(node.func, aliases)
                short_name = resolved.split(".")[-1] if resolved else ""

                # 1. Dangerous Dynamic Code Execution
                if resolved in ("eval", "exec", "compile", "__import__", "builtins.eval", "builtins.exec", "builtins.compile"):
                    _record(
                        "DANGEROUS_DYNAMIC_EXECUTION",
                        "CRITICAL",
                        f"Dangerous dynamic execution '{short_name}()' allows arbitrary code execution.",
                        lineno,
                    )

                # 2. OS Shell / Command Injection
                if resolved in ("os.system", "os.popen", "subprocess.getoutput", "subprocess.getstatusoutput") or (
                    resolved.startswith("os.spawn")
                ) or (
                    isinstance(node.func, ast.Attribute) and short_name in ("system", "popen", "spawn")
                ):
                    _record(
                        "COMMAND_INJECTION_RISK",
                        "CRITICAL",
                        f"OS shell command '{resolved or short_name}()' invocation without argument isolation.",
                        lineno,
                    )
                elif resolved in (
                    "subprocess.run",
                    "subprocess.Popen",
                    "subprocess.call",
                    "subprocess.check_call",
                    "subprocess.check_output",
                ) and self._has_true_keyword(node, "shell"):
                    _record(
                        "COMMAND_INJECTION_RISK",
                        "CRITICAL",
                        f"Command injection risk: '{resolved}(..., shell=True)' executes via system shell.",
                        lineno,
                    )

                # 3. Insecure Deserialization (Pickle, Marshal, Unsafe YAML, PyTorch)
                if resolved in (
                    "pickle.loads", "pickle.load",
                    "_pickle.loads", "_pickle.load",
                    "cPickle.loads", "cPickle.load",
                ):
                    _record(
                        "INSECURE_DESERIALIZATION_PICKLE",
                        "CRITICAL",
                        "Insecure deserialization using pickle allows arbitrary remote code execution (RCE).",
                        lineno,
                    )
                elif resolved in ("marshal.loads", "marshal.load"):
                    _record(
                        "INSECURE_DESERIALIZATION_MARSHAL",
                        "CRITICAL",
                        "Insecure deserialization using marshal allows arbitrary code execution.",
                        lineno,
                    )
                elif resolved == "yaml.unsafe_load":
                    _record(
                        "UNSAFE_YAML_DESERIALIZATION",
                        "HIGH",
                        "Unsafe YAML deserialization via yaml.unsafe_load().",
                        lineno,
                    )
                elif resolved == "yaml.load":
                    has_safe = any(
                        kw.arg == "Loader" and (
                            (isinstance(kw.value, ast.Attribute) and kw.value.attr in ("SafeLoader", "CSafeLoader", "BaseLoader"))
                            or (isinstance(kw.value, ast.Name) and "Safe" in kw.value.id)
                        )
                        for kw in getattr(node, "keywords", [])
                    )
                    if not has_safe:
                        _record(
                            "UNSAFE_YAML_DESERIALIZATION",
                            "HIGH",
                            "Unsafe YAML deserialization without yaml.SafeLoader.",
                            lineno,
                        )
                elif resolved == "torch.load" and not self._has_true_keyword(node, "weights_only"):
                    _record(
                        "INSECURE_DESERIALIZATION_TORCH",
                        "HIGH",
                        "Unsafe PyTorch checkpoint deserialization without weights_only=True.",
                        lineno,
                    )

                # 4. Weak Cryptography (MD5 / SHA1)
                if short_name in ("md5", "sha1") and not self._has_false_keyword(node, "usedforsecurity"):
                    _record(
                        "WEAK_CRYPTOGRAPHIC_HASH",
                        "MEDIUM",
                        f"Use of broken cryptographic hash function '{short_name}'. Use SHA-256 or BLAKE2 instead.",
                        lineno,
                    )

                # 5. Potential SQL Injection
                if short_name in self._SQL_EXEC_METHODS:
                    candidate_args = list(node.args) + [
                        kw.value for kw in getattr(node, "keywords", []) if kw.arg in ("sql", "query", "statement")
                    ]
                    for arg in candidate_args:
                        sqli = self._inspect_sql_expr(arg)
                        if sqli:
                            rule_id, kind_desc = sqli
                            _record(
                                rule_id,
                                "CRITICAL",
                                f"{kind_desc} in database query method '{short_name}()'. Use parameterized queries.",
                                lineno,
                            )

                # 6. SSRF Risks (requests.*, httpx.*, urllib.request.urlopen with dynamic URL)
                is_http_call = (
                    resolved == "urllib.request.urlopen"
                    or (resolved.startswith("requests.") and short_name in self._HTTP_CLIENT_METHODS)
                    or (resolved.startswith("httpx.") and short_name in self._HTTP_CLIENT_METHODS)
                )
                if is_http_call:
                    url_expr: Optional[ast.AST] = None
                    if resolved in ("requests.request", "httpx.request"):
                        if len(node.args) >= 2:
                            url_expr = node.args[1]
                    elif node.args:
                        url_expr = node.args[0]
                    if url_expr is None:
                        for kw in getattr(node, "keywords", []):
                            if kw.arg == "url":
                                url_expr = kw.value
                                break
                    if url_expr is not None and not (isinstance(url_expr, ast.Constant) and isinstance(url_expr.value, str)):
                        _record(
                            "SSRF_DYNAMIC_URL",
                            "HIGH",
                            f"Potential SSRF risk: '{resolved}()' invoked with non-literal dynamic URL expression.",
                            lineno,
                        )

                # 7. Path Traversal Risks in handler / untrusted file contexts
                if (resolved in ("open", "builtins.open", "os.path.join")) and (
                    current_fn is not None and self._is_suspicious_handler(current_fn)
                ) and not self._function_has_path_sanitization(current_fn):
                    path_args = node.args[1:] if resolved == "os.path.join" and len(node.args) > 1 else node.args[:1]
                    for path_arg in path_args:
                        is_dynamic = not (isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str))
                        is_string_build = isinstance(path_arg, (ast.JoinedStr, ast.BinOp, ast.Subscript, ast.Attribute)) or (
                            isinstance(path_arg, ast.Call) and isinstance(path_arg.func, ast.Attribute) and path_arg.func.attr == "format"
                        )
                        if is_dynamic and (is_string_build or isinstance(path_arg, ast.Name)):
                            _record(
                                "PATH_TRAVERSAL_RISK",
                                "HIGH",
                                f"Potential path traversal: '{resolved}()' receives unvalidated dynamic path expression inside handler.",
                                lineno,
                            )
                            break

            # Also flag SQL strings assembled outside .execute(...) when clearly SQL statements
            elif isinstance(node, ast.Assign):
                sqli = self._inspect_sql_expr(node.value)
                if sqli and self._SQL_STMT_RE.search(self._extract_constant_str_parts(node.value)):
                    rule_id, kind_desc = sqli
                    _record(
                        rule_id,
                        "CRITICAL",
                        f"{kind_desc} building raw SQL query statement. Use parameterized queries.",
                        getattr(node, "lineno", 1),
                    )

            for child in ast.iter_child_nodes(node):
                _visit(child, current_fn)

        _visit(tree, None)

        verdict = "CLEAN" if not findings else "VULNERABILITIES_DETECTED"
        latency_ms = int((time.time() - start_t) * 1000)

        return {
            "status": "success",
            "analysis_verdict": verdict,
            "total_vulnerabilities": len(findings),
            "findings": findings,
            "tokens_saved_estimate": 15000,
            "latency_ms": latency_ms
        }

    # Alias for callers expecting scan_python_code
    scan_python_code = scan_code


ASTSecurityScanner = DeepASTVulnerabilityAuditor


class APIAttackSurfaceScanner:
    """
    API Attack Surface & Security Header Scanner.
    Audits HTTP endpoint responses for missing defense headers, wildcard CORS,
    and server information leakage, with strict SSRF protection.
    """

    MANDATORY_SECURITY_HEADERS = [
        ("X-Content-Type-Options", "nosniff", "Prevents MIME-sniffing attacks."),
        ("X-Frame-Options", "DENY", "Blocks clickjacking and UI redressing attacks."),
        ("Content-Security-Policy", None, "Restricts sources of executable scripts, stylesheets, and images."),
        ("Strict-Transport-Security", None, "Enforces HTTPS communication (HSTS)."),
        ("Referrer-Policy", None, "Protects user privacy and internal URL token leakage."),
    ]
    MAX_REDIRECT_HOPS = 3
    _OBFUSCATED_IP_RE = re.compile(
        r"^(?:0x[0-9a-f]+|0[0-7]+|\d+)(?:\.(?:0x[0-9a-f]+|0[0-7]+|\d+)){0,3}$",
        re.IGNORECASE,
    )

    @staticmethod
    def _is_public_ip(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Verifies an IP address is strictly globally routable and not private/loopback/metadata."""
        if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped is not None:
            ip_obj = ip_obj.ipv4_mapped
        return bool(
            ip_obj.is_global
            and not (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            )
        )

    @classmethod
    def _validate_public_url(
        cls,
        url: str,
        allow_unresolved_domain: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates URL scheme (http/https), hostname, and resolved DNS IP addresses
        against SSRF targets (localhost, RFC1918, link-local metadata 169.254.*, IPv6 ULA/LLA).
        """
        if not isinstance(url, str) or not url.strip():
            return False, "Invalid empty URL."

        try:
            parsed = urllib.parse.urlparse(url.strip())
            port = parsed.port
        except ValueError as exc:
            return False, f"Invalid URL format: {exc}"

        scheme = (parsed.scheme or "").lower()
        if scheme not in ("http", "https"):
            return False, f"Unsupported or blocked URL scheme '{scheme}'. Only http and https are allowed."

        if not parsed.netloc or not parsed.hostname:
            return False, f"Invalid URL format: '{url}'"

        if parsed.username or parsed.password:
            return False, "Embedded credentials in URL are not permitted."

        hostname = parsed.hostname.strip().rstrip(".").lower()
        if not hostname or hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
            return False, f"SSRF protection blocked internal/local hostname '{hostname}'."

        host_no_zone = hostname.split("%", 1)[0]
        try:
            ip_lit = ipaddress.ip_address(host_no_zone)
            if not cls._is_public_ip(ip_lit):
                return False, f"SSRF protection blocked non-public IP address '{host_no_zone}'."
            return True, None
        except ValueError:
            if cls._OBFUSCATED_IP_RE.match(host_no_zone):
                return False, f"SSRF protection blocked ambiguous numeric IP hostname '{host_no_zone}'."

        try:
            addr_infos = socket.getaddrinfo(hostname, port)
        except OSError as exc:
            if allow_unresolved_domain:
                return True, None
            return False, f"DNS resolution failed for '{hostname}': {exc}"

        if not addr_infos:
            return False, f"No DNS records resolved for '{hostname}'."

        for info in addr_infos:
            raw_ip = str(info[4][0]).split("%", 1)[0]
            try:
                resolved_ip = ipaddress.ip_address(raw_ip)
            except ValueError:
                return False, f"Invalid resolved IP '{raw_ip}' for '{hostname}'."
            if not cls._is_public_ip(resolved_ip):
                return False, f"SSRF protection blocked non-public resolved IP '{raw_ip}' for '{hostname}'."

        return True, None

    def audit_url(self, target_url: str, headers_to_check: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        start_t = time.time()

        if headers_to_check is not None and (
            not isinstance(headers_to_check, dict)
            or not all(isinstance(k, str) and isinstance(v, str) for k, v in headers_to_check.items())
        ):
            return {
                "status": "error",
                "target_url": target_url,
                "message": "headers_to_check must be a dictionary of HTTP header name -> value strings.",
            }

        is_valid, err_msg = self._validate_public_url(
            target_url,
            allow_unresolved_domain=bool(headers_to_check),
        )
        if not is_valid:
            return {
                "status": "error",
                "target_url": target_url,
                "message": err_msg or f"Invalid or blocked URL: '{target_url}'",
            }

        observed_headers: Dict[str, str] = {}
        fetch_error: Optional[str] = None

        if headers_to_check:
            observed_headers = {str(k).lower(): str(v) for k, v in headers_to_check.items()}
        else:
            current_url = target_url.strip()
            req_headers = {"User-Agent": "SouqSecurityAuditor/1.0"}
            try:
                for hop in range(self.MAX_REDIRECT_HOPS + 1):
                    resp = requests.get(
                        current_url,
                        headers=req_headers,
                        timeout=10.0,
                        allow_redirects=False,
                    )
                    if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("Location"):
                        if hop >= self.MAX_REDIRECT_HOPS:
                            fetch_error = f"Too many redirects (exceeded {self.MAX_REDIRECT_HOPS} hops)."
                            break
                        next_url = urllib.parse.urljoin(current_url, resp.headers["Location"])
                        ok, redir_err = self._validate_public_url(next_url, allow_unresolved_domain=False)
                        if not ok:
                            fetch_error = f"Blocked unsafe redirect target: {redir_err}"
                            break
                        current_url = next_url
                        continue
                    observed_headers = {str(k).lower(): str(v) for k, v in resp.headers.items()}
                    break
            except Exception as ex:
                fetch_error = str(ex)

        if fetch_error:
            return {
                "status": "error",
                "target_url": target_url,
                "message": f"Failed to reach target URL: {fetch_error}"
            }

        missing_headers = []
        header_recommendations = []
        for header_name, expected_val, desc in self.MANDATORY_SECURITY_HEADERS:
            key_low = header_name.lower()
            if key_low not in observed_headers:
                missing_headers.append(header_name)
                header_recommendations.append(f"Add '{header_name}': {desc}")
            elif expected_val and expected_val.lower() not in observed_headers[key_low].lower():
                header_recommendations.append(f"Header '{header_name}' is set to '{observed_headers[key_low]}', expected '{expected_val}'.")

        # Check for Wildcard CORS on sensitive APIs
        cors_header = observed_headers.get("access-control-allow-origin", "")
        cors_wildcard = cors_header.strip() == "*"

        # Check for Server Information Leakage
        server_header = observed_headers.get("server", "")
        powered_by = observed_headers.get("x-powered-by", "")

        # Scoring: A (0 missing), B (1-2 missing), C (3-4 missing), F (all missing)
        missing_count = len(missing_headers)
        if missing_count == 0:
            grade = "A"
        elif missing_count <= 2:
            grade = "B"
        elif missing_count <= 4:
            grade = "C"
        else:
            grade = "F"

        latency_ms = int((time.time() - start_t) * 1000)

        return {
            "status": "success",
            "target_url": target_url,
            "security_grade": grade,
            "missing_security_headers": missing_headers,
            "wildcard_cors_active": cors_wildcard,
            "exposed_server_info": {
                "server": server_header or "Hidden (Good)",
                "x_powered_by": powered_by or "Hidden (Good)"
            },
            "hardening_recommendations": header_recommendations,
            "tokens_saved_estimate": 12000,
            "latency_ms": latency_ms
        }
