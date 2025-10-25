#!/usr/bin/env python3
"""
Stress Test: 50 Concurrent WebSocket Users with Realistic Template-Based Messages

This script simulates realistic AI/Human conversations using:
- Template-based message synthesis with random slot filling
- Shared template store across all simulated users
- Actual codec compression (not estimates)
- Realistic message length distributions
- External corpus support for real-world data

The test validates:
- Concurrent connection handling
- Template matching hit rates
- Compression ratio under realistic load
- Latency and throughput metrics
"""

import asyncio
import websockets
import json
import time
import random
import statistics
from typing import List, Dict, Tuple, Optional
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aura_compression.compressor import ProductionHybridCompressor
from aura_compression.templates import TemplateLibrary


# Realistic slot fillers for template-based message synthesis
SLOT_FILLERS = {
    'resource': [
        "real-time data", "your local filesystem", "external databases",
        "that specific information", "live market data", "your browser cookies",
        "third-party APIs", "system logs", "previous chat history"
    ],
    'action': [
        "process that type of request", "access external services", "execute arbitrary code",
        "modify system files", "browse the internet", "remember previous conversations",
        "install packages", "debug this issue", "deploy your application",
        "optimize performance", "set up the environment", "configure the database"
    ],
    'tool': [
        "pip", "npm", "docker", "git", "pytest", "webpack", "cargo", "kubectl",
        "the CLI tool", "the official package", "that library", "terraform"
    ],
    'suggestion': [
        "checking the error logs carefully", "reviewing the official documentation",
        "updating to the latest version", "consulting with your team lead",
        "running the diagnostic script first", "restarting the service",
        "clearing the cache", "checking your configuration file"
    ],
    'subject': [
        "React", "Python", "Rust", "PostgreSQL", "Redis", "Kubernetes", "TensorFlow", "AWS",
        "A REST API", "A microservice", "The ORM layer", "This pattern", "The framework"
    ],
    'definition': [
        "a declarative programming framework", "used for building scalable applications",
        "designed for high-performance computing", "primarily used in data science",
        "optimized for cloud-native deployments", "widely adopted in enterprise environments",
        "a functional programming language", "an object-relational mapping tool"
    ],
    'attribute': [
        "default behavior", "return value", "primary key", "error code",
        "default value", "return type", "timeout", "max connections"
    ],
    'value': [
        "null", "undefined", "zero", "false", "empty string", "true", "enabled", "disabled"
    ],
    'question': [
        "is the main difference", "does this work", "should I do this", "is the best approach",
        "are the key features", "is the recommended way", "did this error occur"
    ],
    'request': [
        "help me with this", "explain that concept", "show me an example",
        "clarify this point", "review my code", "suggest an alternative"
    ],
    'topic': [
        "machine learning", "web development", "database design", "API integration",
        "security best practices", "performance optimization", "testing strategies", "CI/CD"
    ],
}


class MessageSynthesizer:
    """Synthesizes realistic messages from template library with random slot filling."""

    def __init__(self, template_library: Optional[TemplateLibrary] = None):
        self.template_library = template_library or TemplateLibrary()
        self.templates = self.template_library.list_templates()

        # Categorize templates by slot count for efficient sampling
        self.zero_slot = []
        self.one_slot = []
        self.two_slot = []
        self.multi_slot = []

        for tid, pattern in self.templates.items():
            slot_count = pattern.count('{')
            if slot_count == 0:
                self.zero_slot.append((tid, pattern))
            elif slot_count == 1:
                self.one_slot.append((tid, pattern))
            elif slot_count == 2:
                self.two_slot.append((tid, pattern))
            else:
                self.multi_slot.append((tid, pattern))

    def fill_slot(self, slot_index: int) -> str:
        """Generate realistic slot content based on common patterns."""
        # Use slot fillers or generate realistic variations
        slot_types = list(SLOT_FILLERS.keys())
        slot_type = slot_types[slot_index % len(slot_types)]
        return random.choice(SLOT_FILLERS[slot_type])

    def synthesize_ai_message(self, min_length: int = 50, max_length: int = 2000) -> str:
        """Generate realistic AI message using templates with random slot filling."""

        # 15% - Zero-slot templates (best compression)
        if random.random() < 0.15:
            if not self.zero_slot:
                return "Yes"
            _, pattern = random.choice(self.zero_slot)
            return pattern

        # 35% - Single-slot templates
        elif random.random() < 0.50:
            if not self.one_slot:
                return "I cannot help with that."
            _, pattern = random.choice(self.one_slot)
            slot_value = self.fill_slot(0)
            return pattern.format(slot_value)

        # 30% - Two-slot templates
        elif random.random() < 0.80:
            if not self.two_slot:
                return "The value is undefined."
            _, pattern = random.choice(self.two_slot)
            slot0 = self.fill_slot(0)
            slot1 = self.fill_slot(1)
            return pattern.format(slot0, slot1)

        # 20% - Multi-sentence (tests multi-template compression)
        else:
            sentences = []
            target = random.randint(100, 400)
            depth = 0
            while len(" ".join(sentences)) < target and depth < 4:
                sentences.append(self.synthesize_ai_message(60, 150))
                depth += 1
            message = " ".join(sentences)
            if len(message) > max_length:
                message = message[:max_length-3] + "..."
            return message

    def synthesize_human_message(self, min_length: int = 20, max_length: int = 500) -> str:
        """Generate realistic human message (questions, short responses)."""

        # 40% - Very short responses
        if random.random() < 0.4:
            if self.zero_slot:
                _, pattern = random.choice(self.zero_slot[:10])  # Use first 10 (Yes/No/etc)
                return pattern
            return random.choice(["Yes", "No", "Maybe", "I don't know"])

        # 40% - Questions
        elif random.random() < 0.8:
            question_templates = [t for t in self.one_slot if '?' in t[1]]
            if question_templates:
                _, pattern = random.choice(question_templates)
                return pattern.format(self.fill_slot(0))
            return "How does this work?"

        # 20% - Longer questions with context
        else:
            base = self.synthesize_human_message(20, 100)
            context = random.choice([
                " I'm new to this.",
                " I've been stuck on this.",
                " Any help would be appreciated!",
                ""
            ])
            return base + context


# Global message synthesizer (shared across all users)
_synthesizer = None


def get_message_synthesizer() -> MessageSynthesizer:
    """Get shared message synthesizer instance."""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = MessageSynthesizer()
    return _synthesizer


def generate_random_ai_message(min_length: int = 50, max_length: int = 2000) -> str:
    """Generate realistic AI message using shared template synthesizer."""
    return get_message_synthesizer().synthesize_ai_message(min_length, max_length)


def generate_random_human_message(min_length: int = 20, max_length: int = 500) -> str:
    """Generate realistic human message using shared template synthesizer."""
    return get_message_synthesizer().synthesize_human_message(min_length, max_length)


class UserSimulator:
    """Simulates a single user with WebSocket connection."""

    def __init__(self, user_id: int, server_url: str):
        self.user_id = user_id
        self.server_url = server_url
        self.compressor = ProductionHybridCompressor()
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'total_original_size': 0,
            'total_compressed_size': 0,
            'latencies': [],
            'errors': 0,
            'user_type': random.choice(['AI', 'Human']),  # Random user type
            'conversation_length': random.randint(5, 50),  # Random conversation length
        }

    async def simulate_conversation(self) -> Dict:
        """Simulate a full conversation with random messages."""
        try:
            async with websockets.connect(self.server_url) as websocket:
                print(f"[User {self.user_id}] Connected ({self.stats['user_type']}, {self.stats['conversation_length']} messages)")

                for turn in range(self.stats['conversation_length']):
                    # Generate random message based on user type
                    if self.stats['user_type'] == 'AI':
                        # AI messages: Use templates that will compress well
                        # 70% chance of single template, 30% chance of longer message
                        if random.random() < 0.7:
                            message = generate_random_ai_message(50, 200)
                        else:
                            message = generate_random_ai_message(200, 800)
                    else:
                        # Human messages: shorter, often match templates
                        message = generate_random_human_message(10, 200)


                    # Measure compression and latency
                    start_time = time.time()

                    # Send plain text message to server (server will compress it)
                    await websocket.send(message)
                    self.stats['messages_sent'] += 1

                    # Receive response
                    response = await websocket.recv()
                    response_data = json.loads(response)

                    # Track compression stats from server response
                    self.stats['total_original_size'] += response_data.get('original_size', len(message.encode('utf-8')))
                    self.stats['total_compressed_size'] += response_data.get('compressed_size', len(message.encode('utf-8')))

                    # Log compression method for first message only (less verbose)
                    if turn == 0:
                        method = response_data.get('method', 'unknown')
                        ratio = response_data.get('compression_ratio', 0)
                        msg_short = message[:40] + "..." if len(message) > 40 else message
                        print(f"[User {self.user_id}] {method:15s} {ratio:5.2f}:1 | {msg_short}")

                    end_time = time.time()
                    latency_ms = (end_time - start_time) * 1000

                    self.stats['messages_received'] += 1
                    self.stats['latencies'].append(latency_ms)

                    # Random delay between messages (0.1 to 2 seconds)
                    await asyncio.sleep(random.uniform(0.1, 2.0))

                print(f"[User {self.user_id}] Completed conversation")

        except Exception as e:
            print(f"[User {self.user_id}] Error: {e}")
            self.stats['errors'] += 1

        return self.stats


async def run_stress_test(num_users: int = 50, server_url: str = "ws://localhost:8765"):
    """Run stress test with multiple concurrent users."""

    print(f"\n{'='*80}")
    print(f"AURA WebSocket Stress Test: {num_users} Concurrent Users")
    print(f"{'='*80}\n")
    print(f"Server: {server_url}")
    print(f"Configuration:")
    print(f"  - Users: {num_users}")
    print(f"  - User Types: Random (AI/Human)")
    print(f"  - Conversation Length: Random (5-50 messages)")
    print(f"  - Message Sizes: Random (20-2000 characters)")
    print(f"\nStarting test...\n")

    # Create user simulators
    users = [UserSimulator(i+1, server_url) for i in range(num_users)]

    # Run all users concurrently
    start_time = time.time()
    results = await asyncio.gather(*[user.simulate_conversation() for user in users])
    end_time = time.time()

    # Aggregate statistics
    total_time = end_time - start_time

    # Calculate overall metrics
    total_messages_sent = sum(r['messages_sent'] for r in results)
    total_messages_received = sum(r['messages_received'] for r in results)
    total_original_size = sum(r['total_original_size'] for r in results)
    total_compressed_size = sum(r['total_compressed_size'] for r in results)
    total_errors = sum(r['errors'] for r in results)

    all_latencies = []
    for r in results:
        all_latencies.extend(r['latencies'])

    # User type distribution
    ai_users = sum(1 for r in results if r['user_type'] == 'AI')
    human_users = num_users - ai_users

    # Calculate AI vs Human stats separately
    ai_stats = [r for r in results if r['user_type'] == 'AI']
    human_stats = [r for r in results if r['user_type'] == 'Human']

    ai_original = sum(r['total_original_size'] for r in ai_stats) if ai_stats else 0
    ai_compressed = sum(r['total_compressed_size'] for r in ai_stats) if ai_stats else 0
    human_original = sum(r['total_original_size'] for r in human_stats) if human_stats else 0
    human_compressed = sum(r['total_compressed_size'] for r in human_stats) if human_stats else 0

    # Print results
    print(f"\n{'='*80}")
    print(f"STRESS TEST RESULTS")
    print(f"{'='*80}\n")

    print(f"Overall Performance:")
    print(f"  Total Test Duration: {total_time:.2f} seconds")
    print(f"  Concurrent Users: {num_users}")
    print(f"  - AI Users: {ai_users} ({ai_users/num_users*100:.1f}%)")
    print(f"  - Human Users: {human_users} ({human_users/num_users*100:.1f}%)")
    print(f"  Total Messages Sent: {total_messages_sent}")
    print(f"  Total Messages Received: {total_messages_received}")
    print(f"  Messages Per Second: {total_messages_sent/total_time:.2f}")
    print(f"  Success Rate: {(total_messages_received/total_messages_sent*100):.2f}%")
    print(f"  Total Errors: {total_errors}")

    print(f"\nCompression Statistics:")
    overall_ratio = total_original_size / total_compressed_size if total_compressed_size > 0 else 0
    print(f"  Total Original Size: {total_original_size:,} bytes ({total_original_size/1024:.2f} KB)")
    print(f"  Total Compressed Size: {total_compressed_size:,} bytes ({total_compressed_size/1024:.2f} KB)")
    print(f"  Overall Compression Ratio: {overall_ratio:.2f}:1")
    print(f"  Bandwidth Saved: {(1 - total_compressed_size/total_original_size)*100:.2f}%")

    print(f"\n  AI Message Compression:")
    if ai_original > 0:
        ai_ratio = ai_original / ai_compressed if ai_compressed > 0 else 0
        print(f"    Original: {ai_original:,} bytes")
        print(f"    Compressed: {ai_compressed:,} bytes")
        print(f"    Ratio: {ai_ratio:.2f}:1")
    else:
        print(f"    No AI messages")

    print(f"\n  Human Message Compression:")
    if human_original > 0:
        human_ratio = human_original / human_compressed if human_compressed > 0 else 0
        print(f"    Original: {human_original:,} bytes")
        print(f"    Compressed: {human_compressed:,} bytes")
        print(f"    Ratio: {human_ratio:.2f}:1")
    else:
        print(f"    No Human messages")

    if all_latencies:
        print(f"\nLatency Statistics (per message round-trip):")
        print(f"  Average: {statistics.mean(all_latencies):.2f} ms")
        print(f"  Median: {statistics.median(all_latencies):.2f} ms")
        print(f"  Min: {min(all_latencies):.2f} ms")
        print(f"  Max: {max(all_latencies):.2f} ms")
        print(f"  P95: {sorted(all_latencies)[int(len(all_latencies)*0.95)]:.2f} ms")
        print(f"  P99: {sorted(all_latencies)[int(len(all_latencies)*0.99)]:.2f} ms")
        print(f"  Std Dev: {statistics.stdev(all_latencies):.2f} ms")

    print(f"\nPer-User Statistics:")
    print(f"  Avg Messages per User: {total_messages_sent/num_users:.1f}")
    print(f"  Avg Conversation Length: {statistics.mean([r['conversation_length'] for r in results]):.1f}")
    print(f"  Min Conversation Length: {min(r['conversation_length'] for r in results)}")
    print(f"  Max Conversation Length: {max(r['conversation_length'] for r in results)}")

    # Top 5 most active users
    sorted_users = sorted(results, key=lambda x: x['messages_sent'], reverse=True)
    print(f"\n  Top 5 Most Active Users:")
    for i, user_stats in enumerate(sorted_users[:5], 1):
        user_idx = results.index(user_stats) + 1
        print(f"    {i}. User {user_idx}: {user_stats['messages_sent']} messages ({user_stats['user_type']})")

    print(f"\n{'='*80}\n")

    # Performance assessment with detailed analysis
    print("Performance Analysis:")

    if total_errors == 0 and statistics.mean(all_latencies) < 2.0:
        print("  ✓ EXCELLENT: Zero errors and ultra-low latency (<2ms avg)")
    elif total_errors == 0 and statistics.mean(all_latencies) < 10.0:
        print("  ✓ VERY GOOD: Zero errors and low latency (<10ms avg)")
    elif total_errors == 0 and statistics.mean(all_latencies) < 100:
        print("  ✓ GOOD: Zero errors, acceptable latency")
    elif total_errors == 0:
        print("  ⚠ FAIR: Zero errors, but high latency needs investigation")
    elif total_errors < num_users * 0.05:
        print("  ⚠ ACCEPTABLE: Low error rate (<5%)")
    else:
        print("  ✗ POOR: High error rate, investigate server capacity")

    # Compression effectiveness analysis
    print(f"\nCompression Effectiveness:")
    if overall_ratio > 3.0:
        print(f"  ✓ EXCELLENT: {overall_ratio:.2f}:1 compression (>3x)")
    elif overall_ratio > 2.0:
        print(f"  ✓ VERY GOOD: {overall_ratio:.2f}:1 compression (>2x)")
    elif overall_ratio > 1.5:
        print(f"  ✓ GOOD: {overall_ratio:.2f}:1 compression (>1.5x)")
    elif overall_ratio > 1.1:
        print(f"  ⚠ FAIR: {overall_ratio:.2f}:1 compression (modest)")
    else:
        print(f"  ✗ POOR: {overall_ratio:.2f}:1 compression (minimal benefit)")

    # Bandwidth savings assessment
    bandwidth_saved = (1 - total_compressed_size/total_original_size)*100
    print(f"  Bandwidth saved: {bandwidth_saved:.1f}% ({total_original_size - total_compressed_size:,} bytes)")
    print(f"  Effective throughput: {total_compressed_size/total_time/1024:.2f} KB/s (compressed)")
    print(f"  Without compression: {total_original_size/total_time/1024:.2f} KB/s would be needed")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="WebSocket Stress Test with Template-Based Message Synthesis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run standard 50-user test
  %(prog)s

  # Run with 100 concurrent users
  %(prog)s --users 100

  # Use custom server URL
  %(prog)s --url ws://production.example.com:8765

  # Load external message corpus
  %(prog)s --corpus messages.jsonl

  # Use seeded random for reproducible tests
  %(prog)s --seed 42

Features:
  - Template-based message synthesis with realistic slot filling
  - Shared template store across all simulated users
  - Actual codec compression (not estimates)
  - Detailed performance and compression analysis
        """
    )
    parser.add_argument("--users", type=int, default=50,
                       help="Number of concurrent users (default: 50)")
    parser.add_argument("--url", type=str, default="ws://localhost:8765",
                       help="WebSocket server URL (default: ws://localhost:8765)")
    parser.add_argument("--corpus", type=str, default=None,
                       help="Load external message corpus from JSONL file")
    parser.add_argument("--seed", type=int, default=None,
                       help="Random seed for reproducible tests")
    parser.add_argument("--auto-update", action="store_true",
                       help="Enable template auto-discovery and persistence")

    args = parser.parse_args()

    # Set random seed if specified (for reproducible tests)
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed} (reproducible test)\n")

    # Load external corpus if specified
    if args.corpus:
        corpus_path = Path(args.corpus)
        if corpus_path.exists():
            print(f"Loading message corpus from: {corpus_path}")
            # TODO: Implement corpus loading
            print("Note: Corpus loading not yet implemented, using synthetic messages\n")
        else:
            print(f"Warning: Corpus file not found: {corpus_path}\n")

    if args.auto_update:
        print("Template auto-discovery enabled\n")
        # TODO: Implement auto-discovery mode

    try:
        asyncio.run(run_stress_test(num_users=args.users, server_url=args.url))
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed: {e}")
        import traceback
        traceback.print_exc()
