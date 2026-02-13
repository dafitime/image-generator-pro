"""
src/image_processor.py
Handles image metadata extraction and integration with AI tagging.
"""
import hashlib
from pathlib import Path
from datetime import datetime
from PIL import Image, ExifTags
from typing import Dict, Any, List

# Always import the class (it is safe now)
from src.ai_processor import AIImageProcessor

class ImageProcessor:
    def __init__(self):
        # Initialize AI, but remember it won't load PyTorch until the first scan
        self.ai_processor = AIImageProcessor()

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """Generate MD5 hash to detect duplicates"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def extract_metadata(self, image_path: Path) -> Dict[str, Any]:
        """Extract basic EXIF and file info"""
        try:
            stat = image_path.stat()
            
            with Image.open(image_path) as img:
                width, height = img.size
                file_type = img.format
                mode = img.mode
                
                exif_data = {}
                date_taken = None
                
                try:
                    exif = img._getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            exif_data[tag] = str(value) 
                        
                        date_taken = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
                except Exception:
                    pass 
            
            file_hash = self.calculate_file_hash(image_path)
            
            return {
                'filename': image_path.name,
                'original_path': str(image_path.absolute()),
                'file_size': stat.st_size,
                'width': width,
                'height': height,
                'file_type': file_type,
                'mode': mode,
                'created_date': date_taken or datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'file_hash': file_hash
            }
        except Exception as e:
            print(f"Error processing {image_path.name}: {e}")
            return None

    def generate_tags(self, image_info: Dict[str, Any], image_path: Path) -> List[str]:
        """Generate tags based on metadata + AI analysis"""
        tags = []
        
        width = image_info.get('width', 0)
        height = image_info.get('height', 0)
        
        if width > height: tags.append("landscape")
        elif height > width: tags.append("portrait")
        else: tags.append("square")
        
        # This will trigger the AI load on the very first image
        if self.ai_processor:
            ai_tags = self.ai_processor.generate_ai_tags(image_path)
            tags.extend(ai_tags)
        
        return list(set(tags)) 

    def generate_title(self, filename: str, tags: List[str]) -> str:
        name = Path(filename).stem
        name = name.replace('_', ' ').replace('-', ' ').strip()
        return name.title() if name else "Untitled Image"