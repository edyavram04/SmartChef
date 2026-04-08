"""
Nutrition Calculator — Estimates nutritional values for detected ingredients.

Reads per-100g data from nutrition_data.json and computes totals
using typical serving sizes. No external libraries needed.
"""

import json
import os
from typing import Dict, List


class NutritionCalculator:
    """Calculates nutritional breakdown for a set of ingredients."""

    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = os.path.join(
                os.path.dirname(__file__), "..", "data", "nutrition_data.json"
            )
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.nutrition_db = data["ingredients"]

    def calculate(self, ingredient_names: List[str]) -> Dict:
        """
        Calculate total and per-ingredient nutrition for detected ingredients.

        Returns:
            {
                "total": {"calories": ..., "protein": ..., "carbs": ..., "fat": ..., "fiber": ...},
                "per_ingredient": [
                    {"name": "apple", "emoji": "🍎", "serving_g": 150, "calories": 78, ...},
                    ...
                ]
            }

        Values are estimated using typical serving sizes (not per-100g).
        """
        total = {
            "calories": 0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
        }
        per_ingredient = []

        for name in ingredient_names:
            if name not in self.nutrition_db:
                continue

            info = self.nutrition_db[name]
            serving = info["serving_g"]
            factor = serving / 100.0  # scale from per-100g to per-serving

            item = {
                "name": name,
                "emoji": info.get("emoji", "🍽️"),
                "serving_g": serving,
                "calories": round(info["calories"] * factor),
                "protein": round(info["protein"] * factor, 1),
                "carbs": round(info["carbs"] * factor, 1),
                "fat": round(info["fat"] * factor, 1),
                "fiber": round(info["fiber"] * factor, 1),
            }
            per_ingredient.append(item)

            total["calories"] += item["calories"]
            total["protein"] += item["protein"]
            total["carbs"] += item["carbs"]
            total["fat"] += item["fat"]
            total["fiber"] += item["fiber"]

        # Round totals
        total["protein"] = round(total["protein"], 1)
        total["carbs"] = round(total["carbs"], 1)
        total["fat"] = round(total["fat"], 1)
        total["fiber"] = round(total["fiber"], 1)

        return {"total": total, "per_ingredient": per_ingredient}
