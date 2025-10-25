"""
AURA Compression - Comprehensive Metrics Collector
Collects detailed performance metrics during stress testing

Copyright (c) 2025 Todd James Hendricks
Licensed under Apache License 2.0
Patent Pending - Application No. 19/366,538
"""

import asyncio
import websockets
import time
import statistics
import json
import random
from typing import List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class MessageMetrics:
    """Metrics for a single message"""
    timestamp: float
    user_id: int
    user_type: str
    message_size: int
    compressed_size: int
    compression_ratio: float
    compression_method: str
    latency_ms: float
    throughput_mbps: float
    error: str = None


@dataclass
class UserMetrics:
    """Aggregated metrics for a user"""
    user_id: int
    user_type: str
    total_messages: int
    successful_messages: int
    failed_messages: int
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_compression_ratio: float
    total_bytes_sent: int
    total_bytes_compressed: int
    bandwidth_saved_percent: float
    avg_throughput_mbps: float
    methods_used: List[str]


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    test_start_time: str
    test_duration_seconds: float
    total_users: int
    total_messages: int
    successful_messages: int
    failed_messages: int
    messages_per_second: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_compression_ratio: float
    total_bytes_sent: int
    total_bytes_compressed: int
    bandwidth_saved_percent: float
    avg_throughput_mbps: float
    peak_throughput_mbps: float
    compression_methods: Dict[str, int]


class MetricsCollector:
    """Collects and aggregates metrics from stress tests"""

    def __init__(self):
        self.message_metrics: List[MessageMetrics] = []
        self.user_metrics: Dict[int, UserMetrics] = {}
        self.test_start_time = None
        self.test_end_time = None

    def record_message(self, metrics: MessageMetrics):
        """Record metrics for a single message"""
        self.message_metrics.append(metrics)

    def calculate_user_metrics(self) -> Dict[int, UserMetrics]:
        """Calculate aggregated metrics for each user"""
        user_data = {}

        for msg in self.message_metrics:
            if msg.user_id not in user_data:
                user_data[msg.user_id] = {
                    'user_type': msg.user_type,
                    'latencies': [],
                    'ratios': [],
                    'throughputs': [],
                    'bytes_sent': 0,
                    'bytes_compressed': 0,
                    'methods': set(),
                    'errors': 0,
                    'total': 0
                }

            data = user_data[msg.user_id]
            data['total'] += 1

            if msg.error:
                data['errors'] += 1
            else:
                data['latencies'].append(msg.latency_ms)
                data['ratios'].append(msg.compression_ratio)
                data['throughputs'].append(msg.throughput_mbps)
                data['bytes_sent'] += msg.message_size
                data['bytes_compressed'] += msg.compressed_size
                data['methods'].add(msg.compression_method)

        # Create UserMetrics objects
        for user_id, data in user_data.items():
            latencies = data['latencies']
            ratios = data['ratios']
            throughputs = data['throughputs']

            bandwidth_saved = 0
            if data['bytes_sent'] > 0:
                bandwidth_saved = ((data['bytes_sent'] - data['bytes_compressed']) /
                                 data['bytes_sent']) * 100

            self.user_metrics[user_id] = UserMetrics(
                user_id=user_id,
                user_type=data['user_type'],
                total_messages=data['total'],
                successful_messages=data['total'] - data['errors'],
                failed_messages=data['errors'],
                avg_latency_ms=statistics.mean(latencies) if latencies else 0,
                min_latency_ms=min(latencies) if latencies else 0,
                max_latency_ms=max(latencies) if latencies else 0,
                p50_latency_ms=statistics.median(latencies) if latencies else 0,
                p95_latency_ms=self._percentile(latencies, 95) if latencies else 0,
                p99_latency_ms=self._percentile(latencies, 99) if latencies else 0,
                avg_compression_ratio=statistics.mean(ratios) if ratios else 0,
                total_bytes_sent=data['bytes_sent'],
                total_bytes_compressed=data['bytes_compressed'],
                bandwidth_saved_percent=bandwidth_saved,
                avg_throughput_mbps=statistics.mean(throughputs) if throughputs else 0,
                methods_used=list(data['methods'])
            )

        return self.user_metrics

    def calculate_system_metrics(self) -> SystemMetrics:
        """Calculate system-wide metrics"""
        if not self.message_metrics:
            return None

        all_latencies = []
        all_ratios = []
        all_throughputs = []
        total_bytes_sent = 0
        total_bytes_compressed = 0
        failed_count = 0
        method_counts = {}

        for msg in self.message_metrics:
            if msg.error:
                failed_count += 1
            else:
                all_latencies.append(msg.latency_ms)
                all_ratios.append(msg.compression_ratio)
                all_throughputs.append(msg.throughput_mbps)
                total_bytes_sent += msg.message_size
                total_bytes_compressed += msg.compressed_size

                method_counts[msg.compression_method] = \
                    method_counts.get(msg.compression_method, 0) + 1

        duration = self.test_end_time - self.test_start_time
        total_messages = len(self.message_metrics)
        successful_messages = total_messages - failed_count

        bandwidth_saved = 0
        if total_bytes_sent > 0:
            bandwidth_saved = ((total_bytes_sent - total_bytes_compressed) /
                             total_bytes_sent) * 100

        return SystemMetrics(
            test_start_time=datetime.fromtimestamp(self.test_start_time).isoformat(),
            test_duration_seconds=duration,
            total_users=len(self.user_metrics),
            total_messages=total_messages,
            successful_messages=successful_messages,
            failed_messages=failed_count,
            messages_per_second=total_messages / duration if duration > 0 else 0,
            avg_latency_ms=statistics.mean(all_latencies) if all_latencies else 0,
            p50_latency_ms=statistics.median(all_latencies) if all_latencies else 0,
            p95_latency_ms=self._percentile(all_latencies, 95) if all_latencies else 0,
            p99_latency_ms=self._percentile(all_latencies, 99) if all_latencies else 0,
            avg_compression_ratio=statistics.mean(all_ratios) if all_ratios else 0,
            total_bytes_sent=total_bytes_sent,
            total_bytes_compressed=total_bytes_compressed,
            bandwidth_saved_percent=bandwidth_saved,
            avg_throughput_mbps=statistics.mean(all_throughputs) if all_throughputs else 0,
            peak_throughput_mbps=max(all_throughputs) if all_throughputs else 0,
            compression_methods=method_counts
        )

    def export_json(self, filename: str):
        """Export all metrics to JSON file"""
        data = {
            'test_info': {
                'start_time': datetime.fromtimestamp(self.test_start_time).isoformat(),
                'end_time': datetime.fromtimestamp(self.test_end_time).isoformat(),
                'duration_seconds': self.test_end_time - self.test_start_time
            },
            'system_metrics': asdict(self.calculate_system_metrics()),
            'user_metrics': {
                user_id: asdict(metrics)
                for user_id, metrics in self.user_metrics.items()
            },
            'message_metrics': [asdict(msg) for msg in self.message_metrics]
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def print_summary(self):
        """Print comprehensive metrics summary"""
        system = self.calculate_system_metrics()

        print("\n" + "=" * 80)
        print("COMPREHENSIVE METRICS SUMMARY")
        print("=" * 80)

        print("\nSYSTEM METRICS:")
        print("-" * 80)
        print(f"Test Duration: {system.test_duration_seconds:.2f} seconds")
        print(f"Total Users: {system.total_users}")
        print(f"Total Messages: {system.total_messages}")
        print(f"Successful: {system.successful_messages}")
        print(f"Failed: {system.failed_messages}")
        print(f"Success Rate: {(system.successful_messages / system.total_messages * 100):.2f}%")
        print(f"Messages/Second: {system.messages_per_second:.2f}")
        print()

        print("LATENCY METRICS:")
        print(f"  Average: {system.avg_latency_ms:.3f} ms")
        print(f"  P50: {system.p50_latency_ms:.3f} ms")
        print(f"  P95: {system.p95_latency_ms:.3f} ms")
        print(f"  P99: {system.p99_latency_ms:.3f} ms")
        print()

        print("COMPRESSION METRICS:")
        print(f"  Average Ratio: {system.avg_compression_ratio:.2f}:1")
        print(f"  Total Bytes Sent: {system.total_bytes_sent:,} bytes")
        print(f"  Total Bytes Compressed: {system.total_bytes_compressed:,} bytes")
        print(f"  Bandwidth Saved: {system.bandwidth_saved_percent:.2f}%")
        print()

        print("THROUGHPUT METRICS:")
        print(f"  Average: {system.avg_throughput_mbps:.2f} Mbps")
        print(f"  Peak: {system.peak_throughput_mbps:.2f} Mbps")
        print()

        print("COMPRESSION METHODS:")
        for method, count in sorted(system.compression_methods.items(),
                                   key=lambda x: x[1], reverse=True):
            percentage = (count / system.successful_messages) * 100
            print(f"  {method}: {count} messages ({percentage:.1f}%)")
        print()

        print("USER METRICS:")
        print("-" * 80)
        print(f"{'User':<6} {'Type':<8} {'Msgs':<6} {'Success':<8} {'Latency':<12} "
              f"{'P95':<10} {'Ratio':<8} {'BW Saved':<10}")
        print("-" * 80)

        for user_id in sorted(self.user_metrics.keys()):
            um = self.user_metrics[user_id]
            print(f"{um.user_id:<6} {um.user_type:<8} {um.total_messages:<6} "
                  f"{um.successful_messages:<8} {um.avg_latency_ms:<12.3f} "
                  f"{um.p95_latency_ms:<10.3f} {um.avg_compression_ratio:<8.2f} "
                  f"{um.bandwidth_saved_percent:<10.2f}%")

        print("-" * 80)

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Test messages
AI_MESSAGES = [
    "I cannot browse the internet.",
    "I don't have access to real-time information.",
    "I'm unable to execute code on your computer.",
    "The capital of France is Paris.",
    "Python is a high-level programming language.",
]

HUMAN_MESSAGES = [
    "How do I install Python?",
    "Can you help me debug this code?",
    "What's the weather like today?",
    "Tell me a joke!",
    "How do I reset my password?",
]


async def run_metrics_test(uri: str, num_users: int = 10, messages_per_user: int = 20):
    """Run stress test with comprehensive metrics collection"""

    collector = MetricsCollector()
    collector.test_start_time = time.time()

    print("=" * 80)
    print("AURA Compression - Comprehensive Metrics Test")
    print("=" * 80)
    print(f"Users: {num_users}")
    print(f"Messages per user: {messages_per_user}")
    print(f"Total messages: {num_users * messages_per_user}")
    print()

    async def user_task(user_id: int, user_type: str):
        """Simulate a single user"""
        try:
            async with websockets.connect(uri) as websocket:
                for i in range(messages_per_user):
                    # Select message
                    if user_type == "ai":
                        message = random.choice(AI_MESSAGES)
                    else:
                        message = random.choice(HUMAN_MESSAGES)

                    # Send and measure
                    msg_start = time.time()
                    await websocket.send(message)
                    response = await websocket.recv()
                    msg_end = time.time()

                    latency_ms = (msg_end - msg_start) * 1000

                    # Parse response
                    try:
                        data = json.loads(response)
                        compressed_size = data.get('compressed_size', len(message))
                        compression_ratio = data.get('compression_ratio', 1.0)
                        method = data.get('method', 'unknown')
                        error = None
                    except:
                        compressed_size = len(response)
                        compression_ratio = 1.0
                        method = 'unknown'
                        error = None

                    # Calculate throughput
                    duration_s = (msg_end - msg_start)
                    bytes_transferred = len(message) + compressed_size
                    throughput_mbps = (bytes_transferred * 8) / (duration_s * 1_000_000)

                    # Record metrics
                    metrics = MessageMetrics(
                        timestamp=msg_start,
                        user_id=user_id,
                        user_type=user_type,
                        message_size=len(message),
                        compressed_size=compressed_size,
                        compression_ratio=compression_ratio,
                        compression_method=method,
                        latency_ms=latency_ms,
                        throughput_mbps=throughput_mbps,
                        error=error
                    )
                    collector.record_message(metrics)

                    # Random delay
                    await asyncio.sleep(random.uniform(0.01, 0.5))

        except Exception as e:
            # Record error
            metrics = MessageMetrics(
                timestamp=time.time(),
                user_id=user_id,
                user_type=user_type,
                message_size=0,
                compressed_size=0,
                compression_ratio=0,
                compression_method='error',
                latency_ms=0,
                throughput_mbps=0,
                error=str(e)
            )
            collector.record_message(metrics)

    # Create user tasks
    tasks = []
    for i in range(num_users):
        user_type = "ai" if i < num_users // 2 else "human"
        tasks.append(user_task(i + 1, user_type))

    # Run all users
    print("Running users...")
    await asyncio.gather(*tasks)

    collector.test_end_time = time.time()
    collector.calculate_user_metrics()

    # Print summary
    collector.print_summary()

    # Export to JSON
    filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    collector.export_json(filename)
    print(f"\nMetrics exported to: {filename}")

    return collector


if __name__ == "__main__":
    SERVER_URI = "ws://localhost:8765"
    NUM_USERS = 10
    MESSAGES_PER_USER = 20

    try:
        asyncio.run(run_metrics_test(SERVER_URI, NUM_USERS, MESSAGES_PER_USER))
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
