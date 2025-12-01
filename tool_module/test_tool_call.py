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
