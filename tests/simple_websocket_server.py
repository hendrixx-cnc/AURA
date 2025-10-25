"""
Simple WebSocket Server for Stress Testing

Copyright (c) 2025 Todd James Hendricks
Licensed under Apache License 2.0
Patent Pending - Application No. 19/366,538
"""

import asyncio
import websockets
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aura_compression.compressor import ProductionHybridCompressor


class SimpleWebSocketServer:
    def __init__(self, host='localhost', port=8765, min_compression_size=35):
        self.host = host
        self.port = port
        self.compressor = ProductionHybridCompressor(
            enable_aura=True,
            enable_audit_logging=False,
            min_compression_size=min_compression_size  # Lowered from 50 to 35 for better compression
        )
        self.connections = 0
        self.messages_processed = 0

    async def handle_client(self, websocket):
        """Handle a client connection"""
        self.connections += 1
        client_id = self.connections
        print(f"Client {client_id} connected")

        try:
            async for message in websocket:
                self.messages_processed += 1

                # Compress the message
                try:
                    compressed, method, metadata = self.compressor.compress(message)

                    # Calculate sizes properly in bytes
                    original_bytes = len(message.encode('utf-8'))
                    compressed_bytes = len(compressed)
                    actual_ratio = original_bytes / compressed_bytes if compressed_bytes > 0 else 1.0

                    # Create response
                    response = {
                        'status': 'ok',
                        'original_message': message,
                        'compressed_size': compressed_bytes,
                        'original_size': original_bytes,
                        'compression_ratio': actual_ratio,
                        'method': method.name,
                        'message_count': self.messages_processed,
                        'metadata': metadata
                    }

                    # Add template_id to top level for easy access (full feedback loop)
                    if metadata and 'template_id' in metadata:
                        response['template_id'] = metadata['template_id']

                    # Send response as JSON
                    await websocket.send(json.dumps(response))

                except Exception as e:
                    error_response = {
                        'status': 'error',
                        'error': str(e),
                        'original_message': message
                    }
                    await websocket.send(json.dumps(error_response))

        except websockets.exceptions.ConnectionClosed:
            print(f"Client {client_id} disconnected")
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")

    async def start(self):
        """Start the WebSocket server"""
        print(f"Starting WebSocket server on {self.host}:{self.port}")
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"Server ready - waiting for connections...")
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    server = SimpleWebSocketServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
