"""
Tool for summarizing code files using an LLM.
"""
import google.generativeai as genai
import logging
import os
from .base import BaseTool

log = logging.getLogger(__name__)

# Define thresholds for summarization vs. full view
MAX_LINES_FOR_FULL_CONTENT = 1000 # View files smaller than this directly
MAX_CHARS_FOR_FULL_CONTENT = 50 * 1024 # 50 KB

# Simple summarization prompt
SUMMARIZATION_SYSTEM_PROMPT = """You are an expert code summarizer. Given the following code file content, provide a concise summary focusing on:
- The file's main purpose.
- Key classes and functions defined (names and brief purpose).
- Any major dependencies imported or used.
- Overall structure.
Keep the summary brief and informative, suitable for providing context to another AI agent."""

class SummarizeCodeTool(BaseTool):
    """
    Tool to summarize a code file, especially useful for large files.
    Returns full content for small files.
    """
    name = "summarize_code"
    description = "Provides a summary of a code file's purpose, key functions/classes, and structure. Use for large files or when only an overview is needed."

    def __init__(self, model_instance: genai.GenerativeModel | None = None):
        """
        Requires the initialized Gemini model instance for performing summarization.
        (This implies the tool needs access to the model from the main class)
        """
        super().__init__()
        # This creates a dependency: the tool needs the model.
        # We'll need to modify how tools are instantiated or pass the model reference.
        self.model = model_instance

    def execute(self, file_path: str | None = None, directory_path: str | None = None, query: str | None = None, glob_pattern: str | None = None) -> str:
        """
        Summarizes code based on path, directory, or query.
        # ... (rest of docstring)
        """
        log.debug(f"[SummarizeCodeTool] Current working directory: {os.getcwd()}")
        log.info(f"SummarizeCodeTool called with file='{file_path}', dir='{directory_path}', query='{query}', glob='{glob_pattern}'")

        if not self.model:
             # This check is important if the model wasn't passed during init
             log.error("SummarizeCodeTool cannot execute: Model instance not provided.")
             return "Error: Summarization tool not properly configured (missing model instance)."

        try:
            # Basic path safety
            if ".." in file_path.split(os.path.sep):
                 log.warning(f"Attempted access to parent directory: {file_path}")
                 return f"Error: Invalid file path '{file_path}'."

            target_path = os.path.abspath(os.path.expanduser(file_path))
            log.info(f"Summarize/View file: {target_path}")

            if not os.path.exists(target_path):
                 return f"Error: File not found: {file_path}"
            if not os.path.isfile(target_path):
                 return f"Error: Path is not a file: {file_path}"

            # Check file size/lines
            file_size = os.path.getsize(target_path)
            line_count = 0
            try:
                 with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                      for _ in f:
                           line_count += 1
            except Exception:
                 pass # Ignore line count errors, rely on size

            log.debug(f"File '{file_path}': Size={file_size} bytes, Lines={line_count}")

            # Return full content if file is small
            if line_count < MAX_LINES_FOR_FULL_CONTENT and file_size < MAX_CHARS_FOR_FULL_CONTENT:
                log.info(f"File '{file_path}' is small, returning full content.")
                try:
                    with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    # Add a prefix to indicate it's full content
                    return f"--- Full Content of {file_path} ---\n{content}"
                except Exception as read_err:
                    log.error(f"Error reading small file '{target_path}': {read_err}", exc_info=True)
                    return f"Error reading file: {read_err}"

            # Generate summary if file is large
            else:
                log.info(f"File '{file_path}' is large, attempting summarization...")
                try:
                    with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Limit content sent for summarization to avoid exceeding limits there too?
                        # E.g., read only first/last N lines or first X KB. For now, read all.
                        content_to_summarize = f.read()

                    if not content_to_summarize.strip():
                         return f"--- Summary of {file_path} ---\n(File is empty)"

                    # Prepare prompt for internal summarization call
                    summarization_prompt = f"Please summarize the following code from the file '{file_path}':\n\n```\n{content_to_summarize[:20000]}\n```" # Limit sent content

                    # Make the internal LLM call for summarization
                    # Use a simpler generation config? No tools needed here.
                    summary_config = genai.types.GenerationConfig(temperature=0.3) # Low temp for factual summary
                    summary_response = self.model.generate_content(
                        contents=[
                             # Provide system prompt separately if API supports it, otherwise prepend
                             {'role': 'user', 'parts': [SUMMARIZATION_SYSTEM_PROMPT, summarization_prompt]}
                        ],
                        generation_config=summary_config,
                        # safety_settings= ... # Use parent's safety settings?
                    )

                    summary_text = self._extract_text_from_summary_response(summary_response)

                    # Add a prefix to indicate it's a summary
                    return f"--- Summary of {file_path} ---\n{summary_text}"

                except Exception as summary_err:
                    log.error(f"Error generating summary for '{target_path}': {summary_err}", exc_info=True)
                    return f"Error generating summary: {summary_err}"

        except Exception as e:
            log.error(f"Error in SummarizeCodeTool for '{file_path}': {e}", exc_info=True)
            return f"Error processing file for summary/view: {str(e)}"

    # Helper to extract text from the internal summarization call's response
    def _extract_text_from_summary_response(self, response):
        try:
            if response.candidates:
                 if response.candidates[0].finish_reason.name == "STOP":
                      return "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                 else:
                      return f"(Summarization failed: {response.candidates[0].finish_reason.name})"
            else:
                 return "(Summarization failed: No candidates)"
        except Exception as e:
             log.error(f"Error extracting summary text: {e}")
             return "(Error extracting summary text)"