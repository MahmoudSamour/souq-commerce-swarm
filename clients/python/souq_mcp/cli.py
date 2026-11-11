import sys
import argparse
import json
from .client import SouqClient
from .mcp_server import StdioMCPServer


def main():
    parser = argparse.ArgumentParser(
        description="SOUQ MCP Client & CLI - Fast sub-cent AI agent micro-services on Base L2"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Command: stdio server (default when run via uvx souq-mcp)
    serve_parser = subparsers.add_parser("serve", help="Run MCP stdio server (for Claude Desktop, Cursor, etc.)")

    # Command: call <tool> [json_args]
    call_parser = subparsers.add_parser("call", help="Directly invoke a SOUQ micro-service tool")
    call_parser.add_argument("tool", help="Tool identifier (e.g. prediction_market_arbitrage_radar)")
    call_parser.add_argument("--args", default="{}", help="JSON payload arguments")

    # Command: list
    subparsers.add_parser("list", help="List available SOUQ tools and their economic ROI")

    args = parser.parse_args()

    if args.command == "serve" or args.command is None:
        # Default behavior: run MCP stdio server
        server = StdioMCPServer()
        server.run()

    elif args.command == "call":
        client = SouqClient()
        try:
            kwargs = json.loads(args.args)
        except Exception as e:
            sys.stderr.write(f"Invalid JSON args: {e}\n")
            sys.exit(1)
        try:
            res = client.call_tool(args.tool, **kwargs)
            print(json.dumps(res, indent=2))
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.exit(1)

    elif args.command == "list":
        client = SouqClient()
        import urllib.request
        try:
            req = urllib.request.Request(f"{client.endpoint}/.well-known/mcp.json", headers={"User-Agent": "souq-cli"})
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                print(json.dumps(json.loads(resp.read().decode("utf-8")), indent=2))
        except Exception as e:
            sys.stderr.write(f"Failed to fetch tool listing: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
