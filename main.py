""" Dashboard for an easier life """

import importlib
import importlib.util
import importlib.abc
import importlib.machinery
from importlib.machinery import ModuleSpec
import os
import logging
import sys
import tkinter as tk
from typing import List, Optional
import time
from base_module import BaseModule


DARK_MODE_BG = "#202020"
DARK_MODE_TEXT = "#ffffff"
DARK_MODE_H1 = "#FF8888"
DARK_MODE_H2 = "#FFBBBB"
DARK_MODE_H3 = "#FFDDDD"
LIGHT_MODE_BG = "#f0f0f0"
LIGHT_MODE_TEXT = "#000000"
LIGHT_MODE_H1 = "#FF8888"
LIGHT_MODE_H2 = "#FFBBBB"
LIGHT_MODE_H3 = "#FFDDDD"


MODULES_PATH = "modules"

###################### LOGGING ######################

LOGGER_COLORS = {
    "DEBUG": "\033[94m",
    "INFO": "\033[92m",
    "WARNING": "\033[93m",
    "ERROR": "\033[91m",
    "CRITICAL": "\033[91m",
    "ENDC": "\033[0m",
}


class ConsoleHandler(logging.StreamHandler):
    """Console handler class"""

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(LOGGER_COLORS[record.levelname])
            stream.write(msg + self.terminator)
            stream.write(LOGGER_COLORS["ENDC"])
            self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)


def settup_logging(debug: bool = False) -> logging.Logger:
    """Set up logging"""
    log_path = f"logs/{time.strftime('%Y-%m-%d')}.log"
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s]: %(message)s")
    )

    console_handler = ConsoleHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s]: %(message)s")
    )

    logger.handlers = [
        file_handler,
        console_handler,
    ]
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[file_handler, console_handler],
    )
    logger.info("Logging set up.")
    return logger


###################### MODULES ######################
class ModuleDataNotAvailable(Exception):
    """Module data not available exception"""

    def __init__(self, module_name: str):
        super().__init__(f"Module data not available: {module_name}")


# setup main logger
MAIN_LOGGER = settup_logging("-d" in sys.argv or "--debug" in sys.argv)
MAIN_LOGGER.info("Starting Py Dashboard %s", time.strftime("%Y-%m-%d %H:%M:%S"))


class DashModule:
    """Module class"""

    name: str = "Module"
    path: str = ""

    settings_path: str = ""
    data: dict = {}

    # Set up logging

    def __init__(self, path: str, spec: ModuleSpec):
        self.path = path  # path ex: "modules/module_name"
        self.name = path.split("/")[-1].split(".")[0].replace("_", " ").title()
        self._spec = spec
        self.frame = None
        self._loader = None
        self._sub_module = None
        self._sub_class: Optional[BaseModule] = None

    def run(self, frame: tk.Frame) -> int:
        """Run the module, to create a data file in 'data' folder."""
        logging.info("Running module %s", self)
        self.frame = frame
        if not self._sub_class:
            logging.error("Module is not loaded.")
            return -1

        self._sub_class.display_module(frame)
        return 0

    def load_module(self) -> None:
        """Load the module"""
        if self.is_loaded():
            logging.warning("Module already loaded.")
            return

        self._loader = self._spec.loader
        if not self._loader:
            logging.error("Could not load module %s", self.path)
            return

        self._sub_module = importlib.util.module_from_spec(self._spec)

        try:
            self._loader.exec_module(self._sub_module)
        except Exception as error:
            MAIN_LOGGER.error("Error executing module %s: %s", self.path, error)
            return

        found_subclass = False  # Track if we found a valid subclass

        for cls_name, cls in self._sub_module.__dict__.items():
            if (
                isinstance(cls, type)
                and issubclass(cls, BaseModule)
                and cls is not BaseModule
            ):
                logging.info("Found class %s in module %s", cls_name, self.path)
                self._sub_class = cls(self.path, MAIN_LOGGER)
                found_subclass = True
                break  # Stop searching once we find the valid subclass

        if not found_subclass:
            logging.error("No subclass of BaseModule found in %s", self.path)
            logging.debug("Module dictionary contents: %s", self._sub_module.__dict__)

    def is_loaded(self) -> bool:
        """Check if module is loaded"""
        return self._sub_module is not None

    def __str__(self) -> str:
        return f"DashModule: {self.path} loaded: {self.is_loaded()}"

    def __repr__(self) -> str:
        return self.__str__()


###################### DASHBOARD ######################


class Dashboard(tk.Tk):
    """Dashboard class"""

    def __init__(self):
        super().__init__()
        self.title("Py Dashboard")
        self.modules: List[DashModule] = []
        self.bg_color = "#f0f0f0"
        self.text_color = "#000000"
        self.moduels_amount = 0
        self.dark_mode = False
        self.configure(bg=self.bg_color)
        self.width = 800
        self.height = 600
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(True, True)

        # Bindings
        self.bind("<Control-f>", self.toggle_fullscreen)
        self.bind("<Control-d>", self.toggle_dark_mode)
        self.bind("<r>", lambda _: self.reload_layout() if self.modules else None)
        self.bind("<Escape>", lambda _: self.quit())

        # Load modules and create frames
        self.load_modules()
        self.frames = self.create_frames()

        # Recalculate layout in 5 ms
        self.after(10, self.reload_layout)

    def load_modules(self) -> None:
        """Load modules"""

        logging.debug("Looking for modules in %s", MODULES_PATH)
        for module_folder in os.listdir(MODULES_PATH):
            logging.debug("Found module folder: %s", module_folder)
            try:
                modules_folder = os.path.join(MODULES_PATH, module_folder)
                module_exec_path = os.path.join(modules_folder, f"{module_folder}.py")
                logging.debug("Loading module from path: %s", module_exec_path)
                spec = importlib.util.spec_from_file_location(
                    module_folder, module_exec_path
                )
                if spec is None:
                    raise FileNotFoundError(
                        f"Module spec not found for {module_exec_path}"
                    )
                module = DashModule(modules_folder, spec)
                self.modules.append(module)
            except Exception as error:
                MAIN_LOGGER.error("Error loading module %s: %s", module_folder, error)

    def destroy_frames(self) -> None:
        """Destroy frames"""
        for frame in self.winfo_children():
            frame.destroy()

    def create_frames(self) -> list[tk.Frame]:
        """Create frames"""

        # Check if there are any modules loaded
        if not self.modules:
            logging.error("No modules loaded.")
            no_modules_label = tk.Label(
                self,
                text="No modules loaded. Please check your modules directory.",
                bg=self.bg_color,
                fg=self.text_color,
            )
            no_modules_label.pack()
            return []

        # Calculate rows and cols
        modules_amount = len(self.modules)
        cols = min(modules_amount, max(modules_amount // 2, 1))
        rows = (modules_amount + cols - 1) // cols

        # Create frames
        frames: list[tk.Frame] = []

        for i, module in enumerate(self.modules):
            # Adjust the width of the last frame

            row, col = divmod(i, cols)
            frame = tk.Frame(
                self,
                bg=self.bg_color,
                width=self.width // cols,
                height=self.height // rows,
            )
            frame.grid(row=row, column=col, sticky="nsew")
            frames.append(frame)

        # Return frames
        return frames

    def save_settings(self) -> None:
        """Save settings"""
        for module in self.modules:
            with open(module.settings_path, "w", encoding="utf-8") as file:
                for key, value in module.__dict__.items():
                    if key in ["name", "path", "settings_path"]:
                        continue
                    file.write(f"{key}={value}\n")

    def reload_layout(self) -> None:
        """Reload layout"""
        self.destroy_frames()
        self.update()
        self.frames = self.create_frames()
        self.update()

        # do Run on all modules for each frame
        for module, frame in zip(self.modules, self.frames):
            module.load_module()
            module.run(frame)

    def toggle_fullscreen(self, _) -> None:
        """Toggle fullscreen mode"""
        # self.attributes("-fullscreen", not self.attributes("-fullscreen"))
        self.width = self.winfo_screenwidth() if self.attributes("-fullscreen") else 800
        self.height = (
            self.winfo_screenheight() if self.attributes("-fullscreen") else 600
        )
        self.geometry(f"{self.width}x{self.height}")
        self.reload_layout()

    def toggle_dark_mode(self, _) -> None:
        """Toggle dark mode and recalculate layout"""
        self.dark_mode = not self.dark_mode

        if self.dark_mode:
            self.bg_color = DARK_MODE_BG
            self.text_color = DARK_MODE_TEXT
        else:
            self.bg_color = LIGHT_MODE_BG
            self.text_color = LIGHT_MODE_TEXT

        self.configure(bg=self.bg_color)
        self.reload_layout()


def main():
    """Main function"""
    dashboard = Dashboard()
    dashboard.mainloop()


if __name__ == "__main__":
    main()
