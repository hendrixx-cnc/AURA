"""Token definitions for the Brio prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass
class LiteralToken:
    value: int  # single byte


@dataclass
class DictionaryToken:
    entry_id: int


@dataclass
class MatchToken:
    distance: int
    length: int


Token = Union[LiteralToken, DictionaryToken, MatchToken]


@dataclass
class MetadataEntry:
    token_index: int
    kind: int
    value: int


__all__ = [
    "LiteralToken",
    "DictionaryToken",
    "MatchToken",
    "Token",
    "MetadataEntry",
]
