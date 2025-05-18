import asyncio
import sys
from mcp.client import MCPClient

async def main():
    client = MCPClient("terminal-interactive-client")
    
    # Connect to server
    print("Connecting to MCP server...")
    await client.connect(transport="stdio", 
                        subprocess_args=["python", "terminal_controller.py"])
    
    print("Connected! Available commands:")
    print("- execute <command>: Run a system command")
    print("- ls [path]: List directory contents")
    print("- cd <path>: Change directory")
    print("- pwd: Show current directory")
    print("- exit: Quit this client")
    print("-" * 50)
    
    while True:
        try:
            cmd = input("> ")
            if cmd.lower() == "exit":
                break
                
            parts = cmd.split(maxsplit=1)
            if not parts:
                continue
                
            if parts[0] == "execute" and len(parts) > 1:
                result = await client.call("execute_command", {"command": parts[1]})
                print(result)
                
            elif parts[0] == "ls":
                path = parts[1] if len(parts) > 1 else None
                result = await client.call("list_directory", {"path": path})
                print(result)
                
            elif parts[0] == "cd" and len(parts) > 1:
                result = await client.call("change_directory", {"path": parts[1]})
                print(result)
                
            elif parts[0] == "pwd":
                result = await client.call("get_current_directory", {})
                print(result)
                
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            print("\nCtrl+C pressed. Type 'exit' to quit.")
        except Exception as e:
            print(f"Error: {str(e)}")
            
    await client.close()
    print("Disconnected from server")

if __name__ == "__main__":
    asyncio.run(main())