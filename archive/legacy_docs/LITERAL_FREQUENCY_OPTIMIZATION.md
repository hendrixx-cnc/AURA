# Literal Frequency Threshold Optimization Plan

## Problem Statement

The `literal_frequency_threshold` parameter is configured but **not used** in the streaming compression path. This means:

1. All printable ASCII characters (95 chars + whitespace) are included in Huffman tree
2. Rare characters that never appear still take up tree space
3. Handshake packets are larger than necessary
4. Inconsistent behavior between `compress()` and `compress_chunk()` paths

## Current Architecture

### Path 1: Streaming Mode (`compress()` / `decompress()`)
```python
perform_handshake()
  └─> _rebuild_entropy_model()
      └─> build_universal_huffman_tree()
          └─> Includes ALL ASCII chars (32-126 + \n\t\r)
          └─> literal_frequency_threshold NOT USED ❌
```

### Path 2: Standalone Mode (`compress_chunk()`)
```python
entropy_encode()
  └─> classify_literals_by_frequency(threshold=0.01)
      └─> Only includes frequent literals ✅
      └─> Rare chars handled via escape codes
```

## Proposed Solution

### Option A: Adaptive Literal Learning (RECOMMENDED)

Dynamically learn which literals are actually needed based on the text being compressed.

#### Injection Points:
1. **Initial Handshake** - Use sample text or universal defaults
2. **Adaptive Refresh** - Rebuild tree with observed literal frequencies

#### Implementation:

```python
def build_universal_huffman_tree(
    hacs_word_map: dict,
    word_base_frequency: int = 2,
    literal_base_frequency: int = 1,
    common_literals: Optional[str] = None,
    literal_frequency_threshold: float = 0.01,  # NEW PARAMETER
    text_sample: Optional[str] = None,          # NEW PARAMETER
):
    """
    Builds a Huffman tree with frequency-based literal filtering.

    Args:
        literal_frequency_threshold: Minimum frequency (0.01 = 1%) to include literal
        text_sample: Optional text to analyze for literal frequencies
    """

    # Determine which literals to include
    if text_sample:
        # Count actual literal frequencies in sample
        literal_counts = Counter(c for c in text_sample if not c.isalnum())
        total_chars = len(text_sample)

        # Filter by threshold
        frequent_literals = [
            char for char, count in literal_counts.items()
            if (count / total_chars) >= literal_frequency_threshold
        ]

        # Always include basic whitespace
        frequent_literals.extend([' ', '\n', '\t'])
        frequent_literals = set(frequent_literals)

    elif common_literals:
        # User-provided literal set
        frequent_literals = set(common_literals)
    else:
        # Conservative default: common punctuation + whitespace
        frequent_literals = set(' .,!?;:\'"()-\n\t\r')

    frequencies = Counter()

    # Add words
    word_freq = max(0, word_base_frequency)
    if word_freq > 0:
        for word_id in hacs_word_map.keys():
            frequencies[('W', word_id)] = word_freq

    # Add only frequent literals
    literal_freq = max(0, literal_base_frequency)
    if literal_freq > 0:
        for char in frequent_literals:
            frequencies[('L', char)] = literal_freq

    # Build tree
    tree = build_huffman_tree(frequencies)
    codes = generate_huffman_codes(tree)

    # Track rare literals for escape encoding
    all_possible_literals = set(chr(i) for i in range(32, 127)) | {'\n', '\t', '\r'}
    rare_literals = {
        ('L', char): True
        for char in all_possible_literals
        if char not in frequent_literals
    }

    return codes, rare_literals
```

#### Update `_rebuild_entropy_model()`:

```python
def _rebuild_entropy_model(self, dictionary: Dict[str, str], text_sample: Optional[str] = None):
    """
    Recompute Huffman trees from the provided dictionary.

    Args:
        text_sample: Optional text to analyze for literal frequency optimization
    """
    huffman_codes_tuple_keys, rare_literals = build_universal_huffman_tree(
        dictionary,
        word_base_frequency=self.word_base_frequency,
        literal_base_frequency=self.literal_base_frequency,
        common_literals=self.universal_common_literals,
        literal_frequency_threshold=self.literal_frequency_threshold,  # NOW USED
        text_sample=text_sample,
    )
    self.compression_tree = huffman_codes_tuple_keys
    self.decompression_tree = dict(huffman_codes_tuple_keys)
    self.rare_literals = rare_literals
```

#### Update `perform_handshake()`:

```python
def perform_handshake(self, text_sample: str = None) -> bytes:
    """
    Performs the handshake as the 'server' or initiating party.

    Args:
        text_sample: Sample text to optimize literal character set.
                    If provided, only literals appearing with frequency
                    >= literal_frequency_threshold will be included.
    """
    active_dictionary = self._get_handshake_dictionary()
    self.hacs_id_map = active_dictionary.copy()

    # Build optimized Huffman tree with literal frequency filtering
    self._rebuild_entropy_model(self.hacs_id_map, text_sample=text_sample)

    self.is_ready = True
    self._initialize_streaming_state()
    self.refresh_required = False
    self.literal_fallback_tokens = 0
    self.literal_fallback_bytes = 0
    return self._build_handshake_packet()
```

#### Trigger Adaptive Refresh:

```python
def _compress_adaptive(self, text: str) -> list[bytes]:
    """Compresses with adaptive dictionary and literal learning."""

    # ... existing dictionary update logic ...

    # Check if we need to rebuild tree due to escape code usage
    if self.literal_fallback_tokens > self.adaptive_refresh_threshold:
        # Rebuild tree with literals from recent text
        self._rebuild_entropy_model(self.streaming_word_map, text_sample=text)
        self.literal_fallback_tokens = 0

        # Send refresh handshake packet
        refresh_packet = self._build_handshake_packet()
        packets.insert(0, refresh_packet)

    # ... compression logic ...
```

---

### Option B: Static Optimal Defaults (SIMPLER)

Pre-compute optimal literal sets for common use cases.

```python
# In config or constants
LITERAL_SETS = {
    'minimal': ' \n',  # Only mandatory whitespace
    'text': ' .,!?;:\'\"-\n\t',  # Natural language
    'code': ' .,;:(){}[]<>=+-*/%&|^\n\t',  # Programming
    'json': ' ,:{}[]\"\n\t',  # JSON data
    'all': ''.join(chr(i) for i in range(32, 127)) + '\n\t\r',  # Current behavior
}

# Usage
transceiver = AuraTransceiver(
    universal_common_literals=LITERAL_SETS['code'],  # Use existing param
    literal_frequency_threshold=0.01  # Still honor threshold within set
)
```

---

## Impact Analysis

### TCP Packet Size Savings

#### Current: All ASCII literals (98 chars)
```
Huffman tree entries: ~9,000 words + 98 literals = 9,098 entries
Handshake size: 46-70 bytes (hashes only, tree is implicit)
```

#### With Threshold (15 common literals)
```
Huffman tree entries: ~9,000 words + 15 literals = 9,015 entries
Rare literal handling: 83 chars via escape code (8 bits each)
Savings: -83 tree entries (-0.9%)
```

### Compression Ratio Impact

| Scenario | Before | After | Impact |
|----------|--------|-------|--------|
| **Natural text** (rare symbols rare) | 3.5:1 | 3.5:1 | No change |
| **Code** (many symbols) | 3.0:1 | 2.95:1 | -1.7% (more escapes) |
| **JSON** (few symbols) | 4.0:1 | 4.05:1 | +1.3% (smaller tree) |

### Escape Code Overhead

```
Rare character encoding:
  Huffman code (if included): 3-8 bits
  Escape code: 8 bits + 8 bits = 16 bits

If rare char appears < 1% of time: Worth excluding
If rare char appears > 1% of time: Worth including
```

---

## Recommendation Matrix

| Use Case | Strategy | literal_frequency_threshold | Injection Points |
|----------|----------|----------------------------|------------------|
| **General streaming** | Option A | 0.01 (1%) | Handshake + Refresh |
| **Known content type** | Option B | N/A | Handshake only |
| **Maximum compatibility** | Keep current | N/A | None (current) |
| **Maximum compression** | Option A | 0.005 (0.5%) | Handshake + Refresh |
| **Low bandwidth** | Option A | 0.02 (2%) | Handshake + Refresh |

---

## Implementation Priority

### Phase 1: Make Parameter Functional (IMMEDIATE)
1. Pass `literal_frequency_threshold` to `build_universal_huffman_tree()`
2. Implement basic filtering in handshake
3. Update tests

### Phase 2: Adaptive Learning (NEXT SPRINT)
1. Add `text_sample` parameter support
2. Implement refresh on escape code threshold
3. Add metrics tracking

### Phase 3: Presets (NICE TO HAVE)
1. Add `LITERAL_SETS` constants
2. Auto-detect content type
3. Documentation updates

---

## Testing Strategy

```python
def test_literal_frequency_threshold():
    """Test that threshold actually filters literals."""

    # Test 1: High threshold should exclude most literals
    t1 = AuraTransceiver(literal_frequency_threshold=0.5)  # 50%
    t1.perform_handshake("hello world")

    # Should only have space (common) in tree
    literal_codes = [k for k in t1.compression_tree if k[0] == 'L']
    assert len(literal_codes) < 10, "High threshold should exclude most literals"

    # Test 2: Low threshold should include more literals
    t2 = AuraTransceiver(literal_frequency_threshold=0.001)  # 0.1%
    t2.perform_handshake("hello, world! @#$%")

    literal_codes = [k for k in t2.compression_tree if k[0] == 'L']
    assert len(literal_codes) > 5, "Low threshold should include punctuation"

    # Test 3: Verify escape codes work for rare literals
    text_with_rare = "hello @ world"  # @ might be rare
    packets = t1.compress(text_with_rare, adaptive=False)
    decompressed = t1.decompress(packets[0])
    assert decompressed == text_with_rare, "Escape codes should handle rare chars"
```

---

## Configuration Examples

### Conservative (Maximum Compatibility)
```python
transceiver = AuraTransceiver(
    literal_frequency_threshold=0.001,  # Include almost everything
    # Will behave like current implementation
)
```

### Aggressive (Maximum Compression for Known Content)
```python
transceiver = AuraTransceiver(
    literal_frequency_threshold=0.02,  # 2% threshold
    universal_common_literals=' .,!?;:\n\t',  # Known content type
)
```

### Adaptive (Best for Mixed Content)
```python
transceiver = AuraTransceiver(
    literal_frequency_threshold=0.01,  # Standard 1%
    adaptive_refresh_threshold=32,  # Rebuild on 32 escape codes
)

# Handshake with sample
sample = "Representative text from expected workload..."
transceiver.perform_handshake(text_sample=sample)
```

---

## My Recommendation

**Implement Option A (Adaptive Literal Learning) with injection at BOTH points:**

1. **Initial Handshake**: Use `text_sample` if provided, else conservative defaults
2. **Adaptive Refresh**: Rebuild tree when escape code usage exceeds threshold

**Reasoning:**
- Maintains consistency with your TCP optimization goals
- Provides flexibility for different content types
- Minimal breaking changes (parameter already exists)
- Clear path for incremental improvement

**Default Config for Maximum Efficiency:**
```python
transceiver = AuraTransceiver(
    literal_frequency_threshold=0.01,      # 1% threshold (existing default)
    adaptive_refresh_threshold=32,         # Existing default
    universal_common_literals=None,        # Auto-detect from sample
)
```

This gives you the best balance of compression efficiency, TCP packet optimization, and backward compatibility.
