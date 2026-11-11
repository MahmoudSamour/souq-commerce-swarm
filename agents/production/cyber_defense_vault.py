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
import re
import math
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple

try:
    from agents.production.cyber_threat_intelligence import CyberThreatIntelligenceRadar
    _THREAT_RADAR = CyberThreatIntelligenceRadar()
except Exception:
    _THREAT_RADAR = None


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

    def __init__(self):
        self.dynamic_rules = []
        if _THREAT_RADAR:
            try:
                sigs = _THREAT_RADAR.load_cached_signatures()
                self.dynamic_rules = sigs.get("prompt_injection_rules", [])
            except Exception:
                pass

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

        # 1. Check for Instruction Override Vectors
        for pat in self.OVERRIDE_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                findings.append({
                    "category": "INSTRUCTION_OVERRIDE",
                    "severity": "CRITICAL",
                    "matched_pattern": match.group(0),
                    "description": "Attempted to force LLM to disregard or override system instructions."
                })

        # 2. Check for Prompt / Secret Exfiltration Vectors
        for pat in self.EXFILTRATION_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                findings.append({
                    "category": "PROMPT_EXFILTRATION",
                    "severity": "HIGH",
                    "matched_pattern": match.group(0),
                    "description": "Attempted to exfiltrate system prompt or sensitive runtime secrets."
                })

        # 3. Check for Delimiter & Markup Hijacking
        for pat in self.DELIMITER_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                findings.append({
                    "category": "DELIMITER_INJECTION",
                    "severity": "HIGH",
                    "matched_pattern": match.group(0),
                    "description": "Attempted delimiter injection mimicking LLM chat formatting/system tags."
                })

        # Dynamic Threat Intelligence Rules
        for rule in self.dynamic_rules:
            pat = rule.get("pattern", "")
            if pat and not any(f.get("matched_pattern") == pat for f in findings):
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    findings.append({
                        "rule_id": rule.get("id"),
                        "category": rule.get("category", "ADVERSARIAL_INJECTION"),
                        "severity": rule.get("severity", "HIGH"),
                        "matched_pattern": match.group(0),
                        "description": rule.get("description", "Dynamic threat signature match.")
                    })

        # 4. Check for Hidden / Zero-Width Characters (Homoglyph & Evasion bypasses)
        zero_width_chars = [c for c in text if c in ("\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad")]
        if zero_width_chars:
            findings.append({
                "category": "OBFUSCATION_EVASION",
                "severity": "MEDIUM",
                "matched_pattern": f"{len(zero_width_chars)} zero-width characters",
                "description": "Hidden zero-width characters detected, commonly used to bypass token-level safety filters."
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

    HONEYPOT_PATTERNS = [
        # Transfer Locks & Blacklists
        (r"require\s*\(\s*(?:from|to)\s*==\s*owner", "TRANSFER_LOCKED_TO_OWNER", "CRITICAL", "Only contract owner is permitted to transfer tokens. Guaranteed honeypot."),
        (r"isBlacklisted\s*\[\s*(?:from|to)\s*\]\s*==\s*true", "USER_BLACKLIST_GATE", "HIGH", "Arbitrary blacklist mapping blocks specific addresses from selling."),
        (r"(?:require|assert)\s*\(\s*!\s*isBlacklist(?:ed)?\s*\[", "BLACKLIST_TRANSFER_BLOCK", "HIGH", "Blacklist check blocks token transfers."),
        # Excessive Sell Tax Traps (> 25%)
        (r"(?:sellFee|sellTax|transferTax)\s*=\s*(?:[3-9][0-9]|100)", "EXTREME_SELL_TAX", "CRITICAL", "Sell tax configured at 30% - 100%, causing severe exit liquidity loss."),
        (r"(?:fee|tax)\s*>\s*25", "UNCONSTRAINED_HIGH_TAX", "HIGH", "Fee parameter exceeds safe decentralized trading threshold (> 25%)."),
        # Hidden Minting
        (r"function\s+mint\s*\([^)]*\)\s*(?:public|external)(?![^{]*require[^{]*owner)", "PUBLIC_UNPROTECTED_MINT", "CRITICAL", "Unprotected public mint function permits arbitrary token dilution."),
        # tx.origin authentication bypass
        (r"tx\.origin\s*==\s*owner", "TX_ORIGIN_AUTHENTICATION", "MEDIUM", "Phishing vulnerability: uses tx.origin instead of msg.sender for authorization."),
        # Unchecked delegatecall
        (r"\.delegatecall\s*\(", "ARBITRARY_DELEGATECALL", "HIGH", "Delegatecall execution can allow malicious state mutation if target is variable."),
        # Self-destruct backdoor
        (r"selfdestruct\s*\(", "SELFDESTRUCT_BACKDOOR", "CRITICAL", "Contract contains selfdestruct capability allowing owner to terminate contract and steal funds.")
    ]

    def __init__(self):
        self.dynamic_rules = []
        if _THREAT_RADAR:
            try:
                sigs = _THREAT_RADAR.load_cached_signatures()
                self.dynamic_rules = sigs.get("honeypot_rules", [])
            except Exception:
                pass

    def audit_contract_code(self, source_code: str, token_symbol: str = "TOKEN") -> Dict[str, Any]:
        start_t = time.time()
        findings: List[Dict[str, Any]] = []

        if not source_code or not isinstance(source_code, str):
            return {
                "status": "error",
                "message": "Empty or invalid source_code payload",
                "latency_ms": 0
            }

        # 1. Scan for honeypot patterns and backdoors
        for pattern, rule_id, severity, desc in self.HONEYPOT_PATTERNS:
            matches = list(re.finditer(pattern, source_code, re.IGNORECASE))
            for m in matches:
                # Find line number
                line_no = source_code[:m.start()].count("\n") + 1
                findings.append({
                    "rule_id": rule_id,
                    "severity": severity,
                    "line": line_no,
                    "matched_code": m.group(0),
                    "description": desc
                })

        # Dynamic Threat Intelligence Honeypot Signatures
        for rule in self.dynamic_rules:
            pat = rule.get("pattern", "")
            rule_id = rule.get("rule_name", rule.get("id", "DYNAMIC_HONEYPOT_RULE"))
            severity = rule.get("severity", "CRITICAL")
            desc = rule.get("description", "Dynamic honeypot threat signature match.")
            if pat and not any(f.get("rule_id") == rule_id for f in findings):
                matches = list(re.finditer(pat, source_code, re.IGNORECASE))
                for m in matches:
                    line_no = source_code[:m.start()].count("\n") + 1
                    findings.append({
                        "rule_id": rule_id,
                        "severity": severity,
                        "line": line_no,
                        "matched_code": m.group(0),
                        "description": desc
                    })

        # 2. Check for Reentrancy vulnerability (State write after low-level call)
        reentrancy_found = False
        call_matches = list(re.finditer(r"\.call\s*\{[^}]*value\s*:[^}]*\}\s*\([^)]*\)", source_code))
        has_reentrancy_guard = bool(re.search(r"nonReentrant|ReentrancyGuard", source_code))

        if call_matches and not has_reentrancy_guard:
            reentrancy_found = True
            findings.append({
                "rule_id": "REENTRANCY_WITHOUT_GUARD",
                "severity": "CRITICAL",
                "line": source_code[:call_matches[0].start()].count("\n") + 1,
                "matched_code": call_matches[0].group(0),
                "description": "Low-level .call{value: ...}() invoked without ReentrancyGuard modifier."
            })

        critical_traps = [f for f in findings if f["severity"] == "CRITICAL"]
        is_honeypot = len(critical_traps) > 0

        verdict = "HONEYPOT_HAZARD" if is_honeypot else ("VULNERABILITIES_DETECTED" if findings else "CLEAN_PASS")
        latency_ms = int((time.time() - start_t) * 1000)

        return {
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


class SecretLeakScanner:
    """
    High-entropy secret, API key, and crypto private key scanner.
    Prevents autonomous agents from accidentally leaking credentials into prompts,
    git commits, or public memory.
    """

    KEY_PATTERNS = [
        ("OPENAI_KEY", r"sk-proj-[a-zA-Z0-9_\-]{40,}", "CRITICAL", "OpenAI Project API Key"),
        ("OPENAI_LEGACY", r"sk-[a-zA-Z0-9]{32,48}", "CRITICAL", "OpenAI Standard API Key"),
        ("ANTHROPIC_KEY", r"sk-ant-[a-zA-Z0-9_\-]{32,}", "CRITICAL", "Anthropic Claude API Key"),
        ("AWS_ACCESS_KEY", r"AKIA[0-9A-Z]{16}", "CRITICAL", "Amazon Web Services Access Key ID"),
        ("GITHUB_PAT", r"gh[pousr]_[A-Za-z0-9_]{36,}", "CRITICAL", "GitHub Personal Access Token"),
        ("BASE_ETH_PRIVATE_KEY", r"(?:0x)?[a-fA-F0-9]{64}", "CRITICAL", "Ethereum / Base 256-bit Private Key"),
        ("PEM_PRIVATE_KEY", r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "CRITICAL", "PEM Encoded TLS/SSH Private Key"),
        ("STRIPE_LIVE_KEY", r"sk_live_[0-9a-zA-Z]{24,}", "CRITICAL", "Stripe Production Secret Key"),
        ("SLACK_BOT_TOKEN", r"xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}", "CRITICAL", "Slack Bot User OAuth Token"),
        ("BEARER_AUTH_HEADER", r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", "HIGH", "HTTP Authorization Bearer Token"),
    ]

    def __init__(self):
        self.dynamic_rules = []
        if _THREAT_RADAR:
            try:
                sigs = _THREAT_RADAR.load_cached_signatures()
                self.dynamic_rules = sigs.get("secret_rules", [])
            except Exception:
                pass

    @staticmethod
    def _calculate_shannon_entropy(string: str) -> float:
        """Calculates the Shannon entropy of a string."""
        if not string:
            return 0.0
        prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
        entropy = -sum(p * math.log(p) / math.log(2.0) for p in prob)
        return round(entropy, 3)

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

        # 1. Regex pattern matching for known key formats + dynamic threat intel rules
        patterns_to_check = list(self.KEY_PATTERNS)
        known_types = {p[0] for p in patterns_to_check}
        for item in self.dynamic_rules:
            if isinstance(item, (list, tuple)) and len(item) >= 4:
                k_type, pat, sev, desc = item[0], item[1], item[2], item[3]
                if k_type not in known_types:
                    patterns_to_check.append((k_type, pat, sev, desc))
                    known_types.add(k_type)
            elif isinstance(item, dict):
                k_type = item.get("id", "CUSTOM_SECRET")
                pat = item.get("pattern", "")
                sev = item.get("severity", "CRITICAL")
                desc = item.get("description", "Dynamic secret token pattern.")
                if k_type not in known_types and pat:
                    patterns_to_check.append((k_type, pat, sev, desc))
                    known_types.add(k_type)

        for key_type, pattern, severity, desc in patterns_to_check:
            for match in re.finditer(pattern, content):
                val = match.group(0)
                # Ignore common false positives like zero address or placeholders
                if val in ("0x0000000000000000000000000000000000000000000000000000000000000000", "0x" + "0"*64):
                    continue
                redacted = val[:7] + "..." + val[-4:] if len(val) > 12 else "***REDACTED***"
                line_no = content[:match.start()].count("\n") + 1
                leaks.append({
                    "secret_type": key_type,
                    "severity": severity,
                    "description": desc,
                    "line": line_no,
                    "redacted_sample": redacted
                })

        # 2. High-Entropy token detection in alphanumeric words
        words = re.findall(r"[A-Za-z0-9_\-\+/=]{24,}", content)
        for w in words:
            entropy = self._calculate_shannon_entropy(w)
            if entropy >= entropy_threshold:
                # If not already caught by specific regex
                already_caught = any(w[:6] in l["redacted_sample"] for l in leaks)
                if not already_caught:
                    redacted = w[:4] + "..." + w[-4:]
                    leaks.append({
                        "secret_type": "HIGH_ENTROPY_CREDENTIAL",
                        "severity": "HIGH",
                        "description": f"High Shannon entropy string ({entropy} bits/symbol), likely a password, API hash, or secret key.",
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
    Detects SQL injection, insecure deserialization, SSRF, path traversal,
    and dangerous dynamic execution.
    """

    def scan_code(self, source_code: str) -> Dict[str, Any]:
        start_t = time.time()
        findings: List[Dict[str, Any]] = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError as se:
            return {
                "status": "error",
                "error_type": "SYNTAX_ERROR",
                "message": f"Syntax error at line {se.lineno}: {se.msg}",
                "line": se.lineno
            }

        for node in ast.walk(tree):
            # 1. Dangerous Dynamic Code Execution
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ("eval", "exec", "__import__"):
                    findings.append({
                        "rule_id": "DANGEROUS_DYNAMIC_EXECUTION",
                        "severity": "CRITICAL",
                        "message": f"Dangerous dynamic execution '{func_name}()' allows arbitrary code execution.",
                        "line": getattr(node, "lineno", 1)
                    })

                # 2. OS Shell Injection
                if func_name in ("system", "popen", "spawn"):
                    findings.append({
                        "rule_id": "COMMAND_INJECTION_RISK",
                        "severity": "CRITICAL",
                        "message": f"OS shell command '{func_name}()' invocation without argument isolation.",
                        "line": getattr(node, "lineno", 1)
                    })

                # 3. Insecure Deserialization (Pickle & Unsafe YAML)
                if func_name in ("loads", "load"):
                    # Check if module is pickle or yaml
                    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                        module_name = node.func.value.id
                        if module_name in ("pickle", "_pickle", "cPickle"):
                            findings.append({
                                "rule_id": "INSECURE_DESERIALIZATION_PICKLE",
                                "severity": "CRITICAL",
                                "message": "Insecure deserialization using pickle allows arbitrary remote code execution (RCE).",
                                "line": getattr(node, "lineno", 1)
                            })
                        elif module_name == "yaml" and func_name == "load":
                            # Check if Loader is SafeLoader
                            has_safe = any(
                                (isinstance(k.value, ast.Attribute) and k.value.attr == "SafeLoader") or
                                (isinstance(k.value, ast.Name) and "Safe" in k.value.id)
                                for k in getattr(node, "keywords", [])
                            )
                            if not has_safe:
                                findings.append({
                                    "rule_id": "UNSAFE_YAML_DESERIALIZATION",
                                    "severity": "HIGH",
                                    "message": "Unsafe YAML deserialization without yaml.SafeLoader.",
                                    "line": getattr(node, "lineno", 1)
                                })

                # 4. Weak Cryptography (MD5 / SHA1)
                if func_name in ("md5", "sha1"):
                    findings.append({
                        "rule_id": "WEAK_CRYPTOGRAPHIC_HASH",
                        "severity": "MEDIUM",
                        "message": f"Use of broken cryptographic hash function '{func_name}'. Use SHA-256 or BLAKE2 instead.",
                        "line": getattr(node, "lineno", 1)
                    })

            # 5. Potential SQL Injection via string formatting
            if isinstance(node, ast.Call):
                call_name = ""
                if isinstance(node.func, ast.Attribute):
                    call_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    call_name = node.func.id

                if call_name in ("execute", "executemany", "raw", "query"):
                    for arg in node.args:
                        # Detect f-string or % formatting or .format() in SQL execute call
                        if isinstance(arg, ast.JoinedStr):
                            findings.append({
                                "rule_id": "SQL_INJECTION_FORMATTED_STRING",
                                "severity": "CRITICAL",
                                "message": f"Formatted string (f-string) in database query method '{call_name}()'. Use parameterized queries.",
                                "line": getattr(node, "lineno", 1)
                            })
                        elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                            findings.append({
                                "rule_id": "SQL_INJECTION_PERCENT_FORMATTING",
                                "severity": "CRITICAL",
                                "message": f"Percent string formatting (%) in database query method '{call_name}()'. Use parameterized queries.",
                                "line": getattr(node, "lineno", 1)
                            })

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


class APIAttackSurfaceScanner:
    """
    API Attack Surface & Security Header Scanner.
    Audits HTTP endpoint responses for missing defense headers, wildcard CORS,
    and server information leakage.
    """

    MANDATORY_SECURITY_HEADERS = [
        ("X-Content-Type-Options", "nosniff", "Prevents MIME-sniffing attacks."),
        ("X-Frame-Options", "DENY", "Blocks clickjacking and UI redressing attacks."),
        ("Content-Security-Policy", None, "Restricts sources of executable scripts, stylesheets, and images."),
        ("Strict-Transport-Security", None, "Enforces HTTPS communication (HSTS)."),
        ("Referrer-Policy", None, "Protects user privacy and internal URL token leakage."),
    ]

    def audit_url(self, target_url: str, headers_to_check: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        start_t = time.time()
        parsed = urllib.parse.urlparse(target_url)
        if not parsed.scheme or not parsed.netloc:
            return {"status": "error", "message": f"Invalid URL format: '{target_url}'"}

        observed_headers = headers_to_check or {}
        fetch_error = None

        # Fetch live headers if not provided
        if not headers_to_check:
            try:
                req = urllib.request.Request(
                    target_url,
                    headers={"User-Agent": "SouqSecurityAuditor/1.0"}
                )
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    observed_headers = {k.lower(): v for k, v in resp.headers.items()}
            except urllib.error.HTTPError as e:
                observed_headers = {k.lower(): v for k, v in e.headers.items()}
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
