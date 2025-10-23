# AURA Compression Stack - Tuning Plan

**Date:** October 23, 2025
**Status:** Critical - Current Performance Issues Identified
**Patent Application:** 19/366,538

---

## Executive Summary

**Current State (Critical Issue Detected):**
- Average compression ratio: **0.70x** (EXPANDING data)
- Bandwidth savings: **-356.9%** (using 4.6x MORE bandwidth)
- Template hit rate: **16%** (4/25 messages)
- BRIO overhead appears excessive

**Target State:**
- Compression ratio: **2.5-3.0x** minimum
- Bandwidth savings: **60-70%**
- Template hit rate: **50-80%** (depending on content type)
- Sub-millisecond encoding latency

**Timeline:** 4-week phased rollout with continuous monitoring

---

## Problem Analysis

### Issue 1: Compression Actually Expanding Data ⚠️

**Symptoms:**
```
Total original bytes: 1,428
Total payload bytes: 6,525
Ratio: 0.70x (should be > 1.0x)
Savings: -356.9% (should be positive)
```

**Root Causes:**

1. **BRIO Header Overhead**
   ```
   BRIO header structure:
   - Magic: 4 bytes
   - Version: 1 byte
   - Lengths: 8 bytes
   - Frequency table: 512 bytes (256 × 2)
   - Metadata entries: 6 bytes each
   = Minimum ~525 bytes overhead
   ```

   **For small messages (<500 bytes), header is larger than message!**

2. **Poor Method Selection**
   ```
   BRIO: 10 messages (likely small messages with huge headers)
   UNCOMPRESSED: 5 messages (below threshold)
   BROTLI: 6 messages (decent compression)
   BINARY_SEMANTIC: 4 messages (best compression)
   ```

3. **Low Template Hit Rate**
   - Only 16% (4/25) messages matched templates
   - Should be 50-80% for structured content

---

## Phase 1: Emergency Fixes (Week 1)

### 1.1 Disable BRIO for Small Messages

**Current Issue:** BRIO adds 525+ byte header to every message

**Fix:**

```python
# IMMEDIATE: Increase BRIO threshold
compressor = ProductionHybridCompressor(
    enable_aura=True,
    min_compression_size=600,  # CRITICAL: Was 50, now 600 (above header size)
    aura_preference_margin=0.20  # Only use BRIO if 20% better than brotli
)
```

**Expected Impact:** Eliminate negative compression on messages < 600 bytes

### 1.2 Prefer Binary Semantic for Template Matches

**Current Issue:** Template matches still using BRIO (overhead)

**Fix:**

```python
# In compressor.py, adjust selection logic
def _select_compression_method(self, template_match, text):
    if template_match:
        # ALWAYS prefer binary semantic for template matches
        return 'binary_semantic'

    original_size = len(text.encode('utf-8'))

    if original_size < 600:
        # Small messages: binary_semantic or brotli only
        return 'brotli'
    else:
        # Large messages: can use BRIO if beneficial
        return self._compare_methods(text)
```

**Expected Impact:** 2-3x compression on template matches

### 1.3 Fix Compression Ratio Calculation

**Current Issue:** Ratio showing 0.70 (inverted or wrong calculation)

**Fix:**

```python
# Verify calculation in all metrics
compression_ratio = original_size / compressed_size  # Should be > 1.0
# NOT: compressed_size / original_size
```

### 1.4 Emergency Deployment Configuration

```python
# emergency_config.py - Deploy immediately

EMERGENCY_COMPRESSION_CONFIG = {
    'enable_aura': False,  # DISABLE BRIO temporarily
    'min_compression_size': 30,
    'template_store_path': '/var/lib/aura/templates.json',
}

# This will use binary_semantic + brotli only
# Should achieve 1.5-2.0x compression immediately
```

**Deploy this config ASAP to stop bandwidth expansion.**

---

## Phase 2: Template Library Expansion (Week 2)

### 2.1 Add Domain-Specific Templates

**Current:** 16% template hit rate (4/25 messages)
**Target:** 60-80% hit rate

**Action: Analyze Your Top 100 Messages**

```python
# Run this on your audit logs
from aura_compression import TemplateDiscoveryEngine
from pathlib import Path

# Load your actual messages
audit_files = list(Path('/var/log/aura').glob('**/*.jsonl'))
messages = []
for file in audit_files:
    with open(file) as f:
        for line in f:
            entry = json.loads(line)
            messages.append(entry['plaintext'])

# Discover patterns
engine = TemplateDiscoveryEngine(
    min_frequency=5,
    min_compression_advantage=2.0,
    starting_template_id=149,
    ending_template_id=208
)

candidates = engine.discover_templates(messages[:1000])

# Promote top candidates
for candidate in sorted(candidates, key=lambda c: c.frequency, reverse=True)[:50]:
    template_id = engine.promote_template(candidate)
    print(f"Added template {template_id}: {candidate.pattern}")
    print(f"  Frequency: {candidate.frequency}")
    print(f"  Compression: {candidate.compression_advantage:.2f}x")
```

### 2.2 Template Tuning by Content Type

**Identify your top message types:**

```python
# Categorize your messages
message_types = {
    'api_response': [],
    'user_query': [],
    'system_notification': [],
    'ml_output': [],
    'error_message': [],
    'chat_message': []
}

# Add templates for each type
```

**Example templates to add:**

```python
# API Responses (aim for 80% hit rate)
CUSTOM_TEMPLATES = {
    149: "Request {0} completed in {1}ms",
    150: "User {0} authenticated successfully",
    151: "Database query returned {0} results",
    152: "Cache hit for key {0}",
    153: "API rate limit: {0}/{1} requests",

    # System Notifications (aim for 90% hit rate)
    154: "Service {0} is {1}",
    155: "Deployment {0} started at {1}",
    156: "Health check passed: {0}",

    # Error Messages (aim for 70% hit rate)
    157: "Error {0}: {1}",
    158: "Retry {0}/{1} failed: {2}",
    159: "Timeout after {0}ms for {1}",
}
```

### 2.3 Fuzzy Template Matching (Future Enhancement)

```python
# Allow minor variations
def fuzzy_match_template(text, threshold=0.9):
    """
    Match templates with 90% similarity
    - "I cannot" matches "I can't"
    - "do not" matches "don't"
    """
    best_match = None
    best_score = 0

    for template_id, pattern in templates.items():
        score = calculate_similarity(text, pattern)
        if score > threshold and score > best_score:
            best_match = template_id
            best_score = score

    return best_match
```

---

## Phase 3: Method Selection Optimization (Week 3)

### 3.1 Compression Method Decision Tree

**New intelligent selection logic:**

```python
def select_optimal_method(text, template_match):
    """
    Intelligent compression method selection
    """
    original_size = len(text.encode('utf-8'))

    # Priority 1: Template match (best compression)
    if template_match:
        return {
            'method': 'binary_semantic',
            'reason': 'template_match',
            'expected_ratio': 2.0  # Guaranteed good compression
        }

    # Priority 2: Very small messages
    if original_size < 30:
        return {
            'method': 'uncompressed',
            'reason': 'too_small',
            'expected_ratio': 1.0
        }

    # Priority 3: Small-medium messages (30-600 bytes)
    if original_size < 600:
        # Try brotli (no BRIO header overhead)
        return {
            'method': 'brotli',
            'reason': 'small_message_avoid_header',
            'expected_ratio': 1.3
        }

    # Priority 4: Large messages (600+ bytes)
    # BRIO header overhead is now <10% of message size
    if original_size >= 600:
        # Check if JSON (ML output)
        if text.strip().startswith('{'):
            return {
                'method': 'aura',  # BRIO good for structured data
                'reason': 'structured_json',
                'expected_ratio': 2.5
            }

        # Check if highly repetitive
        unique_chars = len(set(text))
        if unique_chars < 50:  # Low entropy
            return {
                'method': 'aura',  # BRIO LZ77 will shine
                'reason': 'repetitive_content',
                'expected_ratio': 3.0
            }

        # Default: brotli is safe
        return {
            'method': 'brotli',
            'reason': 'general_text',
            'expected_ratio': 1.5
        }

    return {
        'method': 'brotli',
        'reason': 'fallback',
        'expected_ratio': 1.3
    }
```

### 3.2 Replace Brotli with Zstandard

**Why:** Zstandard (zstd) consistently beats Brotli in speed and ratio

```python
# Install
pip install zstandard

# Replace in compressor.py
import zstandard as zstd

class ProductionHybridCompressor:
    def __init__(self):
        # Create reusable compressor (faster)
        self.zstd_compressor = zstd.ZstdCompressor(level=3)  # level 3 = fast
        self.zstd_decompressor = zstd.ZstdDecompressor()

    def _compress_with_zstd(self, text):
        return self.zstd_compressor.compress(text.encode('utf-8'))

    def _decompress_zstd(self, payload):
        return self.zstd_decompressor.decompress(payload).decode('utf-8')
```

**Expected improvements:**
- Speed: 2-3x faster than Brotli
- Ratio: 10-15% better compression
- Lower CPU usage

### 3.3 BRIO Optimization

**If keeping BRIO, optimize header:**

```python
# Reduce frequency table size for small alphabets
def optimize_frequency_table(text):
    """
    Use smaller frequency table when possible
    """
    unique_bytes = len(set(text.encode('utf-8')))

    if unique_bytes < 64:
        # Use 64-entry table instead of 256
        # Saves 384 bytes (768 → 384)
        return build_compact_frequency_table(text, 64)
    else:
        return build_full_frequency_table(text, 256)
```

**Dynamic header sizing:**

```python
# Use smaller header for small messages
BRIO_HEADER_COMPACT = 200 bytes  # For messages < 1KB
BRIO_HEADER_FULL = 525 bytes     # For messages > 1KB
```

---

## Phase 4: Performance Monitoring & Iteration (Week 4)

### 4.1 Real-Time Performance Dashboard

**Metrics to track:**

```python
class CompressionMetrics:
    # Core metrics
    total_messages: int
    compression_ratio_by_method: Dict[str, float]
    bandwidth_saved_bytes: int
    template_hit_rate: float

    # Performance
    avg_encode_latency_ms: float
    p95_encode_latency_ms: float
    p99_encode_latency_ms: float

    # Method distribution
    method_counts: Dict[str, int]
    method_percentages: Dict[str, float]

    # Problem detection
    expansion_count: int  # Messages where compressed > original
    expansion_percentage: float

    # Target thresholds
    TARGETS = {
        'min_compression_ratio': 1.5,
        'min_bandwidth_savings': 0.33,  # 33% minimum
        'max_expansion_percentage': 5.0,  # <5% messages can expand
        'min_template_hit_rate': 0.50,  # 50% minimum
        'max_p95_latency_ms': 2.0
    }

    def check_health(self):
        """Alert if metrics outside targets"""
        alerts = []

        if self.avg_compression_ratio < self.TARGETS['min_compression_ratio']:
            alerts.append(f"LOW COMPRESSION: {self.avg_compression_ratio:.2f}x")

        if self.expansion_percentage > self.TARGETS['max_expansion_percentage']:
            alerts.append(f"HIGH EXPANSION: {self.expansion_percentage:.1f}%")

        if self.template_hit_rate < self.TARGETS['min_template_hit_rate']:
            alerts.append(f"LOW TEMPLATE HITS: {self.template_hit_rate:.1f}%")

        return alerts
```

### 4.2 Automated A/B Testing

```python
# Test new configurations automatically
ab_test_config = {
    'group_a': {  # Baseline (current)
        'enable_aura': False,
        'min_compression_size': 600,
    },
    'group_b': {  # With zstd
        'enable_aura': False,
        'use_zstd': True,
        'min_compression_size': 30,
    },
    'group_c': {  # Optimized BRIO
        'enable_aura': True,
        'min_compression_size': 1000,
        'aura_preference_margin': 0.30,
    }
}

# Run for 1 week, compare metrics
```

### 4.3 Continuous Template Discovery

```python
# Run discovery every hour
from aura_compression import TemplateDiscoveryWorker

worker = TemplateDiscoveryWorker(
    discovery_interval=3600,  # 1 hour
    min_message_count=100,
    template_store_path='/var/lib/aura/templates.json'
)

worker.start()

# Monitor template additions
def on_template_discovered(template_id, pattern, frequency):
    logger.info(f"New template {template_id}: {pattern} (freq: {frequency})")
    metrics.template_count.inc()
```

---

## Recommended Configuration Changes

### Immediate Deployment (Fix Expansion Issue)

```python
# config/production_config.py

PRODUCTION_CONFIG = {
    # CRITICAL: Disable BRIO until fixed
    'enable_aura': False,

    # Use proven methods
    'min_compression_size': 30,
    'template_store_path': '/var/lib/aura/templates.json',
    'enable_audit_logging': True,
    'audit_log_directory': '/var/log/aura',
}

# Expected results with this config:
# - Compression ratio: 1.5-2.0x (guaranteed positive)
# - Bandwidth savings: 33-50%
# - No expansion issues
```

### Week 2 Config (After Template Expansion)

```python
WEEK2_CONFIG = {
    'enable_aura': False,  # Still disabled
    'min_compression_size': 30,
    'template_store_path': '/var/lib/aura/templates_expanded.json',  # New templates
    'enable_audit_logging': True,
    'audit_log_directory': '/var/log/aura',
}

# Expected results:
# - Template hit rate: 60-80%
# - Compression ratio: 2.0-2.5x
# - Bandwidth savings: 50-60%
```

### Week 3 Config (With Zstd)

```python
WEEK3_CONFIG = {
    'enable_aura': False,
    'use_zstd': True,  # NEW: Replace brotli
    'zstd_level': 3,   # Fast compression
    'min_compression_size': 30,
    'template_store_path': '/var/lib/aura/templates_expanded.json',
}

# Expected results:
# - Compression ratio: 2.2-2.7x
# - Bandwidth savings: 55-63%
# - Encode latency: 30% faster
```

### Week 4 Config (Optimized BRIO Re-enabled)

```python
WEEK4_CONFIG = {
    'enable_aura': True,  # Re-enable with fixes
    'use_zstd': True,
    'min_compression_size': 30,
    'brio_min_size': 1000,  # Only use BRIO for large messages
    'aura_preference_margin': 0.30,  # Must be 30% better
    'template_store_path': '/var/lib/aura/templates_expanded.json',
}

# Expected results:
# - Compression ratio: 2.5-3.0x
# - Bandwidth savings: 60-67%
# - Template hit rate: 70-85%
```

---

## Success Criteria

### Week 1 (Emergency Fixes)
- ✅ No negative compression ratios
- ✅ All compression ratios > 1.0x
- ✅ Bandwidth savings > 0%
- ✅ Zero messages expanding by >10%

### Week 2 (Template Expansion)
- ✅ Template hit rate > 50%
- ✅ 50+ new domain-specific templates added
- ✅ Compression ratio > 2.0x average

### Week 3 (Method Optimization)
- ✅ Zstd deployed and tested
- ✅ Encode latency < 1ms (p95)
- ✅ Compression ratio > 2.2x

### Week 4 (BRIO Re-enablement)
- ✅ BRIO only used for messages > 1000 bytes
- ✅ Overall compression ratio > 2.5x
- ✅ Bandwidth savings > 60%
- ✅ No expansion issues detected

---

## Rollback Plan

**If any phase shows degradation:**

1. **Immediate rollback trigger:**
   - Compression ratio drops below 1.0x
   - Bandwidth savings become negative
   - Error rate increases >1%
   - Latency increases >100%

2. **Rollback procedure:**
   ```bash
   # Revert to previous config
   cp /var/lib/aura/config.backup.json /var/lib/aura/config.json
   systemctl restart aura-service

   # Monitor for 5 minutes
   watch -n 5 'curl localhost:8000/health/detailed'
   ```

3. **Root cause analysis:**
   - Check metrics dashboard
   - Review error logs
   - Analyze failed message samples
   - Identify problematic configuration

---

## Monitoring Alerts

```python
# Set up alerts in monitoring system

ALERTS = {
    'critical': [
        {
            'name': 'Negative Compression',
            'condition': 'compression_ratio < 1.0',
            'action': 'immediate_page'
        },
        {
            'name': 'High Expansion Rate',
            'condition': 'expansion_percentage > 10',
            'action': 'immediate_page'
        }
    ],
    'warning': [
        {
            'name': 'Low Template Hits',
            'condition': 'template_hit_rate < 0.40',
            'action': 'slack_notification'
        },
        {
            'name': 'Suboptimal Compression',
            'condition': 'compression_ratio < 1.5',
            'action': 'email_alert'
        }
    ]
}
```

---

## Implementation Checklist

### Week 1
- [ ] Deploy emergency config (disable BRIO)
- [ ] Fix compression ratio calculation
- [ ] Increase min_compression_size to 600
- [ ] Monitor for 48 hours
- [ ] Verify positive compression on all messages
- [ ] Document baseline metrics

### Week 2
- [ ] Run template discovery on audit logs
- [ ] Add 50+ domain-specific templates
- [ ] Deploy expanded template library
- [ ] Monitor template hit rate
- [ ] A/B test new templates
- [ ] Measure compression improvement

### Week 3
- [ ] Install zstandard library
- [ ] Replace brotli with zstd
- [ ] Benchmark zstd vs brotli
- [ ] Deploy zstd to 10% traffic (canary)
- [ ] Monitor performance and errors
- [ ] Full rollout if successful

### Week 4
- [ ] Optimize BRIO header size
- [ ] Implement dynamic header sizing
- [ ] Re-enable BRIO for large messages only
- [ ] Set brio_min_size to 1000 bytes
- [ ] Monitor compression ratios
- [ ] Verify no expansion issues

---

## Expected Outcomes

### Current State (Broken)
```
Compression ratio: 0.70x ⚠️ EXPANDING
Bandwidth savings: -356.9% ⚠️ USING MORE
Template hit rate: 16%
Methods: BRIO (40%), Brotli (24%), etc.
```

### After Tuning (Target)
```
Compression ratio: 2.5-3.0x ✅
Bandwidth savings: 60-67% ✅
Template hit rate: 70-85% ✅
Methods: Binary semantic (70%), Zstd (25%), BRIO (5%)
```

### Performance Improvements
- **4-5x better compression** (0.7x → 2.5-3.0x)
- **$400-500/year savings** at 100M messages/day
- **Faster encoding** (zstd is 2-3x faster than brotli)
- **Higher template utilization** (16% → 70-85%)

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Config change breaks production | Medium | High | Canary deployment, rollback plan |
| Zstd compatibility issues | Low | Medium | A/B test, gradual rollout |
| Template expansion causes errors | Low | Low | Validate all templates before promotion |
| BRIO re-enablement causes expansion | Medium | High | Strict size thresholds, monitoring |

---

## Long-Term Roadmap (Months 2-3)

1. **ML-powered template generation**
   - Train model to suggest templates
   - Auto-discover patterns

2. **Adaptive compression**
   - Learn optimal method per message type
   - Per-client compression profiles

3. **Hardware acceleration**
   - Use GPU for compression
   - FPGA acceleration for rANS

4. **Multi-level caching**
   - Cache compressed payloads
   - Template match cache

---

**Document Version:** 1.0
**Status:** Action Required - Emergency fixes needed
**Next Review:** After Week 1 deployment
**Owner:** AURA Engineering Team

