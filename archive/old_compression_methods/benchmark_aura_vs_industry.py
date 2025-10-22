#!/usr/bin/env python3
"""
Comprehensive Benchmark: AURA vs Gzip vs Brotli
Tests on realistic AI responses to prove commercial value
"""
import sys
import os
import gzip
import brotli
import time
import json
from statistics import mean, median, stdev

# Add package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages/aura-compressor-py/src'))

from aura_compressor.streamer import AuraTransceiver

# Realistic AI responses (simulating OpenAI, Claude, etc.)
REALISTIC_AI_RESPONSES = [
    # Short responses (50-200 bytes)
    "I don't have access to real-time information, so I can't tell you the current weather. Please check a weather website or app.",

    "Yes, I can help with that. What specific aspect would you like to know more about?",

    "The capital of France is Paris.",

    # Medium responses (200-500 bytes)
    """Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves. The process involves training algorithms on large datasets to identify patterns and make predictions or decisions.""",

    """To install Python packages, you can use pip, which is Python's package installer. Simply run 'pip install package_name' in your terminal or command prompt. For example, to install the requests library, you would type 'pip install requests'. Make sure you have pip installed and added to your PATH.""",

    # Long responses (500-1500 bytes)
    """Here's a simple example of how to use Python for data analysis:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
data = pd.read_csv('data.csv')

# Perform basic analysis
print(data.describe())
print(data.head())

# Create visualization
plt.figure(figsize=(10, 6))
plt.plot(data['date'], data['value'])
plt.xlabel('Date')
plt.ylabel('Value')
plt.title('Data Over Time')
plt.show()
```

This code loads a CSV file, displays statistical summaries, shows the first few rows, and creates a line plot. You can customize this based on your specific dataset and analysis needs.""",

    """Neural networks are computing systems inspired by biological neural networks in animal brains. They consist of interconnected nodes (neurons) organized in layers:

1. Input Layer: Receives the initial data
2. Hidden Layers: Process information through weighted connections
3. Output Layer: Produces the final result

Each connection has a weight that adjusts during training through backpropagation. The network learns by minimizing the difference between predicted and actual outputs using optimization algorithms like gradient descent.

Key components:
- Activation functions (ReLU, sigmoid, tanh)
- Loss functions (MSE, cross-entropy)
- Optimizers (Adam, SGD, RMSprop)

Neural networks excel at pattern recognition, classification, and regression tasks.""",

    """The React component lifecycle has evolved with hooks, but understanding the traditional lifecycle is still valuable:

1. Mounting Phase:
   - constructor(): Initialize state
   - render(): Return JSX
   - componentDidMount(): Side effects, API calls

2. Updating Phase:
   - shouldComponentUpdate(): Optimization
   - render(): Re-render
   - componentDidUpdate(): Post-update operations

3. Unmounting Phase:
   - componentWillUnmount(): Cleanup

With hooks, these map to:
- useState() for state
- useEffect() for side effects
- useMemo() and useCallback() for optimization

Modern React favors functional components with hooks for cleaner, more maintainable code.""",

    # Very long responses (1500-3000 bytes)
    """Let me explain the differences between SQL and NoSQL databases in detail:

**SQL Databases (Relational):**
Examples: MySQL, PostgreSQL, Oracle, SQL Server

Advantages:
- ACID compliance (Atomicity, Consistency, Isolation, Durability)
- Structured data with predefined schemas
- Complex queries using JOIN operations
- Data integrity through foreign keys and constraints
- Mature ecosystem with excellent tooling
- Suitable for complex transactions

Disadvantages:
- Rigid schema makes changes difficult
- Vertical scaling can be expensive
- Not ideal for unstructured data
- Performance can degrade with massive datasets

**NoSQL Databases (Non-relational):**
Examples: MongoDB, Cassandra, Redis, DynamoDB

Types:
1. Document stores (MongoDB, CouchDB)
2. Key-value stores (Redis, DynamoDB)
3. Column-family stores (Cassandra, HBase)
4. Graph databases (Neo4j, ArangoDB)

Advantages:
- Flexible schemas (schema-less)
- Horizontal scaling (distributed architecture)
- High performance for specific use cases
- Better suited for unstructured/semi-structured data
- Easy to scale for big data applications

Disadvantages:
- Eventual consistency (not always ACID)
- Less mature ecosystem in some cases
- Limited query capabilities compared to SQL
- Potential for data duplication

**When to use SQL:**
- Complex queries and transactions
- Data integrity is critical
- Structured data with clear relationships
- Financial systems, ERP, CRM

**When to use NoSQL:**
- Rapid development with changing requirements
- Large volumes of unstructured data
- High scalability needs
- Real-time web applications
- IoT and big data analytics
- Content management systems

The choice depends on your specific requirements, data structure, scalability needs, and consistency requirements. Many modern applications use both (polyglot persistence).""",

    """Here's a comprehensive guide to implementing authentication in a web application:

**1. Password-Based Authentication:**

Backend (Node.js/Express):
```javascript
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

// Register user
app.post('/register', async (req, res) => {
  const { email, password } = req.body;

  // Hash password
  const saltRounds = 10;
  const hashedPassword = await bcrypt.hash(password, saltRounds);

  // Save to database
  await User.create({ email, password: hashedPassword });

  res.status(201).json({ message: 'User created' });
});

// Login
app.post('/login', async (req, res) => {
  const { email, password } = req.body;

  // Find user
  const user = await User.findOne({ email });
  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Verify password
  const valid = await bcrypt.compare(password, user.password);
  if (!valid) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Generate JWT
  const token = jwt.sign(
    { userId: user.id, email: user.email },
    process.env.JWT_SECRET,
    { expiresIn: '24h' }
  );

  res.json({ token });
});
```

**2. OAuth 2.0 / Social Login:**

```javascript
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;

passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: '/auth/google/callback'
  },
  async (accessToken, refreshToken, profile, done) => {
    // Find or create user
    let user = await User.findOne({ googleId: profile.id });
    if (!user) {
      user = await User.create({
        googleId: profile.id,
        email: profile.emails[0].value,
        name: profile.displayName
      });
    }
    return done(null, user);
  }
));
```

**3. Security Best Practices:**

- Use HTTPS everywhere
- Implement rate limiting
- Add CSRF protection
- Set secure cookie flags (httpOnly, secure, sameSite)
- Use environment variables for secrets
- Implement password strength requirements
- Add email verification
- Enable two-factor authentication (2FA)
- Log authentication attempts
- Implement account lockout after failed attempts
- Use secure session management
- Regularly rotate secrets and tokens

**4. Frontend (React):**

```javascript
// Auth context
const AuthContext = createContext();

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const login = async (email, password) => {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const { token } = await response.json();
    localStorage.setItem('token', token);
    // Decode and set user
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

This provides a solid foundation for authentication in modern web applications.""",

    # Code-heavy responses
    """Here's a complete implementation of a binary search tree in Python:

```python
class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

class BinarySearchTree:
    def __init__(self):
        self.root = None

    def insert(self, value):
        if self.root is None:
            self.root = Node(value)
        else:
            self._insert_recursive(self.root, value)

    def _insert_recursive(self, node, value):
        if value < node.value:
            if node.left is None:
                node.left = Node(value)
            else:
                self._insert_recursive(node.left, value)
        else:
            if node.right is None:
                node.right = Node(value)
            else:
                self._insert_recursive(node.right, value)

    def search(self, value):
        return self._search_recursive(self.root, value)

    def _search_recursive(self, node, value):
        if node is None:
            return False
        if node.value == value:
            return True
        if value < node.value:
            return self._search_recursive(node.left, value)
        return self._search_recursive(node.right, value)

    def inorder_traversal(self):
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)

# Usage
bst = BinarySearchTree()
values = [50, 30, 70, 20, 40, 60, 80]
for val in values:
    bst.insert(val)

print(bst.search(40))  # True
print(bst.inorder_traversal())  # [20, 30, 40, 50, 60, 70, 80]
```

Time complexity: O(log n) average, O(n) worst case for unbalanced trees.""",

    # JSON-heavy response
    """{
  "status": "success",
  "data": {
    "users": [
      {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "admin",
        "permissions": ["read", "write", "delete"],
        "metadata": {
          "created_at": "2024-01-15T10:30:00Z",
          "last_login": "2024-10-22T08:15:00Z",
          "preferences": {
            "theme": "dark",
            "notifications": true,
            "language": "en"
          }
        }
      },
      {
        "id": 2,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "role": "user",
        "permissions": ["read", "write"],
        "metadata": {
          "created_at": "2024-02-20T14:45:00Z",
          "last_login": "2024-10-21T18:30:00Z",
          "preferences": {
            "theme": "light",
            "notifications": false,
            "language": "es"
          }
        }
      }
    ],
    "total_count": 2,
    "page": 1,
    "per_page": 10
  }
}""",

    # Mixed content
    """The CAP theorem states that a distributed system can only guarantee two of three properties:

**Consistency (C):** All nodes see the same data at the same time
**Availability (A):** Every request receives a response
**Partition Tolerance (P):** System continues operating despite network failures

Since network partitions are inevitable, you must choose between CP or AP:

**CP Systems (Consistency + Partition Tolerance):**
- MongoDB, HBase, Redis
- Sacrifice availability during partitions
- Ensure data consistency
- Good for: Financial transactions, inventory management

**AP Systems (Availability + Partition Tolerance):**
- Cassandra, CouchDB, DynamoDB
- Sacrifice consistency during partitions
- Eventual consistency model
- Good for: Social media, content delivery, analytics

**CA Systems (Consistency + Availability):**
- Traditional RDBMS in single-node setup
- Not partition-tolerant
- Impractical for distributed systems

Modern databases often allow tuning consistency levels per query, enabling flexible trade-offs based on specific use cases.""",
]

def compress_gzip(text: str, level: int = 9) -> bytes:
    """Compress text with Gzip"""
    return gzip.compress(text.encode('utf-8'), compresslevel=level)

def compress_brotli(text: str, quality: int = 11) -> bytes:
    """Compress text with Brotli"""
    return brotli.compress(text.encode('utf-8'), quality=quality)

def compress_aura(transceiver: AuraTransceiver, text: str) -> bytes:
    """Compress text with AURA"""
    packets = transceiver.compress(text, adaptive=True)
    # Combine all packets
    return b''.join(packets)

def benchmark_compression():
    """Run comprehensive benchmark"""

    print("=" * 80)
    print("COMPREHENSIVE COMPRESSION BENCHMARK: AURA vs Gzip vs Brotli")
    print("=" * 80)
    print()

    # Initialize AURA transceiver
    print("Initializing AURA transceiver...")
    server = AuraTransceiver()
    client = AuraTransceiver()

    # Perform handshake
    handshake_packet = server.perform_handshake()
    client.receive_handshake(handshake_packet)
    print(f"AURA handshake complete. Handshake size: {len(handshake_packet)} bytes")
    print()

    # Track results
    results = {
        'original': [],
        'gzip': [],
        'brotli': [],
        'aura': [],
        'gzip_time': [],
        'brotli_time': [],
        'aura_time': [],
    }

    print("=" * 80)
    print("BENCHMARKING ON REALISTIC AI RESPONSES")
    print("=" * 80)
    print()

    for idx, text in enumerate(REALISTIC_AI_RESPONSES, 1):
        original_size = len(text.encode('utf-8'))

        # Gzip compression
        start = time.perf_counter()
        gzip_compressed = compress_gzip(text)
        gzip_time = (time.perf_counter() - start) * 1000  # ms
        gzip_size = len(gzip_compressed)

        # Brotli compression
        start = time.perf_counter()
        brotli_compressed = compress_brotli(text)
        brotli_time = (time.perf_counter() - start) * 1000  # ms
        brotli_size = len(brotli_compressed)

        # AURA compression
        start = time.perf_counter()
        aura_compressed = compress_aura(server, text)
        aura_time = (time.perf_counter() - start) * 1000  # ms
        aura_size = len(aura_compressed)

        # Store results
        results['original'].append(original_size)
        results['gzip'].append(gzip_size)
        results['brotli'].append(brotli_size)
        results['aura'].append(aura_size)
        results['gzip_time'].append(gzip_time)
        results['brotli_time'].append(brotli_time)
        results['aura_time'].append(aura_time)

        # Calculate ratios
        gzip_ratio = original_size / gzip_size if gzip_size > 0 else 0
        brotli_ratio = original_size / brotli_size if brotli_size > 0 else 0
        aura_ratio = original_size / aura_size if aura_size > 0 else 0

        # Determine winner
        best_size = min(gzip_size, brotli_size, aura_size)
        if aura_size == best_size:
            winner = "🏆 AURA"
        elif brotli_size == best_size:
            winner = "Brotli"
        else:
            winner = "Gzip"

        print(f"Response {idx} ({original_size:,} bytes):")
        print(f"  Gzip:   {gzip_size:6,} bytes ({gzip_ratio:5.2f}:1) - {gzip_time:6.2f}ms")
        print(f"  Brotli: {brotli_size:6,} bytes ({brotli_ratio:5.2f}:1) - {brotli_time:6.2f}ms")
        print(f"  AURA:   {aura_size:6,} bytes ({aura_ratio:5.2f}:1) - {aura_time:6.2f}ms")
        print(f"  Winner: {winner}")
        print()

    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()

    total_original = sum(results['original'])
    total_gzip = sum(results['gzip'])
    total_brotli = sum(results['brotli'])
    total_aura = sum(results['aura'])

    print(f"Total Original Size:  {total_original:,} bytes")
    print(f"Total Gzip Size:      {total_gzip:,} bytes ({total_original/total_gzip:.2f}:1)")
    print(f"Total Brotli Size:    {total_brotli:,} bytes ({total_original/total_brotli:.2f}:1)")
    print(f"Total AURA Size:      {total_aura:,} bytes ({total_original/total_aura:.2f}:1)")
    print()

    gzip_savings = total_original - total_gzip
    brotli_savings = total_original - total_brotli
    aura_savings = total_original - total_aura

    print(f"Bandwidth Savings:")
    print(f"  Gzip:   {gzip_savings:,} bytes ({100*gzip_savings/total_original:.1f}%)")
    print(f"  Brotli: {brotli_savings:,} bytes ({100*brotli_savings/total_original:.1f}%)")
    print(f"  AURA:   {aura_savings:,} bytes ({100*aura_savings/total_original:.1f}%)")
    print()

    # AURA advantage over competitors
    aura_vs_gzip = total_gzip - total_aura
    aura_vs_brotli = total_brotli - total_aura

    print(f"AURA Advantage:")
    print(f"  vs Gzip:   {aura_vs_gzip:+,} bytes ({100*aura_vs_gzip/total_gzip:+.1f}%)")
    print(f"  vs Brotli: {aura_vs_brotli:+,} bytes ({100*aura_vs_brotli/total_brotli:+.1f}%)")
    print()

    # Performance statistics
    avg_gzip_time = mean(results['gzip_time'])
    avg_brotli_time = mean(results['brotli_time'])
    avg_aura_time = mean(results['aura_time'])

    print(f"Average Compression Time:")
    print(f"  Gzip:   {avg_gzip_time:.3f}ms")
    print(f"  Brotli: {avg_brotli_time:.3f}ms")
    print(f"  AURA:   {avg_aura_time:.3f}ms")
    print()

    # OpenAI cost savings calculation
    print("=" * 80)
    print("COMMERCIAL IMPACT: OpenAI Cost Savings Calculation")
    print("=" * 80)
    print()

    # Assumptions
    monthly_responses = 1_000_000_000  # 1 billion responses/month (conservative for OpenAI)
    avg_response_size = mean(results['original'])

    print(f"Assumptions:")
    print(f"  Monthly AI responses: {monthly_responses:,}")
    print(f"  Average response size: {avg_response_size:.0f} bytes")
    print()

    # Calculate monthly bandwidth
    monthly_bandwidth_uncompressed = monthly_responses * avg_response_size / (1024**3)  # GB
    monthly_bandwidth_gzip = monthly_responses * mean(results['gzip']) / (1024**3)
    monthly_bandwidth_brotli = monthly_responses * mean(results['brotli']) / (1024**3)
    monthly_bandwidth_aura = monthly_responses * mean(results['aura']) / (1024**3)

    print(f"Monthly Bandwidth (1B responses):")
    print(f"  Uncompressed: {monthly_bandwidth_uncompressed:,.0f} GB")
    print(f"  With Gzip:    {monthly_bandwidth_gzip:,.0f} GB")
    print(f"  With Brotli:  {monthly_bandwidth_brotli:,.0f} GB")
    print(f"  With AURA:    {monthly_bandwidth_aura:,.0f} GB")
    print()

    # Cost calculation (AWS CloudFront pricing: ~$0.085/GB)
    cost_per_gb = 0.085

    cost_gzip = monthly_bandwidth_gzip * cost_per_gb
    cost_brotli = monthly_bandwidth_brotli * cost_per_gb
    cost_aura = monthly_bandwidth_aura * cost_per_gb

    savings_vs_gzip = (cost_gzip - cost_aura) * 12  # Annual
    savings_vs_brotli = (cost_brotli - cost_aura) * 12  # Annual

    print(f"Monthly Bandwidth Costs (@ ${cost_per_gb}/GB):")
    print(f"  With Gzip:   ${cost_gzip:,.0f}/month")
    print(f"  With Brotli: ${cost_brotli:,.0f}/month")
    print(f"  With AURA:   ${cost_aura:,.0f}/month")
    print()

    print(f"💰 ANNUAL SAVINGS WITH AURA:")
    print(f"  vs Gzip:   ${savings_vs_gzip:,.0f}/year")
    print(f"  vs Brotli: ${savings_vs_brotli:,.0f}/year")
    print()

    # At scale (10B responses/month - realistic for OpenAI)
    scale_factor = 10
    print(f"At 10x Scale ({monthly_responses * scale_factor:,} responses/month):")
    print(f"  Annual savings vs Gzip:   ${savings_vs_gzip * scale_factor:,.0f}/year")
    print(f"  Annual savings vs Brotli: ${savings_vs_brotli * scale_factor:,.0f}/year")
    print()

    # Win rate
    wins = sum(1 for i in range(len(results['original']))
               if results['aura'][i] <= min(results['gzip'][i], results['brotli'][i]))

    print(f"AURA Win Rate: {wins}/{len(results['original'])} ({100*wins/len(results['original']):.0f}%)")
    print()

    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()

    if aura_vs_brotli > 0:
        print(f"✅ AURA compresses {100*aura_vs_brotli/total_brotli:.1f}% better than Brotli")
        print(f"✅ AURA saves OpenAI ${savings_vs_brotli:,.0f}/year (1B responses)")
        print(f"✅ At scale: ${savings_vs_brotli * scale_factor:,.0f}/year (10B responses)")
    else:
        print(f"⚠️  AURA compresses {100*abs(aura_vs_brotli)/total_brotli:.1f}% worse than Brotli")
        print(f"⚠️  Need to optimize AURA for better compression ratios")

    print()

    # Export results to JSON
    export_data = {
        'summary': {
            'total_original_bytes': total_original,
            'total_gzip_bytes': total_gzip,
            'total_brotli_bytes': total_brotli,
            'total_aura_bytes': total_aura,
            'gzip_ratio': total_original / total_gzip,
            'brotli_ratio': total_original / total_brotli,
            'aura_ratio': total_original / total_aura,
            'aura_advantage_vs_gzip_percent': 100 * aura_vs_gzip / total_gzip,
            'aura_advantage_vs_brotli_percent': 100 * aura_vs_brotli / total_brotli,
            'annual_savings_vs_brotli_usd': savings_vs_brotli,
        },
        'detailed_results': [
            {
                'response_index': i + 1,
                'original_bytes': results['original'][i],
                'gzip_bytes': results['gzip'][i],
                'brotli_bytes': results['brotli'][i],
                'aura_bytes': results['aura'][i],
                'gzip_time_ms': results['gzip_time'][i],
                'brotli_time_ms': results['brotli_time'][i],
                'aura_time_ms': results['aura_time'][i],
            }
            for i in range(len(results['original']))
        ]
    }

    with open('benchmark_results.json', 'w') as f:
        json.dump(export_data, f, indent=2)

    print("📊 Results exported to benchmark_results.json")
    print()

if __name__ == "__main__":
    benchmark_compression()
