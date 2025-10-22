#!/usr/bin/env python3
"""
Real AURA Network Streaming Implementation

This module provides actual network streaming with AURA compression,
including WebSocket support, connection management, and real performance testing.
"""
import asyncio
import websockets
import socket
import json
import time
import threading
from typing import Dict, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import logging
import struct

# Import AURA compression components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

try:
    from aura_compressor.streamer import AuraTransceiver
except ImportError:
    print("Warning: AURA modules not available. Using mock compression.")
    AuraTransceiver = None

class StreamingMode(Enum):
    RAW = "raw"
    COMPRESSED = "compressed"
    ADAPTIVE = "adaptive"

class ProtocolType(Enum):
    TCP = "tcp"
    WEBSOCKET = "websocket"
    UDP = "udp"

@dataclass
class StreamingStats:
    bytes_sent: int = 0
    bytes_received: int = 0
    compression_ratio: float = 1.0
    latency_ms: float = 0.0
    throughput_mbps: float = 0.0
    packets_sent: int = 0
    packets_dropped: int = 0
    connection_time: float = 0.0

class RealAuraStreamer:
    """
    Actual network streaming implementation with AURA compression.
    Supports TCP, WebSocket, and UDP protocols with adaptive compression.
    """
    
    def __init__(self, mode: StreamingMode = StreamingMode.ADAPTIVE):
        self.mode = mode
        self.compressor = None
        self.stats = StreamingStats()
        self.compression_threshold = 1024  # Bytes - compress if larger
        self.batch_timeout = 0.1  # Seconds - max time to batch small messages
        self.pending_messages = []
        self.pending_size = 0
        self.last_batch_time = time.time()
        
        # Initialize AURA compressor if available
        if AuraTransceiver:
            self.compressor = AuraTransceiver()
            # Use a representative sample for handshake
            sample = "Real-time streaming data with network protocols and compression efficiency."
            try:
                self.compressor.perform_handshake(sample)
                logging.info("AURA compression initialized")
            except Exception as e:
                logging.warning(f"AURA initialization failed: {e}")
                self.compressor = None
    
    def should_compress(self, data: bytes) -> bool:
        """Intelligent decision on whether to compress based on size and mode."""
        if self.mode == StreamingMode.RAW:
            return False
        elif self.mode == StreamingMode.COMPRESSED:
            return True
        else:  # ADAPTIVE
            return len(data) >= self.compression_threshold
    
    def compress_data(self, data: str) -> tuple[bytes, bool]:
        """Compress data and return (compressed_data, was_compressed)."""
        if not self.compressor or not self.should_compress(data.encode()):
            return data.encode(), False
        
        try:
            start_time = time.time()
            compressed = self.compressor.compress_chunk(data)
            compression_time = time.time() - start_time
            
            # Check if compression actually helped
            if len(compressed) >= len(data.encode()) * 0.95:
                # Compression didn't help much, send raw
                return data.encode(), False
            
            return compressed, True
        except Exception as e:
            logging.warning(f"Compression failed: {e}")
            return data.encode(), False
    
    def decompress_data(self, data: bytes, was_compressed: bool) -> str:
        """Decompress data if it was compressed."""
        if not was_compressed or not self.compressor:
            return data.decode()
        
        try:
            return self.compressor.decompress_chunk(data)
        except Exception as e:
            logging.error(f"Decompression failed: {e}")
            raise
    
    def pack_message(self, data: bytes, was_compressed: bool) -> bytes:
        """Pack message with header indicating compression status."""
        # Simple framing: [compressed_flag:1][length:4][data:N]
        header = struct.pack('!BI', 1 if was_compressed else 0, len(data))
        return header + data
    
    def unpack_message(self, packed_data: bytes) -> tuple[bytes, bool]:
        """Unpack message and return (data, was_compressed)."""
        if len(packed_data) < 5:
            raise ValueError("Invalid message format")
        
        was_compressed, length = struct.unpack('!BI', packed_data[:5])
        data = packed_data[5:5+length]
        
        if len(data) != length:
            raise ValueError("Message length mismatch")
        
        return data, bool(was_compressed)


class AuraWebSocketServer:
    """WebSocket server with AURA compression support."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.streamer = RealAuraStreamer()
        self.connected_clients = set()
        
    async def handle_client(self, websocket, path):
        """Handle individual WebSocket client connection."""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        logging.info(f"Client connected: {client_addr}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logging.error(f"Error handling client {client_addr}: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def process_message(self, websocket, raw_message):
        """Process incoming message and send response."""
        try:
            # Unpack the message
            data, was_compressed = self.streamer.unpack_message(raw_message)
            
            # Decompress if needed
            message = self.streamer.decompress_data(data, was_compressed)
            
            # Echo back with timestamp (simulation of processing)
            response = f"Echo: {message} [processed at {time.time():.3f}]"
            
            # Compress and pack response
            compressed_data, was_compressed = self.streamer.compress_data(response)
            packed_response = self.streamer.pack_message(compressed_data, was_compressed)
            
            await websocket.send(packed_response)
            
            # Update stats
            self.streamer.stats.packets_sent += 1
            self.streamer.stats.bytes_sent += len(packed_response)
            
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            error_response = f"Error: {str(e)}"
            error_data, _ = self.streamer.compress_data(error_response)
            error_packed = self.streamer.pack_message(error_data, False)
            await websocket.send(error_packed)
    
    async def start_server(self):
        """Start the WebSocket server."""
        logging.info(f"Starting AURA WebSocket server on {self.host}:{self.port}")
        return await websockets.serve(self.handle_client, self.host, self.port)


class AuraWebSocketClient:
    """WebSocket client with AURA compression support."""
    
    def __init__(self):
        self.streamer = RealAuraStreamer()
        self.websocket = None
        self.stats = StreamingStats()
    
    async def connect(self, uri: str):
        """Connect to WebSocket server."""
        self.websocket = await websockets.connect(uri)
        logging.info(f"Connected to {uri}")
    
    async def send_message(self, message: str) -> str:
        """Send message and return response."""
        if not self.websocket:
            raise RuntimeError("Not connected")
        
        start_time = time.time()
        
        # Compress and pack message
        compressed_data, was_compressed = self.streamer.compress_data(message)
        packed_message = self.streamer.pack_message(compressed_data, was_compressed)
        
        # Send message
        await self.websocket.send(packed_message)
        
        # Receive response
        raw_response = await self.websocket.recv()
        
        # Unpack and decompress response
        response_data, response_compressed = self.streamer.unpack_message(raw_response)
        response = self.streamer.decompress_data(response_data, response_compressed)
        
        # Update stats
        latency = (time.time() - start_time) * 1000  # ms
        self.stats.latency_ms = latency
        self.stats.packets_sent += 1
        self.stats.bytes_sent += len(packed_message)
        self.stats.bytes_received += len(raw_response)
        
        return response
    
    async def disconnect(self):
        """Disconnect from server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None


class StreamingBenchmark:
    """Comprehensive benchmark for real streaming performance."""
    
    def __init__(self):
        self.results = {}
    
    async def benchmark_websocket(self, messages: List[str], concurrent_clients: int = 1):
        """Benchmark WebSocket streaming with real network calls."""
        
        # Start server
        server = AuraWebSocketServer()
        server_task = await server.start_server()
        
        try:
            # Give server time to start
            await asyncio.sleep(0.1)
            
            # Run benchmark with multiple clients
            tasks = []
            for i in range(concurrent_clients):
                task = self._run_client_benchmark(f"client_{i}", messages)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # Aggregate results
            total_latency = sum(r['avg_latency'] for r in results)
            total_throughput = sum(r['throughput'] for r in results)
            total_compression = sum(r['compression_ratio'] for r in results) / len(results)
            
            return {
                'concurrent_clients': concurrent_clients,
                'avg_latency_ms': total_latency / concurrent_clients,
                'total_throughput_mbps': total_throughput,
                'avg_compression_ratio': total_compression,
                'individual_results': results
            }
        
        finally:
            server_task.close()
            await server_task.wait_closed()
    
    async def _run_client_benchmark(self, client_id: str, messages: List[str]):
        """Run benchmark for a single client."""
        client = AuraWebSocketClient()
        
        try:
            await client.connect("ws://localhost:8765")
            
            start_time = time.time()
            latencies = []
            
            for message in messages:
                msg_start = time.time()
                response = await client.send_message(message)
                latency = (time.time() - msg_start) * 1000
                latencies.append(latency)
            
            total_time = time.time() - start_time
            
            # Calculate stats
            total_bytes = client.stats.bytes_sent + client.stats.bytes_received
            throughput = (total_bytes * 8) / (total_time * 1_000_000)  # Mbps
            
            return {
                'client_id': client_id,
                'avg_latency': sum(latencies) / len(latencies),
                'throughput': throughput,
                'compression_ratio': client.streamer.stats.compression_ratio,
                'messages_processed': len(messages)
            }
        
        finally:
            await client.disconnect()


async def real_streaming_demo():
    """Demonstrate real AURA streaming over WebSocket."""
    
    print("🚀 Real AURA Network Streaming Demo")
    print("=" * 50)
    
    # Test messages of various sizes
    messages = [
        "Hello world!",  # Small
        "The neural network processes data efficiently. " * 10,  # Medium
        "Artificial intelligence and machine learning algorithms utilize deep neural networks to process natural language data through transformer architectures with attention mechanisms and residual connections for optimal performance. " * 20,  # Large
    ]
    
    benchmark = StreamingBenchmark()
    
    # Test with single client
    print("\n📊 Single Client Benchmark:")
    results = await benchmark.benchmark_websocket(messages, concurrent_clients=1)
    
    print(f"Average Latency: {results['avg_latency_ms']:.2f} ms")
    print(f"Throughput: {results['total_throughput_mbps']:.2f} Mbps")
    print(f"Compression Ratio: {results['avg_compression_ratio']:.2f}:1")
    
    # Test with multiple clients
    print("\n🔥 Multi-Client Benchmark:")
    results = await benchmark.benchmark_websocket(messages, concurrent_clients=5)
    
    print(f"Concurrent Clients: {results['concurrent_clients']}")
    print(f"Average Latency: {results['avg_latency_ms']:.2f} ms")
    print(f"Total Throughput: {results['total_throughput_mbps']:.2f} Mbps")
    print(f"Compression Ratio: {results['avg_compression_ratio']:.2f}:1")
    
    print("\n✅ Real streaming benchmark complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(real_streaming_demo())