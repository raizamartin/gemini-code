"""
System operation tools.
"""

import os
import subprocess
import tempfile
from .base import BaseTool

class BashTool(BaseTool):
    """Tool to execute bash commands."""
    
    name = "bash"
    description = "Execute a bash command"
    
    # List of banned commands for security
    BANNED_COMMANDS = [
        'curl', 'wget', 'nc', 'netcat', 'telnet',
        'lynx', 'w3m', 'links', 'ssh',
    ]
    
    def execute(self, command, timeout=30000):
        """
        Execute a bash command.
        
        Args:
            command: The command to execute
            timeout: Timeout in milliseconds (optional)
        """
        try:
            # Check for banned commands
            for banned in self.BANNED_COMMANDS:
                if banned in command.split():
                    return f"Error: The command '{banned}' is not allowed for security reasons."
            
            # Convert timeout to seconds (with better error handling)
            try:
                timeout_sec = int(timeout) / 1000
            except ValueError:
                # If timeout can't be converted to int, use default
                timeout_sec = 30
            
            # Remove the temporary directory context
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout_sec)
                
                if process.returncode != 0:
                    return f"Command exited with status {process.returncode}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
                
                return stdout
            
            except subprocess.TimeoutExpired:
                process.kill()
                return f"Error: Command timed out after {timeout_sec} seconds"
        
        except Exception as e:
            return f"Error executing command: {str(e)}"