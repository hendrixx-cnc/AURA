#!/usr/bin/env python3
"""
Compare Original vs Server-Side Auditing Approach

This shows the dramatic difference between:
1. Original: Client-side auditable format (embedded audit data)
2. New: Server-side auditing with efficient transmission
"""
import sys
import os
import json

# Import AURA compression components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

try:
    from aura_compressor.streamer import AuraTransceiver
except ImportError:
    print("❌ AURA modules not available.")
    sys.exit(1)

def compare_auditing_approaches():
    """Compare original client-side auditing vs server-side auditing."""
    
    print("🔍 Client-Side vs Server-Side Auditing Comparison")
    print("=" * 60)
    
    # Create two compressors: one regular, one with server-side auditing
    client_compressor = AuraTransceiver()  # Original client-side auditing
    server_compressor = AuraTransceiver(enable_server_audit=True)  # Server-side auditing
    
    sample = "Testing AURA compression auditing approaches with neural networks"
    
    # Initialize both
    client_compressor.perform_handshake(sample)
    server_compressor.perform_handshake(sample)
    
    print("✅ Both compressors initialized")
    
    # Test messages
    test_messages = [
        "Real-time status update from neural network training",
        "Model accuracy improved to 97.5% on validation dataset with transformer architecture",
        "Processing batch 1500 of 2000 with deep learning algorithms and attention mechanisms for optimal performance"
    ]
    
    print(f"\n📊 Transmission Size Comparison:")
    print("-" * 60)
    print("Message | Original | Raw+Server | Client Audit | Difference")
    print("-" * 60)
    
    total_original = 0
    total_raw_server = 0
    total_client_audit = 0
    
    for i, message in enumerate(test_messages, 1):
        original_size = len(message)
        
        # Raw compression with server-side auditing
        raw_compressed = server_compressor.compress_raw(message)
        
        # Original client-side auditable format
        client_audit_compressed = client_compressor.compress_chunk(message)
        
        # Sizes
        raw_size = len(raw_compressed)
        client_audit_size = len(client_audit_compressed)
        
        # Totals
        total_original += original_size
        total_raw_server += raw_size
        total_client_audit += client_audit_size
        
        # Calculate difference
        difference = client_audit_size - raw_size
        savings_pct = (1 - raw_size/client_audit_size) * 100
        
        print(f"Msg {i:2d}  | {original_size:8d} | {raw_size:10d} | {client_audit_size:12d} | -{difference:8d} ({savings_pct:5.1f}%)")
    
    print("-" * 60)
    print(f"TOTAL   | {total_original:8d} | {total_raw_server:10d} | {total_client_audit:12d} | -{total_client_audit-total_raw_server:8d}")
    
    # Calculate overall efficiency
    raw_ratio = total_original / total_raw_server
    client_ratio = total_original / total_client_audit
    bandwidth_improvement = (1 - total_raw_server/total_client_audit) * 100
    
    print(f"\n📈 Efficiency Analysis:")
    print(f"   Raw + Server Audit:  {raw_ratio:.3f}:1 compression")
    print(f"   Client-Side Audit:   {client_ratio:.3f}:1 compression")
    print(f"   Bandwidth Improvement: {bandwidth_improvement:.1f}% by using server-side auditing")
    
    # Show what server-side auditing captured
    print(f"\n🖥️  Server-Side Audit Summary:")
    audit_summary = server_compressor.get_audit_summary()
    stats = audit_summary['statistics']
    
    print(f"   Total compressions: {stats['total_compressions']}")
    print(f"   Original bytes: {stats['total_original_bytes']:,}")
    print(f"   Compressed bytes: {stats['total_compressed_bytes']:,}")
    print(f"   Average ratio: {stats['avg_compression_ratio']:.3f}:1")
    print(f"   Total time: {stats['total_compression_time_ms']:.1f}ms")
    
    # Show sample audit entries
    if audit_summary['recent_entries']:
        print(f"\n📋 Sample Audit Entries:")
        for entry in audit_summary['recent_entries'][-2:]:  # Show last 2
            print(f"   • {entry['timestamp']}: {entry['original_size_bytes']}→{entry['compressed_size_bytes']}b ({entry['compression_ratio']:.3f}:1)")
            print(f"     Content: '{entry['content_sample']}'")
    
    # Demonstrate audit export
    print(f"\n💾 Audit Export Sample:")
    audit_log = server_compressor.export_audit_log()
    audit_data = json.loads(audit_log)
    
    print(f"   Audit metadata: {len(audit_data['audit_entries'])} entries")
    print(f"   Export size: {len(audit_log):,} bytes")
    print(f"   First entry timestamp: {audit_data['audit_entries'][0]['timestamp'] if audit_data['audit_entries'] else 'None'}")
    
    # Compare transmission vs audit overhead
    print(f"\n⚖️  Overhead Analysis:")
    print(f"   Data transmitted: {total_raw_server:,} bytes")
    print(f"   Audit log size: {len(audit_log):,} bytes")
    print(f"   Audit overhead: {(len(audit_log)/total_raw_server)*100:.1f}% (server-side only)")
    print(f"   VS client-side embedding: {((total_client_audit-total_raw_server)/total_raw_server)*100:.1f}% per message")
    
    print(f"\n✅ Conclusion:")
    print(f"   🚀 Server-side auditing: Efficient transmission + complete audit trail")
    print(f"   📊 Client-side auditing: Massive bandwidth waste for audit data")
    print(f"   💡 Server audit happens once, client audit happens per message")

def custom_audit_callback_demo():
    """Demonstrate custom audit callback for real-world usage."""
    
    print(f"\n🔧 Custom Audit Callback Demo:")
    print("=" * 40)
    
    # Custom audit handler that could write to database, file, etc.
    audit_entries = []
    
    def custom_audit_handler(entry):
        """Custom audit handler - could write to DB, send to monitoring, etc."""
        # Add custom fields
        entry['custom_severity'] = 'HIGH' if entry['compression_ratio'] < 1.0 else 'NORMAL'
        entry['custom_efficiency'] = 'POOR' if entry['compression_ratio'] < 1.2 else 'GOOD'
        
        # Store (in real app, this would go to database/monitoring system)
        audit_entries.append(entry)
        
        # Could also send alerts
        if entry['compression_ratio'] < 1.0:
            print(f"   ⚠️  ALERT: Poor compression detected for content starting with '{entry['content_sample'][:30]}...'")
    
    # Create compressor with custom audit callback
    compressor = AuraTransceiver(enable_server_audit=True, audit_callback=custom_audit_handler)
    compressor.perform_handshake("Custom audit demo")
    
    # Test with various content types
    test_cases = [
        "Good compression: neural networks machine learning artificial intelligence",
        "x",  # Poor compression case
        "Medium case with some AI terms and some random text: foo bar baz neural network"
    ]
    
    print("   Testing with custom audit handler...")
    
    for case in test_cases:
        compressed = compressor.compress_raw(case)
        print(f"   • {len(case)}→{len(compressed)}b")
    
    print(f"\n   Custom audit entries captured: {len(audit_entries)}")
    for entry in audit_entries:
        print(f"   • {entry['custom_severity']}: {entry['compression_ratio']:.3f}:1 - {entry['custom_efficiency']}")

if __name__ == "__main__":
    compare_auditing_approaches()
    custom_audit_callback_demo()