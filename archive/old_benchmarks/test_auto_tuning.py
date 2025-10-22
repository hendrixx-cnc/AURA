#!/usr/bin/env python3
"""
Phase 3 validation: auto-tuning behavior and environment overrides.
"""
import json
import os
import sys
import tempfile

# Ensure package source path is available
sys.path.insert(0, 'packages/aura-compressor-py/src')

from aura_compressor.streamer import AuraTransceiver, AutoTuningTransceiver  # noqa: E402


def _reset_env(keys):
    for key, value in keys.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_auto_tuning_adapts_thresholds():
    print("=== Auto-tuning threshold adjustment test ===")

    server = AutoTuningTransceiver(
        tune_interval=2,
        ratio_target=1.05,
        ratio_tolerance=0.12,
        refresh_adjust=4,
        occurrence_adjust=1,
        min_refresh_threshold=8,
        max_refresh_threshold=64,
        min_occurrences_limit=1,
        max_occurrences_limit=6,
        min_compression_size=0,
        load_env=False,
    )
    client = AuraTransceiver(min_compression_size=0, load_env=False)

    handshake = server.perform_handshake()
    client.receive_handshake(handshake)

    initial_refresh = server.adaptive_refresh_threshold
    initial_occ = server.min_adaptive_occurrences

    # Poorly compressible text (high entropy)
    poor_text = ''.join(chr((i % 94) + 32) for i in range(2048))
    server.compress(poor_text, adaptive=False)
    server.compress(poor_text, adaptive=False)

    assert server.adaptive_refresh_threshold == initial_refresh, "Baseline pass should not adjust immediately."
    assert server.min_adaptive_occurrences == initial_occ, "Occurrence requirement should remain unchanged initially."

    # Persistently low ratios should tighten thresholds
    stubborn_text = "A" * 4096
    server.compress(stubborn_text, adaptive=False)
    server.compress(stubborn_text, adaptive=False)

    lowered_refresh = server.adaptive_refresh_threshold
    assert lowered_refresh < initial_refresh, "Refresh threshold should decrease after sustained poor ratios."
    assert server.min_adaptive_occurrences <= initial_occ, "Occurrence requirement should not increase under poor ratios."

    # Highly compressible text should allow the tuner to relax again
    ai_text = ("The neural network generated a concise summary with excellent compression. ") * 40
    server.compress(ai_text, adaptive=False)
    server.compress(ai_text, adaptive=False)

    final_refresh = server.adaptive_refresh_threshold
    history = server.get_auto_tuning_history()
    print(f"   ➡️ Auto-tuning history: {history}")
    print(f"   ✅ Threshold after first tuning cycle: {lowered_refresh}")
    print(f"   ✅ Threshold after second tuning cycle: {final_refresh}")

    assert final_refresh > lowered_refresh, "Refresh threshold should recover after strong ratios."
    assert final_refresh >= server.min_refresh_threshold, "Refresh threshold must respect configured minimum."
    assert server.min_adaptive_occurrences >= server.min_occurrences_limit, "Occurrences limit should respect minimum bound."
    assert server.min_adaptive_occurrences >= initial_occ, "Occurrence threshold should rebound once compression improves."

    assert len(history) >= 2, "Auto-tuning history should record both tuning cycles."
    print(f"   ✅ Auto-tuning events recorded: {len(history)}")


def test_environment_overrides():
    print("\n=== Environment override loading test ===")

    snapshot = {key: os.environ.get(key) for key in [
        "AURA_MIN_COMPRESSION_SIZE",
        "AURA_ENABLE_AUDIT",
        "AURA_ADAPTIVE_REFRESH_THRESHOLD",
        "AURA_CONFIG_PATH",
    ]}

    try:
        os.environ["AURA_MIN_COMPRESSION_SIZE"] = "128"
        os.environ["AURA_ENABLE_AUDIT"] = "true"
        os.environ["AURA_ADAPTIVE_REFRESH_THRESHOLD"] = "48"

        server_env = AuraTransceiver()
        assert server_env.min_compression_size == 128
        assert server_env.enable_server_audit is True
        assert server_env.adaptive_refresh_threshold == 48
        print("   ✅ Direct environment overrides applied.")

        # Config file override
        config_data = {
            "min_compression_size": 300,
            "adaptive_refresh_threshold": 40,
            "enable_audit": False
        }
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            json.dump(config_data, handle)
            config_path = handle.name

        os.environ["AURA_CONFIG_PATH"] = config_path
        # Remove direct override to check config load precedence
        os.environ.pop("AURA_MIN_COMPRESSION_SIZE", None)
        os.environ.pop("AURA_ADAPTIVE_REFRESH_THRESHOLD", None)
        os.environ.pop("AURA_ENABLE_AUDIT", None)

        server_cfg = AuraTransceiver()
        assert server_cfg.min_compression_size == 300
        assert server_cfg.adaptive_refresh_threshold == 40
        assert server_cfg.enable_server_audit is False
        print("   ✅ Configuration file override loaded from AURA_CONFIG_PATH.")

        server_no_env = AuraTransceiver(load_env=False)
        assert server_no_env.min_compression_size == 200
        assert server_no_env.adaptive_refresh_threshold == 32
        print("   ✅ load_env=False ignores environment.")
    finally:
        # Cleanup temp file and environment
        config_file = os.environ.get("AURA_CONFIG_PATH")
        if config_file and os.path.exists(config_file):
            os.unlink(config_file)
        _reset_env(snapshot)


if __name__ == "__main__":
    test_auto_tuning_adapts_thresholds()
    test_environment_overrides()
    print("\nAll auto-tuning and environment tests passed ✅")
