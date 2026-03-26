# Development Guide for OllamaRama

This guide covers how to develop and contribute to OllamaRama.

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- Docker (for testing images)
- Virtual environment tool (venv recommended)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/OllamaRama.git
cd OllamaRama

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock black flake8 mypy

# Copy and configure environment
cp .env.example .env
# Edit .env with your test port configuration
```

### Running Locally

```bash
# Development mode with Flask
export FLASK_APP=app.py
export FLASK_ENV=development
export OLLAMA_PORTS=11434-11436
python app.py

# Or directly
OLLAMA_PORTS=11434-11436 DEBUG=True python app.py
```

The app will be available at `http://localhost:8000`

## Project Structure

```
OllamaRama/
├── app.py                      # Main application
├── requirements.txt            # Dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Local docker setup
├── tests/
│   ├── __init__.py
│   └── test_app.py            # Unit tests
├── .github/workflows/
│   ├── docker-build.yml       # CI/CD pipeline
│   └── tests.yml              # Test runner
├── .env.example               # Configuration template
└── README.md                  # User documentation
```

## Testing

### Running Tests

```bash
# Basic test run
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html

# Specific test
pytest tests/test_app.py::TestPortParsing::test_parse_single_ports -v

# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw
```

### Writing Tests

```python
# tests/test_feature.py
import pytest
from app import SomeClass

def test_feature():
    """Test description"""
    result = SomeClass.method()
    assert result == expected_value

class TestFeatureGroup:
    """Group related tests"""
    
    def test_case_1(self):
        assert True
    
    def test_case_2(self, mocker):
        """Use pytest-mock for mocking"""
        mock_func = mocker.patch('app.some_function')
        # test code
```

### Test Coverage Goals

- Target: >80% code coverage
- Always test error paths
- Mock external API calls
- Use fixtures for common setup

## Code Style

### Format with Black

```bash
# Format all Python files
black .

# Check formatting
black --check .
```

### Lint with Flake8

```bash
# Check code style
flake8 .

# Configuration in .flake8 or setup.cfg
```

### Type Checking with MyPy

```bash
# Check type hints
mypy app.py

# Configuration in mypy.ini
```

### PEP 8 Standards

- Line length: 88 characters (Black default)
- 4 spaces for indentation
- Two blank lines between functions
- One blank line between methods

## Making Changes

### Feature Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes**
   ```bash
   # Edit files
   vim app.py
   
   # Run tests
   pytest tests/ -v
   
   # Check code style
   black . && flake8 . && mypy app.py
   ```

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add my feature"
   
   # Commit message conventions:
   # feat: new feature
   # fix: bug fix
   # docs: documentation
   # refactor: code refactoring
   # test: test improvements
   # chore: maintenance
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub
   ```

## Key Components

### OllamaInstanceManager

Manages failover logic and instance rotation.

```python
# Usage
manager = OllamaInstanceManager("11434-11436,11440")

# Get next instance
instance = manager.get_next_instance()  # "http://localhost:11434"

# Reset for new request
manager.reset_to_start()

# Get all instances
instances = manager.get_all_instances()
```

**To enhance**:
- Add load balancing strategies
- Implement instance health caching
- Add metrics collection

### Proxy Request Function

Handles request routing and failover.

```python
def proxy_request(path: str, method: str = 'GET'):
    """
    1. Parse request data
    2. Extract model name
    3. Try each instance in order
    4. Check/pull model if needed
    5. Forward request
    6. Return response or try next instance
    """
```

**To enhance**:
- Add request rate limiting
- Implement request queueing
- Add response caching
- Support streaming improvements

## Common Tasks

### Adding a New Endpoint

```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    """Proxy new endpoint"""
    return proxy_request('/api/new-endpoint', 'POST')
```

### Adding Configuration Option

1. Add to `.env.example`
2. Read in code with `os.getenv('VAR_NAME', 'default')`
3. Add to documentation

### Adding Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log at different levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Testing with Docker

```bash
# Build image
docker build -t ollamarama:test .

# Run tests in container
docker run --rm \
  -e OLLAMA_PORTS=11434-11436 \
  ollamarama:test \
  pytest tests/ -v
```

## Performance Optimization

### Profiling

```python
# Use cProfile for profiling
python -m cProfile -s cumulative app.py

# Or use line_profiler
pip install line_profiler

# Decorate function with @profile and run:
kernprof -l -v app.py
```

### Memory Optimization

```bash
# Monitor memory usage
docker stats OllamaRama

# Check Python memory
python -m memory_profiler app.py
```

## Debugging

### Using Python Debugger

```python
import pdb

# In code:
pdb.set_trace()

# Then in Python shell:
# n (next line)
# s (step into)
# c (continue)
# l (list)
# p variable (print)
```

### Using Flask Debugger

```bash
FLASK_ENV=development FLASK_DEBUG=True python app.py
```

### Docker Debugging

```bash
# Interactive shell in running container
docker exec -it OllamaRama /bin/bash

# View logs
docker logs -f OllamaRama

# Full container inspection
docker inspect OllamaRama
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function(param1: str, param2: int) -> bool:
    """Brief description.
    
    Longer description if needed. Explain the purpose, behavior,
    and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is wrong
    """
```

### Updating README

- Keep README.md up to date
- Add examples for new features
- Document new configuration options
- Update API documentation

## Submitting Changes

### Before Submitting PR

```bash
# Ensure all tests pass
pytest tests/ -v

# Check code style
black . && flake8 . && mypy app.py

# Check Docker build
docker build -t ollamarama:test .

# Update version in code if needed
# Update CHANGELOG.md

# Ensure docs are updated
```

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Release Process

### Version Numbering

Follow Semantic Versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Creating Release

```bash
# Tag release
git tag v1.0.0

# Push tag to trigger GitHub Actions
git push origin v1.0.0

# GitHub Actions automatically:
# 1. Builds Docker image
# 2. Pushes to ghcr.io with v1.0.0 tag
# 3. Pushes latest tag
```

## Troubleshooting Development

### Import errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Tests failing

```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Run specific test with verbose output
pytest tests/test_file.py::TestClass::test_method -vv
```

### Docker build fails

```bash
# Check Docker logs
docker build -t test . -v

# Rebuild without cache
docker build --no-cache -t test .

# Check Dockerfile syntax
docker run --rm -i hadolint/hadolint < Dockerfile
```

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Requests Library](https://requests.readthedocs.io/)
- [Python Testing](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions](https://docs.github.com/en/actions)

## Community

- Report bugs via GitHub Issues
- Suggest features via GitHub Discussions
- Join the conversation in issues and PRs

---

Happy coding! 🚀
