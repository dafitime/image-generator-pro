"""
src/ai/efficientnet_tagger.py
Uses EfficientNet B7 (pretrained on ImageNet) for tagging.
Outputs tags from 1000 predefined classes.
"""
import torch
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
from pathlib import Path

class EfficientNetTagger:
    def __init__(self, threshold=0.5, device=None):
        """
        :param threshold: Confidence threshold (0.0–1.0). Lower = more tags.
        :param device: 'cuda' or 'cpu'. Auto-detected if None.
        """
        self.threshold = threshold
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")

        # Load pretrained EfficientNet B7
        self.model = models.efficientnet_b7(weights='DEFAULT')
        self.model.eval()
        self.model.to(self.device)

        # Standard ImageNet preprocessing
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        # Load ImageNet class labels
        self.classes = self._load_classes()

    def _load_classes(self):
        """Load ImageNet class names from file."""
        class_file = Path(__file__).parent.parent.parent / "imagenet_classes.txt"
        try:
            with open(class_file, 'r') as f:
                return [line.strip() for line in f.readlines()]
        except Exception as e:
            print(f"Failed to load imagenet_classes.txt: {e}")
            return [f"class_{i}" for i in range(1000)]

    def set_threshold(self, threshold):
        self.threshold = max(0.0, min(1.0, threshold))

    def predict_tags(self, image_path, top_k=5):
        """
        Returns list of tags above threshold, sorted by confidence.
        """
        image = Image.open(image_path).convert('RGB')
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = F.softmax(outputs[0], dim=0)

        # Gather tags above threshold
        results = []
        for idx, prob in enumerate(probabilities):
            if prob > self.threshold:
                results.append((self.classes[idx], prob.item()))

        results.sort(key=lambda x: x[1], reverse=True)
        return [tag for tag, _ in results[:top_k]]

    def predict_tags_batch(self, image_paths, top_k=5):
        """
        Batch prediction for multiple images (faster).
        """
        images = []
        valid_indices = []
        valid_paths = []
        for i, path in enumerate(image_paths):
            try:
                img = Image.open(path).convert('RGB')
                images.append(self.transform(img))
                valid_indices.append(i)
                valid_paths.append(path)
            except Exception:
                continue

        if not images:
            return [[] for _ in image_paths]

        batch = torch.stack(images).to(self.device)
        with torch.no_grad():
            outputs = self.model(batch)
            probabilities = F.softmax(outputs, dim=1)

        # Process each image in batch
        batch_results = []
        prob_idx = 0
        for i in range(len(image_paths)):
            if i in valid_indices:
                probs = probabilities[prob_idx]
                results = []
                for idx, prob in enumerate(probs):
                    if prob > self.threshold:
                        results.append((self.classes[idx], prob.item()))
                results.sort(key=lambda x: x[1], reverse=True)
                batch_results.append([tag for tag, _ in results[:top_k]])
                prob_idx += 1
            else:
                batch_results.append([])  # failed image gets no tags
        return batch_results