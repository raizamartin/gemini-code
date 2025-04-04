"""
Tools for code quality (linting, formatting).
Requires external tools like 'ruff', 'black', 'flake8' etc. to be installed
in the environment where this CLI runs.
"""
import subprocess
import logging
import shlex
import os
from .base import BaseTool

log = logging.getLogger(__name__)

# --- Helper for running commands ---
def _run_quality_command(command: list[str], tool_name: str) -> str:
    log.info(f"Executing {tool_name} command: {' '.join(command)}")
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False, # Check return code manually
            timeout=120 # 2 minute timeout
        )
        stdout = process.stdout.strip()
        stderr = process.stderr.strip()
        log.info(f"{tool_name} completed. Exit Code: {process.returncode}")
        log.debug(f"{tool_name} stdout:\n{stdout}")
        if stderr: log.debug(f"{tool_name} stderr:\n{stderr}")

        result = f"{tool_name} Result (Exit Code: {process.returncode}):\n"
        if stdout: result += f"-- Output --\n{stdout}\n"
        if stderr: result += f"-- Errors --\n{stderr}\n"
        if not stdout and not stderr: result += "(No output)"

        # Truncate long results?
        max_len = 2000
        if len(result) > max_len:
             result = result[:max_len] + "\n... (output truncated)"

        return result

    except FileNotFoundError:
        cmd_str = command[0]
        log.error(f"{tool_name} command '{cmd_str}' not found.")
        return f"Error: Command '{cmd_str}' not found. Is '{cmd_str}' installed and in PATH?"
    except subprocess.TimeoutExpired:
        log.error(f"{tool_name} run timed out.")
        return f"Error: {tool_name} run timed out (2 minutes)."
    except Exception as e:
        log.error(f"Unexpected error running {tool_name}: {e}", exc_info=True)
        return f"Error running {tool_name}: {str(e)}"


class LinterCheckerTool(BaseTool):
    """Tool to run a code linter (e.g., ruff, flake8)."""
    name = "linter_checker"
    description = "Runs a code linter (default: 'ruff check') on a specified path to find potential issues."

    def execute(self, path: str = '.', linter_command: str = 'ruff check') -> str:
        """
        Runs the linter.

        Args:
            path: The file or directory path to lint (default: current directory).
            linter_command: The base command for the linter (default: 'ruff check'). Arguments like the path will be appended.

        Returns:
            The output from the linter.
        """
        if ".." in path.split(os.path.sep):
             log.warning(f"Attempted to access parent directory in linter path: {path}")
             return f"Error: Invalid path '{path}'. Cannot access parent directories."
        target_path = os.path.abspath(os.path.expanduser(path))

        # Basic command splitting, assumes simple command name possibly with one arg
        command_parts = shlex.split(linter_command)
        command = command_parts + [target_path]

        return _run_quality_command(command, "Linter")


class FormatterTool(BaseTool):
    """Tool to run a code formatter (e.g., black, prettier)."""
    name = "formatter"
    description = "Runs a code formatter (default: 'black') on a specified path to automatically fix styling."

    def execute(self, path: str = '.', formatter_command: str = 'black') -> str:
        """
        Runs the formatter.

        Args:
            path: The file or directory path to format (default: current directory).
            formatter_command: The base command for the formatter (default: 'black'). Arguments like the path will be appended.

        Returns:
            The output from the formatter.
        """
        if ".." in path.split(os.path.sep):
             log.warning(f"Attempted to access parent directory in formatter path: {path}")
             return f"Error: Invalid path '{path}'. Cannot access parent directories."
        target_path = os.path.abspath(os.path.expanduser(path))

        # Basic command splitting
        command_parts = shlex.split(formatter_command)
        command = command_parts + [target_path]

        return _run_quality_command(command, "Formatter")