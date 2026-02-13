"""
launcher.py
Entry point. 
FIXED: Loads theme preference BEFORE showing any windows.
"""
import sys
import time

from PyQt6.QtWidgets import QApplication
import qdarktheme
from src.config import Config # Import config to read theme

from src.gui.splash_screen import SplashScreen

def main():
    app = QApplication(sys.argv)
    
    # 1. Load Config Early
    config = Config()
    
    # 2. Apply Saved Theme
    qdarktheme.setup_theme(config.theme)

    # 3. Show Splash
    splash = SplashScreen()
    splash.show()
    
    splash.update_progress(10, "Initializing Core...")
    time.sleep(0.1)

    splash.update_progress(30, "Loading Configuration...")

    splash.update_progress(50, "Loading GUI Components...")
    try:
        from src.gui.main_window import ImageOrganizerGUI
    except Exception as e:
        print(f"GUI Import Error: {e}")
        sys.exit(1)

    splash.update_progress(70, "Starting AI Engine...")
    
    # 4. Initialize Main Window
    window = ImageOrganizerGUI()
    
    splash.update_progress(90, "Finalizing...")
    
    window.show()
    splash.finish(window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()