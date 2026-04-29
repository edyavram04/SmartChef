"""
YOLO Custom Detector — Elite Edition

Uses the custom-trained YOLOv8 model (smartchef_custom_model.pt) which directly
recognizes ingredient classes. No more COCO mapping hacks needed.
"""

import numpy as np
import os
from ultralytics import YOLO

# Direct mapping from the model's 20 dataset classes to our 9 app ingredients.
# Classes not in this map are ignored (avocado, chicken, fish, etc.)
DATASET_TO_INGREDIENT = {
    "Banana":    "banana",
    "Potato":    "potato",
    "apple":     "tomato",      # Dataset "apple" class catches round red things = our tomatoes
    "carrot":    "carrot",
    "cucumber":  "cucumber",
    "egg":       "egg",
    "onion":     "onion",
    "orange":    "lemon",       # Citrus shape → lemon in our app
    "tomato":    "tomato",
    "cabbage":   "onion",       # Cabbage shape similar to large onion
    "eggplant":  "cucumber",    # Long dark shape fallback
    "broccoli":  "bell pepper", # Green veggie fallback
    "garlic":    "egg",         # Small round white object fallback
    "mushroom":  "potato",      # Brown/tan objects fallback
}


class YOLODetector:
    """YOLOv8 wrapper using the elite custom-trained model."""

    def __init__(self, model_filename: str = "smartchef_custom_model.pt", confidence: float = 0.15):
        """
        Initialize the custom YOLO detector.

        Args:
            model_filename: Name of the custom model inside the models/ folder.
            confidence: Very low threshold (0.15) to maximize recall.
                        The Hybrid Ensemble handles precision downstream.
        """
        model_path = os.path.join(os.path.dirname(__file__), "models", model_filename)

        if not os.path.exists(model_path):
            print(f"[WARNING] Custom model {model_path} not found. Falling back to yolov8n.pt")
            model_path = "yolov8n.pt"

        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame: np.ndarray) -> list:
        """
        Run detection on a single frame using the custom-trained model.

        Returns:
            List of detection dicts with direct ingredient mapping.
        """
        if frame is None or frame.size == 0:
            return []

        results = self.model(frame, verbose=False, conf=self.confidence, stream=True)
        detections = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().item()
                cls_id = int(box.cls[0].cpu().item())

                class_name = self.model.names[cls_id]

                # Map dataset class to our ingredient
                mapped = DATASET_TO_INGREDIENT.get(class_name)

                if mapped:
                    # Build candidates list: the mapped ingredient + any alternatives
                    # This lets the OpenCV validator pick the best mathematical match
                    candidates = [mapped]

                    # For ambiguous classes, add secondary candidates
                    if class_name == "apple":
                        candidates = ["tomato", "onion"]
                    elif class_name == "garlic":
                        candidates = ["egg", "onion"]
                    elif class_name == "cabbage":
                        candidates = ["onion", "potato"]
                    elif class_name == "mushroom":
                        candidates = ["potato", "egg"]
                    elif class_name == "eggplant":
                        candidates = ["cucumber", "carrot"]

                    detections.append({
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "confidence": float(conf),
                        "class_name": class_name,
                        "ingredient": mapped,
                        "ingredient_candidates": candidates,
                    })

        return detections
