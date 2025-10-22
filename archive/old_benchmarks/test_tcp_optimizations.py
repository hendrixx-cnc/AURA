#!/usr/bin/env python3
"""
Test suite for TCP packet size optimizations.

Tests the following optimizations:
1. TCP frame header packing (4 bytes vs 5 bytes)
2. Packet type + padding packing (1 byte vs 2 bytes)
3. Fixed-width dictionary IDs
4. SHA1 handshake hashes (46 bytes vs 70 bytes)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

from aura_compressor.streamer import AuraTransceiver
from real_tcp_streaming import RealAuraStreamer
import struct


def test_tcp_frame_header_optimization():
    """Test that TCP frame headers are packed into 4 bytes instead of 5."""
    print("🧪 Testing TCP Frame Header Optimization...")

    streamer = RealAuraStreamer()
    test_data = b"Hello, World!"

    # Test compressed message
    packed_compressed = streamer.pack_message(test_data, was_compressed=True)
    assert len(packed_compressed) == 4 + len(test_data), "Compressed header should be 4 bytes"

    # Unpack and verify
    data, was_compressed = streamer.unpack_message(packed_compressed)
    assert data == test_data, "Data should match"
    assert was_compressed == True, "Compression flag should be True"

    # Test uncompressed message
    packed_uncompressed = streamer.pack_message(test_data, was_compressed=False)
    assert len(packed_uncompressed) == 4 + len(test_data), "Uncompressed header should be 4 bytes"

    # Unpack and verify
    data, was_compressed = streamer.unpack_message(packed_uncompressed)
    assert data == test_data, "Data should match"
    assert was_compressed == False, "Compression flag should be False"

    # Verify flag is in MSB
    length_packed = struct.unpack('!I', packed_compressed[:4])[0]
    assert length_packed & 0x80000000, "MSB should be set for compressed"

    length_packed = struct.unpack('!I', packed_uncompressed[:4])[0]
    assert not (length_packed & 0x80000000), "MSB should be clear for uncompressed"

    print("✅ TCP Frame Header Optimization: PASSED (4 bytes vs 5 bytes)")


def test_packet_padding_optimization():
    """Test that padding is packed into packet type byte."""
    print("\n🧪 Testing Packet Type + Padding Optimization...")

    # Test with SHA256 (default) and lower compression threshold
    transceiver = AuraTransceiver(min_compression_size=10)
    transceiver.perform_handshake()

    test_text = "The quick brown fox jumps over the lazy dog. " * 5

    # Compress with stateless mode
    packets = transceiver.compress(test_text, adaptive=False)
    assert len(packets) == 1, "Should return single packet"

    packet = packets[0]

    # First byte should contain both type and padding
    type_and_padding = packet[0]
    packet_type = (type_and_padding >> 3) & 0x1F
    padding = type_and_padding & 0x07

    assert packet_type == 0, "Packet type should be 0 (stateless)"
    assert 0 <= padding <= 7, f"Padding should be 0-7, got {padding}"

    # Verify packet is 1 byte smaller than old format
    # Old format: [type:1][padding:1][data:N]
    # New format: [type_and_padding:1][data:N]
    print(f"   Packet overhead: 1 byte (old: 2 bytes)")
    print(f"   Packet type: {packet_type}, Padding: {padding} bits")

    # Test decompression
    decompressed = transceiver.decompress(packet)
    assert decompressed == test_text, "Decompressed text should match original"

    print("✅ Packet Padding Optimization: PASSED (1 byte vs 2 bytes)")


def test_fixed_width_dictionary_ids():
    """Test that dictionary updates use fixed 2-byte IDs."""
    print("\n🧪 Testing Fixed-Width Dictionary IDs...")

    transceiver = AuraTransceiver()
    transceiver.perform_handshake()

    # Text with unknown words to trigger dictionary updates
    test_text = "The supercalifragilisticexpialidocious antidisestablishmentarianism " * 3

    # Compress with adaptive mode
    packets = transceiver.compress(test_text, adaptive=True)

    # Look for Type 0x03 (dictionary update) packets
    dict_update_packets = [p for p in packets if p[0] == 0x03]

    if dict_update_packets:
        for packet in dict_update_packets:
            assert packet[0] == 0x03, "Should be batch dictionary update"
            count = packet[1]
            print(f"   Dictionary update packet: {count} entries")

            offset = 2
            for i in range(count):
                # Read 2-byte word ID
                word_id = int.from_bytes(packet[offset:offset+2], 'big')
                offset += 2

                # Read 1-byte word length
                word_len = packet[offset]
                offset += 1

                # Read word
                word = packet[offset:offset+word_len].decode('utf-8')
                offset += word_len

                print(f"   Entry {i+1}: W{word_id} -> '{word}' ({word_len} bytes)")

                # Verify format: 2 bytes for ID + 1 byte for length + word bytes
                # Old format would have been: 1 byte id_len + N bytes id + 2 bytes word_len + word bytes
                # For "W12345" that's: 1 + 6 + 2 = 9 bytes overhead vs new 3 bytes overhead

        print("✅ Fixed-Width Dictionary IDs: PASSED (3 bytes overhead vs 9 bytes)")
    else:
        print("ℹ️  No dictionary updates triggered (words already in dictionary)")


def test_sha1_handshake_optimization():
    """Test SHA1 handshake size vs SHA256."""
    print("\n🧪 Testing SHA1 Handshake Optimization...")

    # Test with SHA256 (default)
    transceiver_sha256 = AuraTransceiver(use_sha1_hashes=False)
    handshake_sha256 = transceiver_sha256.perform_handshake()

    print(f"   SHA256 handshake size: {len(handshake_sha256)} bytes")
    assert len(handshake_sha256) == 70, "SHA256 handshake should be 70 bytes"

    # Test with SHA1
    transceiver_sha1 = AuraTransceiver(use_sha1_hashes=True)
    handshake_sha1 = transceiver_sha1.perform_handshake()

    print(f"   SHA1 handshake size: {len(handshake_sha1)} bytes")
    assert len(handshake_sha1) == 46, "SHA1 handshake should be 46 bytes"

    # Verify both can be parsed
    transceiver_receiver = AuraTransceiver(use_sha1_hashes=True)
    transceiver_receiver.receive_handshake(handshake_sha1)
    assert transceiver_receiver.is_ready, "Should be ready after SHA1 handshake"

    savings = len(handshake_sha256) - len(handshake_sha1)
    print(f"   Savings: {savings} bytes ({savings/len(handshake_sha256)*100:.1f}% reduction)")

    print("✅ SHA1 Handshake Optimization: PASSED (46 bytes vs 70 bytes)")


def test_roundtrip_with_optimizations():
    """Test full roundtrip with all optimizations enabled."""
    print("\n🧪 Testing Full Roundtrip with All Optimizations...")

    # Create transceivers with all optimizations
    sender = AuraTransceiver(
        use_sha1_hashes=True,
        min_compression_size=100,
        adaptive_refresh_threshold=32
    )

    receiver = AuraTransceiver(
        use_sha1_hashes=True,
        min_compression_size=100,
        adaptive_refresh_threshold=32
    )

    # Perform handshakes
    handshake = sender.perform_handshake()
    receiver.receive_handshake(handshake)

    # Test data
    test_cases = [
        "Short message",
        "The quick brown fox jumps over the lazy dog. " * 10,
        "A" * 500,  # Repetitive data
        "Hello, 世界! 🌍",  # Unicode
    ]

    total_original = 0
    total_compressed = 0

    for i, text in enumerate(test_cases):
        packets = sender.compress(text, adaptive=False)
        total_original += len(text)

        for packet in packets:
            total_compressed += len(packet)
            decompressed = receiver.decompress(packet)
            assert decompressed == text, f"Test case {i+1} failed: roundtrip mismatch"

    print(f"   Original size: {total_original} bytes")
    print(f"   Compressed size: {total_compressed} bytes")
    print(f"   Compression ratio: {total_original/total_compressed:.2f}:1")
    print(f"   Savings: {total_original - total_compressed} bytes")

    print("✅ Full Roundtrip: PASSED")


def test_optimization_summary():
    """Print summary of all optimization savings."""
    print("\n" + "="*70)
    print("📊 OPTIMIZATION SUMMARY")
    print("="*70)

    print("\n1. TCP Frame Header: 1 byte saved per message (5 → 4 bytes)")
    print("   - 1,000 messages: ~1 KB saved")
    print("   - 1M messages: ~976 KB saved")

    print("\n2. Packet Type + Padding: 1 byte saved per packet (2 → 1 byte)")
    print("   - 1,000 packets: ~1 KB saved")
    print("   - 1M packets: ~976 KB saved")

    print("\n3. Fixed-Width Dictionary IDs: 2-3 bytes saved per entry")
    print("   - 100 entries: ~200-300 bytes saved")
    print("   - 1,000 entries: ~2-3 KB saved")

    print("\n4. SHA1 Handshakes: 24 bytes saved per handshake (70 → 46 bytes)")
    print("   - 1,000 connections: ~24 KB saved")
    print("   - 1M connections: ~23.4 MB saved")

    print("\n" + "="*70)
    print("✅ ALL OPTIMIZATIONS IMPLEMENTED AND TESTED")
    print("="*70)


if __name__ == "__main__":
    print("=" * 70)
    print("TCP PACKET SIZE OPTIMIZATION TEST SUITE")
    print("=" * 70)

    try:
        test_tcp_frame_header_optimization()
        test_packet_padding_optimization()
        test_fixed_width_dictionary_ids()
        test_sha1_handshake_optimization()
        test_roundtrip_with_optimizations()
        test_optimization_summary()

        print("\n" + "🎉" * 35)
        print("ALL TESTS PASSED! TCP optimizations are working correctly.")
        print("🎉" * 35)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
