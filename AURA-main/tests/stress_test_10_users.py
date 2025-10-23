"""
AURA Compression - 10 Concurrent Users Stress Test
Tests AI-to-AI and Human-to-AI communication patterns

Copyright (c) 2025 Todd James Hendricks
Licensed under Apache License 2.0
Patent Pending - Application No. 19/366,538
"""

import asyncio
import websockets
import time
import statistics
from typing import List, Dict, Tuple
import random
import json

# Test message datasets
AI_MESSAGES = [
    "I cannot browse the internet.",
    "I don't have access to real-time information.",
    "I'm unable to execute code on your computer.",
    "I cannot access external databases.",
    "I don't have the ability to send emails.",
    "I'm not able to make phone calls.",
    "I cannot access your file system directly.",
    "I don't have access to your camera or microphone.",
    "I'm unable to modify system settings.",
    "I cannot interact with other applications on your device.",
    "The capital of France is Paris.",
    "Python is a high-level programming language.",
    "The population of Earth is approximately 8 billion people.",
    "Machine learning is a subset of artificial intelligence.",
    "The speed of light is approximately 299,792 kilometers per second.",
    "Water boils at 100 degrees Celsius at sea level.",
    "The human body has 206 bones.",
    "DNA stands for Deoxyribonucleic Acid.",
    "The largest ocean on Earth is the Pacific Ocean.",
    "Photosynthesis is the process by which plants convert sunlight into energy.",
]

HUMAN_MESSAGES = [
    "How do I install Python on Windows?",
    "Can you help me debug this code?",
    "What's the weather like today?",
    "Tell me a joke!",
    "How do I reset my password?",
    "What are the best practices for data security?",
    "Can you recommend a good book?",
    "How does machine learning work?",
    "What's the difference between AI and ML?",
    "Help me write a resume.",
    "I need help with my homework.",
    "What's the capital of Japan?",
    "How do I learn to code?",
    "Can you translate this to Spanish?",
    "What's the meaning of life?",
    "How do I fix my computer?",
    "What are some healthy recipes?",
    "How do I get better at math?",
    "Can you explain quantum physics?",
    "What should I do this weekend?",
]

MIXED_CONVERSATIONS = [
    ("What can you do?", "I can help you with a variety of tasks including answering questions, writing code, and providing explanations."),
    ("Can you browse the web?", "I cannot browse the internet."),
    ("What's 2+2?", "The answer is 4."),
    ("Help me learn Python", "I'd be happy to help you learn Python. What specific aspect would you like to start with?"),
    ("Write me a poem", "I cannot write creative content without more specific guidance."),
]


class UserSimulator:
    """Simulates a single user's interaction with the WebSocket server"""

    def __init__(self, user_id: int, user_type: str, num_messages: int = 20):
        self.user_id = user_id
        self.user_type = user_type  # "ai", "human", or "mixed"
        self.num_messages = num_messages
        self.latencies = []
        self.compression_ratios = []
        self.methods_used = []
        self.errors = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0

    async def run(self, uri: str) -> Dict:
        """Run the user simulation"""
        try:
            async with websockets.connect(uri) as websocket:
                for i in range(self.num_messages):
                    # Select message based on user type
                    if self.user_type == "ai":
                        message = random.choice(AI_MESSAGES)
                    elif self.user_type == "human":
                        message = random.choice(HUMAN_MESSAGES)
                    else:  # mixed
                        if random.random() < 0.5:
                            message = random.choice(HUMAN_MESSAGES)
                        else:
                            message = random.choice(AI_MESSAGES)

                    # Send message and measure latency
                    start_time = time.time()
                    await websocket.send(message)
                    self.total_bytes_sent += len(message.encode('utf-8'))

                    # Receive response
                    response = await websocket.recv()
                    end_time = time.time()

                    latency = (end_time - start_time) * 1000  # Convert to ms
                    self.latencies.append(latency)
                    self.total_bytes_received += len(response)

                    # Try to parse response for metadata
                    try:
                        data = json.loads(response) if response.startswith('{') else {}
                        if 'compression_ratio' in data:
                            self.compression_ratios.append(data['compression_ratio'])
                        if 'method' in data:
                            self.methods_used.append(data['method'])
                    except:
                        pass

                    # Random delay between messages (10-500ms)
                    await asyncio.sleep(random.uniform(0.01, 0.5))

        except Exception as e:
            self.errors += 1
            print(f"User {self.user_id} error: {e}")

        return self.get_stats()

    def get_stats(self) -> Dict:
        """Get statistics for this user"""
        return {
            'user_id': self.user_id,
            'user_type': self.user_type,
            'messages_sent': self.num_messages,
            'errors': self.errors,
            'avg_latency_ms': statistics.mean(self.latencies) if self.latencies else 0,
            'min_latency_ms': min(self.latencies) if self.latencies else 0,
            'max_latency_ms': max(self.latencies) if self.latencies else 0,
            'p50_latency_ms': statistics.median(self.latencies) if self.latencies else 0,
            'p95_latency_ms': self._percentile(self.latencies, 95) if self.latencies else 0,
            'p99_latency_ms': self._percentile(self.latencies, 99) if self.latencies else 0,
            'avg_compression_ratio': statistics.mean(self.compression_ratios) if self.compression_ratios else 0,
            'total_bytes_sent': self.total_bytes_sent,
            'total_bytes_received': self.total_bytes_received,
            'bandwidth_saved_percent': ((self.total_bytes_sent - self.total_bytes_received) / self.total_bytes_sent * 100) if self.total_bytes_sent > 0 else 0,
            'methods_used': list(set(self.methods_used)),
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


async def run_stress_test(uri: str, num_users: int = 10, messages_per_user: int = 20):
    """Run stress test with multiple concurrent users"""

    print("=" * 80)
    print("AURA Compression - 10 Concurrent Users Stress Test")
    print("=" * 80)
    print(f"\nTest Configuration:")
    print(f"  URI: {uri}")
    print(f"  Number of users: {num_users}")
    print(f"  Messages per user: {messages_per_user}")
    print(f"  Total messages: {num_users * messages_per_user}")
    print(f"  User types: 3 AI, 3 Human, 4 Mixed")
    print()

    # Create users
    users = []
    for i in range(num_users):
        if i < 3:
            user_type = "ai"
        elif i < 6:
            user_type = "human"
        else:
            user_type = "mixed"

        users.append(UserSimulator(i + 1, user_type, messages_per_user))

    # Run all users concurrently
    print("Starting concurrent users...")
    start_time = time.time()

    tasks = [user.run(uri) for user in users]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    total_duration = end_time - start_time

    # Process results
    print("\n" + "=" * 80)
    print("Test Results")
    print("=" * 80)

    all_latencies = []
    all_compression_ratios = []
    total_errors = 0
    total_bytes_sent = 0
    total_bytes_received = 0
    all_methods = []

    print("\nPer-User Statistics:")
    print("-" * 80)
    print(f"{'User':<6} {'Type':<8} {'Msgs':<6} {'Errors':<8} {'Avg Latency':<14} {'P95':<10} {'P99':<10} {'Comp Ratio':<12}")
    print("-" * 80)

    for result in results:
        if isinstance(result, dict):
            all_latencies.extend([result['avg_latency_ms']] * result['messages_sent'])
            if result['avg_compression_ratio'] > 0:
                all_compression_ratios.append(result['avg_compression_ratio'])
            total_errors += result['errors']
            total_bytes_sent += result['total_bytes_sent']
            total_bytes_received += result['total_bytes_received']
            all_methods.extend(result['methods_used'])

            print(f"{result['user_id']:<6} {result['user_type']:<8} {result['messages_sent']:<6} "
                  f"{result['errors']:<8} {result['avg_latency_ms']:<14.2f} "
                  f"{result['p95_latency_ms']:<10.2f} {result['p99_latency_ms']:<10.2f} "
                  f"{result['avg_compression_ratio']:<12.2f}")

    print("-" * 80)

    # Overall statistics
    print("\nOverall Statistics:")
    print("-" * 80)
    print(f"Total duration: {total_duration:.2f} seconds")
    print(f"Total messages: {num_users * messages_per_user}")
    print(f"Messages per second: {(num_users * messages_per_user) / total_duration:.2f}")
    print(f"Total errors: {total_errors}")
    print(f"Error rate: {(total_errors / (num_users * messages_per_user)) * 100:.2f}%")
    print()

    if all_latencies:
        print("Latency Statistics:")
        print(f"  Average: {statistics.mean(all_latencies):.2f} ms")
        print(f"  Median: {statistics.median(all_latencies):.2f} ms")
        print(f"  Min: {min(all_latencies):.2f} ms")
        print(f"  Max: {max(all_latencies):.2f} ms")
        print(f"  P50: {statistics.median(all_latencies):.2f} ms")
        print(f"  P95: {_percentile(all_latencies, 95):.2f} ms")
        print(f"  P99: {_percentile(all_latencies, 99):.2f} ms")
        print()

    if all_compression_ratios:
        print("Compression Statistics:")
        print(f"  Average compression ratio: {statistics.mean(all_compression_ratios):.2f}:1")
        print(f"  Min compression ratio: {min(all_compression_ratios):.2f}:1")
        print(f"  Max compression ratio: {max(all_compression_ratios):.2f}:1")
        print()

    print("Bandwidth Statistics:")
    print(f"  Total bytes sent: {total_bytes_sent:,} bytes ({total_bytes_sent / 1024:.2f} KB)")
    print(f"  Total bytes received: {total_bytes_received:,} bytes ({total_bytes_received / 1024:.2f} KB)")
    if total_bytes_sent > 0:
        bandwidth_saved = ((total_bytes_sent - total_bytes_received) / total_bytes_sent) * 100
        print(f"  Bandwidth saved: {bandwidth_saved:.2f}%")
    print()

    if all_methods:
        method_counts = {}
        for method in all_methods:
            method_counts[method] = method_counts.get(method, 0) + 1

        print("Compression Methods Used:")
        for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {method}: {count} users")
        print()

    print("=" * 80)

    # Test verdict
    print("\nTest Verdict:")
    avg_latency = statistics.mean(all_latencies) if all_latencies else 0
    error_rate = (total_errors / (num_users * messages_per_user)) * 100

    if error_rate == 0 and avg_latency < 100:
        print("  PASS - Excellent performance, no errors")
    elif error_rate < 1 and avg_latency < 200:
        print("  PASS - Good performance, minimal errors")
    elif error_rate < 5 and avg_latency < 500:
        print("  WARNING - Acceptable performance with some issues")
    else:
        print("  FAIL - Performance issues detected")

    print("=" * 80)

    return results


def _percentile(data: List[float], percentile: int) -> float:
    """Calculate percentile"""
    if not data:
        return 0
    sorted_data = sorted(data)
    index = int(len(sorted_data) * percentile / 100)
    return sorted_data[min(index, len(sorted_data) - 1)]


if __name__ == "__main__":
    # Configuration
    SERVER_URI = "ws://localhost:8765"
    NUM_USERS = 10
    MESSAGES_PER_USER = 20

    # Run stress test
    try:
        asyncio.run(run_stress_test(SERVER_URI, NUM_USERS, MESSAGES_PER_USER))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
