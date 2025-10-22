#!/usr/bin/env python3
"""
Test small data handling and compression threshold
Validates that small data is not expanded by compression overhead
"""
import sys
import os

# Add the package src to the path
sys.path.insert(0, 'packages/aura-compressor-py/src')
from aura_compressor.streamer import AuraTransceiver

def test_small_data_sizes():
    """Test compression/bypass behavior for various small data sizes"""
    print("=== Testing Small Data Handling ===\n")

    # Test different sizes around the threshold
    test_cases = [
        ("Tiny", "Hello, world!", 13),
        ("Small", "The quick brown fox jumps over the lazy dog.", 45),
        ("Medium", "The quick brown fox jumps over the lazy dog. " * 2, 90),
        ("Threshold-1", "x" * 199, 199),
        ("Threshold", "x" * 200, 200),
        ("Threshold+1", "x" * 201, 201),
        ("Above", "The quick brown fox jumps over the lazy dog. " * 10, 450),
    ]

    results = []

    for name, text, expected_size in test_cases:
        print(f"📊 Testing '{name}' ({len(text)} bytes)...")

        try:
            # Create fresh transceivers
            server = AuraTransceiver(min_compression_size=200)
            client = AuraTransceiver(min_compression_size=200)

            # Perform handshake
            handshake_packet = server.perform_handshake()
            client.receive_handshake(handshake_packet)

            # Compress
            compressed_packets = server.compress(text, adaptive=False)
            compressed = compressed_packets[0]

            # Decompress
            decompressed = client.decompress(compressed)

            # Check packet type
            packet_type = compressed[0]
            packet_type_name = "UNCOMPRESSED (0xFF)" if packet_type == 0xFF else f"COMPRESSED (0x{packet_type:02X})"

            # Calculate metrics
            original_size = len(text)
            compressed_size = len(compressed)
            ratio = original_size / compressed_size if compressed_size > 0 else 0

            # Verify correctness
            is_correct = decompressed == text
            is_beneficial = compressed_size <= original_size + 1  # Allow 1 byte for packet type

            result = {
                'name': name,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'packet_type': packet_type_name,
                'ratio': ratio,
                'is_correct': is_correct,
                'is_beneficial': is_beneficial,
                'expansion': compressed_size - original_size
            }

            results.append(result)

            status = "✅" if is_correct and is_beneficial else "❌"
            print(f"   {status} Original: {original_size} bytes")
            print(f"   {status} Compressed: {compressed_size} bytes")
            print(f"   {status} Packet type: {packet_type_name}")
            print(f"   {status} Ratio: {ratio:.2f}:1")
            print(f"   {status} Expansion: {result['expansion']:+d} bytes")
            print(f"   {status} Correct: {is_correct}")
            print(f"   {status} Beneficial: {is_beneficial}")
            print()

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            print()

    return results

def test_threshold_configuration():
    """Test different threshold configurations"""
    print("\n=== Testing Threshold Configuration ===\n")

    test_text = "x" * 150  # 150 bytes

    thresholds = [50, 100, 200, 300]

    for threshold in thresholds:
        print(f"📊 Testing with threshold={threshold} bytes...")

        server = AuraTransceiver(min_compression_size=threshold)
        client = AuraTransceiver(min_compression_size=threshold)

        handshake = server.perform_handshake()
        client.receive_handshake(handshake)

        compressed = server.compress(test_text, adaptive=False)[0]
        packet_type = compressed[0]

        should_compress = len(test_text) >= threshold
        is_compressed = packet_type != 0xFF

        status = "✅" if is_compressed == should_compress else "❌"
        action = "COMPRESSED" if is_compressed else "UNCOMPRESSED"

        print(f"   {status} Text: {len(test_text)} bytes")
        print(f"   {status} Threshold: {threshold} bytes")
        print(f"   {status} Expected: {'COMPRESS' if should_compress else 'BYPASS'}")
        print(f"   {status} Actual: {action}")
        print(f"   {status} Packet size: {len(compressed)} bytes")
        print()

def test_edge_cases():
    """Test edge cases like empty strings and special characters"""
    print("\n=== Testing Edge Cases ===\n")

    edge_cases = [
        ("Empty", ""),
        ("Single char", "x"),
        ("Unicode", "Hello 世界 🌍"),
        ("Special chars", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
        ("Whitespace", "   \n\t\r   "),
        ("Numbers", "1234567890" * 5),
    ]

    for name, text in edge_cases:
        print(f"📊 Testing '{name}': '{text[:30]}{'...' if len(text) > 30 else ''}'")

        try:
            server = AuraTransceiver(min_compression_size=200)
            client = AuraTransceiver(min_compression_size=200)

            handshake = server.perform_handshake()
            client.receive_handshake(handshake)

            compressed = server.compress(text, adaptive=False)[0]
            decompressed = client.decompress(compressed)

            is_correct = decompressed == text
            packet_type = compressed[0]

            status = "✅" if is_correct else "❌"
            print(f"   {status} Size: {len(text)} bytes → {len(compressed)} bytes")
            print(f"   {status} Packet type: 0x{packet_type:02X}")
            print(f"   {status} Roundtrip correct: {is_correct}")
            print()

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            print()

def main():
    print("🚀 AURA Small Data Handling Tests\n")

    # Test 1: Various small data sizes
    size_results = test_small_data_sizes()

    # Test 2: Different threshold configurations
    test_threshold_configuration()

    # Test 3: Edge cases
    test_edge_cases()

    # Final summary
    print("\n" + "="*60)
    print("📋 FINAL SUMMARY")
    print("="*60)

    if size_results:
        print(f"✅ Size tests completed for {len(size_results)} test cases")

        # Check if small data was handled correctly
        small_data_tests = [r for r in size_results if r['original_size'] < 200]
        correct_handling = all(r['packet_type'] == "UNCOMPRESSED (0xFF)" for r in small_data_tests)

        if correct_handling:
            print(f"✅ All data under 200 bytes was sent uncompressed (no expansion)")
        else:
            print(f"❌ Some small data was compressed (causing expansion)")

        # Check if large data was compressed
        large_data_tests = [r for r in size_results if r['original_size'] >= 200]
        if large_data_tests:
            compressed_count = sum(1 for r in large_data_tests if r['packet_type'].startswith("COMPRESSED"))
            print(f"✅ {compressed_count}/{len(large_data_tests)} data over 200 bytes was compressed")

        # Check correctness
        all_correct = all(r['is_correct'] for r in size_results)
        if all_correct:
            print(f"✅ All roundtrip compression/decompression tests passed")
        else:
            print(f"❌ Some roundtrip tests failed")

    print(f"\n🎉 Small data handling tests completed!")

if __name__ == "__main__":
    main()
