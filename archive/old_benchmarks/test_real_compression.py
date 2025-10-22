#!/usr/bin/env python3
"""
Test real streaming with larger, more realistic data to verify compression works.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

from real_tcp_streaming import RealStreamingBenchmark
import logging

def test_compression_effectiveness():
    """Test with realistic data sizes to verify compression works."""
    
    print("🔍 Testing AURA Compression Effectiveness Over Real Network")
    print("=" * 60)
    
    # Create realistic data samples
    test_samples = {
        "Tiny (50 bytes)": "This is a small message for testing purposes.",
        
        "Small (500 bytes)": "The artificial intelligence system processes natural language data using advanced neural network architectures with transformer attention mechanisms. " * 5,
        
        "Medium (2KB)": "Machine learning algorithms utilize deep neural networks to analyze complex patterns in large datasets. These sophisticated models employ various techniques including convolutional layers, recurrent connections, and attention mechanisms to achieve state-of-the-art performance on challenging tasks such as natural language processing, computer vision, and speech recognition. " * 10,
        
        "Large (10KB)": "In the rapidly evolving field of artificial intelligence, researchers and practitioners continuously develop innovative approaches to enhance model performance and efficiency. Deep learning frameworks enable the construction of complex neural architectures that can learn hierarchical representations from raw data. These models demonstrate remarkable capabilities across diverse domains including natural language understanding, image recognition, autonomous systems, and predictive analytics. The integration of attention mechanisms, residual connections, and advanced optimization techniques has led to significant breakthroughs in model accuracy and computational efficiency. " * 50,
        
        "Very Large (50KB)": "The comprehensive analysis of machine learning systems reveals intricate relationships between model architecture, training methodologies, and performance outcomes. Advanced neural networks incorporate sophisticated mechanisms such as multi-head attention, layer normalization, dropout regularization, and residual connections to achieve optimal learning dynamics. These architectural innovations enable models to capture complex dependencies in high-dimensional data while maintaining computational tractability. The careful balance between model capacity and generalization capability requires thorough understanding of statistical learning theory, optimization landscapes, and regularization techniques. " * 200
    }
    
    benchmark = RealStreamingBenchmark()
    
    for test_name, data in test_samples.items():
        print(f"\n📊 Testing {test_name}:")
        print(f"   Content size: {len(data):,} bytes")
        
        try:
            # Test with single message
            results = benchmark.benchmark_tcp([data], concurrent_clients=1)
            
            if 'error' not in results and results['individual_results']:
                result = results['individual_results'][0]
                print(f"   Latency: {result['avg_latency']:.2f} ms")
                print(f"   Throughput: {result['throughput']:.4f} Mbps")
                print(f"   Messages processed: {result['messages_processed']}")
                
                # Check if compression actually happened
                if result['compression_ratio'] > 1.0:
                    print(f"   ✅ Compression: {result['compression_ratio']:.2f}:1")
                else:
                    print(f"   ❌ No compression (1.00:1)")
            else:
                print(f"   ❌ Test failed: {results.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📈 Summary:")
    print("- Tiny messages: Expected to expand due to protocol overhead")
    print("- Small messages: May compress if repetitive content")
    print("- Medium+ messages: Should show compression benefits")
    print("- Very large messages: Best compression ratios expected")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise
    test_compression_effectiveness()