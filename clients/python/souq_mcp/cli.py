import sys
import argparse
import json
from . import __version__
from .client import SouqClient
from .mcp_server import StdioMCPServer


def main():
    parser = argparse.ArgumentParser(
        description="SOUQ MCP Client & CLI - Fast sub-cent AI agent micro-services on Base L2"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    # Command: stdio server (default when run via uvx souq-mcp)
    subparsers.add_parser("serve", help="Run MCP stdio server (for Claude Desktop, Cursor, etc.)")

    # Command: call <tool> [json_args]
    call_parser = subparsers.add_parser("call", help="Directly invoke a SOUQ micro-service tool")
    call_parser.add_argument("tool", help="Tool identifier (e.g. prediction_market_arbitrage_radar)")
    call_parser.add_argument("json_args", nargs="?", default=None, help="Optional positional JSON payload arguments")
    call_parser.add_argument("--args", dest="args_flag", default=None, help="JSON payload arguments")
    call_parser.add_argument("--api-key", default=None, help="Optional prepaid SOUQ API key (overrides SOUQ_API_KEY)")

    # Command: status
    status_parser = subparsers.add_parser("status", help="Inspect SOUQ API key credit balance & Base USDC settlement details")
    status_parser.add_argument("--api-key", default=None, help="Optional prepaid SOUQ API key")

    # Command: list
    subparsers.add_parser("list", help="List available SOUQ tools and their economic ROI")

    args = parser.parse_args()

    if args.command == "serve" or args.command is None:
        # Default behavior: run MCP stdio server
        server = StdioMCPServer()
        server.run()

    elif args.command == "call":
        client = SouqClient(api_key=args.api_key)
        raw_args = args.args_flag if args.args_flag is not None else (args.json_args if args.json_args is not None else "{}")
        try:
            kwargs = json.loads(raw_args)
            if not isinstance(kwargs, dict):
                raise ValueError("JSON args must decode to an object")
        except Exception as e:
            sys.stderr.write(f"Invalid JSON args: {e}\n")
            sys.exit(1)
        try:
            res = client.call_tool(args.tool, kwargs)
            print(json.dumps(res, indent=2))
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.exit(1)

    elif args.command == "status":
        client = SouqClient(api_key=args.api_key)
        try:
            print(json.dumps(client.balance(), indent=2))
        except Exception as e:
            sys.stderr.write(f"Failed to check status: {e}\n")
            sys.exit(1)

    elif args.command == "list":
        client = SouqClient()
        try:
            print(json.dumps(client.list_tools(), indent=2))
        except Exception as e:
            sys.stderr.write(f"Failed to fetch tool listing: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
