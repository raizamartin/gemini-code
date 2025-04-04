"""
Tool to signal task completion.
"""
import logging
from .base import BaseTool

log = logging.getLogger(__name__)

class TaskCompleteTool(BaseTool):
    """
    Signals that the current task/request is fully completed.
    This MUST be the final tool called by the assistant for a given request.
    """
    name = "task_complete"
    description = "Signals task completion. MUST be called as the final step, providing a user-friendly summary."

    def execute(self, summary: str) -> str:
        """
        Signals completion and returns the summary provided by the LLM.

        Args:
            summary: A concise, user-friendly summary of the actions taken and the final outcome.

        Returns:
            The summary string provided as input. The orchestrator uses this call as a signal to stop.
        """
        log.info(f"Task completion signaled by LLM.")
        
        # --- ADDED/MODIFIED: More Robust Cleaning --- 
        cleaned_summary = summary
        if isinstance(summary, str):
            log.debug(f"Original summary from LLM (Type: {type(summary)}, Length: {len(summary)}): \"{summary}\"")
            # Repeatedly strip common leading/trailing chars like quotes, spaces
            strippable_chars = ' "\'\n\t'
            while cleaned_summary.startswith(tuple(strippable_chars)) or cleaned_summary.endswith(tuple(strippable_chars)):
                prev_summary = cleaned_summary
                cleaned_summary = cleaned_summary.strip(strippable_chars)
                if cleaned_summary == prev_summary: # Avoid infinite loop if strip doesn't change anything
                    break 
            log.debug(f"Final cleaned summary: \"{cleaned_summary}\"")
        else:
             log.warning(f"TaskCompleteTool received non-string summary type: {type(summary)}")
             cleaned_summary = str(summary).strip() # Attempt to convert and strip
        # --- END ADDED/MODIFIED SECTION ---
        
        log.debug(f"Processing summary (cleaned): {cleaned_summary}")
        if not cleaned_summary or len(cleaned_summary) < 5:
             log.warning("TaskCompleteTool called with missing or very short summary.")
             # Provide a default confirmation if summary is bad/missing
             return "Task marked as complete, but the provided summary was insufficient."
        # The orchestrator loop will see this tool was called and use this summary.
        # We just return the summary itself.
        return cleaned_summary