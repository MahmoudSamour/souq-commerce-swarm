"""
SOUQ // FastMCP Server with Native HTTP 402 Settlement Middleware
Runs the live FastMCP tool endpoints with automated x402 payment verification,
Binance live feeds, and negotiation logging.
"""

import os
import sys
import argparse
from typing import Dict, Any, Optional

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastmcp import FastMCP
from agents.production.mcp_tool_builder import (
    MarketMicrostructureEngine,
    ASTSecurityScanner,
    SyntheticSchemaVerifier,
    CrossExchangeArbitrageScanner,
    OrderBookSlippageSimulator,
    SmartMoneyWhaleRadar,
)
from agents.production.token_compressor import TokenContextCompressor, CodeASTSlicer
from agents.treasury.x402_gateway import X402PaymentGateway

# Initialize FastMCP Server
mcp = FastMCP("souq-commerce-server")

# Engines
microstructure_engine = MarketMicrostructureEngine()
security_scanner = ASTSecurityScanner()
schema_verifier = SyntheticSchemaVerifier()
arbitrage_scanner = CrossExchangeArbitrageScanner()
slippage_simulator = OrderBookSlippageSimulator()
whale_radar = SmartMoneyWhaleRadar()
token_compressor = TokenContextCompressor()
ast_slicer = CodeASTSlicer()
payment_gateway = X402PaymentGateway()


def _is_sim_allowed(tx_hash: str) -> bool:
    allow_sim = os.getenv("SOUQ_ALLOW_TEST_SIMULATION", "false").lower() == "true"
    return allow_sim and (tx_hash.startswith("0x_simulated_") or tx_hash.startswith("0x_test_"))


@mcp.tool()
def quant_microstructure_radar(
    symbol: str = "BTC/USDT",
    payment_tx_hash: Optional[str] = None,
    client_id: str = "agent-client-default"
) -> Dict[str, Any]:
    """
    Computes real-time Order Book Imbalance (OBI), liquidation cascade probability,
    and market microstructure regime across Binance public order book ticks.
    Cost: 0.02 USDC on Base. Requires payment_tx_hash for verified execution.
    """
    price_usdc = 0.02
    tool_name = "quant_microstructure_radar"

    if not payment_tx_hash:
        return payment_gateway.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price_usdc,
            client_agent_id=client_id
        )

    settled, settlement_info = payment_gateway.verify_payment_and_settle(
        tx_hash=payment_tx_hash,
        expected_price_usdc=price_usdc,
        tool_name=tool_name,
        payload_data={"symbol": symbol},
        client_agent_id=client_id,
        simulate_test=_is_sim_allowed(payment_tx_hash)
    )

    if not settled:
        return {"error": "Payment Verification Failed", "details": settlement_info}

    result = microstructure_engine.get_microstructure_metrics(symbol=symbol)
    result["settlement_receipt"] = settlement_info
    return result


@mcp.tool()
def cross_exchange_arbitrage_scanner(
    symbol: str = "BTC/USDT",
    payment_tx_hash: Optional[str] = None,
    client_id: str = "agent-client-default"
) -> Dict[str, Any]:
    """
    Scans Spot vs. Perpetual Futures basis spreads and calculates annualized
    Delta-Neutral Funding Rate APR across major crypto pairs.
    Cost: 0.03 USDC on Base. Requires payment_tx_hash.
    """
    price_usdc = 0.03
    tool_name = "cross_exchange_arbitrage_scanner"

    if not payment_tx_hash:
        return payment_gateway.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price_usdc,
            client_agent_id=client_id
        )

    settled, settlement_info = payment_gateway.verify_payment_and_settle(
        tx_hash=payment_tx_hash,
        expected_price_usdc=price_usdc,
        tool_name=tool_name,
        payload_data={"symbol": symbol},
        client_agent_id=client_id,
        simulate_test=_is_sim_allowed(payment_tx_hash)
    )

    if not settled:
        return {"error": "Payment Verification Failed", "details": settlement_info}

    result = arbitrage_scanner.scan_arbitrage_and_funding(symbol=symbol)
    result["settlement_receipt"] = settlement_info
    return result


@mcp.tool()
def orderbook_slippage_simulator(
    symbol: str = "BTC/USDT",
    side: str = "BUY",
    trade_size_usd: float = 10000.0,
    payment_tx_hash: Optional[str] = None,
    client_id: str = "agent-client-default"
) -> Dict[str, Any]:
    """
    Simulates order-book execution depth on live Binance order book.
    Calculates expected VWAP, price impact, and slippage in basis points (bps)
    before an agent executes a live trade.
    Cost: 0.02 USDC on Base. Requires payment_tx_hash.
    """
    price_usdc = 0.02
    tool_name = "orderbook_slippage_simulator"

    if not payment_tx_hash:
        return payment_gateway.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price_usdc,
            client_agent_id=client_id
        )

    settled, settlement_info = payment_gateway.verify_payment_and_settle(
        tx_hash=payment_tx_hash,
        expected_price_usdc=price_usdc,
        tool_name=tool_name,
        payload_data={"symbol": symbol, "side": side, "trade_size_usd": trade_size_usd},
        client_agent_id=client_id,
        simulate_test=_is_sim_allowed(payment_tx_hash)
    )

    if not settled:
        return {"error": "Payment Verification Failed", "details": settlement_info}

    result = slippage_simulator.simulate_slippage(symbol=symbol, side=side, trade_size_usd=trade_size_usd)
    result["settlement_receipt"] = settlement_info
    return result


@mcp.tool()
def smart_money_whale_flow_radar(
    symbol: str = "BTC/USDT",
    block_threshold_usd: float = 50000.0,
    payment_tx_hash: Optional[str] = None,
    client_id: str = "agent-client-default"
) -> Dict[str, Any]:
    """
    Scans live whale block trades (> $50k), calculates the Whale Accumulation Index,
    identifies Open Interest liquidation clusters, and detects institutional flow.
    Cost: 0.03 USDC on Base. Requires payment_tx_hash.
    """
    price_usdc = 0.03
    tool_name = "smart_money_whale_flow_radar"

    if not payment_tx_hash:
        return payment_gateway.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price_usdc,
            client_agent_id=client_id
        )

    settled, settlement_info = payment_gateway.verify_payment_and_settle(
        tx_hash=payment_tx_hash,
        expected_price_usdc=price_usdc,
        tool_name=tool_name,
        payload_data={"symbol": symbol, "block_threshold_usd": block_threshold_usd},
        client_agent_id=client_id,
        simulate_test=_is_sim_allowed(payment_tx_hash)
    )

    if not settled:
        return {"error": "Payment Verification Failed", "details": settlement_info}

    result = whale_radar.get_whale_flow_telemetry(symbol=symbol, block_threshold_usd=block_threshold_usd)
    result["settlement_receipt"] = settlement_info
    return result


@mcp.tool()
def ast_security_scanner(
    source_code: str,
    payment_tx_hash: Optional[str] = None,
    client_id: str = "agent-client-default"
) -> Dict[str, Any]:
    """
    Performs static AST security linting and detects dangerous execution patterns,
    eval injection, and shell vulnerabilities.
    Cost: 0.03 USDC on Base. Requires payment_tx_hash.
    """
    price_usdc = 0.03
    tool_name = "ast_security_scanner"

    if not payment_tx_hash:
        return payment_gateway.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price_usdc,
            client_agent_id=client_id
        )

    settled, settlement_info = payment_gateway.verify_payment_and_settle(
        tx_hash=payment_tx_hash,
        expected_price_usdc=price_usdc,
        tool_name=tool_name,
        payload_data={"code_len": len(source_code)},
        client_agent_id=client_id,
        simulate_test=_is_sim_allowed(payment_tx_hash)
    )

    if not settled:
        return {"error": "Payment Verification Failed", "details": settlement_info}

    result = security_scanner.scan_python_code(source_code=source_code)
    result["settlement_receipt"] = settlement_info
    return result


@mcp.tool()
def synthetic_schema_verifier(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    payment_tx_hash: Optional[str] = None,
    client_id: str = "agent-client-default"
) -> Dict[str, Any]:
    """
    Validates data structures against rigid schema constraints for LLM pipelines.
    Cost: 0.01 USDC on Base. Requires payment_tx_hash.
    """
    price_usdc = 0.01
    tool_name = "synthetic_schema_verifier"

    if not payment_tx_hash:
        return payment_gateway.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price_usdc,
            client_agent_id=client_id
        )

    settled, settlement_info = payment_gateway.verify_payment_and_settle(
        tx_hash=payment_tx_hash,
        expected_price_usdc=price_usdc,
        tool_name=tool_name,
        payload_data={"keys_checked": list(schema.keys())},
        client_agent_id=client_id,
        simulate_test=_is_sim_allowed(payment_tx_hash)
    )

    if not settled:
        return {"error": "Payment Verification Failed", "details": settlement_info}

    result = schema_verifier.verify_schema_conformity(data=data, schema=schema)
    result["settlement_receipt"] = settlement_info
    return result


@mcp.tool()
def token_context_compressor(
    raw_content: str,
    payment_tx_hash: Optional[str] = None,
    client_id: str = "agent-client-default"
) -> Dict[str, Any]:
    """
    High-entropy semantic context compressor that slashes token bloat by 80% to 95%.
    Saves LLM prompt tokens for autonomous agents while preserving all factual metrics.
    Cost: 0.01 USDC on Base. Requires payment_tx_hash.
    """
    price_usdc = 0.01
    tool_name = "token_context_compressor"

    if not payment_tx_hash:
        return payment_gateway.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price_usdc,
            client_agent_id=client_id
        )

    settled, settlement_info = payment_gateway.verify_payment_and_settle(
        tx_hash=payment_tx_hash,
        expected_price_usdc=price_usdc,
        tool_name=tool_name,
        payload_data={"raw_len": len(raw_content)},
        client_agent_id=client_id,
        simulate_test=_is_sim_allowed(payment_tx_hash)
    )

    if not settled:
        return {"error": "Payment Verification Failed", "details": settlement_info}

    result = token_compressor.compress_text_or_json(raw_content=raw_content)
    result["settlement_receipt"] = settlement_info
    return result


@mcp.tool()
def ast_structural_slicer(
    source_code: str,
    target_symbol: str,
    payment_tx_hash: Optional[str] = None,
    client_id: str = "agent-client-default"
) -> Dict[str, Any]:
    """
    Surgically extracts specific function/class AST nodes from code, saving agents
    thousands of tokens by avoiding full repository file ingestion.
    Cost: 0.02 USDC on Base. Requires payment_tx_hash.
    """
    price_usdc = 0.02
    tool_name = "ast_structural_slicer"

    if not payment_tx_hash:
        return payment_gateway.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price_usdc,
            client_agent_id=client_id
        )

    settled, settlement_info = payment_gateway.verify_payment_and_settle(
        tx_hash=payment_tx_hash,
        expected_price_usdc=price_usdc,
        tool_name=tool_name,
        payload_data={"target_symbol": target_symbol, "code_len": len(source_code)},
        client_agent_id=client_id,
        simulate_test=_is_sim_allowed(payment_tx_hash)
    )

    if not settled:
        return {"error": "Payment Verification Failed", "details": settlement_info}

    result = ast_slicer.slice_symbol(source_code=source_code, target_symbol=target_symbol)
    result["settlement_receipt"] = settlement_info
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SOUQ FastMCP Server")
    parser.add_argument("--port", type=int, default=8402, help="Port to run FastMCP on")
    args = parser.parse_args()

    print(f"🚀 Starting SOUQ Paid FastMCP Server on port {args.port}...")
    mcp.run()
