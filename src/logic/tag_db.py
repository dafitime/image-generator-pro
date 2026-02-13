"""
src/logic/tag_db.py
Persistent JSON tag storage on NAS – thread‑safe, network‑friendly.
"""
import json
import threading
from pathlib import Path
from datetime import datetime

class TagDatabase:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self.data = {}  # relative_path -> {"tags": list, "filename": str, "last_modified": str}
        self._load()

    def _load(self):
        """Load JSON from NAS. If file doesn't exist, start fresh."""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Error loading tag database: {e}")
                self.data = {}
        else:
            self.data = {}

    def _save(self):
        """Write JSON to NAS atomically (temp file + replace)."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.db_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            temp_path.replace(self.db_path)
        except Exception as e:
            print(f"Error saving tag database: {e}")

    def get_tags(self, relative_path: str) -> dict:
        """Return {'tags': [...], 'filename': ...} or empty defaults."""
        with self.lock:
            entry = self.data.get(relative_path, {})
            return {
                'tags': entry.get('tags', []),
                'filename': entry.get('filename', Path(relative_path).stem)
            }

    def set_metadata(self, relative_path: str, filename: str, tags: list):
        """Store metadata for an image and immediately save to disk."""
        with self.lock:
            self.data[relative_path] = {
                'tags': tags,
                'filename': filename,
                'last_modified': datetime.now().isoformat()
            }
            self._save()

    def search(self, query: str) -> list:
        """Return list of relative_paths that match query in tags or filename."""
        if not query:
            return []
        query = query.lower()
        results = []
        with self.lock:
            for rel_path, meta in self.data.items():
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

    def all_tags(self) -> set:
        """Return set of all unique tags in the database."""
        tags = set()
        with self.lock:
            for meta in self.data.values():
                tags.update(meta.get('tags', []))
        return tags