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

### Option B: Hybrid Setup (Recommended - Local Dev, Remote Inference)

**Current Recommended Setup:** Run ARKOS locally but use the remote VLLM server for inference.

This setup gives you:
- Fast local development (edit code instantly)
- Remote GPU access (use Mistral model on server)
- No need to upload code for every change

#### SSH Tunnel Setup

Create an SSH tunnel to access the remote VLLM server:

```bash
ssh -L 20000:localhost:20000 jack.ark@ark.mit.edu
```

This command:
- `-L 20000:localhost:20000`: Forward local port 20000 to remote port 20000
- Keeps the tunnel open in your terminal (don't close it)
- Allows your local code to access the remote VLLM server

**Note:** The current setup uses VLLM (port 20000) with Mistral model. If you want to use SGLANG instead:

```bash
ssh -L 30000:localhost:30000 jack.ark@ark.mit.edu
```

#### Current Configuration

The `base_module/app.py` is already configured for this setup:

```python
llm = ArkModelLink(
    base_url="http://localhost:20000/v1",  # Via SSH tunnel
    model_name="mistralai/Ministral-3-14B-Instruct-2512"  # VLLM model
)
```

#### Start FastAPI Server Locally

In a new terminal (keep SSH tunnel running):

```bash
source venv/bin/activate
python base_module/app.py
```

The server will connect to the remote VLLM server through the SSH tunnel.

#### Test the Server

In another terminal:

```bash
source venv/bin/activate
python base_module/main_interface.py
```

### Option C: Fully Remote (Alternative - Everything on Server)

Run everything directly on the remote server. Better for production/deployment.

#### Upload Code to Server

```bash
# From your laptop
rsync -avz --exclude 'venv' --exclude '__pycache__' \
  ./ jack.ark@ark.mit.edu:~/arkos/
```

#### SSH into Server and Setup

```bash
ssh jack.ark@ark.mit.edu
cd ~/arkos
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Update Configuration for Direct Connection

In `base_module/app.py` on the server:

```python
llm = ArkModelLink(
    base_url="http://localhost:20000/v1",  # Direct connection (no tunnel needed)
    model_name="mistralai/Ministral-3-14B-Instruct-2512"
)
```

#### Run on Server (with tmux for persistence)

```bash
tmux new -s arkos
python base_module/app.py
# Press Ctrl+B then D to detach
# Reattach later: tmux attach -t arkos
```

#### Access from Laptop (optional)

If you want to test from your laptop:

```bash
ssh -L 1111:localhost:1111 jack.ark@ark.mit.edu
# Then main_interface.py will work
```

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
| FastAPI Server | 1111 | Main ARKOS API server (runs locally in hybrid setup) |
| VLLM (Remote) | 20000 | VLLM inference engine on remote server (Mistral model) |
| SGLANG (Remote) | 30000 | SGLANG inference engine on remote server (Qwen 2.5) |
| SSH Tunnel (Local) | 20000 | Local port forwarded to remote VLLM (current setup) |

**Current Setup:** FastAPI (local:1111) → SSH Tunnel (local:20000) → VLLM (remote:20000)

## Troubleshooting

### FileNotFoundError: state_graph.yaml

**Status:** ✅ Fixed in current codebase

The YAML path is now handled with absolute paths. If you still see this error, make sure you're running the latest code.

### Model Not Found (404 Error)

**Status:** ✅ Fixed in current codebase

The model name is now correctly set to `mistralai/Ministral-3-14B-Instruct-2512`. If you see a 404 error:

1. Check available models:
   ```bash
   curl -H "Authorization: Bearer token-abc123" http://localhost:20000/v1/models
   ```

2. Verify the model name in `base_module/app.py` matches the server's model.

### VLLM add_generation_prompt Error (400 Error)

**Status:** ✅ Fixed in current codebase

This error occurs when the message history ends with an assistant message. The code now automatically filters trailing assistant messages before LLM calls.

If you see this error, make sure you're running the latest code with the fixes applied.

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

## Complete Workflow (Hybrid Setup)

You need **3 terminals** for the complete setup:

### Terminal 1: SSH Tunnel (Keep Running)
```bash
ssh -L 20000:localhost:20000 jack.ark@ark.mit.edu
```
- Keep this terminal open
- This creates the bridge to the remote VLLM server
- Don't close it while working

### Terminal 2: FastAPI Server (Keep Running)
```bash
cd "/mnt/c/Users/Jack Luo/Desktop/(local) github software/(o) arkos/arkos"
source venv/bin/activate
python base_module/app.py
```
- Keep this running
- You'll see server logs here
- Restart after code changes (auto-reload enabled)

### Terminal 3: Test Interface (As Needed)
```bash
cd "/mnt/c/Users/Jack Luo/Desktop/(local) github software/(o) arkos/arkos"
source venv/bin/activate
python base_module/main_interface.py
```
- Use this to test your agent
- Type messages and see responses
- Exit with `quit` or `exit`

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

3. **Set up your environment:**
   ```bash
   # Terminal 1: Start SSH tunnel
   ssh -L 20000:localhost:20000 jack.ark@ark.mit.edu
   
   # Terminal 2: Start FastAPI server
   source venv/bin/activate
   python base_module/app.py
   ```

4. **Make changes and test:**
   ```bash
   # Terminal 3: Test your changes
   source venv/bin/activate
   python base_module/main_interface.py
   ```

5. **Commit and push:**
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

## Understanding the Setup

### OpenAI Library vs OpenAI Service

**Important:** ARKOS uses the `openai` Python library as a **client tool**, but does NOT use OpenAI's GPT models.

- **OpenAI Library:** Python package used to communicate with OpenAI-compatible APIs
- **Actual Model:** Mistral (self-hosted on remote server)
- **Connection:** Your code → OpenAI library → VLLM server → Mistral model

Think of it like: Using an "OpenAI-compatible phone" to call "Mistral" instead of "GPT".

### Model Information

- **Current Model:** `mistralai/Ministral-3-14B-Instruct-2512`
- **License:** Apache 2.0 (free and open-source)
- **Cost:** Free when self-hosted (no API fees)
- **Location:** Running on `ark.mit.edu` via VLLM server

### API Key Configuration

The VLLM server requires authentication. The API key is configured in `model_module/ArkModelNew.py`:

```python
api_key = os.getenv("VLLM_API_KEY", "token-abc123")
```

You can set a custom key via environment variable:
```bash
export VLLM_API_KEY="your-key-here"
```

### Architecture Summary

**Current Hybrid Setup:**
- **FastAPI Server:** Runs locally on your laptop (port 1111)
- **VLLM Server:** Runs remotely on `ark.mit.edu` (port 20000)
- **Connection:** SSH tunnel bridges local and remote
- **Model:** Mistral (free, self-hosted)

**Benefits:**
- Fast development (edit code locally)
- GPU access (use remote server's GPUs)
- No per-request costs (self-hosted model)

## Notes

- The remote server runs VLLM with Mistral on port 20000 (currently in use)
- SGLANG + Qwen 2.5 is also available on port 30000 (alternative option)
- Use SSH tunnels when developing locally but using remote inference
- For persistent sessions on remote server, use `tmux`:
  ```bash
  tmux new -s arkos
  # Your commands here
  # Detach: Ctrl+B then D
  # Reattach: tmux attach -t arkos
  ```

