"""
src/logic/catalog.py
Portable image catalog – JSON file, cloud‑sync friendly.
"""
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ImageCatalog:
    """Manages a shared catalog of images with tags and custom filenames."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = Path(catalog_path) if catalog_path else None
        self.lock = threading.Lock()
        self.images: Dict[str, dict] = {}  # relative_path -> metadata
        self.base_dir: Optional[Path] = None  # user's local image root
        self._modified = False

    def create_new(self, catalog_path: Path):
        """Create a new empty catalog."""
        self.catalog_path = Path(catalog_path)
        self.images = {}
        self.base_dir = None
        self._modified = True
        self.save()

    def load(self, catalog_path: Optional[Path] = None) -> bool:
        """Load catalog from JSON file. Returns True on success."""
        if catalog_path:
            self.catalog_path = Path(catalog_path)
        if not self.catalog_path or not self.catalog_path.exists():
            return False
        with self.lock:
            try:
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.images = data.get('images', {})
                base_dir_str = data.get('base_dir', '')
                self.base_dir = Path(base_dir_str) if base_dir_str else None
                self._modified = False
                return True
            except Exception as e:
                print(f"Failed to load catalog: {e}")
                return False

    def save(self) -> bool:
        """Write catalog to disk (atomic). Returns True on success."""
        if not self.catalog_path:
            return False
        with self.lock:
            try:
                self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = self.catalog_path.with_suffix('.tmp')
                data = {
                    'images': self.images,
                    'base_dir': str(self.base_dir) if self.base_dir else '',
                    'version': '1.0',
                    'updated': datetime.now().isoformat()
                }
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                temp_path.replace(self.catalog_path)
                self._modified = False
                return True
            except Exception as e:
                print(f"Failed to save catalog: {e}")
                return False

    def set_base_dir(self, path: Path):
        """Set the local root folder where images are stored."""
        self.base_dir = Path(path)
        self._modified = True

    def add_or_update_image(self, absolute_path: Path, filename: str, tags: List[str]):
        """Add or update an image in the catalog using its absolute path."""
        if not self.base_dir:
            raise ValueError("Base directory not set. Call set_base_dir() first.")
        try:
            rel_path = str(absolute_path.relative_to(self.base_dir))
        except ValueError:
            print(f"Warning: {absolute_path} is not under base dir {self.base_dir}. Using absolute path.")
            rel_path = str(absolute_path)
        with self.lock:
            self.images[rel_path] = {
                'filename': filename,
                'tags': tags,
                'last_modified': datetime.now().isoformat()
            }
        self._modified = True

    def get_image_metadata(self, absolute_path: Path) -> dict:
        """Retrieve metadata for an image using its absolute path."""
        if not self.base_dir:
            return {'filename': absolute_path.stem, 'tags': []}
        try:
            rel_path = str(absolute_path.relative_to(self.base_dir))
        except ValueError:
            rel_path = str(absolute_path)
        with self.lock:
            entry = self.images.get(rel_path, {})
            return {
                'filename': entry.get('filename', absolute_path.stem),
                'tags': entry.get('tags', [])
            }

    def search(self, query: str) -> List[str]:
        """Return list of relative paths matching query in filename or tags."""
        if not query:
            return []
        query = query.lower()
        results = []
        with self.lock:
            for rel_path, meta in self.images.items():
                if query in rel_path.lower():
                    results.append(rel_path)
                    continue
                if query in meta.get('filename', '').lower():
                    results.append(rel_path)
                    continue
                for tag in meta.get('tags', []):
                    if query in tag.lower():
                        results.append(rel_path)
                        break
        return results

    def get_all_tags(self) -> set:
        """Return set of all unique tags in the catalog."""
        tags = set()
        with self.lock:
            for meta in self.images.values():
                tags.update(meta.get('tags', []))
        return tags

    def is_modified(self) -> bool:
        return self._modified