"""
AURA Compression - AI-Optimized Hybrid Compression Protocol

Copyright (c) 2025 Todd Hendricks
Licensed under Apache License 2.0
"""

__version__ = "1.0.0"
__author__ = "Todd Hendricks"
__license__ = "Apache 2.0"

from .compressor import ProductionHybridCompressor, AuditLogger, CompressionMethod
from .templates import TemplateLibrary

__all__ = [
    "ProductionHybridCompressor",
    "AuditLogger",
    "CompressionMethod",
    "TemplateLibrary",
]
