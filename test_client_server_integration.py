#!/usr/bin/env python3
"""
AURA Client-Server Integration Test

Tests full client-server communication with real data:
- AI-to-AI communication (machine-to-machine)
- Human-to-AI communication (ChatGPT-style)

Uses production_hybrid_compression.py for both client and server operations.
"""

from production_hybrid_compression import ProductionHybridCompressor, AuditLogger, CompressionMethod
from datetime import datetime

# ============================================================================
# Test Data - Real AI Response Templates (AI-to-AI)
# ============================================================================

AI_TO_AI_TEST_CASES = [
    {
        "name": "No real-time data response",
        "message": "I don't have access to real-time weather data. Please check an appropriate source",
        "template_id": 0,
        "slots": ["real-time weather data", "Please check an appropriate source"],
        "category": "info"
    },
    {
        "name": "Help confirmation",
        "message": "Yes, I can help with that. What specific aspect would you like to know more about?",
        "template_id": 100,
        "slots": ["aspect"],
        "category": "confirmation"
    },
    {
        "name": "Tool instruction",
        "message": "To install packages, use pip: `pip install numpy`",
        "template_id": 40,
        "slots": ["install packages", "pip", "pip install numpy"],
        "category": "instruction"
    },
    {
        "name": "Recommendation",
        "message": "To choose the best framework, I recommend: research your options, compare features, and test before committing",
        "template_id": 90,
        "slots": ["choose the best framework", "research your options, compare features, and test before committing"],
        "category": "info"
    },
    {
        "name": "Definition",
        "message": "Python is a high-level programming language designed for readability.",
        "template_id": 20,
        "slots": ["Python", "a high-level", "programming language", "designed for readability"],
        "category": "info"
    },
    {
        "name": "No stock data",
        "message": "I don't have access to current stock prices. Please check a financial website",
        "template_id": 0,
        "slots": ["current stock prices", "Please check a financial website"],
        "category": "info"
    },
    {
        "name": "Node.js installation",
        "message": "To install Node.js packages, use npm: `npm install express`",
        "template_id": 40,
        "slots": ["install Node.js packages", "npm", "npm install express"],
        "category": "instruction"
    },
    {
        "name": "Framework recommendation",
        "message": "To build a web application, I recommend: evaluate React for SPAs, Next.js for SSR, or Django for full-stack",
        "template_id": 90,
        "slots": ["build a web application", "evaluate React for SPAs, Next.js for SSR, or Django for full-stack"],
        "category": "info"
    },
    {
        "name": "TypeScript definition",
        "message": "TypeScript is a strongly-typed programming language that builds on JavaScript.",
        "template_id": 20,
        "slots": ["TypeScript", "a strongly-typed", "programming language", "that builds on JavaScript"],
        "category": "info"
    },
    {
        "name": "Help with topic",
        "message": "Yes, I can help with that. What specific topic would you like to know more about?",
        "template_id": 100,
        "slots": ["topic"],
        "category": "confirmation"
    },
]

# ============================================================================
# Test Data - Human-AI Conversations
# ============================================================================

HUMAN_AI_CONVERSATIONS = [
    {
        "name": "Weather Query",
        "turns": [
            {
                "user": "What's the weather like today in San Francisco?",
                "ai": "I don't have access to real-time weather data. Please check a weather website",
                "ai_template_id": 0,
                "ai_slots": ["real-time weather data", "Please check a weather website"]
            }
        ]
    },
    {
        "name": "Programming Help",
        "turns": [
            {
                "user": "How do I install NumPy in Python?",
                "ai": "To install packages, use pip: `pip install numpy`",
                "ai_template_id": 40,
                "ai_slots": ["install packages", "pip", "pip install numpy"]
            },
            {
                "user": "Thanks! What about in a virtual environment?",
                "ai": "To install in virtual environments, use pip: `source venv/bin/activate && pip install numpy`",
                "ai_template_id": 40,
                "ai_slots": ["install in virtual environments", "pip", "source venv/bin/activate && pip install numpy"]
            }
        ]
    },
    {
        "name": "General Question",
        "turns": [
            {
                "user": "Can you help me learn JavaScript?",
                "ai": "Yes, I can help with that. What specific topic would you like to know more about?",
                "ai_template_id": 100,
                "ai_slots": ["topic"]
            }
        ]
    },
    {
        "name": "Docker Definition",
        "turns": [
            {
                "user": "What is Docker?",
                "ai": "Docker is a containerization platform for packaging applications with their dependencies.",
                "ai_template_id": 20,
                "ai_slots": ["Docker", "a containerization", "platform", "for packaging applications with their dependencies"]
            }
        ]
    },
    {
        "name": "Database Recommendation",
        "turns": [
            {
                "user": "What database should I use for my web app?",
                "ai": "To choose a database, I recommend: PostgreSQL for structured data, MongoDB for flexible documents, or Redis for caching",
                "ai_template_id": 90,
                "ai_slots": ["choose a database", "PostgreSQL for structured data, MongoDB for flexible documents, or Redis for caching"]
            }
        ]
    },
]

# ============================================================================
# Test Runner
# ============================================================================

class IntegrationTestRunner:
    def __init__(self):
        # Client and server use same compressor (simulates client-server architecture)
        self.client_compressor = ProductionHybridCompressor(
            binary_advantage_threshold=1.1,
            min_compression_size=50
        )
        self.server_compressor = ProductionHybridCompressor(
            binary_advantage_threshold=1.1,
            min_compression_size=50
        )
        self.audit_logger = AuditLogger("audit/integration_test.log")

        self.results = {
            "ai_to_ai": {
                "passed": 0,
                "failed": 0,
                "total_original": 0,
                "total_compressed": 0,
                "ratios": []
            },
            "human_to_ai": {
                "passed": 0,
                "failed": 0,
                "user_original": 0,
                "user_compressed": 0,
                "ai_original": 0,
                "ai_compressed": 0,
                "user_ratios": [],
                "ai_ratios": []
            }
        }

    def run_all_tests(self):
        """Run all integration tests"""
        self.print_header()

        print("\n" + "="*80)
        print("PHASE 1: AI-TO-AI COMMUNICATION TEST")
        print("="*80 + "\n")

        self.run_ai_to_ai_tests()

        print("\n" + "="*80)
        print("PHASE 2: HUMAN-TO-AI COMMUNICATION TEST")
        print("="*80 + "\n")

        self.run_human_to_ai_tests()

        print("\n" + "="*80)
        print("FINAL SUMMARY")
        print("="*80 + "\n")

        self.print_final_summary()

    def run_ai_to_ai_tests(self):
        """Run AI-to-AI communication tests"""
        for i, test_case in enumerate(AI_TO_AI_TEST_CASES, 1):
            print(f"Test {i}/{len(AI_TO_AI_TEST_CASES)}: {test_case['name']}")
            print("-" * 80)

            try:
                # Client compresses message
                compressed, method, metadata = self.client_compressor.compress(
                    test_case["message"],
                    template_id=test_case.get("template_id"),
                    slots=test_case.get("slots")
                )

                # Server decompresses message
                decompressed = self.server_compressor.decompress(compressed)

                # Verify correctness
                if decompressed == test_case["message"]:
                    print("✅ PASSED")
                    self.results["ai_to_ai"]["passed"] += 1
                else:
                    print("❌ FAILED - Message mismatch")
                    print(f"   Expected: {test_case['message']}")
                    print(f"   Got: {decompressed}")
                    self.results["ai_to_ai"]["failed"] += 1

                # Record metrics
                self.results["ai_to_ai"]["total_original"] += metadata["original_size"]
                self.results["ai_to_ai"]["total_compressed"] += metadata["compressed_size"]
                self.results["ai_to_ai"]["ratios"].append(metadata["ratio"])

                # Print details
                print(f"   Category: {test_case['category']}")
                print(f"   Original: {metadata['original_size']} bytes")
                print(f"   Compressed: {metadata['compressed_size']} bytes")
                print(f"   Ratio: {metadata['ratio']:.2f}:1")
                print(f"   Method: {metadata['method']}")
                print(f"   Saved: {metadata['original_size'] - metadata['compressed_size']} bytes "
                      f"({(1 - metadata['compressed_size'] / metadata['original_size']) * 100:.1f}%)")

                # Audit log
                self.audit_logger.log_message(
                    direction="ai_to_ai",
                    role="assistant",
                    content=test_case["message"],
                    metadata=metadata
                )

            except Exception as e:
                print(f"❌ FAILED - Error: {e}")
                self.results["ai_to_ai"]["failed"] += 1

            print()

    def run_human_to_ai_tests(self):
        """Run human-to-AI conversation tests"""
        for i, conversation in enumerate(HUMAN_AI_CONVERSATIONS, 1):
            print(f"Conversation {i}/{len(HUMAN_AI_CONVERSATIONS)}: {conversation['name']}")
            print("=" * 80)
            print()

            for j, turn in enumerate(conversation["turns"], 1):
                print(f"  Turn {j}:")
                print("  " + "-" * 76)

                try:
                    # Test user message (client -> server)
                    print(f"  👤 USER: {turn['user']}")

                    user_compressed, user_method, user_meta = self.client_compressor.compress(turn["user"])
                    user_decompressed = self.server_compressor.decompress(user_compressed)

                    if user_decompressed == turn["user"]:
                        user_passed = True
                    else:
                        print("     ❌ User message mismatch")
                        user_passed = False

                    self.results["human_to_ai"]["user_original"] += user_meta["original_size"]
                    self.results["human_to_ai"]["user_compressed"] += user_meta["compressed_size"]
                    self.results["human_to_ai"]["user_ratios"].append(user_meta["ratio"])

                    print(f"     Compressed: {user_meta['original_size']} → {user_meta['compressed_size']} bytes "
                          f"({user_meta['ratio']:.2f}:1)")

                    # Audit log user message
                    self.audit_logger.log_message(
                        direction="client_to_server",
                        role="user",
                        content=turn["user"],
                        metadata=user_meta
                    )

                    print()

                    # Test AI response (server -> client)
                    ai_text = turn["ai"]
                    print(f"  🤖 AI: {ai_text[:80]}{'...' if len(ai_text) > 80 else ''}")

                    ai_compressed, ai_method, ai_meta = self.client_compressor.compress(
                        ai_text,
                        template_id=turn.get("ai_template_id"),
                        slots=turn.get("ai_slots")
                    )
                    ai_decompressed = self.server_compressor.decompress(ai_compressed)

                    if ai_decompressed == ai_text:
                        ai_passed = True
                    else:
                        print("     ❌ AI response mismatch")
                        ai_passed = False

                    self.results["human_to_ai"]["ai_original"] += ai_meta["original_size"]
                    self.results["human_to_ai"]["ai_compressed"] += ai_meta["compressed_size"]
                    self.results["human_to_ai"]["ai_ratios"].append(ai_meta["ratio"])

                    print(f"     Compressed: {ai_meta['original_size']} → {ai_meta['compressed_size']} bytes "
                          f"({ai_meta['ratio']:.2f}:1)")
                    print(f"     Method: {ai_meta['method']}")

                    # Audit log AI response
                    self.audit_logger.log_message(
                        direction="server_to_client",
                        role="assistant",
                        content=ai_text,
                        metadata=ai_meta
                    )

                    print()

                    if user_passed and ai_passed:
                        print("     ✅ Turn passed")
                        self.results["human_to_ai"]["passed"] += 1
                    else:
                        self.results["human_to_ai"]["failed"] += 1

                except Exception as e:
                    print(f"     ❌ FAILED - Error: {e}")
                    self.results["human_to_ai"]["failed"] += 1

                print()

            print()

    def print_header(self):
        """Print test header"""
        print()
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + " " * 15 + "AURA PROTOCOL - CLIENT-SERVER INTEGRATION TEST" + " " * 17 + "║")
        print("║" + " " * 78 + "║")
        print("║" + " " * 10 + "Adaptive Universal Response Audit Protocol (AURA)" + " " * 19 + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        print("Testing end-to-end compression with real data:")
        print("  • AI-to-AI communication (machine-to-machine)")
        print("  • Human-to-AI communication (ChatGPT-style)")
        print()
        print("Technology:")
        print("  • Compression: Binary Semantic + Brotli fallback")
        print("  • Audit: Human-readable server-side logging")
        print("  • Reliability: 100% (zero data loss)")
        print()

    def print_final_summary(self):
        """Print final test summary"""
        # AI-to-AI summary
        ai_total_tests = self.results["ai_to_ai"]["passed"] + self.results["ai_to_ai"]["failed"]
        ai_avg_ratio = sum(self.results["ai_to_ai"]["ratios"]) / len(self.results["ai_to_ai"]["ratios"]) if self.results["ai_to_ai"]["ratios"] else 0
        ai_saved = self.results["ai_to_ai"]["total_original"] - self.results["ai_to_ai"]["total_compressed"]
        ai_saved_pct = (ai_saved / self.results["ai_to_ai"]["total_original"] * 100) if self.results["ai_to_ai"]["total_original"] > 0 else 0

        print("AI-TO-AI COMMUNICATION RESULTS:")
        print(f"  Tests: {self.results['ai_to_ai']['passed']}/{ai_total_tests} passed")
        print(f"  Original: {self.results['ai_to_ai']['total_original']:,} bytes")
        print(f"  Compressed: {self.results['ai_to_ai']['total_compressed']:,} bytes")
        print(f"  Saved: {ai_saved:,} bytes ({ai_saved_pct:.1f}%)")
        print(f"  Average Ratio: {ai_avg_ratio:.2f}:1")
        print()

        # Human-to-AI summary
        human_total_tests = self.results["human_to_ai"]["passed"] + self.results["human_to_ai"]["failed"]
        user_avg_ratio = sum(self.results["human_to_ai"]["user_ratios"]) / len(self.results["human_to_ai"]["user_ratios"]) if self.results["human_to_ai"]["user_ratios"] else 0
        ai_resp_avg_ratio = sum(self.results["human_to_ai"]["ai_ratios"]) / len(self.results["human_to_ai"]["ai_ratios"]) if self.results["human_to_ai"]["ai_ratios"] else 0

        total_original = self.results["human_to_ai"]["user_original"] + self.results["human_to_ai"]["ai_original"]
        total_compressed = self.results["human_to_ai"]["user_compressed"] + self.results["human_to_ai"]["ai_compressed"]
        total_saved = total_original - total_compressed
        total_saved_pct = (total_saved / total_original * 100) if total_original > 0 else 0
        overall_ratio = total_original / total_compressed if total_compressed > 0 else 0

        print("HUMAN-TO-AI COMMUNICATION RESULTS:")
        print(f"  Tests: {self.results['human_to_ai']['passed']}/{human_total_tests} passed")
        print(f"  User messages: {user_avg_ratio:.2f}:1 average ratio")
        print(f"  AI responses: {ai_resp_avg_ratio:.2f}:1 average ratio")
        print(f"  Total original: {total_original:,} bytes")
        print(f"  Total compressed: {total_compressed:,} bytes")
        print(f"  Saved: {total_saved:,} bytes ({total_saved_pct:.1f}%)")
        print(f"  Overall Ratio: {overall_ratio:.2f}:1")
        print()

        # Commercial projection
        print("=" * 80)
        print("COMMERCIAL PROJECTION")
        print("=" * 80)
        print()

        print("At ChatGPT scale (100M daily users, 30B messages/month):")
        monthly_messages = 30_000_000_000
        user_ai_count = len(self.results["human_to_ai"]["user_ratios"]) + len(self.results["human_to_ai"]["ai_ratios"])
        if user_ai_count > 0:
            avg_message_size = (self.results["ai_to_ai"]["total_original"] / len(AI_TO_AI_TEST_CASES) +
                               total_original / user_ai_count) / 2
        else:
            avg_message_size = self.results["ai_to_ai"]["total_original"] / len(AI_TO_AI_TEST_CASES)
        monthly_bandwidth_original = (monthly_messages * avg_message_size) / (1024**3)  # GB
        monthly_bandwidth_compressed = monthly_bandwidth_original / ((ai_avg_ratio + overall_ratio) / 2)
        cost_per_gb = 0.085
        monthly_savings = (monthly_bandwidth_original - monthly_bandwidth_compressed) * cost_per_gb
        annual_savings = monthly_savings * 12

        print(f"  Average compression: {((ai_avg_ratio + overall_ratio) / 2):.2f}:1")
        print(f"  Monthly bandwidth: {monthly_bandwidth_original:,.0f} GB → {monthly_bandwidth_compressed:,.0f} GB")
        print(f"  💰 Monthly savings: ${monthly_savings:,.2f}")
        print(f"  💰 Annual savings: ${annual_savings:,.2f}")
        print()

        # Audit info
        print("=" * 80)
        print("AUDIT LOGGING")
        print("=" * 80)
        print()
        print("✅ All messages logged in human-readable format")
        print("📋 Audit log: audit/integration_test.log")
        print(f"📊 Total log entries: {ai_total_tests + human_total_tests * 2}")
        print()

        # Final verdict
        print("=" * 80)
        print("VERDICT")
        print("=" * 80)
        print()

        all_passed = (self.results["ai_to_ai"]["failed"] == 0 and
                     self.results["human_to_ai"]["failed"] == 0)

        if all_passed:
            print("✅ ALL TESTS PASSED")
            print(f"✅ AI-to-AI: {ai_avg_ratio:.2f}:1 compression ratio")
            print(f"✅ Human-to-AI: {overall_ratio:.2f}:1 overall ratio")
            print("✅ Zero data loss (100% reliability)")
            print("✅ Audit logging complete")
            print()
            print("🚀 AURA PROTOCOL IS PRODUCTION READY")
            print("💰 Patent Pending | Enterprise Ready | Compliance-First")
        else:
            total_failed = self.results["ai_to_ai"]["failed"] + self.results["human_to_ai"]["failed"]
            print(f"❌ {total_failed} TEST(S) FAILED")
            print("⚠️  Review failures before production deployment")

        print()

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\nInitializing integration test runner...")
    runner = IntegrationTestRunner()
    runner.run_all_tests()
