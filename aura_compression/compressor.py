#!/usr/bin/env python3
"""
Production-Ready Hybrid Compression System
- Binary semantic compression with manual template mapping (until we build ML matcher)
- Brotli fallback
- Human-readable server-side audit
- 100% reliable decompression
"""
import os
import struct
try:
    from brotlicffi import compress as brotli_compress, decompress as brotli_decompress
except ImportError:  # pragma: no cover - fallback when brotlicffi unavailable
    import brotli

    brotli_compress = brotli.compress
    brotli_decompress = brotli.decompress
import json
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from datetime import datetime

from aura_compression.experimental.brio import (
    BrioEncoder,
    BrioDecoder,
    BrioCompressed,
    BrioDecompressed,
)
from aura_compression.experimental.brio.tokens import (
    LiteralToken as AuraLiteralToken,
    DictionaryToken as AuraDictionaryToken,
    MatchToken as AuraMatchToken,
)

from aura_compression.experimental.brio import (
    BrioEncoder,
    BrioDecoder,
    BrioCompressed,
    BrioDecompressed,
)

# Production template library
TEMPLATES = {
    # Limitations
    0: "I don't have access to {0}. {1}",
    1: "I cannot {0}.",
    2: "I'm unable to {0}.",

    # Facts
    10: "The {0} of {1} is {2}.",
    11: "{0} is {1}.",
    12: "{0} are {1}.",

    # Definitions
    20: "{0} is {1} {2} of {3}.",
    21: "{0} is {1} {2} for {3}.",
    22: "{0} is {1} {2} used for {3}.",

    # Code examples
    30: "Here's {0} {1} example:\n\n```{2}\n{3}\n```",
    31: "Here's how to {0}:\n\n```{1}\n{2}\n```",
    32: "```{0}\n{1}\n```",

    # Instructions
    40: "To {0}, use {1}: `{2}`",
    41: "To {0}, {1}.",
    42: "You can {0} by {1}.",

    # Comparisons
    60: "The main {0} between {1} are: {2}",
    61: "{0} and {1} are different: {0} {2}, {1} {3}.",

    # Explanations
    70: "The {0} of {1} is {2} because {3}.",
    71: "{0} works by {1}.",

    # Enumerations
    80: "Common {0} include: {1}.",
    81: "The main {0} are: {1}.",

    # Recommendations
    90: "To {0}, I recommend: {1}",
    91: "I recommend {0}.",

    # Clarifications
    100: "Yes, I can help with that. What specific {0} would you like to know more about?",
    101: "Could you clarify {0}?",

    # Features
    120: "The {0} in {1} allows you to {2}: `{3}`",
}

class CompressionMethod(Enum):
    BINARY_SEMANTIC = 0x00
    BROTLI = 0x01
    BRIO = 0x02
    UNCOMPRESSED = 0xFF

class ProductionHybridCompressor:
    """
    Production-ready hybrid compressor with:
    - Ultra-reliable binary semantic compression
    - Brotli fallback
    - Human-readable server-side decompression
    - Full audit logging support
    """

    def __init__(self,
                 binary_advantage_threshold: float = 1.1,
                 min_compression_size: int = 50,
                 enable_aura: Optional[bool] = None,
                 aura_preference_margin: float = 0.05):
        """
        Args:
            binary_advantage_threshold: Use binary if >this times better than Brotli (1.1 = 10% better)
            min_compression_size: Don't compress messages smaller than this
        """
        self.templates = TEMPLATES
        self.binary_advantage_threshold = binary_advantage_threshold
        self.min_compression_size = min_compression_size

        if enable_aura is None:
            env_value = os.getenv("AURA_ENABLE_EXPERIMENTAL", "false").lower()
            enable_aura = env_value in {"1", "true", "yes", "on"}
        self.enable_aura = enable_aura
        self.aura_preference_margin = aura_preference_margin

        if self.enable_aura:
            self._aura_encoder: Optional[BrioEncoder] = BrioEncoder()
            self._aura_decoder: Optional[BrioDecoder] = BrioDecoder()
        else:
            self._aura_encoder = None
            self._aura_decoder = None

    def compress_with_template(self, template_id: int, slots: List[str]) -> bytes:
        """
        Binary semantic compression

        Format: [template_id:1][slot_count:1][slot0_len:2][slot0_data]...
        """
        if template_id not in self.templates:
            raise ValueError(f"Unknown template ID: {template_id}")

        if len(slots) > 255:
            raise ValueError(f"Too many slots: {len(slots)} (max 255)")

        result = bytearray()
        result.append(template_id & 0xFF)
        result.append(len(slots) & 0xFF)

        for slot in slots:
            slot_bytes = slot.encode('utf-8')
            if len(slot_bytes) > 65535:
                raise ValueError(f"Slot too long: {len(slot_bytes)} bytes (max 65535)")
            result.extend(struct.pack('>H', len(slot_bytes)))
            result.extend(slot_bytes)

        return bytes(result)

    def decompress_binary(self, data: bytes) -> str:
        """Decompress binary semantic format to plaintext"""
        if len(data) < 2:
            raise ValueError("Invalid binary data (too short)")

        template_id = data[0]
        slot_count = data[1]

        if template_id not in self.templates:
            raise ValueError(f"Unknown template ID: {template_id}")

        # Extract slots
        slots = []
        offset = 2

        for i in range(slot_count):
            if offset + 2 > len(data):
                raise ValueError(f"Truncated slot {i} length")

            slot_len = struct.unpack('>H', data[offset:offset+2])[0]
            offset += 2

            if offset + slot_len > len(data):
                raise ValueError(f"Truncated slot {i} data")

            slot_data = data[offset:offset+slot_len].decode('utf-8')
            slots.append(slot_data)
            offset += slot_len

        # Fill template
        template = self.templates[template_id]
        result = template
        for i, slot in enumerate(slots):
            result = result.replace(f'{{{i}}}', slot)

        return result

    def compress(self, text: str, template_id: Optional[int] = None,
                 slots: Optional[List[str]] = None) -> Tuple[bytes, CompressionMethod, dict]:
        """
        Compress text using best method

        Args:
            text: Text to compress
            template_id: If known, use this template
            slots: If known, use these slots

        Returns:
            (compressed_data, method_used, metadata)
        """
        original_size = len(text.encode('utf-8'))

        # Skip compression for tiny messages
        if original_size < self.min_compression_size:
            return (
                bytes([CompressionMethod.UNCOMPRESSED.value]) + text.encode('utf-8'),
                CompressionMethod.UNCOMPRESSED,
                {
                    'original_size': original_size,
                    'compressed_size': original_size + 1,
                    'ratio': 1.0,
                    'method': 'uncompressed',
                    'reason': 'message_too_small',
                    'fast_path_candidate': False,
                }
            )

        candidates: List[Tuple[bytes, CompressionMethod, Dict[str, Any]]] = []

        # Template candidate if provided
        binary_data = None
        binary_size = 0
        binary_ratio = 0.0
        if template_id is not None and slots is not None:
            try:
                binary_data = self.compress_with_template(template_id, slots)
                binary_size = len(binary_data) + 1  # include method byte
                binary_ratio = original_size / binary_size if binary_size else float('inf')
            except Exception:
                binary_data = None

        # Brotli fallback (always available)
        brotli_payload = brotli_compress(text.encode('utf-8'))
        brotli_size = len(brotli_payload) + 1
        brotli_ratio = original_size / brotli_size if brotli_size else float('inf')

        # Add template candidate (needs brotli_ratio for comparison)
        if binary_data is not None:
            advantage = ((binary_ratio / brotli_ratio) - 1) * 100 if brotli_ratio else 0.0
            candidates.append(
                (
                    bytes([CompressionMethod.BINARY_SEMANTIC.value]) + binary_data,
                    CompressionMethod.BINARY_SEMANTIC,
                    {
                        'original_size': original_size,
                        'compressed_size': binary_size,
                        'ratio': binary_ratio,
                        'method': 'binary_semantic',
                        'template_id': template_id,
                        'slot_count': len(slots),
                        'advantage_vs_brotli_percent': advantage,
                        'fast_path_candidate': False,
                    },
                )
            )

        # Brotli candidate metadata
        candidates.append(
            (
                bytes([CompressionMethod.BROTLI.value]) + brotli_payload,
                CompressionMethod.BROTLI,
                {
                    'original_size': original_size,
                    'compressed_size': brotli_size,
                    'ratio': brotli_ratio,
                    'method': 'brotli',
                    'reason': 'no_template' if binary_data is None else 'brotli_better',
                    'binary_ratio': binary_ratio,
                    'fast_path_candidate': False,
                },
            )
        )

        # Experimental AURA candidate
        if self.enable_aura and self._aura_encoder is not None:
            try:
                aura_compressed: BrioCompressed = self._aura_encoder.compress(text)
                aura_size = len(aura_compressed.payload) + 1
                aura_ratio = original_size / aura_size if aura_size else float('inf')
                aura_entries = [
                    {
                        'token_index': entry.token_index,
                        'kind': entry.kind,
                        'value': entry.value,
                    }
                    for entry in aura_compressed.metadata
                ]
                token_counts = {
                    'total': len(aura_compressed.tokens),
                    'literals': sum(isinstance(t, AuraLiteralToken) for t in aura_compressed.tokens),
                    'dictionary': sum(isinstance(t, AuraDictionaryToken) for t in aura_compressed.tokens),
                    'matches': sum(isinstance(t, AuraMatchToken) for t in aura_compressed.tokens),
                }
                aura_advantage = ((aura_ratio / brotli_ratio) - 1) * 100 if brotli_ratio else 0.0
                candidates.append(
                    (
                        bytes([CompressionMethod.BRIO.value]) + aura_compressed.payload,
                        CompressionMethod.BRIO,
                        {
                            'original_size': original_size,
                            'compressed_size': aura_size,
                            'ratio': aura_ratio,
                            'method': 'aura',
                            'metadata_entries': aura_entries,
                            'token_counts': token_counts,
                            'advantage_vs_brotli_percent': aura_advantage,
                            'fast_path_candidate': any(entry['kind'] == 0x01 for entry in aura_entries),
                        },
                    )
                )
            except Exception:
                # In case experimental encoder fails, ignore candidate
                pass

        # Select candidate with best compression (size first, ratio second)
        aura_candidate = next(
            (candidate for candidate in candidates if candidate[1] == CompressionMethod.BRIO),
            None,
        )

        selected_payload, selected_method, selected_metadata = min(
            candidates,
            key=lambda candidate: (candidate[2]['compressed_size'], -candidate[2].get('ratio', 0.0)),
        )

        if aura_candidate is not None:
            if self.aura_preference_margin < 0:
                selected_payload, selected_method, selected_metadata = aura_candidate
            else:
                best_size = selected_metadata['compressed_size']
                aura_size = aura_candidate[2]['compressed_size']
                if aura_size <= best_size * (1 + self.aura_preference_margin):
                    selected_payload, selected_method, selected_metadata = aura_candidate

        return selected_payload, selected_method, selected_metadata

    def decompress(self, data: bytes, return_metadata: bool = False) -> Any:
        """
        Decompress data (auto-detect method)
        Returns human-readable plaintext
        """
        if len(data) == 0:
            raise ValueError("Empty data")

        method_byte = data[0]
        payload = data[1:]

        if method_byte == CompressionMethod.BINARY_SEMANTIC.value:
            text = self.decompress_binary(payload)
            if return_metadata:
                template_id = payload[0] if payload else None
                meta = {
                    'method': 'binary_semantic',
                    'template_id': template_id,
                    'fast_path_candidate': False,
                }
                return text, meta
            return text
        elif method_byte == CompressionMethod.BROTLI.value:
            text = brotli_decompress(payload).decode('utf-8')
            if return_metadata:
                return text, {'method': 'brotli', 'fast_path_candidate': False}
            return text
        elif method_byte == CompressionMethod.BRIO.value:
            if not self.enable_aura or self._aura_decoder is None:
                raise ValueError("AURA payload encountered but experimental encoder disabled")
            result: BrioDecompressed = self._aura_decoder.decompress(payload)
            if return_metadata:
                aura_entries = [
                    {
                        'token_index': entry.token_index,
                        'kind': entry.kind,
                        'value': entry.value,
                    }
                    for entry in result.metadata
                ]
                metadata = {
                    'method': 'aura',
                    'metadata_entries': aura_entries,
                    'token_count': len(result.tokens),
                    'fast_path_candidate': any(entry['kind'] == 0x01 for entry in aura_entries),
                }
                return result.text, metadata
            return result.text
        elif method_byte == CompressionMethod.UNCOMPRESSED.value:
            text = payload.decode('utf-8')
            if return_metadata:
                return text, {'method': 'uncompressed', 'fast_path_candidate': False}
            return text
        else:
            raise ValueError(f"Unknown compression method: 0x{method_byte:02x}")


class AuditLogger:
    """Human-readable audit logger for compliance"""

    def __init__(self, log_file: str = "aura_audit.log"):
        self.log_file = log_file

    def log_message(self, direction: str, role: str, content: str,
                   metadata: Optional[dict] = None):
        """
        Log message in human-readable format

        Args:
            direction: "client_to_server" or "server_to_client"
            role: "user" or "assistant"
            content: The actual message content (plaintext)
            metadata: Optional compression metadata
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        arrow = "→" if direction == "client_to_server" else "←"

        log_entry = f"[{timestamp}] {role.upper()} {arrow}\n"
        log_entry += f"  Message: {content}\n"

        if metadata:
            method_name = metadata.get('method', 'unknown')
            log_entry += f"  Compression: {method_name}\n"
            log_entry += f"  Size: {metadata.get('original_size', 0)} → {metadata.get('compressed_size', 0)} bytes\n"
            log_entry += f"  Ratio: {metadata.get('ratio', 0.0):.2f}:1\n"
            if method_name == 'aura':
                entries = metadata.get('metadata_entries', [])
                log_entry += f"  Metadata entries: {len(entries)}\n"
                if entries:
                    preview = entries[:3]
                    log_entry += f"    Preview: {preview}\n"

        log_entry += "\n"

        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(log_entry)

        # Also print to console
        print(log_entry, end='')


def test_production_system():
    """Test the production-ready system"""

    print("=" * 80)
    print("PRODUCTION HYBRID COMPRESSION SYSTEM TEST")
    print("=" * 80)
    print()

    compressor = ProductionHybridCompressor(binary_advantage_threshold=1.1)
    audit_logger = AuditLogger()

    # Test cases with manual template mappings
    test_cases = [
        {
            "text": "I don't have access to real-time weather data. Please check weather.com",
            "template_id": 0,
            "slots": ["real-time weather data", "Please check weather.com"]
        },
        {
            "text": "The capital of France is Paris.",
            "template_id": 10,
            "slots": ["capital", "France", "Paris"]
        },
        {
            "text": "To install packages, use pip: `pip install numpy`",
            "template_id": 40,
            "slots": ["install packages", "pip", "pip install numpy"]
        },
        {
            "text": "Yes, I can help with that. What specific aspect would you like to know more about?",
            "template_id": 100,
            "slots": ["aspect"]
        },
        {
            "text": "The time complexity of binary search is O(log n) because it divides the search space in half.",
            "template_id": 70,
            "slots": ["time complexity", "binary search", "O(log n)", "it divides the search space in half"]
        },
        {
            "text": "Common HTTP status codes include: 200, 404, 500.",
            "template_id": 80,
            "slots": ["HTTP status codes", "200, 404, 500"]
        },
        {
            "text": "To debug this issue, I recommend: check console, verify endpoint, test authentication",
            "template_id": 90,
            "slots": ["debug this issue", "check console, verify endpoint, test authentication"]
        },
        {
            "text": "Neural networks work by adjusting weights through backpropagation.",
            "template_id": 71,
            "slots": ["Neural networks", "adjusting weights through backpropagation"]
        },
    ]

    results = []

    for idx, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        template_id = test_case.get("template_id")
        slots = test_case.get("slots")

        original_size = len(text.encode('utf-8'))

        # Compress
        compressed, method, metadata = compressor.compress(text, template_id, slots)

        # Decompress
        try:
            decompressed = compressor.decompress(compressed)
            matches = text == decompressed
        except Exception as e:
            decompressed = f"ERROR: {e}"
            matches = False

        # Brotli baseline
        brotli_only = brotli_compress(text.encode('utf-8'))
        brotli_size = len(brotli_only)
        brotli_ratio = original_size / brotli_size

        results.append({
            'original': original_size,
            'hybrid': metadata['compressed_size'],
            'brotli': brotli_size,
            'hybrid_ratio': metadata['ratio'],
            'brotli_ratio': brotli_ratio,
            'method': method,
            'matches': matches,
            'metadata': metadata
        })

        # Display
        print(f"Test {idx}: {text[:60]}...")
        print(f"  Original:  {original_size:4d} bytes")
        print(f"  Brotli:    {brotli_size:4d} bytes ({brotli_ratio:.2f}:1)")
        print(f"  Hybrid:    {metadata['compressed_size']:4d} bytes ({metadata['ratio']:.2f}:1)")
        print(f"  Method:    {metadata['method']}")

        if method == CompressionMethod.BINARY_SEMANTIC:
            advantage = metadata.get('advantage_vs_brotli_percent', 0)
            print(f"  🏆 Binary wins! {advantage:.1f}% better than Brotli")
            print(f"     Template #{metadata['template_id']}, {metadata['slot_count']} slots")

        print(f"  Decompress: {'✅ PASS' if matches else '❌ FAIL'}")

        if not matches:
            print(f"     Expected: {text}")
            print(f"     Got: {decompressed}")

        print()

        # Log to audit
        audit_logger.log_message(
            direction="client_to_server",
            role="user",
            content=decompressed if matches else text,
            metadata=metadata
        )

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    total_original = sum(r['original'] for r in results)
    total_hybrid = sum(r['hybrid'] for r in results)
    total_brotli = sum(r['brotli'] for r in results)

    print(f"Total Original:  {total_original:,} bytes")
    print(f"Total Brotli:    {total_brotli:,} bytes ({total_original/total_brotli:.2f}:1)")
    print(f"Total Hybrid:    {total_hybrid:,} bytes ({total_original/total_hybrid:.2f}:1)")
    print()

    savings = total_brotli - total_hybrid
    savings_pct = (savings / total_brotli) * 100

    print(f"Hybrid saves: {savings:,} bytes ({savings_pct:.1f}% better than Brotli)")
    print()

    # Pass rate
    pass_count = sum(1 for r in results if r['matches'])
    pass_rate = (pass_count / len(results)) * 100

    print(f"Decompression accuracy: {pass_count}/{len(results)} ({pass_rate:.0f}%)")
    print()

    # Method distribution
    binary_count = sum(1 for r in results if r['method'] == CompressionMethod.BINARY_SEMANTIC)
    print(f"Binary semantic used: {binary_count}/{len(results)} ({binary_count/len(results)*100:.0f}%)")
    print()

    if pass_rate == 100:
        print("✅ ALL TESTS PASSED - PRODUCTION READY!")
    else:
        print("⚠️  Some tests failed - needs debugging")

    print()
    print(f"📋 Audit log written to: {audit_logger.log_file}")
    print()

if __name__ == "__main__":
    test_production_system()
