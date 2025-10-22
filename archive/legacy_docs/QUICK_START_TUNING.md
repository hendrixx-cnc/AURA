# AURA Protocol Tuning - Quick Start Guide

**Last Updated**: 2025-10-22

---

## What Just Got Fixed? 🎉

**Problem**: Small messages were being EXPANDED instead of compressed.
- Example: 45 bytes → 405 bytes (9x larger!)

**Solution**: Added smart threshold that bypasses compression for small data.
- New result: 45 bytes → 46 bytes (only 1 byte overhead)

**Improvement**: 88.6% reduction in overhead for small messages!

---

## How to Use the Fixed Protocol

### Basic Usage (Default Settings)

```python
from aura_compressor.streamer import AuraTransceiver

# Create server and client
server = AuraTransceiver()  # Automatically uses min_compression_size=200
client = AuraTransceiver()

# Handshake
handshake = server.perform_handshake()
client.receive_handshake(handshake)

# Compress & send
text = "Your message here"
compressed = server.compress(text, adaptive=False)
# Send compressed[0] over the network...

# Receive & decompress
decompressed = client.decompress(compressed[0])
# decompressed == text
```

**What happens automatically**:
- Messages <200 bytes: Sent uncompressed (1 byte overhead)
- Messages ≥200 bytes: Compressed normally (saves bandwidth)

---

## Configuration for Different Use Cases

### 1. Real-Time Chat (Optimize for Speed)

```python
chat_server = AuraTransceiver(
    min_compression_size=100,      # Lower threshold
    adaptive_refresh_threshold=16   # Quick dictionary updates
)
```

**Best for**: WebSocket chat, messaging apps, real-time collaboration

---

### 2. AI/LLM API Streaming (Optimize for AI Text)

```python
api_server = AuraTransceiver(
    min_compression_size=200,      # Balanced
    adaptive_refresh_threshold=32,  # Moderate adaptation
    enable_server_audit=True        # Track performance
)
```

**Best for**: Streaming GPT/Claude responses, AI API endpoints

---

### 3. Batch Processing (Optimize for Throughput)

```python
batch_server = AuraTransceiver(
    min_compression_size=500,       # Higher threshold
    adaptive_refresh_threshold=128  # Fewer dictionary updates
)
```

**Best for**: Processing large documents, log files, bulk data

---

### 4. Always Compress (No Threshold)

```python
compress_all = AuraTransceiver(
    min_compression_size=0  # Always compress, even tiny data
)
```

**Best for**: When you need consistent behavior regardless of size

---

## Quick Tests

### Test 1: Verify the fix works
```bash
cd /Users/hendrixx./Downloads/AURA-main
python3 test_small_data.py
```

Expected output: All ✅ (tests pass)

---

### Test 2: See the improvement
```bash
python3 demo_improvement.py
```

Expected output: Shows 88.6% improvement

---

### Test 3: Original tests still work
```bash
cd packages/aura-compressor-py
python3 src/aura_compressor/test_streamer.py
```

Expected output: 🎉 All bidirectional tests passed successfully! 🎉

---

## Parameters You Can Tune

| Parameter | Default | What It Does | When to Change |
|-----------|---------|--------------|----------------|
| `min_compression_size` | 200 | Minimum bytes before compression | Lower for chat (100), higher for batch (500) |
| `adaptive_refresh_threshold` | 32 | Dictionary update frequency | Lower for evolving vocab (16), higher for stable (128) |
| `enable_server_audit` | False | Track compression metrics | Enable in production for monitoring |

---

## Performance Expectations

### Small Data (<200 bytes)
- **Overhead**: 1 byte (packet type)
- **Ratio**: ~0.98:1 (minimal expansion)
- **Speed**: Instant (no compression overhead)

### Medium Data (200-1000 bytes)
- **Compression**: Varies by content
- **Ratio**: 1.0-1.5:1 typical
- **Speed**: <10ms on modern hardware

### Large Data (>1000 bytes)
- **Compression**: Good
- **Ratio**: 2.0-4.0:1 for AI text
- **Speed**: <50ms for 10KB

---

## Common Issues

### Issue: Still seeing expansion
**Symptom**: Small messages are getting larger
**Solution**: Make sure you're using `compress()` not `compress_chunk()`

```python
# WRONG (has JSON overhead)
compressed = server.compress_chunk(text)

# RIGHT (efficient)
compressed = server.compress(text, adaptive=False)
```

---

### Issue: Want different threshold per message
**Symptom**: Need dynamic thresholds
**Solution**: Create multiple transceiver instances or adjust threshold

```python
# Option 1: Multiple instances
chat_server = AuraTransceiver(min_compression_size=100)
batch_server = AuraTransceiver(min_compression_size=500)

# Option 2: Adjust threshold (not recommended in production)
server.min_compression_size = 300  # Change threshold
```

---

## What's Next?

### Phase 2: More Configurable Parameters ✅
- Use `AuraTransceiver.literal_frequency_threshold`, `min_adaptive_occurrences`, and `min_adaptive_word_length` to tune compression behavior.
- Adjust universal Huffman weights with `word_base_frequency` / `literal_base_frequency`.
- Load presets via `AuraConfig.load("config/<preset>.json")` and `AuraTransceiver.from_config(...)`.

### Phase 3: Auto-Tuning ✅
- Swap in `AutoTuningTransceiver` to monitor ratios/latency and self-adjust adaptive thresholds.
- Inspect `server.get_auto_tuning_history()` to review recent tuning decisions.
- Use env presets or constructor arguments to bound aggressiveness (`tune_interval`, `ratio_target`, etc.).

### Environment Overrides ✅
- Populate `.env.example` and export `AURA_*` variables to override defaults without code changes.
- `AURA_CONFIG_PATH` can point to any JSON preset under `config/` for quick swapping.

### Phase 4: Benchmarking ✅
- Run `python3 benchmarks/benchmark_suite.py --quick --no-large` for fast health-checks or omit flags for full sweep.
- Review/update `benchmarks/baseline_quick.json` when algorithms change and re-run `test_benchmark_regression.py`.
- Use generated JSON summaries to feed dashboards or SLA monitoring.

**See**: `PROTOCOL_TUNING_GUIDE.md` for full roadmap

---

## Need Help?

### Documentation Files
- `PROTOCOL_TUNING_GUIDE.md` - Full tuning guide (parameters, strategies, presets)
- `IMPLEMENTATION_SUMMARY.md` - Technical details of what was implemented
- `QUICK_START_TUNING.md` - This file (quick reference)

### Test Files
- `test_small_data.py` - Comprehensive small data tests
- `demo_improvement.py` - Before/after demonstration
- `test_streamer.py` - Original bidirectional tests

### Source Files
- `packages/aura-compressor-py/src/aura_compressor/streamer.py` - Main implementation

---

## Summary

✅ Small data expansion **FIXED**
✅ Now handles tiny messages efficiently (1 byte overhead)
✅ Still compresses large data well (2-4:1 for AI text)
✅ Configurable for different use cases
✅ Fully backward compatible

**Start using**: `AuraTransceiver(min_compression_size=200)` and enjoy efficient compression!

---

**Questions?** Check `PROTOCOL_TUNING_GUIDE.md` or assign tasks in the "Implementation Checklist" section.
