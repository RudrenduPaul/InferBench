# Contributing to InferBench

InferBench ships two independently maintained, equally first-class
distributions of the same benchmark tool: an npm package (`inferbench-cli`,
TypeScript, repo root) and a PyPI package (`inferbench-cli`, Python,
`python/`). Both start the same two supported engines' own
OpenAI-compatible HTTP servers (`omlx serve`, `llama-server`) and measure
them with the same architecture. Please read this whole file before
opening a PR -- which section applies depends on which codebase you're
touching.

## Ground rules

- Every change lands with tests. Neither test suite is optional scaffolding
  -- both are the mechanism that keeps the two implementations behaving
  the same way.
- A measurement-logic change (the HTTP harness, the recommendation rule,
  the hardware detector) should be made in **both** `src/` (TypeScript) and
  `python/src/inferbench/` (Python), with equivalent test coverage added to
  both suites, unless the PR description explicitly says the two are meant
  to diverge (state the reason if so).
- No `eval`/`exec` of anything read from external input, in either
  codebase. Every subprocess call to an inference engine binary is a fixed
  argv list, never a shell string -- a `--model` value must never be able
  to inject additional shell commands.
- If you add or change a supported engine, verify its actual CLI/HTTP
  interface against that engine's own real documentation before writing
  adapter code -- this project's own history includes one real instance of
  planning a benchmark-CLI-parsing approach for `omlx` before discovering,
  against its real README, that no such CLI command exists (its benchmark
  feature is GUI-only). Verify first, then build.

## Working on the TypeScript package (repo root)

```bash
npm install
npm run build
npm test
npm run lint
```

- Source lives under `src/`: `benchmark.ts` (orchestration),
  `engines/` (per-engine adapters), `harness/` (the shared HTTP
  measurement code), `hardware/detect.ts`, `recommend/config.ts`,
  `report/json.ts`, `cost/cloud_comparison.ts`, `cli.ts`.
- Tests use `vitest` (`src/**/*.test.ts`, one file per module).
- `npm run build` compiles to `dist/`, which the `bin` entry
  (`inferbench`) resolves to.

## Working on the Python package (`python/`)

```bash
cd python
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

- Source lives under `python/src/inferbench/`, laid out to mirror the
  TypeScript module structure 1:1 (`engines/`, `harness/`,
  `hardware/`, `recommend/`, `report/`, `cost/`, `cli.py`, `types.py`,
  `errors.py`, `benchmark.py`, `prompts.py`) so a change in one codebase
  has an obvious counterpart to check in the other.
- Tests use `pytest` (`python/tests/test_*.py`).
- Build and verify a real install before opening a PR that touches
  packaging. Build the venv **outside** the `python/` source tree --
  building it inside gets accidentally bundled into the sdist:
  ```bash
  python3 -m venv /tmp/inferbench-verify
  /tmp/inferbench-verify/bin/pip install -e "python[dev]"
  /tmp/inferbench-verify/bin/pytest python
  python3 -m build python --outdir /tmp/inferbench-dist
  tar tzf /tmp/inferbench-dist/*.tar.gz   # inspect the file listing before publishing anything
  ```

## Adding or changing engine adapter logic

1. Verify the engine's real CLI flags and HTTP server behavior against its
   own current documentation -- do not assume parity with an existing
   adapter's flags.
2. Implement `is_installed()` / `isInstalled()` as a fixed-argv version
   check (never a shell string) and `start_server()` / `startServer()`
   using the shared `spawn_server_and_wait_ready` / `spawnServerAndWaitReady`
   harness so readiness polling stays consistent across engines.
3. Add unit tests mocking the subprocess/HTTP calls (see
   `python/tests/test_llamacpp.py` / `src/engines/llamacpp.test.ts` for the
   pattern), plus, where feasible in your own environment, a real
   end-to-end run against the actual engine binary -- document plainly in
   the PR description which parts were verified against a real engine and
   which were only unit-tested with mocks.

## Reporting a security issue

Do not open a public issue for a security vulnerability. See
[SECURITY.md](./SECURITY.md).

## License

By contributing, you agree your contribution is licensed under the same
Apache License, Version 2.0 that covers the rest of this repository (see
[LICENSE](./LICENSE)).
