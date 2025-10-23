# AURA Compression - Technical Reference

**Patent Application:** 19/366,538
**Version:** 1.0
**Last Updated:** October 23, 2025

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Modules](#core-modules)
3. [Experimental BRIO Compression](#experimental-brio-compression)
4. [API Reference](#api-reference)
5. [Data Formats](#data-formats)
6. [Performance Characteristics](#performance-characteristics)
7. [Configuration](#configuration)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AURA Compression System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Hybrid          │  │  Template    │  │  Audit        │  │
│  │ Compressor      │──│  Library     │  │  Logger       │  │
│  └─────────────────┘  └──────────────┘  └───────────────┘  │
│          │                                      │            │
│          ├──────────────────────────────────────┘            │
│          │                                                   │
│  ┌───────▼──────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ Metadata         │  │  Router      │  │  Discovery    │ │
│  │ Extractor        │──│  (Fast Path) │  │  Engine       │ │
│  └──────────────────┘  └──────────────┘  └───────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        Experimental BRIO Compression Engine          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │   │
│  │  │ LZ77    │ │ Dict    │ │ rANS    │ │ Template │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Compression Methods

| Method | Format | Best For | Ratio | Speed |
|--------|--------|----------|-------|-------|
| **binary_semantic** | Template ID + slots | Structured messages | 1.2-2.0x | Very Fast |
| **aura (BRIO)** | LZ77 + dict + rANS + templates | All content | 1.5-5.0x | Fast |
| **brotli** | Standard brotli | General text | 1.2-2.5x | Medium |
| **uncompressed** | Raw bytes | Tiny messages | 1.0x | Instant |

### Template ID Allocation (V3)

```
┌─────────────────────────────────────────────────────────┐
│  0-49    │ AI→AI Universal (50 slots)                   │
├──────────┴───────────────────────────────────────────────┤
│  50-108  │ Human→AI Universal (59 slots)                │
├──────────┴───────────────────────────────────────────────┤
│  109-148 │ ML/AI Model Outputs (40 slots)               │
├──────────┴───────────────────────────────────────────────┤
│  149-208 │ Platform Rolling Dynamic (60 slots)          │
├──────────┴───────────────────────────────────────────────┤
│  209-223 │ Reserved Routing (15 slots)                  │
├──────────┴───────────────────────────────────────────────┤
│  224-255 │ User-Specific Per-Session (32 slots)         │
└──────────────────────────────────────────────────────────┘
```

---

## Core Modules

### 1. ProductionHybridCompressor

**File:** `compressor.py` (850 lines)

**Purpose:** Main compression orchestrator with intelligent method selection

#### Initialization

```python
from aura_compression import ProductionHybridCompressor

compressor = ProductionHybridCompressor(
    template_store_path="template_store.json",  # Dynamic templates
    enable_aura=True,                           # Enable BRIO (default: False)
    min_compression_size=50,                    # Min bytes to compress (default: 50)
    enable_audit_logging=True,                  # Enable audit logs
    audit_log_directory="./audit",              # Audit log location
    session_id="session_123",                   # Session identifier
    aura_preference_margin=0.10                 # BRIO preference threshold (10%)
)
```

#### Core Methods

**compress(text: str) → (bytes, CompressionMethod, dict)**

```python
payload, method, metadata = compressor.compress("I cannot process this request.")

# Returns:
# payload: b'\x01\x01\x01\x19process this request'
# method: CompressionMethod.BINARY_SEMANTIC
# metadata: {
#     'method': 'binary_semantic',
#     'template_id': 1,
#     'original_size': 30,
#     'compressed_size': 25,
#     'ratio': 1.20,
#     'slot_count': 1
# }
```

**decompress(payload: bytes) → str**

```python
text = compressor.decompress(payload)
# Returns: "I cannot process this request."
```

**compress_with_template(template_id: int, slots: List[str]) → bytes**

```python
# Direct template compression
payload = compressor.compress_with_template(1, ["process this request"])
# Returns: b'\x01\x01\x19process this request'
```

#### Binary Semantic Format

```
┌──────────────┬───────────────┬────────────────┬─────────────────────┐
│ Template ID  │ Slot Count    │ Slot 0 Length  │ Slot 0 Data         │
│ (1 byte)     │ (1 byte)      │ (2 bytes BE)   │ (variable)          │
└──────────────┴───────────────┴────────────────┴─────────────────────┘
```

#### Compression Selection Logic

```python
def _select_best_method(binary_ratio, brotli_ratio, aura_ratio, aura_enabled):
    if aura_enabled and aura_ratio > max(binary_ratio, brotli_ratio) * (1 + margin):
        return AURA
    elif binary_ratio > brotli_ratio:
        return BINARY_SEMANTIC
    else:
        return BROTLI
```

---

### 2. TemplateLibrary

**File:** `templates.py` (150 lines)

**Purpose:** Template management with regex-based matching

#### Initialization

```python
from aura_compression import TemplateLibrary

# Default templates only
lib = TemplateLibrary()

# With custom templates
lib = TemplateLibrary(custom_templates={
    200: "Your balance is {0}.",
    201: "Transaction {0} succeeded."
})

# With user-specific templates
lib = TemplateLibrary(user_id="user_123")  # Loads user-specific templates 224-255
```

#### Core Methods

**match(text: str) → Optional[TemplateMatch]**

```python
match = lib.match("I cannot process this request.")
# Returns: TemplateMatch(template_id=1, slots=['process this request'])

if match:
    print(f"Template {match.template_id} with slots: {match.slots}")
```

**format_template(template_id: int, slots: List[str]) → str**

```python
text = lib.format_template(1, ["access your account"])
# Returns: "I cannot access your account."
```

**add(template_id: int, pattern: str)**

```python
lib.add(200, "Your balance is {0}.")
```

#### Template Pattern Format

```python
# Single slot
"I cannot {0}."

# Multiple slots
"The {0} of {1} is {2}."

# Example with extraction
text = "The price of Product A is $99.99."
match = lib.match(text)
# Returns: TemplateMatch(
#     template_id=10,
#     slots=['price', 'Product A', '$99.99']
# )
```

#### Default Templates

**AI→AI (0-49):**
- 0: "I don't have access to {0}. {1}"
- 1: "I cannot {0}."
- 2: "I'm unable to {0}."
- 5: "The {0} is {1}."
- 10: "The {0} of {1} is {2}."
- ...

**Human→AI (50-108):**
- 50: "I forgot my password for {0}"
- 55: "Where is my order {0}?"
- 59: "I have a question about invoice {0}"
- ...

**ML→AI (109-148):**
- 109: '{"model": "{0}", "prediction": {1}, "confidence": {2}}'
- 111: '{"class": "{0}", "probability": {1}, "top_k": [{2}]}'
- 119: '{"embeddings": [{0}], "dimensions": {1}}'
- ...

---

### 3. AuditLogger

**File:** `audit.py` (400 lines)

**Purpose:** Compliance-grade append-only audit logging with cryptographic integrity

#### Initialization

```python
from aura_compression import AuditLogger, AuditLogType

logger = AuditLogger(
    log_directory="./audit",
    session_id="session_123",
    user_id="user_456"  # Optional for user-specific logs
)
```

#### Core Methods

**log_compression(text: str, payload: bytes, metadata: dict)**

```python
logger.log_compression(
    text="I cannot process this request.",
    payload=b'\x01\x01\x19process this request',
    metadata={
        'method': 'binary_semantic',
        'template_id': 1,
        'ratio': 1.20
    }
)
```

**log_ai_output(pre_text: str, post_text: str, safety_score: float, moderation_flags: dict)**

```python
logger.log_ai_output(
    pre_text="<potentially harmful content>",
    post_text="<sanitized content>",
    safety_score=0.85,
    moderation_flags={'violence': False, 'profanity': False}
)
```

**log_safety_alert(text: str, harm_type: str, severity: str, action: str)**

```python
logger.log_safety_alert(
    text="<blocked harmful content>",
    harm_type="hate_speech",
    severity="high",
    action="blocked"
)
```

**verify_integrity() → bool**

```python
# Verify cryptographic chain integrity
is_valid = logger.verify_integrity()
print(f"Audit log integrity: {'VALID' if is_valid else 'COMPROMISED'}")
```

#### Log File Structure

```
audit/
├── client_delivered/
│   └── session_123_YYYYMMDD_HHMMSS.jsonl
├── ai_generated/
│   └── session_123_YYYYMMDD_HHMMSS.jsonl
├── metadata_only/
│   └── session_123_YYYYMMDD_HHMMSS.jsonl
└── safety_alerts/
    └── session_123_YYYYMMDD_HHMMSS.jsonl
```

#### Log Entry Format

```json
{
  "timestamp": "2025-10-23T12:34:56.789Z",
  "session_id": "session_123",
  "user_id": "user_456",
  "message_id": "msg_789",
  "plaintext": "I cannot process this request.",
  "compressed_payload": "base64_encoded_bytes",
  "compression_method": "binary_semantic",
  "original_size": 30,
  "compressed_size": 25,
  "ratio": 1.20,
  "template_id": 1,
  "integrity_hash": "sha256_hash_of_previous_entry"
}
```

---

### 4. MetadataExtractor

**File:** `metadata.py` (250 lines)

**Purpose:** Extract metadata without decompression (76-200x speedup)

#### Core Method

**extract(payload: bytes) → ExtractedMetadata**

```python
from aura_compression import MetadataExtractor

metadata = MetadataExtractor.extract(payload)

print(f"Method: {metadata.method}")
print(f"Template IDs: {metadata.template_ids}")
print(f"Fast path candidate: {metadata.fast_path_candidate}")
print(f"Extraction time: {metadata.extraction_time_ms}ms")
```

#### ExtractedMetadata Structure

```python
@dataclass
class ExtractedMetadata:
    method: str                      # Compression method
    original_size: int               # Original bytes
    compressed_size: int             # Compressed bytes
    ratio: float                     # Compression ratio
    template_ids: List[int]          # All template IDs used
    metadata_entries: List[dict]     # Raw metadata entries
    fast_path_candidate: bool        # Can use fast-path routing?
    extraction_time_ms: float        # Extraction latency
```

#### Performance

| Operation | Time | Speedup |
|-----------|------|---------|
| **Metadata extraction** | 0.17 ms | - |
| **Full decompression** | 13 ms | 76x slower |

---

### 5. TemplateDiscoveryEngine

**File:** `discovery.py` (470 lines)

**Purpose:** Automatic template discovery from audit logs

#### Initialization

```python
from aura_compression import TemplateDiscoveryEngine

engine = TemplateDiscoveryEngine(
    min_frequency=10,           # Minimum pattern occurrences
    min_compression_advantage=2.0,  # Minimum 2x compression ratio
    starting_template_id=149,   # Start of dynamic range
    ending_template_id=208      # End of dynamic range
)
```

#### Discovery Pipeline

```python
# 1. Load messages from audit logs
messages = ["I cannot process this.", "I cannot verify that.", ...]

# 2. Run discovery
candidates = engine.discover_templates(messages)

# 3. Review and promote
for candidate in candidates:
    if candidate.compression_advantage > 2.5:
        template_id = engine.promote_template(candidate)
        print(f"Promoted: {template_id} -> {candidate.pattern}")

# 4. Export for client sync
store = engine.get_template_store()
# Returns: {149: "pattern1", 150: "pattern2", ...}
```

#### TemplateCandidate Structure

```python
@dataclass
class TemplateCandidate:
    pattern: str                     # Template pattern
    example_messages: List[str]      # Example matches
    frequency: int                   # Usage count
    avg_original_size: float         # Average original bytes
    avg_compressed_size: float       # Average compressed bytes
    compression_advantage: float     # Compression ratio
    usage_count: int                 # Total uses
    last_used: float                 # Timestamp
    safety_approved: bool            # Passed safety screening
```

#### Safety Screening

```python
HARMFUL_KEYWORDS = [
    "password", "secret", "credit_card", "ssn",
    "hack", "exploit", "vulnerability",
    "hate", "violence", "illegal"
]
```

---

### 6. ProductionRouter

**File:** `router.py` (305 lines)

**Purpose:** Metadata-based fast-path routing (60%+ messages)

#### Initialization

```python
from aura_compression import ProductionRouter, LoadBalancer

router = ProductionRouter()

# Register handlers
router.register_route(
    template_ids=[1, 2, 5],
    function_ids=["execute_task"],
    handler=lambda msg: handle_fast(msg),
    cache_ttl=300  # 5 minute cache
)
```

#### Core Method

**route(payload: bytes) → RouteDecision**

```python
decision, handler, metrics = router.route(payload)

if decision == RouteDecision.FAST_PATH:
    result = handler(payload)  # No decompression!
elif decision == RouteDecision.SLOW_PATH:
    text = decompress(payload)
    result = handler(text)
elif decision == RouteDecision.CACHED:
    result = get_cached_response(payload)

print(f"Fast-path usage: {metrics.fast_path_percentage:.1f}%")
```

#### RoutingMetrics

```python
@dataclass
class RoutingMetrics:
    total_messages: int
    fast_path_count: int
    slow_path_count: int
    cached_count: int
    fast_path_percentage: float      # Target: 60%+
    avg_fast_path_latency_ms: float  # Target: <1ms
    avg_slow_path_latency_ms: float
    speedup_factor: float            # Fast vs slow ratio
```

---

### 7. ConversationAccelerator

**File:** `acceleration.py` (200+ lines)

**Purpose:** Progressive conversation speedup (13ms → 0.15ms after 50 messages)

#### Initialization

```python
from aura_compression import ConversationAccelerator

accelerator = ConversationAccelerator(
    session_id="session_123",
    cache_size=1000,             # LRU cache size
    temporal_decay=0.95          # Decay factor per hour
)
```

#### Usage

```python
# First message: 13ms (full pipeline)
metadata1 = accelerator.process_message(payload1)

# Similar messages: progressively faster
for payload in messages:
    metadata = accelerator.process_message(payload)
    # Eventually reaches ~0.15ms (87x speedup)
```

#### Acceleration Curve

```
Latency (ms)
  │
13│●
  │
  │  ●
  │    ●
 5│      ●●
  │        ●●●
  │           ●●●●
  │              ●●●●●●●
0.15│___________________●●●●●●●
  └─────────────────────────────► Messages
    0  10  20  30  40  50  60  70
```

---

## Experimental BRIO Compression

### Architecture

```
Input Text
   │
   ▼
┌──────────────────────────────┐
│   Template Matching          │
│   (if template_match != None)│
└─────────────┬────────────────┘
              │
              ▼
┌──────────────────────────────┐
│   Tokenization               │
│   ├─ Literals                │
│   ├─ Dictionary phrases      │
│   ├─ LZ77 matches            │
│   └─ Template tokens         │
└─────────────┬────────────────┘
              │
              ▼
┌──────────────────────────────┐
│   Frequency Analysis         │
│   (build symbol frequencies) │
└─────────────┬────────────────┘
              │
              ▼
┌──────────────────────────────┐
│   rANS Entropy Coding        │
│   (near-optimal compression) │
└─────────────┬────────────────┘
              │
              ▼
┌──────────────────────────────┐
│   Header Construction        │
│   ├─ Magic: "AURA"           │
│   ├─ Version: 1              │
│   ├─ Lengths                 │
│   ├─ Frequency table         │
│   └─ Metadata entries        │
└─────────────┬────────────────┘
              │
              ▼
    Compressed Payload
```

### BrioEncoder

**File:** `experimental/brio/encoder.py` (100+ lines)

#### Usage

```python
from aura_compression.experimental.brio import BrioEncoder
from aura_compression import TemplateLibrary, TemplateMatch

encoder = BrioEncoder(template_library=TemplateLibrary())

# With template
match = TemplateMatch(template_id=1, slots=["process this"])
result = encoder.compress("I cannot process this.", template_match=match)

# Without template
result = encoder.compress("Some random text here.")

print(f"Compressed: {len(result.payload)} bytes")
print(f"Tokens: {len(result.tokens)}")
print(f"Metadata entries: {len(result.metadata)}")
```

#### BRIO Payload Format

```
┌────────────────────────────────────────────────────────────┐
│ Header                                                      │
├────────────────────────────────────────────────────────────┤
│ Magic:        "AURA" (4 bytes)                             │
│ Version:      1 (1 byte)                                   │
│ Plain length: 4 bytes (big-endian)                         │
│ rANS length:  4 bytes (big-endian)                         │
│ Metadata cnt: 2 bytes (big-endian)                         │
├────────────────────────────────────────────────────────────┤
│ Frequency Table (512 bytes)                                │
│   256 symbols × 2 bytes each                               │
├────────────────────────────────────────────────────────────┤
│ Metadata Entries (6 bytes each)                            │
│   token_index: 2 bytes                                     │
│   kind:        1 byte                                      │
│   value:       2 bytes                                     │
│   flags:       1 byte                                      │
├────────────────────────────────────────────────────────────┤
│ rANS Payload (variable)                                    │
└────────────────────────────────────────────────────────────┘
```

### Token Types

```python
# Literal: single byte
buf.append(0x00)
buf.append(byte_value)

# Dictionary: phrase reference
buf.append(0x01)
buf.append(entry_id)

# LZ77 Match: backreference
buf.append(0x02)
buf.extend(distance.to_bytes(2, 'big'))
buf.append(length)

# Template: template with slots
buf.append(0x03)
buf.append(template_id)
buf.append(slot_count)
for slot in slots:
    buf.extend(len(slot).to_bytes(2, 'big'))
    buf.extend(slot.encode('utf-8'))
```

### rANS Parameters

```python
ANS_SCALE_BITS = 12
ANS_SCALE = 4096  # (1 << 12)
LOWER_BOUND = (ANS_SCALE << 8)  # Renormalization threshold
```

---

## Data Formats

### 1. Template Store JSON

**File:** `template_store.json`

```json
{
  "version": "1.0",
  "platform_templates": {
    "149": {
      "pattern": "Your balance is {0}.",
      "frequency": 42,
      "avg_compression": 2.5,
      "discovered_by": "user_123",
      "created_at": "2025-10-23T12:00:00Z"
    },
    "150": {
      "pattern": "Transaction {0} completed successfully.",
      "frequency": 38,
      "avg_compression": 2.8,
      "discovered_by": "discovery_engine",
      "created_at": "2025-10-23T13:00:00Z"
    }
  },
  "user_templates": {
    "user_123": {
      "224": {
        "pattern": "My custom pattern {0}",
        "frequency": 5,
        "avg_compression": 1.8
      }
    }
  }
}
```

### 2. Audit Log Entry

**File:** `audit/client_delivered/session_*.jsonl`

```json
{
  "timestamp": "2025-10-23T12:34:56.789123Z",
  "session_id": "session_abc123",
  "user_id": "user_456",
  "message_id": "msg_xyz789",
  "plaintext": "I cannot process this request.",
  "compressed_payload": "AQEZcHJvY2VzcyB0aGlzIHJlcXVlc3Q=",
  "compression_method": "binary_semantic",
  "original_size": 30,
  "compressed_size": 25,
  "ratio": 1.2,
  "template_id": 1,
  "slot_count": 1,
  "integrity_hash": "d2a84f4b8b650937ec8f73cd8be2c74add5a911ba64df27458ed8229da804a26"
}
```

---

## Performance Characteristics

### Compression Ratios by Content Type

| Content Type | Template Hit Rate | Compression Ratio | Effective Ratio* |
|--------------|-------------------|-------------------|------------------|
| **ML/AI JSON** | 100% | 1.9x | **6.8x** |
| **API responses** | 80-100% | 1.5-2.5x | **3.5-5.5x** |
| **User forms** | 92% | 1.9x | **3.3x** |
| **AI responses** | 55% | 1.3x | **3.1x** |
| **Natural conversation** | 2-5% | 1.2x | **1.4x** |

*Effective ratio includes metadata elimination

### Latency Benchmarks

| Operation | Time | Throughput |
|-----------|------|------------|
| **Server encode** | 0.56 ms | 1,785 ops/sec |
| **Client decode** | 0.01 ms | 100,000 ops/sec |
| **Per-token latency** | 61 μs | 16,393 tokens/sec |
| **Metadata extraction** | 0.17 ms | 5,882 ops/sec |
| **Full decompression** | 13 ms | 76 ops/sec |

### Throughput at Scale

| Messages/Day | Cores Required | Bandwidth Saved |
|--------------|----------------|-----------------|
| 1M | 0.02 | 7.4 MB/day |
| 10M | 0.2 | 74 MB/day |
| 100M | 2 | 740 MB/day |
| 1B | 20 | 7.4 GB/day |

---

## Configuration

### Environment Variables

```bash
# Enable experimental BRIO compression
export AURA_ENABLE_EXPERIMENTAL=true

# Template store location
export AURA_TEMPLATE_STORE=/path/to/template_store.json

# Audit log directory
export AURA_AUDIT_LOG_DIR=/var/log/aura

# Minimum compression threshold
export AURA_MIN_COMPRESSION_SIZE=50

# Discovery interval (seconds)
export AURA_DISCOVERY_INTERVAL=3600
```

### Production Configuration

```python
# production_config.py

COMPRESSION_CONFIG = {
    'enable_aura': True,
    'min_compression_size': 10,
    'aura_preference_margin': 0.10,
    'template_store_path': '/var/lib/aura/templates.json',
    'enable_audit_logging': True,
    'audit_log_directory': '/var/log/aura',
}

DISCOVERY_CONFIG = {
    'enabled': True,
    'interval_seconds': 3600,
    'min_frequency': 10,
    'min_compression_advantage': 2.0,
    'starting_template_id': 149,
    'ending_template_id': 208,
}

ROUTER_CONFIG = {
    'enable_fast_path': True,
    'target_fast_path_percentage': 60.0,
    'cache_ttl_seconds': 300,
}
```

---

## Patent Claims Implementation

| Claim | Module | Status |
|-------|--------|--------|
| 1-10: Core Compression | compressor.py, experimental/brio/ | ✅ Complete |
| 11-14: Metadata & Audit | audit.py, metadata.py | ✅ Complete |
| 15-18: Template Discovery | discovery.py, background_workers.py | ✅ Complete |
| 19-20: Function Routing | function_parser.py, router.py | ✅ Complete |
| 21-30: Fast-Path Routing | metadata.py, router.py | ✅ Complete |
| 31-31E: Acceleration | acceleration.py | ✅ Complete |
| 32-35: Compliance | audit.py | ✅ Complete |

---

**Document Version:** 1.0
**Patent Application:** 19/366,538
**Last Updated:** October 23, 2025
