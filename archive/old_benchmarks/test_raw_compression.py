#!/usr/bin/env python3
"""
Test Raw AURA Compression vs Auditable Format

This demonstrates the dramatic difference between:
1. Raw AURA compression (maximum efficiency)
2. Auditable AURA compression (transparency + overhead)
"""
import sys
import os
import time

# Import AURA compression components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

try:
    from aura_compressor.streamer import AuraTransceiver
except ImportError:
    print("❌ AURA modules not available.")
    sys.exit(1)

def test_raw_vs_auditable():
    """Compare raw compression vs auditable format."""
    
    print("🔍 Raw AURA vs Auditable Format Comparison")
    print("=" * 60)
    
    # Initialize compressor
    compressor = AuraTransceiver()
    sample = "Testing raw AURA compression efficiency with neural networks and machine learning algorithms"
    handshake = compressor.perform_handshake(sample)
    print(f"✅ AURA initialized (handshake: {len(handshake)} bytes)")
    
    # Test data of various sizes
    test_cases = [
        ("Tiny", "Hello AURA compression!"),
        ("Small", "Neural network machine learning artificial intelligence deep learning. " * 5),
        ("Medium", "The comprehensive AURA compression system integrates HACS tokenization with Huffman entropy encoding to achieve superior compression ratios for AI-optimized content delivery. " * 20),
        ("Large", "Advanced neural network architectures utilize transformer attention mechanisms for optimal performance in natural language processing tasks with machine learning algorithms and deep learning models. " * 100)
    ]
    
    print("\nComparison Results:")
    print("=" * 60)
    print("Size     | Original | Raw Comp | Raw Ratio | Audit Comp | Audit Ratio | Difference")
    print("-" * 80)
    
    for test_name, test_data in test_cases:
        original_size = len(test_data)
        
        try:
            # Test raw compression
            start_time = time.time()
            raw_compressed = compressor.compress_raw(test_data)
            raw_time = (time.time() - start_time) * 1000
            
            # Test raw decompression
            raw_decompressed = compressor.decompress_raw(raw_compressed)
            raw_integrity = raw_decompressed == test_data
            
            # Test auditable compression
            start_time = time.time()
            audit_compressed = compressor.compress_chunk(test_data)
            audit_time = (time.time() - start_time) * 1000
            
            # Test auditable decompression
            audit_decompressed = compressor.decompress_chunk(audit_compressed)
            audit_integrity = audit_decompressed == test_data
            
            # Calculate metrics
            raw_size = len(raw_compressed)
            audit_size = len(audit_compressed)
            
            raw_ratio = original_size / raw_size if raw_size > 0 else 0
            audit_ratio = original_size / audit_size if audit_size > 0 else 0
            
            difference = audit_size - raw_size
            
            # Format output
            name_str = test_name.ljust(8)
            orig_str = f"{original_size:,}".rjust(8)
            raw_comp_str = f"{raw_size:,}".rjust(8)
            raw_ratio_str = f"{raw_ratio:.3f}".rjust(9)
            audit_comp_str = f"{audit_size:,}".rjust(10)
            audit_ratio_str = f"{audit_ratio:.3f}".rjust(11)
            diff_str = f"+{difference:,}".rjust(10)
            
            print(f"{name_str} | {orig_str} | {raw_comp_str} | {raw_ratio_str} | {audit_comp_str} | {audit_ratio_str} | {diff_str}")
            
            # Show efficiency analysis
            print(f"         └─ Raw: {'✅ COMPRESSES' if raw_ratio > 1.0 else '❌ EXPANDS'} "
                  f"({raw_time:.1f}ms, {'✅' if raw_integrity else '❌'} integrity)")
            print(f"         └─ Audit: {'✅ COMPRESSES' if audit_ratio > 1.0 else '❌ EXPANDS'} "
                  f"({audit_time:.1f}ms, {'✅' if audit_integrity else '❌'} integrity)")
            
            if raw_ratio > 1.0:
                savings = (1 - 1/raw_ratio) * 100
                print(f"         └─ Raw compression: {savings:.1f}% reduction")
            
            if audit_ratio > 1.0:
                savings = (1 - 1/audit_ratio) * 100
                print(f"         └─ Auditable format: {savings:.1f}% reduction")
            else:
                expansion = (audit_ratio - 1) * -100
                print(f"         └─ Auditable format: {expansion:.1f}% expansion")
            
            print()
            
        except Exception as e:
            print(f"{test_name.ljust(8)} | ERROR: {e}")
    
    print("=" * 60)
    print("📊 Key Findings:")
    print("   • Raw AURA compression achieves true compression ratios")
    print("   • Auditable format adds significant overhead for transparency")
    print("   • Raw format ideal for bandwidth-sensitive applications")
    print("   • Auditable format ideal for compliance and transparency")
    
    # Test breakeven point for raw compression
    print(f"\n🎯 Finding Raw Compression Breakeven Point:")
    
    base_pattern = "neural network machine learning AI "
    breakeven_found = False
    
    for size in [50, 100, 200, 500, 1000, 2000]:
        test_content = (base_pattern * (size // len(base_pattern) + 1))[:size]
        actual_size = len(test_content)
        
        try:
            raw_compressed = compressor.compress_raw(test_content)
            raw_ratio = actual_size / len(raw_compressed)
            
            status = "🟢 COMPRESSES" if raw_ratio > 1.0 else "🔴 EXPANDS"
            print(f"   {actual_size:4d} bytes: {raw_ratio:.3f}:1 - {status}")
            
            if raw_ratio > 1.0 and not breakeven_found:
                breakeven_found = True
                print(f"   🎯 Raw compression breakeven at {actual_size} bytes!")
                
        except Exception as e:
            print(f"   {actual_size:4d} bytes: ERROR - {e}")
    
    if not breakeven_found:
        print("   ⚠️ No breakeven found in tested range")

def test_streaming_efficiency():
    """Test which format is better for streaming."""
    
    print(f"\n🌊 Streaming Efficiency Analysis:")
    print("=" * 40)
    
    compressor = AuraTransceiver()
    sample = "Streaming test with neural networks"
    compressor.perform_handshake(sample)
    
    # Simulate streaming messages
    stream_messages = [
        "Status update: neural network training progress 45%",
        "Alert: model accuracy improved to 97.3% on validation set",
        "Data: batch processing 1000 samples with transformer architecture",
        "Info: gradient descent optimization converging after 150 epochs"
    ]
    
    total_original = 0
    total_raw = 0
    total_audit = 0
    
    print("Message Analysis:")
    
    for i, msg in enumerate(stream_messages, 1):
        original_size = len(msg)
        raw_compressed = compressor.compress_raw(msg)
        audit_compressed = compressor.compress_chunk(msg)
        
        raw_size = len(raw_compressed)
        audit_size = len(audit_compressed)
        
        total_original += original_size
        total_raw += raw_size
        total_audit += audit_size
        
        raw_ratio = original_size / raw_size
        audit_ratio = original_size / audit_size
        
        print(f"  Msg {i}: {original_size:3d}b → Raw:{raw_size:3d}b({raw_ratio:.2f}:1) Audit:{audit_size:4d}b({audit_ratio:.3f}:1)")
    
    print(f"\nStream Totals:")
    print(f"  Original:  {total_original:,} bytes")
    print(f"  Raw:       {total_raw:,} bytes ({total_original/total_raw:.3f}:1)")
    print(f"  Auditable: {total_audit:,} bytes ({total_original/total_audit:.3f}:1)")
    
    bandwidth_savings_raw = (1 - total_raw/total_original) * 100
    bandwidth_cost_audit = (total_audit/total_original - 1) * 100
    
    if bandwidth_savings_raw > 0:
        print(f"  Raw format saves {bandwidth_savings_raw:.1f}% bandwidth")
    else:
        print(f"  Raw format uses {-bandwidth_savings_raw:.1f}% extra bandwidth")
        
    print(f"  Auditable format uses {bandwidth_cost_audit:.1f}% extra bandwidth")
    
    print(f"\n💡 Recommendation for Streaming:")
    if total_raw < total_original:
        print("  ✅ Use raw compression for real-time streaming")
    else:
        print("  ⚠️ Consider uncompressed for very small messages")
    print("  📋 Use auditable format for data archival/compliance")

if __name__ == "__main__":
    test_raw_vs_auditable()
    test_streaming_efficiency()