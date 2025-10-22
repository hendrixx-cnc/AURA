#!/usr/bin/env python3
"""
Test Two-Way (Bidirectional) AURA Compression

This verifies that all compression formats support both:
1. Compression (text -> bytes)
2. Decompression (bytes -> text)
With data integrity maintained.
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

def test_bidirectional_compression():
    """Test all compression formats for two-way functionality."""
    
    print("🔄 Two-Way AURA Compression Test")
    print("=" * 50)
    
    # Initialize compressor
    compressor = AuraTransceiver(enable_server_audit=True)
    sample = "Testing bidirectional compression with neural networks and machine learning"
    handshake = compressor.perform_handshake(sample)
    print(f"✅ AURA initialized (handshake: {len(handshake)} bytes)")
    
    # Test data of various complexities
    test_cases = [
        ("Simple", "Hello AURA!"),
        ("AI Terms", "neural network machine learning artificial intelligence deep learning transformer"),
        ("Mixed", "The AI model achieved 97.3% accuracy using transformer architecture with 12.8B parameters"),
        ("Long", "Comprehensive analysis of neural network architectures reveals that transformer attention mechanisms combined with residual connections and layer normalization provide optimal performance for natural language processing tasks in large-scale machine learning applications. " * 3)
    ]
    
    print(f"\n🧪 Testing All Compression Formats:")
    print("-" * 80)
    print("Format      | Test     | Original | Compressed | Ratio   | Time | Integrity")
    print("-" * 80)
    
    formats_tested = 0
    formats_passed = 0
    
    for test_name, test_data in test_cases:
        original_size = len(test_data)
        
        # Test 1: Raw Compression
        try:
            start_time = time.time()
            raw_compressed = compressor.compress_raw(test_data)
            raw_time = (time.time() - start_time) * 1000
            
            raw_decompressed = compressor.decompress_raw(raw_compressed)
            raw_integrity = raw_decompressed == test_data
            raw_ratio = original_size / len(raw_compressed)
            
            formats_tested += 1
            if raw_integrity:
                formats_passed += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"Raw         | {test_name:<8} | {original_size:8d} | {len(raw_compressed):10d} | {raw_ratio:7.3f} | {raw_time:4.1f} | {status}")
            
        except Exception as e:
            print(f"Raw         | {test_name:<8} | {original_size:8d} | ERROR: {e}")
        
        # Test 2: Traceable Compression
        try:
            start_time = time.time()
            traceable_compressed = compressor.compress_traceable(test_data)
            traceable_time = (time.time() - start_time) * 1000
            
            traceable_decompressed, metadata = compressor.decompress_traceable(traceable_compressed)
            traceable_integrity = traceable_decompressed == test_data
            traceable_ratio = original_size / len(traceable_compressed)
            
            formats_tested += 1
            if traceable_integrity:
                formats_passed += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"Traceable   | {test_name:<8} | {original_size:8d} | {len(traceable_compressed):10d} | {traceable_ratio:7.3f} | {traceable_time:4.1f} | {status}")
            
        except Exception as e:
            print(f"Traceable   | {test_name:<8} | {original_size:8d} | ERROR: {e}")
        
        # Test 3: Original Auditable Format (Client-side audit)
        try:
            start_time = time.time()
            auditable_compressed = compressor.compress_chunk(test_data)
            auditable_time = (time.time() - start_time) * 1000
            
            auditable_decompressed = compressor.decompress_chunk(auditable_compressed)
            auditable_integrity = auditable_decompressed == test_data
            auditable_ratio = original_size / len(auditable_compressed)
            
            formats_tested += 1
            if auditable_integrity:
                formats_passed += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"Auditable   | {test_name:<8} | {original_size:8d} | {len(auditable_compressed):10d} | {auditable_ratio:7.3f} | {auditable_time:4.1f} | {status}")
            
        except Exception as e:
            print(f"Auditable   | {test_name:<8} | {original_size:8d} | ERROR: {e}")
        
        print("-" * 80)
    
    print(f"\n📊 Two-Way Compression Summary:")
    print(f"   Formats tested: {formats_tested}")
    print(f"   Formats passed: {formats_passed}")
    print(f"   Success rate: {(formats_passed/formats_tested)*100:.1f}%")
    
    if formats_passed == formats_tested:
        print("   ✅ All formats support bidirectional compression!")
    else:
        print("   ❌ Some formats failed bidirectional testing")

def test_cross_compatibility():
    """Test if data compressed on one instance can be decompressed on another."""
    
    print(f"\n🔗 Cross-Instance Compatibility Test:")
    print("=" * 50)
    
    # Create two separate compressor instances
    compressor_a = AuraTransceiver()
    compressor_b = AuraTransceiver()
    
    # Use same handshake data to ensure compatibility
    sample = "Cross-instance compression test with neural networks"
    handshake_a = compressor_a.perform_handshake(sample)
    handshake_b = compressor_b.perform_handshake(sample)
    
    print(f"✅ Two independent compressors initialized")
    print(f"   Compressor A handshake: {len(handshake_a)} bytes")
    print(f"   Compressor B handshake: {len(handshake_b)} bytes")
    
    test_message = "Cross-instance test: machine learning algorithms with transformer attention mechanisms"
    
    # Test A->B compatibility
    print(f"\n🧪 A compresses, B decompresses:")
    
    try:
        # Compress with A
        compressed_by_a = compressor_a.compress_raw(test_message)
        print(f"   A compressed: {len(test_message)} → {len(compressed_by_a)} bytes")
        
        # Decompress with B
        decompressed_by_b = compressor_b.decompress_raw(compressed_by_a)
        a_to_b_success = decompressed_by_b == test_message
        
        print(f"   B decompressed: {len(decompressed_by_b)} bytes")
        print(f"   Integrity: {'✅ PASS' if a_to_b_success else '❌ FAIL'}")
        
        if a_to_b_success:
            print(f"   Content match: '{decompressed_by_b[:50]}{'...' if len(decompressed_by_b) > 50 else ''}'")
        else:
            print(f"   Original:  '{test_message[:50]}'")
            print(f"   Got:       '{decompressed_by_b[:50]}'")
            
    except Exception as e:
        print(f"   ❌ A->B failed: {e}")
        a_to_b_success = False
    
    # Test B->A compatibility
    print(f"\n🧪 B compresses, A decompresses:")
    
    try:
        # Compress with B
        compressed_by_b = compressor_b.compress_raw(test_message)
        print(f"   B compressed: {len(test_message)} → {len(compressed_by_b)} bytes")
        
        # Decompress with A
        decompressed_by_a = compressor_a.decompress_raw(compressed_by_b)
        b_to_a_success = decompressed_by_a == test_message
        
        print(f"   A decompressed: {len(decompressed_by_a)} bytes")
        print(f"   Integrity: {'✅ PASS' if b_to_a_success else '❌ FAIL'}")
        
        if b_to_a_success:
            print(f"   Content match: '{decompressed_by_a[:50]}{'...' if len(decompressed_by_a) > 50 else ''}'")
        else:
            print(f"   Original:  '{test_message[:50]}'")
            print(f"   Got:       '{decompressed_by_a[:50]}'")
            
    except Exception as e:
        print(f"   ❌ B->A failed: {e}")
        b_to_a_success = False
    
    print(f"\n🔗 Cross-Compatibility Results:")
    if a_to_b_success and b_to_a_success:
        print("   ✅ Perfect cross-instance compatibility!")
        print("   💡 Data compressed by any instance can be decompressed by any other")
    elif a_to_b_success or b_to_a_success:
        print("   ⚠️ Partial compatibility - one direction works")
    else:
        print("   ❌ No cross-compatibility - instances cannot share compressed data")

def test_streaming_scenario():
    """Test bidirectional compression in a streaming scenario."""
    
    print(f"\n🌊 Streaming Scenario Test:")
    print("=" * 40)
    
    # Simulate client and server
    client = AuraTransceiver(enable_server_audit=False)  # Client doesn't need audit
    server = AuraTransceiver(enable_server_audit=True)   # Server does auditing
    
    # Both use same handshake
    handshake_data = "Streaming test with bidirectional AURA compression"
    client.perform_handshake(handshake_data)
    server.perform_handshake(handshake_data)
    
    print("✅ Client and server initialized")
    
    # Simulate bidirectional message exchange
    messages = [
        ("Client→Server", "REQUEST: Get neural network training status"),
        ("Server→Client", "RESPONSE: Training 85% complete, accuracy 94.7%"),
        ("Client→Server", "REQUEST: Update learning rate to 0.001"),
        ("Server→Client", "RESPONSE: Learning rate updated successfully"),
    ]
    
    print(f"\n📡 Bidirectional Message Exchange:")
    
    total_original = 0
    total_compressed = 0
    all_successful = True
    
    for direction, message in messages:
        original_size = len(message)
        
        try:
            if "Client→Server" in direction:
                # Client compresses, server decompresses
                compressed = client.compress_raw(message)
                decompressed = server.decompress_raw(compressed)
                compressor_name = "Client"
            else:
                # Server compresses, client decompresses
                compressed = server.compress_raw(message)
                decompressed = client.decompress_raw(compressed)
                compressor_name = "Server"
            
            compressed_size = len(compressed)
            ratio = original_size / compressed_size
            integrity = decompressed == message
            
            if not integrity:
                all_successful = False
            
            total_original += original_size
            total_compressed += compressed_size
            
            status = "✅" if integrity else "❌"
            print(f"   {direction}: {original_size}→{compressed_size}b ({ratio:.3f}:1) {status}")
            
        except Exception as e:
            print(f"   {direction}: ❌ ERROR - {e}")
            all_successful = False
    
    overall_ratio = total_original / total_compressed if total_compressed > 0 else 0
    
    print(f"\n📊 Streaming Results:")
    print(f"   Total data: {total_original} → {total_compressed} bytes")
    print(f"   Overall ratio: {overall_ratio:.3f}:1")
    print(f"   All messages: {'✅ SUCCESS' if all_successful else '❌ FAILED'}")
    
    if all_successful:
        print("   🎉 Bidirectional streaming works perfectly!")
    else:
        print("   ⚠️ Some streaming messages failed")
    
    # Show server audit of the streaming session
    audit_summary = server.get_audit_summary()
    print(f"\n📋 Server Audit Summary:")
    print(f"   Messages processed: {audit_summary['statistics']['total_compressions']}")
    print(f"   Average compression: {audit_summary['statistics']['avg_compression_ratio']:.3f}:1")

if __name__ == "__main__":
    test_bidirectional_compression()
    test_cross_compatibility() 
    test_streaming_scenario()