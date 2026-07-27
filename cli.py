"""CLI entry point for the pip-installed pe-mcp-thin package.

Mirrors entrypoint.sh's `serve`/`validate` subcommands for native
(non-Docker) installs. `setup`'s interactive /config-volume wizard is
Docker-specific and isn't replicated here — native installs set
SMART_MCP_URL / PE_CA_CERT directly in the environment instead.
"""

import sys


def main():
    args = sys.argv[1:]
    command = args[0] if args else "serve"

    if command == "serve":
        import proxy

        proxy.proxy.run(transport="stdio")
    elif command == "validate":
        import selftest

        selftest.main()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Usage: pe-mcp-thin {serve|validate}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
