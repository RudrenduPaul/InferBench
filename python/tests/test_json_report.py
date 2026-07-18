import os

import pytest

from inferbench.report.json_report import UnsafeOutputPathError, write_json_report
from inferbench.types import BenchmarkReport, HardwareProfile

REPORT = BenchmarkReport(
    timestamp="2026-07-18T00:00:00.000Z",
    hardware=HardwareProfile(
        platform="linux",
        arch="x64",
        total_memory_gb=32,
        cpu_model="Test CPU",
        is_apple_silicon=False,
    ),
    model="test-model",
    engines=[],
    recommendation=None,
)


@pytest.fixture
def in_tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_writes_report_to_a_plain_relative_path(in_tmp_cwd):
    write_json_report(REPORT, "report.json")
    assert (in_tmp_cwd / "report.json").exists()


def test_writes_report_to_a_nested_relative_path_within_cwd(in_tmp_cwd):
    (in_tmp_cwd / "out").mkdir()
    write_json_report(REPORT, os.path.join("out", "report.json"))
    assert (in_tmp_cwd / "out" / "report.json").exists()


def test_rejects_a_relative_out_path_that_traverses_outside_cwd(in_tmp_cwd):
    with pytest.raises(UnsafeOutputPathError):
        write_json_report(REPORT, os.path.join("..", "..", "outside-report.json"))


def test_allows_an_explicit_absolute_out_path_outside_cwd(in_tmp_cwd, tmp_path_factory):
    outside_dir = tmp_path_factory.mktemp("inferbench-outside")
    absolute_out = str(outside_dir / "report.json")
    write_json_report(REPORT, absolute_out)
    assert os.path.exists(absolute_out)
