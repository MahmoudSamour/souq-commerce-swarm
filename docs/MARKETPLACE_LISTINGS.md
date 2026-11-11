# SOUQ Marketplace & Agent Directory Guide

This document outlines the registration metadata, payloads, and step-by-step listing verification for SOUQ across major AI Agent directories.

---

## 1. Directory Matrix

| Marketplace / Directory | Primary Interface | Protocol / Manifest | Status |
| :--- | :--- | :--- | :--- |
| **Smithery.ai** | `npx -y @smithery/cli run souq-mcp` | `smithery.yaml` | Ready |
| **Glama.ai (mcp.directory)** | Web Registry & Search | `/.well-known/mcp.json` | Published & Verified |
| **MCP.so** | MCP Catalog Indexer | `/.well-known/mcp.json` | Published & Verified |
| **A2A (Agent-to-Agent)** | Decentralized Agent Discovery | `/.well-known/agent-card.json` | Published & Verified |
| **IndexNow (Bing/Yandex/Seznam)** | Web/Agent Search Crawler Ping | `agents/distribution/munadi_herald.py` | Active Broadcast |
| **PyPI (`souq-mcp`)** | `pip install souq-mcp` / `uvx souq-mcp` | `clients/python/pyproject.toml` | Built & Ready for Publish |
| **npm (`souq-mcp`)** | `npx souq-mcp` | `clients/npm/package.json` | Built & Ready for Publish |

---

## 2. Listing Details

### Smithery (`smithery.yaml`)
- **Package**: `souq-mcp`
- **Command**: `npx -y souq-mcp`
- **Description**: Sub-cent algorithmic MCP tools on Base L2: Polymarket arbitrage radar, 90% prompt token compression, Binance microstructure, and smart money whale flows.
- **Settlement**: Free evaluation tier (1 call/day) + x402 on Base USDC.

### Glama & MCP.so (`.well-known/mcp.json`)
- **Discovery Endpoint**: `https://written-emera-arapython-bf7436a4.apps.mistral.run/.well-known/mcp.json`
- **Specification Version**: MCP 2024-11-05
- **Tool Inventory**: 11 active micro-services.

### A2A Protocol (`.well-known/agent-card.json`)
- **Discovery Endpoint**: `https://written-emera-arapython-bf7436a4.apps.mistral.run/.well-known/agent-card.json`
- **Schema**: `https://a2a-protocol.org/schemas/agent-card.json`

---

## 3. One-Click Publishing to PyPI and npm

To release the public clients to global package managers when desired:

### Publish to PyPI:
```bash
cd /home/mm/Souq/souq-commerce-swarm/clients/python
../../.venv/bin/python -m build
twine upload dist/*
```

### Publish to npm:
```bash
cd /home/mm/Souq/souq-commerce-swarm/clients/npm
npm publish --access public
```
