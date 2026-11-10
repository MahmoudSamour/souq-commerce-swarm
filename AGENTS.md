# Project SOUQ (السوق) // Swarm Directives & Governance Rules

## 1. Zero-Friction Agent-to-Agent (A2A) Commerce Protocol
- **Native HTTP 402 ("x402") Standard**: All agent tool endpoints MUST issue standardized HTTP 402 Payment Required challenges when called without payment.
- **Base USDC Settlement**: The official settlement rail for agent micropayments is **USDC on Base (Chain ID: 8453)** to ensure sub-cent transaction fees and sub-second finality.
- **Zero Human Gatekeeping**: Never require client agents to fill out captchas, create manual user accounts, or solve web challenges.

## 2. Mandatory Cryptographic Receipt & Anti-Replay Nullifier Rule
- **Anti-Replay Nullification**: `X402PaymentGateway` MUST check `CryptoReceiptEngine.is_tx_already_redeemed()` before executing any paid service. Any reused transaction hash is rejected immediately with a `Payment Nullified` error.
- **Cryptographic Audit Signatures**: Every on-chain settlement MUST generate a deterministic SHA-256 receipt signature and write an individual JSON audit receipt to `data/receipts/`.
- **IRS & Koinly Compliance**: All earnings must be instantly exportable to standard Koinly CSV (`./souq.sh tax-report`) with complete cost-basis and transaction hashes for zero-headache tax filing.

## 3. Mandatory A2A Negotiation & Workflow Telemetry Rule
- **Every Interaction Recorded**: Every tool challenge, price quote, agent user-agent, negotiation latency, and settlement outcome MUST be recorded into `data/souq_treasury_lake.duckdb` via `NegotiationTracker`.
- **Adaptive Pricing Loop**: The swarm monitors conversion rates and consecutive rejections to dynamically optimize prices without human intervention.

## 4. Universal Legal & Safe Harbor Directives (Amin Auditor)
- **CFAA Safe Harbor (*hiQ v. LinkedIn*)**: The swarm strictly queries open, unauthenticated public endpoints. Never bypass authentication boundaries or login walls.
- **DMCA §1201 Safe Harbor**: Never attempt to bypass CAPTCHAs, bot-blockers, or Cloudflare Turnstile challenges. If blocked, mark as `RESTRICTED` and use official APIs.
- **Feist Copyright Doctrine**: Only monetize raw mathematical facts, market depth metrics, and clean-room synthesized code templates. Never scrape or resell copyrighted creative text or imagery.
- **Hard Zero-PII Policy**: Strictly forbidden from collecting or storing Personally Identifiable Information (names, private emails, phone numbers).

## 5. Merchant of Record (MoR) Fiat Protection
- **Polar.sh as Legal MoR**: All fiat transactions (data lakes and code templates) are processed through Polar.sh to ensure 100% of global VAT/GST and sales taxes are collected and remitted automatically.
