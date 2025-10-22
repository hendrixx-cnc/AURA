# AURA Compression: Deployment Guide

**Complete guide for deploying AURA Compression in production environments**

---

## Table of Contents

1. [Installation Methods](#installation-methods)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Monitoring & Logging](#monitoring-logging)
7. [Troubleshooting](#troubleshooting)

---

## Installation Methods

### Method 1: From PyPI (Recommended)

```bash
pip install aura-compression
```

**Verify installation:**
```bash
python3 -c "from aura_compression import AuraCompressor; print('✅ AURA installed')"
```

### Method 2: From Source

```bash
# Clone repository
git clone https://github.com/yourusername/aura-compression.git
cd aura-compression

# Run automated install script
./scripts/install.sh
```

**Manual installation:**
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Method 3: Docker

```bash
# Pull pre-built image
docker pull aura/compression:latest

# Or build locally
docker build -t aura/compression:latest .
```

---

## Local Development

### Quick Start

```bash
# Install in development mode
pip install -e ".[dev]"

# Run demo server
python3 production_websocket_server.py
```

**Expected output:**
```
=== AURA Production WebSocket Demo ===

Test 1: AI response - "Yes, I can help with that..."
  Original: 81 bytes → Compressed: 10 bytes
  Ratio: 8.10:1 ✅

Overall Performance:
  Average ratio: 1.45:1
  Total bandwidth saved: 40.9%
```

### Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linter
flake8 aura_compression/

# Format code
black aura_compression/
```

---

## Docker Deployment

### Option 1: Docker Run

```bash
# Build image
docker build -t aura/compression:latest .

# Run container
docker run -d \
  --name aura-server \
  -p 8765:8765 \
  --restart unless-stopped \
  aura/compression:latest

# Check logs
docker logs -f aura-server

# Stop container
docker stop aura-server
```

### Option 2: Docker Compose (Recommended)

```bash
# Start server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop server
docker-compose down
```

**Custom docker-compose.yml:**
```yaml
version: '3.8'

services:
  aura-server:
    image: aura/compression:latest
    container_name: aura-server
    ports:
      - "8765:8765"
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.connect(('localhost', 8765)); s.close()"]
      interval: 30s
      timeout: 3s
      retries: 3
```

### Automated Docker Deployment

```bash
# Use deployment script
./scripts/deploy_docker.sh
```

---

## Production Deployment

### System Requirements

**Minimum:**
- CPU: 1 core
- RAM: 512 MB
- Disk: 100 MB
- Python: 3.8+

**Recommended:**
- CPU: 2+ cores
- RAM: 2 GB
- Disk: 1 GB (for logs)
- Python: 3.10+

### Environment Setup

```bash
# Create production user
sudo useradd -m -s /bin/bash aura
sudo su - aura

# Install AURA
cd /opt
git clone https://github.com/yourusername/aura-compression.git
cd aura-compression
pip install --user .
```

### Systemd Service (Linux)

Create `/etc/systemd/system/aura-compression.service`:

```ini
[Unit]
Description=AURA Compression Server
After=network.target

[Service]
Type=simple
User=aura
Group=aura
WorkingDirectory=/opt/aura-compression
Environment="PATH=/home/aura/.local/bin:/usr/bin"
ExecStart=/usr/bin/python3 /opt/aura-compression/production_websocket_server.py
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aura-compression

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/aura-compression/logs

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable aura-compression
sudo systemctl start aura-compression

# Check status
sudo systemctl status aura-compression

# View logs
sudo journalctl -u aura-compression -f
```

### Nginx Reverse Proxy

**For WebSocket proxying:**

```nginx
upstream aura_backend {
    server localhost:8765;
}

server {
    listen 80;
    server_name aura.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aura.example.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/aura.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aura.example.com/privkey.pem;

    # WebSocket proxying
    location / {
        proxy_pass http://aura_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
}
```

**Enable Nginx config:**
```bash
sudo ln -s /etc/nginx/sites-available/aura /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: EC2 Instance

```bash
# Launch EC2 instance (Amazon Linux 2)
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Deploy AURA
git clone https://github.com/yourusername/aura-compression.git
cd aura-compression
./scripts/deploy_docker.sh

# Configure security group: Allow inbound port 8765
```

#### Option 2: ECS (Elastic Container Service)

**Task definition:**
```json
{
  "family": "aura-compression",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "aura-server",
      "image": "aura/compression:latest",
      "memory": 512,
      "cpu": 256,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8765,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/aura-compression",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512"
}
```

#### Option 3: Lambda (For API Gateway integration)

**Note:** Lambda has 15-minute timeout, suitable for REST API compression (not WebSocket)

```python
# lambda_handler.py
from aura_compression import AuraCompressor

compressor = AuraCompressor()

def lambda_handler(event, context):
    # Compress response
    text = event.get('body', '')
    result = compressor.compress(text)

    return {
        'statusCode': 200,
        'body': result['compressed_data'],
        'headers': {
            'Content-Type': 'application/octet-stream',
            'X-Compression-Method': result['method'],
            'X-Compression-Ratio': str(result['compression_ratio'])
        }
    }
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/aura-compression

# Deploy to Cloud Run
gcloud run deploy aura-compression \
  --image gcr.io/PROJECT_ID/aura-compression \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8765 \
  --memory 512Mi \
  --cpu 1
```

### Azure Deployment

#### Azure Container Instances

```bash
# Create resource group
az group create --name aura-rg --location eastus

# Deploy container
az container create \
  --resource-group aura-rg \
  --name aura-compression \
  --image aura/compression:latest \
  --dns-name-label aura-compression \
  --ports 8765 \
  --cpu 1 \
  --memory 0.5
```

### Kubernetes (K8s) Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aura-compression
  labels:
    app: aura-compression
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aura-compression
  template:
    metadata:
      labels:
        app: aura-compression
    spec:
      containers:
      - name: aura-server
        image: aura/compression:latest
        ports:
        - containerPort: 8765
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          tcpSocket:
            port: 8765
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          tcpSocket:
            port: 8765
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: aura-compression-service
spec:
  selector:
    app: aura-compression
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8765
  type: LoadBalancer
```

**Deploy:**
```bash
kubectl apply -f deployment.yaml
kubectl get services aura-compression-service
```

---

## Monitoring & Logging

### Log Rotation

**logrotate config (`/etc/logrotate.d/aura-compression`):**
```
/opt/aura-compression/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 aura aura
    sharedscripts
    postrotate
        systemctl reload aura-compression > /dev/null 2>&1 || true
    endscript
}
```

### Prometheus Metrics (Optional)

```python
# Add to production_websocket_server.py
from prometheus_client import Counter, Histogram, start_http_server

compression_requests = Counter('aura_compression_requests_total', 'Total compression requests')
compression_ratio = Histogram('aura_compression_ratio', 'Compression ratio')
compression_method = Counter('aura_compression_method', 'Compression method used', ['method'])

# Start metrics server
start_http_server(8000)
```

### Health Check Endpoint

```python
# health_check.py
import socket

def health_check():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(('localhost', 8765))
        s.close()
        return True
    except:
        return False

if __name__ == "__main__":
    if health_check():
        print("✅ AURA server is healthy")
        exit(0)
    else:
        print("❌ AURA server is down")
        exit(1)
```

---

## Troubleshooting

### Issue 1: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'aura_compression'`

**Solution:**
```bash
# Reinstall package
pip install --force-reinstall aura-compression

# Or from source
pip install -e .
```

### Issue 2: Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 8765
lsof -i :8765

# Kill process
kill -9 <PID>

# Or use different port
python3 production_websocket_server.py --port 8766
```

### Issue 3: Docker Container Exits Immediately

**Solution:**
```bash
# Check container logs
docker logs aura-compression-server

# Run in foreground for debugging
docker run -it --rm aura/compression:latest

# Check health status
docker inspect aura-compression-server | grep Health
```

### Issue 4: Brotli Module Not Found

**Error:** `ModuleNotFoundError: No module named 'brotli'`

**Solution:**
```bash
# Install brotli
pip install brotli

# On macOS with system Python
pip3 install brotli --break-system-packages
```

### Issue 5: Permission Denied (Linux)

**Solution:**
```bash
# Fix file permissions
sudo chown -R aura:aura /opt/aura-compression

# Fix script permissions
chmod +x scripts/*.sh
```

---

## Performance Tuning

### For High-Traffic Deployments

**1. Use multiple workers (gunicorn/uvicorn):**
```bash
gunicorn production_websocket_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8765
```

**2. Enable connection pooling:**
```python
# In production code
compressor = AuraCompressor()  # Reuse instance
```

**3. Increase OS file descriptor limits:**
```bash
# /etc/security/limits.conf
aura soft nofile 65536
aura hard nofile 65536
```

**4. Tune kernel parameters:**
```bash
# /etc/sysctl.conf
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.ip_local_port_range = 10000 65000
```

---

## Support

**Issues:** https://github.com/yourusername/aura-compression/issues
**Docs:** https://github.com/yourusername/aura-compression/blob/main/docs/
**Email:** support@auraprotocol.org

---

**Last Updated:** 2025-10-22
**Version:** 1.0.0
