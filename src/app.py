"""
src/app.py
Core application logic using EfficientNet for tagging.
"""
import shutil
from pathlib import Path
from collections import defaultdict
from src.ai.efficientnet_tagger import EfficientNetTagger

class ImageOrganizerApp:
    def __init__(self, config):
        self.config = config
        self.tagger = EfficientNetTagger(threshold=self.config.ai_threshold)

    def update_ai_threshold(self, threshold):
        """Update the confidence threshold of the tagger."""
        self.tagger.set_threshold(threshold)

    def preview_organization(self, source_path, recursive=True, group_by="tag",
                             progress_callback=None, stop_event=None):
        plan = defaultdict(list)
        source = Path(source_path)

        files = list(source.rglob("*")) if recursive else list(source.glob("*"))
        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}
        images = [f for f in files if f.suffix.lower() in valid_exts]

        total = len(images)

        # Define priority categories for folder naming
        priority_cats = ['military', 'vehicles', 'people', 'animals',
                         'construction', 'electronics']

        for i, img_path in enumerate(images):
            if stop_event and stop_event.is_set():
                break

            if progress_callback:
                progress_callback(i + 1, total, img_path.name)

            # Get tags from EfficientNet
            tags = self.tagger.predict_tags(img_path, top_k=5)

            # Choose folder based on first priority tag found
            folder_name = "Uncategorized"
            if tags:
                found_cat = next((t for t in tags if t.lower() in priority_cats), None)
                if found_cat:
                    folder_name = found_cat.title()
                else:
                    folder_name = tags[0].title()

            file_data = {
                'original_path': str(img_path),
                'filename': img_path.name,
                'new_filename': img_path.name,
                'tags': tags,
                'proposed_folder': folder_name
            }
            plan[folder_name].append(file_data)

        return dict(plan)

    def execute_plan(self, plan):
        dest_base = Path(self.config.default_dest)
        stats = {'processed': 0, 'failed': 0, 'merged': 0}

        if not dest_base.exists():
            dest_base.mkdir(parents=True)

        for folder, files in plan.items():
            target_dir = dest_base / folder
            if not target_dir.exists():
                target_dir.mkdir(parents=True)

            for f in files:
                src = Path(f['original_path'])
                dst = target_dir / f['filename']

                try:
                    if dst.exists():
                        stem = dst.stem
                        suffix = dst.suffix
                        counter = 1
                        while dst.exists():
                            dst = target_dir / f"{stem}_{counter}{suffix}"
                            counter += 1
                        stats['merged'] += 1

                    shutil.copy2(src, dst)
                    stats['processed'] += 1
                except Exception as e:
                    print(f"Error copying {src}: {e}")
                    stats['failed'] += 1

        return stats