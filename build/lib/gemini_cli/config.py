"""
Configuration management for Gemini CLI.
"""

import os
import yaml
from pathlib import Path

class Config:
    """Manages configuration for the Gemini CLI application."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "gemini-code"
        self.config_file = self.config_dir / "config.yaml"
        self._ensure_config_exists()
        self.config = self._load_config()
    
    def _ensure_config_exists(self):
        """Create config directory and file if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.config_file.exists():
            default_config = {
                "api_keys": {},
                "default_model": "models/gemini-2.5-pro-exp-03-25",
                "settings": {
                    "max_tokens": 1000000,
                    "temperature": 0.7,
                    "token_warning_threshold": 800000,
                    "auto_compact_threshold": 950000,
                }
            }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(default_config, f)
    
    def _load_config(self):
        """Load configuration from file."""
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f)
    
    def get_api_key(self, provider):
        """Get API key for a specific provider."""
        return self.config.get("api_keys", {}).get(provider)
    
    def set_api_key(self, provider, key):
        """Set API key for a specific provider."""
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        
        self.config["api_keys"][provider] = key
        self._save_config()
    
    def get_default_model(self):
        """Get the default model."""
        return self.config.get("default_model")
    
    def set_default_model(self, model):
        """Set the default model."""
        self.config["default_model"] = model
        self._save_config()
    
    def get_setting(self, setting, default=None):
        """Get a specific setting."""
        return self.config.get("settings", {}).get(setting, default)
    
    def set_setting(self, setting, value):
        """Set a specific setting."""
        if "settings" not in self.config:
            self.config["settings"] = {}
        
        self.config["settings"][setting] = value
        self._save_config()