"""
src/ai_processor.py
Heavyweight AI tagging using PyTorch & Transformers (ViT).
UPGRADED: Massive military/technical vocabulary and hierarchical categorization.
"""
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image

class AIImageProcessor:
    def __init__(self, use_gpu: bool = False):
        self.model = None
        self.feature_extractor = None
        self.device = None
        self._load_successful = False
        
        # --- EXPANDED VOCABULARY ---
        # Maps specific keywords to Broad Categories
        self.category_mapping = {
            'Military': [
                'tank', 'cannon', 'artillery', 'missile', 'projectile', 'weapon', 'rifle', 
                'gun', 'firearm', 'soldier', 'uniform', 'camouflage', 'mortar', 'howitzer', 
                'rocket', 'grenade', 'warplane', 'fighter', 'bomber', 'aircraft', 'helicopter',
                'carrier', 'submarine', 'warship', 'battleship', 'destroyer', 'frigate',
                'jeep', 'humvee', 'armored', 'radar', 'antenna', 'radio', 'satellite'
            ],
            'Electronics': [
                'screen', 'monitor', 'computer', 'keyboard', 'mouse', 'laptop', 'server',
                'circuit', 'chip', 'processor', 'robot', 'drone', 'sensor', 'camera', 'lens',
                'cable', 'wire', 'battery', 'charger', 'plug', 'socket', 'switch', 'console'
            ],
            'Vehicles': [
                'car', 'truck', 'bus', 'train', 'bicycle', 'motorcycle', 'boat', 'ship', 
                'liner', 'yacht', 'vehicle', 'wheel', 'tire', 'engine', 'motor'
            ],
            'Construction': [
                'crane', 'drill', 'hammer', 'tool', 'wrench', 'screwdriver', 'pliers', 
                'helmet', 'vest', 'ladder', 'scaffold', 'concrete', 'brick', 'building'
            ],
            'Nature': [
                'mountain', 'beach', 'forest', 'tree', 'flower', 'grass', 'sky', 'cloud', 
                'sunset', 'sunrise', 'river', 'lake', 'ocean', 'sea', 'water', 'sand'
            ],
            'Animals': [
                'dog', 'cat', 'bird', 'horse', 'cow', 'sheep', 'wildlife', 'pet', 'animal',
                'fish', 'insect', 'reptile', 'amphibian'
            ],
            'People': [
                'person', 'man', 'woman', 'child', 'girl', 'boy', 'face', 'portrait', 
                'crowd', 'group', 'people', 'human'
            ]
        }
        
        self._init_model()

    def _init_model(self):
        print("Initializing PyTorch AI Engine (ViT)...")
        try:
            import torch
            from transformers import ViTForImageClassification, ViTImageProcessor

            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # ViT Base - Good balance of speed and accuracy
            model_name = "google/vit-base-patch16-224"
            
            print(f"Loading model: {model_name}...")
            self.feature_extractor = ViTImageProcessor.from_pretrained(model_name)
            self.model = ViTForImageClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self._load_successful = True
            print(f"✅ AI Engine loaded on {self.device}")
        except Exception as e:
            print(f"❌ AI Engine failed to load: {e}")
            self._load_successful = False

    def analyze_image(self, image_path: Path) -> List[Dict[str, Any]]:
        if not self._load_successful: return []
        
        try:
            import torch
            
            image = Image.open(image_path).convert("RGB")
            inputs = self.feature_extractor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

            # Get Top 20 predictions (Cast wide net)
            top_probs, top_indices = torch.topk(probs, 20)
            
            predictions = []
            for score, idx in zip(top_probs[0], top_indices[0]):
                score = score.item()
                # Ultra-low threshold to capture details (1%)
                if score > 0.01: 
                    label = self.model.config.id2label[idx.item()]
                    clean_label = self._clean_label(label)
                    
                    predictions.append({
                        'label': clean_label,
                        'confidence': score,
                        'category': self._get_category(clean_label)
                    })
            return predictions

        except Exception as e:
            print(f"Error processing {image_path.name}: {e}")
            return []

    def _clean_label(self, label: str) -> str:
        # Cleans ImageNet labels (e.g. "n045... projectile, missile" -> "projectile")
        if ' ' in label and label.split(' ')[0].startswith('n0'):
             label = " ".join(label.split(' ')[1:])
        # Return the first synonym
        return label.split(',')[0].lower().replace('_', ' ').strip()

    def _get_category(self, label: str) -> str:
        """Finds which high-level bucket a tag belongs to."""
        for category, terms in self.category_mapping.items():
            if any(term in label for term in terms):
                return category
        return "Uncategorized"

    def generate_ai_tags(self, image_path: Path, min_confidence: float = 0.02) -> List[str]:
        """
        Public API. Returns a list of unique tags.
        """
        predictions = self.analyze_image(image_path)
        tags = []
        for pred in predictions:
            if pred['confidence'] >= min_confidence:
                # Add the specific tag (e.g., 'tank')
                tags.append(pred['label'])
                
                # Add the category if confidence is decent (e.g., 'Military')
                # But don't spam 'Uncategorized'
                if pred['category'] != 'Uncategorized' and pred['confidence'] > 0.05:
                    tags.append(pred['category'])
                    
        return list(set(tags))