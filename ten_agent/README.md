# Therapist TEN Agent - Docker Setup

This directory contains the TEN (Ten Agent Framework) implementation for the AI therapist, configured to be Docker-composeable like the AI Agents in the ten-framework.

## Quick Start

1. **Copy environment file and configure:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and settings
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the services:**
   - **API Server**: http://localhost:8080
   - **Graph Designer**: http://localhost:49483
   - **Demo Interface**: http://localhost:3002

## Services

### therapist_agent_dev
- **Image**: docker.theten.ai/ten-framework/ten_agent_build:0.6.11
- **Ports**: 8080 (API), 49483 (Graph Designer)
- **Volumes**: Mounts current directory for development
- **Purpose**: Development server with live code reloading

### therapist_agent_demo
- **Image**: ghcr.io/ten-framework/ten_agent_demo:0.10.6-19-g8ecacde4
- **Port**: 3002 (mapped to container's 3000)
- **Purpose**: Demo interface for testing the therapist agent

## Environment Variables

Required variables in `.env`:
- `SERVER_PORT`: API server port (default: 8080)
- `GRAPH_DESIGNER_SERVER_PORT`: Graph designer port (default: 49483)
- `LOG_PATH`: Path for logs (default: /tmp/ten_logs)
- `EMOTIV_APP_CLIENT_ID`: EMOTIV Cortex API client ID
- `EMOTIV_APP_CLIENT_SECRET`: EMOTIV Cortex API client secret
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI features)
- `HF_TOKEN`: Hugging Face API token

## Development

### Building Custom Images

1. **Build the therapist agent image:**
   ```bash
   docker build -t therapist-agent .
   ```

2. **Use custom image in docker-compose:**
   ```bash
   # In docker-compose.yml, change therapist_agent_dev image to:
   # image: therapist-agent:latest
   ```

### Local Development

For local development without Docker:

1. **Install dependencies:**
   ```bash
   ./scripts/install_deps_and_build.sh
   ```

2. **Run the agent:**
   ```bash
   ./bin/ten_agent
   ```

## Directory Structure

```
therapist/ten_agent/
├── docker-compose.yml      # Docker services configuration
├── Dockerfile             # Custom Docker image
├── .env.example          # Environment variables template
├── start-servers.sh      # Server startup script
├── examples/             # Agent configurations
│   └── therapist/        # Therapist-specific agent config
├── scripts/              # Build and utility scripts
└── ...                   # TEN framework files
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `.env` if 8080 or 49483 are in use
2. **Permission denied**: Ensure start-servers.sh is executable: `chmod +x start-servers.sh`
3. **Missing environment variables**: Copy `.env.example` to `.env` and fill in required values
4. **EMOTIV connection issues**: Verify EMOTIV credentials and headset connectivity

### Logs

View logs for debugging:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f therapist_agent_dev
```

### Interactive Debugging

```bash
# Access container shell
docker exec -it therapist_agent_dev bash

# Check running processes
docker exec therapist_agent_dev ps aux
```

## Advanced Configuration

### Custom Agent Configuration

To use a different agent configuration:

1. **Modify the Dockerfile:**
   ```dockerfile
   ARG USE_AGENT=examples/your_custom_agent
   ```

2. **Rebuild the image:**
   ```bash
   docker build -t therapist-agent-custom .
   ```

### Network Configuration

The services use a custom bridge network (`therapist_agent_network`) for inter-container communication. If you need to connect to external services, you can:

1. **Add external networks:**
   ```yaml
   networks:
     therapist_agent_network:
       external: true
   ```

2. **Or use host networking:**
   ```yaml
   network_mode: host
   ```

## Integration with EMOTIV EEG

The therapist agent is designed to work with EMOTIV Insight 2.0 EEG headset. Ensure:

1. EMOTIV Launcher is installed and running
2. Headset is connected and paired
3. EMOTIV API credentials are configured in `.env`
4. Network connectivity allows WebSocket connections to EMOTIV Cortex API