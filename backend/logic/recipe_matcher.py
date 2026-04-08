"""
Recipe Matcher — Custom recommendation algorithm using Jaccard Similarity.

This module matches detected ingredients against a recipe database,
scoring each recipe by coverage, complexity, and Jaccard similarity.
100% custom code, no ML libraries.
"""

import json
import os
from typing import List, Dict, Tuple


class RecipeMatcher:
    """Matches detected ingredients to recipes using custom scoring."""

    def __init__(self, recipes_path: str = None):
        if recipes_path is None:
            recipes_path = os.path.join(
                os.path.dirname(__file__), "..", "data", "recipes.json"
            )
        with open(recipes_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.recipes = data["recipes"]

    def jaccard_similarity(self, set_a: set, set_b: set) -> float:
        """
        Compute Jaccard Similarity: J(A,B) = |A ∩ B| / |A ∪ B|
        Returns 0.0 if both sets are empty.
        """
        intersection = set_a & set_b
        union = set_a | set_b
        if not union:
            return 0.0
        return len(intersection) / len(union)

    def coverage_score(
        self, detected: set, recipe_ingredients: List[Dict]
    ) -> float:
        """
        Weighted coverage score — primary ingredients count more.
        Primary ingredient match = 2x weight, secondary = 1x weight.
        """
        total_weight = 0.0
        matched_weight = 0.0

        for ing in recipe_ingredients:
            weight = 2.0 if ing["importance"] == "primary" else 1.0
            total_weight += weight
            if ing["name"] in detected:
                matched_weight += weight

        if total_weight == 0:
            return 0.0
        return matched_weight / total_weight

    def complexity_score(
        self, detected: set, recipe_ingredients: List[Dict]
    ) -> float:
        """
        Complexity score — fewer missing ingredients = higher score.
        Score = 1 - (missing / total), clamped to [0, 1].
        """
        recipe_names = {ing["name"] for ing in recipe_ingredients}
        missing = recipe_names - detected
        total = len(recipe_names)
        if total == 0:
            return 0.0
        return 1.0 - (len(missing) / total)

    def match(
        self, detected_ingredients: List[str], top_n: int = 5
    ) -> List[Dict]:
        """
        Match detected ingredients against all recipes.
        Returns top_n recipes sorted by combined score (descending).

        Combined score = 0.4 * jaccard + 0.35 * coverage + 0.25 * complexity

        Each result includes the recipe data plus:
        - match_percent: int (0-100)
        - matched_ingredients: list of matched ingredient names
        - missing_ingredients: list of missing ingredient names
        """
        detected_set = set(detected_ingredients)
        results = []

        for recipe in self.recipes:
            recipe_ing_names = {ing["name"] for ing in recipe["ingredients"]}

            j_score = self.jaccard_similarity(detected_set, recipe_ing_names)
            c_score = self.coverage_score(detected_set, recipe["ingredients"])
            x_score = self.complexity_score(detected_set, recipe["ingredients"])

            # Weighted combination
            combined = 0.40 * j_score + 0.35 * c_score + 0.25 * x_score

            matched = list(detected_set & recipe_ing_names)
            missing = list(recipe_ing_names - detected_set)

            # Only include recipes that have at least 1 ingredient matched
            if matched:
                results.append(
                    {
                        **recipe,
                        "match_percent": round(combined * 100),
                        "matched_ingredients": sorted(matched),
                        "missing_ingredients": sorted(missing),
                    }
                )

        # Sort by match percentage descending, then by fewer missing ingredients
        results.sort(
            key=lambda r: (r["match_percent"], -len(r["missing_ingredients"])),
            reverse=True,
        )

        return results[:top_n]
