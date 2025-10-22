#!/usr/bin/env python3
"""
AURA WebSocket Large File Streaming Test

This script tests AURA's ability to compress and stream a large file
in real-time over a WebSocket connection.

- The server starts in a background task.
- The client reads a large file in chunks and streams it to the server.
- The server receives each chunk, compresses it, and streams it back immediately.
- The client receives the compressed chunks, decompresses them, and writes them to a new file.
- Finally, the script verifies that the original and decompressed files are identical.
"""
import asyncio
import websockets
import sys
import os
import threading
import time
import hashlib

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
LARGE_FILE_PATH = "large_test_file.txt"
DECOMPRESSED_FILE_PATH = "large_test_file.decompressed.txt"
CHUNK_SIZE = 65536  # 64KB chunks
STREAM_END_MARKER = b"__AURA_STREAM_END__"

HANDSHAKE_CORPUS = """
GPT language model transformer neural network attention mechanism fine-tuning reinforcement learning human feedback RLHF tokenization embedding vector space semantic similarity API inference completion chat conversation system user assistant temperature top_p nucleus sampling beam search greedy decoding prompt engineering few-shot learning in-context learning natural language processing computer vision multimodal training data supervised learning unsupervised learning model parameters weights biases gradients backpropagation.
The transformer architecture utilizes self-attention mechanisms for natural language processing tasks. Deep learning models require extensive hyperparameter tuning including learning rate optimization, batch normalization, and dropout regularization.
{"id": "chatcmpl-123", "object": "chat.completion", "model": "gpt-4", "content": "The transformer architecture revolutionized natural language processing."}
"""

# --- 2. Server Implementation ---
aura_compressor = None

async def server_handler(websocket, path=None):
    """Handles a client connection, compressing and echoing chunks."""
    print("[Server] 🔗 Client connected for streaming.")
    total_received = 0
    total_sent = 0
    try:
        async for message in websocket:
            if message == STREAM_END_MARKER:
                await websocket.send(STREAM_END_MARKER)
                break

            total_received += len(message)
            compressed_chunk = aura_compressor.compress_raw(message)
            total_sent += len(compressed_chunk)
            await websocket.send(compressed_chunk)
        
        print(f"[Server] 📥 Total received: {total_received / 1024:.2f} KB")
        print(f"[Server] 📦 Total sent (compressed): {total_sent / 1024:.2f} KB")

    except websockets.exceptions.ConnectionClosed:
        print("[Server] 🔌 Client disconnected.")
    except Exception as e:
        print(f"[Server] ❌ Error: {e}")

# --- 3. Client Implementation ---
async def run_client():
    """Connects, streams a large file, and verifies the result."""
    uri = f"ws://{HOST}:{PORT}"
    print(f"[Client] 🚀 Connecting to {uri}")

    if not os.path.exists(LARGE_FILE_PATH):
        print(f"[Client] ❌ Error: Large file not found at '{LARGE_FILE_PATH}'")
        return

    # Clean up previous decompressed file if it exists
    if os.path.exists(DECOMPRESSED_FILE_PATH):
        os.remove(DECOMPRESSED_FILE_PATH)

    try:
        async with websockets.connect(uri, max_size=2**20 * 10) as websocket: # Increase max message size
            print("[Client] ✅ Connection successful.")

            aura_decompressor = AuraTransceiver()
            aura_decompressor.perform_handshake(HANDSHAKE_CORPUS)
            print("[Client] ✅ Handshake complete.")

            # --- Streaming Upload ---
            print(f"[Client] 📤 Starting to stream '{LARGE_FILE_PATH}'...")
            total_sent = 0
            with open(LARGE_FILE_PATH, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    await websocket.send(chunk)
                    total_sent += len(chunk)
            await websocket.send(STREAM_END_MARKER)
            print(f"[Client] 📤 Finished sending {total_sent / 1024:.2f} KB.")

            # --- Streaming Download and Decompression ---
            print("[Client] 📥 Receiving compressed stream...")
            total_received = 0
            with open(DECOMPRESSED_FILE_PATH, "wb") as f:
                while True:
                    compressed_chunk = await websocket.recv()
                    if compressed_chunk == STREAM_END_MARKER:
                        break
                    total_received += len(compressed_chunk)
                    decompressed_chunk = aura_decompressor.decompress_raw(compressed_chunk)
                    f.write(decompressed_chunk.encode('utf-8'))
            print(f"[Client] 📥 Finished receiving {total_received / 1024:.2f} KB (compressed).")

            # --- Verification ---
            print("\n" + "="*40)
            print("📊 VERIFICATION")
            print("="*40)
            original_hash = hashlib.sha256(open(LARGE_FILE_PATH, 'rb').read()).hexdigest()
            decompressed_hash = hashlib.sha256(open(DECOMPRESSED_FILE_PATH, 'rb').read()).hexdigest()

            ratio = total_sent / total_received if total_received > 0 else 0
            print(f"   Original Size:     {total_sent / (1024*1024):.2f} MB")
            print(f"   Compressed Size:   {total_received / (1024*1024):.2f} MB")
            print(f"   Compression Ratio: {ratio:.2f}:1")
            print(f"   Original SHA-256:    {original_hash}")
            print(f"   Decompressed SHA-256: {decompressed_hash}")

            if original_hash == decompressed_hash:
                print("   Integrity Check:   ✅ PASS")
                print("\n🎉 SUCCESS: Large file streaming with AURA is working!")
            else:
                print("   Integrity Check:   ❌ FAIL")
            print("="*40 + "\n")

    except ConnectionRefusedError:
        print(f"[Client] ❌ Connection refused. Server not ready?")
    except Exception as e:
        print(f"[Client] ❌ An unexpected error occurred: {e}")
    finally:
        # Clean up decompressed file
        if os.path.exists(DECOMPRESSED_FILE_PATH):
            os.remove(DECOMPRESSED_FILE_PATH)


# --- 4. Main Execution (Identical to previous test) ---
def main():
    """Runs the server in a separate thread and the client in the main thread."""
    stop_server_event = threading.Event()

    def server_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_and_wait():
            stop_future = loop.create_future()
            
            def on_stop_set():
                if not stop_future.done():
                    loop.call_soon_threadsafe(stop_future.set_result, None)

            stop_server_event.set = on_stop_set
            
            global aura_compressor
            print("[Server] 🔥 Initializing...")
            aura_compressor = AuraTransceiver()
            aura_compressor.perform_handshake(HANDSHAKE_CORPUS)
            print("[Server] ✅ Handshake complete.")

            async with websockets.serve(server_handler, HOST, PORT, max_size=2**20 * 10):
                print(f"[Server] 🚀 Listening on ws://{HOST}:{PORT}")
                await stop_future
                server.close()
                await server.wait_closed()
        
        loop.run_until_complete(run_and_wait())
        print("[Server] 🛑 Stopped.")

    server_thread = threading.Thread(target=server_loop, daemon=True)
    server_thread.start()
    
    print("[Main] ⏰ Waiting for server to initialize...")
    time.sleep(2) 

    try:
        asyncio.run(run_client())
    finally:
        print("[Main] 🛑 Signaling server to stop.")
        stop_server_event.set() 
        server_thread.join(timeout=5)
        print("[Main] ✅ Test complete.")

if __name__ == "__main__":
    main()
