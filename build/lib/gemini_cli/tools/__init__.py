"""
Tools module initialization. Registers all available tools.
Includes Summarizer Tool.
"""

import logging
from .base import BaseTool
from .file_tools import ViewTool, EditTool, GrepTool, GlobTool
from .directory_tools import LsTool

# --- Tool Imports ---
try: from .system_tools import BashTool; bash_tool_available = True
except ImportError: logging.warning("system_tools.BashTool not found. Disabled."); bash_tool_available = False

try: from .task_complete_tool import TaskCompleteTool; task_complete_available = True
except ImportError: logging.warning("task_complete_tool.TaskCompleteTool not found. Disabled."); task_complete_available = False

try: from .directory_tools import CreateDirectoryTool; create_dir_available = True
except ImportError: logging.warning("directory_tools.CreateDirectoryTool not found. Disabled."); create_dir_available = False

try: from .quality_tools import LinterCheckerTool, FormatterTool; quality_tools_available = True
except ImportError: logging.warning("quality_tools not found or missing classes. Disabled."); quality_tools_available = False

# Import the new summarizer tool
try: from .summarizer_tool import SummarizeCodeTool; summarizer_available = True
except ImportError: logging.warning("summarizer_tool.SummarizeCodeTool not found. Disabled."); summarizer_available = False

# Assuming test_runner exists from previous steps
test_runner_available = True
if test_runner_available:
    try: from .test_runner import TestRunnerTool
    except ImportError: logging.warning("test_runner.py exists but failed import?"); test_runner_available=False
# --- End Tool Imports ---

from .tree_tool import TreeTool

# AVAILABLE_TOOLS maps tool names (strings) to the actual tool classes.
# Start with core, guaranteed tools
AVAILABLE_TOOLS = {
    "view": ViewTool,
    "edit": EditTool,
    "ls": LsTool,
    "grep": GrepTool,
    "glob": GlobTool,
    "create_directory": CreateDirectoryTool,
    "task_complete": TaskCompleteTool,
    "tree": TreeTool,
}

# Conditionally add tools based on successful imports
if bash_tool_available: AVAILABLE_TOOLS["bash"] = BashTool
# task_complete is core, already added
# create_directory is core, already added
if quality_tools_available:
    AVAILABLE_TOOLS["linter_checker"] = LinterCheckerTool
    AVAILABLE_TOOLS["formatter"] = FormatterTool
# Summarizer tool is not added by default
if test_runner_available: AVAILABLE_TOOLS["test_runner"] = TestRunnerTool
# tree is core, already added

def get_tool(name: str) -> BaseTool | None:
    """
    Retrieves an *instance* of the tool class based on its name.
    NOTE: Does NOT handle special constructors (like SummarizeCodeTool needing the model).
          That specific instantiation happens in the GeminiModel class now.
    """
    tool_class = AVAILABLE_TOOLS.get(name)
    if tool_class:
        try:
             # For most tools, simple instantiation works
             if name != "summarize_code": # Exclude the special case
                  return tool_class()
             else:
                  # Raise error or return None if called for summarize_code,
                  # as it needs special handling elsewhere.
                  logging.error(f"get_tool() called for '{name}', which requires special instantiation with model instance.")
                  return None
        except Exception as e:
             logging.error(f"Error instantiating tool '{name}': {e}", exc_info=True)
             return None
    else:
        logging.warning(f"Tool '{name}' not found in AVAILABLE_TOOLS.")
        return None

logging.info(f"Tools initialized. Available: {list(AVAILABLE_TOOLS.keys())}")