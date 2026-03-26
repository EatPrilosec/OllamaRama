# OllamaRama Quick Reference

Quick answers to common questions and tasks.

## Quick Start (30 seconds)

```bash
cd /home/munch/.ollama-docker/OllamaRama
docker-compose up -d
curl http://localhost:8000/health
```

## Port Configuration

```bash
# Edit .env file
OLLAMA_PORTS=11434-11436

# Single ports: 11434,11435,11436
# Port range:   11434-11436
# Mixed:        11434-11436,11440
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tags` | GET | List models |
| `/api/generate` | POST | Generate text |
| `/api/chat` | POST | Chat |
| `/api/pull` | POST | Download model |
| `/api/delete` | DELETE | Remove model |
| `/health` | GET | Health status |
| `/` | GET | Info |

## Example Requests

### List Models
```bash
curl http://localhost:8000/api/tags | jq
```

### Generate Text
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "What is AI?",
    "stream": false
  }'
```

### Pull Model
```bash
curl -X POST http://localhost:8000/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "mistral"}'
```

## Development Commands

```bash
make install        # Install dependencies
make dev           # Start dev server
make test          # Run tests
make lint          # Check code style
make format        # Format code
make build         # Build Docker image
make clean         # Clean up junk
```

## Docker Commands

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Check health
curl http://localhost:8000/health

# Shell into container
docker exec -it OllamaRama bash
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Configuration (edit for your setup) |
| `.env.example` | Template |
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Local setup |
| `requirements.txt` | Python packages |

## Documentation Map

| Document | Use When |
|----------|----------|
| `README.md` | Learning how to use it |
| `DEPLOYMENT.md` | Deploying to production |
| `DEVELOPMENT.md` | Contributing code |
| `ARCHITECTURE.md` | Understanding design |
| `CONFIGURATION.md` | Setting up ports |

## Troubleshooting

### Service won't start
```bash
docker logs OllamaRama
# Check: OLLAMA_PORTS set correctly
# Check: Ollama instances running on those ports
```

### All instances show unhealthy
```bash
# Check if Ollama is running on specified ports
docker ps | grep ollama
curl http://localhost:11434/api/tags
```

### Slow responses
```bash
# Check health of instances
curl http://localhost:8000/health | jq

# Check logs
docker-compose logs -f
```

## Port Ranges

### Common Setups

**Development**
```
OLLAMA_PORTS=11434-11436
```

**Production HA**
```
OLLAMA_PORTS=11420-11430
```

**Multi-node**
```
OLLAMA_PORTS=11400-11450
```

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `OLLAMA_PORTS` | Required | Comma-separated ports/ranges |
| `HOST` | 0.0.0.0 | Bind address |
| `PORT` | 8000 | Proxy port |
| `DEBUG` | False | Enable verbose logging |

## Model Management

### Auto-Pulled Models

If a model isn't on an instance when requested:
1. OllamaRama detects it's missing
2. Pulls it automatically
3. Retries the request

### Manual Pull

```bash
curl -X POST http://localhost:8000/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "mistral"}'
```

## Failover Logic

When an instance returns:
- `2xx` → Success ✓
- `429, 403, 402, 500, 502, 503, 504, 505` → Try next instance
- Connection refused → Try next instance
- Network error → Try next instance
- All failed → Return 503

## Health Check

```bash
curl http://localhost:8000/health
```

Response shows:
- Overall status
- Healthy instance count
- Per-instance details

## Docker Images

### Build locally
```bash
docker build -t ollamarama:latest .
```

### Run
```bash
docker run -d \
  --name OllamaRama \
  -p 8000:8000 \
  -e OLLAMA_PORTS=11434-11436 \
  ollamarama:latest
```

## GitHub Actions

Two workflows included:

**docker-build.yml** - Build and push image
- Triggers: push, PR, tag
- Outputs to: ghcr.io

**tests.yml** - Run tests
- Triggers: push, PR
- Tests: Python 3.9, 3.10, 3.11

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov

# Specific test
pytest tests/test_app.py::TestPortParsing -v
```

## Security

- Runs as non-root user
- Health checks enabled
- Timeouts configured
- No hardcoded credentials
- Error handling prevents leaks

## Performance Tips

1. Use port ranges: `11434-11436` not `11434,11435,11436`
2. 3-5 instances recommended
3. Keep models synchronized
4. Monitor `/health` endpoint
5. Use reverse proxy for production

## Common Port Numbers

| Port Range | Use Case |
|-----------|----------|
| 11434 | Default Ollama |
| 11434-11436 | Dev (3 instances) |
| 11420-11430 | HA (11 instances) |
| 11400-11450 | Large deployment |

## Logs

View logs while running:
```bash
docker-compose logs -f OllamaRama
```

Look for:
- "Attempt X" → Failover in progress
- "Pulling model" → Auto-pulling
- "All instances failed" → Everything is down

## Files to Edit

| File | For What |
|------|----------|
| `.env` | Port configuration |
| `docker-compose.yml` | Docker setup |
| `Dockerfile` | Image customization |
| `app.py` | Logic changes |

## Deployment Checklist

- [ ] Clone repository
- [ ] Copy `.env.example` to `.env`
- [ ] Configure `OLLAMA_PORTS`
- [ ] Start Ollama instances on those ports
- [ ] Run `docker-compose up -d`
- [ ] Test with `curl http://localhost:8000/health`
- [ ] Test with actual requests

## Getting Help

1. Check `README.md` for overview
2. See `DEPLOYMENT.md` for your use case
3. Check `CONFIGURATION.md` for port issues
4. View `DEVELOPMENT.md` for code changes
5. Read `ARCHITECTURE.md` for design details

## Version

**OllamaRama v1.0.0** - Production Ready

Created: March 2026
License: MIT
