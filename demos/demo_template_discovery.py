#!/usr/bin/env python3
"""
AURA Template Discovery Demo
Demonstrates automatic template learning from AI response corpus.

Copyright (c) 2025 Todd Hendricks
Patent Pending
"""

import sys
import os

# Add package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                'packages/aura-compressor-py/src'))

from aura_compressor.lib.template_discovery import TemplateDiscovery
from aura_compressor.lib.template_manager import TemplateManager


def demo_automatic_discovery():
    """Demonstrate automatic template discovery"""

    print("=" * 70)
    print("AURA AUTOMATIC TEMPLATE DISCOVERY DEMO")
    print("Patent-Pending Technology")
    print("=" * 70)

    # Sample AI response corpus (simulating real AI assistant responses)
    sample_responses = [
        "I don't have access to real-time information.",
        "I don't have access to your personal files.",
        "I don't have access to the internet.",
        "I don't have access to your location data.",
        "I don't have access to external databases.",

        "I cannot execute code because I'm a text-based AI.",
        "I cannot access your camera because I lack hardware access.",
        "I cannot make purchases because I don't have payment capabilities.",
        "I cannot browse websites because I'm not connected to the internet.",

        "As an AI, I cannot feel emotions.",
        "As an AI, I cannot make phone calls.",
        "As an AI, I cannot physically interact with objects.",
        "As an AI assistant, I cannot access confidential data.",

        "You can improve performance by optimizing your code.",
        "You can save money by using caching strategies.",
        "You can increase security by enabling two-factor authentication.",
        "You can reduce latency by using a CDN.",

        "To install the package, you need to run pip install.",
        "To enable the feature, you need to set the configuration flag.",
        "To access the API, you need to obtain an API key.",
        "To debug the issue, you need to check the error logs.",

        "Error: File not found.",
        "Error: Permission denied.",
        "Error: Connection timeout.",
        "Error: Invalid credentials.",

        "The compression ratio is 3.5:1.",
        "The execution time is 245ms.",
        "The file size is 1.2MB.",
        "The success rate is 98.7%.",
    ]

    print(f"\n📊 Sample Corpus: {len(sample_responses)} AI responses")
    print("\nSample responses:")
    for i, resp in enumerate(sample_responses[:5], 1):
        print(f"  {i}. {resp}")
    print("  ...")

    # Initialize discovery engine
    print("\n🔬 Initializing Template Discovery Engine...")
    discovery = TemplateDiscovery(
        min_occurrences=3,
        min_compression_ratio=2.0,
        min_confidence=0.7
    )

    # Add responses to corpus
    print("📥 Adding responses to corpus...")
    for response in sample_responses:
        discovery.add_response(response)

    # Run discovery
    print("\n🔍 Running automatic template discovery...")
    print("   Algorithms: N-gram analysis, Similarity clustering, Regex patterns, Prefix/suffix matching")

    candidates = discovery.discover_templates()

    # Display results
    print(f"\n✓ Discovery Complete!")
    print(f"   Found {len(candidates)} viable templates\n")

    print("=" * 70)
    print("DISCOVERED TEMPLATES")
    print("=" * 70)

    for i, candidate in enumerate(candidates[:10], 1):  # Top 10
        print(f"\n#{i} Template (Category: {candidate.category})")
        print(f"   Pattern: {candidate.pattern}")
        print(f"   Occurrences: {candidate.occurrences}")
        print(f"   Compression Ratio: {candidate.compression_ratio:.2f}:1")
        print(f"   Confidence: {candidate.confidence:.2f}")
        print(f"   Examples:")
        for ex in candidate.examples[:2]:
            print(f"     - {ex}")

    # Show statistics
    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)

    stats = {
        'total_templates': len(candidates),
        'total_responses': len(sample_responses),
        'avg_compression_ratio': sum(c.compression_ratio for c in candidates) / max(1, len(candidates)),
        'total_pattern_matches': sum(c.occurrences for c in candidates),
        'coverage': sum(c.occurrences for c in candidates) / len(sample_responses) * 100,
    }

    print(f"   Total Responses Analyzed: {stats['total_responses']}")
    print(f"   Templates Discovered: {stats['total_templates']}")
    print(f"   Avg Compression Ratio: {stats['avg_compression_ratio']:.2f}:1")
    print(f"   Total Pattern Matches: {stats['total_pattern_matches']}")
    print(f"   Corpus Coverage: {stats['coverage']:.1f}%")

    # Demonstrate template manager integration
    print("\n" + "=" * 70)
    print("TEMPLATE MANAGER INTEGRATION")
    print("=" * 70)

    manager = TemplateManager(auto_update=True)

    print("\n🔄 Adding discovered templates to active library...")

    for i, candidate in enumerate(candidates[:5]):  # Add top 5
        success = manager.add_template(
            template_id=100 + i,  # Use high IDs to avoid conflicts
            pattern=candidate.pattern,
            category=candidate.category,
            confidence=candidate.confidence
        )
        if success:
            print(f"   ✓ Added: {candidate.pattern}")

    # Test matching
    print("\n🧪 Testing template matching...")
    test_responses = [
        "I don't have access to your calendar.",
        "You can enhance security by using encryption.",
        "Error: Database connection failed.",
    ]

    for test in test_responses:
        match = manager.match_template(test)
        if match:
            template_id, slot_values = match
            template = manager.templates[template_id]
            print(f"\n   Input: {test}")
            print(f"   ✓ Matched Template: {template.pattern}")
            print(f"     Slots: {slot_values}")

            # Calculate savings
            original_bytes = len(test.encode('utf-8'))
            compressed_bytes = 2 + sum(len(s.encode('utf-8')) + 2 for s in slot_values)
            ratio = original_bytes / compressed_bytes
            savings = (1 - compressed_bytes / original_bytes) * 100

            print(f"     Original: {original_bytes} bytes")
            print(f"     Compressed: {compressed_bytes} bytes")
            print(f"     Ratio: {ratio:.2f}:1")
            print(f"     Savings: {savings:.1f}%")
        else:
            print(f"\n   Input: {test}")
            print(f"   ✗ No template match")

    print("\n" + "=" * 70)
    print("PATENT-PENDING INNOVATIONS DEMONSTRATED")
    print("=" * 70)
    print("""
✓ Automatic template discovery from unstructured AI response corpus
✓ Statistical pattern detection (N-gram, clustering, regex, prefix/suffix)
✓ Candidate validation based on compression ratio and confidence
✓ Runtime performance tracking and optimization
✓ Dynamic template library management with promotion/demotion
✓ Self-learning system that improves over time

This technology is covered by USPTO provisional patent application.
All rights reserved. Copyright (c) 2025 Todd Hendricks.
    """)

    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    demo_automatic_discovery()
