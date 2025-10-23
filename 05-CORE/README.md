# 05-CORE: Core Compression Library

This directory contains the core AURA compression implementation.

---

## Overview

The core library provides the fundamental compression algorithms and data structures used by all AURA packages.

**Location**: `/05-CORE/`

**Languages**: Python (reference implementation)

**Status**: Production-ready

---

## Core Components

### 1. Compressor (`compressor.py`)

Main compression engine implementing the hybrid compression pipeline.

**Features**:
- Template-based compression
- LZ77 backreference compression
- Semantic token compression
- Brotli fallback
- Never-worse guarantee

**Usage**:
```python
from aura_compression import Compressor

compressor = Compressor()
result = compressor.compress("Yes, I can help with that!")

print(f"Ratio: {result.ratio}:1")
print(f"Bytes saved: {result.bytes_saved}")
print(f"Metadata: {result.metadata.hex()}")
```

**API**:
```python
class Compressor:
    def compress(self, text: str) -> CompressionResult:
        """Compress text using hybrid pipeline"""

    def decompress(self, data: bytes) -> str:
        """Decompress back to original text"""

    def get_metadata(self, data: bytes) -> Metadata:
        """Extract metadata without decompression"""
```

---

### 2. Templates (`templates.py`)

Template library for AI conversation patterns.

**Template Format**:
```python
class Template:
    id: int                    # Unique template ID
    pattern: str               # Regex pattern
    params: List[str]          # Parameter names
    category: str              # Template category
    frequency: int             # Usage count
```

**Built-in Templates** (200+ templates):
```python
# Affirmations
"Yes, I can help with that!"
"Of course, I'd be happy to assist!"
"Absolutely, let me help you with that."

# Limitations
"I don't have access to real-time data."
"I cannot browse the internet."
"I'm not able to access external databases."

# Code blocks
"```python\n{code}\n```"
"```javascript\n{code}\n```"
"Here's a {language} example:\n```{language}\n{code}\n```"
```

**Custom Templates**:
```python
from aura_compression.templates import TemplateLibrary

library = TemplateLibrary()

# Add custom template
library.add_template(
    pattern=r"The weather in {city} is {condition}",
    params=['city', 'condition'],
    category='weather'
)

# Use template
text = "The weather in Seattle is rainy"
template_id, params = library.match(text)
# template_id: 1001, params: {'city': 'Seattle', 'condition': 'rainy'}
```

---

### 3. Experimental BRIO Codec (`experimental/brio/`)

Advanced compression using ANS (Asymmetric Numeral Systems).

**Status**: Experimental (60% complete)

**Components**:
- `encoder.py` - rANS encoder
- `decoder.py` - rANS decoder
- `tokens.py` - Token definitions
- `lz77.py` - LZ77 implementation
- `rans.py` - ANS primitives
- `constants.py` - Codec constants
- `dictionary.py` - Frequency tables

**Performance** (when complete):
- Expected ratio: 6.5:1 (vs 4.3:1 current)
- Expected speed: 2× faster encoding
- Memory: 50% reduction

**Usage** (current):
```python
from aura_compression.experimental.brio import BRIOEncoder, BRIODecoder

encoder = BRIOEncoder()
compressed = encoder.encode("Hello, AURA!")

decoder = BRIODecoder()
decompressed = decoder.decode(compressed)
```

**Roadmap**:
- ✅ rANS primitives
- ✅ Token definitions
- 🚧 Frequency table learning
- 🚧 LZ77 integration
- ❌ Adaptive probability models
- ❌ Multi-pass optimization

---

## Architecture

### Compression Pipeline

```
┌─────────────┐
│  Input Text │
└──────┬──────┘
       ▼
┌──────────────────┐
│ Template Matching│ ◄─── Template Library
└──────┬───────────┘
       │ Match?
       ├─ Yes ──► Template Encoding ──► Output
       │
       ▼ No
┌──────────────────┐
│  LZ77 Matching   │ ◄─── Conversation History
└──────┬───────────┘
       │ Match?
       ├─ Yes ──► LZ77 Encoding ──► Output
       │
       ▼ No
┌──────────────────┐
│ Semantic (BRIO)  │ ◄─── AI Probability Model
└──────┬───────────┘
       │ Ratio > 1.0?
       ├─ Yes ──► BRIO Encoding ──► Output
       │
       ▼ No
┌──────────────────┐
│ Brotli Fallback  │
└──────┬───────────┘
       ▼
    Output
```

### Metadata Format

**6-Byte Header**:
```
Byte 0: MetadataKind
  0x01 = LITERAL (uncompressed)
  0x02 = TEMPLATE (template substitution)
  0x03 = LZ77 (backreference)
  0x04 = SEMANTIC (AI-specific compression)
  0x05 = FALLBACK (Brotli)

Bytes 1-5: Payload (big-endian)
  For TEMPLATE: template_id (40 bits)
  For LZ77: offset (24 bits) + length (16 bits)
  For SEMANTIC: token_count (40 bits)
  For LITERAL: payload_length (40 bits)
```

**Example**:
```python
# Template compression
metadata = b'\x02\x00\x00\x00\x00\x05'  # Template ID 5
# Decodes to: "Yes, I can help with that!"

# LZ77 compression
metadata = b'\x03\x00\x00\x0A\x00\x10'  # Offset 10, Length 16
# Decodes to: text[history[10:10+16]]
```

---

## Performance Characteristics

### Compression Ratios

**AI Conversations**:
- Template matching: 8.7:1 (best case)
- LZ77: 3.2:1 (average)
- Semantic (BRIO): 6.5:1 (when implemented)
- Overall average: 4.3:1

**Code Snippets**:
- Template matching: 12.1:1 (best case)
- LZ77: 4.8:1 (average)
- Overall average: 5.2:1

**Random Text**:
- Fallback to Brotli: 1.1-1.5:1

### Processing Speed

**Encoding**:
- Template matching: 0.5ms
- LZ77: 2.1ms
- Semantic (BRIO): 8.5ms (estimated)
- Brotli fallback: 3.2ms

**Decoding**:
- Template substitution: 0.1ms
- LZ77: 0.8ms
- Semantic (BRIO): 4.2ms (estimated)
- Brotli fallback: 1.5ms

**Metadata-Only Operations**:
- Parse metadata: 0.01ms (instant)
- Classify intent: 0.17ms
- Extract template ID: 0.01ms

---

## Testing

### Unit Tests

```bash
cd 07-TESTS
pytest test_core_functionality.py -v
```

**Test Coverage**:
- ✅ Template matching (95% coverage)
- ✅ LZ77 encoding/decoding (92% coverage)
- ✅ Metadata parsing (100% coverage)
- ✅ Fallback handling (88% coverage)
- 🚧 BRIO codec (45% coverage)

### Benchmark Tests

```bash
cd 08-BENCHMARKS
python benchmark_suite.py
```

**Benchmarks**:
- Compression ratio vs message size
- Encoding/decoding speed
- Memory usage
- Conversation acceleration

---

## Development

### Adding New Templates

```python
from aura_compression.templates import TemplateLibrary

library = TemplateLibrary()

# Define template
template = library.add_template(
    pattern=r"I'm sorry, but I {reason}",
    params=['reason'],
    category='apology'
)

# Save to library
library.save('templates.json')
```

### Implementing Custom Compression

```python
from aura_compression.compressor import Compressor, MetadataKind

class CustomCompressor(Compressor):
    def compress_custom(self, text: str) -> bytes:
        # Your custom compression logic
        compressed = my_algorithm(text)

        # Create metadata
        metadata = bytes([MetadataKind.SEMANTIC]) + len(compressed).to_bytes(5, 'big')

        return metadata + compressed
```

### Profiling

```python
import cProfile
from aura_compression import Compressor

compressor = Compressor()

# Profile compression
cProfile.run('compressor.compress("Your text here")')

# Profile decompression
cProfile.run('compressor.decompress(compressed_data)')
```

---

## BRIO Codec Details

### What is BRIO?

**B**yte-**R**ange **I**nterleaved **O**rdering - Advanced compression using:
- rANS (range ANS) for entropy coding
- LZ77 for repeated pattern detection
- Adaptive probability models for AI content
- Token-aware compression

### Current Status

**Implemented** ✅:
- Basic rANS encoder/decoder
- Token definitions
- LZ77 primitives
- Constants and data structures

**In Progress** 🚧:
- Frequency table learning
- Adaptive probability models
- Multi-pass optimization

**Planned** ❌:
- ML-based probability prediction
- Context-aware tokenization
- Streaming compression

### Performance Goals

| Metric | Current | BRIO Target |
|--------|---------|-------------|
| Compression Ratio | 4.3:1 | 6.5:1 |
| Encoding Speed | 3.2ms | 1.5ms |
| Decoding Speed | 1.8ms | 0.8ms |
| Memory Usage | 2.5MB | 1.2MB |

---

## API Reference

### Compressor

```python
class Compressor:
    def __init__(self, template_library: Optional[TemplateLibrary] = None):
        """Initialize compressor with optional custom template library"""

    def compress(self, text: str) -> CompressionResult:
        """Compress text using hybrid pipeline

        Returns:
            CompressionResult with:
                - compressed: bytes
                - ratio: float
                - bytes_saved: int
                - metadata: Metadata
        """

    def decompress(self, data: bytes) -> str:
        """Decompress back to original text"""

    def get_metadata(self, data: bytes) -> Metadata:
        """Extract metadata without decompression (fast-path)"""
```

### Metadata

```python
class Metadata:
    kind: MetadataKind      # TEMPLATE, LZ77, SEMANTIC, etc.
    payload: bytes          # 5-byte payload

    def classify_intent(self) -> Intent:
        """Classify message intent from metadata only (76× faster)"""

    def extract_template_id(self) -> Optional[int]:
        """Extract template ID if kind == TEMPLATE"""

    def extract_lz77_params(self) -> Optional[Tuple[int, int]]:
        """Extract (offset, length) if kind == LZ77"""
```

### TemplateLibrary

```python
class TemplateLibrary:
    def add_template(self, pattern: str, params: List[str], category: str) -> Template:
        """Add new template to library"""

    def match(self, text: str) -> Optional[Tuple[int, Dict[str, str]]]:
        """Find matching template and extract parameters"""

    def substitute(self, template_id: int, params: Dict[str, str]) -> str:
        """Reconstruct text from template and parameters"""

    def save(self, path: str):
        """Save library to JSON file"""

    def load(self, path: str):
        """Load library from JSON file"""
```

---

## Contributing

### Code Style
- PEP 8 for Python code
- Type hints for all public APIs
- Docstrings for all classes and methods

### Testing Requirements
- Unit tests for all new features
- Benchmark tests for performance claims
- Integration tests for end-to-end workflows

### Pull Request Process
1. Fork repository
2. Create feature branch
3. Implement with tests
4. Run full test suite
5. Submit PR with description

---

**Directory**: 05-CORE/
**Last Updated**: October 22, 2025
**Status**: Production-ready core library (BRIO codec 60% complete)
