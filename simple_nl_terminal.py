import os
import subprocess
import re

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def process_query(query):
    query = query.lower().strip()
    
    # File listing commands
    if re.search(r"(list|show|display).*files", query) or "directory contents" in query:
        return "dir", "List files in the current directory"
    
    # System information
    elif "system" in query and any(word in query for word in ["info", "information", "details"]):
        return "systeminfo", "Display system information"
    
    # Current directory
    elif "current directory" in query or "where am i" in query:
        return "cd", "Show current directory"
    
    # Network information
    elif "network" in query and ("connections" in query or "info" in query):
        return "netstat -a", "Show network connections"
    
    # IP configuration
    elif "ip" in query and "config" in query:
        return "ipconfig /all", "Show IP configuration"
    
    # Process information
    elif "process" in query and ("list" in query or "running" in query):
        return "tasklist", "List running processes"
        
    # Create directory
    elif re.search(r"(create|make).*folder|directory.*(\w+)", query):
        match = re.search(r"(folder|directory).*?([a-zA-Z0-9_-]+)", query)
        if match:
            folder_name = match.group(2)
            return f"mkdir {folder_name}", f"Create directory named {folder_name}"
    
    # Disk space
    elif "disk space" in query or "storage" in query:
        return "wmic logicaldisk get deviceid, size, freespace, description", "Show disk space information"
    
    # Default case
    return None, "I couldn't understand that command"

def main():
    print("Simple Natural Language Terminal")
    print("Type commands in English or 'exit' to quit")
    print("-----------------------------------------")
    
    while True:
        try:
            user_input = input("NL> ")
            
            if user_input.lower() == "exit":
                break
                
            if not user_input.strip():
                continue
            
            # Convert natural language to command
            command, explanation = process_query(user_input)
            
            if not command:
                print(explanation)
                continue
                
            # Show what's about to be executed
            print(f"Command: {command}")
            print(f"Explanation: {explanation}")
            confirm = input("Execute this command? (y/n): ")
            
            if confirm.lower() != "y":
                print("Command cancelled.")
                continue
                
            # Execute the command
            result = run_command(command)
            
            if result["success"]:
                print("Command executed successfully")
                if result["stdout"]:
                    print("\nOutput:")
                    print(result["stdout"])
                else:
                    print("Command had no output.")
            else:
                print("Command execution failed")
                if result["stderr"]:
                    print("\nError:")
                    print(result["stderr"])
                print(f"Return code: {result['returncode']}")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            
    print("Terminal closed")

if __name__ == "__main__":
    main()