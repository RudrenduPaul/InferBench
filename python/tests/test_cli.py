from __future__ import annotations

import pytest

from inferbench.cli import run_cli


def test_no_subcommand_prints_help_and_exits_0(capsys):
    exit_code = run_cli(["inferbench"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "inferbench" in captured.out


def test_missing_required_model_flag_exits_2_via_argparse(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run_cli(["inferbench", "run"])
    assert exc_info.value.code == 2


def test_unknown_engine_name_exits_1_with_a_usage_message(capsys):
    exit_code = run_cli(["inferbench", "run", "--model", "any", "--engines", "not-a-real-engine"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Unknown engine" in captured.err
    assert "not-a-real-engine" in captured.err


def test_invalid_max_tokens_exits_1_with_a_usage_message(capsys):
    exit_code = run_cli(
        ["inferbench", "run", "--model", "any", "--engines", "omlx", "--max-tokens", "not-a-number"]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Invalid --max-tokens" in captured.err


def test_version_flag_reports_the_package_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        run_cli(["inferbench", "--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "inferbench" in captured.out
