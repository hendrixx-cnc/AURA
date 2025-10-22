import asyncio
import websockets
import threading
import time
import os
import sys

# --- Setup Python Path ---
# This allows the script to find the aura_compressor module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'packages/aura-compressor-py/src')))

try:
    from aura_compressor.streamer import AuraTransceiver, HANDSHAKE_MAGIC
except ImportError:
    print("❌ AURA modules not available. Ensure the path is correct.")
    sys.exit(1)

# --- Configuration ---
HOST = 'localhost'
PORT = 8765
CHUNK_SIZE = 1460
TEST_FILE = 'test.txt'
# Limit the number of chunks to avoid excessively long tests
TOTAL_CHUNKS_TO_SEND = 50

# --- Global State ---
reconstructed_data = ""
stop_server_flag = asyncio.Event()
client_finished_flag = asyncio.Event()
total_original_size = 0
total_compressed_size = 0

# --- WebSocket Server ---
class WebSocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = None

    async def handler(self, websocket):
        """
        Handles a single client connection. Each client gets its own
        AuraTransceiver instance to maintain independent adaptive state.
        """
        global reconstructed_data, total_compressed_size
        print("Server: Client connected.")
        
        # Instantiate a transceiver for this specific connection
        transceiver = AuraTransceiver(enable_server_audit=True)

        try:
            # 1. Handshake (server initiates and sends to client)
            handshake_packet = transceiver.perform_handshake()
            await websocket.send(handshake_packet)
            print("Server: Handshake sent.")

            # 2. Main receive loop
            while not stop_server_flag.is_set():
                try:
                    packet = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    
                    if isinstance(packet, str) and packet == "END_OF_STREAM":
                        print("Server: Received end of stream signal.")
                        client_finished_flag.set()
                        break

                    if isinstance(packet, (bytes, bytearray)):
                        packet_bytes = bytes(packet)
                        
                        # Handle refresh handshake packets
                        if packet_bytes.startswith(HANDSHAKE_MAGIC):
                            transceiver.receive_handshake(packet_bytes)
                            print("Server: Refresh handshake applied.")
                            continue
                        
                        total_compressed_size += len(packet_bytes)
                        
                        # Decompress returns text for data packets, None for dict updates
                        decompressed_chunk = transceiver.decompress(packet_bytes)
                        
                        if decompressed_chunk:
                            reconstructed_data += decompressed_chunk
                    else:
                        print("Server: Received unexpected non-bytes packet type, ignoring.")

                except asyncio.TimeoutError:
                    # This is normal if the client is idle, just continue waiting
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("Server: Client disconnected.")
                    break
        
        finally:
            print("Server: Handler loop finished.")

    async def start(self):
        """Starts the WebSocket server and waits for the stop signal."""
        print(f"Server: Starting WebSocket server on {self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port, max_size=2**20) as server:
            self.server = server
            await stop_server_flag.wait()
        print("Server: WebSocket server stopped.")

    def run(self):
        """Entry point for the server thread."""
        # Each thread needs its own event loop
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(self.start())

def run_server_thread():
    """Function to run the server in a separate thread."""
    server_instance = WebSocketServer(HOST, PORT)
    server_instance.run()

# --- WebSocket Client ---
async def run_client():
    """Connects to the server, streams a file, and signals completion."""
    global total_original_size
    uri = f"ws://{HOST}:{PORT}"
    try:
        async with websockets.connect(uri, max_size=2**20) as websocket:
            print("Client: Connected to server.")
            transceiver = AuraTransceiver()

            # 1. Handshake - receive server packet
            server_handshake = await websocket.recv()
            if not isinstance(server_handshake, (bytes, bytearray)):
                raise RuntimeError("Handshake payload must be bytes.")
            transceiver.receive_handshake(bytes(server_handshake))
            print("Client: Handshake completed.")

            # 2. Read file and stream in chunks
            with open(TEST_FILE, 'r', encoding='utf-8') as f:
                chunks_sent = 0
                while (chunk := f.read(CHUNK_SIZE)) and chunks_sent < TOTAL_CHUNKS_TO_SEND:
                    total_original_size += len(chunk.encode('utf-8'))
                    
                    # Compress adaptively, which returns a list of packets
                    packets = transceiver.compress(chunk, adaptive=True)
                    
                    for packet in packets:
                        await websocket.send(packet)
                    
                    # If encoder recommends refreshing the entropy tree, send new handshake
                    if transceiver.needs_entropy_refresh():
                        refresh_packet = transceiver.generate_refresh_handshake()
                        await websocket.send(refresh_packet)
                        print("Client: Sent refresh handshake.")
                    
                    chunks_sent += 1
                    print(f"Client: Sent chunk {chunks_sent}/{TOTAL_CHUNKS_TO_SEND} ({len(packets)} packets)")
                    await asyncio.sleep(0.01) # Prevent overwhelming the server

            # 3. Signal end of stream
            await websocket.send("END_OF_STREAM")
            print("Client: Sent end of stream signal.")

    except Exception as e:
        print(f"Client: An error occurred: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(TEST_FILE):
        print(f"Error: Test file '{TEST_FILE}' not found.")
    else:
        # 1. Start the server in a background thread
        server_thread = threading.Thread(target=run_server_thread, daemon=True)
        server_thread.start()
        time.sleep(2) # Give the server a moment to start up

        # 2. Run the client
        try:
            asyncio.run(run_client())

            # 3. Wait for the server to confirm it received the end signal
            print("Main: Waiting for server to process final chunks...")
            try:
                asyncio.run(asyncio.wait_for(client_finished_flag.wait(), timeout=10))
            except (asyncio.TimeoutError, TimeoutError):
                print("Main: Timed out waiting for server confirmation.")

        finally:
            # 4. Cleanly shut down the server
            print("Main: Stopping server...")
            stop_server_flag.set()
            server_thread.join(timeout=5)
            print("Main: Server stopped.")

            # 5. Verification
            print("\n" + "="*20 + " Verification " + "="*20)
            
            # Read the exact portion of the original file that was sent
            original_subset = ""
            with open(TEST_FILE, 'r', encoding='utf-8') as f:
                 original_subset = f.read(CHUNK_SIZE * TOTAL_CHUNKS_TO_SEND)

            print(f"Original data sent:    {total_original_size} bytes")
            print(f"Total compressed size: {total_compressed_size} bytes")
            
            if total_original_size > 0:
                compression_ratio = total_compressed_size / total_original_size
                print(f"Overall Compression Ratio: {compression_ratio:.4f}")
                if compression_ratio < 1:
                    print(f"✅ Compression successful: Saved {((1 - compression_ratio) * 100):.2f}%")
                else:
                    print(f"❌ Data expanded by {((compression_ratio - 1) * 100):.2f}%")
            
            print("-" * 54)
            print(f"Original data length:      {len(original_subset)}")
            print(f"Reconstructed data length: {len(reconstructed_data)}")

            if original_subset == reconstructed_data:
                print("✅ Data integrity check passed. Reconstructed data matches original.")
            else:
                print("❌ Data integrity check failed. Reconstructed data does not match original.")
                if len(original_subset) != len(reconstructed_data):
                    print(f"   Length mismatch is the first issue.")
                
                # Find the first point of divergence
                for i, (o, r) in enumerate(zip(original_subset, reconstructed_data)):
                    if o != r:
                        print(f"   Mismatch at index {i}:")
                        print(f"   Original: ...{original_subset[max(0, i-20):i+20]}...")
                        print(f"   Recon:    ...{reconstructed_data[max(0, i-20):i+20]}...")
                        break
            print("="*54)
