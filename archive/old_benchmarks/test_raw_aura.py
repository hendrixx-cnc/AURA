#!/usr/bin/env python3
"""
Test AURA compression directly to see actual compression ratios.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

from aura_compressor.streamer import AuraTransceiver

def test_raw_aura_compression():
    """Test raw AURA compression without network protocol overhead."""
    
    print("🔍 Testing Raw AURA Compression")
    print("=" * 40)
    
    compressor = AuraTransceiver()
    
    # Initialize with sample
    sample = "Machine learning artificial intelligence neural networks deep learning data processing"
    handshake = compressor.perform_handshake(sample)
    print(f"Handshake size: {len(handshake):,} bytes")
    
    # Test different data types
    test_cases = [
        ("Short", "Hello world"),
        ("Repetitive", "the cat sat on the mat. " * 50),
        ("AI Terms", "neural network machine learning artificial intelligence deep learning transformer attention " * 30),
        ("Natural Language", "The artificial intelligence system processes natural language data using advanced neural network architectures with transformer attention mechanisms. " * 25),
        ("Mixed Content", "In 2024, AI models achieved 95.7% accuracy on benchmark tests. The neural networks utilized 12.8B parameters across 48 transformer layers with 16-head attention mechanisms. Performance metrics showed 99.2% uptime with 0.003ms latency." * 20)
    ]
    
    for name, data in test_cases:
        print(f"\n📊 {name}:")
        print(f"  Original: {len(data):,} bytes")
        
        try:
            # Raw AURA compression
            compressed = compressor.compress_chunk(data)
            decompressed = compressor.decompress_chunk(compressed)
            
            ratio = len(data) / len(compressed)
            print(f"  Compressed: {len(compressed):,} bytes")
            print(f"  Ratio: {ratio:.3f}:1")
            
            if ratio > 1.0:
                print(f"  ✅ Compression effective ({(1 - 1/ratio)*100:.1f}% reduction)")
            else:
                print(f"  ❌ Expansion ({(ratio - 1)*100:.1f}% increase)")
            
            # Check integrity
            if decompressed == data:
                print(f"  ✅ Data integrity verified")
            else:
                print(f"  ❌ Data corruption detected")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n📋 Analysis:")
    print(f"  - AURA uses HACS tokenization + Huffman encoding")
    print(f"  - Effectiveness depends on vocabulary overlap with HACS dictionary")
    print(f"  - AI/ML terms should compress well (in HACS vocabulary)")
    print(f"  - Natural language should show moderate compression")
    print(f"  - Random/numeric data may expand due to manifest overhead")

if __name__ == "__main__":
    test_raw_aura_compression()