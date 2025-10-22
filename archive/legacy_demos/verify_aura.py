#!/usr/bin/env python3
"""
Simple verification script to check if the AURA file has the correct structure
"""
import struct

def verify_aura_file(filename):
    print(f"Verifying AURA file: {filename}")
    
    try:
        with open(filename, 'rb') as f:
            # Read header
            magic = f.read(4)
            if magic != b'AURA':
                print(f"❌ Invalid magic number: {magic}")
                return False
            print(f"✅ Magic number: {magic.decode('ascii')}")
            
            # Read version
            version = struct.unpack('B', f.read(1))[0]
            print(f"✅ Version: {version}")
            
            # Read manifest length
            manifest_length = struct.unpack('>I', f.read(4))[0]
            print(f"✅ Manifest length: {manifest_length} bytes")
            
            # Calculate file positions
            header_size = 9  # 4 + 1 + 4
            manifest_end = header_size + manifest_length
            
            # Get file size
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            payload_size = file_size - manifest_end
            
            print(f"✅ File structure:")
            print(f"   - Header: {header_size} bytes")
            print(f"   - Manifest: {manifest_length} bytes")
            print(f"   - Payload: {payload_size} bytes")
            print(f"   - Total: {file_size} bytes")
            
            # Try to peek at manifest
            f.seek(header_size)
            manifest_peek = f.read(min(100, manifest_length))
            if manifest_peek.startswith(b'L3M1'):
                print(f"✅ Manifest appears to be L3M format")
            else:
                print(f"✅ Manifest preview: {manifest_peek[:50]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def compare_with_original(aura_file, text_file):
    try:
        with open(text_file, 'r') as f:
            original_content = f.read()
        
        with open(aura_file, 'rb') as f:
            f.seek(0, 2)
            aura_size = f.tell()
        
        print(f"\n📊 Compression Analysis:")
        print(f"   - Original text: {len(original_content)} bytes")
        print(f"   - AURA file: {aura_size} bytes")
        
        if aura_size > len(original_content):
            overhead = aura_size - len(original_content)
            print(f"   - Overhead: +{overhead} bytes (expected for small files)")
            print(f"   - Note: AURA is optimized for larger data streams")
        else:
            ratio = len(original_content) / aura_size
            print(f"   - Compression ratio: {ratio:.2f}:1")
            
    except Exception as e:
        print(f"❌ Error comparing files: {e}")

if __name__ == "__main__":
    success = verify_aura_file("test.aura")
    if success:
        compare_with_original("test.aura", "test.txt")
        print(f"\n🎉 AURA file verification completed successfully!")
    else:
        print(f"\n❌ AURA file verification failed!")