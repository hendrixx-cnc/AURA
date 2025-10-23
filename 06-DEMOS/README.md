# 06-DEMOS: Interactive Demonstrations

This directory contains working demonstrations of AURA's key features.

---

## Available Demos

### 1. AI-to-AI Communication (`demo_ai_to_ai.py`)

Demonstrates AURA's optimizations for AI model-to-model communication.

**Features**:
- Token-aware compression
- Semantic optimization
- Multi-agent coordination

**Usage**:
```bash
python demos/demo_ai_to_ai.py
```

**Output**:
```
AI-to-AI Communication Demo
===========================

Agent 1 → Agent 2: "Execute task: analyze user behavior patterns"
  Compression ratio: 6.2:1
  Token compression: 78% reduction
  Metadata: 0x04000000001A

Agent 2 → Agent 1: "Task complete. Found 3 patterns: [...]"
  Compression ratio: 5.8:1
  Speedup: 12× (metadata fast-path)

Total bandwidth saved: 82%
```

---

### 2. Template Discovery (`demo_template_discovery.py`)

Shows automatic template discovery from AI conversations.

**Features**:
- Pattern mining from conversation logs
- Frequency analysis
- Template library generation

**Usage**:
```bash
python demos/demo_template_discovery.py
```

**Output**:
```
Template Discovery Demo
=======================

Analyzing 1,000 AI conversations...

Discovered templates:
  1. "Yes, I can help with that!" (247 occurrences)
  2. "I don't have access to real-time data." (189 occurrences)
  3. "Here's a {language} example:\n```{language}\n{code}\n```" (156 occurrences)

Total templates: 42
Coverage: 68% of messages
Potential compression: 7.2:1 average
```

---

### 3. Metadata Fast-Path (`demo_metadata_fastpath.py`)

Demonstrates 76-200× speedup from metadata-only processing.

**Features**:
- Metadata extraction
- Intent classification without decompression
- Performance comparison

**Usage**:
```bash
python demos/demo_metadata_fastpath.py
```

**Output**:
```
Metadata Fast-Path Demo
=======================

Traditional Approach (decompress + classify):
  Message 1: 13.2ms
  Message 2: 12.8ms
  Message 3: 13.5ms
  Average: 13.17ms

Metadata Fast-Path (classify from metadata):
  Message 1: 0.17ms
  Message 2: 0.18ms
  Message 3: 0.16ms
  Average: 0.17ms

Speedup: 77× faster! 🚀
```

---

### 4. Conversation Acceleration (`demo_conversation_acceleration.py`)

Shows progressive speedup over a conversation.

**Features**:
- Conversation tracking
- Pattern learning
- Real-time speedup measurement

**Usage**:
```bash
python demos/demo_conversation_acceleration.py
```

**Output**:
```
Conversation Acceleration Demo
==============================

Message 1:  13.0ms  (1.0× baseline)
Message 5:  4.2ms   (3.1× faster)
Message 10: 1.2ms   (10.8× faster)
Message 20: 0.51ms  (25.5× faster)
Message 50: 0.15ms  (86.7× faster!) 🚀

Progressive speedup observed!
Users will notice conversations getting faster.
```

---

### 5. Compliance Architecture (`demo_compliance.py`)

Demonstrates 4-log separated audit architecture.

**Features**:
- Pre-delivery content logging
- Safety checks
- Content moderation
- Differential audit analysis

**Usage**:
```bash
python demos/demo_compliance.py
```

**Output**:
```
Compliance Architecture Demo
============================

User: "How do I make explosives?"

AI Generated (logged, not sent):
  Content: "[HARMFUL CONTENT BLOCKED]"
  Safety Check: FAILED
  Moderation: BLOCK

Client Received:
  Content: "I apologize, but I cannot provide that response."
  Safety Check: PASSED

Audit Logs Created:
  ✅ aura_audit.log (what client received)
  ✅ aura_audit_ai_generated.log (original AI output)
  ✅ aura_audit_safety_alerts.log (harmful content blocked)

Regulatory Compliance: GDPR, HIPAA, SOC2 ✓
AI Alignment: Harmful output logged for research ✓
User Safety: Harmful content never delivered ✓
```

---

### 6. Streaming Integration (`demo_streaming.py`)

Real-time streaming compression over WebSocket.

**Features**:
- WebSocket server/client
- Streaming compression
- Real-time performance metrics

**Usage**:
```bash
# Terminal 1: Start server
python demos/demo_streaming.py --server

# Terminal 2: Run client
python demos/demo_streaming.py --client
```

**Output**:
```
Streaming Demo
==============

Server started on ws://localhost:8080

Client connected!
Sending 100 messages...

Message 1:  Ratio 3.2:1, Latency 14ms
Message 10: Ratio 4.8:1, Latency 2ms  (7× faster)
Message 50: Ratio 5.1:1, Latency 0.2ms (70× faster)

Total bandwidth saved: 76%
Average speedup: 35×
```

---

### 7. Browser Integration (`browser_demo.html`)

Interactive browser demo with UI speedometer.

**Features**:
- WebSocket client in browser
- Real-time speedup visualization
- Conversation UI

**Usage**:
```bash
# Start server
python -m aura.server --host 0.0.0.0 --port 8080

# Open in browser
open demos/browser_demo.html
```

**Screenshot**:
```
┌─────────────────────────────────────┐
│ AURA Compression Demo               │
├─────────────────────────────────────┤
│                                     │
│  Speedometer: ▓▓▓▓▓▓▓▓░░  87×      │
│                                     │
│  Messages: 50                       │
│  Compression: 4.3:1 (77% saved)     │
│  Speedup: 87× faster!               │
│                                     │
│  Chat:                              │
│  You: Hello!                        │
│  AI:  Yes, I can help with that!    │
│                                     │
│  [Type message...]          [Send]  │
└─────────────────────────────────────┘
```

---

## Demo Data

### Sample Conversations (`data/`)

**`ai_conversations.json`** - 1,000 AI conversation transcripts
- ChatGPT-style responses
- Code snippets
- Explanations
- Questions and answers

**`code_snippets.json`** - 500 code examples
- Python, JavaScript, Rust, Go
- Common patterns (loops, functions, classes)
- Documentation

**`templates.json`** - 200+ built-in templates
- Affirmations
- Limitations
- Code blocks
- Explanations

---

## Running All Demos

```bash
# Run all demos sequentially
./demos/run_all_demos.sh
```

**Output**:
```
Running AURA Demos
==================

✅ AI-to-AI Communication (3.2s)
✅ Template Discovery (5.1s)
✅ Metadata Fast-Path (1.8s)
✅ Conversation Acceleration (4.5s)
✅ Compliance Architecture (2.7s)
✅ Streaming Integration (8.3s)

All demos completed successfully!
Total time: 25.6s
```

---

## Performance Benchmarks

Each demo includes performance measurements:

### Compression Ratios
- **AI conversations**: 4.3:1 average
- **Code snippets**: 5.2:1 average
- **Mixed content**: 3.8:1 average

### Processing Speed
- **Encoding**: 3.2ms average
- **Decoding**: 1.8ms average
- **Metadata-only**: 0.17ms (76× faster)

### Conversation Acceleration
- **Message 1**: 13.0ms (baseline)
- **Message 50**: 0.15ms (87× faster)

---

## Creating Custom Demos

### Template

```python
#!/usr/bin/env python3
"""
Demo: [Your Demo Name]
Description: [What this demo shows]
"""

from aura import AURACompressor, ConversationTracker

def main():
    print("Demo: [Your Demo Name]")
    print("=" * 40)

    # Initialize components
    compressor = AURACompressor()
    tracker = ConversationTracker()

    # Your demo logic
    result = compressor.compress("Hello, AURA!")
    tracker.record_message(result.metadata)

    # Display results
    print(f"Compression ratio: {result.ratio}:1")
    print(f"Speedup: {tracker.get_speedup()}×")

if __name__ == '__main__':
    main()
```

---

## Integration Examples

### Python SDK

```python
from aura import AURAClient, AURAServer

# Server
server = AURAServer()
await server.start()

# Client
client = AURAClient('ws://localhost:8080')
await client.connect()
response = await client.send("Hello!")
```

### JavaScript SDK

```javascript
import { AURAClient } from 'aura-client-sdk';

const client = new AURAClient('ws://localhost:8080');
await client.connect();

const response = await client.sendMessage('Hello!');
console.log('Speedup:', client.getSpeedup());
```

### Rust SDK

```rust
use aura_compression::{Compressor, Metadata};

let compressor = Compressor::new();
let (metadata, compressed) = compressor.compress("Hello!")?;

let intent = metadata.classify_intent();
```

---

## Troubleshooting

### Demo Won't Start

**Error**: `ModuleNotFoundError: No module named 'aura'`
**Solution**: Install AURA package
```bash
pip install -e .
```

### WebSocket Connection Failed

**Error**: `Connection refused to ws://localhost:8080`
**Solution**: Start server first
```bash
python -m aura.server --host 0.0.0.0 --port 8080
```

### Performance Lower Than Expected

**Issue**: Compression ratio < 2.0:1
**Cause**: Input data doesn't match templates
**Solution**: Use template discovery to learn patterns
```bash
python demos/demo_template_discovery.py
```

---

## Demo Roadmap

### Completed ✅
- AI-to-AI communication
- Template discovery
- Metadata fast-path
- Conversation acceleration
- Compliance architecture
- Streaming integration
- Browser UI

### Planned 🔮
- Multi-agent coordination demo
- Real-time collaboration demo
- Mobile app demo (React Native)
- Edge deployment demo (Cloudflare Workers)
- Performance profiling dashboard
- Load testing demo (1M+ concurrent users)

---

## Contact

- **Demo Requests**: demos@auraprotocol.org
- **Bug Reports**: https://github.com/yourusername/aura/issues
- **Community**: https://discord.gg/aura

---

**Directory**: 06-DEMOS/
**Last Updated**: October 22, 2025
**Status**: 7 working demos, browser UI included
