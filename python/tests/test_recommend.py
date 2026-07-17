from __future__ import annotations

from typing import Optional

from inferbench.recommend.config import recommend
from inferbench.types import EngineBenchmarkResult


def _fake_result(engine: str, installed: bool, avg: Optional[float]) -> EngineBenchmarkResult:
    return EngineBenchmarkResult(
        engine=engine,
        installed=installed,
        runs=[],
        avg_tokens_per_second=avg,
        min_tokens_per_second=avg,
        max_tokens_per_second=avg,
    )


def test_picks_the_engine_with_the_highest_avg_tokens_per_second():
    results = [_fake_result("omlx", True, 40), _fake_result("llama.cpp", True, 75)]
    rec = recommend(results)
    assert rec is not None
    assert rec.engine == "llama.cpp"


def test_ignores_engines_that_were_not_installed():
    results = [_fake_result("omlx", False, None), _fake_result("llama.cpp", True, 50)]
    rec = recommend(results)
    assert rec is not None
    assert rec.engine == "llama.cpp"


def test_ignores_engines_with_no_successful_runs():
    results = [_fake_result("omlx", True, None), _fake_result("llama.cpp", True, 50)]
    rec = recommend(results)
    assert rec is not None
    assert rec.engine == "llama.cpp"


def test_returns_none_when_no_engine_has_a_usable_result():
    results = [_fake_result("omlx", False, None), _fake_result("llama.cpp", True, None)]
    assert recommend(results) is None


def test_returns_none_for_an_empty_result_set():
    assert recommend([]) is None


def test_states_the_recommendation_is_run_specific_not_a_universal_ranking():
    results = [_fake_result("omlx", True, 60)]
    rec = recommend(results)
    assert rec is not None
    assert "this hardware and model" in rec.reason
    assert "not a universal ranking" in rec.reason
