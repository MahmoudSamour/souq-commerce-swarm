import pytest
from agents.production.token_compressor import TokenContextCompressor, CodeASTSlicer


def test_token_context_compressor():
    compressor = TokenContextCompressor()
    bloated_text = """
    <html>
        <head><title>Bloated Test Page</title></head>
        <body>
            <script>console.log("noisy scripts");</script>
            <p>Hello! Please note that this is a disclaimer: all rights reserved.</p>
            <h1>Key Finding: Bitcoin Liquidation Wall at $98,500 with 1,420 BTC Depth</h1>
            <p>Order book imbalance is currently skewed +0.42 bullish.</p>
        </body>
    </html>
    """

    res = compressor.compress_text_or_json(bloated_text)
    assert res["status"] == "success"
    assert res["tokens_saved"] > 0
    assert res["compression_ratio_pct"] > 30.0
    assert "Bitcoin Liquidation Wall at $98,500" in res["compressed_payload"]
    assert "<script>" not in res["compressed_payload"]
    assert "estimated_llm_cost_saved_usd" in res


def test_code_ast_slicer():
    slicer = CodeASTSlicer()
    full_module = """
import os
import sys

def helper_alpha():
    return 42

def execute_trade(pair, amount):
    '''Target execution function'''
    print(f"Executing trade for {pair} of {amount}")
    return {"status": "FILLED", "pair": pair, "amount": amount}

def helper_beta():
    return 100
"""

    res = slicer.slice_symbol(source_code=full_module, target_symbol="execute_trade")
    assert res["status"] == "success"
    assert res["target_symbol"] == "execute_trade"
    assert "def execute_trade" in res["sliced_code"]
    assert "helper_alpha" not in res["sliced_code"]
    assert "helper_beta" not in res["sliced_code"]
    assert res["tokens_saved"] > 0


def test_token_compressor_json_and_log_dedup():
    import json
    compressor = TokenContextCompressor()

    bloated_json = json.dumps({
        "metadata": {"empty_note": "", "unused": None, "nested_empty": {}},
        "events": [
            {"id": i, "symbol": "BTC/USDT", "price": 90000 + i, "note": ""}
            for i in range(6)
        ],
    }, indent=2)
    j_res = compressor.compress_text_or_json(bloated_json)
    assert j_res["status"] == "success"
    assert j_res["content_mode"] == "json_structured"
    assert j_res["tokens_saved"] > 0
    assert "__cols__" in j_res["compressed_payload"]
    assert "empty_note" not in j_res["compressed_payload"]

    repeated_logs = "\n".join(["INFO Connection timeout retrying..." for _ in range(10)])
    l_res = compressor.compress_text_or_json(repeated_logs)
    assert l_res["content_mode"] == "text_cleaned"
    assert "[x10]" in l_res["compressed_payload"]
    assert l_res["tokens_saved"] > 0


