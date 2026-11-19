#!/usr/bin/env node

const readline = require("readline");

let VERSION = "0.3.0";
try {
  VERSION = require("../package.json").version || VERSION;
} catch {
  // Fallback when executed outside package directory
}

const ENDPOINT = (process.env.SOUQ_ENDPOINT || "https://written-emera-arapython-bf7436a4.apps.mistral.run").replace(/\/+$/, "");
const DEFAULT_RECIPIENT = "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF";
const FETCH_TIMEOUT_MS = 30000;
const consumedEnvPaymentTxs = new Set();

const TOOLS_METADATA = [
  {
    name: "souq_account_status",
    description: "Free discovery & balance check: inspects current prepaid SOUQ_API_KEY credits, Base USDC payment details, and tool pricing.",
    inputSchema: {
      type: "object",
      properties: {}
    }
  },
  {
    name: "token_context_compressor",
    description: "Compresses bloated HTML, JSON, code, logs, or markdown by 60-95% to save prompt tokens ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        raw_content: { type: "string", description: "The raw HTML, JSON, code, log, or markdown text to compress" },
        max_compression: { type: "boolean", default: true, description: "Enable aggressive pruning, table compaction, and log deduplication" },
        mode: { type: "string", enum: ["auto", "html", "json", "code", "log", "logs", "markdown", "prose"], default: "auto", description: "Optional compression profile hint" },
        target_ratio: { type: "number", description: "Optional target compression ratio in (0.05, 0.95)" }
      },
      required: ["raw_content"]
    }
  },
  {
    name: "ast_structural_slicer",
    description: "Surgically extracts a single AST function or class from Python source code ($0.02 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        source_code: { type: "string", description: "The Python source code" },
        target_symbol: { type: "string", description: "The function or class name to slice" }
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
    description: "Scans Spot vs Perpetual Futures basis spreads and annualized delta-neutral funding APR ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string", default: "BTC/USDT", description: "Trading pair symbol" }
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
    description: "Compressed API schemas and snippets for major developer platforms (openai, anthropic, stripe, base_evm, fastmcp, mcp, duckdb) ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        ecosystem: {
          type: "string",
          enum: ["openai", "anthropic", "stripe", "base_evm", "fastmcp", "mcp", "duckdb"],
          default: "openai"
        }
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
        asset: { type: "string", default: "BTC", description: "Target crypto asset (BTC, ETH, SOL)" },
        limit: { type: "integer", default: 5, description: "Maximum number of arbitrage opportunities to return" }
      }
    }
  },
  {
    name: "ast_security_scanner",
    description: "Python AST code security linter (compatibility alias for deep_ast_vulnerability_auditor) ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        source_code: { type: "string", description: "Python source code to audit for vulnerabilities" }
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
        data: { type: "object", description: "The JSON object to validate" },
        schema: { type: "object", description: "Target field-to-type validation mapping" }
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
    description: "Audits Solidity contracts OR live Base 0x contract addresses for honeypots, transfer blacklists, and reentrancy ($0.03 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        source_code: { type: "string", default: "", description: "Solidity source code" },
        contract_address: { type: "string", description: "Optional Base 0x contract address for live bytecode & Blockscout source inspection" },
        token_symbol: { type: "string", default: "TKN" }
      }
    }
  },
  {
    name: "secret_leak_scanner",
    description: "High-entropy credential scanner detecting leaked AWS, OpenAI, Anthropic, and Base private keys ($0.01 USDC).",
    inputSchema: {
      type: "object",
      properties: {
        content: { type: "string", description: "File or text content to scan for secret keys" },
        entropy_threshold: { type: "number", default: 4.2, description: "Shannon entropy threshold for unknown secret detection" }
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
        target_url: { type: "string", description: "HTTP endpoint URL to audit" },
        headers_to_check: {
          type: "object",
          additionalProperties: { type: "string" },
          description: "Optional HTTP response headers map to audit offline"
        }
      },
      required: ["target_url"]
    }
  }
];

function summarizeNonJsonBody(status, text) {
  const trimmed = (text || "").trim();
  if (!trimmed) {
    return `Empty response body (HTTP ${status})`;
  }
  const titleMatch = trimmed.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  if (titleMatch && titleMatch[1]) {
    const title = titleMatch[1].replace(/\s+/g, " ").trim();
    if (title) return `HTTP ${status}: ${title}`;
  }
  const plain = trimmed.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  return `Non-JSON response (HTTP ${status}): ${plain.slice(0, 200)}`;
}

async function fetchJson(url, options = {}) {
  const resp = await fetch(url, {
    ...options,
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS)
  });
  const text = await resp.text();
  let data = null;
  let parseError = null;

  if (text && text.trim()) {
    try {
      data = JSON.parse(text);
    } catch (err) {
      parseError = err;
    }
  }

  if (!resp.ok) {
    const parsedErr = data && typeof data === "object" ? (data.message || data.error) : null;
    const errorMsg = parsedErr || summarizeNonJsonBody(resp.status, text);
    return {
      ok: false,
      status: resp.status,
      headers: resp.headers,
      data,
      text,
      error: errorMsg
    };
  }

  if (parseError) {
    return {
      ok: false,
      status: resp.status,
      headers: resp.headers,
      data: null,
      text,
      error: summarizeNonJsonBody(resp.status, text)
    };
  }

  return {
    ok: true,
    status: resp.status,
    headers: resp.headers,
    data: data !== null ? data : {},
    text,
    error: null
  };
}

function resolveApiKey(overrideKey) {
  return (overrideKey || process.env.SOUQ_API_KEY || "").trim();
}

async function getAccountStatus(apiKeyOverride = "") {
  const apiKey = resolveApiKey(apiKeyOverride);
  if (apiKey) {
    const res = await fetchJson(`${ENDPOINT}/api/credits/balance`, {
      headers: { "X-API-Key": apiKey, "User-Agent": `souq-mcp-node/${VERSION}` }
    });
    if (!res.ok || !res.data || typeof res.data !== "object") {
      return {
        authenticated: false,
        status: res.status,
        endpoint: ENDPOINT,
        topup_url: `${ENDPOINT}/#topup`,
        error: res.error || `HTTP ${res.status}`
      };
    }
    return { authenticated: true, status: res.status, endpoint: ENDPOINT, ...res.data };
  }

  const res = await fetchJson(`${ENDPOINT}/api/catalog`, {
    headers: { "User-Agent": `souq-mcp-node/${VERSION}` }
  });
  if (!res.ok || !res.data || typeof res.data !== "object") {
    return {
      authenticated: false,
      status: res.status,
      endpoint: ENDPOINT,
      topup_url: `${ENDPOINT}/#topup`,
      error: res.error || `HTTP ${res.status}`
    };
  }

  return {
    authenticated: false,
    endpoint: ENDPOINT,
    recipient_wallet: res.data.recipient_wallet,
    topup_url: `${ENDPOINT}/#topup`,
    topup_endpoint: `${ENDPOINT}/api/credits/topup`,
    message: `Set SOUQ_API_KEY in MCP env for prepaid unlimited micro-calls (fund at ${ENDPOINT}/#topup), or evaluate 1 free call/24h per IP.`,
    tools_count: Array.isArray(res.data.tools) ? res.data.tools.length : 16
  };
}

async function listRemoteTools() {
  const res = await fetchJson(`${ENDPOINT}/.well-known/mcp.json`, {
    headers: { "User-Agent": `souq-mcp-node/${VERSION}` }
  });
  if (!res.ok) {
    throw new Error(res.error || `HTTP ${res.status}`);
  }
  return res.data;
}

async function callRemoteTool(toolName, args = {}, options = {}) {
  if (toolName === "souq_account_status") {
    return await getAccountStatus(options.apiKey);
  }

  const url = `${ENDPOINT}/api/tools/call`;
  const payload = { tool: toolName, ...args };
  const headers = {
    "Content-Type": "application/json",
    "User-Agent": `souq-mcp-node/${VERSION}`
  };
  const apiKey = resolveApiKey(options.apiKey);
  if (apiKey) headers["X-API-Key"] = apiKey;

  const envTx = (process.env.SOUQ_PAYMENT_TX || "").trim();
  let skippedConsumedEnvTx = false;
  let sentEnvTxThisCall = false;
  if (envTx) {
    if (consumedEnvPaymentTxs.has(envTx)) {
      skippedConsumedEnvTx = true;
      process.stderr.write(
        `[souq-mcp] Note: static env SOUQ_PAYMENT_TX was already attempted/consumed in this process and skipped. ` +
        `Pass a fresh tx hash or configure SOUQ_API_KEY (fund at ${ENDPOINT}/#topup).\n`
      );
    } else {
      headers["X-Payment-Tx"] = envTx;
      consumedEnvPaymentTxs.add(envTx);
      sentEnvTxThisCall = true;
    }
  }

  const res = await fetchJson(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    if (res.status === 402) {
      const body = (res.data && typeof res.data === "object") ? res.data : {};
      const details = body.payment_details || {};
      const recipient = details.recipient_address || body.recipient || body.x402_recipient || DEFAULT_RECIPIENT;
      const amount = details.amount || (res.headers && res.headers.get("x-souq-price-usdc")) || "0.02";
      const consumedNote = skippedConsumedEnvTx
        ? " Note: static env SOUQ_PAYMENT_TX was already attempted/consumed; pass a fresh tx or set SOUQ_API_KEY."
        : "";
      throw new Error(
        `SOUQ HTTP 402 Payment Required (${amount} USDC on Base -> ${recipient}). ` +
        `Fund a prepaid key once at ${ENDPOINT}/#topup and set env SOUQ_API_KEY, ` +
        `or pass a fresh Base USDC tx hash via SOUQ_PAYMENT_TX.${consumedNote}`
      );
    }

    const extraDetails = (res.data && typeof res.data === "object" && res.data.details)
      ? ` (${JSON.stringify(res.data.details)})`
      : "";
    const txNote = (sentEnvTxThisCall && res.status === 400)
      ? ` Static SOUQ_PAYMENT_TX was marked consumed and will not be retried; pass a fresh tx or set SOUQ_API_KEY (${ENDPOINT}/#topup).`
      : "";
    throw new Error(`${res.error || `HTTP ${res.status}`}${extraDetails}${txNote}`);
  }

  return res.data;
}

function sendJsonRpc(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

async function handleMessage(msg) {
  if (!msg || typeof msg !== "object") {
    return {
      jsonrpc: "2.0",
      id: null,
      error: { code: -32600, message: "Invalid Request" }
    };
  }

  const { id, method } = msg;
  const params = (msg.params && typeof msg.params === "object") ? msg.params : {};

  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: {
          name: "souq-mcp",
          version: VERSION
        }
      }
    };
  }

  if (method === "notifications/initialized" || (typeof method === "string" && method.startsWith("notifications/") && (id === undefined || id === null))) {
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
    const toolName = params.name || "";
    const args = (params.arguments && typeof params.arguments === "object" && !Array.isArray(params.arguments))
      ? params.arguments
      : {};
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
        result: {
          isError: true,
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

function startMcpServer() {
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
}

function formatHelp() {
  return [
    `souq-mcp v${VERSION} — SOUQ Autonomous Commerce Swarm MCP Server & CLI`,
    "",
    "Usage:",
    "  souq-mcp                          Start MCP JSON-RPC 2.0 stdio server (default)",
    "  souq-mcp serve                    Start MCP JSON-RPC 2.0 stdio server",
    "  souq-mcp status [--api-key KEY]   Inspect SOUQ_API_KEY balance or public Base USDC payment rails",
    "  souq-mcp list                     List live SOUQ tools from /.well-known/mcp.json",
    "  souq-mcp call <tool> [json]       Invoke a SOUQ tool directly (supports --args JSON and --api-key KEY)",
    "  souq-mcp --help                   Show this help message",
    "  souq-mcp --version                Show version",
    "",
    "Environment:",
    `  SOUQ_ENDPOINT     Edge endpoint URL (default: ${ENDPOINT})`,
    `  SOUQ_API_KEY      Prepaid X-API-Key minted at ${ENDPOINT}/#topup`,
    "  SOUQ_PAYMENT_TX   Single-use Base USDC tx hash (attempted once per process)",
    ""
  ].join("\n");
}

function parseCliArgs(argv) {
  const args = [...argv];
  if (args.length === 0) {
    return { command: "serve" };
  }

  const first = args[0];
  if (first === "--help" || first === "-h" || first === "help") {
    return { command: "help" };
  }
  if (first === "--version" || first === "-v") {
    return { command: "version" };
  }
  if (first === "serve") {
    return { command: "serve" };
  }
  if (first === "list") {
    return { command: "list" };
  }

  if (first === "status" || first === "call") {
    let apiKey = "";
    let argsFlag = null;
    const positionals = [];

    for (let i = 1; i < args.length; i++) {
      const token = args[i];
      if (token === "--help" || token === "-h") {
        return { command: "help" };
      } else if (token === "--api-key") {
        if (i + 1 >= args.length) throw new Error("Missing value for --api-key");
        apiKey = args[++i];
      } else if (token.startsWith("--api-key=")) {
        apiKey = token.slice("--api-key=".length);
      } else if (first === "call" && token === "--args") {
        if (i + 1 >= args.length) throw new Error("Missing value for --args");
        argsFlag = args[++i];
      } else if (first === "call" && token.startsWith("--args=")) {
        argsFlag = token.slice("--args=".length);
      } else if (token.startsWith("-")) {
        throw new Error(`Unknown option: ${token}`);
      } else {
        positionals.push(token);
      }
    }

    if (first === "status") {
      if (positionals.length > 0) {
        throw new Error(`Unexpected argument for status: ${positionals[0]}`);
      }
      return { command: "status", apiKey };
    }

    const toolName = positionals[0];
    if (!toolName) {
      throw new Error("Missing <tool> argument. Usage: souq-mcp call <tool> [json]");
    }
    if (positionals.length > 2) {
      throw new Error(`Unexpected extra arguments: ${positionals.slice(2).join(" ")}`);
    }
    const rawJson = argsFlag !== null ? argsFlag : (positionals[1] !== undefined ? positionals[1] : "{}");
    let parsedArgs;
    try {
      parsedArgs = JSON.parse(rawJson);
    } catch (err) {
      throw new Error(`Invalid JSON args: ${err.message}`);
    }
    if (!parsedArgs || typeof parsedArgs !== "object" || Array.isArray(parsedArgs)) {
      throw new Error("Tool JSON args must be an object");
    }
    return { command: "call", toolName, parsedArgs, apiKey };
  }

  throw new Error(`Unknown command or flag: ${first}`);
}

async function main() {
  let parsed;
  try {
    parsed = parseCliArgs(process.argv.slice(2));
  } catch (err) {
    process.stderr.write(`Error: ${err.message}\n\n${formatHelp()}`);
    process.exit(1);
    return;
  }

  if (parsed.command === "help") {
    process.stdout.write(formatHelp());
    return;
  }
  if (parsed.command === "version") {
    process.stdout.write(`${VERSION}\n`);
    return;
  }
  if (parsed.command === "serve") {
    startMcpServer();
    return;
  }
  if (parsed.command === "status") {
    try {
      const status = await getAccountStatus(parsed.apiKey);
      process.stdout.write(JSON.stringify(status, null, 2) + "\n");
    } catch (err) {
      process.stderr.write(`Failed to check status: ${err.message}\n`);
      process.exit(1);
    }
    return;
  }
  if (parsed.command === "list") {
    try {
      const manifest = await listRemoteTools();
      process.stdout.write(JSON.stringify(manifest, null, 2) + "\n");
    } catch (err) {
      process.stderr.write(`Failed to fetch tool listing: ${err.message}\n`);
      process.exit(1);
    }
    return;
  }
  if (parsed.command === "call") {
    try {
      const result = await callRemoteTool(parsed.toolName, parsed.parsedArgs, { apiKey: parsed.apiKey });
      process.stdout.write(JSON.stringify(result, null, 2) + "\n");
    } catch (err) {
      process.stderr.write(`Error: ${err.message}\n`);
      process.exit(1);
    }
  }
}

if (require.main === module) {
  main().catch((err) => {
    process.stderr.write(`Fatal error: ${err.message}\n`);
    process.exit(1);
  });
}

module.exports = {
  ENDPOINT,
  TOOLS_METADATA,
  consumedEnvPaymentTxs,
  fetchJson,
  getAccountStatus,
  listRemoteTools,
  callRemoteTool,
  handleMessage,
  parseCliArgs
};
