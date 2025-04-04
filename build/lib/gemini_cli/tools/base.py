"""
Base tool implementation and interfaces.
"""

import shlex
import inspect
from abc import ABC, abstractmethod
from google.generativeai.types import FunctionDeclaration
import logging

log = logging.getLogger(__name__)

class BaseTool(ABC):
    """Base class for all tools."""
    
    name = None
    description = "Base tool"
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the tool with the given arguments."""
        pass
    
    @classmethod
    def get_function_declaration(cls) -> FunctionDeclaration | None:
        """Generates FunctionDeclaration based on the execute method's signature."""
        if not cls.name or not cls.description:
            log.warning(f"Tool {cls.__name__} is missing name or description. Cannot generate declaration.")
            return None

        try:
            exec_sig = inspect.signature(cls.execute)
            parameters = {}
            required = []

            for param_name, param in exec_sig.parameters.items():
                # Skip 'self' if it's the first parameter
                if param_name == 'self':
                    continue 
                
                # Basic type mapping (can be enhanced)
                param_type = "string" # Default to string
                if param.annotation == str: param_type = "string"
                elif param.annotation == int: param_type = "integer"
                elif param.annotation == float: param_type = "number"
                elif param.annotation == bool: param_type = "boolean"
                elif param.annotation == list: param_type = "array" # Note: items type not specified here
                elif param.annotation == dict: param_type = "object" # Note: properties not specified here
                # Add more complex type handling if needed (e.g., from typing import List, Dict)

                # Assume description from docstring or default
                # (More advanced: parse docstring for arg descriptions)
                param_description = f"Parameter {param_name}"

                parameters[param_name] = {
                    "type": param_type,
                    "description": param_description
                }

                # Check if parameter is required (no default value)
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)

            # Handle case where no parameters are needed (besides self)
            if not parameters:
                schema = None
            else:
                schema = {
                    "type": "object",
                    "properties": parameters,
                     # Ensure required list is not empty if there are required params
                    "required": required if required else None 
                }
                # Clean up schema if required is None/empty
                if schema["required"] is None:
                    del schema["required"]

            return FunctionDeclaration(
                name=cls.name,
                description=cls.description,
                parameters=schema
            )

        except Exception as e:
            log.error(f"Error generating FunctionDeclaration for tool '{cls.name}': {e}", exc_info=True)
            return None