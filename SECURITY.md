# Security Policy

InferBench starts real local server processes (`omlx serve`,
`llama-server`) and sends them HTTP requests built partly from
user-supplied input (`--model`, `--max-tokens`). A vulnerability that lets
a crafted `--model` value or a malicious response from a benchmarked
server escape the intended read-only measurement flow is taken seriously
and handled as a priority.

## Supported versions

| Package | Version | Supported |
| --- | --- | --- |
| `inferbench-cli` (npm) | 0.1.x | Yes |
| `inferbench-cli` (PyPI) | 0.1.x | Yes |

Both distributions are pre-1.0 and under active development. Security
fixes land on the latest `0.1.x` release of each; there is no older
supported line to backport to yet.

## Reporting a vulnerability

**Do not open a public GitHub issue for a security vulnerability.**

Report it privately via
[GitHub Security Advisories](https://github.com/RudrenduPaul/InferBench/security/advisories/new)
for this repository. Include:

- Which distribution is affected (npm package, PyPI package, or both).
- A minimal reproduction: the exact command/library call, and the
  `--model` value or engine response content that triggers the issue.
- What you expected InferBench to do, and what it actually did.
- Your assessment of impact.

## What counts as in scope

- Any code path where a `--model` value, or any other CLI/library input,
  is passed to a subprocess call in a way that could execute additional
  shell commands. Both distributions launch engine binaries with a fixed
  argv list (`spawn`/`execFile` in TypeScript, `subprocess.Popen` with an
  argv list in Python) rather than a shell string -- a report showing an
  actual injection path through this would be a serious, in-scope finding.
- Any code path where content returned by a benchmarked engine's own HTTP
  server (a value this tool did not generate itself) is `eval`'d,
  dynamically executed, or written outside the report file the user
  explicitly asked for via `--out`.
- A crafted engine response causing unbounded resource consumption (an
  unbounded hang, unbounded memory growth reading a response body) that
  bypasses the documented request timeout.

## What is out of scope

- The benchmark *numbers themselves* being unrepresentative of your
  hardware or workload -- that is an inherent property of any benchmark,
  not a security bug. Open a normal issue if you believe the measurement
  methodology itself is flawed.
- Vulnerabilities in a benchmarked engine itself (`omlx`, `llama.cpp`) --
  report those to that engine's own maintainers.
- The fact that InferBench requires a locally installed, already-trusted
  inference engine binary to function -- InferBench does not download,
  vet, or sandbox engine binaries; it assumes you already trust whatever
  engine you installed and are choosing to benchmark.
- `--out <path>` writing to any path you pass it within the current
  working directory, or to any absolute path you supply directly -- this
  is the same trust model as `curl -o`/`tar -xf`: you are supplying that
  path yourself, to your own filesystem, with your own permissions. Note
  this does **not** extend to a relative path that traverses outside the
  current working directory (e.g. `--out ../../etc/cron.d/x`): that case
  is rejected by `assertSafeOutputPath()` (`src/report/json.ts`), so it is
  not part of the trust model described here and is not out of scope --
  see the FAQ in the [project README](./README.md) for the exact
  behavior. Only an explicit absolute path bypasses that check, since
  that's a value the caller passed directly rather than one that escaped
  via `..` traversal. If you wrap InferBench in a script that builds
  `--out` from an untrusted source, validating any absolute path you
  allow through remains your script's responsibility, not InferBench's.

## Response

We aim to acknowledge a report within 5 business days and to have a fix or
a mitigation plan within 30 days for a confirmed, in-scope vulnerability.
Credit is given in the release notes unless you ask to remain anonymous.
