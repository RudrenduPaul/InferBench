"""
Default varied prompt set, ported verbatim from src/prompts.ts: 8 distinct
prompts across different topics and lengths, deliberately never repeating
the exact same prompt, to avoid the prefix-cache skew observed during the
original TypeScript tool's real validation (a repeated identical prompt let
llama.cpp reuse 39/40 cached prompt tokens on the second call, which is not
a fair steady-state comparison).
"""
from __future__ import annotations

DEFAULT_PROMPTS: list[str] = [
    "Explain in one paragraph why the sky is blue.",
    "Write a short haiku about autumn leaves falling in a quiet forest.",
    "What are three practical tips for someone learning to cook rice perfectly every time?",
    "Summarize the plot of a story about a lighthouse keeper who discovers a message in a bottle.",
    "List five differences between a cat and a dog as household pets.",
    "Describe how a bicycle chain transfers power from the pedals to the rear wheel.",
    "Give a brief explanation of why leaves change color in autumn, covering chlorophyll and other pigments.",
    "What is the difference between weather and climate? Explain with a simple example.",
]

WARMUP_PROMPT = "Say hello."
