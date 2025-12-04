# ARKOS

ARK (Automated Resource Knowledgebase) revolutionizes resource management via automation. Using advanced algorithms, it streamlines collection, organization, and access to resource data, facilitating efficient decision-making.


## Languages and dependencies

The entire codebase is in Python, except for a few shell scripts. We use the following four dependencies:

* `openai` (needed to standardize inference engine communication)
* `pyyaml`
* `pydantic` for defining schemas
* `requests`

## File structure

(As of September 11, 2025.)


* `base_module/` for main interface
* `config_module/` for YAML configuration files
* `model_module/` for core LLM-inference logic
* `agent_module/` for agentic structure 
* `state_module/` for defining agent state graphs 
* `tool_module/` for MCP compatibility 
* `memory_module/` for long term memory and context management
* `schemas/` for JSON schemas when communicating between frontend and backend
* `state_module/`
* `tool_module/`
* `.gitignore`
* `README.md` (this very file)
* `requirements.txt` (Python dependencies)

## Instructions

### Quick Start (Hybrid Setup - Recommended)

**Prerequisites:** SSH access to `ark.mit.edu` and an active SSH tunnel.

1. **Set up SSH tunnel** (in one terminal):
   ```bash
   ssh -L 20000:localhost:20000 jack.ark@ark.mit.edu
   ```
   Keep this terminal open.

2. **Start FastAPI server** (in another terminal):
   ```bash
   source venv/bin/activate
   python base_module/app.py
   ```

3. **Test the server** (in a third terminal):
   ```bash
   source venv/bin/activate
   python base_module/main_interface.py
   ```

### Alternative: Local SGLANG

If you have Docker and GPU access locally:

* Run latest SGLANG image
* cmd: bash model_module/run.sh
* Note: Qwen 2.5 is what is currently in use
* Update `base_module/app.py` to use `http://localhost:30000/v1`

### Current Configuration

- **Model:** `mistralai/Ministral-3-14B-Instruct-2512` (VLLM on remote server)
- **API Key:** Configured via `VLLM_API_KEY` environment variable (default: `token-abc123`)
- **Base URL:** `http://localhost:20000/v1` (via SSH tunnel to remote VLLM)

For detailed setup instructions, see [GETTING_STARTED.md](GETTING_STARTED.md).

## Contributors + contact

| Name                  | Role           | GitHub username | Affiliation   |
| --------------------  | -------------- | --------------- | --------------|
| Nathaniel Morgan      | Project leader | nmorgan         | MIT           |
| Joshua Guo            | Frontend       | duck_master     | MIT           |
| Ilya Gulko            | Backend        | gulkily         | MIT           |
| Jack Luo              | Backend        | thejackluo      | Georgia Tech  |
| Bryce Roberts         | Backend        | BryceRoberts13  | MIT           |
| Angela Liu            | Backend        | angelaliu6      | MIT           |
| Ishaana Misra         | Backend        | ishaanam        | MIT           |
