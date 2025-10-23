#!/usr/bin/env python3
"""
EMERGENCY CONFIGURATION - Week 1 Deployment
CRITICAL: Fixes compression expansion issue (-356.9% bandwidth savings)

Deploy this configuration immediately to stop data expansion.

Issue: BRIO header (525 bytes) larger than small messages, causing 4.6x expansion
Solution: Disable BRIO, use binary_semantic + brotli only

Expected Results:
- Compression ratio: 1.5-2.0x (from current 0.70x)
- Bandwidth savings: 33-50% (from -356.9%)
- Zero expansion issues
"""

EMERGENCY_COMPRESSION_CONFIG = {
    # CRITICAL: Disable BRIO to stop expansion
    'enable_aura': False,

    # Use proven methods only (binary_semantic + brotli)
    'min_compression_size': 30,  # Compress messages > 30 bytes

    # Template configuration
    'template_store_path': 'template_store_expanded.json',  # Use expanded templates
    'template_cache_size': 128,

    # Optimizations
    'enable_normalization': True,  # Enable timestamp/UUID/IP normalization

    # Audit logging for compliance (disabled for benchmarking)
    'enable_audit_logging': False,  # Enable in production with proper directory
    'audit_log_directory': './audit_logs',  # Use local directory

    # Binary semantic settings
    'binary_advantage_threshold': 1.1,  # Use binary if 10% better than brotli
}

# Alternative: If you want to keep BRIO for large messages only
CONSERVATIVE_BRIO_CONFIG = {
    'enable_aura': True,

    # CRITICAL: Only use BRIO for large messages (above header overhead)
    'min_compression_size': 600,  # Messages must be > 600 bytes for BRIO

    # BRIO must be significantly better to justify header overhead
    'aura_preference_margin': 0.30,  # BRIO must be 30% better than alternatives

    # Template configuration
    'template_store_path': 'template_store.json',  # Use local path for testing
    'template_cache_size': 128,

    # Audit logging (disabled for benchmarking)
    'enable_audit_logging': False,  # Enable in production with proper directory
    'audit_log_directory': './audit_logs',  # Use local directory

    # Binary semantic settings
    'binary_advantage_threshold': 1.1,
}

# Recommended: Start with EMERGENCY_COMPRESSION_CONFIG
# Monitor for 48 hours, then consider CONSERVATIVE_BRIO_CONFIG if needed
DEFAULT_CONFIG = EMERGENCY_COMPRESSION_CONFIG


def get_compressor(**overrides):
    """
    Create compressor with emergency configuration

    Usage:
        from config.emergency_config import get_compressor
        compressor = get_compressor()
    """
    from aura_compression import ProductionHybridCompressor

    config = DEFAULT_CONFIG.copy()
    config.update(overrides)

    return ProductionHybridCompressor(**config)


if __name__ == "__main__":
    print("=" * 80)
    print("EMERGENCY CONFIGURATION - Week 1 Deployment")
    print("=" * 80)
    print()
    print("CRITICAL ISSUE:")
    print("  - Current compression ratio: 0.70x (EXPANDING data)")
    print("  - Bandwidth savings: -356.9% (using 4.6x MORE bandwidth)")
    print("  - Root cause: BRIO header (525 bytes) larger than small messages")
    print()
    print("EMERGENCY FIX:")
    print("  - Disable BRIO temporarily")
    print("  - Use binary_semantic + brotli only")
    print("  - Expected compression: 1.5-2.0x")
    print("  - Expected bandwidth savings: 33-50%")
    print()
    print("DEPLOYMENT:")
    print("  1. Update your compressor initialization:")
    print("     from config.emergency_config import get_compressor")
    print("     compressor = get_compressor()")
    print()
    print("  2. Monitor metrics for 48 hours")
    print()
    print("  3. Verify:")
    print("     - All compression ratios > 1.0x")
    print("     - Bandwidth savings > 0%")
    print("     - Zero messages expanding by >10%")
    print()
    print("=" * 80)

    # Test the configuration
    print()
    print("Testing emergency configuration...")
    print()

    compressor = get_compressor()

    # Test small message (previously expanded by BRIO)
    test_message = "The capital of France is Paris."
    compressed, method, metadata = compressor.compress(test_message)

    print(f"Test message: {test_message}")
    print(f"Original size: {metadata['original_size']} bytes")
    print(f"Compressed size: {metadata['compressed_size']} bytes")
    print(f"Compression ratio: {metadata['ratio']:.2f}x")
    print(f"Method: {metadata['method']}")
    print()

    if metadata['ratio'] > 1.0:
        print("SUCCESS: Compression is working correctly")
    else:
        print("ERROR: Still expanding data - needs investigation")
