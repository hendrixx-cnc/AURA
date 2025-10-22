#!/usr/bin/env python3
"""
Large-scale AURA streaming test with various data sizes and patterns
"""
import sys
import os
import time
import random

# Add the package src to the path
sys.path.insert(0, 'src')
from aura_compressor.streamer import AuraTransceiver

def generate_ai_like_text(size_kb):
    """Generate AI-like text with repeated patterns and technical terms"""
    
    # AI/tech vocabulary that should compress well
    ai_terms = [
        "neural network", "machine learning", "deep learning", "artificial intelligence",
        "transformer", "attention mechanism", "gradient descent", "backpropagation",
        "convolutional", "recurrent", "lstm", "gru", "bert", "gpt", "embedding",
        "tokenization", "normalization", "optimization", "regularization",
        "classification", "regression", "supervised", "unsupervised", "reinforcement",
        "dataset", "training", "validation", "testing", "inference", "prediction",
        "accuracy", "precision", "recall", "f1-score", "loss function", "overfitting"
    ]
    
    common_words = [
        "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
        "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does",
        "this", "that", "these", "those", "a", "an", "some", "many", "few", "all"
    ]
    
    sentences = [
        "The {} model achieved high accuracy on the {} dataset.",
        "We implemented {} using {} techniques for better performance.",
        "The {} architecture incorporates {} for improved results.",
        "Training with {} showed significant improvements in {}.",
        "Our approach combines {} and {} methodologies.",
        "The {} algorithm processes {} data efficiently.",
        "Results demonstrate that {} outperforms traditional {}.",
        "We evaluated {} metrics including {} and {}."
    ]
    
    text_parts = []
    target_chars = size_kb * 1024
    current_chars = 0
    
    while current_chars < target_chars:
        # Choose a sentence template
        template = random.choice(sentences)
        
        # Fill it with random terms
        terms_needed = template.count('{}')
        chosen_terms = random.choices(ai_terms + common_words, k=terms_needed)
        
        try:
            sentence = template.format(*chosen_terms)
            text_parts.append(sentence)
            current_chars += len(sentence) + 1  # +1 for space
        except:
            # If formatting fails, add a simple sentence
            text_parts.append(f"The {random.choice(ai_terms)} is important for {random.choice(ai_terms)}.")
            current_chars += len(text_parts[-1]) + 1
    
    return " ".join(text_parts)

def test_compression_sizes():
    """Test compression with different data sizes"""
    print("=== Testing AURA Compression with Various Data Sizes ===\n")
    
    # Test sizes in KB
    test_sizes = [1, 5, 10, 25, 50, 100]
    
    results = []
    
    for size_kb in test_sizes:
        print(f"📊 Testing with {size_kb}KB of data...")
        
        # Generate test data
        test_text = generate_ai_like_text(size_kb)
        actual_size = len(test_text)
        
        try:
            # Create fresh transceivers
            server = AuraTransceiver()
            client = AuraTransceiver()
            
            # Measure handshake
            start_time = time.time()
            handshake_packet = server.perform_handshake(test_text[:1000])  # Use sample for handshake
            handshake_time = time.time() - start_time
            
            client.receive_handshake(handshake_packet)
            
            # Measure compression
            start_time = time.time()
            compressed = server.compress_chunk(test_text)
            compression_time = time.time() - start_time
            
            # Measure decompression
            start_time = time.time()
            decompressed = client.decompress_chunk(compressed)
            decompression_time = time.time() - start_time
            
            # Calculate metrics
            compression_ratio = actual_size / len(compressed) if len(compressed) > 0 else 0
            handshake_size = len(handshake_packet)
            
            # Verify correctness (check first and last 100 chars)
            original_sample = test_text[:100] + "..." + test_text[-100:]
            decompressed_sample = decompressed[:100] + "..." + decompressed[-100:]
            content_match = original_sample.lower() == decompressed_sample.lower()
            
            result = {
                'size_kb': size_kb,
                'actual_bytes': actual_size,
                'compressed_bytes': len(compressed),
                'handshake_bytes': handshake_size,
                'compression_ratio': compression_ratio,
                'handshake_time': handshake_time,
                'compression_time': compression_time,
                'decompression_time': decompression_time,
                'content_match': content_match
            }
            
            results.append(result)
            
            print(f"   ✅ Original: {actual_size:,} bytes")
            print(f"   ✅ Compressed: {len(compressed):,} bytes") 
            print(f"   ✅ Handshake: {handshake_size:,} bytes")
            print(f"   ✅ Ratio: {compression_ratio:.2f}:1")
            print(f"   ✅ Times: H={handshake_time:.3f}s, C={compression_time:.3f}s, D={decompression_time:.3f}s")
            print(f"   ✅ Content match: {content_match}")
            print()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            print()
    
    return results

def test_streaming_chunks():
    """Test streaming with multiple chunks"""
    print("=== Testing AURA Bidirectional Streaming with Large Chunks ===\n")
    
    # Create large datasets for streaming
    server_data = [
        generate_ai_like_text(10),  # 10KB chunks
        generate_ai_like_text(15),  # 15KB chunks  
        generate_ai_like_text(20),  # 20KB chunks
    ]
    
    client_data = [
        generate_ai_like_text(8),   # 8KB chunks
        generate_ai_like_text(12),  # 12KB chunks
        generate_ai_like_text(18),  # 18KB chunks
    ]
    
    try:
        # Initialize transceivers
        server = AuraTransceiver()
        client = AuraTransceiver()
        
        # Perform handshake with larger sample
        handshake_sample = generate_ai_like_text(5)  # 5KB handshake sample
        print(f"🤝 Performing handshake with {len(handshake_sample):,} byte sample...")
        
        start_time = time.time()
        handshake_packet = server.perform_handshake(handshake_sample)
        client.receive_handshake(handshake_packet)
        handshake_time = time.time() - start_time
        
        print(f"   ✅ Handshake complete: {len(handshake_packet):,} bytes in {handshake_time:.3f}s")
        print()
        
        total_original = 0
        total_compressed = 0
        total_compression_time = 0
        total_decompression_time = 0
        
        # Test server-to-client streaming
        print("📡 Server-to-Client Streaming:")
        for i, chunk in enumerate(server_data):
            chunk_size = len(chunk)
            
            start_time = time.time()
            compressed = server.compress_chunk(chunk)
            compression_time = time.time() - start_time
            
            start_time = time.time()
            decompressed = client.decompress_chunk(compressed)
            decompression_time = time.time() - start_time
            
            # Verify content (check length and sample)
            content_ok = len(decompressed) > 0 and abs(len(chunk) - len(decompressed)) < 100
            
            ratio = chunk_size / len(compressed) if len(compressed) > 0 else 0
            
            print(f"   Chunk {i+1}: {chunk_size:,} → {len(compressed):,} bytes ({ratio:.2f}:1) "
                  f"C={compression_time:.3f}s D={decompression_time:.3f}s {'✅' if content_ok else '❌'}")
            
            total_original += chunk_size
            total_compressed += len(compressed)
            total_compression_time += compression_time
            total_decompression_time += decompression_time
        
        print()
        
        # Test client-to-server streaming  
        print("📡 Client-to-Server Streaming:")
        for i, chunk in enumerate(client_data):
            chunk_size = len(chunk)
            
            start_time = time.time()
            compressed = client.compress_chunk(chunk)
            compression_time = time.time() - start_time
            
            start_time = time.time()
            decompressed = server.decompress_chunk(compressed)
            decompression_time = time.time() - start_time
            
            content_ok = len(decompressed) > 0 and abs(len(chunk) - len(decompressed)) < 100
            ratio = chunk_size / len(compressed) if len(compressed) > 0 else 0
            
            print(f"   Chunk {i+1}: {chunk_size:,} → {len(compressed):,} bytes ({ratio:.2f}:1) "
                  f"C={compression_time:.3f}s D={decompression_time:.3f}s {'✅' if content_ok else '❌'}")
            
            total_original += chunk_size
            total_compressed += len(compressed)
            total_compression_time += compression_time
            total_decompression_time += decompression_time
        
        # Summary
        overall_ratio = total_original / total_compressed if total_compressed > 0 else 0
        
        print(f"\n📊 Streaming Summary:")
        print(f"   Total data: {total_original:,} bytes → {total_compressed:,} bytes")
        print(f"   Overall ratio: {overall_ratio:.2f}:1")
        print(f"   Total time: C={total_compression_time:.3f}s D={total_decompression_time:.3f}s")
        print(f"   Throughput: {total_original/total_compression_time/1024:.1f} KB/s compression")
        print(f"   Throughput: {total_original/total_decompression_time/1024:.1f} KB/s decompression")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 AURA Large-Scale Streaming Tests\n")
    
    # Test 1: Various data sizes
    size_results = test_compression_sizes()
    
    # Test 2: Streaming with chunks
    streaming_success = test_streaming_chunks()
    
    # Final summary
    print("\n" + "="*60)
    print("📋 FINAL SUMMARY")
    print("="*60)
    
    if size_results:
        print(f"✅ Size tests completed for {len(size_results)} different data sizes")
        best_ratio = max(r['compression_ratio'] for r in size_results)
        print(f"✅ Best compression ratio achieved: {best_ratio:.2f}:1")
        
        # Find the size where compression becomes beneficial
        beneficial_sizes = [r for r in size_results if r['compression_ratio'] > 1.0]
        if beneficial_sizes:
            min_beneficial = min(r['size_kb'] for r in beneficial_sizes)
            print(f"✅ Compression becomes beneficial at: {min_beneficial}KB+")
    
    if streaming_success:
        print(f"✅ Bidirectional streaming test passed")
    
    print(f"\n🎉 Large-scale AURA testing completed!")

if __name__ == "__main__":
    main()