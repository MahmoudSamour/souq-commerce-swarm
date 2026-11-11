#!/usr/bin/env node

const readline = require("readline");

const ENDPOINT = process.env.SOUQ_ENDPOINT || "https://written-emera-arapython-bf7436a4.apps.mistral.run";

const TOOLS_METADATA = [
  {
    name: "token_context_compressor",
    description: "Slashes LLM context bloat by 80-95% to save prompt tokens ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        raw_content: { type: "string", description: "The raw text, markdown, or code to compress" }
      },
      required: ["raw_content"]
    }
  },
  {
    name: "ast_structural_slicer",
    description: "Surgically slices targeted AST functions from source code ($0.02 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        source_code: { type: "string", description: "Source code" },
        target_symbol: { type: "string", description: "Function or class name" }
      },
      required: ["source_code", "target_symbol"]
    }
  },
  {
    name: "quant_microstructure_radar",
    description: "Real-time Binance order book depth, Order Book Imbalance (OBI), and liquidation risk ($0.02 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string", default: "BTC/USDT", description: "Trading pair symbol" }
      }
    }
  },
  {
    name: "cross_exchange_arbitrage_scanner",
    description: "Scans Spot vs Perpetual Futures basis spreads and calculates annualized delta-neutral funding APR ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string", default: "BTC/USDT" }
      }
    }
  },
  {
    name: "orderbook_slippage_simulator",
    description: "Walks live Binance order book depth (100 levels) to simulate VWAP, slippage bps, and price impact ($0.02 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string", default: "BTC/USDT" },
        side: { type: "string", enum: ["BUY", "SELL"], default: "BUY" },
        trade_size_usd: { type: "number", default: 10000.0 }
      }
    }
  },
  {
    name: "smart_money_whale_flow_radar",
    description: "Aggregates live whale block trades (> $50k) and computes Whale Accumulation Index ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string", default: "BTC/USDT" },
        block_threshold_usd: { type: "number", default: 50000.0 }
      }
    }
  },
  {
    name: "dev_api_cheatsheet_vault",
    description: "Compressed API schemas and snippets for major developer platforms (openai, anthropic, stripe, base_evm, fastmcp, duckdb) ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: { type: "string", default: "openai" }
      }
    }
  },
  {
    name: "daily_tech_ai_trends_radar",
    description: "Daily intelligence snapshot of trending GitHub AI repos, HackerNews, and arXiv ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        force_refresh: { type: "boolean", default: false }
      }
    }
  },
  {
    name: "prediction_market_arbitrage_radar",
    description: "Cross-market probability discrepancy engine between Polymarket consensus and spot/volatility Black-Scholes pricing ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        asset: { type: "string", default: "BTC", description: "Crypto asset (BTC, ETH, SOL)" }
      }
    }
  },
  {
    name: "ast_security_scanner",
    description: "Static AST code security linter for Python and Solidity ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        source_code: { type: "string", description: "Source code to audit" }
      },
      required: ["source_code"]
    }
  },
  {
    name: "synthetic_schema_verifier",
    description: "Validates JSON objects against standard schema constraints ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        data: { type: "object" },
        schema: { type: "object" }
      },
      required: ["data", "schema"]
    }
  },
  {
    name: "prompt_injection_firewall",
    description: "Adversarial prompt injection, DAN jailbreak, and system prompt exfiltration detector ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string", description: "Input text or prompt to analyze" },
        strict_mode: { type: "boolean", default: false }
      },
      required: ["text"]
    }
  },
  {
    name: "smart_contract_honeypot_radar",
    description: "Audits Solidity contracts for 99% sell taxes, transfer blacklists, and reentrancy traps ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        source_code: { type: "string", description: "Solidity source code" },
        token_symbol: { type: "string", default: "TKN" }
      },
      required: ["source_code"]
    }
  },
  {
    name: "secret_leak_scanner",
    description: "High-entropy credential scanner detecting leaked AWS, OpenAI, Anthropic, and Base private keys ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        content: { type: "string", description: "File or text content to scan for secret keys" }
      },
      required: ["content"]
    }
  },
  {
    name: "deep_ast_vulnerability_auditor",
    description: "Deep AST code vulnerability auditor for Python detecting SQLi, insecure deserialization, and RCE ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        source_code: { type: "string", description: "Python source code" }
      },
      required: ["source_code"]
    }
  },
  {
    name: "api_attack_surface_scanner",
    description: "API attack surface and defensive security header linter ($0.02 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        target_url: { type: "string", description: "HTTP endpoint URL to audit" }
      },
      required: ["target_url"]
    }
  }
];

async function callRemoteTool(toolName, args) {
  const url = `${ENDPOINT}/api/tools/call`;
  const payload = { tool: toolName, ...args };
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "User-Agent": "souq-mcp-node/0.1.0"
    },
    body: JSON.stringify(payload)
  });

  const body = await resp.json();
  if (!resp.ok) {
    if (resp.status === 402) {
      throw new Error(`SOUQ 402: Free daily call limit reached. Micro-payment required to recipient: ${body.recipient || '0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF'}`);
    }
    throw new Error(body.error || `HTTP ${resp.status}`);
  }
  return body;
}

function sendJsonRpc(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

async function handleMessage(msg) {
  const { id, method, params } = msg;

  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: {
          name: "souq-mcp",
          version: "0.1.0"
        }
      }
    };
  }

  if (method === "notifications/initialized") {
    return null;
  }

  if (method === "tools/list") {
    return {
      jsonrpc: "2.0",
      id,
      result: { tools: TOOLS_METADATA }
    };
  }

  if (method === "tools/call") {
    const toolName = params ? params.name : "";
    const args = (params && params.arguments) ? params.arguments : {};
    try {
      const toolRes = await callRemoteTool(toolName, args);
      return {
        jsonrpc: "2.0",
        id,
        result: {
          content: [
            { type: "text", text: JSON.stringify(toolRes, null, 2) }
          ]
        }
      };
    } catch (err) {
      return {
        jsonrpc: "2.0",
        id,
        isError: true,
        result: {
          content: [
            { type: "text", text: `Error calling ${toolName}: ${err.message}` }
          ]
        }
      };
    }
  }

  if (method === "ping") {
    return { jsonrpc: "2.0", id, result: {} };
  }

  return {
    jsonrpc: "2.0",
    id,
    error: { code: -32601, message: `Method '${method}' not found` }
  };
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on("line", async (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;
  try {
    const msg = JSON.parse(trimmed);
    const reply = await handleMessage(msg);
    if (reply) sendJsonRpc(reply);
  } catch (err) {
    sendJsonRpc({
      jsonrpc: "2.0",
      id: null,
      error: { code: -32603, message: err.message }
    });
  }
});
