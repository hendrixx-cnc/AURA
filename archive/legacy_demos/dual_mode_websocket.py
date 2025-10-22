#!/usr/bin/env python3
"""
WebSocket AURA: Test Both Raw and Auditable Compression Formats

This tests:
1. Raw AURA compression (maximum efficiency)
2. Auditable format (transparency + compression)
3. Performance comparison over real WebSocket connection
"""
import asyncio
import json
import time
import base64
import struct
from typing import Dict, Optional, List
import logging
from dataclasses import dataclass
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import hashlib
import socket

# Import AURA compression components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

try:
    from aura_compressor.streamer import AuraTransceiver
    from aura_compressor.lib.hacs_tokenizer import HACSTokenizer
    from aura_compressor.lib.cdis_entropy_encode_v3 import (
        encode_with_tree, bits_to_bytes, decode_with_huffman, bytes_to_bits
    )
except ImportError:
    print("Warning: AURA modules not available.")
    AuraTransceiver = None

class RawAuraCompressor:
    """Direct AURA compression without auditable overhead."""
    
    def __init__(self):
        self.transceiver = None
        if AuraTransceiver:
            self.transceiver = AuraTransceiver()
    
    def initialize(self, sample_text: str):
        """Initialize with handshake."""
        if self.transceiver:
            return self.transceiver.perform_handshake(sample_text)
        return b""
    
    def compress_raw(self, text: str) -> bytes:
        """Raw compression without auditable format."""
        if not self.transceiver or not self.transceiver.is_ready:
            return text.encode()
        
        try:
            # Direct HACS tokenization
            hacs_tokens = self.transceiver.hacs_tokenizer.tokenize_text_with_map(
                text, self.transceiver.hacs_id_map
            )
            
            # Direct entropy encoding
            bit_string = encode_with_tree(
                hacs_tokens,
                self.transceiver.compression_tree,
                self.transceiver.rare_literals,
                escape_code=self.transceiver.escape_code,
            )
            
            compressed_data, padding = bits_to_bytes(bit_string)
            
            # Return raw compressed bytes with minimal header
            # Format: [padding_bits:1][compressed_data:N]
            return bytes([padding]) + compressed_data
            
        except Exception as e:
            print(f"Raw compression failed: {e}")
            return text.encode()
    
    def decompress_raw(self, compressed_data: bytes) -> str:
        """Raw decompression."""
        if not self.transceiver or not self.transceiver.is_ready:
            return compressed_data.decode()
        
        try:
            # Extract padding and data
            padding = compressed_data[0]
            data = compressed_data[1:]
            
            # Convert to bits
            bit_string = bytes_to_bits(data, padding)
            
            # Decode with Huffman
            result = decode_with_huffman(
                bit_string,
                self.transceiver.decompression_tree,
                self.transceiver.rare_literals,
                escape_code=self.transceiver.escape_code,
            )
            hacs_tokens = result.get('substituted_tokens', [])
            
            # Convert back to text
            return self.transceiver.hacs_tokenizer.detokenize_to_text(hacs_tokens)
            
        except Exception as e:
            print(f"Raw decompression failed: {e}")
            return compressed_data.decode()

class DualModeWebSocketServer:
    """WebSocket server that tests both raw and auditable AURA compression."""
    
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.auditable_compressor = None  # Original auditable format
        self.raw_compressor = None        # Raw compression
        
    def start_server(self):
        """Start the WebSocket server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        logging.info(f"Dual-Mode AURA WebSocket Server started on {self.host}:{self.port}")
        
        while self.running:
            try:
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
        """Handle WebSocket client with dual compression modes."""
        try:
            # Perform WebSocket handshake
            if not self.websocket_handshake(client_socket):
                logging.error("WebSocket handshake failed")
                return
            
            # Initialize both compressors
            if AuraTransceiver:
                sample_text = "WebSocket dual-mode AURA compression testing with raw and auditable formats"
                
                # Initialize auditable compressor
                self.auditable_compressor = AuraTransceiver()
                auditable_handshake = self.auditable_compressor.perform_handshake(sample_text)
                
                # Initialize raw compressor
                self.raw_compressor = RawAuraCompressor()
                raw_handshake = self.raw_compressor.initialize(sample_text)
                
                # Send initialization confirmation
                init_message = {
                    "type": "dual_mode_ready",
                    "auditable_handshake_size": len(auditable_handshake),
                    "raw_handshake_size": len(raw_handshake),
                    "modes_available": ["raw", "auditable"]
                }
                
                self.send_websocket_frame(client_socket, json.dumps(init_message))
                logging.info("Dual-mode AURA initialized")
            
            # Handle incoming messages
            while self.running:
                frame_data = self.receive_websocket_frame(client_socket)
                if not frame_data:
                    break
                
                try:
                    message = json.loads(frame_data.decode('utf-8'))
                    response = self.process_dual_mode_message(message)
                    
                    if response:
                        self.send_websocket_frame(client_socket, json.dumps(response))
                        
                except json.JSONDecodeError:
                    logging.error("Invalid JSON received")
                    
        except Exception as e:
            logging.error(f"Error handling client {client_addr}: {e}")
        finally:
            client_socket.close()
            logging.info(f"Client disconnected: {client_addr}")
    
    def process_dual_mode_message(self, message: Dict) -> Optional[Dict]:
        """Process message with both compression modes."""
        msg_type = message.get("type")
        
        if msg_type == "compare_compression":
            text = message.get("text", "")
            
            results = {
                "type": "compression_comparison",
                "original_size": len(text),
                "results": {}
            }
            
            # Test raw compression
            if self.raw_compressor:
                start_time = time.time()
                raw_compressed = self.raw_compressor.compress_raw(text)
                raw_time = (time.time() - start_time) * 1000
                
                # Test decompression
                start_time = time.time()
                raw_decompressed = self.raw_compressor.decompress_raw(raw_compressed)
                raw_decomp_time = (time.time() - start_time) * 1000
                
                raw_ratio = len(text) / len(raw_compressed) if len(raw_compressed) > 0 else 0
                
                results["results"]["raw"] = {
                    "compressed_size": len(raw_compressed),
                    "compression_ratio": round(raw_ratio, 3),
                    "compression_time_ms": round(raw_time, 2),
                    "decompression_time_ms": round(raw_decomp_time, 2),
                    "integrity_check": raw_decompressed == text,
                    "efficiency": "excellent" if raw_ratio > 1.5 else "good" if raw_ratio > 1.0 else "poor"
                }
            
            # Test auditable compression
            if self.auditable_compressor:
                start_time = time.time()
                auditable_compressed = self.auditable_compressor.compress_chunk(text)
                auditable_time = (time.time() - start_time) * 1000
                
                # Test decompression
                start_time = time.time()
                auditable_decompressed = self.auditable_compressor.decompress_chunk(auditable_compressed)
                auditable_decomp_time = (time.time() - start_time) * 1000
                
                auditable_ratio = len(text) / len(auditable_compressed) if len(auditable_compressed) > 0 else 0
                
                results["results"]["auditable"] = {
                    "compressed_size": len(auditable_compressed),
                    "compression_ratio": round(auditable_ratio, 3),
                    "compression_time_ms": round(auditable_time, 2),
                    "decompression_time_ms": round(auditable_decomp_time, 2),
                    "integrity_check": auditable_decompressed == text,
                    "efficiency": "excellent" if auditable_ratio > 1.5 else "good" if auditable_ratio > 1.0 else "poor"
                }
            
            return results
        
        return {"type": "unknown", "message": "Unknown message type"}
    
    def websocket_handshake(self, client_socket: socket.socket) -> bool:
        """Perform WebSocket handshake."""
        try:
            request = client_socket.recv(4096).decode('utf-8')
            lines = request.split('\r\n')
            websocket_key = None
            for line in lines:
                if line.startswith('Sec-WebSocket-Key:'):
                    websocket_key = line.split(': ')[1]
                    break
            
            if not websocket_key:
                return False
            
            magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept_key = base64.b64encode(
                hashlib.sha1((websocket_key + magic_string).encode()).digest()
            ).decode()
            
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n"
                "\r\n"
            )
            
            client_socket.send(response.encode())
            return True
            
        except Exception as e:
            logging.error(f"WebSocket handshake error: {e}")
            return False
    
    def send_websocket_frame(self, client_socket: socket.socket, data: str):
        """Send WebSocket frame."""
        data_bytes = data.encode('utf-8')
        frame = bytearray()
        frame.append(0x81)  # FIN + text opcode
        
        if len(data_bytes) < 126:
            frame.append(len(data_bytes))
        elif len(data_bytes) < 65536:
            frame.append(126)
            frame.extend(struct.pack('>H', len(data_bytes)))
        else:
            frame.append(127)
            frame.extend(struct.pack('>Q', len(data_bytes)))
        
        frame.extend(data_bytes)
        client_socket.send(frame)
    
    def receive_websocket_frame(self, client_socket: socket.socket) -> Optional[bytes]:
        """Receive WebSocket frame."""
        try:
            header = client_socket.recv(2)
            if len(header) != 2:
                return None
            
            byte1, byte2 = header
            masked = (byte2 & 0x80) != 0
            payload_length = byte2 & 0x7F
            
            if payload_length == 126:
                length_data = client_socket.recv(2)
                payload_length = struct.unpack('>H', length_data)[0]
            elif payload_length == 127:
                length_data = client_socket.recv(8)
                payload_length = struct.unpack('>Q', length_data)[0]
            
            mask = None
            if masked:
                mask = client_socket.recv(4)
            
            payload = client_socket.recv(payload_length)
            
            if masked and mask:
                payload = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
            
            return payload
            
        except Exception as e:
            logging.error(f"Error receiving WebSocket frame: {e}")
            return None
    
    def stop_server(self):
        """Stop the server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


def dual_mode_compression_demo():
    """Demonstrate raw vs auditable AURA compression over WebSocket."""
    
    print("🚀 Dual-Mode AURA WebSocket Compression Test")
    print("=" * 60)
    
    # Start server
    server = DualModeWebSocketServer()
    server_thread = threading.Thread(target=server.start_server)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1.0)
    
    try:
        # Connect client
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", 8765))
        
        # WebSocket handshake
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET / HTTP/1.1\r\n"
            f"Host: localhost:8765\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        client_socket.send(handshake.encode())
        response = client_socket.recv(4096).decode()
        
        if "101 Switching Protocols" not in response:
            print("❌ WebSocket handshake failed")
            return
        
        print("✅ WebSocket connection established")
        
        # Wait for initialization
        init_data = server._receive_websocket_frame_client(client_socket)
        if init_data:
            init_message = json.loads(init_data.decode('utf-8'))
            print(f"✅ Dual-mode AURA initialized")
            print(f"   Modes: {init_message.get('modes_available', [])}")
        
        # Test compression comparison
        test_cases = [
            ("Small", "AURA compression test with neural networks and machine learning algorithms. " * 3),
            ("Medium", "The artificial intelligence system utilizes advanced neural network architectures with transformer attention mechanisms for optimal performance in natural language processing and data compression tasks. " * 15),
            ("Large", "Comprehensive analysis of machine learning compression algorithms reveals that AURA's HACS tokenization combined with Huffman entropy encoding provides superior compression ratios for AI-optimized content streams over traditional compression methods. " * 30)
        ]
        
        print(f"\n🧪 Raw vs Auditable Compression Comparison:")
        print("-" * 60)
        
        for test_name, test_data in test_cases:
            print(f"\n📊 {test_name} Test ({len(test_data):,} bytes):")
            
            # Send comparison request
            message = {
                "type": "compare_compression",
                "text": test_data
            }
            
            server._send_websocket_frame_client(client_socket, json.dumps(message))
            response_data = server._receive_websocket_frame_client(client_socket)
            
            if response_data:
                response = json.loads(response_data.decode('utf-8'))
                
                if response.get("type") == "compression_comparison":
                    original_size = response["original_size"]
                    
                    for mode, result in response["results"].items():
                        print(f"   {mode.upper()} Mode:")
                        print(f"     Compressed: {result['compressed_size']:,} bytes")
                        print(f"     Ratio: {result['compression_ratio']:.3f}:1")
                        print(f"     Time: {result['compression_time_ms']:.2f}ms")
                        print(f"     Efficiency: {result['efficiency']}")
                        print(f"     Integrity: {'✅' if result['integrity_check'] else '❌'}")
                        
                        if result['compression_ratio'] > 1.0:
                            savings = (1 - 1/result['compression_ratio']) * 100
                            print(f"     Savings: {savings:.1f}%")
                        else:
                            expansion = (result['compression_ratio'] - 1) * -100
                            print(f"     Expansion: {expansion:.1f}%")
        
        client_socket.close()
        
    finally:
        server.stop_server()
    
    print("\n✅ Dual-mode compression test complete!")

# Add client helper methods to server class
def _send_websocket_frame_client(self, client_socket, data):
    """Send WebSocket frame from client (with masking)."""
    data_bytes = data.encode('utf-8')
    frame = bytearray([0x81])  # FIN + text
    
    if len(data_bytes) < 126:
        frame.append(0x80 | len(data_bytes))
    else:
        frame.append(0x80 | 126)
        frame.extend(struct.pack('>H', len(data_bytes)))
    
    mask = os.urandom(4)
    frame.extend(mask)
    masked_payload = bytes(data_bytes[i] ^ mask[i % 4] for i in range(len(data_bytes)))
    frame.extend(masked_payload)
    
    client_socket.send(frame)

def _receive_websocket_frame_client(self, client_socket):
    """Receive WebSocket frame from client perspective."""
    header = client_socket.recv(2)
    if len(header) != 2:
        return None
    
    byte1, byte2 = header
    payload_length = byte2 & 0x7F
    
    if payload_length == 126:
        length_data = client_socket.recv(2)
        payload_length = struct.unpack('>H', length_data)[0]
    elif payload_length == 127:
        length_data = client_socket.recv(8)
        payload_length = struct.unpack('>Q', length_data)[0]
    
    payload = client_socket.recv(payload_length)
    return payload

# Monkey patch helper methods
DualModeWebSocketServer._send_websocket_frame_client = _send_websocket_frame_client
DualModeWebSocketServer._receive_websocket_frame_client = _receive_websocket_frame_client

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    dual_mode_compression_demo()
