#!/usr/bin/env python3
"""
AURA WebSocket Packet Compression Test

This script tests AURA's ability to compress a standard TCP-sized packet (1460 bytes)
by at least 50% in a real-time WebSocket stream.

- The server starts in a background task.
- The client reads a large file in 1460-byte chunks.
- The server receives, compresses, and returns each chunk.
- The client verifies the compression ratio and overall file integrity.
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
CHUNK_SIZE = 1460  # Standard TCP data payload size
TARGET_COMPRESSION_RATIO = 2.0
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
    try:
        async for message in websocket:
            if message == STREAM_END_MARKER:
                await websocket.send(STREAM_END_MARKER)
                break
            
            # Message is received as bytes, decode to string for AURA
            text_chunk = message.decode('utf-8', errors='ignore')
            compressed_chunk = aura_compressor.compress_raw(text_chunk)
            await websocket.send(compressed_chunk)
            
    except websockets.exceptions.ConnectionClosed:
        pass # Client disconnected, which is expected.
    except Exception as e:
        print(f"[Server] ❌ Error: {e}")

# --- 3. Client Implementation ---
async def run_client():
    """Connects, streams file chunks, and verifies compression."""
    uri = f"ws://{HOST}:{PORT}"
    print(f"[Client] 🚀 Connecting to {uri}")

    if not os.path.exists(LARGE_FILE_PATH):
        print(f"[Client] ❌ Error: File not found at '{LARGE_FILE_PATH}'")
        return

    if os.path.exists(DECOMPRESSED_FILE_PATH):
        os.remove(DECOMPRESSED_FILE_PATH)

    try:
        async with websockets.connect(uri, max_size=2**20) as websocket:
            print("[Client] ✅ Connection successful.")

            aura_decompressor = AuraTransceiver()
            aura_decompressor.perform_handshake(HANDSHAKE_CORPUS)
            print("[Client] ✅ Handshake complete.")

            total_sent = 0
            total_received = 0
            chunks_meeting_target = 0
            total_chunks = 0

            # --- Streaming and Verification ---
            print(f"[Client] 📤 Streaming '{LARGE_FILE_PATH}' in {CHUNK_SIZE}-byte chunks...")
            with open(LARGE_FILE_PATH, "rb") as read_file, open(DECOMPRESSED_FILE_PATH, "wb") as write_file:
                while True:
                    chunk = read_file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    total_chunks += 1
                    await websocket.send(chunk)
                    total_sent += len(chunk)

                    compressed_chunk = await websocket.recv()
                    total_received += len(compressed_chunk)

                    # Check if this chunk meets the compression target
                    ratio = len(chunk) / len(compressed_chunk) if len(compressed_chunk) > 0 else 0
                    if ratio >= TARGET_COMPRESSION_RATIO:
                        chunks_meeting_target += 1

                    decompressed_chunk = aura_decompressor.decompress_raw(compressed_chunk)
                    write_file.write(decompressed_chunk.encode('utf-8'))

            await websocket.send(STREAM_END_MARKER)
            await websocket.recv() # Wait for server to acknowledge end

            # --- Final Verification ---
            print("\n" + "="*50)
            print("📊 VERIFICATION RESULTS")
            print("="*50)
            original_hash = hashlib.sha256(open(LARGE_FILE_PATH, 'rb').read()).hexdigest()
            decompressed_hash = hashlib.sha256(open(DECOMPRESSED_FILE_PATH, 'rb').read()).hexdigest()

            overall_ratio = total_sent / total_received if total_received > 0 else 0
            success_percentage = (chunks_meeting_target / total_chunks) * 100 if total_chunks > 0 else 0

            print(f"   Chunk Size:              {CHUNK_SIZE} bytes")
            print(f"   Target Compression Ratio:  {TARGET_COMPRESSION_RATIO:.2f}:1")
            print("-" * 50)
            print(f"   Total Chunks Processed:    {total_chunks}")
            print(f"   Chunks Meeting Target:     {chunks_meeting_target} ({success_percentage:.2f}%)")
            print("-" * 50)
            print(f"   Overall Compression Ratio: {overall_ratio:.2f}:1")
            print(f"   Original SHA-256:          {original_hash}")
            print(f"   Decompressed SHA-256:       {decompressed_hash}")

            if original_hash == decompressed_hash and success_percentage > 95:
                print("\n   Integrity Check:           ✅ PASS")
                print("   Compression Target:        ✅ ACHIEVED")
                print("\n🎉 SUCCESS: AURA consistently compresses TCP-sized packets by at least 2:1.")
            elif original_hash == decompressed_hash:
                print("\n   Integrity Check:           ✅ PASS")
                print("   Compression Target:        ❌ FAILED")
                print("\n⚠️ WARNING: File integrity is good, but compression target was not met.")
            else:
                print("\n   Integrity Check:           ❌ FAIL")
                print("\n😞 ERROR: File content mismatch after decompression.")
            print("="*50 + "\n")

    except Exception as e:
        print(f"[Client] ❌ An unexpected error occurred: {e}")
    finally:
        if os.path.exists(DECOMPRESSED_FILE_PATH):
            os.remove(DECOMPRESSED_FILE_PATH)

# --- 4. Main Execution ---
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

            server = await websockets.serve(server_handler, HOST, PORT, max_size=2**20)
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
