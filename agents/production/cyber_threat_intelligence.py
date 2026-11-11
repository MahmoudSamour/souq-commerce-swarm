"""
SOUQ // Sayf Cyber Threat Intelligence Agent (سيف - الحارس السيبراني)
Specialist Cybersecurity Agent operating under the Update Team Lead.
Continuously synthesizes and updates threat intelligence signatures:
1. Prompt Injection & Adversarial Jailbreak Patterns
2. Smart Contract Honeypot & Reentrancy Signatures
3. High-Entropy Secret & Key Formats (OpenAI, Anthropic, HuggingFace, Groq, DeepSeek)
"""

import os
import json
import time
from typing import Dict, Any, List

CACHE_FILE_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
    "data", "cache", "cyber_threat_signatures.json"
)


class CyberThreatIntelligenceRadar:
    """
    Autonomous cybersecurity intelligence agent.
    Collects, compiles, and publishes hot-reloading threat signatures
    for the SOUQ cyber defense suite.
    """

    def __init__(self, cache_path: str = CACHE_FILE_PATH):
        self.cache_path = cache_path
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

    def fetch_latest_threat_signatures(self) -> Dict[str, Any]:
        """
        Synthesizes the latest evolving threat intelligence definitions.
        In production, this queries security feeds, CVE databases, and research sources.
        """
        now = time.time()

        # 1. Advanced Prompt Injection & Jailbreak Signatures
        prompt_injection_rules = [
            {
                "id": "PI-OVERRIDE-GEN",
                "pattern": r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|directives|rules)",
                "category": "INSTRUCTION_OVERRIDE",
                "severity": "CRITICAL",
                "description": "Standard instruction wipe override attempt."
            },
            {
                "id": "PI-ROLEPLAY-DAN",
                "pattern": r"you\s+are\s+now\s+(?:DAN|unrestricted|jailbroken|evil|unfiltered|STAN)",
                "category": "ROLEPLAY_JAILBREAK",
                "severity": "CRITICAL",
                "description": "Adversarial roleplay jailbreak personality persona."
            },
            {
                "id": "PI-HYPOTHETICAL-BYPASS",
                "pattern": r"(?:hypothetical|fictional)\s+(?:scenario|world)\s+where\s+(?:all\s+)?(?:rules|ethics|safety)\s+(?:are\s+)?(?:removed|disabled|ignored)",
                "category": "HYPOTHETICAL_BYPASS",
                "severity": "HIGH",
                "description": "Hypothetical framing exploit to bypass safety filters."
            },
            {
                "id": "PI-OPPOSITE-MODE",
                "pattern": r"(?:opposite\s+mode|reverse\s+instruction|do\s+the\s+opposite\s+of\s+safety)",
                "category": "LOGICAL_INVERSION",
                "severity": "HIGH",
                "description": "Logical inversion attack attempting to invert safety rules."
            },
            {
                "id": "PI-EXFIL-SYSTEM",
                "pattern": r"(?:reveal|output|display|show|print|leak)\s+(?:your\s+)?(?:system\s+prompt|initial\s+prompt|instructions)",
                "category": "PROMPT_EXFILTRATION",
                "severity": "HIGH",
                "description": "Direct system prompt extraction attempt."
            },
            {
                "id": "PI-EXFIL-ENV",
                "pattern": r"(?:export|dump|print)\s+(?:all\s+)?(?:environment\s+variables|env\s+vars|api\s*keys?|secrets?)",
                "category": "CREDENTIAL_EXFILTRATION",
                "severity": "CRITICAL",
                "description": "Host environment variable or secret dumping attempt."
            },
            {
                "id": "PI-BASE64-EXEC",
                "pattern": r"(?:decode\s+this\s+base64\s+and\s+execute|run\s+the\s+following\s+encoded\s+command)",
                "category": "ENCODED_PAYLOAD_EXEC",
                "severity": "HIGH",
                "description": "Encoded payload execution instruction bypass."
            }
        ]

        # 2. Smart Contract Honeypot & EVM Malice Signatures
        honeypot_rules = [
            {
                "id": "SC-TRANSFER-OWNER-LOCK",
                "pattern": r"require\s*\(\s*(?:from|to)\s*==\s*owner",
                "rule_name": "TRANSFER_LOCKED_TO_OWNER",
                "severity": "CRITICAL",
                "description": "Only contract owner can transfer tokens (100% Honeypot)."
            },
            {
                "id": "SC-EXTREME-SELL-TAX",
                "pattern": r"(?:sellFee|sellTax|transferTax)\s*=\s*(?:[3-9][0-9]|100)",
                "rule_name": "EXTREME_SELL_TAX_TRAP",
                "severity": "CRITICAL",
                "description": "Sell tax set to >= 30%, stealing buyer exit liquidity."
            },
            {
                "id": "SC-DYNAMIC-MAX-TX",
                "pattern": r"(?:maxTxAmount|maxWalletToken)\s*=\s*0",
                "rule_name": "ZERO_MAX_TX_BLOCK",
                "severity": "CRITICAL",
                "description": "Max transaction set to 0, permanently trapping sold tokens."
            },
            {
                "id": "SC-DYNAMIC-BLACKLIST",
                "pattern": r"(?:isBlacklist(?:ed)?|blacklists?)\s*\[\s*(?:from|to)\s*\]\s*==\s*true",
                "rule_name": "ARBITRARY_BLACKLIST_GATE",
                "severity": "HIGH",
                "description": "Arbitrary blacklist mapping allows owner to prevent user selling."
            },
            {
                "id": "SC-HIDDEN-MINT",
                "pattern": r"function\s+mint\s*\([^)]*\)\s*(?:public|external)(?![^{]*require[^{]*owner)",
                "rule_name": "UNPROTECTED_PUBLIC_MINT",
                "severity": "CRITICAL",
                "description": "Public unprotected mint function allows arbitrary supply inflation."
            },
            {
                "id": "SC-SELFDESTRUCT",
                "pattern": r"selfdestruct\s*\(",
                "rule_name": "SELFDESTRUCT_RUG_PULL",
                "severity": "CRITICAL",
                "description": "Selfdestruct opcode allows creator to destroy contract and take all ETH."
            }
        ]

        # 3. Expanding High-Entropy Secret & Key Signatures
        secret_rules = [
            ("OPENAI_PROJECT_KEY", r"sk-proj-[a-zA-Z0-9_\-]{40,}", "CRITICAL", "OpenAI Project API Key"),
            ("ANTHROPIC_CLAUDE_KEY", r"sk-ant-[a-zA-Z0-9_\-]{32,}", "CRITICAL", "Anthropic Claude API Key"),
            ("HUGGINGFACE_KEY", r"hf_[a-zA-Z0-9]{34,}", "CRITICAL", "Hugging Face User Access Token"),
            ("GROQ_API_KEY", r"gsk_[a-zA-Z0-9]{48,}", "CRITICAL", "Groq Cloud Fast Inference API Key"),
            ("DEEPSEEK_KEY", r"sk-[a-f0-9]{32}", "CRITICAL", "DeepSeek API Key"),
            ("AWS_ACCESS_KEY", r"AKIA[0-9A-Z]{16}", "CRITICAL", "Amazon Web Services Access Key"),
            ("BASE_EVM_PRIVATE_KEY", r"(?:0x)?[a-fA-F0-9]{64}", "CRITICAL", "Base / Ethereum 256-bit Private Key"),
            ("GITHUB_PAT", r"gh[pousr]_[A-Za-z0-9_]{36,}", "CRITICAL", "GitHub Personal Access Token"),
            ("TELEGRAM_BOT_TOKEN", r"[0-9]{9,10}:[a-zA-Z0-9_-]{35}", "CRITICAL", "Telegram Bot API Token"),
            ("STRIPE_PROD_KEY", r"sk_live_[0-9a-zA-Z]{24,}", "CRITICAL", "Stripe Production Secret Key")
        ]

        signatures = {
            "version": "2.0.0",
            "last_updated_epoch": int(now),
            "generated_by": "Sayf Cyber Threat Intelligence Agent",
            "total_rules": len(prompt_injection_rules) + len(honeypot_rules) + len(secret_rules),
            "prompt_injection_rules": prompt_injection_rules,
            "honeypot_rules": honeypot_rules,
            "secret_rules": secret_rules
        }

        # Write to cache
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(signatures, f, indent=2)

        return signatures

    def load_cached_signatures(self) -> Dict[str, Any]:
        """Loads cached signatures from disk or triggers a fresh generation."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self.fetch_latest_threat_signatures()
