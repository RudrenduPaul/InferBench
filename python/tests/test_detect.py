from __future__ import annotations

from inferbench.hardware.detect import detect_hardware


def test_returns_a_profile_with_the_expected_shape():
    profile = detect_hardware()
    assert isinstance(profile.platform, str)
    assert isinstance(profile.arch, str)
    assert profile.total_memory_gb > 0
    assert isinstance(profile.cpu_model, str)
    assert isinstance(profile.is_apple_silicon, bool)


def test_only_reports_apple_silicon_true_on_darwin_arm64():
    profile = detect_hardware()
    if profile.is_apple_silicon:
        assert profile.platform == "darwin"
        assert profile.arch == "arm64"
