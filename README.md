# ARKOS

ARK (Automated Resource Knowledgebase) revolutionizes resource management via automation. Using advanced algorithms, it streamlines collection, organization, and access to resource data, facilitating efficient decision-making.


## Languages and Dependencies

The entire codebase is in Python, except for a few shell scripts. 

### Core Dependencies

* **`openai>=1.61.0`** - OpenAI Python SDK for standardizing inference engine communication and API compatibility
* **`pyyaml>=6.0.2`** - YAML parser for configuration files (state graphs, etc.)
* **`pydantic>=2.10.6`** - Data validation and schema definition using Python type annotations
* **`requests>=2.32.3`** - HTTP library for making API requests to external services and tools

### Web Framework

* **`fastapi>=0.115.0`** - Modern, fast web framework for building the API server with automatic OpenAPI documentation
* **`uvicorn>=0.32.0`** - ASGI server for running FastAPI applications

### Database & Memory

* **`psycopg2-binary>=2.9.11`** - PostgreSQL adapter for Python (binary distribution, no compilation required). Used for storing conversation context and long-term memory
* **`mem0ai`** - Memory management library for vector-based memory storage and retrieval using Supabase

### CLI & User Interface

* **`rich>=13.7.0`** - Terminal formatting and rich text rendering for the enhanced CLI interface. Provides tables, progress bars, panels, and syntax highlighting

### Installation

Install all dependencies using:

```bash
pip install -r requirements.txt
```

**Note:** `psycopg2-binary` is used instead of `psycopg2` to avoid requiring PostgreSQL development libraries (`libpq-dev`) on the system. For production deployments, you may want to use `psycopg2` with proper system dependencies.

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

### Start Inference Engine

The project uses SGLang to run the Qwen 2.5-7B-Instruct model. Start the inference server:

```bash
bash model_module/run.sh
```

This will start the SGLang server on port 30000. The model Qwen/Qwen2.5-7B-Instruct is currently in use.

### Running the Application

ARK OS provides multiple interfaces for interaction:

#### Option 1: Enhanced CLI (Recommended)

The enhanced CLI provides a rich terminal interface with real-time memory visualization:

```bash
python base_module/ark_repl.py
```

Features:
- Real-time memory operation visualization
- Interactive commands (/search, /stats, /memories, /context, etc.)
- Rich terminal UI with tables and formatted output
- Session management and performance tracking

See [base_module/CLI_GUIDE.md](base_module/CLI_GUIDE.md) for full documentation and command reference.

#### Option 2: Basic CLI

Simple text-based interface for quick testing:

```bash
python base_module/main_interface.py
```

This provides a minimal interactive CLI. Type your messages and press Enter. Type `exit` or `quit` to stop.

#### Option 3: API Server

Start the FastAPI server for programmatic access:

```bash
python base_module/app.py
```

This starts the OpenAI-compatible API server on port 1111 at `/v1/chat/completions`.

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
