# Getting Started with ARKOS

This guide will help you set up and run ARKOS on your local machine or connect to the remote development server.

## Prerequisites

- Python 3.12 or higher
- Git
- SSH access to `ark.mit.edu` (for remote development)
- Docker (optional, for local SGLANG inference)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/SGIARK/ARKOS.git
cd ARKOS
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- `openai>=1.61.0` - Standardized inference engine communication
- `pyyaml>=6.0.2` - YAML configuration parsing
- `pydantic>=2.10.6` - Schema validation
- `requests>=2.32.3` - HTTP requests
- `fastapi>=0.115.0` - Web framework
- `uvicorn>=0.32.0` - ASGI server

## Development Options

You have two main options for running ARKOS:

### Option A: Local Development (Recommended for Testing)

Run everything locally on your machine.

#### Start Local SGLANG Inference Engine

If you have Docker and GPU access:

```bash
bash model_module/run.sh
```

This starts SGLANG with Qwen 2.5 on port 30000.

**Note:** If you don't have GPU access, you can use a smaller model or CPU mode. Alternatively, use Option B to connect to the remote server.

#### Start FastAPI Server

In a new terminal:

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python base_module/app.py
```

The server will run on `http://localhost:1111`.

#### Test the Server

In another terminal:

```bash
source venv/bin/activate
python base_module/main_interface.py
```

### Option B: Remote Development (Recommended for Production)

Connect to the remote server at `ark.mit.edu` where SGLANG is already running.

#### SSH Tunnel Setup

Create an SSH tunnel to access the remote SGLANG server:

```bash
ssh -N -L 8000:localhost:30000 jack.ark@ark.mit.edu
```

This command:
- `-N`: Don't execute remote commands (just forward ports)
- `-L 8000:localhost:30000`: Forward local port 8000 to remote port 30000
- Keeps the tunnel open in your terminal

**Alternative:** If you want to use the VLLM server (port 20000) instead:

```bash
ssh -N -L 8000:localhost:20000 jack.ark@ark.mit.edu
```

#### Configure App to Use Tunneled Port

Update `base_module/app.py` line 23 to use the tunneled port:

```python
# For SGLANG (port 30000) via tunnel:
llm = ArkModelLink(base_url="http://localhost:8000/v1")

# OR for VLLM (port 20000) via tunnel:
llm = ArkModelLink(base_url="http://localhost:8000/v1")  # if tunneled to 20000
```

#### Start FastAPI Server Locally

```bash
source venv/bin/activate
python base_module/app.py
```

The server will connect to the remote inference engine through the SSH tunnel.

## Remote Development with VSCode

You can develop directly on the remote server using VSCode Remote SSH:

1. Install the [Remote - SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) extension
2. Connect to `jack.ark@ark.mit.edu`
3. Open the project folder on the remote server
4. Develop as if you were working locally

See: https://code.visualstudio.com/docs/remote/ssh

## Port Configuration

| Service | Port | Description |
|---------|------|-------------|
| FastAPI Server | 1111 | Main ARKOS API server |
| SGLANG (Remote) | 30000 | SGLANG inference engine on remote server |
| VLLM (Remote) | 20000 | VLLM inference engine on remote server (nmorgan's) |
| SSH Tunnel (Local) | 8000 | Local port forwarded to remote inference engine |

## Troubleshooting

### FileNotFoundError: state_graph.yaml

If you get this error, the YAML path is relative and depends on where you run the script from.

**Fix:** Run the server from the project root:

```bash
cd /path/to/ARKOS
python base_module/app.py
```

Or update `app.py` line 21 to use an absolute path:

```python
import os
yaml_path = os.path.join(os.path.dirname(__file__), "..", "state_module", "state_graph.yaml")
flow = StateHandler(yaml_path=os.path.abspath(yaml_path))
```

### Connection Refused Errors

- **Port 1111:** Make sure the FastAPI server is running (`python base_module/app.py`)
- **Port 30000/20000:** Ensure SSH tunnel is active or SGLANG/VLLM is running
- **Port 8000:** Verify SSH tunnel command is running in a separate terminal

### Port Already in Use

Check what's using the port:

```bash
# Linux/Mac
ss -tuln | grep <port>
# or
lsof -i :<port>

# Windows
netstat -ano | findstr :<port>
```

## Project Structure

```
ARKOS/
├── agent_module/       # Agentic structure
├── base_module/        # Main interface (app.py, main_interface.py)
├── config_module/      # YAML configuration files
├── memory_module/       # Long-term memory and context management
├── model_module/       # Core LLM inference logic
│   └── run.sh          # SGLANG startup script
├── state_module/       # Agent state graphs
│   └── state_graph.yaml
├── tool_module/        # MCP compatibility
├── requirements.txt    # Python dependencies
└── README.md           # Project overview
```

## Development Workflow

1. **Pull latest changes:**
   ```bash
   git fetch origin
   git checkout main  # or your branch
   ```

2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes and test:**
   ```bash
   # Start inference engine (if local)
   bash model_module/run.sh
   
   # Start server
   python base_module/app.py
   
   # Test
   python base_module/main_interface.py
   ```

4. **Commit and push:**
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin feature/your-feature-name
   ```

## Additional Resources

- **Documentation:** https://arkos.mintlify.app/
- **GitHub:** https://github.com/SGIARK/ARKOS
- **Remote Server:** `ark.mit.edu`
- **SGLANG Docs:** https://docs.sglang.ai/

## Getting Help

- Check the `#ark` channel on Slack
- Review existing issues on GitHub
- Contact the team lead: @nmorgan

## Notes

- The remote server runs SGLANG + Qwen 2.5 on port 30000
- VLLM (Mistral) is also available on port 20000 (managed by nmorgan)
- Use SSH tunnels when developing locally but using remote inference
- For persistent sessions on remote server, use `tmux`:
  ```bash
  tmux new -s arkos
  # Your commands here
  # Detach: Ctrl+B then D
  # Reattach: tmux attach -t arkos
  ```

