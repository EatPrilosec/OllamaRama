#!/bin/bash

# OllamaRama Quick Start Script
# This script helps you get OllamaRama running quickly

set -e

echo "================================"
echo "OllamaRama Quick Start"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"
echo ""

# Ask user for port configuration
echo "Port Configuration"
echo "=================="
echo ""
echo "Enter the ports/port ranges where Ollama instances are running."
echo "Examples:"
echo "  - Single ports:     11434,11435,11436"
echo "  - Port range:       11434-11436"
echo "  - Mixed:            11434-11436,11440,11442-11443"
echo ""
read -p "Enter OLLAMA_PORTS [11434-11436]: " OLLAMA_PORTS
OLLAMA_PORTS=${OLLAMA_PORTS:-"11434-11436"}

echo ""
echo "Proxy Port Configuration"
echo "========================"
read -p "Enter proxy port [8000]: " PROXY_PORT
PROXY_PORT=${PROXY_PORT:-"8000"}

echo ""
echo "Debug Mode"
echo "=========="
read -p "Enable debug mode? (y/n) [n]: " DEBUG_MODE
DEBUG_MODE=${DEBUG_MODE:-"n"}
if [ "$DEBUG_MODE" = "y" ] || [ "$DEBUG_MODE" = "Y" ]; then
    DEBUG="True"
else
    DEBUG="False"
fi

# Create .env file
echo ""
echo "Creating .env file..."
cat > .env << EOF
# OllamaRama Configuration
OLLAMA_PORTS=$OLLAMA_PORTS
HOST=0.0.0.0
PORT=$PROXY_PORT
DEBUG=$DEBUG
EOF

echo -e "${GREEN}✓ .env file created${NC}"
echo ""

# Show configuration
echo "Configuration Summary"
echo "===================="
echo "OLLAMA_PORTS: $OLLAMA_PORTS"
echo "Proxy Port:   $PROXY_PORT"
echo "Debug Mode:   $DEBUG"
echo ""

# Ask if user has Ollama running on specified ports
read -p "Do you have Ollama instances running on the specified ports? (y/n) [y]: " OLLAMA_RUNNING
OLLAMA_RUNNING=${OLLAMA_RUNNING:-"y"}

if [ "$OLLAMA_RUNNING" != "y" ] && [ "$OLLAMA_RUNNING" != "Y" ]; then
    echo ""
    echo -e "${YELLOW}Note: You need to start Ollama on the specified ports before starting OllamaRama${NC}"
    echo ""
    echo "To start Ollama on multiple ports, you can:"
    echo "1. Run in Docker:"
    echo "   docker run -d -e OLLAMA_HOST=127.0.0.1:11434 ollama/ollama"
    echo "   docker run -d -e OLLAMA_HOST=127.0.0.1:11435 ollama/ollama"
    echo ""
    echo "2. Or start multiple instances manually with different OLLAMA_HOST"
    echo ""
fi

# Ask if user wants to start now
echo ""
read -p "Start OllamaRama now? (y/n) [y]: " START_NOW
START_NOW=${START_NOW:-"y"}

if [ "$START_NOW" = "y" ] || [ "$START_NOW" = "Y" ]; then
    echo ""
    echo "Building Docker image..."
    docker-compose build
    
    echo ""
    echo "Starting OllamaRama..."
    docker-compose up -d
    
    echo ""
    echo "Waiting for service to be ready..."
    sleep 3
    
    echo ""
    echo "Checking service health..."
    if curl -s http://localhost:$PROXY_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OllamaRama is running!${NC}"
        echo ""
        echo "Health check:"
        curl -s http://localhost:$PROXY_PORT/health | python -m json.tool 2>/dev/null || curl -s http://localhost:$PROXY_PORT/health
        echo ""
        echo "API endpoint: http://localhost:$PROXY_PORT/api/"
        echo ""
        echo "Test with:"
        echo "  curl http://localhost:$PROXY_PORT/api/tags"
        echo "  curl http://localhost:$PROXY_PORT/health"
    else
        echo -e "${RED}✗ Service failed to start${NC}"
        echo ""
        echo "Check logs with: docker-compose logs -f"
        exit 1
    fi
else
    echo ""
    echo "To start OllamaRama later, run:"
    echo "  docker-compose up -d"
    echo ""
    echo "To check status:"
    echo "  docker-compose ps"
    echo "  docker-compose logs -f"
    echo ""
fi

echo ""
echo "================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Visit the documentation: less README.md"
echo "2. Test the API: curl http://localhost:$PROXY_PORT/health"
echo "3. For more info: cat DEPLOYMENT.md"
echo ""
