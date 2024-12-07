"""Base module implementation"""

import tkinter as tk
import configparser
import os
import logging
from abc import abstractmethod


class ModuleDataNotAvailable(Exception):
    """Module data not available exception"""

    def __init__(self, module_name: str):
        super().__init__(f"Module data not available: {module_name}")


class BaseModule:
    """Base Module for sub modules"""

    def __init__(self, path: str, logger: logging.Logger):
        self.path = path
        self.name = self.__class__.__name__
        self.version = "0.0"
        self.description = "Base module"
        self.author = "Unknown"
        self.license = "Unspecified"
        self.dependencies = []
        self.settings = {}
        self.logger = logger
        self.load_settings()
        self.on_init()

    def load_settings(self):
        """Load settings from settings.ini located in the module's directory."""
        settings_file = os.path.join(
            os.path.dirname(__file__), self.path, "settings.ini"
        )
        if not os.path.exists(settings_file):
            self.log_warning(
                "No settings.ini found for module %s. Using empty settings.", self.name
            )
            return

        config = configparser.ConfigParser()
        try:
            config.read(settings_file)
            if "Module" in config.sections():
                self.name = config.get("Module", "name", fallback=self.name)
                self.version = config.get("Module", "version", fallback=self.version)
                self.description = config.get(
                    "Module", "description", fallback=self.description
                )

            self.settings = {
                section: dict(config.items(section)) for section in config.sections()
            }
            self.log_debug(
                "Settings loaded for module %s: %s", self.name, self.settings
            )
        except (configparser.Error, OSError) as error:
            self.log_error(
                "Failed to load settings for module %s: %s", self.name, error
            )
            self.settings = {}

    def validate_settings(self, required_keys: dict):
        """Validate if required keys exist in the settings."""
        for section, keys in required_keys.items():
            if section not in self.settings:
                raise KeyError(f"Missing section: {section}")
            for key in keys:
                if key not in self.settings[section]:
                    raise KeyError(f"Missing key '{key}' in section '{section}'")

    def log_debug(self, message, *args):
        """Log info message."""
        message = f"[{self.name}]: {message}"
        if args:
            self.logger.debug(message % args)
        else:
            self.logger.debug(message)

    def log_info(self, message, *args):
        """Log info message."""
        message = f"[{self.name}]: {message}"
        if args:
            self.logger.info(message % args)
        else:
            self.logger.info(message)

    def log_warning(self, message, *args):
        """Log warning message."""
        message = f"[{self.name}]: {message}"
        if args:
            self.logger.warning(message % args)
        else:
            self.logger.warning(message)

    def log_error(self, message, *args):
        """Log error message."""
        message = f"[{self.name}]: {message}"
        if args:
            self.logger.error(message % args)
        else:
            self.logger.error(message)

    def on_init(self):
        """Hook for custom initialization logic."""
        self.log_debug("Module %s initialized", self.name)

    def on_cleanup(self):
        """Hook for cleanup logic."""
        self.log_debug("Module %s cleaned up", self.name)

    @abstractmethod
    def display_module(self, frame: tk.Frame) -> None:
        """Display module."""
        raise ModuleDataNotAvailable(self.name)
