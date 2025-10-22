import sys, os
sys.path.insert(0, "packages/aura-compressor-py/src")
from aura_compressor.streamer import AuraTransceiver

t = AuraTransceiver(literal_frequency_threshold=0.1, min_compression_size=10)
t.perform_handshake(text_sample="hello world this is a test")

text = "hello @ world # test"
packets = t.compress(text, adaptive=False)
print(f"Compressed {len(text)} bytes into {len(packets[0])} bytes")

try:
    result = t.decompress(packets[0])
    print(f"Original:     '{text}'")
    print(f"Decompressed: '{result}'")
    print(f"Match: {result == text}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
