#!/usr/bin/env python3
"""
AURA WebSocket Bidirectional Test

This single script runs both a WebSocket server and a client to test
AURA's real-time compression.

- The server starts in a background task.
- The client waits for the server to be ready, then connects.
- The client sends a message, receives the compressed response, and verifies it.
- The script coordinates a clean shutdown.
"""
import asyncio
import websockets
import sys
import os
import threading
import time

# --- Setup Python Path ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'packages/aura-compressor-py/src')))

try:
    from aura_compressor.streamer import AuraTransceiver
except ImportError:
    print("❌ AURA modules not available. Ensure the path is correct.")
    sys.exit(1)

# --- 1. Shared Configuration ---
HOST = "localhost"
PORT = 8765
HANDSHAKE_CORPUS = """
GPT language model transformer neural network attention mechanism fine-tuning reinforcement learning human feedback RLHF tokenization embedding vector space semantic similarity API inference completion chat conversation system user assistant temperature top_p nucleus sampling beam search greedy decoding prompt engineering few-shot learning in-context learning natural language processing computer vision multimodal training data supervised learning unsupervised learning model parameters weights biases gradients backpropagation.
The transformer architecture utilizes self-attention mechanisms for natural language processing tasks. Deep learning models require extensive hyperparameter tuning including learning rate optimization, batch normalization, and dropout regularization.
{"id": "chatcmpl-123", "object": "chat.completion", "model": "gpt-4", "content": "The transformer architecture revolutionized natural language processing."}
"""
TEST_MESSAGE = """
The transformer architecture, introduced in "Attention Is All You Need", has become the foundation for most state-of-the-art natural language processing models. Its core innovation is the self-attention mechanism, which allows the model to weigh the importance of different words in the input sequence when processing a particular word. This parallelizable approach overcomes the sequential limitations of recurrent neural networks (RNNs), enabling the training of much larger models on massive datasets.
"""

# --- 2. Server Implementation ---
# Global server-side compressor, initialized by the server thread
aura_compressor = None

async def server_handler(websocket, path=None):
    """Handles a client connection, compresses one message, and sends it back."""
    print("[Server] 🔗 Client connected.")
    try:
        message = await websocket.recv()
        print(f"[Server] 📥 Received {len(message)} bytes.")

        compressed_message = aura_compressor.compress_raw(message)
        print(f"[Server] 📦 Compressed to {len(compressed_message)} bytes.")

        await websocket.send(compressed_message)
        print("[Server] 📤 Sent compressed response.")
    except websockets.exceptions.ConnectionClosed:
        print("[Server] 🔌 Client disconnected.")
    except Exception as e:
        print(f"[Server] ❌ Error: {e}")

async def start_server(stop_event):
    """Initializes and runs the WebSocket server."""
    global aura_compressor
    print("[Server] 🔥 Initializing...")
    aura_compressor = AuraTransceiver()
    aura_compressor.perform_handshake(HANDSHAKE_CORPUS)
    print("[Server] ✅ Handshake complete.")

    async with websockets.serve(server_handler, HOST, PORT) as server:
        print(f"[Server] 🚀 Listening on ws://{HOST}:{PORT}")
        await stop_event.wait() # Keep server running until stop_event is set
        server.close()
        await server.wait_closed()
        print("[Server] 🛑 Stopped.")

# --- 3. Client Implementation ---
async def run_client():
    """Connects, sends a message, and verifies the response."""
    uri = f"ws://{HOST}:{PORT}"
    print(f"[Client] 🚀 Connecting to {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("[Client] ✅ Connection successful.")

            # Initialize client-side decompressor
            aura_decompressor = AuraTransceiver()
            aura_decompressor.perform_handshake(HANDSHAKE_CORPUS)
            print("[Client] ✅ Handshake complete.")

            # Send message
            print(f"[Client] 📤 Sending {len(TEST_MESSAGE)} bytes.")
            await websocket.send(TEST_MESSAGE)

            # Receive and decompress response
            compressed_response = await websocket.recv()
            print(f"[Client] 📥 Received {len(compressed_response)} bytes.")
            
            decompressed_message = aura_decompressor.decompress_raw(compressed_response)
            print(f"[Client] 📦 Decompressed to {len(decompressed_message)} bytes.")

            # Verification
            print("\n" + "="*40)
            print("📊 VERIFICATION")
            print("="*40)
            original_size = len(TEST_MESSAGE.encode('utf-8'))
            compressed_size = len(compressed_response)
            ratio = original_size / compressed_size if compressed_size > 0 else 0
            print(f"   Original Size:     {original_size} bytes")
            print(f"   Compressed Size:   {compressed_size} bytes")
            print(f"   Compression Ratio: {ratio:.2f}:1")

            if decompressed_message.strip().lower() == TEST_MESSAGE.strip().lower():
                print("   Integrity Check:   ✅ PASS")
                print("\n🎉 SUCCESS: Real-time WebSocket compression is working!")
            else:
                print("   Integrity Check:   ❌ FAIL")
                print("\n😞 ERROR: Decompressed message does not match original.")
            print("="*40 + "\n")

    except ConnectionRefusedError:
        print(f"[Client] ❌ Connection refused. Server not ready?")
    except Exception as e:
        print(f"[Client] ❌ An unexpected error occurred: {e}")

# --- 4. Main Execution ---
def main():
    """Runs the server in a separate thread and the client in the main thread."""
    # Use a thread-safe event to signal the server to stop
    stop_server_event = threading.Event()

    def server_loop():
        """The function that will run in the new thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Define a coroutine that will run the server and wait for the stop signal
        async def run_and_wait():
            stop_future = loop.create_future()
            
            def on_stop_set():
                if not stop_future.done():
                    loop.call_soon_threadsafe(stop_future.set_result, None)

            stop_server_event.set = on_stop_set # Monkey-patch the set method
            
            async with websockets.serve(server_handler, HOST, PORT) as server:
                print(f"[Server] 🚀 Listening on ws://{HOST}:{PORT}")
                await stop_future # Wait until the future is resolved
                server.close()
                await server.wait_closed()

        # Initialize and run the server
        global aura_compressor
        print("[Server] 🔥 Initializing...")
        aura_compressor = AuraTransceiver()
        aura_compressor.perform_handshake(HANDSHAKE_CORPUS)
        print("[Server] ✅ Handshake complete.")
        
        loop.run_until_complete(run_and_wait())
        print("[Server] 🛑 Stopped.")

    server_thread = threading.Thread(target=server_loop, daemon=True)
    server_thread.start()
    
    print("[Main] ⏰ Waiting for server to initialize...")
    time.sleep(2) 

    # Run client in the main thread's event loop
    try:
        asyncio.run(run_client())
    finally:
        # Signal server to stop
        print("[Main] 🛑 Signaling server to stop.")
        # The patched set() will resolve the future in the server's loop
        stop_server_event.set() 
        server_thread.join(timeout=5)
        print("[Main] ✅ Test complete.")

if __name__ == "__main__":
    main()
