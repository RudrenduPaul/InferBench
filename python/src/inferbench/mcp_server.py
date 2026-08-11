"""
MCP (Model Context Protocol) stdio server wrapping the inferbench CLI.

This wrapper shells out to the real Node/TypeScript `inferbench` CLI (the
canonical implementation) rather than reimplementing benchmark logic --
this Python package is a port of that CLI, but the MCP tool here calls
the npm-distributed binary directly so agent callers get identical
behavior to `npx inferbench`.

Production default: `npx inferbench <args>`.
Local-test override: set INFERBENCH_CLI_JS to a built `dist/cli.js` path
to invoke `node <path> <args>` instead -- useful when developing against
a repo checkout where the npm package may not be globally linked.

stdout is reserved for MCP's JSON-RPC framing over stdio, so anything this
module logs goes to stderr.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

from mcp.server import MCPServer

# Local-test override: point at a built dist/cli.js instead of `npx inferbench`.
# The npm package may not be globally linked on a dev machine, so testing
# this wrapper against a repo checkout needs a direct `node <path>` command.
# Production default (no env var set) is `npx inferbench`.
_LOCAL_CLI_JS = os.environ.get("INFERBENCH_CLI_JS")


def _base_command() -> list[str]:
    if _LOCAL_CLI_JS:
        return ["node", _LOCAL_CLI_JS]
    return ["npx", "inferbench"]


def _capture_help() -> str:
    """Best-effort `--help` capture, used as the tool's dynamic description
    instead of a hardcoded string."""
    fallback = (
        "Run the inferbench CLI (benchmarks local-LLM-inference engines "
        "omlx and llama.cpp against a model on this machine's hardware)."
    )
    try:
        proc = subprocess.run(
            [*_base_command(), "--help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.stdout.strip() or fallback
    except Exception as exc:  # noqa: BLE001 - degrade to a generic description
        print(f"inferbench-mcp: could not capture --help: {exc}", file=sys.stderr)
        return fallback


mcp = MCPServer(name="inferbench")


@mcp.tool(description=_capture_help())
def run(args: list[str]) -> dict[str, Any]:
    """Run the inferbench CLI with the given arguments and return parsed JSON.

    `args` should be the subcommand and flags as separate list items, e.g.
    ["run", "--model", "qwen2.5-1.5b-instruct-4bit", "--engines", "omlx"].
    `--json` is appended automatically so output is always machine-readable.
    """
    command = [*_base_command(), *args, "--json"]
    print(f"inferbench-mcp: running {command!r}", file=sys.stderr)
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired as exc:
        return {"error": f"{command!r} timed out after {exc.timeout}s", "command": command}
    except OSError as exc:
        return {"error": f"failed to exec {command!r}: {exc}", "command": command}

    if proc.stderr:
        print(f"inferbench-mcp: stderr: {proc.stderr}", file=sys.stderr)

    if proc.returncode != 0:
        return {
            "error": f"inferbench exited with code {proc.returncode}",
            "stderr": proc.stderr.strip(),
            "command": command,
        }

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {
            "error": f"could not parse JSON output: {exc}",
            "stdout": proc.stdout,
            "command": command,
        }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
