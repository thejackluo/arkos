# ARKOS Remote MCP Integration - Technical Proposal

**Author**: ARKOS Development Team
**Date**: 2025-11-15
**Target**: tool_module/tool_call.py

---

## 1. Problem Understanding

**Objective**: Enable ARKOS agent to dynamically connect to external MCP (Model Context Protocol) servers and use their tools without hardcoding functionality.

**Why**:
- Extensibility: Add new capabilities (GitHub, Slack, databases, etc.) without modifying core code
- Modularity: Each MCP server is isolated in its own process (Docker/NPX)
- Standard Protocol: MCP uses JSON-RPC 2.0, making it interoperable with Claude ecosystem

**What We're Building**:
- `MCPClient`: Manages single MCP server connection (subprocess + JSON-RPC communication)
- `MCPToolManager`: Orchestrates multiple MCP servers, provides unified tool interface
- Integration with ARKOS agent for automatic tool discovery and execution

---

## 2. Proposed Solution

### Complete Implementation: `tool_module/tool_call.py`

```python
"""
Remote MCP (Model Context Protocol) Integration for ARKOS.

This module manages connections to external MCP servers, handles tool discovery,
and executes tool calls via JSON-RPC 2.0 over stdio.
"""

import asyncio
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""

    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class MCPClient:
    """
    Manages a single MCP server connection via subprocess.

    Handles JSON-RPC 2.0 communication over stdin/stdout and implements
    the MCP protocol for tool discovery and execution.

    Parameters
    ----------
    config : MCPServerConfig
        Configuration for the MCP server connection

    Attributes
    ----------
    process : Optional[asyncio.subprocess.Process]
        The running subprocess for the MCP server
    request_id : int
        Counter for JSON-RPC request IDs
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self._lock = Lock()
        self._initialized = False

    async def start(self) -> None:
        """
        Start the MCP server subprocess and perform initialization handshake.

        Raises
        ------
        RuntimeError
            If the server fails to start or initialize
        """
        logger.info(f"Starting MCP server: {self.config.name}")

        # Build environment
        env = dict(self.config.env) if self.config.env else {}

        try:
            # Start subprocess
            self.process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Initialize MCP connection
            init_response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "arkos",
                    "version": "1.0.0"
                }
            })

            if "error" in init_response:
                raise RuntimeError(f"MCP initialization failed: {init_response['error']}")

            # Send initialized notification
            await self._send_notification("notifications/initialized", {})

            self._initialized = True
            logger.info(f"MCP server '{self.config.name}' initialized successfully")

        except Exception as e:
            logger.error(f"Failed to start MCP server '{self.config.name}': {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the MCP server subprocess gracefully."""
        if self.process:
            logger.info(f"Stopping MCP server: {self.config.name}")
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Force killing MCP server: {self.config.name}")
                self.process.kill()
                await self.process.wait()
            finally:
                self.process = None
                self._initialized = False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Request list of available tools from the MCP server.

        Returns
        -------
        List[Dict[str, Any]]
            List of tool definitions with name, description, and input schema

        Raises
        ------
        RuntimeError
            If server is not initialized or request fails
        """
        if not self._initialized:
            raise RuntimeError(f"MCP server '{self.config.name}' not initialized")

        response = await self._send_request("tools/list", {})

        if "error" in response:
            raise RuntimeError(f"tools/list failed: {response['error']}")

        tools = response.get("result", {}).get("tools", [])
        logger.debug(f"Server '{self.config.name}' has {len(tools)} tools")
        return tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool on the MCP server.

        Parameters
        ----------
        name : str
            Name of the tool to execute
        arguments : Dict[str, Any]
            Arguments to pass to the tool

        Returns
        -------
        Any
            Tool execution result

        Raises
        ------
        RuntimeError
            If server is not initialized or tool execution fails
        """
        if not self._initialized:
            raise RuntimeError(f"MCP server '{self.config.name}' not initialized")

        logger.info(f"Calling tool '{name}' on server '{self.config.name}'")
        logger.debug(f"Arguments: {arguments}")

        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        if "error" in response:
            error_msg = response["error"]
            logger.error(f"Tool call failed: {error_msg}")
            raise RuntimeError(f"Tool '{name}' execution failed: {error_msg}")

        result = response.get("result", {})
        logger.debug(f"Tool result: {result}")
        return result

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC 2.0 request and wait for response.

        Parameters
        ----------
        method : str
            JSON-RPC method name
        params : Dict[str, Any]
            Method parameters

        Returns
        -------
        Dict[str, Any]
            JSON-RPC response
        """
        with self._lock:
            self.request_id += 1
            req_id = self.request_id

        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }

        logger.debug(f"[{self.config.name}] >> {json.dumps(request)}")

        # Send request
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line.encode())
        await self.process.stdin.drain()

        # Read response
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError(f"MCP server '{self.config.name}' closed connection")

        response = json.loads(response_line.decode())
        logger.debug(f"[{self.config.name}] << {json.dumps(response)}")

        return response

    async def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send a JSON-RPC 2.0 notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        logger.debug(f"[{self.config.name}] >> {json.dumps(notification)}")

        notification_line = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_line.encode())
        await self.process.stdin.drain()


class MCPToolManager:
    """
    Manages multiple MCP server connections and provides unified tool interface.

    Coordinates tool discovery across all servers and routes tool execution
    to the appropriate server.

    Parameters
    ----------
    config : Dict[str, Dict[str, Any]]
        MCP servers configuration from config file

    Attributes
    ----------
    clients : Dict[str, MCPClient]
        Active MCP client connections by server name
    """

    def __init__(self, config: Dict[str, Dict[str, Any]]):
        self.config = config
        self.clients: Dict[str, MCPClient] = {}
        self._tool_registry: Dict[str, str] = {}  # tool_name -> server_name

    async def initialize_servers(self) -> None:
        """
        Initialize all configured MCP server connections.

        Starts each server, performs handshake, and builds tool registry.

        Raises
        ------
        RuntimeError
            If any server fails to initialize
        """
        logger.info(f"Initializing {len(self.config)} MCP servers")

        for server_name, server_config in self.config.items():
            try:
                config = MCPServerConfig(
                    name=server_name,
                    command=server_config["command"],
                    args=server_config["args"],
                    env=server_config.get("env")
                )

                client = MCPClient(config)
                await client.start()

                # Discover tools
                tools = await client.list_tools()
                for tool in tools:
                    tool_name = tool["name"]
                    self._tool_registry[tool_name] = server_name
                    logger.info(f"Registered tool '{tool_name}' from '{server_name}'")

                self.clients[server_name] = client

            except Exception as e:
                logger.error(f"Failed to initialize server '{server_name}': {e}")
                # Continue with other servers

        if not self.clients:
            raise RuntimeError("No MCP servers successfully initialized")

        logger.info(f"Initialized {len(self.clients)} servers with {len(self._tool_registry)} total tools")

    async def list_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all available tools from all servers.

        Returns
        -------
        List[Dict[str, Any]]
            Combined list of all tools with server name added
        """
        all_tools = []

        for server_name, client in self.clients.items():
            try:
                tools = await client.list_tools()
                for tool in tools:
                    tool["_server"] = server_name  # Add server metadata
                    all_tools.append(tool)
            except Exception as e:
                logger.error(f"Failed to list tools from '{server_name}': {e}")

        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name, routing to the correct server.

        Parameters
        ----------
        tool_name : str
            Name of the tool to execute
        arguments : Dict[str, Any]
            Tool arguments

        Returns
        -------
        Any
            Tool execution result

        Raises
        ------
        ValueError
            If tool is not found in registry
        RuntimeError
            If tool execution fails
        """
        server_name = self._tool_registry.get(tool_name)
        if not server_name:
            raise ValueError(f"Unknown tool: {tool_name}")

        client = self.clients.get(server_name)
        if not client:
            raise RuntimeError(f"Server '{server_name}' not connected")

        return await client.call_tool(tool_name, arguments)

    async def shutdown(self) -> None:
        """Gracefully shutdown all MCP server connections."""
        logger.info("Shutting down all MCP servers")

        for client in self.clients.values():
            try:
                await client.stop()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")

        self.clients.clear()
        self._tool_registry.clear()
```

---

## 3. Integration Plan

### File Structure
```
tool_module/
├── __init__.py
├── tool_call.py          # New MCP integration (above code)
└── base_tools.py         # Existing tools (if any)
```

### Integration with ARKOS Modules

**Config Loading** (`config_module/`):
```python
# config_module/config.py
import yaml

def load_mcp_config(config_path: str) -> dict:
    """Load MCP server configuration from YAML."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config.get("mcpServers", {})
```

**Agent Usage** (`agent_module/`):
```python
# agent_module/agent.py
from tool_module.tool_call import MCPToolManager

class ARKAgent:
    def __init__(self, config):
        self.mcp_manager = None
        self.mcp_config = config.get("mcpServers", {})

    async def initialize(self):
        """Initialize agent with MCP tools."""
        if self.mcp_config:
            self.mcp_manager = MCPToolManager(self.mcp_config)
            await self.mcp_manager.initialize_servers()

            # Get available tools for system prompt
            self.available_tools = await self.mcp_manager.list_all_tools()

    async def execute_tool(self, tool_name: str, args: dict):
        """Execute a tool via MCP."""
        return await self.mcp_manager.call_tool(tool_name, args)

    async def shutdown(self):
        """Cleanup."""
        if self.mcp_manager:
            await self.mcp_manager.shutdown()
```

---

## 4. Input/Output Specification

### Input: Configuration Format

**JSON** (as provided):
```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxx"}
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/documents"]
    }
  }
}
```

**YAML** (recommended for ARKOS):
```yaml
mcpServers:
  github:
    command: docker
    args:
      - run
      - -i
      - --rm
      - -e
      - GITHUB_PERSONAL_ACCESS_TOKEN
      - ghcr.io/github/github-mcp-server
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: ghp_xxxxx

  filesystem:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-filesystem"
      - /home/me/documents
```

### Output: Tool Discovery

```python
tools = await mcp_manager.list_all_tools()
# Returns:
[
  {
    "name": "create_issue",
    "description": "Create a GitHub issue",
    "inputSchema": {
      "type": "object",
      "properties": {
        "repo": {"type": "string"},
        "title": {"type": "string"},
        "body": {"type": "string"}
      },
      "required": ["repo", "title"]
    },
    "_server": "github"
  },
  {
    "name": "read_file",
    "description": "Read a file from the filesystem",
    "inputSchema": {
      "type": "object",
      "properties": {
        "path": {"type": "string"}
      },
      "required": ["path"]
    },
    "_server": "filesystem"
  }
]
```

### Output: Tool Execution

```python
result = await mcp_manager.call_tool("read_file", {"path": "/home/me/test.txt"})
# Returns:
{
  "content": [
    {
      "type": "text",
      "text": "File contents here..."
    }
  ]
}
```

---

## 5. Implementation Timeline

**Week 1**: Core Implementation
- Day 1-2: Implement `MCPClient` class with JSON-RPC communication
- Day 3-4: Implement `MCPToolManager` for multi-server orchestration
- Day 5: Integration with config_module, basic testing

**Week 2**: Integration & Testing
- Day 1-2: Integrate with agent_module
- Day 3-4: Write unit tests and integration tests
- Day 5: Documentation and examples

**Week 3**: Refinement
- Day 1-2: Performance testing with multiple servers
- Day 3-4: Error handling improvements, edge cases
- Day 5: Code review and deployment

---

## 6. Testing Strategy

### Unit Tests

```python
# tests/test_tool_call.py
import asyncio
import pytest
from tool_module.tool_call import MCPClient, MCPToolManager, MCPServerConfig

@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client starts and initializes."""
    config = MCPServerConfig(
        name="test_server",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    )

    client = MCPClient(config)
    await client.start()

    assert client._initialized is True

    tools = await client.list_tools()
    assert len(tools) > 0

    await client.stop()

@pytest.mark.asyncio
async def test_tool_manager_multiple_servers():
    """Test tool manager with multiple servers."""
    config = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        }
    }

    manager = MCPToolManager(config)
    await manager.initialize_servers()

    tools = await manager.list_all_tools()
    assert len(tools) > 0

    await manager.shutdown()

@pytest.mark.asyncio
async def test_tool_execution():
    """Test actual tool execution."""
    config = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        }
    }

    manager = MCPToolManager(config)
    await manager.initialize_servers()

    # Test tool call (assuming filesystem server has list_directory)
    result = await manager.call_tool("list_directory", {"path": "/tmp"})
    assert result is not None

    await manager.shutdown()
```

### Integration Tests

```python
# tests/integration/test_agent_mcp.py
import pytest
from agent_module.agent import ARKAgent

@pytest.mark.asyncio
async def test_agent_with_mcp_tools():
    """Test agent using MCP tools."""
    config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            }
        }
    }

    agent = ARKAgent(config)
    await agent.initialize()

    # Agent should have MCP tools available
    assert len(agent.available_tools) > 0

    # Execute a tool through agent
    result = await agent.execute_tool("list_directory", {"path": "/tmp"})
    assert result is not None

    await agent.shutdown()
```

---

## 7. Usage Examples

### Example 1: Basic Setup

```python
import asyncio
import logging
from tool_module.tool_call import MCPToolManager

logging.basicConfig(level=logging.INFO)

async def main():
    # Load config
    config = {
        "github": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                     "ghcr.io/github/github-mcp-server"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token"}
        }
    }

    # Initialize MCP manager
    manager = MCPToolManager(config)
    await manager.initialize_servers()

    # List available tools
    tools = await manager.list_all_tools()
    for tool in tools:
        print(f"Tool: {tool['name']} - {tool['description']}")

    # Cleanup
    await manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Agent Integration

```python
import asyncio
from tool_module.tool_call import MCPToolManager

class SimpleAgent:
    def __init__(self, mcp_config):
        self.mcp_manager = MCPToolManager(mcp_config)

    async def start(self):
        await self.mcp_manager.initialize_servers()
        self.tools = await self.mcp_manager.list_all_tools()
        print(f"Agent ready with {len(self.tools)} tools")

    async def process_query(self, query: str):
        """Process user query and execute tools."""
        # Simple example: if query mentions "create issue", use that tool
        if "create issue" in query.lower():
            result = await self.mcp_manager.call_tool(
                "create_issue",
                {
                    "repo": "SGIARK/arkos",
                    "title": "Test issue",
                    "body": "Created via MCP"
                }
            )
            return result

    async def stop(self):
        await self.mcp_manager.shutdown()

# Usage
async def main():
    config = {
        "github": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                     "ghcr.io/github/github-mcp-server"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_token"}
        }
    }

    agent = SimpleAgent(config)
    await agent.start()

    result = await agent.process_query("Create issue for bug fix")
    print(f"Result: {result}")

    await agent.stop()

asyncio.run(main())
```

---

## 8. Dependencies

**Standard Library** (no new installs needed):
- `asyncio` - Async I/O operations
- `json` - JSON-RPC encoding/decoding
- `logging` - Debug logging
- `subprocess` - Process management
- `dataclasses` - Config data structures
- `threading` - Thread-safe request ID counter

**Existing ARKOS Dependencies**:
- `pyyaml` - Config file parsing (already in project)

**Optional for Testing**:
- `pytest` - Unit testing
- `pytest-asyncio` - Async test support

**No additional dependencies required** for core functionality.

---

## 9. Security Considerations

### 1. **Environment Variables & Secrets**
- **Risk**: Tokens in config files
- **Mitigation**:
  - Use environment variables: `"env": {"TOKEN": "$GITHUB_TOKEN"}`
  - Add `.env` to `.gitignore`
  - Consider using `python-dotenv` for secret management

### 2. **Subprocess Isolation**
- **Risk**: Malicious MCP servers
- **Mitigation**:
  - Docker containers run with `--rm` (auto-cleanup)
  - No `--privileged` flag
  - Read-only filesystem mounts where possible
  - Network isolation for untrusted servers

### 3. **Input Validation**
- **Risk**: Command injection via tool arguments
- **Mitigation**:
  - MCP servers validate inputs against schema
  - No shell=True in subprocess calls
  - Validate config before starting servers

### 4. **Resource Limits**
- **Risk**: Resource exhaustion from misbehaving servers
- **Mitigation**:
  - Timeout on subprocess startup (5s)
  - Graceful termination with force-kill fallback
  - Consider adding per-tool execution timeouts

### 5. **Logging**
- **Risk**: Sensitive data in logs
- **Mitigation**:
  - Sanitize env vars from logs
  - Use DEBUG level for request/response bodies
  - Rotate log files in production

---

## 10. Future Enhancements (NOT in MVP)

Based on YAGNI principle, these are **deferred**:

1. **Retry Logic** - Add exponential backoff for failed tool calls
2. **Health Checks** - Periodic ping to detect dead servers
3. **Hot Reload** - Add/remove servers without agent restart
4. **Caching** - Cache tool lists to reduce list_tools calls
5. **Metrics** - Track tool usage, latency, error rates
6. **Server Pooling** - Multiple instances of same server for load balancing
7. **Authentication** - Support OAuth/API key rotation
8. **WebSocket Support** - For servers that support bidirectional comms
9. **Tool Composition** - Chain multiple tools automatically
10. **Sandboxing** - More aggressive isolation (gVisor, Firecracker)

**Decision**: Keep it simple. Add these only when proven necessary by usage data.

---

## Appendix: Quick Start Checklist

- [ ] Copy `tool_call.py` to `tool_module/`
- [ ] Create `config/mcp_servers.yaml` with server configs
- [ ] Install MCP servers: `npx @modelcontextprotocol/server-*` or pull Docker images
- [ ] Test with: `python -m pytest tests/test_tool_call.py`
- [ ] Integrate with agent_module
- [ ] Add logging configuration
- [ ] Document server-specific quirks in wiki

---

**End of Proposal**
