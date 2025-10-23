# 09-CONFIG: Configuration Files

This directory contains configuration files for different deployment scenarios.

---

## Available Configurations

### 1. AI Streaming Configuration

**`ai_streaming.json`** - Optimized for real-time AI streaming

```json
{
  "compression": {
    "template_matching_enabled": true,
    "lz77_enabled": true,
    "semantic_enabled": false,
    "fallback": "brotli",
    "min_compression_ratio": 1.1
  },
  "metadata": {
    "fast_path_enabled": true,
    "intent_classification_enabled": true
  },
  "conversation": {
    "acceleration_enabled": true,
    "pattern_learning_enabled": true,
    "cache_size": 1000
  },
  "audit": {
    "enabled": true,
    "compliance_mode": "strict",
    "log_ai_generated": true,
    "safety_checks_enabled": true
  }
}
```

**Use Case**: ChatGPT-style AI assistants, real-time chat

**Performance**: 4.3:1 compression, 87× speedup

---

### 2. Batch Processing Configuration

**`batch_processing.json`** - Optimized for high-throughput batch jobs

```json
{
  "compression": {
    "template_matching_enabled": true,
    "lz77_enabled": true,
    "semantic_enabled": true,
    "fallback": "brotli",
    "min_compression_ratio": 1.0
  },
  "metadata": {
    "fast_path_enabled": false,
    "intent_classification_enabled": false
  },
  "conversation": {
    "acceleration_enabled": false,
    "pattern_learning_enabled": false,
    "cache_size": 0
  },
  "audit": {
    "enabled": false,
    "compliance_mode": "disabled"
  },
  "performance": {
    "max_threads": 8,
    "batch_size": 1000
  }
}
```

**Use Case**: Log compression, dataset preprocessing

**Performance**: 6.5:1 compression (BRIO enabled), high throughput

---

### 3. Code Compression Configuration

**`code_compression.json`** - Optimized for source code

```json
{
  "compression": {
    "template_matching_enabled": true,
    "lz77_enabled": true,
    "semantic_enabled": false,
    "fallback": "brotli",
    "min_compression_ratio": 1.2
  },
  "templates": {
    "code_templates_enabled": true,
    "languages": ["python", "javascript", "rust", "go"],
    "auto_discovery_enabled": true
  },
  "metadata": {
    "fast_path_enabled": true,
    "language_detection_enabled": true
  },
  "audit": {
    "enabled": false
  }
}
```

**Use Case**: Code repository compression, snippet storage

**Performance**: 5.2:1 compression, language-aware

---

### 4. Real-Time Chat Configuration

**`realtime_chat.json`** - Optimized for low-latency chat

```json
{
  "compression": {
    "template_matching_enabled": true,
    "lz77_enabled": false,
    "semantic_enabled": false,
    "fallback": "none",
    "min_compression_ratio": 1.0
  },
  "metadata": {
    "fast_path_enabled": true,
    "intent_classification_enabled": true
  },
  "conversation": {
    "acceleration_enabled": true,
    "pattern_learning_enabled": true,
    "cache_size": 500
  },
  "performance": {
    "max_latency_ms": 5,
    "priority": "speed"
  },
  "audit": {
    "enabled": true,
    "compliance_mode": "minimal",
    "async_logging": true
  }
}
```

**Use Case**: Instant messaging, live chat support

**Performance**: 3.2:1 compression, <5ms latency

---

## Configuration Schema

### Root Configuration

```json
{
  "compression": { /* Compression settings */ },
  "metadata": { /* Metadata settings */ },
  "conversation": { /* Conversation acceleration */ },
  "templates": { /* Template library settings */ },
  "audit": { /* Audit logging settings */ },
  "performance": { /* Performance tuning */ },
  "security": { /* Security settings */ }
}
```

---

### Compression Settings

```json
{
  "compression": {
    "template_matching_enabled": true,     // Use template matching
    "lz77_enabled": true,                  // Use LZ77 backreferences
    "semantic_enabled": false,             // Use semantic (BRIO) compression
    "fallback": "brotli",                  // Fallback: "brotli", "gzip", "none"
    "min_compression_ratio": 1.1,          // Never-worse threshold
    "max_window_size": 32768,              // LZ77 window size (bytes)
    "template_priority": true              // Try templates first
  }
}
```

---

### Metadata Settings

```json
{
  "metadata": {
    "fast_path_enabled": true,             // Enable metadata fast-path
    "intent_classification_enabled": true,  // Classify from metadata
    "language_detection_enabled": false,    // Detect programming language
    "metadata_format": "binary"            // "binary" or "json"
  }
}
```

---

### Conversation Settings

```json
{
  "conversation": {
    "acceleration_enabled": true,          // Enable conversation acceleration
    "pattern_learning_enabled": true,      // Learn patterns over time
    "cache_size": 1000,                    // Max cached patterns
    "platform_learning_enabled": false,    // Share patterns across users
    "learning_rate": 0.1                   // Pattern learning rate
  }
}
```

---

### Template Settings

```json
{
  "templates": {
    "library_path": "templates.json",      // Template library file
    "code_templates_enabled": true,        // Use code templates
    "languages": ["python", "javascript"], // Supported languages
    "auto_discovery_enabled": true,        // Auto-discover templates
    "discovery_threshold": 3,              // Min occurrences to create template
    "max_templates": 10000                 // Max template library size
  }
}
```

---

### Audit Settings

```json
{
  "audit": {
    "enabled": true,                       // Enable audit logging
    "compliance_mode": "strict",           // "strict", "minimal", "disabled"
    "log_dir": "/var/log/aura",            // Log directory
    "log_ai_generated": true,              // Log AI output pre-moderation
    "safety_checks_enabled": true,         // Run content safety checks
    "async_logging": false,                // Async vs sync logging
    "retention_days": 2555,                // 7 years (GDPR/HIPAA)
    "encryption_enabled": false,           // Encrypt logs at rest
    "immutable_logs": true                 // Append-only logs
  }
}
```

---

### Performance Settings

```json
{
  "performance": {
    "max_threads": 4,                      // Thread pool size
    "batch_size": 100,                     // Batch processing size
    "max_latency_ms": 10,                  // Max acceptable latency
    "priority": "balanced",                // "speed", "ratio", "balanced"
    "memory_limit_mb": 512,                // Max memory usage
    "connection_pool_size": 100            // WebSocket connections
  }
}
```

---

### Security Settings

```json
{
  "security": {
    "content_safety_enabled": true,        // Content moderation
    "safety_api": "openai",                // "openai", "custom", "none"
    "safety_threshold": 0.8,               // Moderation threshold
    "block_harmful_content": true,         // Block vs flag
    "rate_limiting_enabled": true,         // Rate limiting
    "max_requests_per_minute": 1000,       // Rate limit
    "encryption_required": false           // Require TLS
  }
}
```

---

## Loading Configurations

### Python

```python
from aura import AURAServer
import json

# Load configuration
with open('config/ai_streaming.json') as f:
    config = json.load(f)

# Create server with config
server = AURAServer(
    template_matching=config['compression']['template_matching_enabled'],
    audit_enabled=config['audit']['enabled'],
    compliance_mode=config['audit']['compliance_mode']
)
```

### JavaScript

```javascript
const config = require('./config/realtime_chat.json');

const client = new AURAClient(wsUrl, {
  fastPath: config.metadata.fast_path_enabled,
  acceleration: config.conversation.acceleration_enabled
});
```

---

## Environment Variables

### Override Configuration

```bash
# Override compression settings
export AURA_COMPRESSION_ENABLED=true
export AURA_MIN_RATIO=1.1

# Override audit settings
export AURA_AUDIT_ENABLED=true
export AURA_LOG_DIR=/var/log/aura

# Override performance settings
export AURA_MAX_THREADS=8
export AURA_BATCH_SIZE=1000
```

### Priority Order

1. Environment variables (highest priority)
2. Configuration file
3. Default values (lowest priority)

---

## Configuration Validation

### Validate Configuration

```python
from aura.config import validate_config

config = load_config('config/ai_streaming.json')
errors = validate_config(config)

if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration valid!")
```

### Schema Validation

```bash
# Validate against JSON schema
python -m aura.config.validate config/ai_streaming.json
```

---

## Deployment Scenarios

### Development

**`development.json`**:
```json
{
  "compression": {"template_matching_enabled": true},
  "audit": {"enabled": true, "compliance_mode": "minimal"},
  "performance": {"max_threads": 1},
  "debug": true
}
```

### Staging

**`staging.json`**:
```json
{
  "compression": {"template_matching_enabled": true},
  "audit": {"enabled": true, "compliance_mode": "strict"},
  "performance": {"max_threads": 4},
  "debug": false
}
```

### Production

**`production.json`**:
```json
{
  "compression": {"template_matching_enabled": true},
  "audit": {
    "enabled": true,
    "compliance_mode": "strict",
    "encryption_enabled": true,
    "immutable_logs": true
  },
  "performance": {
    "max_threads": 8,
    "memory_limit_mb": 2048
  },
  "security": {
    "content_safety_enabled": true,
    "rate_limiting_enabled": true
  },
  "debug": false
}
```

---

## Configuration Best Practices

### 1. Start with Defaults
```python
from aura.config import default_config

config = default_config()
config['compression']['semantic_enabled'] = True
```

### 2. Validate Before Use
```python
errors = validate_config(config)
assert not errors, f"Invalid config: {errors}"
```

### 3. Use Environment-Specific Configs
```bash
# Load environment-specific config
python -m aura.server --config config/production.json
```

### 4. Monitor Performance
```python
# Log configuration on startup
logger.info(f"Starting with config: {config}")
```

---

## Troubleshooting

### Issue: Low Compression Ratio

**Config Fix**:
```json
{
  "compression": {
    "template_matching_enabled": true,
    "lz77_enabled": true,
    "semantic_enabled": true,  // Enable BRIO
    "min_compression_ratio": 1.0  // Lower threshold
  }
}
```

### Issue: High Latency

**Config Fix**:
```json
{
  "compression": {
    "lz77_enabled": false,  // Disable slow compression
    "semantic_enabled": false
  },
  "performance": {
    "priority": "speed",
    "max_latency_ms": 5
  },
  "audit": {
    "async_logging": true  // Async logging
  }
}
```

### Issue: Memory Usage Too High

**Config Fix**:
```json
{
  "conversation": {
    "cache_size": 100  // Reduce cache
  },
  "templates": {
    "max_templates": 1000  // Limit templates
  },
  "performance": {
    "memory_limit_mb": 256  // Set limit
  }
}
```

---

## Configuration Migration

### v0.9 → v1.0

```python
def migrate_config(old_config):
    """Migrate v0.9 config to v1.0"""
    new_config = {
        "compression": {
            "template_matching_enabled": old_config.get("templates", True),
            "lz77_enabled": old_config.get("lz77", True),
            "fallback": old_config.get("fallback", "brotli")
        },
        "audit": {
            "enabled": old_config.get("audit", False),
            "compliance_mode": "strict" if old_config.get("audit") else "disabled"
        }
    }
    return new_config
```

---

**Directory**: 09-CONFIG/
**Last Updated**: October 22, 2025
**Status**: 4 production-ready configurations for common use cases
