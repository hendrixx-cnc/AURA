#!/usr/bin/env python3
"""
Extended breakeven test - test much larger sizes to see if AURA ever compresses.
"""
import sys
import os
import time
import json
import socket
import base64
import hashlib
import struct
import threading

# Import AURA compression components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

try:
    from aura_compressor.streamer import AuraTransceiver
except ImportError:
    print("Warning: AURA modules not available.")
    AuraTransceiver = None

def test_large_sizes():
    """Test very large message sizes to find compression breakeven."""
    
    if not AuraTransceiver:
        print("❌ AURA not available")
        return
    
    print("🔍 Extended AURA Compression Breakeven Test")
    print("Testing MUCH larger sizes...")
    print("=" * 60)
    
    # Initialize compressor
    compressor = AuraTransceiver()
    sample = "neural network machine learning artificial intelligence deep learning transformer attention mechanism "
    handshake = compressor.perform_handshake(sample)
    print(f"✅ AURA initialized (handshake: {len(handshake)} bytes)")
    
    # Test very large sizes
    test_sizes = [
        20_000,   # 20KB
        50_000,   # 50KB
        100_000,  # 100KB
        200_000,  # 200KB
        500_000,  # 500KB
        1_000_000 # 1MB
    ]
    
    base_pattern = "The artificial intelligence neural network utilizes advanced machine learning algorithms with deep learning architectures and transformer attention mechanisms for optimal natural language processing performance. "
    
    print("Size      | Original | Compressed | Ratio   | Time (ms) | Status")
    print("-" * 70)
    
    breakeven_found = False
    
    for size in test_sizes:
        # Create test content
        pattern_reps = (size // len(base_pattern)) + 1
        test_content = (base_pattern * pattern_reps)[:size]
        actual_size = len(test_content)
        
        try:
            # Test compression
            start_time = time.time()
            compressed = compressor.compress_chunk(test_content)
            compression_time = (time.time() - start_time) * 1000
            
            compressed_size = len(compressed)
            ratio = actual_size / compressed_size if compressed_size > 0 else 0
            
            # Format output
            size_str = f"{actual_size:,}".rjust(8)
            orig_str = f"{actual_size:,}".rjust(8)
            comp_str = f"{compressed_size:,}".rjust(10)
            ratio_str = f"{ratio:.3f}".rjust(7)
            time_str = f"{compression_time:.1f}".rjust(9)
            
            if ratio > 1.0:
                status = "🟢 COMPRESSES"
                if not breakeven_found:
                    breakeven_found = True
                    print(f"🎯 FIRST COMPRESSION AT {actual_size:,} bytes!")
            else:
                status = "🔴 EXPANDS"
            
            print(f"{size_str} | {orig_str} | {comp_str} | {ratio_str} | {time_str} | {status}")
            
            # Show compression efficiency details
            if ratio > 1.0:
                savings = (1 - 1/ratio) * 100
                print(f"         └─ {savings:.1f}% reduction achieved!")
            else:
                expansion = (ratio - 1) * -100
                overhead = compressed_size - actual_size
                print(f"         └─ {expansion:.1f}% expansion (+{overhead:,} bytes overhead)")
            
        except Exception as e:
            print(f"{size_str} | ERROR: {e}")
        
        print()  # Empty line for readability
    
    print("=" * 70)
    if breakeven_found:
        print("✅ Compression breakeven found at large message sizes!")
    else:
        print("❌ No compression achieved even at 1MB - auditable format overhead too high")
        print("💡 Raw AURA compression (without JSON manifest) would likely compress much sooner")
    
    # Analyze the overhead
    print(f"\n🔍 Overhead Analysis:")
    
    # Test tiny message to see base overhead
    tiny_msg = "test"
    tiny_compressed = compressor.compress_chunk(tiny_msg)
    base_overhead = len(tiny_compressed) - len(tiny_msg)
    
    print(f"   Base overhead: {base_overhead:,} bytes")
    print(f"   For 1KB message: {(base_overhead/1024)*100:.1f}% overhead")
    print(f"   For 10KB message: {(base_overhead/10240)*100:.1f}% overhead")
    print(f"   For 100KB message: {(base_overhead/102400)*100:.1f}% overhead")
    
    print(f"\n💡 Recommendation:")
    print(f"   - Use raw AURA compression for smaller messages")
    print(f"   - Reserve auditable format for large data transfers")
    print(f"   - Consider hybrid approach based on message size")

if __name__ == "__main__":
    test_large_sizes()