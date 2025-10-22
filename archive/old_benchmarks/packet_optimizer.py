#!/usr/bin/env python3
"""
AURA Packet Size Optimizer

This utility helps determine optimal packet sizes for AURA streaming compression
based on content characteristics and performance requirements.
"""
import sys
import os
import time
from typing import Dict, List, Tuple

# Add path for AURA modules when run standalone
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

try:
    from aura_compressor.streamer import AuraTransceiver
except ImportError:
    print("Error: Could not import AURA modules. Please run from correct directory.")
    sys.exit(1)


class AuraPacketOptimizer:
    """
    Utility to analyze and optimize AURA streaming packet sizes.
    """
    
    def __init__(self):
        self.transceiver = None
        self.manifest_overhead = 520  # Approximate fixed overhead in bytes
        
    def initialize(self, sample_text: str = None):
        """Initialize the AURA transceiver with optimal dictionary."""
        if sample_text is None:
            sample_text = "The neural network architecture processes natural language data efficiently using transformer attention mechanisms."
        
        self.transceiver = AuraTransceiver()
        handshake = self.transceiver.perform_handshake(sample_text)
        print(f"📡 AURA transceiver initialized (handshake: {len(handshake):,} bytes)")
        
    def analyze_packet_size(self, content: str) -> Dict:
        """Analyze compression efficiency for a specific packet."""
        if not self.transceiver:
            raise RuntimeError("Transceiver not initialized. Call initialize() first.")
            
        original_size = len(content)
        
        start_time = time.time()
        compressed = self.transceiver.compress_chunk(content)
        compression_time = time.time() - start_time
        
        start_time = time.time()
        decompressed = self.transceiver.decompress_chunk(compressed)
        decompression_time = time.time() - start_time
        
        # Parse compressed data to analyze components
        import json, base64
        chunk_data = json.loads(compressed.decode('utf-8'))
        manifest_raw = chunk_data['manifest']
        if isinstance(manifest_raw, str):
            manifest_size = len(manifest_raw.encode('utf-8'))
        else:
            manifest_size = len(json.dumps(manifest_raw).encode('utf-8'))
        payload_size = len(chunk_data['payload'].encode('utf-8'))
        raw_compressed_size = len(base64.b64decode(chunk_data['payload']))
        
        ratio = original_size / len(compressed)
        raw_ratio = original_size / raw_compressed_size
        
        return {
            'original_size': original_size,
            'compressed_size': len(compressed),
            'manifest_size': manifest_size,
            'payload_size': payload_size,
            'raw_compressed_size': raw_compressed_size,
            'compression_ratio': ratio,
            'raw_compression_ratio': raw_ratio,
            'compression_time': compression_time,
            'decompression_time': decompression_time,
            'shrinks': ratio > 1.0,
            'efficiency_score': ratio if ratio > 1.0 else 1.0 / ratio,
            'content_integrity': abs(len(decompressed) - original_size) < 10
        }
    
    def find_breakeven_point(self, base_pattern: str, max_size: int = 10000) -> int:
        """Find the minimum packet size where compression starts providing benefits."""
        
        pattern_size = len(base_pattern)
        
        for size in range(pattern_size, max_size, pattern_size):
            test_content = base_pattern * (size // pattern_size)
            actual_size = len(test_content)
            
            analysis = self.analyze_packet_size(test_content)
            
            if analysis['shrinks']:
                return actual_size
                
        return -1  # No breakeven found
    
    def optimize_chunk_size(self, content_samples: List[str], target_efficiency: float = 1.2) -> Dict:
        """
        Determine optimal chunk size for given content samples.
        
        Args:
            content_samples: List of representative content strings
            target_efficiency: Minimum compression ratio to achieve
            
        Returns:
            Dictionary with optimization recommendations
        """
        
        results = []
        
        for sample in content_samples:
            # Test different chunk sizes
            base_size = len(sample)
            
            for multiplier in [1, 2, 5, 10, 20, 50]:
                test_content = sample * multiplier
                if len(test_content) > 50000:  # Reasonable upper limit
                    break
                    
                analysis = self.analyze_packet_size(test_content)
                analysis['multiplier'] = multiplier
                analysis['content_type'] = sample[:50] + "..." if len(sample) > 50 else sample
                results.append(analysis)
        
        # Find optimal sizes
        efficient_results = [r for r in results if r['compression_ratio'] >= target_efficiency]
        
        if efficient_results:
            min_efficient_size = min(r['original_size'] for r in efficient_results)
            best_efficiency = max(r['compression_ratio'] for r in efficient_results)
            optimal_result = max(efficient_results, key=lambda x: x['compression_ratio'] / (x['original_size'] / 1000))
        else:
            min_efficient_size = None
            best_efficiency = max(r['compression_ratio'] for r in results)
            optimal_result = max(results, key=lambda x: x['compression_ratio'])
        
        return {
            'min_efficient_size': min_efficient_size,
            'best_efficiency_achieved': best_efficiency,
            'optimal_chunk_size': optimal_result['original_size'],
            'optimal_ratio': optimal_result['compression_ratio'],
            'recommendation': self._generate_recommendation(min_efficient_size, best_efficiency, target_efficiency),
            'all_results': results
        }
    
    def _generate_recommendation(self, min_size: int, best_ratio: float, target: float) -> str:
        """Generate human-readable recommendation."""
        
        if min_size is None:
            return f"❌ Target efficiency {target:.1f}:1 not achievable. Best achieved: {best_ratio:.2f}:1. Consider larger chunks or different content."
        elif min_size < 1000:
            return f"✅ Target achievable at {min_size:,} bytes. Recommend 2-5KB chunks for safety margin."
        elif min_size < 5000:
            return f"⚠️ Target achievable at {min_size:,} bytes. Recommend 5-10KB chunks for optimal performance."
        else:
            return f"⚠️ Large chunks needed ({min_size:,}+ bytes) for target efficiency. Consider content preprocessing."
    
    def generate_report(self, content_samples: List[str]) -> str:
        """Generate a comprehensive packet optimization report."""
        
        if not self.transceiver:
            self.initialize()
        
        report = []
        report.append("AURA Packet Size Optimization Report")
        report.append("=" * 50)
        report.append("")
        
        # Analyze each sample
        for i, sample in enumerate(content_samples):
            report.append(f"📊 Content Sample #{i+1}:")
            report.append(f"   Text: \"{sample[:100]}{'...' if len(sample) > 100 else ''}\"")
            
            analysis = self.analyze_packet_size(sample)
            
            report.append(f"   Size: {analysis['original_size']:,} bytes")
            report.append(f"   Compressed: {analysis['compressed_size']:,} bytes")
            report.append(f"   Ratio: {analysis['compression_ratio']:.3f}:1")
            report.append(f"   Status: {'✅ Shrinks' if analysis['shrinks'] else '❌ Expands'}")
            report.append(f"   Raw compression: {analysis['raw_compression_ratio']:.3f}:1")
            report.append("")
        
        # Overall optimization
        optimization = self.optimize_chunk_size(content_samples)
        
        report.append("🎯 Optimization Results:")
        report.append(f"   Minimum efficient size: {optimization['min_efficient_size'] or 'Not found'}")
        report.append(f"   Best efficiency: {optimization['best_efficiency_achieved']:.3f}:1")
        report.append(f"   Optimal chunk size: {optimization['optimal_chunk_size']:,} bytes")
        report.append(f"   Recommendation: {optimization['recommendation']}")
        report.append("")
        
        # General guidelines
        report.append("📋 General Guidelines:")
        report.append("   • Packets < 1KB: Likely to expand due to manifest overhead")
        report.append("   • Packets 1-5KB: May achieve compression with repetitive content")
        report.append("   • Packets 5-20KB: Good compression for most content types")
        report.append("   • Packets > 20KB: Optimal compression ratios")
        report.append("")
        report.append("💡 Streaming Strategies:")
        report.append("   1. Batch small messages before compression")
        report.append("   2. Use content-aware chunking for mixed data")
        report.append("   3. Monitor compression ratios in real-time")
        report.append("   4. Fall back to raw transmission for tiny packets")
        
        return "\n".join(report)


def main():
    """Demo usage of the packet optimizer."""
    
    # Sample content types for testing
    samples = [
        "Hello world",  # Tiny message
        "The neural network model processes data efficiently. " * 5,  # Small chunk
        "Artificial intelligence and machine learning algorithms utilize deep neural networks to process natural language data through transformer architectures. " * 10,  # Medium chunk
        "The quick brown fox jumps over the lazy dog. " * 50  # Large chunk
    ]
    
    optimizer = AuraPacketOptimizer()
    optimizer.initialize()
    
    print(optimizer.generate_report(samples))
    
    # Test breakeven point for repetitive content
    print("\n🔍 Breakeven Analysis:")
    breakeven = optimizer.find_breakeven_point("the cat sat on the mat. ")
    if breakeven > 0:
        print(f"   Repetitive content breaks even at: {breakeven:,} bytes")
    else:
        print("   No breakeven found for repetitive content")
    
    print("\n✅ Packet optimization analysis complete!")


if __name__ == "__main__":
    main()
