# OllamaRama 🦙

A robust Ollama API failover proxy that intercepts errors and automatically routes requests to healthy instances. Designed for high-availability Ollama deployments with automatic model failover and pulling.

## Features

✨ **Key Features:**
- 🔄 **Automatic Failover**: Intercepts errors (429, 403, 402, 500, 502, 503, 504, 505) and routes to next available instance
- 🎯 **Multi-Instance Support**: Poll multiple Ollama instances across ports/port ranges
- 📦 **Automatic Model Pulling**: Pulls models on-demand if not available on an instance
- 🏥 **Health Checks**: Built-in health endpoint with instance status monitoring
- 🐳 **Docker-Ready**: Production-ready Docker setup with multi-stage builds
- 🚀 **GitHub Actions**: Automated CI/CD pipeline for deployment
- 📊 **Comprehensive Logging**: Detailed logging for monitoring and debugging
- ⚡ **Performance**: Gunicorn-based production server with multiple workers

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for local development)
- Ollama instances running on specified ports

### Using Docker Compose

```bash
# Clone and navigate to the directory
cd OllamaRama

# Copy and configure environment
cp .env.example .env

# Update port configuration in .env if needed
# Default: OLLAMA_PORTS=11430-11433,11435

# Start the service
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### Using Docker CLI

```bash
# Build the image
docker build -t ollamarama:latest .

# Run the container with Ollama instances on ports 11434-11436
docker run -d \
  --name OllamaRama \
  -p 8000:8000 \
  -e OLLAMA_PORTS="11434-11436" \
  --network host \
  ollamarama:latest
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run the app
python app.py
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_PORTS` | Required | Comma-separated ports/port ranges of Ollama instances |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `DEBUG` | `False` | Enable debug logging |

### Port Configuration Examples

```env
# Single ports
OLLAMA_PORTS=11434,11435,11436

# Port ranges
OLLAMA_PORTS=11430-11433

# Mixed (recommended)
OLLAMA_PORTS=11430-11433,11435,11440-11442
```

## API Usage

OllamaRama proxies all Ollama API endpoints. Replace your Ollama base URL with the proxy URL.

### Generate Text

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Hello, how are you?",
    "stream": false
  }'
```

### Generate with Streaming

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Write a short story",
    "stream": true
  }' | jq '.response' -r
```

### List Models

```bash
curl http://localhost:8000/api/tags
```

### Pull a Model

```bash
curl -X POST http://localhost:8000/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "mistral"}'
```

### Health Check

```bash
curl http://localhost:8000/health | jq
```

Response example:
```json
{
  "status": "healthy",
  "healthy_instances": 3,
  "total_instances": 4,
  "instance_status": {
    "http://localhost:11430": "healthy",
    "http://localhost:11431": "healthy",
    "http://localhost:11432": "healthy",
    "http://localhost:11433": "error 503"
  }
}
```

## Failover Logic

1. **Request arrives** → OllamaRama receives API request
2. **Check model** → If generating, verify model exists on instance
3. **Pull if needed** → If model doesn't exist, pull it automatically
4. **Forward request** → Send request to instance
5. **Monitor response** → Check HTTP status code
   - ✅ 2xx: Success, return response to client
   - ❌ 429/403/402/500/502/503/504/505: Try next instance
   - ⏰ Server actively refuses: Try next instance
   - 📡 Connection error: Try next instance
6. **Repeat** → Move to next instance in the chain
7. **All failed** → Return 503 with error details

## Docker Deployment

### Building

```bash
# Standard build
docker build -t ollamarama:latest .

# Multi-stage build (optimized for production)
# Already configured in Dockerfile
```

### Image Details

- **Base**: `python:3.11-slim`
- **Size**: ~200MB (optimized multi-stage build)
- **User**: Non-root user (ollamarama)
- **Health Check**: Configured
- **Port**: 8000

## GitHub Actions

The repository includes two workflows:

### 1. Docker Build & Push (`docker-build.yml`)
- Triggers on: push to main/develop, PRs, tags
- Builds and pushes to GitHub Container Registry (ghcr.io)
- Supports semantic versioning tags
- Uses BuildKit cache for faster builds

### 2. Tests (`tests.yml`)
- Triggers on: push to main/develop, PRs
- Tests on Python 3.9, 3.10, 3.11
- Runs syntax checks and module imports
- Uploads coverage reports to Codecov

### GitHub Setup

1. **Container Registry Access**:
   ```yaml
   # Already configured with GITHUB_TOKEN
   ```

2. **Docker Hub** (optional):
   Add secrets in GitHub Settings → Secrets:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
   - Update workflow to use Docker Hub login

3. **Enable Actions**:
   - Go to Settings → Actions → Allow all actions

## Advanced Configuration

### Custom Network

```yaml
# docker-compose.yml
networks:
  ollama_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Resource Limits

```yaml
services:
  ollamarama:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Reverse Proxy (Nginx)

```nginx
upstream ollama_proxy {
    server localhost:8000;
}

server {
    listen 80;
    server_name ollama.example.com;

    location /api/ {
        proxy_pass http://ollama_proxy;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
    }

    location /health {
        proxy_pass http://ollama_proxy;
        access_log off;
    }
}
```

## Troubleshooting

### All instances unhealthy
```bash
# Check if Ollama instances are running
docker ps | grep ollama

# Verify port configuration
docker logs OllamaRama | grep "Initialized"

# Test direct connection
curl http://localhost:11434/api/tags
```

### Model not found after pull
```bash
# Check instance logs
docker logs <ollama-container>

# Verify model exists
curl http://localhost:11434/api/tags | jq '.models'
```

### High latency
```bash
# Check instance health
curl http://localhost:8000/health | jq

# Note: Requests now wait indefinitely for responses
# Failover only triggers on connection errors or HTTP error codes
```

### Memory issues
```bash
# Limit concurrent requests with Nginx
# Or add rate limiting in app.py
```

## Performance Tips

1. **Port Range Selection**: Use contiguous port ranges for optimal failover
2. **Instance Count**: 3-5 instances recommended for HA
3. **Model Management**: Keep models synchronized across instances
4. **Resource Sizing**: Allocate at least 2 vCPU and 2GB RAM per instance
5. **Monitoring**: Use `/health` endpoint in monitoring systems

## Security

- ✅ Non-root Docker user
- ✅ Health checks enabled
- ✅ Request timeouts configured
- ✅ Error handling prevents information leakage
- ⚠️ **Note**: This proxy should be behind a reverse proxy with authentication for production use

## Development

### Project Structure

```
OllamaRama/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── .env.example          # Environment configuration template
├── .dockerignore         # Docker build exclusions
├── .gitignore           # Git exclusions
├── .github/
│   └── workflows/       # GitHub Actions workflows
│       ├── docker-build.yml   # Docker image CI/CD
│       └── tests.yml          # Python tests
└── README.md            # This file
```

### Adding Tests

```bash
mkdir tests
cat > tests/test_app.py << 'EOF'
import pytest
from app import OllamaInstanceManager

def test_parse_single_ports():
    manager = OllamaInstanceManager("11434,11435")
    assert len(manager.get_all_instances()) == 2

def test_parse_port_range():
    manager = OllamaInstanceManager("11434-11436")
    assert len(manager.get_all_instances()) == 3

def test_parse_mixed():
    manager = OllamaInstanceManager("11434-11436,11440")
    assert len(manager.get_all_instances()) == 4
EOF

pytest tests/ -v
```

### Running Tests Locally

```bash
pip install pytest pytest-mock pytest-cov
pytest tests/ -v --cov
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Commit and push
6. Open a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check existing documentation
- Review logs: `docker logs OllamaRama`

## Roadmap

- [ ] Load balancing strategies (round-robin, least-loaded)
- [ ] Metrics export (Prometheus)
- [ ] WebSocket support
- [ ] Request rate limiting per model
- [ ] Advanced authentication (API keys)
- [ ] Configuration hot-reload
- [ ] Multi-region failover support

---

**Made with ❤️ for the Ollama community**
