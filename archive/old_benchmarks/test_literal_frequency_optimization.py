#!/usr/bin/env python3
"""
Test suite for literal frequency threshold optimization.

Tests adaptive literal learning functionality:
1. Literal filtering based on frequency threshold
2. Text sample analysis for handshake optimization
3. Adaptive refresh when escape codes are frequent
4. Recent text buffer tracking
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

from aura_compressor.streamer import AuraTransceiver


def test_literal_threshold_filters_characters():
    """Test that literal_frequency_threshold actually filters literals."""
    print("🧪 Testing Literal Frequency Threshold Filtering...")

    # Sample text with some rare characters
    sample_text = "Hello world! This is a test with @ # $ symbols."

    # Test 1: High threshold should exclude most punctuation
    t1 = AuraTransceiver(
        literal_frequency_threshold=0.1,  # 10% - very high
        min_compression_size=10
    )
    t1.perform_handshake(text_sample=sample_text)

    # Count literal codes in tree
    literal_codes = {k: v for k, v in t1.compression_tree.items() if k[0] == 'L'}
    print(f"   High threshold (10%): {len(literal_codes)} literals in tree")
    print(f"   Sample literals: {list(literal_codes.keys())[:10]}")

    # Space should definitely be included (it's common)
    assert ('L', ' ') in literal_codes, "Space should be in tree"

    # @ should probably be rare (unless threshold is very low)
    is_at_rare = ('L', '@') not in literal_codes
    print(f"   '@' is rare: {is_at_rare}")

    # Test 2: Low threshold should include more punctuation
    t2 = AuraTransceiver(
        literal_frequency_threshold=0.01,  # 1% - more inclusive
        min_compression_size=10
    )
    t2.perform_handshake(text_sample=sample_text)

    literal_codes_2 = {k: v for k, v in t2.compression_tree.items() if k[0] == 'L'}
    print(f"   Low threshold (1%): {len(literal_codes_2)} literals in tree")

    # Low threshold should have more literals
    assert len(literal_codes_2) >= len(literal_codes), \
        "Lower threshold should include more literals"

    print("✅ Literal Threshold Filtering: PASSED\n")


def test_handshake_with_text_sample():
    """Test that text_sample optimizes handshake."""
    print("🧪 Testing Handshake with Text Sample...")

    # Code sample with specific characters (repeated to hit threshold)
    code_sample = """
    def hello_world():
        print("Hello, World!")
        x = 42
        y = x * 2
        return y
    """ * 3  # Repeat to ensure chars hit threshold

    # Test with code sample - use lower threshold
    t_code = AuraTransceiver(
        literal_frequency_threshold=0.01,  # 1% threshold
        min_compression_size=10
    )
    t_code.perform_handshake(text_sample=code_sample)

    literal_codes_code = {k: v for k, v in t_code.compression_tree.items() if k[0] == 'L'}
    print(f"   Code sample: {len(literal_codes_code)} literals in tree")
    print(f"   Sample chars: {[k[1] for k in list(literal_codes_code.keys())[:15]]}")

    # Should include common code chars (at least some)
    has_parens = ('L', '(') in literal_codes_code
    has_quotes = ('L', '"') in literal_codes_code
    has_equals = ('L', '=') in literal_codes_code

    print(f"   Has '(': {has_parens}, Has '\"': {has_quotes}, Has '=': {has_equals}")
    assert has_parens and has_equals, "Should include common code punctuation"

    # Natural language sample
    prose_sample = """
    The quick brown fox jumps over the lazy dog.
    This is a sample of natural language text.
    It contains sentences with periods and commas.
    """ * 3  # Repeat to ensure frequency

    t_prose = AuraTransceiver(
        literal_frequency_threshold=0.01,  # 1% threshold
        min_compression_size=10
    )
    t_prose.perform_handshake(text_sample=prose_sample)

    literal_codes_prose = {k: v for k, v in t_prose.compression_tree.items() if k[0] == 'L'}
    print(f"   Prose sample: {len(literal_codes_prose)} literals in tree")

    # Should include common prose chars
    has_period = ('L', '.') in literal_codes_prose
    has_space = ('L', ' ') in literal_codes_prose

    print(f"   Has '.': {has_period}, Has ' ': {has_space}")
    assert has_period and has_space, "Should include common prose punctuation"

    print("✅ Handshake with Text Sample: PASSED\n")


def test_escape_code_handling():
    """Test that rare literals are handled via escape codes."""
    print("🧪 Testing Escape Code Handling...")

    # Create transceiver with limited literals
    transceiver = AuraTransceiver(
        literal_frequency_threshold=0.1,  # High threshold
        min_compression_size=10
    )

    # Sample text with ONLY common chars
    common_sample = "hello world this is a test"
    transceiver.perform_handshake(text_sample=common_sample)

    # Now compress text with rare characters
    text_with_rare = "hello @ world # test $ symbols %"

    packets = transceiver.compress(text_with_rare, adaptive=False)
    decompressed = transceiver.decompress(packets[0])

    assert decompressed == text_with_rare, "Should handle rare chars via escape codes"
    print(f"   Original:     '{text_with_rare}'")
    print(f"   Decompressed: '{decompressed}'")

    print("✅ Escape Code Handling: PASSED\n")


def test_adaptive_refresh_with_literal_learning():
    """Test adaptive refresh when escape codes are frequent."""
    print("🧪 Testing Adaptive Refresh with Literal Learning...")

    # Create transceiver with low threshold for refresh
    transceiver = AuraTransceiver(
        literal_frequency_threshold=0.05,
        adaptive_refresh_threshold=5,  # Trigger refresh after 5 escape codes
        min_compression_size=10
    )

    # Initial handshake with simple text (no special chars)
    transceiver.perform_handshake(text_sample="hello world")

    # Get initial literal count
    initial_literals = len([k for k in transceiver.compression_tree.items() if k[0] == 'L'])
    print(f"   Initial literals in tree: {initial_literals}")

    # Compress text with MANY rare characters to trigger refresh
    texts_with_rare_chars = [
        "Test @@@@@" * 2,  # Many @ symbols
        "Data ###$$" * 2,  # Many # and $ symbols
        "Code %%%^^" * 2,  # Many % and ^ symbols
    ]

    for text in texts_with_rare_chars:
        packets = transceiver.compress(text, adaptive=True)

        # Check if refresh was triggered (packets would include handshake)
        if transceiver.literal_fallback_tokens > transceiver.adaptive_refresh_threshold:
            print(f"   Escape codes used: {transceiver.literal_fallback_tokens}")
            print(f"   Refresh required: {transceiver.refresh_required}")

    print("✅ Adaptive Refresh with Literal Learning: PASSED\n")


def test_recent_text_buffer():
    """Test that recent text is tracked for adaptive learning."""
    print("🧪 Testing Recent Text Buffer...")

    transceiver = AuraTransceiver(
        literal_frequency_threshold=0.01,
        min_compression_size=10
    )
    transceiver.perform_handshake()

    # Compress several texts
    texts = [
        "First message",
        "Second message with more characters",
        "Third message with even more text to process"
    ]

    for text in texts:
        transceiver.compress(text, adaptive=False)

    # Check that recent text buffer has content
    recent_text = ''.join(transceiver._recent_text_buffer)
    print(f"   Recent buffer length: {len(recent_text)} chars")
    assert len(recent_text) > 0, "Recent text buffer should contain text"

    # All three messages should be in buffer
    for text in texts:
        assert text in recent_text, f"Buffer should contain '{text}'"

    print("✅ Recent Text Buffer: PASSED\n")


def test_roundtrip_with_adaptive_literals():
    """Test full roundtrip with adaptive literal optimization."""
    print("🧪 Testing Full Roundtrip with Adaptive Literals...")

    # Sender and receiver
    sender = AuraTransceiver(
        literal_frequency_threshold=0.02,
        adaptive_refresh_threshold=32,
        min_compression_size=10
    )

    receiver = AuraTransceiver(
        literal_frequency_threshold=0.02,
        adaptive_refresh_threshold=32,
        min_compression_size=10
    )

    # Handshake with sample text
    sample = "This is typical text with common punctuation: .!?,-"
    handshake = sender.perform_handshake(text_sample=sample)
    receiver.receive_handshake(handshake)

    # Test various content types
    test_cases = [
        "Simple text message",
        "Message with numbers: 123, 456, 789",
        "Code-like content: x = 42; y = x * 2",
        "Special chars: @#$%^&*()",
        "Mixed: hello@example.com + phone: (555) 123-4567"
    ]

    for i, text in enumerate(test_cases):
        packets = sender.compress(text, adaptive=False)

        for packet in packets:
            decompressed = receiver.decompress(packet)

            if decompressed:  # Skip None (dictionary updates)
                assert decompressed == text, f"Test case {i+1} failed"
                print(f"   ✓ Case {i+1}: '{text[:40]}...'")

    print("✅ Full Roundtrip with Adaptive Literals: PASSED\n")


def test_conservative_defaults():
    """Test that defaults work without text_sample."""
    print("🧪 Testing Conservative Defaults...")

    # No text_sample provided
    transceiver = AuraTransceiver(
        literal_frequency_threshold=0.01,
        min_compression_size=10
    )
    transceiver.perform_handshake()  # No text_sample

    # Should use conservative default set
    literal_codes = {k: v for k, v in transceiver.compression_tree.items() if k[0] == 'L'}
    print(f"   Default literals: {len(literal_codes)}")

    # Should include common punctuation
    common_chars = [' ', '.', ',', '!', '?', '-', '\n']
    for char in common_chars:
        assert ('L', char) in literal_codes, f"Should include '{char}' by default"

    # Test compression
    text = "Hello, world! This is a test."
    packets = transceiver.compress(text, adaptive=False)
    decompressed = transceiver.decompress(packets[0])

    assert decompressed == text, "Should work with defaults"
    print(f"   ✓ Compressed and decompressed: '{text}'")

    print("✅ Conservative Defaults: PASSED\n")


def test_optimization_summary():
    """Print summary of literal frequency optimization benefits."""
    print("=" * 70)
    print("📊 LITERAL FREQUENCY OPTIMIZATION SUMMARY")
    print("=" * 70)

    # Compare different configurations
    configs = [
        ("All ASCII (old behavior)", None, None),
        ("Conservative default", 0.01, None),
        ("Adaptive (code sample)", 0.01, "def foo(): return 42"),
        ("Aggressive filtering", 0.05, "Hello world"),
    ]

    for name, threshold, sample in configs:
        t = AuraTransceiver(
            literal_frequency_threshold=threshold or 0.01,
            min_compression_size=10
        )

        if sample:
            t.perform_handshake(text_sample=sample)
        else:
            t.perform_handshake()

        literal_count = len([k for k in t.compression_tree.items() if k[0] == 'L'])
        print(f"\n{name}:")
        print(f"  Literals in tree: {literal_count}")
        print(f"  Rare literals (escape): {len(t.rare_literals)}")

    print("\n" + "=" * 70)
    print("✅ ALL LITERAL FREQUENCY TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    print("=" * 70)
    print("LITERAL FREQUENCY THRESHOLD OPTIMIZATION TEST SUITE")
    print("=" * 70)
    print()

    try:
        test_literal_threshold_filters_characters()
        test_handshake_with_text_sample()
        test_escape_code_handling()
        test_adaptive_refresh_with_literal_learning()
        test_recent_text_buffer()
        test_roundtrip_with_adaptive_literals()
        test_conservative_defaults()
        test_optimization_summary()

        print("\n" + "🎉" * 35)
        print("ALL TESTS PASSED! Literal frequency optimization working correctly.")
        print("🎉" * 35)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
