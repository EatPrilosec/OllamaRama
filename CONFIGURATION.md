# OllamaRama Configuration Examples

This file contains example configurations for different deployment scenarios.

## Scenario 1: Development with Local Instances

Running Ollama on ports 11434-11436 (default + 2 more)

### .env
```
OLLAMA_PORTS=11434-11436
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### Docker Compose
```bash
docker-compose up -d
curl http://localhost:8000/health
```

---

## Scenario 2: Production HA with Multiple Nodes

Ollama instances distributed across ports 11430-11439 (10 instances)

### .env
```
OLLAMA_PORTS=11430-11439
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### docker-compose.yml for production
```yaml
version: '3.8'
services:
  ollamarama:
    image: ghcr.io/your-username/ollamarama:v1.0.0
    container_name: OllamaRama
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_PORTS=11430-11439
      - DEBUG=False
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    networks:
      - production
networks:
  production:
    driver: bridge
```

---

## Scenario 3: Mixed Port Configuration

Using specific ports with gaps (for selective instances)

### .env
```
OLLAMA_PORTS=11434,11435,11440,11441-11443,11500
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

This creates instances on: 11434, 11435, 11440, 11441, 11442, 11443, 11500

---

## Scenario 4: Remote Ollama Instances

If Ollama instances are on different hosts, you'll need to modify the proxy.
Currently OllamaRama assumes localhost only. To support remote hosts:

### Modified app.py needed:
```python
# Instead of:
# self.instances.append(f"http://localhost:{port}")

# Use configuration like:
# OLLAMA_INSTANCES=http://host1:11434,http://host2:11434
```

---

## Scenario 5: Kubernetes Deployment

Using ConfigMap for port configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollamarama-config
data:
  OLLAMA_PORTS: "11434-11438"
  DEBUG: "false"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollamarama
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: ollamarama
        envFrom:
        - configMapRef:
            name: ollamarama-config
```

---

## Scenario 6: Docker Swarm Deployment

Using environment variables in stack:

```yaml
version: '3.8'
services:
  ollamarama:
    image: ghcr.io/your-username/ollamarama:latest
    environment:
      - OLLAMA_PORTS=11434-11436
      - DEBUG=false
    ports:
      - "8000:8000"
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == worker
```

---

## Testing Port Configurations

### Test with curl
```bash
# Test health endpoint
curl http://localhost:8000/health | jq

# Test with a request
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "llama2", "prompt": "Hello"}'
```

### Docker test
```bash
docker run -it \
  -e OLLAMA_PORTS=11434-11436 \
  ollamarama:latest

# In another terminal
docker exec -it <container-id> curl http://localhost:8000/health
```

### Python test
```python
import requests
from app import OllamaInstanceManager

# Test port parsing
manager = OllamaInstanceManager("11434-11436,11440")
print(manager.get_all_instances())

# Output:
# ['http://localhost:11434', 'http://localhost:11435', 
#  'http://localhost:11436', 'http://localhost:11440']
```

---

## Troubleshooting Port Configuration

### Issue: "No valid ports found"
**Cause**: Port configuration format is incorrect
**Solution**: Check format is either:
- Single ports: `11434,11435`
- Ranges: `11434-11436`
- Mixed: `11434-11436,11440`

### Issue: "Connection refused"
**Cause**: Ollama instances not running on specified ports
**Solution**:
```bash
# Check running instances
docker ps | grep ollama

# Start Ollama on specific ports
# Ollama by default uses 11434
# To use 11435: export OLLAMA_HOST=127.0.0.1:11435
```

### Issue: "All instances failed"
**Cause**: Instances down or unreachable
**Solution**:
```bash
# Check instance health directly
curl http://localhost:11434/api/tags

# Check proxy health
curl http://localhost:8000/health | jq
```

---

## Best Practices

1. **Use ranges when possible**: `11434-11436` instead of `11434,11435,11436`
2. **Start from port 11434**: Default Ollama port
3. **Gap for manual instances**: If you have different configurations, leave gaps
4. **Environment-specific configs**: Use different .env files for dev/prod

### Example multi-environment setup:
```
.env.development   # OLLAMA_PORTS=11434-11436
.env.staging       # OLLAMA_PORTS=11430-11433
.env.production    # OLLAMA_PORTS=11420-11445
```

---

For more information, see [README.md](README.md) or [DEPLOYMENT.md](DEPLOYMENT.md).
