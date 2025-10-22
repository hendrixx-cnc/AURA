# AURA Compression - Production Docker Image
FROM python:3.11-slim

# Metadata
LABEL maintainer="Todd Hendricks <todd@auraprotocol.org>"
LABEL description="AURA Compression - AI-Optimized Hybrid Compression Protocol"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install optional websocket support
RUN pip install --no-cache-dir websockets>=10.0

# Copy application code
COPY aura_compression/ /app/aura_compression/
COPY production_websocket_server.py /app/
COPY README.md LICENSE /app/

# Create non-root user
RUN useradd -m -u 1000 aura && \
    chown -R aura:aura /app

# Switch to non-root user
USER aura

# Expose WebSocket port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 8765)); s.close()" || exit 1

# Default command: run WebSocket demo server
CMD ["python", "production_websocket_server.py"]
