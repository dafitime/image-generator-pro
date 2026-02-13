"""
SQLite database management for image metadata
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class ImageDatabase:
    """Handles all database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._init_tables()
    
    def _init_tables(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Images table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT UNIQUE,
                    original_path TEXT,
                    organized_path TEXT,
                    filename TEXT,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    file_type TEXT,
                    created_date TEXT,
                    last_modified TEXT,
                    title TEXT,
                    tags TEXT,
                    date_added TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tags statistics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tag_stats (
                    tag TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 1,
                    last_used TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON images(tags)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON images(file_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON images(created_date)")
            
            # Folders table for tracking source directories
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_folders (
                    path TEXT PRIMARY KEY,
                    last_processed TEXT,
                    file_count INTEGER
                )
            """)
    
    def add_image(self, image_data: Dict[str, Any]) -> int:
        """
        Add or update an image record
        
        Returns:
            Image ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check for existing image by hash
            cursor.execute(
                "SELECT id FROM images WHERE file_hash = ?",
                (image_data['file_hash'],)
            )
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE images SET 
                    organized_path = ?, title = ?, tags = ?, last_modified = ?
                    WHERE file_hash = ?
                """, (
                    image_data.get('organized_path'),
                    image_data.get('title'),
                    json.dumps(image_data.get('tags', [])),
                    datetime.now().isoformat(),
                    image_data['file_hash']
                ))
                image_id = existing[0]
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO images (
                        file_hash, original_path, organized_path, filename,
                        file_size, width, height, file_type, created_date,
                        last_modified, title, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    image_data['file_hash'],
                    image_data['original_path'],
                    image_data.get('organized_path'),
                    image_data.get('filename'),
                    image_data.get('file_size'),
                    image_data.get('width'),
                    image_data.get('height'),
                    image_data.get('file_type'),
                    image_data.get('created_date'),
                    image_data.get('last_modified'),
                    image_data.get('title'),
                    json.dumps(image_data.get('tags', []))
                ))
                image_id = cursor.lastrowid
            
            # Update tag statistics
            self._update_tag_stats(image_data.get('tags', []), cursor)
            
            conn.commit()
            return image_id
    
    def _update_tag_stats(self, tags: List[str], cursor) -> None:
        """Update tag usage statistics"""
        for tag in tags:
            cursor.execute("""
                INSERT OR REPLACE INTO tag_stats (tag, count, last_used)
                VALUES (?, COALESCE((SELECT count FROM tag_stats WHERE tag = ?), 0) + 1, CURRENT_TIMESTAMP)
            """, (tag, tag))
    
    def search_images(self, 
                     search_term: str, 
                     search_type: str = 'tag',
                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for images
        
        Args:
            search_term: Term to search for
            search_type: 'tag', 'filename', or 'all'
            limit: Maximum number of results
        
        Returns:
            List of image records
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if search_type == 'tag':
                query = """
                    SELECT * FROM images 
                    WHERE tags LIKE ? 
                    ORDER BY date_added DESC
                    LIMIT ?
                """
                params = (f'%"{search_term}"%', limit)
            elif search_type == 'filename':
                query = """
                    SELECT * FROM images 
                    WHERE filename LIKE ? 
                    ORDER BY date_added DESC
                    LIMIT ?
                """
                params = (f'%{search_term}%', limit)
            else:
                query = """
                    SELECT * FROM images 
                    WHERE tags LIKE ? OR filename LIKE ? OR title LIKE ?
                    ORDER BY date_added DESC
                    LIMIT ?
                """
                params = (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_tags(self) -> List[Tuple[str, int]]:
        """Get all unique tags with their counts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tag, count FROM tag_stats 
                ORDER BY count DESC, tag
            """)
            return cursor.fetchall()
    
    def get_image_count(self) -> int:
        """Get total number of images in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM images")
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total images
            cursor.execute("SELECT COUNT(*) FROM images")
            result = cursor.fetchone()
            stats['total_images'] = result[0] if result else 0
            
            # By file type
            cursor.execute("""
                SELECT file_type, COUNT(*) as count 
                FROM images 
                GROUP BY file_type 
                ORDER BY count DESC
            """)
            stats['by_file_type'] = dict(cursor.fetchall())
            
            # By month/year
            try:
                cursor.execute("""
                    SELECT strftime('%Y-%m', created_date) as month, COUNT(*)
                    FROM images
                    WHERE created_date != 'unknown' AND created_date != ''
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 12
                """)
                stats['by_month'] = dict(cursor.fetchall())
            except:
                stats['by_month'] = {}
            
            # Top tags
            cursor.execute("""
                SELECT tag, count FROM tag_stats 
                ORDER BY count DESC 
                LIMIT 20
            """)
            stats['top_tags'] = dict(cursor.fetchall())
            
            # Total tags
            cursor.execute("SELECT COUNT(DISTINCT tag) FROM tag_stats")
            result = cursor.fetchone()
            stats['unique_tags'] = result[0] if result else 0
            
            return stats