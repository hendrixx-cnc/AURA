#!/usr/bin/env python3
"""
Debug compression to see what's actually happening with the data.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

from real_tcp_streaming import RealAuraStreamer

def debug_compression():
    """Debug what's happening with compression."""
    
    print("🔍 Debugging AURA Compression")
    print("=" * 40)
    
    streamer = RealAuraStreamer()
    
    # Test data
    test_data = "Machine learning algorithms utilize deep neural networks to analyze complex patterns in large datasets. These sophisticated models employ various techniques including convolutional layers, recurrent connections, and attention mechanisms. " * 20
    
    print(f"Original size: {len(test_data):,} bytes")
    print(f"First 100 chars: {test_data[:100]}...")
    
    # Test compression directly
    compressed_data, was_compressed = streamer.compress_data(test_data)
    
    print(f"\nCompression results:")
    print(f"  Compressed: {was_compressed}")
    print(f"  Original size: {len(test_data):,} bytes")
    print(f"  Compressed size: {len(compressed_data):,} bytes")
    
    if was_compressed and len(compressed_data) < len(test_data):
        ratio = len(test_data) / len(compressed_data)
        print(f"  Compression ratio: {ratio:.3f}:1")
    else:
        print(f"  No effective compression")
    
    # Test the full protocol
    packed_message = streamer.pack_message(compressed_data, was_compressed)
    print(f"\nProtocol overhead:")
    print(f"  Packed size: {len(packed_message):,} bytes")
    print(f"  Protocol overhead: {len(packed_message) - len(compressed_data)} bytes")
    
    # Test decompression
    try:
        unpacked_data, unpacked_compressed = streamer.unpack_message(packed_message)
        decompressed = streamer.decompress_data(unpacked_data, unpacked_compressed)
        
        print(f"\nDecompression:")
        print(f"  Decompressed size: {len(decompressed):,} bytes")
        print(f"  Data integrity: {'✅ OK' if decompressed == test_data else '❌ FAILED'}")
        
    except Exception as e:
        print(f"  ❌ Decompression failed: {e}")
    
    # Test smaller data
    small_data = "Hello world test message"
    print(f"\n🔍 Testing small data:")
    print(f"Original: {len(small_data)} bytes")
    
    small_compressed, small_was_compressed = streamer.compress_data(small_data)
    print(f"Compressed: {small_was_compressed}, Size: {len(small_compressed)} bytes")
    
    if not small_was_compressed:
        print("  ✅ Correctly skipped compression for small data")
    
    # Check compression threshold
    print(f"\nCompression settings:")
    print(f"  Threshold: {streamer.compression_threshold} bytes")
    print(f"  Mode: {streamer.mode}")
    print(f"  Compressor available: {streamer.compressor is not None}")

if __name__ == "__main__":
    debug_compression()