import asyncio
import json
import sys
from mcp.client import MCPClient

async def main():
    client = MCPClient("terminal-test-client")
    
    # Connect to the already running server
    await client.connect(transport="stdio",
                        subprocess_args=["python", "terminal_controller.py"])
    
    print("Connected to MCP server")
    
    # Try a simple command
    result = await client.call("execute_command", {"command": "dir"})
    print("\nCommand result:")
    print(result)
    
    # Get current directory
    result = await client.call("get_current_directory", {})
    print("\nCurrent directory:")
    print(result)
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())