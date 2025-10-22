#!/usr/bin/env python3
"""
Find the exact breakeven point where AURA compression becomes beneficial.
Tests incremental message sizes over WebSocket to find when compression ratio > 1.0
"""
import sys
import os
import time
import json
import socket
import base64
import hashlib
import struct
import threading
from typing import Dict, Optional, List, Tuple

# Import AURA compression components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'aura-compressor-py', 'src'))

try:
    from aura_compressor.streamer import AuraTransceiver
except ImportError:
    print("Warning: AURA modules not available.")
    AuraTransceiver = None

class CompressionBreakevenTester:
    """Test compression efficiency at different message sizes."""
    
    def __init__(self):
        self.server_socket = None
        self.running = False
        self.compressor = None
        self.breakeven_results = []
        
    def start_test_server(self, host="localhost", port=8766):
        """Start a simple test server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)
        self.running = True
        
        print(f"🔧 Test server started on {host}:{port}")
        
        # Initialize AURA compressor
        if AuraTransceiver:
            self.compressor = AuraTransceiver()
            sample = "Testing compression breakeven point with neural networks and machine learning data"
            handshake = self.compressor.perform_handshake(sample)
            print(f"✅ AURA compressor ready (handshake: {len(handshake)} bytes)")
        
        # Wait for single connection
        client_socket, addr = self.server_socket.accept()
        print(f"📡 Client connected: {addr}")
        
        try:
            # Perform WebSocket handshake
            if self.websocket_handshake(client_socket):
                print("✅ WebSocket handshake complete")
                self.handle_breakeven_tests(client_socket)
            else:
                print("❌ WebSocket handshake failed")
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            client_socket.close()
            self.server_socket.close()
    
    def websocket_handshake(self, client_socket: socket.socket) -> bool:
        """Perform WebSocket handshake."""
        try:
            request = client_socket.recv(4096).decode('utf-8')
            
            # Extract WebSocket key
            websocket_key = None
            for line in request.split('\r\n'):
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
            print(f"WebSocket handshake error: {e}")
            return False
    
    def handle_breakeven_tests(self, client_socket: socket.socket):
        """Handle compression breakeven testing."""
        
        # Send ready signal
        ready_msg = {"type": "ready", "compressor_available": self.compressor is not None}
        self.send_websocket_frame(client_socket, json.dumps(ready_msg))
        
        while self.running:
            try:
                frame_data = self.receive_websocket_frame(client_socket)
                if not frame_data:
                    break
                
                message = json.loads(frame_data.decode('utf-8'))
                
                if message.get("type") == "test_size":
                    response = self.test_compression_at_size(message)
                    self.send_websocket_frame(client_socket, json.dumps(response))
                    
                elif message.get("type") == "get_results":
                    response = {
                        "type": "breakeven_results", 
                        "results": self.breakeven_results
                    }
                    self.send_websocket_frame(client_socket, json.dumps(response))
                    
                elif message.get("type") == "stop":
                    break
                    
            except Exception as e:
                print(f"Error handling message: {e}")
                break
    
    def test_compression_at_size(self, message: Dict) -> Dict:
        """Test compression efficiency at specific size."""
        target_size = message.get("size", 100)
        base_pattern = message.get("pattern", "neural network machine learning artificial intelligence ")
        
        # Create text of target size
        pattern_reps = (target_size // len(base_pattern)) + 1
        test_text = (base_pattern * pattern_reps)[:target_size]
        actual_size = len(test_text)
        
        if not self.compressor:
            return {
                "type": "test_result",
                "size": actual_size,
                "compressed_size": actual_size,
                "ratio": 1.0,
                "compression_time_ms": 0,
                "error": "No compressor available"
            }
        
        try:
            # Test compression
            start_time = time.time()
            compressed = self.compressor.compress_chunk(test_text)
            compression_time = (time.time() - start_time) * 1000
            
            # Calculate ratio
            compressed_size = len(compressed)
            ratio = actual_size / compressed_size if compressed_size > 0 else 0
            
            # Test decompression to verify integrity
            try:
                decompressed = self.compressor.decompress_chunk(compressed)
                integrity_ok = (decompressed == test_text)
            except:
                integrity_ok = False
            
            result = {
                "type": "test_result",
                "size": actual_size,
                "compressed_size": compressed_size,
                "ratio": round(ratio, 4),
                "compression_time_ms": round(compression_time, 2),
                "integrity_ok": integrity_ok,
                "shrinks": ratio > 1.0,
                "efficiency": "excellent" if ratio > 2.0 else "good" if ratio > 1.5 else "fair" if ratio > 1.0 else "poor"
            }
            
            # Store result
            self.breakeven_results.append(result)
            
            return result
            
        except Exception as e:
            return {
                "type": "test_result",
                "size": actual_size,
                "error": str(e)
            }
    
    def send_websocket_frame(self, client_socket: socket.socket, data: str):
        """Send WebSocket frame."""
        data_bytes = data.encode('utf-8')
        frame = bytearray([0x81])  # FIN + text opcode
        
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
            print(f"Error receiving frame: {e}")
            return None

class CompressionBreakevenClient:
    """Client to test compression breakeven points."""
    
    def __init__(self):
        self.socket = None
        self.connected = False
    
    def connect(self, host="localhost", port=8766):
        """Connect to test server."""
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
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def send_message(self, message: Dict) -> Optional[Dict]:
        """Send message and receive response."""
        if not self.connected:
            return None
        
        try:
            # Send message
            self.send_websocket_frame(json.dumps(message))
            
            # Receive response
            response_data = self.receive_websocket_frame()
            if response_data:
                return json.loads(response_data.decode('utf-8'))
            
        except Exception as e:
            print(f"Message exchange failed: {e}")
        
        return None
    
    def send_websocket_frame(self, data: str):
        """Send WebSocket frame (client version with masking)."""
        data_bytes = data.encode('utf-8')
        frame = bytearray([0x81])  # FIN + text
        
        if len(data_bytes) < 126:
            frame.append(0x80 | len(data_bytes))
        elif len(data_bytes) < 65516:
            frame.append(0x80 | 126)
            frame.extend(struct.pack('>H', len(data_bytes)))
        else:
            frame.append(0x80 | 127)
            frame.extend(struct.pack('>Q', len(data_bytes)))
        
        # Generate and apply mask
        mask = os.urandom(4)
        frame.extend(mask)
        masked_payload = bytes(data_bytes[i] ^ mask[i % 4] for i in range(len(data_bytes)))
        frame.extend(masked_payload)
        
        self.socket.send(frame)
    
    def receive_websocket_frame(self) -> Optional[bytes]:
        """Receive WebSocket frame."""
        try:
            header = self.socket.recv(2)
            if len(header) != 2:
                return None
            
            byte1, byte2 = header
            payload_length = byte2 & 0x7F
            
            if payload_length == 126:
                length_data = self.socket.recv(2)
                payload_length = struct.unpack('>H', length_data)[0]
            elif payload_length == 127:
                length_data = self.socket.recv(8)
                payload_length = struct.unpack('>Q', length_data)[0]
            
            payload = self.socket.recv(payload_length)
            return payload
            
        except Exception as e:
            print(f"Error receiving frame: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from server."""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.connected = False

def find_compression_breakeven():
    """Find the exact point where AURA compression becomes beneficial."""
    
    print("🎯 Finding AURA Compression Breakeven Point")
    print("=" * 50)
    
    # Start server in background
    tester = CompressionBreakevenTester()
    server_thread = threading.Thread(target=tester.start_test_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Give server time to start
    time.sleep(1.0)
    
    # Connect client
    client = CompressionBreakevenClient()
    if not client.connect():
        print("❌ Failed to connect to test server")
        return
    
    print("✅ Connected to breakeven test server")
    
    # Wait for ready signal
    ready_response = client.receive_websocket_frame()
    if ready_response:
        ready_data = json.loads(ready_response.decode('utf-8'))
        if ready_data.get("compressor_available"):
            print("✅ AURA compressor ready for testing")
        else:
            print("❌ AURA compressor not available")
            return
    
    # Test various sizes to find breakeven point
    print("\n🧪 Testing compression at different sizes...")
    print("Size (bytes) | Compressed | Ratio | Time (ms) | Status")
    print("-" * 60)
    
    # Test incremental sizes
    test_sizes = []
    
    # Small sizes (every 100 bytes from 100 to 1000)
    test_sizes.extend(range(100, 1001, 100))
    
    # Medium sizes (every 500 bytes from 1000 to 5000)
    test_sizes.extend(range(1000, 5001, 500))
    
    # Larger sizes (every 1000 bytes from 5000 to 15000)
    test_sizes.extend(range(5000, 15001, 1000))
    
    # Remove duplicates and sort
    test_sizes = sorted(list(set(test_sizes)))
    
    breakeven_found = False
    breakeven_size = None
    
    for size in test_sizes:
        # Test this size
        response = client.send_message({
            "type": "test_size",
            "size": size,
            "pattern": "neural network machine learning artificial intelligence deep learning transformer attention "
        })
        
        if response and response.get("type") == "test_result":
            r = response
            
            # Format output
            size_str = f"{r['size']:>4}"
            compressed_str = f"{r.get('compressed_size', 0):>10}"
            ratio_str = f"{r.get('ratio', 0):>5.3f}"
            time_str = f"{r.get('compression_time_ms', 0):>7.2f}"
            
            status = "🟢 SHRINKS" if r.get('shrinks', False) else "🔴 EXPANDS"
            
            print(f"{size_str:>12} | {compressed_str} | {ratio_str} | {time_str} | {status}")
            
            # Check if this is the breakeven point
            if r.get('shrinks', False) and not breakeven_found:
                breakeven_found = True
                breakeven_size = r['size']
                print(f"🎯 BREAKEVEN FOUND AT {breakeven_size:,} bytes!")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.01)
    
    # Get final results
    print(f"\n📊 Breakeven Analysis Complete:")
    if breakeven_size:
        print(f"   🎯 Compression becomes beneficial at: {breakeven_size:,} bytes")
        print(f"   📈 Messages smaller than {breakeven_size:,} bytes will expand")
        print(f"   📉 Messages larger than {breakeven_size:,} bytes will compress")
    else:
        print(f"   ❌ No breakeven point found in tested range")
        print(f"   💡 Try testing with larger message sizes")
    
    # Disconnect
    client.send_message({"type": "stop"})
    client.disconnect()
    
    print("\n✅ Breakeven analysis complete!")

if __name__ == "__main__":
    find_compression_breakeven()