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


_RUN_DESCRIPTION = """Runs a live local-LLM-inference benchmark by shelling out to the `inferbench` CLI (the same binary published as `inferbench-cli` on npm) and returns its parsed JSON report. Call this when an agent needs real, measured tokens-per-second numbers for a locally installed inference engine (currently `omlx` and `llama.cpp`) on the machine this MCP server runs on -- for example, to decide which engine to recommend, to compare a model across engines, or to produce a fresh performance report. Do not call it to benchmark a remote machine, a model that has not been downloaded or cached locally for the chosen engine, or an engine other than omlx/llama.cpp (the CLI supports no others). At least one of the two engines must already be installed on the host (`omlx` via Homebrew, Apple Silicon only; `llama.cpp` via Homebrew or a source build, any platform) -- this tool does not install engines for you.

Each call starts a real local inference server for every engine under test on 127.0.0.1, sends it live completion requests, and can take anywhere from tens of seconds to several minutes to return, capped at a 600-second internal timeout. It is read-only with respect to your project and writes no files, except when `args` explicitly includes `--out <path>`, in which case the CLI also saves the JSON report to that path. No data leaves the machine: every request goes to a server the CLI itself started locally. Calls are not idempotent in the sense of returning cached results -- rerunning the same args re-measures live and can produce different numbers run to run (thermal state, background load). On failure (bad args, no matching engine installed, a CLI crash, or a timeout) the tool does not raise; it returns a JSON object with an "error" key describing what went wrong plus the "command" that was actually run, so the caller can inspect and retry with corrected arguments.

`args` is a `list[str]` of the exact CLI argv, mirroring `inferbench <args>` on the command line -- `--json` is appended automatically, so callers should not add it themselves. The CLI currently exposes one subcommand, `run`. Example argv lists, pulled from the real `inferbench run --help` output:
- ["run", "--model", "bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M", "--engines", "llama.cpp"] -- benchmark llama.cpp against a Hugging Face model spec (llama.cpp downloads and caches it automatically).
- ["run", "--model", "qwen2.5-1.5b-instruct-4bit", "--engines", "omlx", "--max-tokens", "100"] -- benchmark omlx against a model already present under ~/.omlx/models/, with a shorter completion length.
- ["run", "--model", "<spec>", "--out", "report.json", "--verbose"] -- benchmark every installed engine, save the full report to a file, and include raw engine server output for debugging.
- ["--help"] or ["run", "--help"] -- print the CLI's own usage text to discover flags beyond this description; the auto-appended `--json` makes this particular output land in the returned object's "stdout" field rather than parse as JSON.

On success the returned JSON has: `timestamp` (ISO string), `hardware` (`platform`, `arch`, `totalMemoryGb`, `cpuModel`, `isAppleSilicon`), `model` (the spec tested), `engines` (a list of per-engine results with `engine`, `installed`, an optional `error`, per-prompt `runs`, and `avgTokensPerSecond`/`minTokensPerSecond`/`maxTokensPerSecond`), and `recommendation` (`engine` and `reason`, or `null` if no engine could be benchmarked)."""


mcp = MCPServer(name="inferbench")


@mcp.tool(description=_RUN_DESCRIPTION)
def run(args: list[str]) -> dict[str, Any]:
    """Run the inferbench CLI with the given argv and return its parsed JSON report.

    See `_RUN_DESCRIPTION` (the tool's registered description) for the full
    contract: parameter shape, example argv, side effects, and the returned
    JSON's key structure.
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
