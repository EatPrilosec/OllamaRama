# OllamaRama Architecture

This document describes the architecture and design of OllamaRama.

## Overview

OllamaRama is an Ollama API failover proxy that sits between clients and multiple Ollama instances, providing:

- **Automatic Failover**: Intercepts HTTP errors and routes to healthy instances
- **Load Distribution**: Distributes requests across multiple instances
- **Model Management**: Automatically pulls missing models on-demand
- **Health Monitoring**: Built-in health checks and instance status tracking

## System Components

### 1. Flask Application Layer

**File**: `app.py`

The main application using Flask micro-framework provides:

```
┌─────────────────────────────────────┐
│     HTTP Request From Client        │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Flask Request Handler             │
│   @app.route('/api/<path>')         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   proxy_request() Function          │
│   - Parse request                   │
│   - Extract model name              │
│   - Validate with each instance     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ OllamaInstanceManager               │
│ - Rotate through instances          │
│ - Track current index               │
├─────────────────────────────────────┤
│ Instance 1: http://localhost:11434  │
│ Instance 2: http://localhost:11435  │
│ Instance 3: http://localhost:11436  │
└─────────────────────────────────────┘
```

### 2. Instance Management Layer

**Class**: `OllamaInstanceManager`

Responsibilities:
- Parse port configuration (single ports and ranges)
- Manage instance list in memory
- Track current instance index for round-robin rotation
- Reset index for each new request

```python
class OllamaInstanceManager:
    def __init__(self, ports_config: str)
    def _parse_ports(self, ports_config: str) -> List[str]
    def get_next_instance(self) -> str
    def reset_to_start(self)
    def get_all_instances(self) -> List[str]
```

### 3. Failover Logic

The `proxy_request()` function implements the failover strategy:

```
1. Parse incoming request
   ├─ Get request body (POST/PUT)
   ├─ Extract model name
   └─ Determine HTTP method

2. Initialize failover
   ├─ Reset instance index to 0
   ├─ Set last_error to None
   └─ Prepare for retry loop

3. Failover Loop (iterate through all instances)
   ├─ Get next instance URL
   ├─ Check model if needed
   │  ├─ Call check_model_exists()
   │  └─ Pull if missing via pull_model()
   ├─ Forward request to instance
   ├─ Evaluate response
   │  ├─ Success (2xx) → Return response ✓
   │  ├─ Failover Error → Try next instance
   │  │  (429, 403, 402, 500-505)
   │  └─ Other errors → Continue to next
   └─ On timeout/connection error → Try next

4. All instances failed
   └─ Return 503 with error details
```

## Data Flow

### Request Flow for Generation

```
Client Request
    ↓
POST /api/generate {"model": "llama2", "prompt": "..."}
    ↓
Flask Router
    ↓
proxy_request("/api/generate", "POST")
    ↓
Parse JSON body
    ↓
Extract model: "llama2"
    ↓
OllamaInstanceManager.reset_to_start()
    ↓
Loop through instances:
    ├─ Instance 1 (http://localhost:11434)
    │  ├─ Check: does "llama2" exist?
    │  ├─ No: Pull model
    │  ├─ Success: Forward request
    │  ├─ Response: HTTP 200
    │  └─ Return to client ✓
    └─ (If failed, try Instance 2, etc.)
```

### Error Handling Flow

```
Request to Instance 1
    ↓
Receive Response
    ↓
Check Status Code
    ├─ 2xx (Success)
    │  └─ Return to client
    ├─ 429 (Rate Limited)
    │  └─ Try next instance
    ├─ 500 (Server Error)
    │  └─ Try next instance
    ├─ Timeout/Connection Error
    │  └─ Try next instance
    │  ...
    └─ All failed
       └─ Return 503 Service Unavailable
```

## Configuration

### Environment Variables

```
OLLAMA_PORTS    - Instance port configuration (required)
HOST            - Bind address (default: 0.0.0.0)
PORT            - Server port (default: 8000)
DEBUG           - Debug logging (default: False)
```

### Port Configuration Format

```
"11434"              → Single port
"11434,11435"        → Multiple ports
"11434-11436"        → Port range
"11434-11436,11440"  → Mixed format
```

Parsing logic converts these into:
```python
[
    "http://localhost:11434",
    "http://localhost:11435",
    "http://localhost:11436",
    "http://localhost:11440"
]
```

## Request Handling

### Supported Endpoints

All `/api/*` endpoints are proxied:

```
GET  /api/tags                   - List available models
POST /api/generate               - Generate text
POST /api/pull                   - Pull a model
POST /api/chat                   - Chat endpoint
POST /api/embeddings             - Create embeddings
DELETE /api/delete               - Delete model
... (all Ollama API endpoints)
```

### Request Methods

| Method | Support | Notes |
|--------|---------|-------|
| GET    | ✓       | Simple proxy |
| POST   | ✓       | Parse body, extract model |
| PUT    | ✓       | Parse body |
| DELETE | ✓       | No body parsing |

### Streaming Responses

For streaming endpoints (generate with `"stream": true`):

```python
def generate():
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            yield chunk

return Response(
    stream_with_context(generate()),
    headers=dict(response.headers)
)
```

## Model Management

### Model Existence Checking

```python
def check_model_exists(base_url, model):
    GET /api/tags → {"models": [...]}
    Extract model names from response
    Check if requested model is in list
```

### Model Pulling

```python
def pull_model(base_url, model):
    POST /api/pull {"name": model}
    Stream response (for progress updates)
    Return success/failure
```

The pull mechanism:
1. Detects missing model
2. Initiates pull request
3. Waits for pull to complete (up to 5 minutes)
4. Retries request on pull instance
5. Falls back to next instance if pull fails

## Health Monitoring

### Health Check Endpoint

```
GET /health → {
    "status": "healthy|unhealthy",
    "healthy_instances": 3,
    "total_instances": 4,
    "instance_status": {
        "http://localhost:11434": "healthy",
        "http://localhost:11435": "healthy",
        "http://localhost:11436": "healthy",
        "http://localhost:11437": "error 503"
    }
}
```

### Instance Probing

```python
def get_health():
    for each instance:
        try:
            GET /api/tags with 2s timeout
            if 200: instance_status = "healthy"
        except:
            instance_status = "error {code}"
    return aggregate status
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Parse ports | O(n) | n = number of ports |
| Get next instance | O(1) | Modulo operation |
| Forward request | O(1) | Direct HTTP call |
| Failover loop | O(m) | m = number of instances |

### Space Complexity

| Structure | Space | Notes |
|-----------|-------|-------|
| Instance list | O(m) | m = number of instances |
| Request context | O(1) | Per request |
| Health cache | O(m) | Per health check |

### Timeouts

| Operation | Timeout | Rationale |
|-----------|---------|-----------|
| /api/tags check | 5s | Quick check |
| /api/pull | 300s | Model download |
| /api/generate | 300s | Generation time |
| Other endpoints | 30s | Default |

## Security Model

### Request Isolation

- Each request gets fresh instance list
- No state sharing between requests
- No caching of credentials

### Error Handling

- Errors don't reveal internal state
- Timeouts handled gracefully
- Connection errors caught

### Docker Security

- Non-root user (ollamarama)
- Read-only filesystem option available
- Health checks verify functionality
- Resource limits configurable

## Extensions and Future Design

### Planned Enhancements

1. **Load Balancing**
   - Weighted round-robin
   - Least-loaded selection
   - Response time based

2. **Caching Layer**
   - Cache /api/tags results
   - Cache model existence checks
   - Configurable TTL

3. **Metrics Collection**
   - Request count per instance
   - Latency tracking
   - Error rate monitoring
   - Prometheus export

4. **Advanced Features**
   - Request queuing
   - Priority scheduling
   - Rate limiting per model
   - API key authentication

### Extensibility Points

The architecture supports additions:

```python
# Add new reliability feature
class CircuitBreaker:
    def __init__(self, instance, failure_threshold):
        # Track failures per instance
        # Temporarily disable failing instances

# Add metrics
class MetricsCollector:
    def record_request(instance, method, status, latency):
        # Record metrics
        # Export to Prometheus

# Add caching
class ModelCache:
    def get_models(instance, ttl=300):
        # Cache model lists
        # Reduce /api/tags calls
```

## Deployment Architecture

### Docker Strategy

```
┌──────────────────┐
│ GitHub Actions   │
│ (CI/CD)          │
└────────┬─────────┘
         │
         ├─→ Tests
         │
         ├─→ Docker Build
         │
         └─→ GHCR Push
              │
              ▼
         ┌──────────────┐
         │ GHCR Registry│
         └────┬─────────┘
              │
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
Docker Host 1       Docker Host 2
  (OllamaRama)        (OllamaRama)
    │                    │
    ├─→ Ollama 1         ├─→ Ollama 1
    ├─→ Ollama 2         ├─→ Ollama 2
    └─→ Ollama 3         └─→ Ollama 3
```

### Kubernetes Architecture

```
┌──────────────────────────────────┐
│     Kubernetes Cluster           │
├──────────────────────────────────┤
│                                  │
│ ┌────────────────────────────┐  │
│ │ Service (LoadBalancer)     │  │
│ │ Port: 8000                 │  │
│ └────────┬───────────────────┘  │
│          │                       │
│   ┌──────┼──────┐               │
│   │      │      │               │
│   ▼      ▼      ▼               │
│ Pod1   Pod2   Pod3 (Replicas)   │
│ │      │      │                 │
│ └──────┴──────┴─ Ollama Ports   │
└──────────────────────────────────┘
```

## Logging and Observability

### Log Levels

```python
logger.debug()   # Detailed diagnostics
logger.info()    # General information
logger.warning() # Recoverable issues
logger.error()   # Non-recoverable issues
```

### Key Log Points

1. **Initialization**: "Initialized with N instances"
2. **Request**: "Attempt N: METHOD URL"
3. **Model Check**: "Model found|not found"
4. **Pullback**: "Pulling model X on Y"
5. **Failover**: "Got error CODE, trying next"
6. **Complete**: Returned response OR "All instances failed"

---

For implementation details, see [DEVELOPMENT.md](DEVELOPMENT.md).
For deployment scenarios, see [DEPLOYMENT.md](DEPLOYMENT.md).
