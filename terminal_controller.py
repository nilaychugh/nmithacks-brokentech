import asyncio
import os
import subprocess
import platform
import sys
import shutil
import glob
import time
import socket
import psutil
import zipfile
import tarfile
import re
import hashlib
import json
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("extra-terminal-controller")

# List to store command history
command_history = []

# Maximum history size
MAX_HISTORY_SIZE = 100

# Store the initial working directory
INITIAL_WORKING_DIR = os.getcwd()

async def run_command(cmd: str, timeout: int = 30) -> Dict:
    """
    Execute command and return results
    
    Args:
        cmd: Command to execute
        timeout: Command timeout in seconds
        
    Returns:
        Dictionary containing command execution results
    """
    start_time = datetime.now()
    
    try:
        # Create command appropriate for current OS
        if platform.system() == "Windows":
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
        else:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
                executable="/bin/bash"
            )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
            stdout = stdout.decode('utf-8', errors='replace')
            stderr = stderr.decode('utf-8', errors='replace')
            return_code = process.returncode
        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "return_code": -1,
                "duration": str(datetime.now() - start_time),
                "command": cmd
            }
    
        duration = datetime.now() - start_time
        result = {
            "success": return_code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code,
            "duration": str(duration),
            "command": cmd
        }
        
        # Add to history
        command_history.append({
            "timestamp": datetime.now().isoformat(),
            "command": cmd,
            "success": return_code == 0
        })
        
        # If history is too long, remove oldest record
        if len(command_history) > MAX_HISTORY_SIZE:
            command_history.pop(0)
            
        return result
    
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error executing command: {str(e)}",
            "return_code": -1,
            "duration": str(datetime.now() - start_time),
            "command": cmd
        }

@mcp.tool()
async def execute_command(command: str, timeout: int = 30) -> str:
    """
    Execute terminal command and return results
    
    Args:
        command: Command line command to execute
        timeout: Command timeout in seconds, default is 30 seconds
    
    Returns:
        Output of the command execution
    """
    # Check for dangerous commands (can add more security checks)
    dangerous_commands = ["rm -rf /", "mkfs", "format", "deltree"]
    if any(dc in command.lower() for dc in dangerous_commands):
        return "For security reasons, this command is not allowed."
    
    result = await run_command(command, timeout)
    
    if result["success"]:
        output = f"Command executed successfully (duration: {result['duration']})\n\n"
        
        if result["stdout"]:
            output += f"Output:\n{result['stdout']}\n"
        else:
            output += "Command had no output.\n"
            
        if result["stderr"]:
            output += f"\nWarnings/Info:\n{result['stderr']}"
            
        return output
    else:
        output = f"Command execution failed (duration: {result['duration']})\n"
        
        if result["stdout"]:
            output += f"\nOutput:\n{result['stdout']}\n"
            
        if result["stderr"]:
            output += f"\nError:\n{result['stderr']}"
            
        output += f"\nReturn code: {result['return_code']}"
        return output

@mcp.tool()
async def get_command_history(count: int = 10, filter_string: str = None) -> str:
    """
    Get recent command execution history with optional filtering
    
    Args:
        count: Number of recent commands to return
        filter_string: Optional string to filter commands containing this substring
    
    Returns:
        Formatted command history record
    """
    if not command_history:
        return "No command execution history."
    
    filtered_history = command_history
    if filter_string:
        filtered_history = [cmd for cmd in command_history if filter_string.lower() in cmd["command"].lower()]
        
    if not filtered_history:
        return f"No commands found containing '{filter_string}'."
    
    count = min(count, len(filtered_history))
    recent_commands = filtered_history[-count:]
    
    output = f"Recent {count} command history"
    if filter_string:
        output += f" (filtered by '{filter_string}')"
    output += ":\n\n"
    
    for i, cmd in enumerate(recent_commands):
        status = "✓" if cmd["success"] else "✗"
        timestamp = datetime.fromisoformat(cmd["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        output += f"{i+1}. [{status}] {timestamp}: {cmd['command']}\n"
    
    return output

@mcp.tool()
async def get_current_directory() -> str:
    """
    Get current working directory
    
    Returns:
        Path of current working directory
    """
    return os.getcwd()

@mcp.tool()
async def get_home_directory() -> str:
    """
    Get user's home directory
    
    Returns:
        Path of user's home directory
    """
    return os.path.expanduser("~")

@mcp.tool()
async def change_directory(path: str) -> str:
    """
    Change current working directory
    
    Args:
        path: Directory path to switch to
    
    Returns:
        Operation result information
    """
    try:
        # Handle special path shortcuts
        if path == "~":
            path = os.path.expanduser("~")
        elif path == "-":
            # Go to previous directory if available
            if hasattr(change_directory, "prev_dir"):
                prev_dir = os.getcwd()
                os.chdir(change_directory.prev_dir)
                change_directory.prev_dir = prev_dir
                return f"Switched back to directory: {os.getcwd()}"
            else:
                return "No previous directory available."
        elif path == "..":
            path = os.path.dirname(os.getcwd())
        
        # Store previous directory before changing
        prev_dir = os.getcwd()
        os.chdir(path)
        change_directory.prev_dir = prev_dir
        
        return f"Switched to directory: {os.getcwd()}"
    except FileNotFoundError:
        return f"Error: Directory '{path}' does not exist"
    except PermissionError:
        return f"Error: No permission to access directory '{path}'"
    except Exception as e:
        return f"Error changing directory: {str(e)}"

@mcp.tool()
async def list_directory(path: Optional[str] = None, show_hidden: bool = False, 
                         pattern: str = None, sort_by: str = "name", reverse: bool = False,
                         details: bool = False) -> str:
    """
    List files and subdirectories in the specified directory with enhanced options
    
    Args:
        path: Directory path to list contents, default is current directory
        show_hidden: Whether to show hidden files (starting with .)
        pattern: Optional glob pattern to filter files (e.g., "*.py")
        sort_by: Sort method: "name", "size", "type", or "modified"
        reverse: Whether to reverse the sort order
        details: Show detailed file information (size, modified date)
    
    Returns:
        List of directory contents
    """
    if path is None:
        path = os.getcwd()
    
    try:
        # Get list of items
        if pattern:
            items_path = os.path.join(path, pattern)
            items = [os.path.basename(x) for x in glob.glob(items_path)]
        else:
            items = os.listdir(path)
        
        # Filter hidden files if not requested
        if not show_hidden:
            items = [item for item in items if not item.startswith('.')]
        
        # Build detailed information
        file_details = []
        for item in items:
            try:
                full_path = os.path.join(path, item)
                stat_info = os.stat(full_path)
                is_dir = os.path.isdir(full_path)
                
                item_data = {
                    "name": item + ("/" if is_dir else ""),
                    "path": full_path,
                    "size": stat_info.st_size,
                    "human_size": _get_human_size(stat_info.st_size),
                    "modified": stat_info.st_mtime,
                    "modified_date": datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "is_dir": is_dir,
                    "type": "directory" if is_dir else _get_file_type(item)
                }
                file_details.append(item_data)
            except (FileNotFoundError, PermissionError):
                continue
        
        # Sort items
        if sort_by == "name":
            file_details.sort(key=lambda x: x["name"].lower(), reverse=reverse)
        elif sort_by == "size":
            file_details.sort(key=lambda x: x["size"], reverse=reverse)
        elif sort_by == "modified":
            file_details.sort(key=lambda x: x["modified"], reverse=reverse)
        elif sort_by == "type":
            file_details.sort(key=lambda x: (x["type"], x["name"].lower()), reverse=reverse)
        
        # Split into directories and files
        dirs = [x for x in file_details if x["is_dir"]]
        files = [x for x in file_details if not x["is_dir"]]
        
        if not dirs and not files:
            return f"Directory '{path}' is empty or no files match the pattern"
        
        output = f"Contents of directory '{path}'"
        if pattern:
            output += f" (filtered by '{pattern}')"
        output += ":\n\n"
        
        # Show directories
        if dirs:
            output += "Directories:\n"
            for d in dirs:
                if details:
                    output += f"📁 {d['name']} - Modified: {d['modified_date']}\n"
                else:
                    output += f"📁 {d['name']}\n"
            output += "\n"
        
        # Show files
        if files:
            output += "Files:\n"
            for f in files:
                if details:
                    output += f"📄 {f['name']} - Size: {f['human_size']}, Modified: {f['modified_date']}\n"
                else:
                    output += f"📄 {f['name']}\n"
        
        return output
    
    except FileNotFoundError:
        return f"Error: Directory '{path}' does not exist"
    except PermissionError:
        return f"Error: No permission to access directory '{path}'"
    except Exception as e:
        return f"Error listing directory contents: {str(e)}"

def _get_human_size(size_bytes):
    """
    Convert bytes to human-readable format
    """
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f}{size_names[i]}"

def _get_file_type(filename):
    """
    Get file type based on extension
    """
    extension = os.path.splitext(filename)[1].lower()
    type_map = {
        '.txt': 'text',
        '.md': 'markdown',
        '.py': 'python',
        '.js': 'javascript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.xml': 'xml',
        '.csv': 'csv',
        '.pdf': 'pdf',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.svg': 'image',
        '.mp3': 'audio',
        '.wav': 'audio',
        '.mp4': 'video',
        '.zip': 'archive',
        '.tar': 'archive',
        '.gz': 'archive',
        '.exe': 'executable',
        '.sh': 'script',
        '.bat': 'script',
    }
    return type_map.get(extension, 'unknown')

@mcp.tool()
async def write_file(path: str, content: str, mode: str = "overwrite") -> str:
    """
    Write content to a file
    
    Args:
        path: Path to the file
        content: Content to write (string or JSON object)
        mode: Write mode ('overwrite' or 'append')
    
    Returns:
        Operation result information
    """
    try:
        # Handle different content types
        if not isinstance(content, str):
            try:
                import json
                # Advanced JSON serialization with better handling of complex objects
                content = json.dumps(content, 
                                    indent=4, 
                                    sort_keys=False, 
                                    ensure_ascii=False, 
                                    default=lambda obj: str(obj) if hasattr(obj, '__dict__') else repr(obj))
            except Exception as e:
                # Try a more aggressive approach if standard serialization fails
                try:
                    # Convert object to dictionary first if it has __dict__
                    if hasattr(content, '__dict__'):
                        import json
                        content = json.dumps(content.__dict__, 
                                           indent=4, 
                                           sort_keys=False, 
                                           ensure_ascii=False)
                    else:
                        # Last resort: convert to string representation
                        content = str(content)
                except Exception as inner_e:
                    return f"Error: Unable to convert complex object to writable string: {str(e)}, then tried alternative method and got: {str(inner_e)}"
        
        # Choose file mode based on the specified writing mode
        file_mode = "w" if mode.lower() == "overwrite" else "a"
        
        # Ensure content ends with a newline if it doesn't already
        if content and not content.endswith('\n'):
            content += '\n'
        
        # Ensure directory exists
        directory = os.path.dirname(os.path.abspath(path))
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(path, file_mode, encoding="utf-8") as file:
            file.write(content)
        
        # Verify the write operation was successful
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            return f"Successfully wrote {file_size} bytes to '{path}' in {mode} mode."
        else:
            return f"Write operation completed, but unable to verify file exists at '{path}'."
    
    except FileNotFoundError:
        return f"Error: The directory in path '{path}' does not exist and could not be created."
    except PermissionError:
        return f"Error: No permission to write to file '{path}'."
    except Exception as e:
        return f"Error writing to file: {str(e)}"

@mcp.tool()
async def read_file(path: str, start_row: int = None, end_row: int = None, as_json: bool = False) -> str:
    """
    Read content from a file with optional row selection
    
    Args:
        path: Path to the file
        start_row: Starting row to read from (0-based, optional)
        end_row: Ending row to read to (0-based, inclusive, optional)
        as_json: If True, attempt to parse file content as JSON (optional)
    
    Returns:
        File content or selected lines, optionally parsed as JSON
    """
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
            
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file."
        
        # Check file size before reading to prevent memory issues
        file_size = os.path.getsize(path)
        if file_size > 10 * 1024 * 1024:  # 10 MB limit
            return f"Warning: File is very large ({file_size/1024/1024:.2f} MB). Consider using row selection."
            
        with open(path, 'r', encoding='utf-8', errors='replace') as file:
            lines = file.readlines()
            
        # If row selection is specified
        if start_row is not None:
            if start_row < 0:
                return "Error: start_row must be non-negative."
                
            # If only start_row is specified, read just that single row
            if end_row is None:
                if start_row >= len(lines):
                    return f"Error: start_row {start_row} is out of range (file has {len(lines)} lines)."
                content = f"Line {start_row}: {lines[start_row]}"
            else:
                # Both start_row and end_row are specified
                if end_row < start_row:
                    return "Error: end_row must be greater than or equal to start_row."
                    
                if end_row >= len(lines):
                    end_row = len(lines) - 1
                    
                selected_lines = lines[start_row:end_row+1]
                content = ""
                for i, line in enumerate(selected_lines):
                    content += f"Line {start_row + i}: {line}" if not line.endswith('\n') else f"Line {start_row + i}: {line}"
        else:
            # If no row selection, return the entire file
            content = "".join(lines)
        
        # If as_json is True, try to parse the content as JSON
        if as_json:
            try:
                import json
                # If we're showing line numbers, we cannot parse as JSON
                if start_row is not None:
                    return "Error: Cannot parse as JSON when displaying line numbers. Use as_json without row selection."
                
                # Try to parse the content as JSON
                parsed_json = json.loads(content)
                # Return pretty-printed JSON for better readability
                return json.dumps(parsed_json, indent=4, sort_keys=False, ensure_ascii=False)
            except json.JSONDecodeError as e:
                return f"Error: File content is not valid JSON. {str(e)}\n\nRaw content:\n{content}"
        
        return content
            
    except PermissionError:
        return f"Error: No permission to read file '{path}'."
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
async def insert_file_content(path: str, content: str, row: int = None, rows: list = None) -> str:
    """
    Insert content at specific row(s) in a file
    
    Args:
        path: Path to the file
        content: Content to insert (string or JSON object)
        row: Row number to insert at (0-based, optional)
        rows: List of row numbers to insert at (0-based, optional)
    
    Returns:
        Operation result information
    """
    try:
        # Handle different content types
        if not isinstance(content, str):
            try:
                import json
                content = json.dumps(content, indent=4, sort_keys=False, ensure_ascii=False, default=str)
            except Exception as e:
                return f"Error: Unable to convert content to JSON string: {str(e)}"
            
        # Ensure content ends with a newline if it doesn't already
        if content and not content.endswith('\n'):
            content += '\n'
            
        # Create file if it doesn't exist
        directory = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as file:
                pass
            
        with open(path, 'r', encoding='utf-8', errors='replace') as file:
            lines = file.readlines()
        
        # Ensure all existing lines end with newlines
        for i in range(len(lines)):
            if lines[i] and not lines[i].endswith('\n'):
                lines[i] += '\n'
        
        # Prepare lines for insertion
        content_lines = content.splitlines(True)  # Keep line endings
        
        # Handle inserting at specific rows
        if rows is not None:
            if not isinstance(rows, list):
                return "Error: 'rows' parameter must be a list of integers."
                
            # Sort rows in descending order to avoid changing indices during insertion
            rows = sorted(rows, reverse=True)
            
            for r in rows:
                if not isinstance(r, int) or r < 0:
                    return "Error: Row numbers must be non-negative integers."
                    
                if r > len(lines):
                    # If row is beyond the file, append necessary empty lines
                    lines.extend(['\n'] * (r - len(lines)))
                    lines.extend(content_lines)
                else:
                    # Insert content at each specified row
                    for line in reversed(content_lines):
                        lines.insert(r, line)
            
            # Write back to the file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            return f"Successfully inserted content at rows {rows} in '{path}'."
            
        # Handle inserting at a single row
        elif row is not None:
            if not isinstance(row, int) or row < 0:
                return "Error: Row number must be a non-negative integer."
                
            if row > len(lines):
                # If row is beyond the file, append necessary empty lines
                lines.extend(['\n'] * (row - len(lines)))
                lines.extend(content_lines)
            else:
                # Insert content at the specified row
                for line in reversed(content_lines):
                    lines.insert(row, line)
            
            # Write back to the file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            return f"Successfully inserted content at row {row} in '{path}'."
        
        # If neither row nor rows specified, append to the end
        else:
            with open(path, 'a', encoding='utf-8') as file:
                file.write(content)
            return f"Successfully appended content to '{path}'."
            
    except PermissionError:
        return f"Error: No permission to modify file '{path}'."
    except Exception as e:
        return f"Error inserting content: {str(e)}"

@mcp.tool()
async def delete_file_content(path: str, row: int = None, rows: list = None, substring: str = None) -> str:
    """
    Delete content at specific row(s) from a file
    
    Args:
        path: Path to the file
        row: Row number to delete (0-based, optional)
        rows: List of row numbers to delete (0-based, optional)
        substring: If provided, only delete this substring within the specified row(s), not the entire row (optional)
    
    Returns:
        Operation result information
    """
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
            
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file."
            
        with open(path, 'r', encoding='utf-8', errors='replace') as file:
            lines = file.readlines()
        
        total_lines = len(lines)
        deleted_rows = []
        modified_rows = []
        
        # Handle substring deletion (doesn't delete entire rows)
        if substring is not None:
            # For multiple rows
            if rows is not None:
                if not isinstance(rows, list):
                    return "Error: 'rows' parameter must be a list of integers."
                
                for r in rows:
                    if not isinstance(r, int) or r < 0:
                        return "Error: Row numbers must be non-negative integers."
                        
                    if r < total_lines and substring in lines[r]:
                        original_line = lines[r]
                        lines[r] = lines[r].replace(substring, '')
                        # Ensure line ends with newline if original did
                        if original_line.endswith('\n') and not lines[r].endswith('\n'):
                            lines[r] += '\n'
                        modified_rows.append(r)
            
            # For single row
            elif row is not None:
                if not isinstance(row, int) or row < 0:
                    return "Error: Row number must be a non-negative integer."
                    
                if row >= total_lines:
                    return f"Error: Row {row} is out of range (file has {total_lines} lines)."
                    
                if substring in lines[row]:
                    original_line = lines[row]
                    lines[row] = lines[row].replace(substring, '')
                    # Ensure line ends with newline if original did
                    if original_line.endswith('\n') and not lines[row].endswith('\n'):
                        lines[row] += '\n'
                    modified_rows.append(row)
            
            # For entire file
            else:
                for i in range(len(lines)):
                    if substring in lines[i]:
                        original_line = lines[i]
                        lines[i] = lines[i].replace(substring, '')
                        # Ensure line ends with newline if original did
                        if original_line.endswith('\n') and not lines[i].endswith('\n'):
                            lines[i] += '\n'
                        modified_rows.append(i)
            
            # Write back to the file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            if not modified_rows:
                return f"No occurrences of '{substring}' found in the specified rows."
            return f"Successfully removed '{substring}' from {len(modified_rows)} rows ({modified_rows}) in '{path}'."
        
        # Handle deleting multiple rows
        elif rows is not None:
            if not isinstance(rows, list):
                return "Error: 'rows' parameter must be a list of integers."
                
            # Sort rows in descending order to avoid changing indices during deletion
            rows = sorted(rows, reverse=True)
            
            for r in rows:
                if not isinstance(r, int) or r < 0:
                    return "Error: Row numbers must be non-negative integers."
                    
                if r < total_lines:
                    lines.pop(r)
                    deleted_rows.append(r)
            
            # Write back to the file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            if not deleted_rows:
                return f"No rows were within range to delete (file has {total_lines} lines)."
            return f"Successfully deleted {len(deleted_rows)} rows ({deleted_rows}) from '{path}'."
            
        # Handle deleting a single row
        elif row is not None:
            if not isinstance(row, int) or row < 0:
                return "Error: Row number must be a non-negative integer."
                
            if row >= total_lines:
                return f"Error: Row {row} is out of range (file has {total_lines} lines)."
                
            # Delete the specified row
            lines.pop(row)
            
            # Write back to the file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            return f"Successfully deleted row {row} from '{path}'."
        
        # If neither row nor rows specified, clear the file
        else:
            with open(path, 'w', encoding='utf-8') as file:
                pass
            return f"Successfully cleared all content from '{path}'."
            
    except PermissionError:
        return f"Error: No permission to modify file '{path}'."
    except Exception as e:
        return f"Error deleting content: {str(e)}"

@mcp.tool()
async def update_file_content(path: str, content: str, row: int = None, rows: list = None, substring: str = None) -> str:
    """
    Update content at specific row(s) in a file
    
    Args:
        path: Path to the file
        content: New content to place at the specified row(s)
        row: Row number to update (0-based, optional)
        rows: List of row numbers to update (0-based, optional)
        substring: If provided, only replace this substring within the specified row(s), not the entire row
    
    Returns:
        Operation result information
    """
    try:
        # Handle different content types
        if not isinstance(content, str):
            try:
                import json
                content = json.dumps(content, indent=4, sort_keys=False, ensure_ascii=False, default=str)
            except Exception as e:
                return f"Error: Unable to convert content to JSON string: {str(e)}"
        
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
            
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file."
            
        with open(path, 'r', encoding='utf-8', errors='replace') as file:
            lines = file.readlines()
        
        total_lines = len(lines)
        updated_rows = []
        
        # Ensure content ends with a newline if replacing a full line and doesn't already have one
        if substring is None and content and not content.endswith('\n'):
            content += '\n'
        
        # Prepare lines for update
        content_lines = content.splitlines(True) if substring is None else [content]
        
        # Handle updating multiple rows
        if rows is not None:
            if not isinstance(rows, list):
                return "Error: 'rows' parameter must be a list of integers."
                
            for r in rows:
                if not isinstance(r, int) or r < 0:
                    return "Error: Row numbers must be non-negative integers."
                    
                if r >= total_lines:
                    continue
                
                if substring is not None:
                    # Replace substring in the specified row
                    original_line = lines[r]
                    lines[r] = lines[r].replace(substring, content)
                    # Ensure line ends with newline if original did
                    if original_line.endswith('\n') and not lines[r].endswith('\n'):
                        lines[r] += '\n'
                else:
                    # Replace entire row with the content
                    for i, content_line in enumerate(content_lines):
                        if r + i < total_lines:
                            lines[r + i] = content_line
                        else:
                            lines.append(content_line)
                
                updated_rows.append(r)
            
            # Write back to the file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            if not updated_rows:
                return f"No rows were within range to update (file has {total_lines} lines)."
            return f"Successfully updated {len(updated_rows)} rows ({updated_rows}) in '{path}'."
            
        # Handle updating a single row
        elif row is not None:
            if not isinstance(row, int) or row < 0:
                return "Error: Row number must be a non-negative integer."
                
            if row >= total_lines:
                return f"Error: Row {row} is out of range (file has {total_lines} lines)."
                
            if substring is not None:
                # Replace substring in the specified row
                original_line = lines[row]
                lines[row] = lines[row].replace(substring, content)
                # Ensure line ends with newline if original did
                if original_line.endswith('\n') and not lines[row].endswith('\n'):
                    lines[row] += '\n'
            else:
                # Replace entire row with the content
                for i, content_line in enumerate(content_lines):
                    if row + i < total_lines:
                        lines[row + i] = content_line
                    else:
                        lines.append(content_line)
            
            # Write back to the file
            with open(path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
            return f"Successfully updated row {row} in '{path}'."
        
        # If neither row nor rows specified, replace the entire file
        else:
            with open(path, 'w', encoding='utf-8') as file:
                if substring is not None:
                    # Replace substring in all lines
                    for i in range(len(lines)):
                        original_line = lines[i]
                        lines[i] = lines[i].replace(substring, content)
                        # Ensure line ends with newline if original did
                        if original_line.endswith('\n') and not lines[i].endswith('\n'):
                            lines[i] += '\n'
                    file.writelines(lines)
                else:
                    # Replace entire file with new content
                    file.write(content)
            return f"Successfully replaced content in '{path}'."
            
    except PermissionError:
        return f"Error: No permission to modify file '{path}'."
    except Exception as e:
        return f"Error updating content: {str(e)}"
    
@mcp.tool()
async def initialize_git_repository(path: str = None, initial_branch: str = None) -> str:
    """
    Initialize a new Git repository in the specified directory.
    Args:
        path: Directory to initialize git repo (default: current directory)
        initial_branch: Optional name for the initial branch (Git 2.28+)
    Returns:
        Operation result string
    """
    if path is None:
        path = os.getcwd()
    if not os.path.exists(path):
        return f"Error: Directory '{path}' does not exist."
    if not os.path.isdir(path):
        return f"Error: '{path}' is not a directory."
    
    # Check if a Git repository already exists
    git_dir = os.path.join(path, ".git")
    if os.path.exists(git_dir) and os.path.isdir(git_dir):
        return f"Git repository already exists in '{path}'."
    
    # Build the command string
    cmd = "git init"
    if initial_branch:
        cmd += f" --initial-branch {initial_branch}"
    cmd += f" {path}"
    
    # Use the run_command helper function which handles platform differences
    result = await run_command(cmd)
    
    if result["success"]:
        return f"Git repository initialized in '{path}'.\n{result['stdout']}"
    else:
        return f"Failed to initialize git repository in '{path}'.\n{result['stderr']}"

def main():
    print("Starting terminal controller MCP server...")
    print("Server is running and waiting for commands...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    print("Initializing terminal controller...")
    main()