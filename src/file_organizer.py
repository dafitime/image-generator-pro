"""
File scanning, organization, and movement
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional


class FileOrganizer:
    """Handles file operations and organization"""
    
    def __init__(self, base_dest_dir: str, image_extensions: set = None):
        """
        Initialize file organizer
        
        Args:
            base_dest_dir: Base directory for organized files
            image_extensions: Set of image extensions to process
        """
        self.base_dest_dir = Path(base_dest_dir)
        self.base_dest_dir.mkdir(parents=True, exist_ok=True)
        
        self.image_extensions = image_extensions or {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
        }
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Find all image files in a directory
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
        
        Returns:
            List of image file paths
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        
        image_files = []
        
        if recursive:
            for ext in self.image_extensions:
                # Search for both lowercase and uppercase extensions
                image_files.extend(dir_path.rglob(f"*{ext}"))
                image_files.extend(dir_path.rglob(f"*{ext.upper()}"))
        else:
            for ext in self.image_extensions:
                image_files.extend(dir_path.glob(f"*{ext}"))
                image_files.extend(dir_path.glob(f"*{ext.upper()}"))
        
        # Convert to strings and remove duplicates
        return list(set(str(f) for f in image_files))
    
    def get_destination_path(self, 
                            image_info: dict, 
                            title: str) -> Path:
        """
        Determine destination path for an image
        
        Args:
            image_info: Image metadata dictionary
            title: Image title
        
        Returns:
            Destination Path object
        """
        # Parse date from image info
        date_folder = "unknown-date"
        created_date = image_info.get('created_date', '')
        
        if created_date:
            try:
                # Handle different date formats
                if ':' in created_date and ' ' in created_date:
                    created_date = created_date.replace(':', '-', 2).replace(' ', 'T')
                
                date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                date_folder = date_obj.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                pass
        
        # Create destination directory
        dest_dir = self.base_dest_dir / date_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Create safe filename
        safe_title = self._sanitize_filename(title)
        
        # Get original extension
        original_path = Path(image_info['original_path'])
        ext = original_path.suffix.lower()
        
        # Ensure unique filename
        return self._get_unique_filename(dest_dir, safe_title, ext)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        # Keep alphanumeric, spaces, hyphens, underscores
        safe_chars = " -_"
        sanitized = ''.join(c for c in filename if c.isalnum() or c in safe_chars).strip()
        return sanitized or "image"
    
    def _get_unique_filename(self, directory: Path, base_name: str, ext: str) -> Path:
        """Generate a unique filename in the directory"""
        counter = 0
        while True:
            if counter == 0:
                filename = f"{base_name}{ext}"
            else:
                filename = f"{base_name}_{counter}{ext}"
            
            dest_path = directory / filename
            if not dest_path.exists():
                return dest_path
            counter += 1
    
    def organize_file(self, 
                     src_path: str, 
                     dest_path: Path, 
                     mode: str = 'copy') -> Tuple[Optional[str], Optional[str]]:
        """
        Copy or move a file to organized location
        
        Args:
            src_path: Source file path
            dest_path: Destination Path object
            mode: 'copy' or 'move'
        
        Returns:
            Tuple of (organized_path, action) or (None, None) on error
        """
        try:
            src = Path(src_path)
            
            if not src.exists():
                return None, None
            
            if mode == 'move':
                shutil.move(str(src), str(dest_path))
                action = "moved"
            else:  # copy
                shutil.copy2(str(src), str(dest_path))
                action = "copied"
            
            return str(dest_path), action
            
        except Exception as e:
            print(f"Error organizing {src_path}: {e}")
            return None, None