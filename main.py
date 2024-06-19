""" Dashboard for an easier life """

import os
import sys
import tkinter as tk
from typing import List


class Module:
    """Module class"""

    name: str = "Module"
    path: str = ""
    settings_path: str = ""

    def __init__(self, path):
        self.path = path
        self.settings_path = os.path.join(path, "settings.ini")
        self.load_settings()

    def run(self):
        """Run the module"""
        print("Running the module.")

    def load_settings(self):
        """Load settings"""
        if not os.path.exists(self.settings_path):
            return
        with open(self.settings_path, "r") as file:
            for line in file:
                key, value = line.strip().split("=")
                setattr(self, key, value)


class Dashboard(tk.Tk):
    """Dashboard class"""

    def __init__(self):
        super().__init__()
        self.title("Dashboard")
        self.modules: List[Module] = []
        self.bg_color = "#f0f0f0"
        self.text_color = "#000000"
        self.moduels_amount = 0
        self.dark_mode = False
        self.configure(bg=self.bg_color)
        self.geometry("800x600")
        self.resizable(False, False)
        self.width = 800
        self.height = 600

        # Bindings
        # ctrl-f for fullscreen
        self.bind("<Control-f>", self.toggle_fullscreen)

        # ctrl-d for dark mode
        self.bind("<Control-d>", self.toggle_dark_mode)

        # ESC for exit
        self.bind("<Escape>", lambda _: self.quit())

        self.load_modules()

        # recalculate layout in 5 ms
        self.after(10, self.recalculate_layout)

    def exit(self):
        """Exit the dashboard"""
        self.save_settings()
        self.destroy()

    def __enter__(self):
        print("Dashboard entered.")
        return self

    def save_settings(self):
        """Save settings"""
        for module in self.modules:
            with open(module.settings_path, "w", encoding="utf-8") as file:
                for key, value in module.__dict__.items():
                    if key in ["name", "path", "settings_path"]:
                        continue
                    file.write(f"{key}={value}\n")

    def recalculate_layout(self, _=None):
        """Recalculate layout"""
        print("Recalculating layout.")
        self.width = self.winfo_width()
        self.height = self.winfo_height()

        cols = 3
        rows = self.moduels_amount // cols + 1

        for i, module in enumerate(self.modules):
            x = (i % cols) * (self.width // cols)
            y = (i // cols) * (self.height // rows)
            module_canvas = tk.Canvas(
                self,
                width=self.width // cols,
                height=self.height // rows,
                bg=self.bg_color,
                highlightthickness=0,
            )
            module_canvas.create_text(
                self.width // cols // 2,
                self.height // rows // 2,
                text=module.name,
                fill=self.text_color,
                font=("Helvetica", 16),
            )
            module_canvas.place(x=x, y=y)

    def toggle_fullscreen(self, _):
        """Toggle fullscreen mode"""
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))
        self.recalculate_layout()

    def load_modules(self):
        """Load modules"""
        modules_path = "modules"
        for module in os.listdir(modules_path):
            widget_path = os.path.join(modules_path, module)
            widget_main = os.path.join(widget_path, f"{module}.py")
            if not os.path.exists(widget_main):
                continue
            module = Module(widget_path)
            self.moduels_amount += 1
            self.modules.append(module)

    def toggle_dark_mode(self, _):
        """Toggle dark mode"""
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.bg_color = "#202020"
            self.text_color = "#ffffff"
        else:
            self.bg_color = "#f0f0f0"
            self.text_color = "#000000"
        self.configure(bg=self.bg_color)
        self.recalculate_layout()


def main(args, **kwargs):
    """Main function"""
    print(args, kwargs)
    print("Hello, World!")
    print("This is the main function.")

    dashboard = Dashboard()
    dashboard.mainloop()


if __name__ == "__main__":
    main(sys.argv[1:], **os.environ)
