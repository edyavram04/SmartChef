"""
Smart Chef — FastAPI Backend

- REST endpoints for recipes, nutrition, health check
- WebSocket endpoint for real-time video frame detection
"""

import asyncio
import base64
import json
import os

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from vision.yolo_detector import YOLODetector
from vision.custom_classifier import CustomClassifier
from logic.recipe_matcher import RecipeMatcher
from logic.nutrition import NutritionCalculator

app = FastAPI(title="Smart Chef API", version="1.0.0")

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


# ── REST Endpoints ──────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


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
    """
    await websocket.accept()
    print("[WS] Client connected")

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

                # Step 1: YOLO detection (bounding boxes)
                detections = yolo.detect(frame)

                # Step 2: Custom classification on each detection
                ingredients_found = set()
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
                    classifications = classifier.classify(patch, bbox=bbox)

                    if classifications:
                        best = classifications[0]
                        
                        # Filter out very low confidence custom matches (likely background noise)
                        if best["confidence"] < 0.15:
                            continue
                            
                        ingredient = best["ingredient"]
                        
                        # Scale the manual math score to look like a proper confidence 
                        # (a distance score of 0.45 is actually very high, so we map it to ~0.90)
                        confidence = min(0.99, best["confidence"] * 1.8 + 0.1)
                        ingredients_found.add(ingredient)
                    else:
                        # Fall back to YOLO mapping
                        ingredient = det.get("ingredient")
                        confidence = det["confidence"]
                        if ingredient:
                            ingredients_found.add(ingredient)

                    enriched_detections.append({
                        "bbox": bbox,
                        "ingredient": ingredient,
                        "confidence": round(confidence, 2),
                        "yolo_class": det["class_name"],
                    })

                # Step 3: Match recipes
                ing_list = list(ingredients_found)
                matched_recipes = matcher.match(ing_list) if ing_list else []

                # Step 4: Nutrition
                nutrition_data = nutrition.calculate(ing_list) if ing_list else None

                # Send response
                await websocket.send_json({
                    "detections": enriched_detections,
                    "ingredients": sorted(ing_list),
                    "recipes": matched_recipes[:5],
                    "nutrition": nutrition_data,
                })

            except Exception as e:
                await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
