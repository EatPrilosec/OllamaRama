# Deployment Guide for OllamaRama

This guide covers various deployment scenarios for OllamaRama.

## Prerequisites

- Docker and Docker Compose
- GitHub account (for GitHub Container Registry)
- Linux server or Docker host
- Ollama instances running on specified ports

## GitHub Container Registry (GHCR)

### Automatic Deployment via GitHub Actions

The repository includes automatic CI/CD via GitHub Actions.

**Steps:**

1. **Create GitHub Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/OllamaRama.git
   git push -u origin main
   ```

2. **Enable GitHub Actions** (usually enabled by default)
   - Go to Settings → Actions → Allow all actions

3. **Push to trigger build**
   ```bash
   git push origin main
   ```
   This automatically builds and pushes to `ghcr.io/YOUR_USERNAME/ollamarama`

4. **Deploy from GHCR**
   ```bash
   docker pull ghcr.io/YOUR_USERNAME/ollamarama:latest
   docker run -d \
     --name OllamaRama \
     -p 8000:8000 \
     -e OLLAMA_PORTS="11434-11436" \
     ghcr.io/YOUR_USERNAME/ollamarama:latest
   ```

### Manual Push to GHCR

```bash
# Authenticate
echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin

# Build and tag
docker build -t ghcr.io/USERNAME/ollamarama:latest .

# Push
docker push ghcr.io/USERNAME/ollamarama:latest
```

## Docker Hub Deployment

### Setup Secrets

1. Go to Settings → Secrets and variables → Actions
2. Add:
   - `DOCKER_USERNAME` - Your Docker Hub username
   - `DOCKER_PASSWORD` - Your Docker Hub token (not password)

### Update Workflow

Edit `.github/workflows/docker-build.yml` to add Docker Hub login:

```yaml
- name: Log in to Docker Hub
  if: github.event_name != 'pull_request'
  uses: docker/login-action@v2
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}

- name: Build and push
  # ... use docker.io/${{ secrets.DOCKER_USERNAME }}/ollamarama
```

## Single Server Deployment

### Using Docker Compose

```bash
# SSH into server
ssh user@your-server.com

# Clone repository
git clone https://github.com/YOUR_USERNAME/OllamaRama.git
cd OllamaRama

# Configure environment
cp .env.example .env
nano .env
# Edit OLLAMA_PORTS to match your instances

# Start service
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

### Using Systemd Service

Create `/etc/systemd/system/ollamarama.service`:

```ini
[Unit]
Description=OllamaRama Ollama API Failover Proxy
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=unless-stopped
RestartSec=10

ExecStart=/usr/bin/docker run --rm \
  --name OllamaRama \
  -p 8000:8000 \
  -e OLLAMA_PORTS=11434-11436 \
  -e DEBUG=false \
  --network host \
  ghcr.io/YOUR_USERNAME/ollamarama:latest

ExecStop=/usr/bin/docker stop OllamaRama

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ollamarama
sudo systemctl start ollamarama
sudo systemctl status ollamarama
```

## Kubernetes Deployment

### Helm Chart Option

Create `helm/ollamarama/Chart.yaml`:

```yaml
apiVersion: v2
name: ollamarama
description: Ollama API Failover Proxy
type: application
version: 1.0.0
appVersion: 1.0.0
```

Create `helm/ollamarama/values.yaml`:

```yaml
image:
  repository: ghcr.io/YOUR_USERNAME/ollamarama
  tag: latest
  pullPolicy: IfNotPresent

replicaCount: 2

service:
  type: ClusterIP
  port: 8000
  targetPort: 8000

ingress:
  enabled: false
  # className: "nginx"
  # hosts:
  #   - host: ollama.example.com
  #     paths:
  #       - path: /

resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

env:
  - name: OLLAMA_PORTS
    value: "11434-11436"
  - name: DEBUG
    value: "false"

healthCheck:
  enabled: true
  initialDelaySeconds: 10
  periodSeconds: 30
```

Create `helm/ollamarama/templates/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ollamarama.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: ollamarama
  template:
    metadata:
      labels:
        app: ollamarama
    spec:
      containers:
      - name: ollamarama
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.service.targetPort }}
        env:
        {{ range .Values.env }}
        - name: {{ .name }}
          value: "{{ .value }}"
        {{ end }}
        resources:
          {{ toYaml .Values.resources | nindent 12 }}
        livenessProbe:
          httpGet:
            path: /health
            port: {{ .Values.service.targetPort }}
          initialDelaySeconds: {{ .Values.healthCheck.initialDelaySeconds }}
          periodSeconds: {{ .Values.healthCheck.periodSeconds }}
```

Deploy with Helm:

```bash
helm install ollamarama ./helm/ollamarama
```

### Direct Kubernetes YAML

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollamarama-config
data:
  OLLAMA_PORTS: "11434-11436"
  DEBUG: "false"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollamarama
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ollamarama
  template:
    metadata:
      labels:
        app: ollamarama
    spec:
      containers:
      - name: ollamarama
        image: ghcr.io/YOUR_USERNAME/ollamarama:latest
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: ollamarama-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30

---
apiVersion: v1
kind: Service
metadata:
  name: ollamarama
spec:
  selector:
    app: ollamarama
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

Deploy:

```bash
kubectl apply -f ollamarama.yaml
kubectl get svc ollamarama
```

## Docker Swarm Deployment

```yaml
# docker-stack.yml
version: '3.8'

services:
  ollamarama:
    image: ghcr.io/YOUR_USERNAME/ollamarama:latest
    ports:
      - "8000:8000"
    environment:
      OLLAMA_PORTS: "11434-11436"
      DEBUG: "false"
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == worker
      update_config:
        parallelism: 1
        delay: 10s
      rollback_config:
        parallelism: 1
        delay: 10s
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  default:
    driver: overlay
```

Deploy to Swarm:

```bash
docker stack deploy -c docker-stack.yml ollamarama
docker stack services ollamarama
```

## Reverse Proxy Setup

### Nginx

```nginx
upstream ollamarama {
    server localhost:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name ollama.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ollama.example.com;

    ssl_certificate /etc/letsencrypt/live/ollama.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ollama.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://ollamarama;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_read_timeout 3600s;
    }

    location ~ ^/(health|status)$ {
        proxy_pass http://ollamarama;
        access_log off;
    }
}
```

### Apache

```apache
<VirtualHost *:443>
    ServerName ollama.example.com
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/ollama.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/ollama.example.com/privkey.pem

    ProxyPreserveHost On
    ProxyPass / http://localhost:8000/ nocanon
    ProxyPassReverse / http://localhost:8000/

    # For streaming responses
    SetEnv proxy-sendcl 1
    SetEnv proxy-sendchunked 1
</VirtualHost>
```

## Monitoring & Logging

### Health Check Integration

```bash
# With Prometheus
curl http://localhost:8000/health | jq '.healthy_instances'

# With Grafana - use HTTP datasource to /health
```

### Log Aggregation

### With ELK Stack

```yaml
services:
  ollamarama:
    # ... existing config ...
    logging:
      driver: "awslogs"
      options:
        awslogs-group: "/ecs/ollamarama"
        awslogs-region: "us-east-1"
        awslogs-stream-prefix: "ecs"
```

### With Syslog

```bash
docker run \
  --log-driver syslog \
  --log-opt syslog-address=udp://localhost:514 \
  ghcr.io/YOUR_USERNAME/ollamarama:latest
```

## Security Checklist

- [ ] Use HTTPS with valid certificates
- [ ] Configure rate limiting
- [ ] Restrict network access to known IPs
- [ ] Use firewall rules
- [ ] Run container as non-root user (already done)
- [ ] Regularly update base images and dependencies
- [ ] Monitor resource usage
- [ ] Enable audit logging
- [ ] Use secrets management for sensitive data
- [ ] Implement authentication if needed

## Backup & Disaster Recovery

```bash
# Backup container config
docker-compose config > backup-$(date +%s).yml

# Export image
docker save ghcr.io/YOUR_USERNAME/ollamarama:latest > ollamarama-backup.tar

# Export and compress
docker save ghcr.io/YOUR_USERNAME/ollamarama:latest | gzip > ollamarama-backup.tar.gz
```

## Troubleshooting

### Container won't start
```bash
docker logs OllamaRama
# Check: OLLAMA_PORTS env var set
# Check: Ollama instances running on specified ports
```

### High memory usage
```bash
# Limit memory
docker update --memory 512m OllamaRama

# Check what's consuming
docker stats OllamaRama
```

### Slow responses
```bash
# Check instance health
curl http://localhost:8000/health | jq

# Check Ollama instance metrics
docker exec -it ollama_container nvidia-smi
```

---

For additional help, see [README.md](README.md) or open an issue on GitHub.
