#!/usr/bin/env python3
"""
WebSocket AURA Streaming with Proper Handshake Testing

This implementation creates a real WebSocket server/client that:
1. Performs AURA handshake over WebSocket
2. Tests compression effectiveness after handshake
3. Measures real network performance
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
except ImportError:
    print("Warning: AURA modules not available. Using mock compression.")
    AuraTransceiver = None

@dataclass
class StreamingMetrics:
    """Comprehensive streaming performance metrics."""
    handshake_time_ms: float = 0.0
    handshake_size_bytes: int = 0
    messages_sent: int = 0
    total_original_bytes: int = 0
    total_compressed_bytes: int = 0
    total_transmission_time_ms: float = 0.0
    avg_compression_ratio: float = 1.0
    network_overhead_bytes: int = 0

class SimpleWebSocketServer:
    """
    Minimal WebSocket server implementation using standard library only.
    Handles WebSocket handshake and basic frame parsing.
    """
    
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.aura_transceiver = None
        self.metrics = StreamingMetrics()
        
    def start_server(self):
        """Start the WebSocket server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        logging.info(f"AURA WebSocket Server started on {self.host}:{self.port}")
        
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
        """Handle WebSocket client connection."""
        try:
            # Perform WebSocket handshake
            if not self.websocket_handshake(client_socket):
                logging.error("WebSocket handshake failed")
                return
            
            # Initialize AURA transceiver
            if AuraTransceiver:
                self.aura_transceiver = AuraTransceiver()
                
                # Send AURA handshake
                handshake_start = time.time()
                sample_text = "Real-time WebSocket streaming with AURA compression protocol test data"
                handshake_data = self.aura_transceiver.perform_handshake(sample_text)
                handshake_time = (time.time() - handshake_start) * 1000
                
                self.metrics.handshake_time_ms = handshake_time
                self.metrics.handshake_size_bytes = len(handshake_data)
                
                # Send handshake to client
                handshake_message = {
                    "type": "aura_handshake",
                    "handshake_data": base64.b64encode(handshake_data).decode('ascii'),
                    "handshake_time_ms": handshake_time,
                    "ready": True
                }
                
                self.send_websocket_frame(client_socket, json.dumps(handshake_message))
                logging.info(f"AURA handshake sent: {len(handshake_data)} bytes in {handshake_time:.2f}ms")
            
            # Handle incoming messages
            while self.running:
                frame_data = self.receive_websocket_frame(client_socket)
                if not frame_data:
                    break
                
                try:
                    message = json.loads(frame_data.decode('utf-8'))
                    response = self.process_message(message)
                    
                    if response:
                        self.send_websocket_frame(client_socket, json.dumps(response))
                        
                except json.JSONDecodeError:
                    logging.error("Invalid JSON received")
                    
        except Exception as e:
            logging.error(f"Error handling client {client_addr}: {e}")
        finally:
            client_socket.close()
            logging.info(f"Client disconnected: {client_addr}")
    
    def websocket_handshake(self, client_socket: socket.socket) -> bool:
        """Perform WebSocket handshake."""
        try:
            # Receive HTTP request
            request = client_socket.recv(4096).decode('utf-8')
            
            # Extract WebSocket key
            lines = request.split('\r\n')
            websocket_key = None
            for line in lines:
                if line.startswith('Sec-WebSocket-Key:'):
                    websocket_key = line.split(': ')[1]
                    break
            
            if not websocket_key:
                return False
            
            # Generate accept key
            magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept_key = base64.b64encode(
                hashlib.sha1((websocket_key + magic_string).encode()).digest()
            ).decode()
            
            # Send handshake response
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
        
        # First byte: FIN (1) + opcode (1 for text)
        frame.append(0x81)
        
        # Payload length
        if len(data_bytes) < 126:
            frame.append(len(data_bytes))
        elif len(data_bytes) < 65536:
            frame.append(126)
            frame.extend(struct.pack('>H', len(data_bytes)))
        else:
            frame.append(127)
            frame.extend(struct.pack('>Q', len(data_bytes)))
        
        # Payload
        frame.extend(data_bytes)
        
        client_socket.send(frame)
    
    def receive_websocket_frame(self, client_socket: socket.socket) -> Optional[bytes]:
        """Receive WebSocket frame."""
        try:
            # Read first two bytes
            header = client_socket.recv(2)
            if len(header) != 2:
                return None
            
            # Parse header
            byte1, byte2 = header
            fin = (byte1 & 0x80) != 0
            opcode = byte1 & 0x0F
            masked = (byte2 & 0x80) != 0
            payload_length = byte2 & 0x7F
            
            # Handle extended payload length
            if payload_length == 126:
                length_data = client_socket.recv(2)
                payload_length = struct.unpack('>H', length_data)[0]
            elif payload_length == 127:
                length_data = client_socket.recv(8)
                payload_length = struct.unpack('>Q', length_data)[0]
            
            # Read mask if present
            mask = None
            if masked:
                mask = client_socket.recv(4)
            
            # Read payload
            payload = client_socket.recv(payload_length)
            
            # Unmask if necessary
            if masked and mask:
                payload = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
            
            return payload
            
        except Exception as e:
            logging.error(f"Error receiving WebSocket frame: {e}")
            return None
    
    def process_message(self, message: Dict) -> Optional[Dict]:
        """Process incoming message and generate response."""
        msg_type = message.get("type")
        
        if msg_type == "ping":
            return {"type": "pong", "timestamp": time.time()}
        
        elif msg_type == "test_compression" and self.aura_transceiver:
            text = message.get("text", "")
            
            compression_start = time.time()
            
            try:
                # Compress using AURA
                compressed = self.aura_transceiver.compress_chunk(text)
                compression_time = (time.time() - compression_start) * 1000
                
                # Calculate metrics
                original_size = len(text)
                compressed_size = len(compressed)
                compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
                
                # Update metrics
                self.metrics.messages_sent += 1
                self.metrics.total_original_bytes += original_size
                self.metrics.total_compressed_bytes += compressed_size
                self.metrics.total_transmission_time_ms += compression_time
                
                # Calculate running average
                if self.metrics.total_compressed_bytes > 0:
                    self.metrics.avg_compression_ratio = self.metrics.total_original_bytes / self.metrics.total_compressed_bytes
                
                return {
                    "type": "compression_result",
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": round(compression_ratio, 3),
                    "compression_time_ms": round(compression_time, 2),
                    "compressed_data": base64.b64encode(compressed).decode('ascii'),
                    "metrics": {
                        "total_messages": self.metrics.messages_sent,
                        "avg_compression_ratio": round(self.metrics.avg_compression_ratio, 3),
                        "total_original_bytes": self.metrics.total_original_bytes,
                        "total_compressed_bytes": self.metrics.total_compressed_bytes
                    }
                }
                
            except Exception as e:
                return {
                    "type": "error",
                    "message": f"Compression failed: {str(e)}"
                }
        
        elif msg_type == "get_metrics":
            return {
                "type": "metrics",
                "handshake_time_ms": self.metrics.handshake_time_ms,
                "handshake_size_bytes": self.metrics.handshake_size_bytes,
                "messages_processed": self.metrics.messages_sent,
                "avg_compression_ratio": round(self.metrics.avg_compression_ratio, 3),
                "total_data_processed": self.metrics.total_original_bytes,
                "total_compressed": self.metrics.total_compressed_bytes
            }
        
        return {"type": "unknown", "message": "Unknown message type"}
    
    def stop_server(self):
        """Stop the WebSocket server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


class WebSocketAuraClient:
    """Simple WebSocket client for testing AURA compression."""
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.handshake_complete = False
        
    def connect(self, host="localhost", port=8765):
        """Connect to WebSocket server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            
            # Send WebSocket handshake
            key = base64.b64encode(os.urandom(16)).decode()
            handshake = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {host}:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "\r\n"
            )
            
            self.socket.send(handshake.encode())
            
            # Receive handshake response
            response = self.socket.recv(4096).decode()
            
            if "101 Switching Protocols" in response:
                self.connected = True
                logging.info("WebSocket connection established")
                return True
            else:
                logging.error("WebSocket handshake failed")
                return False
                
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False
    
    def send_message(self, message: Dict) -> Optional[Dict]:
        """Send message and receive response."""
        if not self.connected:
            return None
        
        try:
            # Send message
            self._send_websocket_frame(json.dumps(message))
            
            # Receive response
            response_data = self._receive_websocket_frame()
            if response_data:
                return json.loads(response_data.decode('utf-8'))
            
        except Exception as e:
            logging.error(f"Message exchange failed: {e}")
        
        return None
    
    def _send_websocket_frame(self, data: str):
        """Send WebSocket frame (client version with masking)."""
        data_bytes = data.encode('utf-8')
        frame = bytearray()
        
        # First byte: FIN (1) + opcode (1 for text)
        frame.append(0x81)
        
        # Payload length with mask bit
        if len(data_bytes) < 126:
            frame.append(0x80 | len(data_bytes))  # Set mask bit
        elif len(data_bytes) < 65536:
            frame.append(0x80 | 126)  # Set mask bit
            frame.extend(struct.pack('>H', len(data_bytes)))
        else:
            frame.append(0x80 | 127)  # Set mask bit
            frame.extend(struct.pack('>Q', len(data_bytes)))
        
        # Generate mask
        mask = os.urandom(4)
        frame.extend(mask)
        
        # Masked payload
        masked_payload = bytes(data_bytes[i] ^ mask[i % 4] for i in range(len(data_bytes)))
        frame.extend(masked_payload)
        
        self.socket.send(frame)
    
    def _receive_websocket_frame(self) -> Optional[bytes]:
        """Receive WebSocket frame."""
        try:
            # Read first two bytes
            header = self.socket.recv(2)
            if len(header) != 2:
                return None
            
            # Parse header
            byte1, byte2 = header
            payload_length = byte2 & 0x7F
            
            # Handle extended payload length
            if payload_length == 126:
                length_data = self.socket.recv(2)
                payload_length = struct.unpack('>H', length_data)[0]
            elif payload_length == 127:
                length_data = self.socket.recv(8)
                payload_length = struct.unpack('>Q', length_data)[0]
            
            # Read payload (server doesn't mask)
            payload = self.socket.recv(payload_length)
            return payload
            
        except Exception as e:
            logging.error(f"Error receiving frame: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from server."""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.connected = False


def websocket_aura_demo():
    """Demonstrate AURA compression over WebSocket with proper handshake."""
    
    print("🚀 AURA WebSocket Streaming Demo")
    print("=" * 50)
    
    # Start server in background
    server = SimpleWebSocketServer()
    server_thread = threading.Thread(target=server.start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Give server time to start
    time.sleep(1.0)
    
    try:
        # Connect client
        client = WebSocketAuraClient()
        if not client.connect():
            print("❌ Failed to connect to WebSocket server")
            return
        
        print("✅ WebSocket connection established")
        
        # Wait for AURA handshake
        print("\n📡 Waiting for AURA handshake...")
        handshake_response = client._receive_websocket_frame()
        
        if handshake_response:
            handshake_data = json.loads(handshake_response.decode('utf-8'))
            if handshake_data.get("type") == "aura_handshake":
                print(f"✅ AURA handshake received:")
                print(f"   Size: {len(base64.b64decode(handshake_data['handshake_data']))} bytes")
                print(f"   Time: {handshake_data['handshake_time_ms']:.2f}ms")
                client.handshake_complete = True
        
        if not client.handshake_complete:
            print("❌ AURA handshake failed")
            return
        
        # Simulate a typical AI browser conversation
        conversation_turns = [
            ("user", "Hey ChatGPT, I'm planning a weekend trip to Seattle. Can you give me a quick 3-sentence overview of must-see spots?"),
            ("assistant", "Absolutely! Visit Pike Place Market for local eats, grab a view from the Space Needle, and explore the Museum of Pop Culture for immersive exhibits."),
            ("user", "Nice, thanks! Also, what's the weather usually like in early October?"),
            ("assistant", "Early October is usually mild—expect highs around 60°F (16°C) and a good chance of light rain, so pack layers and a waterproof jacket."),
            ("user", "Perfect. Last question: suggest a two-day itinerary that mixes food, coffee, and a scenic hike."),
            ("assistant", "Day one: Pike Place breakfast, coffee crawl in Capitol Hill, sunset at Kerry Park. Day two: Morning hike at Rattlesnake Ledge, lunch in Ballard, and wrap with dinner in the waterfront district."),
        ]

        print(f"\n🧪 Streaming Common AI Browser Conversation:")
        print("-" * 50)

        for turn, (role, content) in enumerate(conversation_turns, start=1):
            enriched_text = f"[{role.upper()} #{turn}] {content}"
            print(f"\n💬 {enriched_text}")

            start_time = time.time()
            response = client.send_message({
                "type": "test_compression",
                "text": enriched_text
            })
            total_time = (time.time() - start_time) * 1000

            if response and response.get("type") == "compression_result":
                ratio = response["compression_ratio"]
                comp_time = response["compression_time_ms"]

                print(f"   Original: {response['original_size']} bytes")
                print(f"   Compressed: {response['compressed_size']} bytes")
                print(f"   Ratio: {ratio:.3f}:1")
                print(f"   Compression time: {comp_time:.2f}ms")
                print(f"   Total round-trip: {total_time:.2f}ms")

                if ratio > 1.0:
                    savings = (1 - 1/ratio) * 100
                    print(f"   ✅ {savings:.1f}% size reduction")
                else:
                    expansion = (ratio - 1) * 100
                    print(f"   ❌ {expansion:.1f}% size increase")
            else:
                print(f"   ❌ Compression test failed: {response}")
        
        # Get final metrics
        print(f"\n📈 Final Metrics:")
        metrics_response = client.send_message({"type": "get_metrics"})
        
        if metrics_response and metrics_response.get("type") == "metrics":
            m = metrics_response
            print(f"   Handshake: {m['handshake_size_bytes']} bytes in {m['handshake_time_ms']:.2f}ms")
            print(f"   Messages processed: {m['messages_processed']}")
            print(f"   Average compression: {m['avg_compression_ratio']:.3f}:1")
            print(f"   Total data: {m['total_data_processed']:,} → {m['total_compressed']:,} bytes")
        
        client.disconnect()
        
    finally:
        server.stop_server()
    
    print("\n✅ WebSocket AURA streaming demo complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    websocket_aura_demo()
