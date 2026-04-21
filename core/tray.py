#
# Abbie Parker
# April 18, 2026
#
# System tray
# 

import logging
import os
import webbrowser
from pystray import Menu, MenuItem, Icon
from PIL import Image, ImageDraw
import config

class Tray:
    def __init__(self):
        self.view_path = config.view_path
        self.default_folder = config.default_folder
        self.icon = None

    def create_placeholder_icon(self):
        """Generates a simple 64x64 blue square for testing."""
        img = Image.new('RGB', (64, 64), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10, 10), "iCalPy+", fill=(255, 255, 0))
        return img

    def on_quit(self):
        """Clean shutdown logic."""
        logging.info("Shutting down...")
        self.icon.stop()

    # actions
    def open_browser(self):
        webbrowser.open(f"http://127.0.0.1:{config.port}")

    def change_folder(self):
        # root = tk.Tk()
        # root.withdraw()  # Hide the main tkinter window
        # root.attributes('-topmost', True) # Bring the picker to the front
        
        # selected_path = filedialog.askdirectory(title="Select View Folder")
        # root.destroy()

        # if selected_path:
        #     config.update_view_path(selected_path)
        #     print(f"Folder updated to: {selected_path}")
        # 
        pass
    
    def change_default(self, icon, item):
        self.default_folder = item.text
        config.update_default_folder(self.default_folder)
        self.icon.update_menu()

    # build a submenu of all the views in the view folder
    def view_menu(self):
        list = []
        for view_name in os.listdir(self.view_path):
            if view_name == self.default_folder:
                list.append(MenuItem(view_name, None, default=True))
            else: list.append(MenuItem(view_name, self.change_default))
        return list

    def build_menu(self):
        return Menu(
                MenuItem("Change Default View", Menu(self.view_menu)),
                MenuItem("Change View Folder", self.change_folder),
                MenuItem(f"Folder: {self.view_path}", None, enabled=False),           
                MenuItem("Change Port", None),
                Menu.SEPARATOR,
                MenuItem("Quit", self.on_quit)
            )
    
    def run(self):

        self.icon = Icon("ICalPy+", 
                         self.create_placeholder_icon(), 
                         "ICalPy+ Manager", 
                         menu=self.build_menu(),
                         action=self.open_browser)
        self.icon.run()