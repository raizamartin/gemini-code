"""
Tools for directory operations.
"""
import os
import logging
import subprocess
from .base import BaseTool

log = logging.getLogger(__name__)

class CreateDirectoryTool(BaseTool):
    """Tool to create a new directory."""
    name = "create_directory"
    description = "Creates a new directory, including any necessary parent directories."

    def execute(self, dir_path: str) -> str:
        """
        Creates a directory.

        Args:
            dir_path: The path of the directory to create.

        Returns:
            A success or error message.
        """
        try:
            # Basic path safety
            if ".." in dir_path.split(os.path.sep):
                 log.warning(f"Attempted to access parent directory in create_directory path: {dir_path}")
                 return f"Error: Invalid path '{dir_path}'. Cannot access parent directories."

            target_path = os.path.abspath(os.path.expanduser(dir_path))
            log.info(f"Attempting to create directory: {target_path}")

            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    log.warning(f"Directory already exists: {target_path}")
                    return f"Directory already exists: {dir_path}"
                else:
                    log.error(f"Path exists but is not a directory: {target_path}")
                    return f"Error: Path exists but is not a directory: {dir_path}"

            os.makedirs(target_path, exist_ok=True) # exist_ok=True handles race conditions slightly better
            log.info(f"Successfully created directory: {target_path}")
            return f"Successfully created directory: {dir_path}"

        except OSError as e:
            log.error(f"Error creating directory '{dir_path}': {e}", exc_info=True)
            return f"Error creating directory: {str(e)}"
        except Exception as e:
            log.error(f"Unexpected error creating directory '{dir_path}': {e}", exc_info=True)
            return f"Error creating directory: {str(e)}"

class LsTool(BaseTool):
    """Tool to list directory contents in a platform independent way."""
    name = "ls"
    description = "Lists the contents of a specified directory (detailed format, including hidden files)."
    args_schema: dict = {
        "path": {
            "type": "string",
            "description": "Optional path to a specific directory relative to the workspace root. If omitted, uses the current directory.",
        }
    }
    required_args: list[str] = []

    def execute(self, path: str | None = None) -> str:
        """Executes directory listing command based on the current platform."""
        target_path = "."  # Default to current directory
        if path:
            # Basic path safety ( prevent navigating outside workspace root if needed)
            target_path = os.path.normpath(path)  # Normalize path
            if target_path.startswith(".."):
                log.warning(f"Attempted to access parent directory in ls path: {path}")
                return f"Error: Invalid path '{path}'. Cannot access parent directories."

        log.info(f"Executing directory listing for path: {target_path}")

        try:
            # Platform-independent implementation using os module
            if not os.path.exists(target_path):
                log.error(f"Directory not found: {target_path}")
                return f"Error: Directory not found: '{target_path}'"
            
            if not os.path.isdir(target_path):
                log.error(f"Path is not a directory: {target_path}")
                return f"Error: Path is not a directory: '{target_path}'"
            
            # Getting all entries in the directory, including hidden files
            entries = []
            for entry in os.listdir(target_path):
                entry_path = os.path.join(target_path, entry)
                stat_info = os.stat(entry_path)
                
                mode = "d" if os.path.isdir(entry_path) else "-"
                
                size = stat_info.st_size if not os.path.isdir(entry_path) else ""
                
                # Geting last modified time
                mtime = stat_info.st_mtime
                last_modified = f"{mtime}"
                try:
                    # Trying to format the time in a more readable way
                    from datetime import datetime
                    last_modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
                
                entries.append((mode, last_modified, size, entry))
            
            # Sorting entries - directories first, then files
            entries.sort(key=lambda x: (x[0] != 'd', x[3].lower()))
            
            # Formating output similar to ls -lA
            output_lines = []
            for mode, last_modified, size, entry in entries:
                size_str = f"{size}" if size != "" else ""
                output_lines.append(f"{mode}---- {last_modified} {size_str:10} {entry}")
            
            output = "\n".join(output_lines)
            
            # Truncate if necessary
            if len(output_lines) > 100:
                log.warning(f"ls output for '{target_path}' exceeded 100 lines. Truncating.")
                output = "\n".join(output_lines[:100]) + "\n... (output truncated)"
            
            return output
            
        except PermissionError:
            log.error(f"Permission denied for path: {target_path}")
            return f"Error: Permission denied for path: '{target_path}'"
        except Exception as e:
            log.exception(f"An unexpected error occurred while listing directory '{target_path}': {e}")
            return f"An unexpected error occurred: {str(e)}"