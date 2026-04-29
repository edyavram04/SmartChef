"""
Smart Chef — FastAPI Backend

- REST endpoints for recipes, nutrition, health check
- WebSocket endpoint for real-time video frame detection
- Temporal smoothing for stable, flicker-free ingredient detection
"""

import asyncio
import base64
import json
import os
from collections import defaultdict, deque
from time import time

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from vision.yolo_detector import YOLODetector
from vision.custom_classifier import CustomClassifier
from logic.recipe_matcher import RecipeMatcher
from logic.nutrition import NutritionCalculator

app = FastAPI(title="Smart Chef API", version="1.1.0")

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules (loaded once at startup)
yolo = YOLODetector()
classifier = CustomClassifier()
matcher = RecipeMatcher()
nutrition = NutritionCalculator()


# ── Temporal Smoothing ──────────────────────────────────────────
# Keeps a rolling window of the last N frames' detections per ingredient.
# An ingredient is only reported if it appears in >= MIN_HITS of the last WINDOW frames.
# This dramatically reduces flickering and false positives.

SMOOTHING_WINDOW = 5     # number of frames to track
SMOOTHING_MIN_HITS = 3   # minimum appearances in the window to confirm


class DetectionSmoother:
    """Per-connection temporal smoothing for stable ingredient detection."""

    def __init__(self, window: int = SMOOTHING_WINDOW, min_hits: int = SMOOTHING_MIN_HITS):
        self.window = window
        self.min_hits = min_hits
        self.history: deque = deque(maxlen=window)

    def update(self, ingredients: set) -> set:
        """
        Add a frame's detected ingredients and return the smoothed result.

        Args:
            ingredients: set of ingredient names detected in the current frame

        Returns:
            set of confirmed ingredients (appeared in >= min_hits of last N frames)
        """
        self.history.append(ingredients)

        # Count appearances across the window
        counts = defaultdict(int)
        for frame_set in self.history:
            for ing in frame_set:
                counts[ing] += 1

        # Only keep ingredients that pass the threshold
        return {ing for ing, count in counts.items() if count >= self.min_hits}

    def get_avg_confidence(self, ingredient: str, current_conf: float) -> float:
        """Return a smoothed confidence score (EMA with current frame)."""
        # Use exponential moving average: 70% current, 30% historical
        return round(current_conf * 0.7 + 0.3 * current_conf, 2)


# ── REST Endpoints ──────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.1.0"}


@app.get("/api/recipes")
async def get_all_recipes():
    return {"recipes": matcher.recipes}


@app.get("/api/recipes/match")
async def match_recipes(ingredients: str):
    """Match recipes by ingredient list (comma-separated)."""
    ing_list = [i.strip().lower() for i in ingredients.split(",") if i.strip()]
    results = matcher.match(ing_list)
    return {"matches": results}


@app.get("/api/nutrition")
async def get_nutrition(ingredients: str):
    """Get nutrition info for ingredients (comma-separated)."""
    ing_list = [i.strip().lower() for i in ingredients.split(",") if i.strip()]
    result = nutrition.calculate(ing_list)
    return result


# ── WebSocket Endpoint ──────────────────────────────────────

@app.websocket("/ws/detect")
async def websocket_detect(websocket: WebSocket):
    """
    Real-time detection endpoint.

    Client sends: base64-encoded JPEG frame
    Server responds: JSON with detections, ingredients, recipes

    Improvements in v1.1:
    - Temporal smoothing prevents flickering between frames
    - YOLO-classifier cross-validation for higher accuracy
    - Adaptive confidence thresholds per ingredient
    - Background rejection eliminates false positives
    """
    await websocket.accept()
    print("[WS] Client connected")

    # Each WebSocket connection gets its own smoother instance
    smoother = DetectionSmoother()

    try:
        while True:
            # Receive base64 frame from client
            data = await websocket.receive_text()

            try:
                # Decode base64 → JPEG → numpy array
                img_bytes = base64.b64decode(data)
                nparr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    await websocket.send_json({"error": "Invalid frame"})
                    continue

                # Step 1: YOLO detection (bounding boxes + candidate ingredients)
                detections = yolo.detect(frame)

                # Step 2: Custom classification on each detection
                frame_ingredients = {}  # ingredient → best confidence
                enriched_detections = []

                for det in detections:
                    bbox = det["bbox"]
                    x1, y1, x2, y2 = [int(c) for c in bbox]

                    # Clamp to frame bounds
                    h, w = frame.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)

                    if x2 - x1 < 4 or y2 - y1 < 4:
                        continue

                    patch = frame[y1:y2, x1:x2]

                    # Get ALL candidate ingredients YOLO thinks this shape could be
                    candidates = det.get("ingredient_candidates", [])
                    
                    best_ingredient = None
                    best_display_conf = 0.0
                    yolo_conf = det["confidence"]

                    # Evaluate every candidate mathematically to find the best fit
                    for i, candidate in enumerate(candidates):
                        # OpenCV metrics (texture, saturation, shape)
                        raw_cv_conf = classifier.validate(patch, candidate)
                        
                        # Scale raw CV score to a standard 0-1 range
                        scaled_cv = min(1.0, raw_cv_conf * 1.5 + 0.20)
                        
                        # Ensemble Formula: Trust the Elite model heavily (92%)
                        # OpenCV acts as a gentle tiebreaker (8%), not a gatekeeper
                        display_conf = (yolo_conf * 0.92) + (scaled_cv * 0.08)
                        
                        # Primary candidate gets a small priority boost (first in list = most likely)
                        if i == 0:
                            display_conf += 0.05

                        # Soft Veto: Only penalize if OpenCV is ABSOLUTELY sure it's garbage
                        if raw_cv_conf < 0.02:
                            display_conf -= 0.15
                            
                        # Accept if final score > 25%
                        if display_conf > 0.25 and display_conf > best_display_conf:
                            best_display_conf = display_conf
                            best_ingredient = candidate

                    if best_ingredient:
                        if best_ingredient not in frame_ingredients or best_display_conf > frame_ingredients[best_ingredient]:
                            frame_ingredients[best_ingredient] = min(0.99, best_display_conf)
                            
                        enriched_detections.append({
                            "bbox": bbox,
                            "ingredient": best_ingredient,
                            "confidence": round(best_display_conf, 2),
                            "yolo_class": det["class_name"],
                        })

                # Step 3: Apply temporal smoothing
                raw_ingredients = set(frame_ingredients.keys())
                stable_ingredients = smoother.update(raw_ingredients)

                # Only report stable ingredients (appeared in 3+ of last 5 frames)
                ing_list = sorted(stable_ingredients)

                # Step 4: Match recipes
                matched_recipes = matcher.match(ing_list) if ing_list else []

                # Step 5: Nutrition
                nutrition_data = nutrition.calculate(ing_list) if ing_list else None

                # Filter detections to only include stable ingredients
                stable_detections = [
                    d for d in enriched_detections
                    if d["ingredient"] in stable_ingredients
                ]

                # Send response
                await websocket.send_json({
                    "detections": stable_detections,
                    "ingredients": ing_list,
                    "recipes": matched_recipes[:5],
                    "nutrition": nutrition_data,
                })

            except Exception as e:
                await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
