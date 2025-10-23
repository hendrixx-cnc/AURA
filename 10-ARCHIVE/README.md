# 10-ARCHIVE: Legacy Files

This directory contains legacy files from previous development iterations.

---

## ⚠️ Warning

**These files are archived for historical reference only.**

- ❌ Do NOT use in production
- ❌ Not maintained
- ❌ May contain bugs or outdated approaches
- ✅ Kept for reference and learning

---

## Archive Structure

```
10-ARCHIVE/
├── legacy_docs/          # Old documentation
├── legacy_demos/         # Old demonstration scripts
├── old_benchmarks/       # Superseded benchmark scripts
└── old_compression_methods/  # Experimental compression approaches
```

---

## Legacy Documentation

**`legacy_docs/`** - Old documentation files

### Notable Documents

**`BRUTAL_HONEST_ASSESSMENT.md`** (2025-10-20)
- Replaced by: `docs/business/BRUTAL_HONEST_PATENT_ASSESSMENT.md`
- Reason: Updated with 35-claim patent analysis

**`CHATGPT_COORDINATION.md`** (2025-10-15)
- Historical: Coordination notes from early development
- Superseded by: Developer-focused documentation

**`CONVERSATION_SUMMARY.md`** (2025-10-18)
- Historical: Mid-development summary
- Superseded by: Comprehensive README.md

**`PROTOCOL_TUNING_GUIDE.md`** (2025-09-25)
- Replaced by: `03-TECHNICAL/DEVELOPER_GUIDE.md`
- Reason: Outdated tuning parameters

---

## Legacy Demos

**`legacy_demos/`** - Old demonstration scripts

### Archived Demos

**`auditable_streaming_demo.py`** (2025-10-10)
- Replaced by: `06-DEMOS/demo_compliance.py`
- Reason: Audit architecture redesigned (4-log system)

**`browser_ai_websocket_test.py`** (2025-09-20)
- Replaced by: `06-DEMOS/browser_demo.html`
- Reason: Full browser UI implementation

**`real_aura_streaming.py`** (2025-09-15)
- Replaced by: `06-DEMOS/demo_streaming.py`
- Reason: Updated for new server SDK

**`websocket_adaptive_test.py`** (2025-09-10)
- Replaced by: `07-TESTS/test_streaming_integration.py`
- Reason: Converted to proper test suite

---

## Old Benchmarks

**`old_benchmarks/`** - Superseded benchmark scripts

### Archived Benchmarks

**`test_raw_aura.py`** (2025-10-05)
- Replaced by: `08-BENCHMARKS/benchmark_suite.py`
- Reason: Comprehensive benchmark suite created

**`test_tcp_optimizations.py`** (2025-09-28)
- Replaced by: `08-BENCHMARKS/benchmark_streaming.py`
- Reason: WebSocket replaced TCP approach

**`find_breakeven.py`** (2025-09-20)
- Replaced by: Configuration-based approach
- Reason: Dynamic breakeven calculation in compressor

**`packet_optimizer.py`** (2025-09-18)
- Superseded: Packet-level optimization removed
- Reason: Focus on message-level compression

---

## Old Compression Methods

**`old_compression_methods/`** - Experimental approaches not adopted

### Archived Methods

**`binary_semantic_compression.py`** (2025-09-25)
- Status: Experimental, not adopted
- Reason: BRIO codec approach preferred
- Performance: 5.8:1 (vs 6.5:1 BRIO target)

**`hybrid_compression.py`** (2025-09-22)
- Status: Superseded by current hybrid pipeline
- Reason: Template-first approach more effective

**`manual_semantic_compression_test.py`** (2025-09-20)
- Status: Proof-of-concept only
- Reason: Automated semantic compression implemented

---

## Why Archived?

### Legacy Documentation

**Reasons for archival**:
1. Outdated information (old patent claim counts, old performance numbers)
2. Replaced by comprehensive documentation in numbered directories
3. Historical development notes no longer relevant

**What to use instead**:
- Patent docs: `01-PATENT/`
- Business docs: `02-BUSINESS/`
- Technical docs: `03-TECHNICAL/`

### Legacy Demos

**Reasons for archival**:
1. Superseded by production-ready demos in `06-DEMOS/`
2. Old WebSocket implementations before server SDK
3. Test scripts converted to proper test suite in `07-TESTS/`

**What to use instead**:
- Demos: `06-DEMOS/`
- Tests: `07-TESTS/`

### Old Benchmarks

**Reasons for archival**:
1. Replaced by comprehensive benchmark suite
2. Measured now-obsolete approaches (TCP vs WebSocket)
3. Inconsistent methodology

**What to use instead**:
- Benchmarks: `08-BENCHMARKS/benchmark_suite.py`
- Results: `08-BENCHMARKS/results/`

### Old Compression Methods

**Reasons for archival**:
1. Experimental approaches that didn't perform as well
2. Superseded by current hybrid compression pipeline
3. Complexity not justified by performance gains

**What to use instead**:
- Core compression: `05-CORE/compressor.py`
- BRIO codec: `05-CORE/experimental/brio/`

---

## Learning from the Archive

### Useful for Understanding

**Evolution of AURA**:
1. Started with TCP-based approach → switched to WebSocket
2. Single audit log → 4-log separated architecture
3. Manual template creation → automatic discovery
4. Various compression experiments → unified hybrid pipeline

**Design Decisions**:
- Why WebSocket over TCP? (See `old_benchmarks/test_tcp_optimizations.py`)
- Why template-first? (See `old_compression_methods/hybrid_compression.py`)
- Why 4-log architecture? (See `legacy_docs/BRUTAL_HONEST_ASSESSMENT.md`)

**Performance Evolution**:
```
Sept 2025:  2.1:1 compression  (early experiments)
Oct 2025:   4.3:1 compression  (template matching added)
Future:     6.5:1 compression  (BRIO codec target)
```

---

## Restoration

### If You Need to Restore

**DON'T** use archived files directly. Instead:

1. **Review the archived file** to understand the approach
2. **Check current implementation** in numbered directories
3. **Adapt the concept** to current architecture if needed

**Example**:
```bash
# ❌ DON'T DO THIS
cp 10-ARCHIVE/old_benchmarks/test_raw_aura.py 08-BENCHMARKS/

# ✅ DO THIS INSTEAD
# 1. Read archived file to understand what it was measuring
# 2. Check if current benchmark suite covers it
# 3. Add missing benchmark to benchmark_suite.py
```

---

## Cleanup Policy

### When Files Get Archived

**Criteria**:
1. File superseded by newer implementation
2. Approach abandoned after experimentation
3. Documentation outdated by >30 days

**Process**:
1. Move to appropriate `10-ARCHIVE/` subdirectory
2. Update this README.md with archival reason
3. Remove from main codebase

### When Files Get Deleted

**Criteria**:
1. Archived for >1 year
2. No historical value
3. Redundant with other archives

**Process**:
1. Review archive contents annually
2. Delete truly obsolete files
3. Keep historically significant experiments

---

## Archive Contents

### Legacy Docs (14 files)
```
legacy_docs/
├── BRUTAL_HONEST_ASSESSMENT.md
├── BROWSER_AI_PIPELINE_ANALYSIS.md
├── CHATGPT_COORDINATION.md
├── CONVERSATION_SUMMARY.md
├── Commercial-License.md
├── IMPLEMENTATION_SUMMARY.md
├── LITERAL_FREQUENCY_IMPLEMENTATION_COMPLETE.md
├── LITERAL_FREQUENCY_OPTIMIZATION.md
├── OPTIMIZED_PIPELINE_SUMMARY.md
├── PROTOCOL_TUNING_GUIDE.md
├── QUICK_START_TUNING.md
├── SEMANTIC_COMPRESSION_STRATEGY.md
├── STRATEGIC_REASSESSMENT.md
└── TCP_OPTIMIZATION_SUMMARY.md
```

### Legacy Demos (16 files)
```
legacy_demos/
├── auditable_streaming_demo.py
├── browser_ai_websocket_test.py
├── dual_mode_websocket.py
├── real_aura_streaming.py
├── real_tcp_streaming.py
├── verify_aura.py
├── websocket_adaptive_test.py
├── websocket_aura_streaming.py
├── websocket_packet_test.py
├── websocket_stream_test.py
├── websocket_test.py
├── benchmark_results.json
├── semantic_compression_results.json
└── test.txt
```

### Old Benchmarks (14 files)
```
old_benchmarks/
├── debug_compression.py
├── debug_escape.py
├── demo_improvement.py
├── find_breakeven.py
├── packet_optimizer.py
├── test_auditing_comparison.py
├── test_auto_tuning.py
├── test_benchmark_regression.py
├── test_bidirectional.py
├── test_large_breakeven.py
├── test_large_scale.py
├── test_literal_frequency_optimization.py
├── test_optimized_handshake.py
└── test_tcp_optimizations.py
```

### Old Compression Methods (4 files)
```
old_compression_methods/
├── benchmark_aura_vs_industry.py
├── binary_semantic_compression.py
├── hybrid_compression.py
└── manual_semantic_compression_test.py
```

**Total Archived Files**: 48 files

---

## Historical Performance Data

### September 2025 (Early Development)
- Compression ratio: 2.1:1
- Processing speed: 8.5ms
- Approach: Simple template matching

### October 2025 (Production Release)
- Compression ratio: 4.3:1
- Processing speed: 3.2ms
- Approach: Hybrid pipeline (templates + LZ77 + fallback)

### Future (BRIO Integration)
- Target ratio: 6.5:1
- Target speed: 1.5ms
- Approach: Add semantic compression (rANS)

---

## Contact

**Questions about archived files?**
- Email: support@auraprotocol.org
- GitHub Issues: Tag with `archive` label

---

**Directory**: 10-ARCHIVE/
**Last Updated**: October 22, 2025
**Total Files**: 48 archived files from September-October 2025 development
**Status**: Historical reference only, not for production use
