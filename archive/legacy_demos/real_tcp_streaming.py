#!/usr/bin/env python3
"""
Real AURA Network Streaming Implementation (No External Dependencies)

This module provides actual network streaming with AURA compression using
only standard library components: socket, asyncio, threading.
No websockets dependency required.
"""
import asyncio
import socket
import json
import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import struct
import select

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
    Uses standard library sockets for real network communication.
    """
    
    def __init__(self, mode: StreamingMode = StreamingMode.ADAPTIVE):
        self.mode = mode
        self.compressor = None
        self.stats = StreamingStats()
        self.compression_threshold = 1024  # Bytes - compress if larger
        
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
        """
        Pack message with optimized header (4 bytes instead of 5).

        Header format: [length_and_flag:4]
        - Bit 31: compression flag (0 = raw, 1 = compressed)
        - Bits 0-30: length (supports up to 2GB messages)

        Optimization: Saves 1 byte per message (20% framing overhead reduction)
        """
        # Pack compression flag into MSB of length field
        length_packed = len(data) | (0x80000000 if was_compressed else 0)
        header = struct.pack('!I', length_packed)
        return header + data

    def unpack_message(self, packed_data: bytes) -> tuple[bytes, bool]:
        """Unpack optimized message format."""
        if len(packed_data) < 4:
            raise ValueError("Invalid message format")

        # Unpack length with compression flag in MSB
        length_packed = struct.unpack('!I', packed_data[:4])[0]
        was_compressed = bool(length_packed & 0x80000000)
        length = length_packed & 0x7FFFFFFF  # Mask out compression flag

        data = packed_data[4:4+length]

        if len(data) != length:
            raise ValueError(f"Message length mismatch: expected {length}, got {len(data)}")

        return data, was_compressed


class AuraTCPServer:
    """TCP server with AURA compression support using raw sockets."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.streamer = RealAuraStreamer()
        self.running = False
        self.server_socket = None
        
    def start_server(self):
        """Start the TCP server in a separate thread."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        logging.info(f"AURA TCP Server started on {self.host}:{self.port}")
        
        while self.running:
            try:
                # Use select for non-blocking accept
                ready = select.select([self.server_socket], [], [], 1.0)
                if ready[0]:
                    client_socket, client_addr = self.server_socket.accept()
                    logging.info(f"Client connected: {client_addr}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, client_addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
            except Exception as e:
                if self.running:
                    logging.error(f"Server error: {e}")
                break
    
    def handle_client(self, client_socket: socket.socket, client_addr):
        """Handle individual client connection."""
        try:
            while self.running:
                # Receive optimized header (4 bytes)
                header_data = self._recv_exactly(client_socket, 4)
                if not header_data:
                    break

                # Unpack header with compression flag in MSB
                length_packed = struct.unpack('!I', header_data)[0]
                was_compressed = bool(length_packed & 0x80000000)
                data_length = length_packed & 0x7FFFFFFF

                # Receive the actual data
                message_data = self._recv_exactly(client_socket, data_length)
                if not message_data:
                    break

                # Decompress if needed
                message = self.streamer.decompress_data(message_data, was_compressed)
                
                # Echo back with timestamp (simulation of processing)
                response = f"Echo: {message} [processed at {time.time():.3f}]"
                
                # Compress and send response
                compressed_data, was_compressed = self.streamer.compress_data(response)
                packed_response = self.streamer.pack_message(compressed_data, was_compressed)
                
                client_socket.sendall(packed_response)
                
                # Update stats
                self.streamer.stats.packets_sent += 1
                self.streamer.stats.bytes_sent += len(packed_response)
                
        except Exception as e:
            logging.error(f"Error handling client {client_addr}: {e}")
        finally:
            client_socket.close()
            logging.info(f"Client disconnected: {client_addr}")
    
    def _recv_exactly(self, sock: socket.socket, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from socket."""
        data = b''
        while len(data) < num_bytes:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return b''
            data += chunk
        return data
    
    def stop_server(self):
        """Stop the server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


class AuraTCPClient:
    """TCP client with AURA compression support."""
    
    def __init__(self):
        self.streamer = RealAuraStreamer()
        self.socket = None
        self.stats = StreamingStats()
    
    def connect(self, host: str = "localhost", port: int = 8765):
        """Connect to TCP server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        logging.info(f"Connected to {host}:{port}")
    
    def send_message(self, message: str) -> str:
        """Send message and return response."""
        if not self.socket:
            raise RuntimeError("Not connected")
        
        start_time = time.time()
        
        # Compress and pack message
        compressed_data, was_compressed = self.streamer.compress_data(message)
        packed_message = self.streamer.pack_message(compressed_data, was_compressed)
        
        # Send message
        self.socket.sendall(packed_message)

        # Receive optimized response header (4 bytes)
        header_data = self._recv_exactly(4)
        length_packed = struct.unpack('!I', header_data)[0]
        was_compressed = bool(length_packed & 0x80000000)
        data_length = length_packed & 0x7FFFFFFF
        
        # Receive response data
        response_data = self._recv_exactly(data_length)
        
        # Decompress response
        response = self.streamer.decompress_data(response_data, bool(was_compressed))
        
        # Update stats
        latency = (time.time() - start_time) * 1000  # ms
        self.stats.latency_ms = latency
        self.stats.packets_sent += 1
        self.stats.bytes_sent += len(packed_message)
        self.stats.bytes_received += len(header_data) + len(response_data)
        
        return response
    
    def _recv_exactly(self, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from socket."""
        data = b''
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    def disconnect(self):
        """Disconnect from server."""
        if self.socket:
            self.socket.close()
            self.socket = None


class RealStreamingBenchmark:
    """Comprehensive benchmark for real TCP streaming performance."""
    
    def __init__(self):
        self.server = None
        self.server_thread = None
    
    def start_test_server(self):
        """Start test server in background."""
        self.server = AuraTCPServer()
        self.server_thread = threading.Thread(target=self.server.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(0.5)  # Give server time to start
    
    def stop_test_server(self):
        """Stop test server."""
        if self.server:
            self.server.stop_server()
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
    
    def benchmark_tcp(self, messages: List[str], concurrent_clients: int = 1):
        """Benchmark TCP streaming with real network calls."""
        
        self.start_test_server()
        
        try:
            # Run benchmark with multiple clients
            threads = []
            results = []
            
            def run_client(client_id: int, messages: List[str]):
                result = self._run_client_benchmark(f"client_{client_id}", messages)
                results.append(result)
            
            # Start client threads
            for i in range(concurrent_clients):
                thread = threading.Thread(target=run_client, args=(i, messages))
                thread.start()
                threads.append(thread)
            
            # Wait for all clients to complete
            for thread in threads:
                thread.join()
            
            # Aggregate results
            if results:
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
            else:
                return {'error': 'No results collected'}
        
        finally:
            self.stop_test_server()
    
    def _run_client_benchmark(self, client_id: str, messages: List[str]):
        """Run benchmark for a single client."""
        client = AuraTCPClient()
        
        try:
            client.connect()
            
            start_time = time.time()
            latencies = []
            
            for message in messages:
                msg_start = time.time()
                response = client.send_message(message)
                latency = (time.time() - msg_start) * 1000
                latencies.append(latency)
            
            total_time = time.time() - start_time
            
            # Calculate stats
            total_bytes = client.stats.bytes_sent + client.stats.bytes_received
            throughput = (total_bytes * 8) / (total_time * 1_000_000) if total_time > 0 else 0  # Mbps
            
            return {
                'client_id': client_id,
                'avg_latency': sum(latencies) / len(latencies) if latencies else 0,
                'throughput': throughput,
                'compression_ratio': client.streamer.stats.compression_ratio,
                'messages_processed': len(messages)
            }
        
        except Exception as e:
            logging.error(f"Client {client_id} error: {e}")
            return {
                'client_id': client_id,
                'error': str(e),
                'avg_latency': 0,
                'throughput': 0,
                'compression_ratio': 1.0,
                'messages_processed': 0
            }
        finally:
            client.disconnect()


def real_streaming_demo():
    """Demonstrate real AURA streaming over TCP."""
    
    print("🚀 Real AURA Network Streaming Demo (TCP)")
    print("=" * 50)
    
    # Test messages of various sizes
    messages = [
        "Hello world!",  # Small
        "The neural network processes data efficiently. " * 10,  # Medium
        "Artificial intelligence and machine learning algorithms utilize deep neural networks to process natural language data through transformer architectures with attention mechanisms and residual connections for optimal performance. " * 20,  # Large
    ]
    
    benchmark = RealStreamingBenchmark()
    
    # Test with single client
    print("\n📊 Single Client Benchmark:")
    try:
        results = benchmark.benchmark_tcp(messages, concurrent_clients=1)
        
        if 'error' in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Average Latency: {results['avg_latency_ms']:.2f} ms")
            print(f"Throughput: {results['total_throughput_mbps']:.4f} Mbps")
            print(f"Compression Ratio: {results['avg_compression_ratio']:.2f}:1")
    except Exception as e:
        print(f"Benchmark failed: {e}")
    
    # Test with multiple clients
    print("\n🔥 Multi-Client Benchmark:")
    try:
        results = benchmark.benchmark_tcp(messages, concurrent_clients=3)
        
        if 'error' in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Concurrent Clients: {results['concurrent_clients']}")
            print(f"Average Latency: {results['avg_latency_ms']:.2f} ms")
            print(f"Total Throughput: {results['total_throughput_mbps']:.4f} Mbps")
            print(f"Compression Ratio: {results['avg_compression_ratio']:.2f}:1")
    except Exception as e:
        print(f"Multi-client benchmark failed: {e}")
    
    print("\n✅ Real streaming benchmark complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    real_streaming_demo()