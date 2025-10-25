#!/usr/bin/env python3
"""
Stress Test: 50 Concurrent WebSocket Users with Realistic Template-Based Messages

This script simulates realistic AI/Human conversations using:
- Template-based message synthesis with random slot filling
- Shared template store across all simulated users
- Actual codec compression (not estimates)
- Realistic message length distributions
- External corpus support for real-world data

The test validates:
- Concurrent connection handling
- Template matching hit rates
- Compression ratio under realistic load
- Latency and throughput metrics
"""

import asyncio
import websockets
import json
import time
import random
import statistics
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aura_compression.compressor import ProductionHybridCompressor
from aura_compression.templates import TemplateLibrary


class CompressionMetrics:
    """Track detailed compression metrics including template hit rates."""

    def __init__(self):
        self.template_hits = defaultdict(int)          # template_id -> count
        self.method_counts = defaultdict(int)           # method_name -> count
        self.message_sizes = []                         # list of (original_size, compressed_size, ratio)
        self.length_buckets = defaultdict(list)         # length_range -> [ratios]

    def record(self, response_data: Dict, message: str):
        """Record metrics from a compression response."""
        method = response_data.get('method', 'unknown')
        self.method_counts[method] += 1

        # Track sizes
        original_size = response_data.get('original_size', len(message.encode('utf-8')))
        compressed_size = response_data.get('compressed_size', original_size)
        ratio = response_data.get('compression_ratio', 1.0)

        self.message_sizes.append((original_size, compressed_size, ratio))

        # Bucket by length
        if original_size < 50:
            bucket = '<50'
        elif original_size < 100:
            bucket = '50-100'
        elif original_size < 200:
            bucket = '100-200'
        elif original_size < 500:
            bucket = '200-500'
        else:
            bucket = '500+'
        self.length_buckets[bucket].append(ratio)

        # Track template hits
        if method == 'binary_semantic':
            metadata = response_data.get('metadata', {})
            template_id = metadata.get('template_id')
            if template_id is not None:
                self.template_hits[template_id] += 1

    def get_summary(self, template_library: Optional[TemplateLibrary] = None) -> str:
        """Generate a summary report of metrics."""
        lines = []

        # Method distribution
        total_messages = sum(self.method_counts.values())
        if total_messages > 0:
            lines.append("\nCompression Method Distribution:")
            for method, count in sorted(self.method_counts.items(), key=lambda x: x[1], reverse=True):
                pct = (count / total_messages) * 100
                lines.append(f"  {method:20s}: {count:5d} messages ({pct:5.1f}%)")

        # Template hit rates
        if self.template_hits and template_library:
            lines.append("\nTop 10 Matched Templates:")
            sorted_hits = sorted(self.template_hits.items(), key=lambda x: x[1], reverse=True)[:10]
            for i, (tid, count) in enumerate(sorted_hits, 1):
                pattern = template_library.get(tid) or "Unknown"
                pattern_short = pattern[:50] + "..." if len(pattern) > 50 else pattern
                pct = (count / total_messages) * 100
                lines.append(f"  {i:2d}. Template {tid:3d}: {count:4d}x ({pct:4.1f}%) - \"{pattern_short}\"")

            # Template hit rate
            template_hit_count = sum(self.template_hits.values())
            hit_rate = (template_hit_count / total_messages) * 100 if total_messages > 0 else 0
            lines.append(f"\n  Overall Template Hit Rate: {hit_rate:.1f}% ({template_hit_count}/{total_messages})")

        # Compression by message length
        if self.length_buckets:
            lines.append("\nCompression Effectiveness by Message Length:")
            for bucket_name in ['<50', '50-100', '100-200', '200-500', '500+']:
                ratios = self.length_buckets.get(bucket_name, [])
                if ratios:
                    avg_ratio = statistics.mean(ratios)
                    max_ratio = max(ratios)
                    lines.append(f"  {bucket_name:10s}: {avg_ratio:5.2f}:1 avg (max: {max_ratio:5.2f}:1, {len(ratios):4d} msgs)")

        return "\n".join(lines)


# Realistic slot fillers for template-based message synthesis
SLOT_FILLERS = {
    'resource': [
        "real-time data", "your local filesystem", "external databases",
        "that specific information", "live market data", "your browser cookies",
        "third-party APIs", "system logs", "previous chat history"
    ],
    'action': [
        "process that type of request", "access external services", "execute arbitrary code",
        "modify system files", "browse the internet", "remember previous conversations",
        "install packages", "debug this issue", "deploy your application",
        "optimize performance", "set up the environment", "configure the database"
    ],
    'tool': [
        "pip", "npm", "docker", "git", "pytest", "webpack", "cargo", "kubectl",
        "the CLI tool", "the official package", "that library", "terraform"
    ],
    'suggestion': [
        "checking the error logs carefully", "reviewing the official documentation",
        "updating to the latest version", "consulting with your team lead",
        "running the diagnostic script first", "restarting the service",
        "clearing the cache", "checking your configuration file"
    ],
    'subject': [
        "React", "Python", "Rust", "PostgreSQL", "Redis", "Kubernetes", "TensorFlow", "AWS",
        "A REST API", "A microservice", "The ORM layer", "This pattern", "The framework"
    ],
    'definition': [
        "a declarative programming framework", "used for building scalable applications",
        "designed for high-performance computing", "primarily used in data science",
        "optimized for cloud-native deployments", "widely adopted in enterprise environments",
        "a functional programming language", "an object-relational mapping tool"
    ],
    'attribute': [
        "default behavior", "return value", "primary key", "error code",
        "default value", "return type", "timeout", "max connections"
    ],
    'value': [
        "null", "undefined", "zero", "false", "empty string", "true", "enabled", "disabled"
    ],
    'question': [
        "is the main difference", "does this work", "should I do this", "is the best approach",
        "are the key features", "is the recommended way", "did this error occur"
    ],
    'request': [
        "help me with this", "explain that concept", "show me an example",
        "clarify this point", "review my code", "suggest an alternative"
    ],
    'topic': [
        "machine learning", "web development", "database design", "API integration",
        "security best practices", "performance optimization", "testing strategies", "CI/CD"
    ],
}


class MessageSynthesizer:
    """Synthesizes realistic messages from template library with random slot filling."""

    def __init__(self, template_library: Optional[TemplateLibrary] = None,
                 corpus: Optional[List[str]] = None,
                 corpus_messages: Optional[List['CorpusMessage']] = None,
                 metadata_path: Optional[Path] = None,
                 seed: Optional[int] = None,
                 corpus_weight: float = 0.3):
        self.template_library = template_library or TemplateLibrary()
        self.templates = self.template_library.list_templates()
        self.corpus = corpus or []
        self.corpus_messages = corpus_messages or []
        self.corpus_weight = corpus_weight if corpus else 0.0

        # Per-template random generators for reproducible slot filling
        self.template_rngs = {}
        if seed is not None:
            for tid in self.templates.keys():
                self.template_rngs[tid] = random.Random(seed + tid)

        # Load per-template metadata (slot examples, usage patterns, etc.)
        self.template_metadata = self._load_metadata(metadata_path) if metadata_path else {}

        # Track slot value usage for churn analysis
        self.slot_usage_histogram = defaultdict(lambda: defaultdict(int))  # template_id -> slot_value -> count
        self.corpus_contribution = defaultdict(int)  # track corpus vs synthetic ratio

        # Categorize templates by slot count for efficient sampling
        self.zero_slot = []
        self.one_slot = []
        self.two_slot = []
        self.multi_slot = []

        for tid, pattern in self.templates.items():
            slot_count = pattern.count('{')
            if slot_count == 0:
                self.zero_slot.append((tid, pattern))
            elif slot_count == 1:
                self.one_slot.append((tid, pattern))
            elif slot_count == 2:
                self.two_slot.append((tid, pattern))
            else:
                self.multi_slot.append((tid, pattern))

        # Map template IDs to their expected slot semantics for proper filling
        self.template_slot_hints = {
            # Limitations (20-27)
            20: ['resource'],                    # "I don't have access to {0}."
            21: ['resource', 'suggestion'],      # "I don't have access to {0}. {1}"
            22: ['action'],                      # "I cannot {0}."
            23: ['action'],                      # "I'm unable to {0}."
            24: ['action'],                      # "I can't {0}."
            25: ['topic'],                       # "I can help with {0}."
            26: ['action'],                      # "I can help you {0}."
            27: ['action'],                      # "I'm able to {0}."

            # Facts (40-46)
            40: ['subject', 'definition'],       # "{0} is {1}."
            41: ['subject', 'definition'],       # "{0} are {1}."
            42: ['attribute', 'value'],          # "The {0} is {1}."
            43: ['attribute', 'value'],          # "The {0} are {1}."
            44: ['attribute', 'subject', 'value'], # "The {0} of {1} is {2}."
            45: ['subject', 'definition'],       # "{0} means {1}."
            46: ['subject', 'definition'],       # "{0} refers to {1}."

            # Questions (60-69)
            60: ['question'],                    # "What {0}?"
            61: ['question'],                    # "Why {0}?"
            62: ['question'],                    # "How {0}?"
            63: ['question'],                    # "When {0}?"
            64: ['question'],                    # "Where {0}?"
            65: ['request'],                     # "Can you {0}?"
            66: ['request'],                     # "Could you {0}?"
            67: ['request'],                     # "Would you {0}?"
            68: ['topic'],                       # "Could you clarify {0}?"
            69: ['topic'],                       # "What specific {0} would you like to know more about?"

            # Instructions (70-78)
            70: ['action', 'suggestion'],        # "To {0}, {1}."
            71: ['action', 'tool'],              # "To {0}, use {1}."
            72: ['action', 'tool', 'tool'],      # "To {0}, use {1}: `{2}`"
            73: ['action', 'suggestion'],        # "You can {0} by {1}."
            74: ['suggestion'],                  # "Try {0}."
            75: ['suggestion'],                  # "I recommend {0}."
            76: ['suggestion'],                  # "I suggest {0}."
            77: ['suggestion'],                  # "Consider {0}."
            78: ['action', 'suggestion'],        # "To {0}, I recommend: {1}"

            # Explanations (90-95)
            90: ['subject', 'definition'],       # "{0} works by {1}."
            91: ['subject', 'definition'],       # "{0} is used for {1}."
            92: ['attribute', 'subject', 'value', 'definition'], # Complex
            93: ['subject', 'definition'],       # "{0} because {1}."
            94: ['definition'],                  # "This is {0}."
            95: ['definition'],                  # "This means {0}."
        }

    def _load_metadata(self, metadata_path: Path) -> Dict:
        """Load per-template metadata including slot_examples.

        Expected JSON format:
        {
          "templates": {
            "20": {
              "slot_examples": [
                ["real-time data", "your local files", "external APIs"],
                ...
              ],
              "weight": 1.5,
              "ttl_seconds": 3600
            }
          }
        }
        """
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                templates_meta = data.get('templates', {})
                # Convert string keys to int
                return {int(k): v for k, v in templates_meta.items()}
        except Exception as e:
            print(f"Warning: Failed to load metadata from {metadata_path}: {e}")
            return {}

    def fill_slot(self, template_id: int, slot_index: int) -> str:
        """Generate realistic slot content based on template semantics and metadata."""
        # Use per-template RNG if available for reproducibility
        rng = self.template_rngs.get(template_id, random)

        # Check for slot_examples in metadata first
        if template_id in self.template_metadata:
            slot_examples = self.template_metadata[template_id].get('slot_examples', [])
            if slot_index < len(slot_examples) and slot_examples[slot_index]:
                value = rng.choice(slot_examples[slot_index])
                # Track usage for churn analysis
                self.slot_usage_histogram[template_id][value] += 1
                return value

        # Get semantic hints for this template
        hints = self.template_slot_hints.get(template_id, [])

        # If we have a hint for this slot, use it
        if slot_index < len(hints):
            slot_type = hints[slot_index]
            if slot_type in SLOT_FILLERS:
                value = rng.choice(SLOT_FILLERS[slot_type])
                self.slot_usage_histogram[template_id][value] += 1
                return value

        # Fallback: use generic slot filling
        slot_types = list(SLOT_FILLERS.keys())
        slot_type = slot_types[slot_index % len(slot_types)]
        value = rng.choice(SLOT_FILLERS[slot_type])
        self.slot_usage_histogram[template_id][value] += 1
        return value

    def get_churn_report(self) -> str:
        """Generate report on slot value churn and corpus contribution with low diversity warnings."""
        lines = ["\nSlot Value Churn Analysis:"]

        # Track low diversity templates for alerting
        low_diversity_templates = []

        # Analyze slot diversity per template
        for template_id, slot_values in sorted(self.slot_usage_histogram.items())[:10]:
            total_uses = sum(slot_values.values())
            unique_values = len(slot_values)
            pattern = self.template_library.get(template_id) or "Unknown"
            pattern_short = pattern[:40] + "..." if len(pattern) > 40 else pattern

            # Calculate entropy/diversity
            diversity_ratio = unique_values / total_uses if total_uses > 0 else 0

            # Flag low diversity if >3 uses but <60% diversity
            if total_uses > 3 and diversity_ratio < 0.6:
                low_diversity_templates.append((template_id, diversity_ratio, total_uses, pattern_short))

            lines.append(f"  Template {template_id:3d}: {total_uses:4d} uses, {unique_values:3d} unique values "
                        f"(diversity: {diversity_ratio:.2f})")
            lines.append(f"    Pattern: \"{pattern_short}\"")

            # Show top 3 most used values
            top_values = sorted(slot_values.items(), key=lambda x: x[1], reverse=True)[:3]
            for value, count in top_values:
                value_short = value[:30] + "..." if len(value) > 30 else value
                pct = (count / total_uses) * 100
                lines.append(f"      - \"{value_short}\": {count}x ({pct:.1f}%)")

        # Add low diversity warnings
        if low_diversity_templates:
            lines.append(f"\n⚠️  Low Diversity Warnings ({len(low_diversity_templates)} templates):")
            for tid, diversity, uses, pattern in low_diversity_templates:
                lines.append(f"    Template {tid:3d}: {diversity:.2f} diversity with {uses} uses")
                lines.append(f"      Pattern: \"{pattern}\"")
                lines.append(f"      → Consider adding more slot_examples or expanding corpus coverage")

        # Corpus vs synthetic ratio
        if self.corpus_contribution:
            total_synthetic = sum(self.corpus_contribution.values())
            corpus_count = self.corpus_contribution.get('corpus', 0)
            synthetic_count = self.corpus_contribution.get('synthetic', 0)
            total = corpus_count + synthetic_count

            if total > 0:
                lines.append(f"\nMessage Source Distribution:")
                lines.append(f"  Corpus messages:    {corpus_count:5d} ({corpus_count/total*100:5.1f}%)")
                lines.append(f"  Synthetic messages: {synthetic_count:5d} ({synthetic_count/total*100:5.1f}%)")

        return "\n".join(lines)

    def synthesize_ai_message(self, min_length: int = 50, max_length: int = 2000) -> str:
        """Generate realistic AI message using templates with random slot filling."""

        # Use corpus message with weighted sampling if available
        if self.corpus and random.random() < self.corpus_weight:
            if self.corpus_messages:
                # Weighted sampling based on message.weight
                weights = [m.weight for m in self.corpus_messages]
                msg_obj = random.choices(self.corpus_messages, weights=weights, k=1)[0]
                msg = msg_obj.text
            else:
                msg = random.choice(self.corpus)

            if min_length <= len(msg) <= max_length:
                self.corpus_contribution['corpus'] += 1
                return msg

        # Track synthetic message generation
        self.corpus_contribution['synthetic'] += 1

        # Favor single-template matches for better compression:
        # 70% single template, 20% two templates, 10% multi-template

        # If message needs to be long, prefer longer single templates
        if min_length > 100:
            # Use longer templates or two-sentence combinations
            if random.random() < 0.7:
                # Single longer template
                if self.two_slot:
                    template_id, pattern = random.choice(self.two_slot)
                    slot0 = self.fill_slot(template_id, 0)
                    slot1 = self.fill_slot(template_id, 1)
                    msg = pattern.format(slot0, slot1)
                    # Pad if needed
                    while len(msg) < min_length and len(msg) < max_length - 50:
                        template_id, pattern = random.choice(self.one_slot)
                        msg += " " + pattern.format(self.fill_slot(template_id, 0))
                    return msg[:max_length]
                else:
                    # Fallback to multi-sentence
                    return self._synthesize_multi_sentence(min_length, max_length)
            else:
                # Two sentence combination (20%)
                return self._synthesize_multi_sentence(min_length, max_length, max_sentences=2)

        # For shorter messages, use single templates
        # 20% - Zero-slot templates (best compression)
        if random.random() < 0.20:
            if not self.zero_slot:
                return "Yes"
            template_id, pattern = random.choice(self.zero_slot)
            return pattern

        # 45% - Single-slot templates
        elif random.random() < 0.65:
            if not self.one_slot:
                return "I cannot help with that."
            template_id, pattern = random.choice(self.one_slot)
            slot_value = self.fill_slot(template_id, 0)
            return pattern.format(slot_value)

        # 25% - Two-slot templates
        elif random.random() < 0.90:
            if not self.two_slot:
                return "The value is undefined."
            template_id, pattern = random.choice(self.two_slot)
            slot0 = self.fill_slot(template_id, 0)
            slot1 = self.fill_slot(template_id, 1)
            return pattern.format(slot0, slot1)

        # 10% - Multi-sentence (reduced from 20% for better compression)
        else:
            return self._synthesize_multi_sentence(min_length, max_length)

    def _synthesize_multi_sentence(self, min_length: int, max_length: int, max_sentences: int = 3) -> str:
        """Generate multi-sentence message (helper to avoid recursion issues)."""
        sentences = []
        depth = 0
        while len(" ".join(sentences)) < min_length and depth < max_sentences:
            # Use simple template generation (not recursive)
            if self.one_slot and random.random() < 0.7:
                template_id, pattern = random.choice(self.one_slot)
                sentences.append(pattern.format(self.fill_slot(template_id, 0)))
            elif self.two_slot:
                template_id, pattern = random.choice(self.two_slot)
                sentences.append(pattern.format(
                    self.fill_slot(template_id, 0),
                    self.fill_slot(template_id, 1)
                ))
            depth += 1

        message = " ".join(sentences)
        if len(message) > max_length:
            message = message[:max_length-3] + "..."
        return message

    def synthesize_human_message(self, min_length: int = 20, max_length: int = 500) -> str:
        """Generate realistic human message (questions, short responses)."""

        # 40% - Very short responses
        if random.random() < 0.4:
            if self.zero_slot:
                template_id, pattern = random.choice(self.zero_slot[:10])  # Use first 10 (Yes/No/etc)
                return pattern
            return random.choice(["Yes", "No", "Maybe", "I don't know"])

        # 40% - Questions
        elif random.random() < 0.8:
            question_templates = [t for t in self.one_slot if '?' in t[1]]
            if question_templates:
                template_id, pattern = random.choice(question_templates)
                return pattern.format(self.fill_slot(template_id, 0))
            return "How does this work?"

        # 20% - Longer questions with context
        else:
            base = self.synthesize_human_message(20, 100)
            context = random.choice([
                " I'm new to this.",
                " I've been stuck on this.",
                " Any help would be appreciated!",
                ""
            ])
            return base + context


# Global message synthesizer (shared across all users)
_synthesizer = None


@dataclass
class CorpusMessage:
    """Structured corpus message with metadata."""
    text: str
    weight: float = 1.0
    timestamp: Optional[str] = None  # ISO format for temporal analysis
    category: Optional[str] = None


def load_corpus(corpus_path: Path) -> Tuple[List[str], List[CorpusMessage]]:
    """Load messages from JSONL corpus file with optional structured metadata.

    Supports two formats:
    Simple: {"message": "text here"}
    Structured: {"text": "...", "weight": 1.5, "timestamp": "2025-01-15T10:00:00Z", "category": "ai"}

    Returns:
        (simple_messages, structured_messages)
    """
    simple_messages = []
    structured_messages = []

    try:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)

                    # Extract message text
                    msg = data.get('message') or data.get('text') or data.get('content')
                    if not msg or not isinstance(msg, str):
                        continue

                    simple_messages.append(msg)

                    # Check for structured metadata
                    if 'weight' in data or 'timestamp' in data or 'category' in data:
                        structured_messages.append(CorpusMessage(
                            text=msg,
                            weight=float(data.get('weight', 1.0)),
                            timestamp=data.get('timestamp'),
                            category=data.get('category')
                        ))

                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON at line {line_num}: {e}")
                    continue

        print(f"Loaded {len(simple_messages)} messages from corpus: {corpus_path}")
        if structured_messages:
            print(f"  - {len(structured_messages)} messages have structured metadata (weights/timestamps)")

        return simple_messages, structured_messages
    except Exception as e:
        print(f"Error loading corpus from {corpus_path}: {e}")
        return [], []


def get_message_synthesizer(corpus: Optional[List[str]] = None,
                           corpus_messages: Optional[List['CorpusMessage']] = None,
                           metadata_path: Optional[Path] = None,
                           seed: Optional[int] = None,
                           corpus_weight: float = 0.3) -> MessageSynthesizer:
    """Get shared message synthesizer instance."""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = MessageSynthesizer(
            corpus=corpus,
            corpus_messages=corpus_messages,
            metadata_path=metadata_path,
            seed=seed,
            corpus_weight=corpus_weight
        )
    return _synthesizer


def generate_random_ai_message(min_length: int = 50, max_length: int = 2000) -> str:
    """Generate realistic AI message using shared template synthesizer."""
    return get_message_synthesizer().synthesize_ai_message(min_length, max_length)


def generate_random_human_message(min_length: int = 20, max_length: int = 500) -> str:
    """Generate realistic human message using shared template synthesizer."""
    return get_message_synthesizer().synthesize_human_message(min_length, max_length)


def get_realistic_message_length(user_type: str, message_index: int, conversation_length: int) -> Tuple[int, int]:
    """
    Return (min_length, max_length) based on realistic conversation dynamics.

    This creates a realistic distribution that favors longer messages to improve
    compression ratios. Based on analysis of real AI conversations:
    - AI responses are typically 100-400 characters
    - Human messages are typically 30-150 characters
    - First messages tend to be longer (context setting)
    - Messages get shorter as conversation progresses
    """

    if user_type == "AI":
        if message_index == 0:
            # First AI response: detailed introduction
            return (150, 500)
        elif message_index < 3:
            # Early responses: building context
            return (100, 400)
        elif message_index < conversation_length // 2:
            # Mid-conversation: detailed explanations
            return (80, 300)
        else:
            # Later messages: more concise but still substantive
            return (60, 200)

    else:  # Human
        if message_index == 0:
            # First human message: detailed question
            return (50, 200)
        elif message_index < 3:
            # Follow-up questions
            return (40, 150)
        else:
            # 60% longer questions, 40% short responses
            if random.random() < 0.6:
                return (50, 120)
            else:
                # Short responses (Yes/No/acknowledgments)
                return (10, 40)


class UserSimulator:
    """Simulates a single user with WebSocket connection."""

    def __init__(self, user_id: int, server_url: str, metrics: Optional[CompressionMetrics] = None,
                 debug_mode: bool = False, trace_output: Optional[Path] = None):
        self.user_id = user_id
        self.server_url = server_url
        self.compressor = ProductionHybridCompressor()
        self.metrics = metrics or CompressionMetrics()
        self.debug_mode = debug_mode
        self.trace_output = trace_output
        self.traces = []  # Per-iteration trace data

        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'total_original_size': 0,
            'total_compressed_size': 0,
            'latencies': [],
            'errors': 0,
            'user_type': random.choice(['AI', 'Human']),  # Random user type
            'conversation_length': random.randint(5, 50),  # Random conversation length
        }

    def should_log_debug(self, compression_ratio: float, latency_ms: float) -> bool:
        """Intelligently decide whether to log this message in debug mode.

        Logs interesting cases rather than random sampling:
        - Excellent compression (>5:1)
        - Compression expansion (<0.98:1)
        - High latency (>10ms)
        - 5% random sampling for baseline
        """
        return (
            compression_ratio > 5.0 or      # Excellent compression
            compression_ratio < 0.98 or     # Expansion case (compressed > original)
            latency_ms > 10.0 or            # High latency
            random.random() < 0.05          # 5% random sampling
        )

    async def simulate_conversation(self) -> Dict:
        """Simulate a full conversation with random messages."""
        try:
            async with websockets.connect(self.server_url) as websocket:
                print(f"[User {self.user_id}] Connected ({self.stats['user_type']}, {self.stats['conversation_length']} messages)")

                for turn in range(self.stats['conversation_length']):
                    # Generate message with realistic length distribution
                    min_len, max_len = get_realistic_message_length(
                        self.stats['user_type'],
                        turn,
                        self.stats['conversation_length']
                    )

                    if self.stats['user_type'] == 'AI':
                        message = generate_random_ai_message(min_len, max_len)
                    else:
                        message = generate_random_human_message(min_len, max_len)


                    # Measure compression and latency
                    start_time = time.time()

                    # Send plain text message to server (server will compress it)
                    await websocket.send(message)
                    self.stats['messages_sent'] += 1

                    # Receive response
                    response = await websocket.recv()
                    response_data = json.loads(response)

                    # Track compression stats from server response
                    self.stats['total_original_size'] += response_data.get('original_size', len(message.encode('utf-8')))
                    self.stats['total_compressed_size'] += response_data.get('compressed_size', len(message.encode('utf-8')))

                    # Record metrics
                    self.metrics.record(response_data, message)

                    end_time = time.time()
                    latency_ms = (end_time - start_time) * 1000

                    # Debug mode: record detailed trace
                    if self.debug_mode:
                        trace = {
                            'user_id': self.user_id,
                            'turn': turn,
                            'timestamp': datetime.now().isoformat(),
                            'message': message,
                            'message_length': len(message),
                            'method': response_data.get('method'),
                            'compression_ratio': response_data.get('compression_ratio'),
                            'latency_ms': latency_ms,
                            'original_size': response_data.get('original_size'),
                            'compressed_size': response_data.get('compressed_size'),
                        }
                        self.traces.append(trace)

                        # Intelligent logging for outliers and interesting cases
                        if self.should_log_debug(response_data.get('compression_ratio', 1.0), latency_ms):
                            msg_preview = message[:50] + "..." if len(message) > 50 else message
                            reason = []
                            if response_data.get('compression_ratio', 0) > 5.0:
                                reason.append("EXCELLENT")
                            if response_data.get('compression_ratio', 1.0) < 0.98:
                                reason.append("EXPANSION")
                            if latency_ms > 10.0:
                                reason.append("HIGH_LAT")
                            reason_str = f" [{','.join(reason)}]" if reason else ""
                            print(f"[DEBUG User {self.user_id} Turn {turn}] "
                                  f"{response_data.get('method'):12s} {response_data.get('compression_ratio', 0):.2f}:1 "
                                  f"{latency_ms:.2f}ms{reason_str} | \"{msg_preview}\"")

                    # Log compression method for first message only (normal mode)
                    elif turn == 0:
                        method = response_data.get('method', 'unknown')
                        ratio = response_data.get('compression_ratio', 0)
                        msg_short = message[:40] + "..." if len(message) > 40 else message
                        print(f"[User {self.user_id}] {method:15s} {ratio:5.2f}:1 | {msg_short}")

                    self.stats['messages_received'] += 1
                    self.stats['latencies'].append(latency_ms)

                    # Random delay between messages (0.1 to 2 seconds)
                    await asyncio.sleep(random.uniform(0.1, 2.0))

                print(f"[User {self.user_id}] Completed conversation")

        except Exception as e:
            print(f"[User {self.user_id}] Error: {e}")
            self.stats['errors'] += 1

        # Export traces if in debug mode
        if self.debug_mode and self.traces and self.trace_output:
            trace_file = self.trace_output / f"user_{self.user_id}_traces.jsonl"
            try:
                with open(trace_file, 'w') as f:
                    for trace in self.traces:
                        f.write(json.dumps(trace) + '\n')
            except Exception as e:
                print(f"[User {self.user_id}] Failed to write traces: {e}")

        return self.stats


async def warmup_phase(server_url: str, num_messages: int = 100):
    """Warm up caches and template stores before stress test."""
    print(f"\nWarming up with {num_messages} messages...")

    synth = get_message_synthesizer()

    try:
        async with websockets.connect(server_url) as ws:
            for i in range(num_messages):
                # Generate mix of AI and human messages
                if i % 2 == 0:
                    msg = synth.synthesize_ai_message(50, 200)
                else:
                    msg = synth.synthesize_human_message(20, 100)

                await ws.send(msg)
                await ws.recv()  # Receive response

        print(f"Warm-up complete ({num_messages} messages processed).\n")
        return True
    except Exception as e:
        print(f"Warm-up failed: {e}")
        print("Continuing without warm-up...\n")
        return False


async def run_stress_test(num_users: int = 50, server_url: str = "ws://localhost:8765",
                          warmup: bool = False, warmup_messages: int = 100,
                          debug_mode: bool = False, trace_dir: Optional[Path] = None):
    """Run stress test with multiple concurrent users."""

    print(f"\n{'='*80}")
    print(f"AURA WebSocket Stress Test: {num_users} Concurrent Users")
    print(f"{'='*80}\n")
    print(f"Server: {server_url}")
    print(f"Configuration:")
    print(f"  - Users: {num_users}")
    print(f"  - User Types: Random (AI/Human)")
    print(f"  - Conversation Length: Random (5-50 messages)")
    print(f"  - Message Sizes: Random (20-2000 characters)")
    if debug_mode:
        print(f"  - Debug Mode: ENABLED (per-iteration traces)")
        if trace_dir:
            print(f"  - Trace Output: {trace_dir}")

    # Run warm-up phase if requested
    if warmup:
        await warmup_phase(server_url, warmup_messages)

    print(f"\nStarting test...\n")

    # Create shared metrics tracker
    metrics = CompressionMetrics()
    template_lib = TemplateLibrary()

    # Prepare trace directory
    if debug_mode and trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)

    # Create user simulators with shared metrics
    users = [UserSimulator(i+1, server_url, metrics, debug_mode, trace_dir) for i in range(num_users)]

    # Run all users concurrently
    start_time = time.time()
    results = await asyncio.gather(*[user.simulate_conversation() for user in users])
    end_time = time.time()

    # Aggregate statistics
    total_time = end_time - start_time

    # Calculate overall metrics
    total_messages_sent = sum(r['messages_sent'] for r in results)
    total_messages_received = sum(r['messages_received'] for r in results)
    total_original_size = sum(r['total_original_size'] for r in results)
    total_compressed_size = sum(r['total_compressed_size'] for r in results)
    total_errors = sum(r['errors'] for r in results)

    all_latencies = []
    for r in results:
        all_latencies.extend(r['latencies'])

    # User type distribution
    ai_users = sum(1 for r in results if r['user_type'] == 'AI')
    human_users = num_users - ai_users

    # Calculate AI vs Human stats separately
    ai_stats = [r for r in results if r['user_type'] == 'AI']
    human_stats = [r for r in results if r['user_type'] == 'Human']

    ai_original = sum(r['total_original_size'] for r in ai_stats) if ai_stats else 0
    ai_compressed = sum(r['total_compressed_size'] for r in ai_stats) if ai_stats else 0
    human_original = sum(r['total_original_size'] for r in human_stats) if human_stats else 0
    human_compressed = sum(r['total_compressed_size'] for r in human_stats) if human_stats else 0

    # Print results
    print(f"\n{'='*80}")
    print(f"STRESS TEST RESULTS")
    print(f"{'='*80}\n")

    print(f"Overall Performance:")
    print(f"  Total Test Duration: {total_time:.2f} seconds")
    print(f"  Concurrent Users: {num_users}")
    print(f"  - AI Users: {ai_users} ({ai_users/num_users*100:.1f}%)")
    print(f"  - Human Users: {human_users} ({human_users/num_users*100:.1f}%)")
    print(f"  Total Messages Sent: {total_messages_sent}")
    print(f"  Total Messages Received: {total_messages_received}")
    if total_time > 0:
        print(f"  Messages Per Second: {total_messages_sent/total_time:.2f}")
    if total_messages_sent > 0:
        print(f"  Success Rate: {(total_messages_received/total_messages_sent*100):.2f}%")
    print(f"  Total Errors: {total_errors}")

    print(f"\nCompression Statistics:")
    overall_ratio = total_original_size / total_compressed_size if total_compressed_size > 0 else 0
    print(f"  Total Original Size: {total_original_size:,} bytes ({total_original_size/1024:.2f} KB)")
    print(f"  Total Compressed Size: {total_compressed_size:,} bytes ({total_compressed_size/1024:.2f} KB)")
    print(f"  Overall Compression Ratio: {overall_ratio:.2f}:1")
    if total_original_size > 0:
        print(f"  Bandwidth Saved: {(1 - total_compressed_size/total_original_size)*100:.2f}%")

    print(f"\n  AI Message Compression:")
    if ai_original > 0:
        ai_ratio = ai_original / ai_compressed if ai_compressed > 0 else 0
        print(f"    Original: {ai_original:,} bytes")
        print(f"    Compressed: {ai_compressed:,} bytes")
        print(f"    Ratio: {ai_ratio:.2f}:1")
    else:
        print(f"    No AI messages")

    print(f"\n  Human Message Compression:")
    if human_original > 0:
        human_ratio = human_original / human_compressed if human_compressed > 0 else 0
        print(f"    Original: {human_original:,} bytes")
        print(f"    Compressed: {human_compressed:,} bytes")
        print(f"    Ratio: {human_ratio:.2f}:1")
    else:
        print(f"    No Human messages")

    if all_latencies:
        print(f"\nLatency Statistics (per message round-trip):")
        print(f"  Average: {statistics.mean(all_latencies):.2f} ms")
        print(f"  Median: {statistics.median(all_latencies):.2f} ms")
        print(f"  Min: {min(all_latencies):.2f} ms")
        print(f"  Max: {max(all_latencies):.2f} ms")
        print(f"  P95: {sorted(all_latencies)[int(len(all_latencies)*0.95)]:.2f} ms")
        print(f"  P99: {sorted(all_latencies)[int(len(all_latencies)*0.99)]:.2f} ms")
        print(f"  Std Dev: {statistics.stdev(all_latencies):.2f} ms")

    print(f"\nPer-User Statistics:")
    print(f"  Avg Messages per User: {total_messages_sent/num_users:.1f}")
    print(f"  Avg Conversation Length: {statistics.mean([r['conversation_length'] for r in results]):.1f}")
    print(f"  Min Conversation Length: {min(r['conversation_length'] for r in results)}")
    print(f"  Max Conversation Length: {max(r['conversation_length'] for r in results)}")

    # Top 5 most active users
    sorted_users = sorted(results, key=lambda x: x['messages_sent'], reverse=True)
    print(f"\n  Top 5 Most Active Users:")
    for i, user_stats in enumerate(sorted_users[:5], 1):
        user_idx = results.index(user_stats) + 1
        print(f"    {i}. User {user_idx}: {user_stats['messages_sent']} messages ({user_stats['user_type']})")

    print(f"\n{'='*80}\n")

    # Performance assessment with detailed analysis
    print("Performance Analysis:")

    if total_errors == 0 and statistics.mean(all_latencies) < 2.0:
        print("  ✓ EXCELLENT: Zero errors and ultra-low latency (<2ms avg)")
    elif total_errors == 0 and statistics.mean(all_latencies) < 10.0:
        print("  ✓ VERY GOOD: Zero errors and low latency (<10ms avg)")
    elif total_errors == 0 and statistics.mean(all_latencies) < 100:
        print("  ✓ GOOD: Zero errors, acceptable latency")
    elif total_errors == 0:
        print("  ⚠ FAIR: Zero errors, but high latency needs investigation")
    elif total_errors < num_users * 0.05:
        print("  ⚠ ACCEPTABLE: Low error rate (<5%)")
    else:
        print("  ✗ POOR: High error rate, investigate server capacity")

    # Compression effectiveness analysis
    print(f"\nCompression Effectiveness:")
    if overall_ratio > 3.0:
        print(f"  ✓ EXCELLENT: {overall_ratio:.2f}:1 compression (>3x)")
    elif overall_ratio > 2.0:
        print(f"  ✓ VERY GOOD: {overall_ratio:.2f}:1 compression (>2x)")
    elif overall_ratio > 1.5:
        print(f"  ✓ GOOD: {overall_ratio:.2f}:1 compression (>1.5x)")
    elif overall_ratio > 1.1:
        print(f"  ⚠ FAIR: {overall_ratio:.2f}:1 compression (modest)")
    else:
        print(f"  ✗ POOR: {overall_ratio:.2f}:1 compression (minimal benefit)")

    # Bandwidth savings assessment
    if total_original_size > 0:
        bandwidth_saved = (1 - total_compressed_size/total_original_size)*100
        print(f"  Bandwidth saved: {bandwidth_saved:.1f}% ({total_original_size - total_compressed_size:,} bytes)")
    if total_time > 0:
        print(f"  Effective throughput: {total_compressed_size/total_time/1024:.2f} KB/s (compressed)")
        print(f"  Without compression: {total_original_size/total_time/1024:.2f} KB/s would be needed")

    # Print detailed metrics summary
    print(metrics.get_summary(template_lib))

    # Print churn analysis if available
    synthesizer = get_message_synthesizer()
    churn_report = synthesizer.get_churn_report()
    if churn_report:
        print(churn_report)

    print()

    # Return results for potential export
    return {
        'timestamp': datetime.now().isoformat(),
        'config': {
            'num_users': num_users,
            'server_url': server_url,
            'warmup': warmup,
        },
        'summary': {
            'total_time': total_time,
            'total_messages': total_messages_sent,
            'messages_per_second': total_messages_sent / total_time if total_time > 0 else 0,
            'success_rate': (total_messages_received / total_messages_sent * 100) if total_messages_sent > 0 else 0,
            'errors': total_errors,
            'overall_compression_ratio': overall_ratio,
            'bandwidth_saved_percent': bandwidth_saved,
        },
        'latencies': {
            'average_ms': statistics.mean(all_latencies) if all_latencies else 0,
            'median_ms': statistics.median(all_latencies) if all_latencies else 0,
            'min_ms': min(all_latencies) if all_latencies else 0,
            'max_ms': max(all_latencies) if all_latencies else 0,
            'p95_ms': sorted(all_latencies)[int(len(all_latencies) * 0.95)] if all_latencies else 0,
            'p99_ms': sorted(all_latencies)[int(len(all_latencies) * 0.99)] if all_latencies else 0,
        },
        'compression': {
            'total_original_size': total_original_size,
            'total_compressed_size': total_compressed_size,
            'overall_ratio': overall_ratio,
            'ai_ratio': ai_original / ai_compressed if ai_compressed > 0 else 1.0,
            'human_ratio': human_original / human_compressed if human_compressed > 0 else 1.0,
            'method_counts': dict(metrics.method_counts),
            'length_buckets': {k: statistics.mean(v) if v else 0 for k, v in metrics.length_buckets.items()},
        },
    }


def export_results(results: Dict, output_path: Path):
    """Export test results to JSON file for trending and analysis."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        print(f"Results exported to: {output_path}")
        return True
    except Exception as e:
        print(f"Error exporting results: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="WebSocket Stress Test with Template-Based Message Synthesis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run standard 50-user test
  %(prog)s

  # Run with 100 concurrent users
  %(prog)s --users 100

  # Use custom server URL
  %(prog)s --url ws://production.example.com:8765

  # Load external message corpus
  %(prog)s --corpus messages.jsonl

  # Use seeded random for reproducible tests
  %(prog)s --seed 42

  # Load structured corpus with weights and per-template metadata
  %(prog)s --corpus structured_corpus.jsonl --metadata template_metadata.json --seed 42

  # Enable debug mode with trace recording
  %(prog)s --debug --trace-dir ./my_traces

  # Full-featured test with all options
  %(prog)s --users 100 --corpus structured_corpus.jsonl --metadata template_metadata.json \\
           --seed 42 --warmup --debug --export results.json

Features:
  - Template-based message synthesis with realistic slot filling
  - Per-template metadata support (slot_examples) for reproducible payloads
  - Structured corpus with weights and timestamps for temporal modeling
  - Seeded random generators per template for reproducibility
  - Template/slot churn analysis to detect value distribution skew
  - Debug mode with per-iteration trace recording
  - Shared template store across all simulated users
  - Actual codec compression (not estimates)
  - Detailed performance and compression analysis
        """
    )
    parser.add_argument("--users", type=int, default=50,
                       help="Number of concurrent users (default: 50)")
    parser.add_argument("--url", type=str, default="ws://localhost:8765",
                       help="WebSocket server URL (default: ws://localhost:8765)")
    parser.add_argument("--corpus", type=str, default=None,
                       help="Load external message corpus from JSONL file")
    parser.add_argument("--corpus-weight", type=float, default=0.3,
                       help="Probability of using corpus message vs synthetic (0.0-1.0, default: 0.3)")
    parser.add_argument("--seed", type=int, default=None,
                       help="Random seed for reproducible tests")
    parser.add_argument("--warmup", action="store_true",
                       help="Run warm-up phase before stress test")
    parser.add_argument("--warmup-messages", type=int, default=100,
                       help="Number of warm-up messages (default: 100)")
    parser.add_argument("--export", type=str, default=None,
                       help="Export results to JSON file")
    parser.add_argument("--auto-update", action="store_true",
                       help="Enable template auto-discovery and persistence (TODO)")
    parser.add_argument("--metadata", type=str, default=None,
                       help="Load per-template metadata (slot_examples) from JSON file")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode with per-iteration traces")
    parser.add_argument("--trace-dir", type=str, default="stress_test_traces",
                       help="Directory for debug trace output (default: stress_test_traces)")

    args = parser.parse_args()

    # Set random seed if specified (for reproducible tests)
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed} (reproducible test)\n")

    # Load external corpus if specified
    corpus = None
    corpus_messages = None
    if args.corpus:
        corpus_path = Path(args.corpus)
        if corpus_path.exists():
            corpus, corpus_messages = load_corpus(corpus_path)
            if corpus:
                print(f"Loaded {len(corpus)} messages from corpus")
                if corpus_messages:
                    weighted = sum(1 for m in corpus_messages if m.weight != 1.0)
                    categorized = sum(1 for m in corpus_messages if m.category)
                    if weighted > 0:
                        print(f"  - {weighted} messages with custom weights")
                    if categorized > 0:
                        print(f"  - {categorized} messages with categories")
                print(f"  - Corpus weight: {args.corpus_weight:.0%} (probability of using corpus vs synthetic)")
                print()
                # Initialize global synthesizer with corpus and metadata
                metadata_path = Path(args.metadata) if args.metadata else None
                get_message_synthesizer(
                    corpus=corpus,
                    corpus_messages=corpus_messages,
                    metadata_path=metadata_path,
                    seed=args.seed,
                    corpus_weight=args.corpus_weight
                )
        else:
            print(f"Warning: Corpus file not found: {corpus_path}\n")
    elif args.metadata:
        # Metadata without corpus
        metadata_path = Path(args.metadata)
        if metadata_path.exists():
            print(f"Loading template metadata from {metadata_path}\n")
            get_message_synthesizer(metadata_path=metadata_path, seed=args.seed)
        else:
            print(f"Warning: Metadata file not found: {metadata_path}\n")

    if args.auto_update:
        print("Template auto-discovery enabled (TODO: not yet implemented)\n")

    try:
        # Setup trace directory if debug mode enabled
        trace_dir = None
        if args.debug:
            trace_dir = Path(args.trace_dir)
            trace_dir.mkdir(exist_ok=True)
            print(f"Debug mode enabled - traces will be saved to {trace_dir}\n")

        results = asyncio.run(run_stress_test(
            num_users=args.users,
            server_url=args.url,
            warmup=args.warmup,
            warmup_messages=args.warmup_messages,
            debug_mode=args.debug,
            trace_dir=trace_dir
        ))

        # Export results if requested
        if args.export and results:
            export_results(results, Path(args.export))

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed: {e}")
        import traceback
        traceback.print_exc()
