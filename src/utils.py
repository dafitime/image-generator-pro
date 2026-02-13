"""
Utility functions and helpers
"""
import sys
import time
from pathlib import Path
from typing import Callable, Any
from datetime import datetime


class Logger:
    """Simple logging utility"""
    
    def __init__(self, log_file: str = None):
        self.log_file = Path(log_file) if log_file else None
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message to console and optionally to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        print(log_message)
        
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper


def validate_path(path_str: str) -> Path:
    """Validate and convert string to Path"""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path_str}")
    return path


def is_image_file(file_path: Path, extensions: set) -> bool:
    """Check if a file is an image based on extension"""
    return file_path.suffix.lower() in extensions


def get_user_confirmation(prompt: str, default_yes: bool = False) -> bool:
    """Get yes/no confirmation from user"""
    if default_yes:
        prompt += " (Y/n): "
    else:
        prompt += " (y/N): "
    
    response = input(prompt).strip().lower()
    
    if default_yes:
        return response != 'n'
    else:
        return response == 'y'