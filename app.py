"""
OllamaRama: Ollama API Failover Proxy
Intercepts Ollama API requests and provides failover capabilities across multiple instances.
"""

import os
import re
import requests
import logging
from typing import List, Tuple
from flask import Flask, request, Response, stream_with_context
from urllib.parse import urljoin
from functools import wraps
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Error codes that trigger failover
FAILOVER_ERRORS = {429, 403, 402, 500, 502, 503, 504, 505}


class OllamaInstanceManager:
    """Manages multiple Ollama instances and failover logic"""
    
    def __init__(self, ports_config: str):
        """
        Initialize with port configuration string.
        Format: "11430-11433,11435,11440-11442"
        """
        self.instances = self._parse_ports(ports_config)
        self.current_index = 0
        logger.info(f"Initialized with {len(self.instances)} instances: {self.instances}")
    
    def _parse_ports(self, ports_config: str) -> List[str]:
        """Parse port configuration string into list of URLs"""
        if not ports_config:
            raise ValueError("OLLAMA_PORTS configuration is required")
        
        instances = []
        for part in ports_config.split(','):
            part = part.strip()
            if '-' in part:
                # Handle port range
                start, end = part.split('-')
                start, end = int(start.strip()), int(end.strip())
                for port in range(start, end + 1):
                    instances.append(f"http://localhost:{port}")
            else:
                # Single port
                port = int(part.strip())
                instances.append(f"http://localhost:{port}")
        
        if not instances:
            raise ValueError("No valid ports found in OLLAMA_PORTS configuration")
        
        return instances
    
    def get_next_instance(self) -> str:
        """Get the next instance in the failover chain"""
        instance = self.instances[self.current_index % len(self.instances)]
        self.current_index += 1
        return instance
    
    def reset_to_start(self):
        """Reset to the first instance (for next request)"""
        self.current_index = 0
    
    def get_all_instances(self) -> List[str]:
        """Get all instances"""
        return self.instances


def initialize_manager():
    """Initialize the instance manager from environment"""
    ports_config = os.getenv('OLLAMA_PORTS', '')
    if not ports_config:
        logger.error("OLLAMA_PORTS environment variable not set")
        raise ValueError("OLLAMA_PORTS environment variable is required")
    return OllamaInstanceManager(ports_config)


try:
    manager = initialize_manager()
except Exception as e:
    logger.error(f"Failed to initialize manager: {e}")
    manager = None


def check_model_exists(base_url: str, model: str) -> bool:
    """Check if a model exists on an instance"""
    try:
        response = requests.get(
            urljoin(base_url, '/api/tags'),
            timeout=None
        )
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '').split(':')[0] for m in models]
            return model in model_names or any(model in name for name in model_names)
        return False
    except Exception as e:
        logger.error(f"Error checking models on {base_url}: {e}")
        return False


def pull_model(base_url: str, model: str) -> bool:
    """Pull a model from an instance"""
    try:
        logger.info(f"Pulling model {model} from {base_url}")
        response = requests.post(
            urljoin(base_url, '/api/pull'),
            json={'name': model},
            timeout=None,  # Indefinite timeout - wait until model is pulled
            stream=True
        )
        
        # For streaming response, just consume it
        for line in response.iter_lines():
            if line:
                logger.debug(f"Pull progress: {line}")
        
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error pulling model {model} from {base_url}: {e}")
        return False


def extract_model_from_request(data: dict) -> str:
    """Extract model name from request JSON"""
    return data.get('model', '')


def proxy_request(path: str, method: str = 'GET'):
    """
    Proxy a request with failover logic.
    Returns (response, status_code)
    """
    if not manager:
        return Response("Manager not initialized", status=500), 500
    
    try:
        # Parse request data
        data = {}
        if method in ['POST', 'PUT'] and request.data:
            try:
                data = request.get_json()
            except:
                data = {}
        
        model = extract_model_from_request(data)
        
        # Reset for this request
        manager.reset_to_start()
        
        # Try each instance
        last_error = None
        for attempt in range(len(manager.instances)):
            instance = manager.get_next_instance()
            url = urljoin(instance, path)
            
            try:
                logger.info(f"Attempt {attempt + 1}: {method} {url} from {instance}")
                
                # Check if model needs to be pulled
                if model and method == 'POST' and 'generate' in path:
                    if not check_model_exists(instance, model):
                        logger.info(f"Model {model} not found on {instance}, attempting to pull...")
                        if pull_model(instance, model):
                            logger.info(f"Successfully pulled {model} on {instance}")
                        else:
                            logger.warning(f"Failed to pull {model} on {instance}, trying next instance")
                            last_error = "Model pull failed"
                            continue
                
                # Make the request
                if method == 'GET':
                    response = requests.get(
                        url,
                        params=request.args,
                        timeout=None,
                        stream=True
                    )
                elif method == 'POST':
                    response = requests.post(
                        url,
                        json=data,
                        timeout=None,  # Indefinite timeout - wait for response
                        stream=True
                    )
                elif method == 'PUT':
                    response = requests.put(
                        url,
                        json=data,
                        timeout=None,
                        stream=True
                    )
                elif method == 'DELETE':
                    response = requests.delete(
                        url,
                        timeout=None
                    )
                else:
                    continue
                
                # Check for failover errors
                if response.status_code in FAILOVER_ERRORS:
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(f"Got error {response.status_code} from {instance}, trying next...")
                    continue
                
                # Success! Stream the response
                if method == 'DELETE':
                    return Response(response.content, status=response.status_code), response.status_code
                else:
                    # For streaming responses (generate endpoint)
                    def generate():
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                yield chunk
                    
                    return Response(
                        stream_with_context(generate()),
                        status=response.status_code,
                        headers=dict(response.headers)
                    ), response.status_code
            
            except requests.Timeout:
                last_error = "Timeout"
                logger.warning(f"Timeout from {instance}, trying next...")
                continue
            except requests.ConnectionError as e:
                last_error = f"Connection error: {e}"
                logger.warning(f"Connection error from {instance}: {e}")
                continue
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error proxying to {instance}: {e}")
                continue
        
        # All instances failed
        error_msg = f"All instances failed. Last error: {last_error}"
        logger.error(error_msg)
        return Response(json.dumps({"error": error_msg}), status=503), 503
    
    except Exception as e:
        logger.error(f"Unexpected error in proxy_request: {e}")
        return Response(json.dumps({"error": str(e)}), status=500), 500


@app.route('/api/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(subpath):
    """Proxy all /api/* requests"""
    path = f"/api/{subpath}"
    method = request.method
    response, status = proxy_request(path, method)
    return response


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    if not manager:
        return Response(json.dumps({"status": "unhealthy", "reason": "Manager not initialized"}), status=503)
    
    healthy_instances = 0
    instance_status = {}
    
    for instance in manager.get_all_instances():
        try:
            response = requests.get(f"{instance}/api/tags", timeout=None)
            if response.status_code == 200:
                healthy_instances += 1
                instance_status[instance] = "healthy"
            else:
                instance_status[instance] = f"error {response.status_code}"
        except Exception as e:
            instance_status[instance] = f"error {str(e)}"
    
    return Response(
        json.dumps({
            "status": "healthy" if healthy_instances > 0 else "unhealthy",
            "healthy_instances": healthy_instances,
            "total_instances": len(manager.get_all_instances()),
            "instance_status": instance_status
        }),
        status=200 if healthy_instances > 0 else 503
    )


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with basic info"""
    return Response(json.dumps({
        "name": "OllamaRama",
        "description": "Ollama API Failover Proxy",
        "version": "1.0.0",
        "endpoints": {
            "/api/*": "Proxy to Ollama API",
            "/health": "Health check",
            "/": "This info"
        }
    }), mimetype='application/json')


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return Response(json.dumps({"error": "Not found"}), status=404)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return Response(json.dumps({"error": "Internal server error"}), status=500)


if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    if manager:
        logger.info(f"Starting OllamaRama on {host}:{port}")
        app.run(host=host, port=port, debug=debug, threaded=True)
    else:
        logger.error("Cannot start: Manager initialization failed")
        exit(1)
