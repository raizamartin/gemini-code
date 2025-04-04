"""
Tool for running automated tests (e.g., pytest).
"""

import subprocess
import logging
import shlex
from .base import BaseTool

# Configure logging for this tool
log = logging.getLogger(__name__)

class TestRunnerTool(BaseTool):
    """
    Tool to execute automated tests using a test runner like pytest.
    Assumes the test runner command (e.g., 'pytest') is available
    in the environment where the CLI is run.
    """
    name = "test_runner"
    description = "Runs automated tests using the project's test runner (defaults to trying 'pytest'). Use after making code changes to verify correctness."

    def execute(self, test_path: str | None = None, options: str | None = None, runner_command: str = "pytest") -> str:
        """
        Executes automated tests.

        Args:
            test_path: Specific file or directory to test (optional, runs tests discovered by the runner if omitted).
            options: Additional command-line options for the test runner (e.g., '-k my_test', '-v', '--cov'). Optional.
            runner_command: The command to invoke the test runner (default: 'pytest').

        Returns:
            A string summarizing the test results, including output on failure.
        """
        command = [runner_command]

        if options:
            # Use shlex to safely split options string respecting quotes
            try:
                command.extend(shlex.split(options))
            except ValueError as e:
                log.warning(f"Could not parse options string '{options}': {e}. Ignoring options.")
                # Optionally return an error message here
                # return f"Error: Invalid options string provided: {options}"

        if test_path:
            command.append(test_path)

        log.info(f"Executing test command: {' '.join(command)}")

        try:
            # Execute the command, capture output, set a timeout (e.g., 5 minutes)
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False, # Don't raise exception on non-zero exit code, we'll check it manually
                timeout=300 # Timeout in seconds (e.g., 5 minutes)
            )

            exit_code = process.returncode
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()

            log.info(f"Test run completed. Exit Code: {exit_code}")
            log.debug(f"Test stdout:\n{stdout}")
            if stderr:
                log.debug(f"Test stderr:\n{stderr}")

            # Prepare summary message
            summary = f"Test run using '{runner_command}' completed.\n"
            summary += f"Exit Code: {exit_code}\n"

            if exit_code == 0:
                summary += "Status: SUCCESS\n"
                # Include stdout even on success, maybe truncated?
                summary += f"\nOutput:\n---\n{stdout[-1000:]}\n---\n" # Show last 1000 chars
            else:
                summary += "Status: FAILED\n"
                summary += f"\nStandard Output:\n---\n{stdout}\n---\n"
                if stderr:
                    summary += f"\nStandard Error:\n---\n{stderr}\n---\n"

            # Specific exit codes for pytest might be useful
            # (e.g., 5 means no tests collected) - can add more logic here
            if exit_code == 5 and 'pytest' in runner_command:
                 summary += "\nNote: Pytest exit code 5 often means no tests were found or collected."


            return summary

        except FileNotFoundError:
            log.error(f"Test runner command '{runner_command}' not found.")
            return f"Error: Test runner command '{runner_command}' not found. Is it installed and in PATH?"
        except subprocess.TimeoutExpired:
            log.error("Test run timed out.")
            return "Error: Test run exceeded the timeout limit (5 minutes)."
        except Exception as e:
            log.error(f"An unexpected error occurred while running tests: {e}", exc_info=True)
            return f"Error: An unexpected error occurred: {str(e)}"