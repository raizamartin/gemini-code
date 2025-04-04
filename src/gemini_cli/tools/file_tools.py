"""
File operation tools.
"""
# --- ADDED IMPORT ---
from .base import BaseTool
# --- END IMPORT ---

import os
import glob
import re
import logging
from pathlib import Path
# Note: MAX_CHARS_FOR_FULL_CONTENT is now defined in summarizer_tool.py,
# so we import it or redefine it here if ViewTool uses it independently.
# Let's import it for consistency.
try:
    from .summarizer_tool import MAX_CHARS_FOR_FULL_CONTENT
except ImportError:
    # Fallback if summarizer_tool doesn't exist or fails import
    MAX_CHARS_FOR_FULL_CONTENT = 50 * 1024
    logging.warning("Could not import MAX_CHARS_FOR_FULL_CONTENT from summarizer_tool, using fallback.")


log = logging.getLogger(__name__)

class ViewTool(BaseTool):
    """Tool to view specific sections or small files. For large files, use summarize_code."""
    name = "view"
    description = "View specific sections of a file using offset/limit, or view small files entirely. Use summarize_code for large files."

    def execute(self, file_path: str, offset: int | None = None, limit: int | None = None) -> str:
        """
        View specific parts or small files. Suggests summarize_code for large files if no offset/limit.

        Args:
            file_path: Path to the file to view.
            offset: Line number to start reading from (1-based index, optional).
            limit: Maximum number of lines to read (optional).
        Returns:
            The requested content or an error/suggestion message.
        """
        try:
            # Basic path safety
            if ".." in file_path.split(os.path.sep):
                 log.warning(f"Attempted to access parent directory in path: {file_path}")
                 return f"Error: Invalid file path '{file_path}'. Cannot access parent directories."

            path = os.path.abspath(os.path.expanduser(file_path))
            log.info(f"Viewing file: {path} (Offset: {offset}, Limit: {limit})")

            if not os.path.exists(path):
                log.warning(f"File not found for view: {file_path}")
                return f"Error: File not found: {file_path}"
            if not os.path.isfile(path):
                 log.warning(f"Attempted to view a directory: {file_path}")
                 return f"Error: Cannot view a directory: {file_path}"

            # Check size if offset/limit are NOT provided
            if offset is None and limit is None:
                 file_size = os.path.getsize(path)
                 if file_size > MAX_CHARS_FOR_FULL_CONTENT:
                      log.warning(f"File '{file_path}' is large ({file_size} bytes) and no offset/limit provided for view.")
                      return f"Error: File '{file_path}' is large. Use the 'summarize_code' tool for an overview, or 'view' with offset/limit for specific sections."

            # Proceed with reading
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            start_index = 0
            if offset is not None:
                start_index = max(0, int(offset) - 1)

            end_index = len(lines)
            if limit is not None:
                end_index = start_index + max(0, int(limit))

            content_slice = lines[start_index:end_index]

            result = []
            for i, line in enumerate(content_slice):
                original_line_num = start_index + i + 1
                result.append(f"{original_line_num:6d} {line}")

            prefix = f"--- Content of {file_path} (Lines {start_index+1}-{start_index+len(content_slice)}) ---" if offset is not None or limit is not None else f"--- Full Content of {file_path} ---"
            return prefix + "\n" + "".join(result) if result else f"{prefix}\n(File is empty or slice resulted in no lines)"

        except Exception as e:
            log.error(f"Error viewing file '{file_path}': {e}", exc_info=True)
            return f"Error viewing file: {str(e)}"


class EditTool(BaseTool):
    """Tool to edit/create files. Can overwrite, replace strings, or create new."""
    name = "edit"
    description = (
        "Edit or create a file. Use 'content' to provide the **entire** new file content (for creation or full overwrite). "
        "Use 'old_string' and 'new_string' to replace the **first** occurrence of an exact string. "
        "For precise changes, it's best to first `view` the relevant section, then use `edit` with the exact `old_string` and `new_string`, "
        "or provide the complete, modified content using the `content` parameter."
    )

    def execute(self, file_path: str, content: str | None = None, old_string: str | None = None, new_string: str | None = None) -> str:
        """
        Edits or creates a file.

        Args:
            file_path: Path to the file to edit or create.
            content: The full content to write to the file. Prioritized over old/new string.
            old_string: The exact string to find for replacement.
            new_string: The string to replace old_string with. Use '' to delete.
        Returns:
            A success message or an error message.
        """
        try:
            if ".." in file_path.split(os.path.sep):
                 log.warning(f"Attempted access to parent directory: {file_path}")
                 return f"Error: Invalid file path '{file_path}'."
            path = os.path.abspath(os.path.expanduser(file_path))
            log.info(f"Editing file: {path}")
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                 log.info(f"Creating directory: {directory}"); os.makedirs(directory, exist_ok=True)

            if content is not None:
                if old_string is not None or new_string is not None: log.warning("Prioritizing 'content' over 'old/new_string'.")
                log.info(f"Writing content (length: {len(content)}) to {path}.")
                with open(path, 'w', encoding='utf-8') as f: f.write(content)
                return f"Successfully wrote content to {file_path}."
            elif old_string is not None and new_string is not None:
                log.info(f"Replacing '{old_string[:50]}...' with '{new_string[:50]}...' in {path}.")
                if not os.path.exists(path): return f"Error: File not found for replacement: {file_path}"
                try:
                    with open(path, 'r', encoding='utf-8') as f: original_content = f.read()
                except Exception as read_err: return f"Error reading file for replacement: {read_err}"
                if old_string not in original_content: return f"Error: `old_string` not found in {file_path}."
                new_content = original_content.replace(old_string, new_string, 1)
                with open(path, 'w', encoding='utf-8') as f: f.write(new_content)
                return f"Successfully replaced first occurrence in {file_path}." if new_string else f"Successfully deleted first occurrence in {file_path}."
            elif old_string is None and new_string is None and content is None:
                 log.info(f"Creating empty file: {path}")
                 with open(path, 'w', encoding='utf-8') as f: f.write("")
                 return f"Successfully created/emptied file {file_path}."
            else: return "Error: Invalid arguments. Use 'content' OR ('old_string' and 'new_string')."
        except IsADirectoryError: return f"Error: Cannot edit a directory: {file_path}"
        except Exception as e: log.error(f"Error editing file '{file_path}': {e}", exc_info=True); return f"Error editing file: {str(e)}"

class GrepTool(BaseTool):
    """Tool to search for patterns in files, Windows-compatible."""
    name = "grep"
    description = "Search for a pattern (regex) in files within a directory."
    
    def execute(self, pattern: str, path: str = '.', include: str | None = None) -> str:
        try:
            if ".." in path.split(os.path.sep):
                return f"Error: Invalid path '{path}'."
                
            target_path = os.path.abspath(os.path.expanduser(path))
            log.info(f"Grepping in {target_path} for '{pattern}' (Include: {include})")
            
            if not os.path.isdir(target_path):
                return f"Error: Path is not a directory: {path}"
                
            try:
                regex = re.compile(pattern)
            except re.error as re_err:
                return f"Error: Invalid regex pattern: {pattern} ({re_err})"
                
            results = []
            files_to_search = []
            
            # Using Path objects for more reliable path handling across platforms
            target_path_obj = Path(target_path)
            
            if include:
                recursive = '**' in include
                try:
                    # Using pathlib for more reliable glob operation
                    if recursive:
                        glob_pattern = str(target_path_obj / include)
                        files_to_search = [str(p) for p in Path(target_path).glob(include)]
                    else:
                        glob_pattern = str(target_path_obj / include)
                        files_to_search = [str(p) for p in Path(target_path).glob(include)]
                except Exception as glob_err:
                    return f"Error finding files with include pattern: {glob_err}"
            else:
                # Walking directory tree manually to avoid platform-specific issues
                for root, _, filenames in os.walk(target_path):
                    basename = os.path.basename(root)
                    if basename.startswith('.') or basename == '__pycache__':
                        continue
                    files_to_search.extend(os.path.join(root, filename) for filename in filenames)
            
            log.info(f"Found {len(files_to_search)} potential files to search.")
            files_searched_count = 0
            matches_found_count = 0
            max_matches = 500
            
            for file_path in files_to_search:
                if not os.path.isfile(file_path):
                    continue
                    
                files_searched_count += 1
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                matches_found_count += 1
                                # Using pathlib for more reliable relative path calculation
                                rel_path = os.path.relpath(file_path, target_path)
                                if os.path.dirname(rel_path) == '':
                                    rel_path = f"./{rel_path}"
                                results.append(f"{rel_path}:{i}: {line.rstrip()}")
                                if matches_found_count >= max_matches:
                                    results.append("--- Match limit reached ---")
                                    break
                except OSError:
                    continue
                except Exception as e:
                    log.warning(f"Error grepping file {file_path}: {e}")
                    continue
                    
                if matches_found_count >= max_matches:
                    break
                    
            log.info(f"Searched {files_searched_count} files, found {matches_found_count} matches.")
            return "\n".join(results) if results else f"No matches found for pattern: {pattern}"
            
        except Exception as e:
            log.error(f"Error during grep: {e}", exc_info=True)
            return f"Error searching files: {str(e)}"

class GlobTool(BaseTool):
    """Tool to find files using glob patterns."""
    name = "glob"
    description = "Find files/directories matching specific glob patterns recursively."
    def execute(self, pattern: str, path: str = '.') -> str:
        log.debug(f"[GlobTool] Current working directory: {os.getcwd()}")
        try:
            if ".." in path.split(os.path.sep): return f"Error: Invalid path '{path}'."
            target_path = os.path.abspath(os.path.expanduser(path)); log.info(f"Globbing in {target_path} for '{pattern}'")
            if not os.path.isdir(target_path): return f"Error: Path is not a directory: {path}"
            search_pattern = os.path.join(target_path, pattern)
            matches = glob.glob(search_pattern, recursive=True)
            if matches:
                relative_matches = sorted([os.path.relpath(m, target_path) for m in matches])
                formatted_matches = [f"./{m}" if os.path.dirname(m) == '' else m for m in relative_matches]
                return "\n".join(formatted_matches)
            else: return f"No files or directories found matching pattern: {pattern}"
        except Exception as e: log.error(f"Error finding files with glob: {e}", exc_info=True); return f"Error finding files: {str(e)}"