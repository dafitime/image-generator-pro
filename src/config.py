"""
src/config.py
Handles saving and loading settings.
Added ai_threshold for CLIP confidence.
"""
import json
from pathlib import Path
from PyQt6.QtCore import QByteArray

class Config:
    def __init__(self):
        self.config_file = Path("config.json")
        self.default_source = str(Path.home() / "Pictures")
        self.default_dest = str(Path.home() / "ImageOrganizer_Output")
        self.theme = "auto"
        self.last_catalog = ""
        self.ai_threshold = 0.5          # default confidence threshold
        
        # Window state storage
        self.window_geometry = None
        self.splitter_state = None
        
        self.load()

    def load(self):
        data = {
            "destination": self.default_dest,
            "theme": self.theme,
            "last_catalog": self.last_catalog,
            "ai_threshold": self.ai_threshold
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data.update(loaded)
                        
                        self.default_dest = data.get("destination", self.default_dest)
                        self.theme = data.get("theme", "auto")
                        self.last_catalog = data.get("last_catalog", "")
                        self.ai_threshold = data.get("ai_threshold", 0.5)
                        
                        if "geometry" in data:
                            self.window_geometry = QByteArray.fromHex(data["geometry"].encode())
                        if "splitter" in data:
                            self.splitter_state = QByteArray.fromHex(data["splitter"].encode())
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return data

    def save(self, updates: dict):
        try:
            current = self.load()
            current.update(updates)
            
            if "destination" in updates:
                self.default_dest = updates["destination"]
            if "theme" in updates:
                self.theme = updates["theme"]
            if "last_catalog" in updates:
                self.last_catalog = updates["last_catalog"]
            if "ai_threshold" in updates:
                self.ai_threshold = updates["ai_threshold"]
            if "geometry" in updates:
                self.window_geometry = QByteArray.fromHex(updates["geometry"].encode())
            if "splitter" in updates:
                self.splitter_state = QByteArray.fromHex(updates["splitter"].encode())

            with open(self.config_file, "w") as f:
                json.dump(current, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")