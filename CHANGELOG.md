# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-26

### Added

- Initial release of OllamaRama
- Ollama API failover proxy with multi-instance support
- Automatic error detection and failover (429, 403, 402, 500, 502, 503, 504, 505)
- Port and port range configuration support
- Automatic model pulling when model not found on instance
- Health check endpoint with instance status
- Docker and Docker Compose setup
- GitHub Actions CI/CD workflows
- Comprehensive documentation
- Unit tests for port parsing and failover logic
- Development guides and deployment guides
- MIT License

### Features

- Multi-instance Ollama proxy with configurable failover
- Automatic round-robin instance rotation
- Model existence checking per instance
- On-demand model pulling via API
- Streaming response support
- Detailed logging for debugging and monitoring
- Non-root Docker user for security
- Production-ready Gunicorn configuration
- Health check with per-instance status

### Documentation

- Complete README with usage examples
- Deployment guide covering multiple scenarios
- Development guide for contributors
- API usage examples and configurations

## [Unreleased]

### Planned Features

- [ ] Load balancing strategies (least-loaded, weighted)
- [ ] Request rate limiting per model
- [ ] Prometheus metrics export
- [ ] WebSocket support for persistent connections
- [ ] Advanced authentication (API keys, JWT)
- [ ] Configuration hot-reload without restart
- [ ] Multi-region failover support
- [ ] Request queueing and priority
- [ ] Response caching for non-generative endpoints
- [ ] Custom error handling and transformations

### Known Issues

- None currently

---

## How to Use This Changelog

- Add new changes under the "Unreleased" section
- Use these categories: Added, Changed, Deprecated, Removed, Fixed, Security
- When making a release:
  1. Update the version number
  2. Change `[Unreleased]` to the new version and date
  3. Create a new Empty `[Unreleased]` section
  4. Commit with message: `chore: release v1.x.x`

### Examples of Change Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Security issue fixes
