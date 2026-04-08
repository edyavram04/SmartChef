"""
YOLO Detector — Wraps YOLOv8 for real-time food object detection.

Uses the YOLOv8n (nano) model for speed on CPU.
Filters detections to food-relevant COCO classes only.
"""

import numpy as np
from ultralytics import YOLO


# COCO class IDs relevant to food items
# 46=banana, 47=apple, 49=orange, 50=broccoli, 51=carrot,
# 52=hot dog, 53=pizza, 54=donut, 55=cake, 56=potted plant (sometimes herbs)
FOOD_CLASS_IDS = {46, 47, 49, 50, 51, 52, 53, 54, 55}

# Mapping from COCO class names to our ingredient vocabulary
COCO_TO_INGREDIENT = {
    "banana": "banana",
    "apple": "apple",
    "orange": "lemon",  # closest match
    "carrot": "carrot",
    "broccoli": "bell pepper",  # rough mapping for green veggies
}


class YOLODetector:
    """YOLOv8 wrapper for food object detection."""

    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.50):
        """
        Initialize the YOLO detector.

        Args:
            model_path: Path to YOLOv8 model weights. Downloads automatically
                        if not found locally.
            confidence: Minimum confidence threshold for detections.
        """
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame: np.ndarray) -> list:
        """
        Run detection on a single frame.

        Args:
            frame: BGR numpy array (H, W, 3)

        Returns:
            List of detection dicts:
            [
                {
                    "class_name": "apple",
                    "confidence": 0.87,
                    "bbox": [x1, y1, x2, y2],  # pixel coordinates
                    "ingredient": "apple"       # mapped ingredient name
                },
                ...
            ]
        """
        results = self.model(frame, conf=self.confidence, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                class_id = int(boxes.cls[i].item())
                conf = float(boxes.conf[i].item())
                class_name = self.model.names[class_id]
                bbox = boxes.xyxy[i].cpu().numpy().tolist()

                # Map to our ingredient vocabulary
                ingredient = COCO_TO_INGREDIENT.get(class_name)

                detections.append(
                    {
                        "class_name": class_name,
                        "confidence": round(conf, 2),
                        "bbox": [round(c) for c in bbox],
                        "ingredient": ingredient,
                    }
                )

        return detections
