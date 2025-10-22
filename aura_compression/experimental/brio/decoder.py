"""Decoder counterpart for the Brio prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .constants import MAGIC, VERSION, WINDOW_SIZE
from .tokens import (
    DictionaryToken,
    LiteralToken,
    MatchToken,
    MetadataEntry,
    Token,
)
from . import dictionary


@dataclass
class BrioDecompressed:
    text: str
    tokens: List[Token]
    metadata: List[MetadataEntry]


@dataclass
class BrioDecoder:
    def decompress(self, payload: bytes) -> BrioDecompressed:
        view = memoryview(payload)
        if view[:4].tobytes() != MAGIC:
            raise ValueError("Invalid Brio payload: missing magic")
        if view[4] != VERSION:
            raise ValueError("Unsupported Brio payload version")

        payload_len = int.from_bytes(view[5:9], "big")
        metadata_count = int.from_bytes(view[9:11], "big")

        metadata_start = 11
        metadata_end = metadata_start + metadata_count * 5
        payload_start = metadata_end
        payload_end = payload_start + payload_len

        metadata: List[MetadataEntry] = []
        meta_bytes = view[metadata_start:metadata_end].tobytes()
        for i in range(0, len(meta_bytes), 5):
            token_index = int.from_bytes(meta_bytes[i : i + 2], "big")
            kind = meta_bytes[i + 2]
            value = int.from_bytes(meta_bytes[i + 3 : i + 5], "big")
            metadata.append(MetadataEntry(token_index, kind, value))

        payload_slice = view[payload_start:payload_end].tobytes()
        payload_bytes = list(payload_slice)
        tokens = self._deserialise_tokens(payload_bytes)
        text = self._reconstruct(tokens).decode("utf-8")
        return BrioDecompressed(text=text, tokens=tokens, metadata=metadata)

    # -- helper utilities -----------------------------------------

    def _deserialise_tokens(self, payload: List[int]) -> List[Token]:
        tokens: List[Token] = []
        i = 0
        size = len(payload)
        while i < size:
            tag = payload[i]
            i += 1
            if tag == 0x00:
                tokens.append(LiteralToken(payload[i]))
                i += 1
            elif tag == 0x01:
                tokens.append(DictionaryToken(payload[i]))
                i += 1
            elif tag == 0x02:
                distance = (payload[i] << 8) | payload[i + 1]
                length = payload[i + 2]
                tokens.append(MatchToken(distance, length))
                i += 3
            else:
                raise ValueError(f"Unknown token tag: {tag:#x}")
        return tokens

    def _reconstruct(self, tokens: List[Token]) -> bytearray:
        window = bytearray()
        output = bytearray()

        for token in tokens:
            if isinstance(token, LiteralToken):
                output.append(token.value)
                window.append(token.value)
            elif isinstance(token, DictionaryToken):
                entry = dictionary.by_id(token.entry_id)
                output.extend(entry.phrase_bytes)
                window.extend(entry.phrase_bytes)
            elif isinstance(token, MatchToken):
                start = len(window) - token.distance
                if start < 0:
                    raise ValueError("Invalid match token distance")
                match_bytes = [window[start + i] for i in range(token.length)]
                output.extend(match_bytes)
                window.extend(match_bytes)
            else:  # pragma: no cover
                raise ValueError(f"Unexpected token type: {token!r}")

            if len(window) > WINDOW_SIZE:
                del window[:-WINDOW_SIZE]

        return output


__all__ = ["BrioDecoder", "BrioDecompressed"]
