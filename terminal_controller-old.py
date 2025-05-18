# import asyncio
# import os
# import subprocess
# import platform
# import sys
# import socket
# import shutil
# import psutil
# import zipfile
# import tarfile
# import getpass
# import signal
# import json
# import time
# import re
# import glob
# import requests
# from typing import List, Dict, Optional, Union, Any
# from datetime import datetime
# from pathlib import Path
# from mcp.server.fastmcp import FastMCP
# import argparse
# from http.server import HTTPServer, BaseHTTPRequestHandler
# from urllib.parse import urlparse
# import threading
# import google.generativeai as genai

# # Initialize Gemini (add this near the top of your file)
# GOOGLE_API_KEY = "AIzaSyA-ePiOwBNxA7b3dPFfQTEfBqM-fejid_E"  # Store this securely
# genai.configure(api_key=GOOGLE_API_KEY)
# model = genai.GenerativeModel('gemini-2.0-flash')

# # Initialize MCP server
# mcp = FastMCP("enhanced-terminal-controller")

# # List to store command history
# command_history = []

# # Maximum history size
# MAX_HISTORY_SIZE = 100

# # Store active interactive terminal sessions
# active_terminals = {}

# async def run_command(cmd: str, timeout: int = 30, cwd: str = None, env: Dict = None) -> Dict:
#     """
#     Execute command and return results
    
#     Args:
#         cmd: Command to execute
#         timeout: Command timeout in seconds
#         cwd: Working directory for command execution
#         env: Environment variables for the command
        
#     Returns:
#         Dictionary containing command execution results
#     """
#     start_time = datetime.now()
    
#     try:
#         # Prepare environment variables
#         process_env = os.environ.copy()
#         if env:
#             process_env.update(env)
        
#         # Create command appropriate for current OS
#         if platform.system() == "Windows":
#             process = await asyncio.create_subprocess_shell(
#                 cmd,
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.PIPE,
#                 shell=True,
#                 cwd=cwd,
#                 env=process_env
#             )
#         else:
#             process = await asyncio.create_subprocess_shell(
#                 cmd,
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.PIPE,
#                 shell=True,
#                 executable="/bin/bash",
#                 cwd=cwd,
#                 env=process_env
#             )
        
#         try:
#             stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
#             stdout = stdout.decode('utf-8', errors='replace')
#             stderr = stderr.decode('utf-8', errors='replace')
#             return_code = process.returncode
#         except asyncio.TimeoutError:
#             try:
#                 process.kill()
#             except:
#                 pass
#             return {
#                 "success": False,
#                 "stdout": "",
#                 "stderr": f"Command timed out after {timeout} seconds",
#                 "return_code": -1,
#                 "duration": str(datetime.now() - start_time),
#                 "command": cmd
#             }
    
#         duration = datetime.now() - start_time
#         result = {
#             "success": return_code == 0,
#             "stdout": stdout,
#             "stderr": stderr,
#             "return_code": return_code,
#             "duration": str(duration),
#             "command": cmd
#         }
        
#         # Add to history
#         command_history.append({
#             "timestamp": datetime.now().isoformat(),
#             "command": cmd,
#             "success": return_code == 0,
#             "cwd": cwd or os.getcwd()
#         })
        
#         # If history is too long, remove oldest record
#         if len(command_history) > MAX_HISTORY_SIZE:
#             command_history.pop(0)
            
#         return result
    
#     except Exception as e:
#         return {
#             "success": False,
#             "stdout": "",
#             "stderr": f"Error executing command: {str(e)}",
#             "return_code": -1,
#             "duration": str(datetime.now() - start_time),
#             "command": cmd
#         }

# def is_dangerous_command(command: str) -> bool:
#     """Check if command is potentially dangerous"""
#     dangerous_patterns = [
#         r"rm\s+-rf\s+/",     # rm -rf /
#         r"mkfs",             # filesystem formatting
#         r"dd\s+if.*of=/dev", # dd to devices
#         r":(){.*};:",        # fork bomb
#         r">(>)?.*/(etc|boot|var|usr)/(passwd|shadow|cron|fstab|grub|sysconfig)" # writing to system files
#     ]
    
#     return any(re.search(pattern, command, re.IGNORECASE) for pattern in dangerous_patterns)

# @mcp.tool()
# async def execute_command(command: str, timeout: int = 30, cwd: str = None, env: Dict = None) -> str:
#     """
#     Execute terminal command and return results
    
#     Args:
#         command: Command line command to execute
#         timeout: Command timeout in seconds, default is 30 seconds
#         cwd: Working directory for command execution
#         env: Environment variables for the command
    
#     Returns:
#         Output of the command execution
#     """
#     # Check for dangerous commands
#     if is_dangerous_command(command):
#         return "For security reasons, this command is not allowed."
    
#     result = await run_command(command, timeout, cwd, env)
    
#     if result["success"]:
#         output = f"Command executed successfully (duration: {result['duration']})\n\n"
        
#         if result["stdout"]:
#             output += f"Output:\n{result['stdout']}\n"
#         else:
#             output += "Command had no output.\n"
            
#         if result["stderr"]:
#             output += f"\nWarnings/Info:\n{result['stderr']}"
            
#         return output
#     else:
#         output = f"Command execution failed (duration: {result['duration']})\n"
        
#         if result["stdout"]:
#             output += f"\nOutput:\n{result['stdout']}\n"
            
#         if result["stderr"]:
#             output += f"\nError:\n{result['stderr']}"
            
#         output += f"\nReturn code: {result['return_code']}"
#         return output

# @mcp.tool()
# async def start_interactive_session(session_id: str = None) -> str:
#     """
#     Start a new interactive terminal session
    
#     Args:
#         session_id: Optional identifier for the session
    
#     Returns:
#         Session information
#     """
#     if not session_id:
#         session_id = f"terminal_{int(time.time())}"
    
#     if session_id in active_terminals:
#         return f"Session '{session_id}' already exists. Use a different session ID or attach to the existing session."
    
#     try:
#         # Create a pseudo-terminal process
#         if platform.system() == "Windows":
#             process = await asyncio.create_subprocess_shell(
#                 "cmd.exe",
#                 stdin=asyncio.subprocess.PIPE,
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.PIPE
#             )
#         else:
#             process = await asyncio.create_subprocess_shell(
#                 "/bin/bash",
#                 stdin=asyncio.subprocess.PIPE,
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.PIPE
#             )
            
#         active_terminals[session_id] = {
#             "process": process,
#             "created_at": datetime.now().isoformat(),
#             "last_activity": datetime.now().isoformat(),
#             "commands": []
#         }
        
#         # Read initial output
#         try:
#             stdout_data = await asyncio.wait_for(process.stdout.read(1024), 1.0)
#             initial_output = stdout_data.decode('utf-8', errors='replace')
#         except:
#             initial_output = ""
        
#         return f"Interactive terminal session '{session_id}' started successfully.\n\n{initial_output}"
    
#     except Exception as e:
#         return f"Error starting interactive session: {str(e)}"

# @mcp.tool()
# async def send_to_interactive_session(session_id: str, command: str) -> str:
#     """
#     Send command to an interactive terminal session
    
#     Args:
#         session_id: Identifier of the terminal session
#         command: Command to send to the terminal
    
#     Returns:
#         Command output
#     """
#     if session_id not in active_terminals:
#         return f"Error: Session '{session_id}' not found. Create a new session with start_interactive_session."
    
#     try:
#         session = active_terminals[session_id]
#         process = session["process"]
        
#         # Update last activity
#         session["last_activity"] = datetime.now().isoformat()
#         session["commands"].append({"command": command, "timestamp": datetime.now().isoformat()})
        
#         # Send command to process
#         process.stdin.write(f"{command}\n".encode('utf-8'))
#         await process.stdin.drain()
        
#         # Wait for output
#         await asyncio.sleep(0.5)  # Short delay to collect output
        
#         # Read output
#         stdout_chunk = b""
#         stderr_chunk = b""
        
#         try:
#             # Non-blocking read from stdout
#             while True:
#                 chunk = await asyncio.wait_for(process.stdout.read(1024), 0.1)
#                 if not chunk:
#                     break
#                 stdout_chunk += chunk
#         except asyncio.TimeoutError:
#             pass  # No more data available now
        
#         try:
#             # Non-blocking read from stderr
#             while True:
#                 chunk = await asyncio.wait_for(process.stderr.read(1024), 0.1)
#                 if not chunk:
#                     break
#                 stderr_chunk += chunk
#         except asyncio.TimeoutError:
#             pass  # No more data available now
        
#         stdout_output = stdout_chunk.decode('utf-8', errors='replace')
#         stderr_output = stderr_chunk.decode('utf-8', errors='replace')
        
#         output = f"Session '{session_id}' output:\n\n"
        
#         if stdout_output:
#             output += f"{stdout_output}\n"
            
#         if stderr_output:
#             output += f"Error output:\n{stderr_output}\n"
            
#         if not stdout_output and not stderr_output:
#             output += "(No output from command)\n"
            
#         return output
    
#     except Exception as e:
#         return f"Error sending command to session: {str(e)}"

# @mcp.tool()
# async def list_interactive_sessions() -> str:
#     """
#     List all active interactive terminal sessions
    
#     Returns:
#         List of active sessions and their details
#     """
#     if not active_terminals:
#         return "No active interactive terminal sessions."
    
#     output = "Active interactive terminal sessions:\n\n"
    
#     for session_id, session in active_terminals.items():
#         output += f"Session ID: {session_id}\n"
#         output += f"Created: {session['created_at']}\n"
#         output += f"Last activity: {session['last_activity']}\n"
#         output += f"Command count: {len(session['commands'])}\n"
#         output += "----------------------------------------\n"
    
#     return output

# @mcp.tool()
# async def terminate_interactive_session(session_id: str) -> str:
#     """
#     Terminate an interactive terminal session
    
#     Args:
#         session_id: Identifier of the terminal session
    
#     Returns:
#         Operation result
#     """
#     if session_id not in active_terminals:
#         return f"Error: Session '{session_id}' not found."
    
#     try:
#         session = active_terminals[session_id]
#         process = session["process"]
        
#         # Terminate the process
#         try:
#             process.kill()
#         except:
#             pass
        
#         # Remove from active sessions
#         del active_terminals[session_id]
        
#         return f"Interactive terminal session '{session_id}' terminated successfully."
    
#     except Exception as e:
#         return f"Error terminating session: {str(e)}"

# @mcp.tool()
# async def get_command_history(count: int = 10) -> str:
#     """
#     Get recent command execution history
    
#     Args:
#         count: Number of recent commands to return
    
#     Returns:
#         Formatted command history record
#     """
#     if not command_history:
#         return "No command execution history."
    
#     count = min(count, len(command_history))
#     recent_commands = command_history[-count:]
    
#     output = f"Recent {count} command history:\n\n"
    
#     for i, cmd in enumerate(recent_commands):
#         status = "✓" if cmd["success"] else "✗"
#         dir_info = f" [in {cmd['cwd']}]" if 'cwd' in cmd else ""
#         output += f"{i+1}. [{status}] {cmd['timestamp']}{dir_info}: {cmd['command']}\n"
    
#     return output

# @mcp.tool()
# async def get_current_directory() -> str:
#     """
#     Get current working directory
    
#     Returns:
#         Path of current working directory
#     """
#     return os.getcwd()

# @mcp.tool()
# async def change_directory(path: str) -> str:
#     """
#     Change current working directory
    
#     Args:
#         path: Directory path to switch to
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Expand user directory (e.g., ~/)
#         expanded_path = os.path.expanduser(path)
        
#         os.chdir(expanded_path)
#         return f"Switched to directory: {os.getcwd()}"
#     except FileNotFoundError:
#         return f"Error: Directory '{path}' does not exist"
#     except PermissionError:
#         return f"Error: No permission to access directory '{path}'"
#     except Exception as e:
#         return f"Error changing directory: {str(e)}"

# @mcp.tool()
# async def list_directory(path: Optional[str] = None, show_hidden: bool = False, 
#                         details: bool = False, pattern: str = None) -> str:
#     """
#     List files and subdirectories in the specified directory
    
#     Args:
#         path: Directory path to list contents, default is current directory
#         show_hidden: Whether to show hidden files and directories
#         details: Whether to show detailed information (size, permissions, dates)
#         pattern: Optional glob pattern to filter files (e.g., "*.txt")
    
#     Returns:
#         List of directory contents
#     """
#     if path is None:
#         path = os.getcwd()
    
#     # Expand user directory (e.g., ~/)
#     path = os.path.expanduser(path)
    
#     try:
#         # Get all items
#         all_items = os.listdir(path)
        
#         # Apply filter if pattern specified
#         if pattern:
#             matched_items = []
#             for item in all_items:
#                 if glob.fnmatch.fnmatch(item, pattern):
#                     matched_items.append(item)
#             items = matched_items
#         else:
#             items = all_items
        
#         # Filter hidden files if not show_hidden
#         if not show_hidden:
#             items = [item for item in items if not item.startswith('.')]
        
#         dirs = []
#         files = []
        
#         for item in items:
#             full_path = os.path.join(path, item)
            
#             # Basic information
#             is_dir = os.path.isdir(full_path)
            
#             # If details are requested, get file stats
#             if details:
#                 stats = os.stat(full_path)
#                 size = stats.st_size
#                 mod_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
#                 # Format permissions (Unix-style even on Windows for consistency)
#                 perms = ""
#                 if platform.system() != "Windows":
#                     mode = stats.st_mode
#                     perms = "d" if is_dir else "-"
#                     perms += "r" if mode & 0o400 else "-"
#                     perms += "w" if mode & 0o200 else "-"
#                     perms += "x" if mode & 0o100 else "-"
#                     perms += "r" if mode & 0o040 else "-"
#                     perms += "w" if mode & 0o020 else "-"
#                     perms += "x" if mode & 0o010 else "-"
#                     perms += "r" if mode & 0o004 else "-"
#                     perms += "w" if mode & 0o002 else "-"
#                     perms += "x" if mode & 0o001 else "-"
#                 else:
#                     # Simplified permissions for Windows
#                     perms = "d" if is_dir else "-"
#                     perms += "r" if os.access(full_path, os.R_OK) else "-"
#                     perms += "w" if os.access(full_path, os.W_OK) else "-"
#                     perms += "x" if os.access(full_path, os.X_OK) else "-"
#                     perms += "------"  # Placeholder for group/other perms
                
#                 # Format size in human-readable format
#                 if size < 1024:
#                     size_str = f"{size} B"
#                 elif size < 1024 * 1024:
#                     size_str = f"{size/1024:.1f} KB"
#                 elif size < 1024 * 1024 * 1024:
#                     size_str = f"{size/(1024*1024):.1f} MB"
#                 else:
#                     size_str = f"{size/(1024*1024*1024):.1f} GB"
                
#                 if is_dir:
#                     dirs.append((f"📁 {item}/", perms, size_str, mod_time))
#                 else:
#                     files.append((f"📄 {item}", perms, size_str, mod_time))
#             else:
#                 # Simple listing without details
#                 if is_dir:
#                     dirs.append(f"📁 {item}/")
#                 else:
#                     files.append(f"📄 {item}")
        
#         # Sort directories and files
#         dirs.sort()
#         files.sort()
        
#         if not dirs and not files:
#             return f"Directory '{path}' is empty"
        
#         output = f"Contents of directory '{path}':\n\n"
        
#         if details:
#             # Format with details
#             output += f"{'Type':<30} {'Permissions':<12} {'Size':<10} {'Modified':<20}\n"
#             output += "-" * 75 + "\n"
            
#             for dir_info in dirs:
#                 output += f"{dir_info[0]:<30} {dir_info[1]:<12} {dir_info[2]:<10} {dir_info[3]:<20}\n"
            
#             for file_info in files:
#                 output += f"{file_info[0]:<30} {file_info[1]:<12} {file_info[2]:<10} {file_info[3]:<20}\n"
#         else:
#             # Simple format
#             if dirs:
#                 output += "Directories:\n"
#                 output += "\n".join(dirs) + "\n\n"
            
#             if files:
#                 output += "Files:\n"
#                 output += "\n".join(files)
        
#         # Add count summary
#         output += f"\n\nTotal: {len(dirs)} directories, {len(files)} files"
#         if pattern:
#             output += f" (filtered by pattern: {pattern})"
        
#         return output
    
#     except FileNotFoundError:
#         return f"Error: Directory '{path}' does not exist"
#     except PermissionError:
#         return f"Error: No permission to access directory '{path}'"
#     except Exception as e:
#         return f"Error listing directory contents: {str(e)}"

# @mcp.tool()
# async def create_directory(path: str, parents: bool = True) -> str:
#     """
#     Create a new directory
    
#     Args:
#         path: Path of the directory to create
#         parents: Whether to create parent directories if they don't exist
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Expand user directory (e.g., ~/)
#         path = os.path.expanduser(path)
        
#         if os.path.exists(path):
#             if os.path.isdir(path):
#                 return f"Directory '{path}' already exists"
#             else:
#                 return f"Error: Path '{path}' exists but is not a directory"
        
#         if parents:
#             os.makedirs(path)
#         else:
#             os.mkdir(path)
        
#         return f"Successfully created directory: {path}"
    
#     except PermissionError:
#         return f"Error: No permission to create directory '{path}'"
#     except Exception as e:
#         return f"Error creating directory: {str(e)}"

# @mcp.tool()
# async def delete_directory(path: str, recursive: bool = False, force: bool = False) -> str:
#     """
#     Delete a directory
    
#     Args:
#         path: Path of the directory to delete
#         recursive: Whether to recursively delete subdirectories and files
#         force: Whether to ignore errors during deletion
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Expand user directory (e.g., ~/)
#         path = os.path.expanduser(path)
        
#         if not os.path.exists(path):
#             return f"Error: Directory '{path}' does not exist"
        
#         if not os.path.isdir(path):
#             return f"Error: Path '{path}' exists but is not a directory"
        
#         if recursive:
#             try:
#                 if force:
#                     def onerror(func, path, exc_info):
#                         # Just log the error and continue
#                         pass
                    
#                     shutil.rmtree(path, onerror=onerror if force else None)
#                 else:
#                     shutil.rmtree(path)
#             except Exception as e:
#                 return f"Error deleting directory recursively: {str(e)}"
#         else:
#             try:
#                 os.rmdir(path)
#             except OSError as e:
#                 if "not empty" in str(e).lower():
#                     return f"Error: Directory '{path}' is not empty. Use recursive=True to delete non-empty directories."
#                 else:
#                     return f"Error deleting directory: {str(e)}"
        
#         return f"Successfully deleted directory: {path}"
    
#     except PermissionError:
#         return f"Error: No permission to delete directory '{path}'"
#     except Exception as e:
#         return f"Error deleting directory: {str(e)}"

# @mcp.tool()
# async def copy_item(source: str, destination: str, recursive: bool = True) -> str:
#     """
#     Copy a file or directory
    
#     Args:
#         source: Path of the source file or directory
#         destination: Path of the destination
#         recursive: Whether to copy directories recursively (for directories)
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Expand user directory (e.g., ~/)
#         source = os.path.expanduser(source)
#         destination = os.path.expanduser(destination)
        
#         if not os.path.exists(source):
#             return f"Error: Source '{source}' does not exist"
        
#         # Check if source is a file or directory
#         if os.path.isfile(source):
#             # Copy file
#             shutil.copy2(source, destination)
#             return f"Successfully copied file from '{source}' to '{destination}'"
#         elif os.path.isdir(source):
#             # Copy directory
#             if not recursive:
#                 return f"Error: Source '{source}' is a directory. Use recursive=True to copy directories."
            
#             # Check if destination exists
#             if os.path.exists(destination):
#                 if not os.path.isdir(destination):
#                     return f"Error: Destination '{destination}' exists but is not a directory"
                
#                 # If destination is a directory, append source basename
#                 dest_path = os.path.join(destination, os.path.basename(source))
#             else:
#                 dest_path = destination
            
#             shutil.copytree(source, dest_path)
#             return f"Successfully copied directory from '{source}' to '{dest_path}'"
#         else:
#             return f"Error: Source '{source}' is neither a file nor a directory"
    
#     except PermissionError:
#         return f"Error: Permission denied while copying"
#     except shutil.Error as e:
#         errors = str(e)
#         return f"Error copying items: {errors}"
#     except Exception as e:
#         return f"Error copying: {str(e)}"

# @mcp.tool()
# async def move_item(source: str, destination: str) -> str:
#     """
#     Move a file or directory
    
#     Args:
#         source: Path of the source file or directory
#         destination: Path of the destination
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Expand user directory (e.g., ~/)
#         source = os.path.expanduser(source)
#         destination = os.path.expanduser(destination)
        
#         if not os.path.exists(source):
#             return f"Error: Source '{source}' does not exist"
        
#         # Move the item
#         shutil.move(source, destination)
        
#         if os.path.isfile(source):
#             return f"Successfully moved file from '{source}' to '{destination}'"
#         else:
#             return f"Successfully moved directory from '{source}' to '{destination}'"
    
#     except PermissionError:
#         return f"Error: Permission denied while moving"
#     except shutil.Error as e:
#         errors = str(e)
#         return f"Error moving items: {errors}"
#     except Exception as e:
#         return f"Error moving: {str(e)}"

# @mcp.tool()
# async def rename_item(path: str, new_name: str) -> str:
#     """
#     Rename a file or directory
    
#     Args:
#         path: Path of the file or directory to rename
#         new_name: New name for the file or directory
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Expand user directory (e.g., ~/)
#         path = os.path.expanduser(path)
        
#         if not os.path.exists(path):
#             return f"Error: Item '{path}' does not exist"
        
#         # Get the directory of the original path
#         directory = os.path.dirname(path)
        
#         # Create the new path by combining the directory and new name
#         new_path = os.path.join(directory, new_name)
        
#         # Check if the new path already exists
#         if os.path.exists(new_path):
#             return f"Error: An item with the name '{new_name}' already exists at '{directory}'"
        
#         # Rename the item
#         os.rename(path, new_path)
        
#         if os.path.isfile(new_path):
#             return f"Successfully renamed file from '{path}' to '{new_path}'"
#         else:
#             return f"Successfully renamed directory from '{path}' to '{new_path}'"
    
#     except PermissionError:
#         return f"Error: Permission denied while renaming"
#     except Exception as e:
#         return f"Error renaming: {str(e)}"

# @mcp.tool()
# async def get_file_info(path: str) -> str:
#     """
#     Get detailed information about a file or directory
    
#     Args:
#         path: Path of the file or directory
    
#     Returns:
#         Detailed information about the file or directory
#     """
#     try:
#         # Expand user directory (e.g., ~/)
#         path = os.path.expanduser(path)
        
#         if not os.path.exists(path):
#             return f"Error: Item '{path}' does not exist"
        
#         # Get basic information
#         is_dir = os.path.isdir(path)
#         item_type = "Directory" if is_dir else "File"
        
#         # Get file stats
#         stats = os.stat(path)
#         size = stats.st_size
#         created_time = datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
#         mod_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
#         accessed_time = datetime.fromtimestamp(stats.st_atime).strftime('%Y-%m-%d %H:%M:%S')
        
#         # Format permissions
#         if platform.system() != "Windows":
#             mode = stats.st_mode
#             perms = "d" if is_dir else "-"
#             perms += "r" if mode & 0o400 else "-"
#             perms += "w" if mode & 0o200 else "-"
#             perms += "x" if mode & 0o100 else "-"
#             perms += "r" if mode & 0o040 else "-"
#             perms += "w" if mode & 0o020 else "-"
#             perms += "x" if mode & 0o010 else "-"
#             perms += "r" if mode & 0o004 else "-"
#             perms += "w" if mode & 0o002 else "-"
#             perms += "x" if mode & 0o001 else "-"
#         else:
#             # Simplified permissions for Windows
#             perms = "d" if is_dir else "-"
#             perms += "r" if os.access(path, os.R_OK) else "-"
#             perms += "w" if os.access(path, os.W_OK) else "-"
#             perms += "x" if os.access(path, os.X_OK) else "-"
#             perms += "------"  # Placeholder for group/other perms
        
#         # Format size in human-readable format
#         if size < 1024:
#             size_str = f"{size} bytes"
#         elif size < 1024 * 1024:
#             size_str = f"{size/1024:.1f} KB ({size} bytes)"
#         elif size < 1024 * 1024 * 1024:
#             size_str = f"{size/(1024*1024):.1f} MB ({size} bytes)"
#         else:
#             size_str = f"{size/(1024*1024*1024):.1f} GB ({size} bytes)"
        
#         # Get additional directory information if applicable
#         if is_dir:
#             try:
#                 items = os.listdir(path)
#                 num_files = sum(1 for item in items if os.path.isfile(os.path.join(path, item)))
#                 num_dirs = sum(1 for item in items if os.path.isdir(os.path.join(path, item)))
#                 dir_info = f"Contains: {num_files} files, {num_dirs} directories"
#             except:
#                 dir_info = "Could not read directory contents"
#         else:
#             # Get file extension and mime type
#             _, ext = os.path.splitext(path)
#             ext = ext.lower()
            
#             # Try to determine if it's a text file
#             try:
#                 is_text = False
#                 with open(path, 'rb') as f:
#                     chunk = f.read(1024)
#                     # Simple heuristic: if the chunk contains null bytes, it's likely binary
#                     is_text = b'\x00' not in chunk
#                 file_type = "Text file" if is_text else "Binary file"
#             except:
#                 file_type = "Unknown file type"
        
#         # Build output
#         output = f"Information for: {path}\n\n"
#         output += f"Type: {item_type}\n"
#         if not is_dir:
#             output += f"File type: {file_type}\n"
#             output += f"Extension: {ext if ext else 'None'}\n"
#         output += f"Size: {size_str}\n"
#         output += f"Permissions: {perms}\n"
#         output += f"Created: {created_time}\n"
#         output += f"Modified: {mod_time}\n"
#         output += f"Last accessed: {accessed_time}\n"
        
#         if is_dir:
#             output += f"\n{dir_info}\n"
        
#         return output
    
#     except PermissionError:
#         return f"Error: Permission denied while accessing '{path}'"
#     except Exception as e:
#         return f"Error getting file information: {str(e)}"

# @mcp.tool()
# async def find_files(pattern: str, path: str = None, recursive: bool = True, 
#                     case_sensitive: bool = True, max_results: int = 100) -> str:
#     """
#     Find files matching a pattern
    
#     Args:
#         pattern: Glob pattern to match (e.g., "*.txt" or "**/*.py")
#         path: Directory to search in, default is current directory
#         recursive: Whether to search recursively in subdirectories
#         case_sensitive: Whether to perform case-sensitive matching
#         max_results: Maximum number of results to return
    
#     Returns:
#         List of matching files
#     """
#     try:
#         # Use current directory if path is not specified
#         if path is None:
#             path = os.getcwd()
        
#         # Expand user directory (e.g., ~/)
#         path = os.path.expanduser(path)
        
#         if not os.path.exists(path):
#             return f"Error: Path '{path}' does not exist"
        
#         if not os.path.isdir(path):
#             return f"Error: Path '{path}' is not a directory"
        
#         # Prepare matching function
#         if recursive:
#             # Use Path.glob for recursive searching with **
#             if not pattern.startswith("**/") and not pattern.startswith("**\\"):
#                 search_pattern = f"**/{pattern}"
#             else:
#                 search_pattern = pattern
                
#             search_path = Path(path)
            
#             if case_sensitive:
#                 matches = list(search_path.glob(search_pattern))
#             else:
#                 # For case-insensitive search, convert to lowercase and compare
#                 search_pattern_lower = search_pattern.lower()
#                 all_files = list(search_path.glob("**/*"))
#                 matches = []
                
#                 for file in all_files:
#                     if fnmatch.fnmatch(str(file).lower(), 
#                                        os.path.join(str(search_path).lower(), search_pattern_lower)):
#                         matches.append(file)
#         else:
#             # Non-recursive search
#             search_path = Path(path)
            
#             if case_sensitive:
#                 matches = list(search_path.glob(pattern))
#             else:
#                 # For case-insensitive search
#                 all_files = list(search_path.glob("*"))
#                 matches = []
                
#                 for file in all_files:
#                     if fnmatch.fnmatch(str(file).lower(), 
#                                        os.path.join(str(search_path).lower(), pattern.lower())):
#                         matches.append(file)
        
#         # Limit results
#         if len(matches) > max_results:
#             result_message = f"Found {len(matches)} matches (showing first {max_results}):"
#             matches = matches[:max_results]
#         elif len(matches) > 0:
#             result_message = f"Found {len(matches)} matches:"
#         else:
#             return f"No files matching '{pattern}' found in '{path}'"
        
#         # Format results
#         output = f"{result_message}\n\n"
        
#         for match in matches:
#             # Get relative path for cleaner output
#             rel_path = os.path.relpath(match, path)
#             output += f"📄 {rel_path}\n"
        
#         return output
    
#     except Exception as e:
#         return f"Error finding files: {str(e)}"

# @mcp.tool()
# async def grep_search(pattern: str, path: str = None, recursive: bool = True, 
#                     case_sensitive: bool = True, max_results: int = 100) -> str:
#     """
#     Search for text pattern in files
    
#     Args:
#         pattern: Text pattern to search for
#         path: File or directory to search in, default is current directory
#         recursive: Whether to search recursively in subdirectories
#         case_sensitive: Whether to perform case-sensitive matching
#         max_results: Maximum number of matching lines to return
    
#     Returns:
#         Lines matching the pattern
#     """
#     try:
#         # Use current directory if path is not specified
#         if path is None:
#             path = os.getcwd()
        
#         # Expand user directory (e.g., ~/)
#         path = os.path.expanduser(path)
        
#         if not os.path.exists(path):
#             return f"Error: Path '{path}' does not exist"
        
#         results = []
        
#         # Compile regex pattern
#         try:
#             if case_sensitive:
#                 regex = re.compile(pattern)
#             else:
#                 regex = re.compile(pattern, re.IGNORECASE)
#         except re.error as e:
#             return f"Error: Invalid regex pattern: {str(e)}"
        
#         # Search in a single file
#         if os.path.isfile(path):
#             try:
#                 with open(path, 'r', encoding='utf-8', errors='replace') as file:
#                     for i, line in enumerate(file, 1):
#                         if regex.search(line):
#                             results.append((path, i, line.rstrip('\n')))
#                             if len(results) >= max_results:
#                                 break
#             except Exception as e:
#                 return f"Error reading file '{path}': {str(e)}"
#         # Search in directory
#         elif os.path.isdir(path):
#             # Get all files
#             if recursive:
#                 file_list = []
#                 for root, _, files in os.walk(path):
#                     for file in files:
#                         file_path = os.path.join(root, file)
#                         file_list.append(file_path)
#             else:
#                 file_list = [os.path.join(path, f) for f in os.listdir(path) 
#                             if os.path.isfile(os.path.join(path, f))]
            
#             # Search in each file
#             for file_path in file_list:
#                 try:
#                     with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
#                         for i, line in enumerate(file, 1):
#                             if regex.search(line):
#                                 results.append((file_path, i, line.rstrip('\n')))
#                                 if len(results) >= max_results:
#                                     break
                    
#                     if len(results) >= max_results:
#                         break
#                 except:
#                     # Skip files that can't be read as text
#                     continue
#         else:
#             return f"Error: Path '{path}' is neither a file nor a directory"
        
#         # Format results
#         if not results:
#             return f"No matches found for pattern '{pattern}'"
        
#         if len(results) == max_results:
#             output = f"Found at least {len(results)} matches (results limited to {max_results}):\n\n"
#         else:
#             output = f"Found {len(results)} matches:\n\n"
        
#         for file_path, line_num, line_content in results:
#             # Get relative path for cleaner output
#             rel_path = os.path.relpath(file_path, os.getcwd())
#             # Truncate long lines
#             if len(line_content) > 150:
#                 line_content = line_content[:147] + "..."
#             output += f"{rel_path}:{line_num}: {line_content}\n"
        
#         return output
    
#     except Exception as e:
#         return f"Error searching for pattern: {str(e)}"

# @mcp.tool()
# async def compress_items(source_paths: List[str], destination: str, 
#                         archive_type: str = "zip", compression_level: int = None) -> str:
#     """
#     Compress files and directories into an archive
    
#     Args:
#         source_paths: List of paths to compress
#         destination: Path of the destination archive
#         archive_type: Type of archive ("zip" or "tar" or "tar.gz" or "tar.bz2")
#         compression_level: Compression level (1-9, higher means better compression)
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Expand user directory in paths
#         source_paths = [os.path.expanduser(p) for p in source_paths]
#         destination = os.path.expanduser(destination)
        
#         # Verify source paths exist
#         for path in source_paths:
#             if not os.path.exists(path):
#                 return f"Error: Source path '{path}' does not exist"
        
#         # Create archive based on type
#         if archive_type.lower() == "zip":
#             # Set compression level
#             compression = zipfile.ZIP_DEFLATED
#             compresslevel = compression_level if compression_level is not None else 6
            
#             # Create zip archive
#             with zipfile.ZipFile(destination, 'w', compression=compression, compresslevel=compresslevel) as zip_file:
#                 for path in source_paths:
#                     if os.path.isfile(path):
#                         # Add file with relative path
#                         arcname = os.path.basename(path)
#                         zip_file.write(path, arcname=arcname)
#                     elif os.path.isdir(path):
#                         # Add all files in directory with relative paths
#                         basedir = os.path.basename(path)
#                         for root, _, files in os.walk(path):
#                             for file in files:
#                                 file_path = os.path.join(root, file)
#                                 # Calculate path within archive
#                                 arcname = os.path.join(basedir, os.path.relpath(file_path, path))
#                                 zip_file.write(file_path, arcname=arcname)
        
#         elif archive_type.lower() in ["tar", "tar.gz", "tar.bz2"]:
#             # Determine compression mode
#             if archive_type.lower() == "tar":
#                 mode = "w"
#             elif archive_type.lower() == "tar.gz":
#                 mode = "w:gz"
#             else:  # tar.bz2
#                 mode = "w:bz2"
            
#             # Create tar archive
#             with tarfile.open(destination, mode) as tar_file:
#                 for path in source_paths:
#                     # Add path to archive
#                     arcname = os.path.basename(path)
#                     tar_file.add(path, arcname=arcname)
        
#         else:
#             return f"Error: Unsupported archive type '{archive_type}'. Use 'zip', 'tar', 'tar.gz', or 'tar.bz2'."
        
#         # Verify archive was created
#         if os.path.exists(destination):
#             size = os.path.getsize(destination)
#             # Format size
#             if size < 1024:
#                 size_str = f"{size} bytes"
#             elif size < 1024 * 1024:
#                 size_str = f"{size/1024:.1f} KB"
#             elif size < 1024 * 1024 * 1024:
#                 size_str = f"{size/(1024*1024):.1f} MB"
#             else:
#                 size_str = f"{size/(1024*1024*1024):.1f} GB"
                
#             return f"Successfully created {archive_type} archive at '{destination}' ({size_str})."
#         else:
#             return f"Archive creation completed, but unable to verify archive exists at '{destination}'."
    
#     except Exception as e:
#         return f"Error creating archive: {str(e)}"

# @mcp.tool()
# async def extract_archive(source: str, destination: str = None, preserve_structure: bool = True) -> str:
#     """
#     Extract files from an archive
    
#     Args:
#         source: Path of the archive to extract
#         destination: Directory to extract to (optional, defaults to current directory)
#         preserve_structure: Whether to preserve the archive's directory structure
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Expand user directory in paths
#         source = os.path.expanduser(source)
        
#         if not os.path.exists(source):
#             return f"Error: Archive '{source}' does not exist"
        
#         if not os.path.isfile(source):
#             return f"Error: '{source}' is not a file"
        
#         # Use current directory if destination is not specified
#         if destination is None:
#             destination = os.getcwd()
#         else:
#             destination = os.path.expanduser(destination)
        
#         # Create destination directory if it doesn't exist
#         if not os.path.exists(destination):
#             os.makedirs(destination)
        
#         # Determine archive type
#         if source.lower().endswith('.zip'):
#             # Extract zip archive
#             with zipfile.ZipFile(source, 'r') as zip_file:
#                 if preserve_structure:
#                     zip_file.extractall(destination)
#                 else:
#                     # Extract without directory structure
#                     for member in zip_file.namelist():
#                         filename = os.path.basename(member)
#                         if not filename:  # Skip directories
#                             continue
                        
#                         # Extract file
#                         with zip_file.open(member) as source_file, \
#                              open(os.path.join(destination, filename), 'wb') as target_file:
#                             shutil.copyfileobj(source_file, target_file)
        
#         elif source.lower().endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2')):
#             # Extract tar archive
#             with tarfile.open(source, 'r:*') as tar_file:
#                 if preserve_structure:
#                     tar_file.extractall(destination)
#                 else:
#                     # Extract without directory structure
#                     for member in tar_file.getmembers():
#                         if member.isfile():
#                             filename = os.path.basename(member.name)
#                             member.name = filename
#                             tar_file.extract(member, destination)
        
#         else:
#             return f"Error: Unsupported archive format. Supported formats: zip, tar, tar.gz, tar.bz2"
        
#         return f"Successfully extracted archive '{source}' to '{destination}'."
    
#     except Exception as e:
#         return f"Error extracting archive: {str(e)}"

# @mcp.tool()
# async def get_system_info() -> str:
#     """
#     Get detailed system information
    
#     Returns:
#         System information including OS, CPU, memory, disk space
#     """
#     try:
#         # Basic system info
#         system_info = {
#             "os": {
#                 "name": platform.system(),
#                 "version": platform.version(),
#                 "release": platform.release(),
#                 "platform": platform.platform(),
#                 "machine": platform.machine(),
#                 "processor": platform.processor()
#             },
#             "python": {
#                 "version": platform.python_version(),
#                 "implementation": platform.python_implementation(),
#                 "compiler": platform.python_compiler()
#             },
#             "time": {
#                 "current_time": datetime.now().isoformat(),
#                 "timezone": time.tzname
#             }
#         }
        
#         # CPU info
#         cpu_info = {
#             "physical_cores": psutil.cpu_count(logical=False),
#             "logical_cores": psutil.cpu_count(),
#             "cpu_percent": psutil.cpu_percent(interval=0.5),
#             "cpu_freq": {
#                 "current": psutil.cpu_freq().current if psutil.cpu_freq() else None,
#                 "min": psutil.cpu_freq().min if psutil.cpu_freq() else None,
#                 "max": psutil.cpu_freq().max if psutil.cpu_freq() else None
#             }
#         }
        
#         # Memory info
#         memory = psutil.virtual_memory()
#         memory_info = {
#             "total": memory.total,
#             "available": memory.available,
#             "used": memory.used,
#             "percent": memory.percent
#         }
        
#         # Disk info
#         disk_info = []
#         for partition in psutil.disk_partitions():
#             try:
#                 usage = psutil.disk_usage(partition.mountpoint)
#                 disk_info.append({
#                     "device": partition.device,
#                     "mountpoint": partition.mountpoint,
#                     "fstype": partition.fstype,
#                     "total": usage.total,
#                     "used": usage.used,
#                     "free": usage.free,
#                     "percent": usage.percent
#                 })
#             except:
#                 # Skip partitions that can't be accessed
#                 continue
        
#         # Network info
#         network_info = {
#             "hostname": socket.gethostname(),
#             "interfaces": psutil.net_if_addrs()
#         }
        
#         # Format output
#         output = "System Information\n"
#         output += "=================\n\n"
        
#         # OS info
#         output += "Operating System:\n"
#         output += f"  Name: {system_info['os']['name']}\n"
#         output += f"  Version: {system_info['os']['version']}\n"
#         output += f"  Release: {system_info['os']['release']}\n"
#         output += f"  Platform: {system_info['os']['platform']}\n"
#         output += f"  Machine: {system_info['os']['machine']}\n"
#         output += f"  Processor: {system_info['os']['processor']}\n\n"
        
#         # Python info
#         output += "Python:\n"
#         output += f"  Version: {system_info['python']['version']}\n"
#         output += f"  Implementation: {system_info['python']['implementation']}\n"
#         output += f"  Compiler: {system_info['python']['compiler']}\n\n"
        
#         # CPU info
#         output += "CPU:\n"
#         output += f"  Physical cores: {cpu_info['physical_cores']}\n"
#         output += f"  Logical cores: {cpu_info['logical_cores']}\n"
#         output += f"  CPU usage: {cpu_info['cpu_percent']}%\n"
#         if cpu_info['cpu_freq']['current']:
#             output += f"  CPU frequency: {cpu_info['cpu_freq']['current']} MHz\n\n"
#         else:
#             output += "\n"
        
#         # Memory info
#         output += "Memory:\n"
#         output += f"  Total: {memory_info['total'] / (1024**3):.2f} GB\n"
#         output += f"  Available: {memory_info['available'] / (1024**3):.2f} GB\n"
#         output += f"  Used: {memory_info['used'] / (1024**3):.2f} GB\n"
#         output += f"  Usage: {memory_info['percent']}%\n\n"
        
#         # Disk info
#         output += "Disk:\n"
#         for disk in disk_info:
#             output += f"  {disk['mountpoint']} ({disk['device']}):\n"
#             output += f"    Type: {disk['fstype']}\n"
#             output += f"    Total: {disk['total'] / (1024**3):.2f} GB\n"
#             output += f"    Used: {disk['used'] / (1024**3):.2f} GB\n"
#             output += f"    Free: {disk['free'] / (1024**3):.2f} GB\n"
#             output += f"    Usage: {disk['percent']}%\n"
#         output += "\n"
        
#         # Network info
#         output += "Network:\n"
#         output += f"  Hostname: {network_info['hostname']}\n"
#         output += "  Network Interfaces:\n"
#         for interface, addrs in network_info['interfaces'].items():
#             output += f"    {interface}:\n"
#             for addr in addrs:
#                 if addr.family == socket.AF_INET:
#                     output += f"      IPv4: {addr.address}\n"
#                 elif addr.family == socket.AF_INET6:
#                     output += f"      IPv6: {addr.address}\n"
        
#         return output
    
#     except Exception as e:
#         return f"Error getting system information: {str(e)}"

# @mcp.tool()
# async def get_environment_variables(filter_pattern: str = None) -> str:
#     """
#     Get environment variables
    
#     Args:
#         filter_pattern: Optional pattern to filter environment variables
    
#     Returns:
#         List of environment variables and their values
#     """
#     try:
#         env_vars = dict(os.environ)
        
#         # Apply filter if specified
#         if filter_pattern:
#             filtered_vars = {}
#             for key, value in env_vars.items():
#                 if filter_pattern.lower() in key.lower():
#                     filtered_vars[key] = value
#             env_vars = filtered_vars
        
#         if not env_vars:
#             if filter_pattern:
#                 return f"No environment variables matching '{filter_pattern}' found."
#             else:
#                 return "No environment variables found."
        
#         # Sort keys
#         sorted_keys = sorted(env_vars.keys())
        
#         output = "Environment Variables:\n\n"
        
#         for key in sorted_keys:
#             value = env_vars[key]
#             output += f"{key} = {value}\n"
        
#         return output
    
#     except Exception as e:
#         return f"Error getting environment variables: {str(e)}"

# @mcp.tool()
# async def set_environment_variable(name: str, value: str) -> str:
#     """
#     Set an environment variable
    
#     Args:
#         name: Name of the environment variable
#         value: Value to set
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Set the environment variable
#         os.environ[name] = value
        
#         return f"Environment variable '{name}' set to '{value}'."
    
#     except Exception as e:
#         return f"Error setting environment variable: {str(e)}"

# @mcp.tool()
# async def get_processes(sort_by: str = "cpu", count: int = 10) -> str:
#     """
#     Get list of running processes
    
#     Args:
#         sort_by: Field to sort by ("cpu", "memory", "pid", "name")
#         count: Number of processes to show
    
#     Returns:
#         List of running processes
#     """
#     try:
#         processes = []
        
#         for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time']):
#             try:
#                 # Get process info
#                 proc_info = proc.info
#                 proc_info['cpu_percent'] = proc.cpu_percent(interval=0.1)
#                 proc_info['memory_percent'] = proc.memory_percent()
                
#                 # Format create time
#                 create_time = datetime.fromtimestamp(proc_info['create_time']).strftime("%Y-%m-%d %H:%M:%S")
#                 proc_info['create_time_str'] = create_time
                
#                 processes.append(proc_info)
#             except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#                 pass
        
#         # Sort processes
#         if sort_by.lower() == "cpu":
#             processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
#         elif sort_by.lower() == "memory":
#             processes.sort(key=lambda x: x['memory_percent'], reverse=True)
#         elif sort_by.lower() == "pid":
#             processes.sort(key=lambda x: x['pid'])
#         elif sort_by.lower() == "name":
#             processes.sort(key=lambda x: x['name'].lower())
#         else:
#             return f"Error: Invalid sort field '{sort_by}'. Use 'cpu', 'memory', 'pid', or 'name'."
        
#         # Limit to requested count
#         processes = processes[:count]
        
#         # Format output
#         output = f"Top {len(processes)} processes (sorted by {sort_by}):\n\n"
#         output += f"{'PID':<8} {'CPU %':<8} {'MEM %':<8} {'User':<15} {'Started':<20} Process\n"
#         output += "-" * 75 + "\n"
        
#         for proc in processes:
#             output += f"{proc['pid']:<8} {proc['cpu_percent']:<8.1f} {proc['memory_percent']:<8.1f} "
#             output += f"{proc['username'][:15]:<15} {proc['create_time_str']:<20} {proc['name']}\n"
        
#         return output
    
#     except Exception as e:
#         return f"Error getting process list: {str(e)}"

# @mcp.tool()
# async def kill_process(pid: int) -> str:
#     """
#     Kill a process by PID
    
#     Args:
#         pid: Process ID to kill
    
#     Returns:
#         Operation result information
#     """
#     try:
#         # Check if process exists
#         if not psutil.pid_exists(pid):
#             return f"Error: Process with PID {pid} does not exist."
        
#         # Get process info
#         process = psutil.Process(pid)
#         process_name = process.name()
        
#         # Kill the process
#         process.kill()
        
#         # Verify process is gone
#         if not psutil.pid_exists(pid):
#             return f"Successfully killed process {process_name} (PID: {pid})."
#         else:
#             return f"Process {process_name} (PID: {pid}) was signaled to terminate but may still be running."
    
#     except psutil.NoSuchProcess:
#         return f"Error: Process with PID {pid} does not exist."
#     except psutil.AccessDenied:
#         return f"Error: No permission to kill process with PID {pid}."
#     except Exception as e:
#         return f"Error killing process: {str(e)}"

# @mcp.tool()
# async def ping_host(host: str, count: int = 4, timeout: int = 5) -> str:
#     """
#     Ping a host
    
#     Args:
#         host: Hostname or IP address to ping
#         count: Number of ping packets to send
#         timeout: Timeout in seconds
    
#     Returns:
#         Ping results
#     """
#     try:
#         # Determine the ping command based on OS
#         if platform.system().lower() == "windows":
#             command = f"ping -n {count} -w {timeout * 1000} {host}"
#         else:
#             command = f"ping -c {count} -W {timeout} {host}"
        
#         result = await run_command(command)
        
#         if result["success"]:
#             return f"Ping to {host} succeeded:\n\n{result['stdout']}"
#         else:
#             return f"Ping to {host} failed:\n\n{result['stderr']}"
    
#     except Exception as e:
#         return f"Error pinging host: {str(e)}"

# @mcp.tool()
# async def http_request(url: str, method: str = "GET", headers: Dict = None, 
#                       data: str = None, timeout: int = 30) -> str:
#     """
#     Make an HTTP request
    
#     Args:
#         url: URL to request
#         method: HTTP method (GET, POST, PUT, DELETE)
#         headers: HTTP headers as a dictionary
#         data: Request body data
#         timeout: Request timeout in seconds
    
#     Returns:
#         HTTP response
#     """
#     try:
#         # Ensure URL has a scheme
#         if not url.startswith('http://') and not url.startswith('https://'):
#             url = 'https://' + url
        
#         # Convert method to uppercase
#         method = method.upper()
        
#         # Set default headers if none provided
#         if headers is None:
#             headers = {
#                 'User-Agent': 'Terminal-Controller/1.0',
#                 'Accept': '*/*'
#             }
        
#         # Make the request
#         response = requests.request(
#             method=method,
#             url=url,
#             headers=headers,
#             data=data,
#             timeout=timeout
#         )
        
#         # Format response
#         output = f"HTTP Request to {url}\n\n"
#         output += f"Status: {response.status_code} {response.reason}\n"
#         output += "Headers:\n"
        
#         for key, value in response.headers.items():
#             output += f"  {key}: {value}\n"
        
#         output += f"\nResponse Body ({len(response.text)} bytes):\n"
        
#         # Try to format response content based on content type
#         content_type = response.headers.get('Content-Type', '').lower()
        
#         if 'application/json' in content_type:
#             try:
#                 # Pretty-print JSON
#                 json_data = response.json()
#                 formatted_body = json.dumps(json_data, indent=2)
#                 output += formatted_body
#             except:
#                 output += response.text[:2000]  # Limit response size
#         elif 'text/' in content_type:
#             # Truncate text for large responses
#             if len(response.text) > 2000:
#                 output += response.text[:2000] + "\n\n[Response truncated, total size: " + str(len(response.text)) + " bytes]"
#             else:
#                 output += response.text
#         else:
#             # For binary responses, just show size
#             output += f"[Binary data, total size: {len(response.content)} bytes]"
        
#         return output
    
#     except requests.exceptions.RequestException as e:
#         return f"HTTP request error: {str(e)}"
#     except Exception as e:
#         return f"Error making HTTP request: {str(e)}"

# @mcp.tool()
# async def convert_natural_language(prompt: str) -> str:
#     """
#     Convert natural language into a terminal command using Gemini
    
#     Args:
#         prompt: Natural language prompt
    
#     Returns:
#         Terminal command
#     """
#     try:
#         # First try the existing pattern matching
#         command = try_pattern_matching(prompt)
#         if command:
#             return command
            
#         # If pattern matching fails, use Gemini
#         system_prompt = """
#         You are a terminal command translator. Convert natural language instructions into 
#         Windows terminal commands. Only return the exact command(s) with no explanation. 
#         For multiple commands, join them with &&. If you cannot translate the command, 
#         respond with "Could not translate".
        
#         Examples:
#         Input: "create a new folder called projects and initialize git"
#         Output: mkdir projects && cd projects && git init
        
#         Input: "show all running processes"
#         Output: tasklist
        
#         Input: "what's my IP address"
#         Output: ipconfig
#         """
        
#         # Combine system prompt with user input
#         full_prompt = f"{system_prompt}\n\nInput: {prompt}\nOutput:"
        
#         # Get response from Gemini
#         response = model.generate_content(full_prompt)
#         command = response.text.strip()
        
#         # Validate the command
#         if command and not command.startswith("Could not translate"):
#             # Basic security check
#             if is_dangerous_command(command):
#                 return "Could not translate: Command contains potentially dangerous operations"
#             return command
            
#         return f"Could not translate: '{prompt}' to a command. Try a simpler phrase."
        
#     except Exception as e:
#         return f"Error translating natural language: {str(e)}"

# def try_pattern_matching(prompt: str) -> Optional[str]:
#     """Basic pattern matching for common commands"""
#     prompt_lower = prompt.lower()
    
#     patterns = {
#         r"list (files|directory)": "dir" if platform.system() == "Windows" else "ls",
#         r"show (current )?directory": "cd" if platform.system() == "Windows" else "pwd",
#         r"create (a )?folder (\w+)": lambda m: f"mkdir {m.group(2)}",
#         r"delete (file|folder) ([\w\.]+)": lambda m: f"del {m.group(2)}" if platform.system() == "Windows" else f"rm {m.group(2)}",
#         r"show file ([\w\.]+)": lambda m: f"type {m.group(1)}" if platform.system() == "Windows" else f"cat {m.group(1)}",
#         r"ping (\w+)": lambda m: f"ping {m.group(1)}",
#         r"system (info|information)": "systeminfo" if platform.system() == "Windows" else "uname -a && lscpu",
#         r"network connections": "netstat -ano" if platform.system() == "Windows" else "netstat -tuln",
#         r"processes": "tasklist" if platform.system() == "Windows" else "ps aux",
#     }
    
#     for pattern, command in patterns.items():
#         match = re.search(pattern, prompt_lower)
#         if match:
#             if callable(command):
#                 return command(match)
#             return command
    
#     return None

# def main():
#     """
#     Entry point function that runs the MCP server.
#     """
#     import argparse
#     import json
#     from http.server import HTTPServer, BaseHTTPRequestHandler
#     import threading
    
#     parser = argparse.ArgumentParser(description="Terminal Controller MCP Server")
#     parser.add_argument("--http", action="store_true", help="Run with HTTP server")
#     parser.add_argument("--port", type=int, default=8000, help="HTTP port to listen on")
#     parser.add_argument("--host", type=str, default="127.0.0.1", help="HTTP host to bind to")
#     args = parser.parse_args()
    
#     print("Starting Enhanced Terminal Controller MCP Server...", file=sys.stderr)
    
#     if args.http:
#         print(f"HTTP server starting on {args.host}:{args.port}", file=sys.stderr)
        
#         class MCPHandler(BaseHTTPRequestHandler):
#             def do_POST(self):
#                 if self.path == "/jsonrpc":
#                     content_length = int(self.headers['Content-Length'])
#                     post_data = self.rfile.read(content_length)
#                     request = json.loads(post_data.decode('utf-8'))
                    
#                     method = request.get("method")
#                     params = request.get("params", {})
#                     req_id = request.get("id")
                    
#                     # Process the request
#                     response = {"jsonrpc": "2.0", "id": req_id}
                    
#                     try:
#                         # Get the method from globals
#                         func = globals().get(method)
#                         if callable(func):
#                             # Run the async function
#                             import asyncio
#                             result = asyncio.run(func(**params))
#                             response["result"] = result
#                         else:
#                             response["error"] = {"code": -32601, "message": "Method not found"}
#                     except Exception as e:
#                         response["error"] = {"code": -32603, "message": str(e)}
                    
#                     # Send response
#                     self.send_response(200)
#                     self.send_header('Content-Type', 'application/json')
#                     self.end_headers()
#                     self.wfile.write(json.dumps(response).encode('utf-8'))
#                 else:
#                     self.send_response(404)
#                     self.end_headers()
        
#         # Create and start HTTP server
#         server = HTTPServer((args.host, args.port), MCPHandler)
#         server_thread = threading.Thread(target=server.serve_forever)
#         server_thread.daemon = True
#         server_thread.start()
        
#         # Run the stdio server in the main thread
#         mcp.run(transport="stdio")
#     else:
#         mcp.run(transport="stdio")

# # Make the module callable
# def __call__():
#     """
#     Make the module callable for uvx.
#     This function is called when the module is executed directly.
#     """
#     print("Enhanced Terminal Controller MCP Server starting via __call__...", file=sys.stderr)
#     mcp.run(transport='stdio')

# # Add this for compatibility with uvx
# sys.modules[__name__].__call__ = __call__

# # Run the server when the script is executed directly
# if __name__ == "__main__":
#     main()
