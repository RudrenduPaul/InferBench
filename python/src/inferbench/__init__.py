"""
Programmatic / agent-native entry point.

    from inferbench import benchmark_engine, detect_hardware, all_engines

    hardware = detect_hardware()
    adapters = all_engines()
    results = [benchmark_engine(a, model="bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M") for a in adapters]

Same core orchestration the CLI calls; inferbench.cli is a thin
argument-parsing wrapper over these functions.

This is the Python port of the inferbench-cli npm package
(https://www.npmjs.com/package/inferbench-cli). Both distributions
benchmark the same two supported local-inference engines (omlx,
llama.cpp) against a fixed, varied prompt set over each engine's own
OpenAI-compatible HTTP server; see
https://github.com/RudrenduPaul/InferBench for the canonical
documentation and the original TypeScript source.
"""
from .benchmark import benchmark_engine
from .cost.cloud_comparison import CLOUD_PRICING_PER_1K_OUTPUT_TOKENS, CostComparison, compare_to_cloud
from .engines.registry import SUPPORTED_ENGINES, all_engines, resolve_engines
from .hardware.detect import detect_hardware
from .recommend.config import recommend
from .report.json_report import report_to_dict, write_json_report
from .types import (
    BenchmarkReport,
    CompletionResult,
    EngineBenchmarkResult,
    HardwareProfile,
    PromptRunResult,
    Recommendation,
    StartedServer,
)

__version__ = "0.1.0"

__all__ = [
    "benchmark_engine",
    "detect_hardware",
    "all_engines",
    "resolve_engines",
    "recommend",
    "compare_to_cloud",
    "report_to_dict",
    "write_json_report",
    "SUPPORTED_ENGINES",
    "CLOUD_PRICING_PER_1K_OUTPUT_TOKENS",
    "BenchmarkReport",
    "CompletionResult",
    "CostComparison",
    "EngineBenchmarkResult",
    "HardwareProfile",
    "PromptRunResult",
    "Recommendation",
    "StartedServer",
    "__version__",
]
