"""
Tool for displaying directory structure using the 'tree' command.
"""
import subprocess
import logging
from google.generativeai.types import FunctionDeclaration, Tool
import os
from .base import BaseTool

log = logging.getLogger(__name__)

DEFAULT_TREE_DEPTH = 3
MAX_TREE_DEPTH = 10
class TreeTool(BaseTool):
    name: str = "tree"
    description: str = (
        f"""Displays the directory structure as a tree. Shows directories and files.
        Use this to understand the hierarchy and layout of the current working directory or a subdirectory.
        Defaults to a depth of {DEFAULT_TREE_DEPTH}. Use the 'depth' argument to specify a different level.
        Optionally specify a 'path' to view a subdirectory instead of the current directory."""
    )
    args_schema: dict = {
         "path": {
            "type": "string",
            "description": "Optional path to a specific directory relative to the workspace root. If omitted, uses the current directory.",
        },
        "depth": {
            "type": "integer",
            "description": f"Optional maximum display depth of the directory tree (Default: {DEFAULT_TREE_DEPTH}, Max: {MAX_TREE_DEPTH}).",
        },
    }
    # Optional args: path, depth
    required_args: list[str] = []

    def execute(self, path: str | None = None, depth: int | None = None) -> str:
        """Creates a tree view of the directory structure using native Python."""
        
        if depth is None:
            depth_limit = DEFAULT_TREE_DEPTH
        else:
            # Clamp depth to be within reasonable limits
            depth_limit = max(1, min(depth, MAX_TREE_DEPTH))
            
        # Add path if specified
        target_path = "." # Default to current directory
        if path:
            target_path = path
            
        log.info(f"Creating directory tree for path: {target_path} with depth {depth_limit}")
        
        try:
            # Check if path exists and is a directory
            if not os.path.exists(target_path):
                log.error(f"Path does not exist: {target_path}")
                return f"Error: Path does not exist: {target_path}"
                
            if not os.path.isdir(target_path):
                log.error(f"Path is not a directory: {target_path}")
                return f"Error: Path is not a directory: {target_path}"
                
            # Generate the tree structure using a recursive approach
            result = []
            base_name = os.path.basename(target_path) or target_path
            result.append(base_name)
            
            self._generate_tree(target_path, "", result, 0, depth_limit)
            
            # Limit output size
            output = "\n".join(result)
            if len(result) > 200:  # Limit lines
                log.warning(f"Tree output for '{target_path}' exceeded 200 lines. Truncating.")
                output = "\n".join(result[:200]) + "\n... (output truncated)"
                
            return output
            
        except Exception as e:
            log.exception(f"An unexpected error occurred while creating directory tree for path '{target_path}': {e}")
            return f"An unexpected error occurred while creating directory tree: {str(e)}"
            
    def _generate_tree(self, path, prefix, result, current_depth, max_depth):
        """Recursively generates the tree structure."""
        if current_depth >= max_depth:
            return
            
        try:
            entries = sorted(os.listdir(path))
            count = len(entries)
            
            for i, entry in enumerate(entries):
                is_last = i == count - 1
                entry_path = os.path.join(path, entry)
                
                # Determine connector and new prefix
                connector = "└── " if is_last else "├── "
                new_prefix = prefix + ("    " if is_last else "│   ")
                
                # Add entry to result
                result.append(f"{prefix}{connector}{entry}")
                
                # Recursively process directories
                if os.path.isdir(entry_path):
                    self._generate_tree(entry_path, new_prefix, result, current_depth + 1, max_depth)
                    
        except PermissionError:
            result.append(f"{prefix}└── [Permission Denied]")
        except Exception as e:
            result.append(f"{prefix}└── [Error: {str(e)}]")