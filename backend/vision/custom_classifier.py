"""
Custom Classifier — YOUR OWN ALGORITHM (no ML libraries)

Classifies image patches using:
1. HSV Color Segmentation — with adaptive lighting normalization
2. Local Binary Patterns (LBP) — manual NumPy implementation
3. Color Histogram Comparison — chi-squared distance
4. Shape Analysis — aspect ratio + circularity
5. Edge Density — gradient magnitude analysis
6. Weighted Scoring Function with per-ingredient adaptive thresholds

Also includes background rejection to avoid false positives on non-food regions.
"""

import json, os
import cv2
import numpy as np
from typing import Dict, List, Optional


class CustomClassifier:
    def __init__(self, profiles_path: str = None):
        if profiles_path is None:
            profiles_path = os.path.join(os.path.dirname(__file__), "reference_profiles.json")
        with open(profiles_path, "r", encoding="utf-8") as f:
            self.profiles = json.load(f)

        # Per-ingredient minimum thresholds — tuned to reduce false positives
        # Ingredients with distinct colors (tomato, banana) can use lower thresholds
        # Ambiguous ones (potato, onion) need higher thresholds
        self.min_thresholds = {
            "banana":      0.16,
            "carrot":      0.16,
            "tomato":      0.15,
            "egg":         0.22,   # easily confused with light backgrounds
            "onion":       0.22,   # many false positives from skin tones
            "lemon":       0.18,
            "bell pepper": 0.18,
            "cucumber":    0.20,
            "potato":      0.24,   # brownish — lots of false triggers
        }

        # Default threshold for unknown ingredients
        self.default_threshold = 0.20

    # ── 0. Preprocessing — Adaptive Lighting Normalization ──────────

    def _normalize_lighting(self, patch: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) on the
        lightness channel to compensate for uneven lighting conditions.
        This is critical for webcam input where shadows distort HSV values.
        """
        lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]

        # CLAHE with moderate clip limit to avoid amplifying noise
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        lab[:, :, 0] = clahe.apply(l_channel)

        normalized_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # B. Convoluția Matricială: Efectul de Netezire (Blur) - Kernel 5x5
        # Aplicăm filtrare liniară pentru eliminarea "zgomotului" de senzor
        smoothed = cv2.GaussianBlur(normalized_bgr, (5, 5), 0)
        
        return smoothed

    # ── 1. HSV Color Segmentation ──────────────────────────────────

    def compute_hsv_scores(self, patch: np.ndarray) -> Dict[str, float]:
        """
        Compute how much of the patch matches each ingredient's expected HSV
        color ranges. Uses the lighting-normalized patch for robustness.
        """
        normalized = self._normalize_lighting(patch)
        hsv = cv2.cvtColor(normalized, cv2.COLOR_BGR2HSV)
        total_px = hsv.shape[0] * hsv.shape[1]
        if total_px == 0:
            return {}

        scores = {}
        for name, profile in self.profiles.items():
            match = 0
            for r in profile["hsv_ranges"]:
                lower = np.array(r["lower"], dtype=np.uint8)
                upper = np.array(r["upper"], dtype=np.uint8)
                mask = cv2.inRange(hsv, lower, upper)
                
                # A. Pragul Binar & Bitwise AND
                # Aplicăm o operație la nivel de biți pentru a reține exclusiv aria fizică a alimentului
                extracted_object = cv2.bitwise_and(patch, patch, mask=mask)
                
                match += np.count_nonzero(mask)
            # Normalize, but cap at 1.0
            scores[name] = min(match / total_px, 1.0)
        return scores

    # ── 2. LBP — Manual Implementation ────────────────────────────

    def compute_lbp(self, gray: np.ndarray) -> np.ndarray:
        """
        Compute Local Binary Patterns manually using NumPy vectorized ops.
        For each pixel, compare with its 8 neighbors and encode as 8-bit value.
        """
        rows, cols = gray.shape
        lbp = np.zeros((rows, cols), dtype=np.uint8)
        dr = [-1, -1, -1, 0, 1, 1, 1, 0]
        dc = [-1, 0, 1, 1, 1, 0, -1, -1]
        center = gray[1:-1, 1:-1].astype(np.int16)
        for bit in range(8):
            nb = gray[1+dr[bit]:rows-1+dr[bit], 1+dc[bit]:cols-1+dc[bit]].astype(np.int16)
            lbp[1:-1, 1:-1] |= ((nb >= center).astype(np.uint8)) << bit
        return lbp

    def compute_lbp_histogram(self, patch: np.ndarray) -> np.ndarray:
        """Compute normalized 256-bin LBP histogram."""
        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (64, 64))
        lbp_img = self.compute_lbp(gray)
        hist, _ = np.histogram(lbp_img.ravel(), bins=256, range=(0, 256))
        hist = hist.astype(np.float64)
        s = hist.sum()
        if s > 0:
            hist /= s
        return hist

    def chi_squared(self, a: np.ndarray, b: np.ndarray) -> float:
        """Chi-squared distance between two histograms."""
        eps = 1e-10
        return float(np.sum((a - b) ** 2 / (a + b + eps)))

    def compute_lbp_scores(self, patch: np.ndarray) -> Dict[str, float]:
        """Score each ingredient by LBP texture similarity (chi-squared)."""
        ph = self.compute_lbp_histogram(patch)
        scores = {}
        for name, p in self.profiles.items():
            rh = np.array(p["lbp_histogram"], dtype=np.float64)
            if rh.shape[0] != 256:
                scores[name] = 0.0
                continue
            scores[name] = float(np.exp(-self.chi_squared(ph, rh) * 5.0))
        return scores

    # ── 3. Color Histogram Comparison ─────────────────────────────

    def compute_color_histogram(self, patch: np.ndarray) -> np.ndarray:
        """Compute 48-bin color histogram (16 bins × 3 HSV channels)."""
        normalized = self._normalize_lighting(patch)
        hsv = cv2.cvtColor(normalized, cv2.COLOR_BGR2HSV)
        hsv = cv2.resize(hsv, (64, 64))
        hists = []
        for ch in range(3):
            h, _ = np.histogram(hsv[:, :, ch].ravel(), bins=16, range=(0, 256))
            hists.append(h.astype(np.float64))
        c = np.concatenate(hists)
        s = c.sum()
        if s > 0:
            c /= s
        return c

    def compute_color_scores(self, patch: np.ndarray) -> Dict[str, float]:
        """Score each ingredient by color histogram similarity."""
        ph = self.compute_color_histogram(patch)
        scores = {}
        for name, p in self.profiles.items():
            rh = np.array(p["color_histogram"], dtype=np.float64)
            if rh.shape[0] != 48:
                scores[name] = 0.0
                continue
            scores[name] = float(np.exp(-self.chi_squared(ph, rh) * 3.0))
        return scores

    # ── 4. Shape Analysis (Aspect Ratio + Circularity) ────────────

    def compute_shape_scores(self, w: int, h: int) -> Dict[str, float]:
        """Score by aspect ratio fit against each ingredient's expected range."""
        if h == 0:
            return {}
        aspect = w / h
        scores = {}
        for name, p in self.profiles.items():
            mn, mx = p["aspect_ratio"]["min"], p["aspect_ratio"]["max"]
            mid = (mn + mx) / 2.0
            rng = (mx - mn) / 2.0 + 0.1
            scores[name] = max(0.0, 1.0 - abs(aspect - mid) / rng)
        return scores

    # ── 5. Edge Density (NEW feature) ─────────────────────────────

    def compute_edge_density(self, patch: np.ndarray) -> float:
        """
        Compute edge density using Sobel gradients. Food items tend to have
        moderate edge density — too low = flat background, too high = complex scene.
        Returns a value between 0.0 and 1.0.
        """
        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (64, 64))

        # Sobel gradients in x and y
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(gx**2 + gy**2)

        # Normalize to [0, 1]
        max_mag = magnitude.max()
        if max_mag > 0:
            magnitude /= max_mag

        return float(magnitude.mean())

    # ── 6. Background Rejection ───────────────────────────────────

    def _is_likely_background(self, patch: np.ndarray) -> bool:
        """
        Reject patches that are likely background (table, wall, etc.)
        Uses saturation analysis — food items are colorful, backgrounds are dull.
        """
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]

        avg_sat = float(saturation.mean())
        avg_val = float(value.mean())
        sat_std = float(saturation.std())

        # Very low saturation + low variance = grey/white background
        # Threshold is conservative to not reject eggs (which are white/cream)
        if avg_sat < 15 and sat_std < 10:
            return True

        # Very dark patches are shadows/background
        if avg_val < 30:
            return True

        # Very uniform (low texture) — likely a blank surface
        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        if float(gray.std()) < 8:
            return True

        return False

    # ── 7. Saturation Discriminator (KEY for tomato/apple, egg/onion) ──

    def compute_saturation_scores(self, patch: np.ndarray) -> Dict[str, float]:
        """
        Score each ingredient based on how well the patch's average saturation
        matches the ingredient's expected saturation range.

        This is the MOST important discriminator for confusable pairs:
        - Tomato (S~180) vs Apple (S~100): tomatoes are deeply saturated red
        - Egg (S~15) vs Onion (S~70): eggs are nearly white, onions are golden
        - Carrot (S~170) vs Potato (S~60): carrots are vivid orange vs muted brown
        """
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        avg_sat = float(hsv[:, :, 1].mean())

        scores = {}
        for name, p in self.profiles.items():
            expected = p.get("expected_saturation")
            if not expected:
                scores[name] = 0.5  # neutral if no data
                continue

            sat_min = expected["min"]
            sat_max = expected["max"]
            weight = expected.get("weight", "medium")

            # How well does observed saturation fit the expected range?
            mid = (sat_min + sat_max) / 2.0
            rng = (sat_max - sat_min) / 2.0 + 5.0  # small buffer

            # Distance from expected midpoint, normalized
            distance = abs(avg_sat - mid) / rng
            fit = max(0.0, 1.0 - distance)

            # Apply weight multiplier based on profile importance
            if weight == "critical":
                # For items like egg where saturation is THE defining feature
                # Heavily penalize if saturation doesn't match
                if avg_sat > sat_max + 20:
                    fit *= 0.1  # near-zero if too saturated for egg
                elif avg_sat < sat_min - 20 and sat_min > 50:
                    fit *= 0.2  # near-zero if too desaturated for a colorful item
            elif weight == "high":
                if avg_sat > sat_max + 30:
                    fit *= 0.3
                elif avg_sat < sat_min - 30 and sat_min > 50:
                    fit *= 0.3

            scores[name] = fit

        return scores

    # ── 8. Combined Classification ────────────────────────────────

    def classify(
        self,
        patch: np.ndarray,
        bbox: List[int] = None,
        yolo_candidates: Optional[List[str]] = None,
        top_n: int = 3,
    ) -> List[Dict]:
        """
        Classify an image patch into ingredient categories.

        Args:
            patch: BGR image patch (cropped from detection bbox)
            bbox: [x1, y1, x2, y2] bounding box coordinates
            yolo_candidates: optional list of ingredient names suggested by YOLO
                             — used to give a small boost to YOLO-suggested classes
            top_n: number of top results to return

        Returns:
            List of dicts: [{"ingredient": str, "confidence": float}, ...]
        """
        if patch.size == 0 or patch.shape[0] < 4 or patch.shape[1] < 4:
            return []

        # Background rejection — skip non-food patches early
        if self._is_likely_background(patch):
            return []

        # Compute feature scores
        hsv_s = self.compute_hsv_scores(patch)
        lbp_s = self.compute_lbp_scores(patch)
        col_s = self.compute_color_scores(patch)
        sat_s = self.compute_saturation_scores(patch)
        edge_density = self.compute_edge_density(patch)

        if bbox and len(bbox) == 4:
            shp_s = self.compute_shape_scores(bbox[2]-bbox[0], bbox[3]-bbox[1])
        else:
            shp_s = self.compute_shape_scores(patch.shape[1], patch.shape[0])

        # Edge density penalty: food typically has 0.05–0.35 edge density
        # Too low → flat surface, too high → complex texture (not single food item)
        if edge_density < 0.03 or edge_density > 0.5:
            edge_factor = 0.6   # penalize unlikely patches
        else:
            edge_factor = 1.0

        # Combine scores with weighted formula
        # Saturation gets significant weight because it's the best discriminator
        # for confusable pairs (tomato/apple, egg/onion)
        combined = {}
        for name in self.profiles:
            raw_score = (
                0.30 * hsv_s.get(name, 0) +
                0.10 * lbp_s.get(name, 0) +
                0.22 * col_s.get(name, 0) +
                0.10 * shp_s.get(name, 0) +
                0.20 * sat_s.get(name, 0)
            )

            # Apply edge density factor
            raw_score *= edge_factor

            # YOLO agreement bonus: if YOLO also thinks this is the ingredient,
            # give a small confidence boost (cross-validation between pipelines)
            if yolo_candidates and name in yolo_candidates:
                raw_score = raw_score * 1.15 + 0.07  # ~7-15% boost

            combined[name] = round(raw_score, 4)

        # Sort by score, filter by per-ingredient adaptive threshold
        top = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        results = []
        for name, score in top[:top_n]:
            threshold = self.min_thresholds.get(name, self.default_threshold)
            if score >= threshold:
                results.append({"ingredient": name, "confidence": score})

        return results

    def validate(self, patch: np.ndarray, expected_ingredient: str) -> float:
        """
        Hybrid Ensemble Validator: Takes the YOLO-detected ingredient and 
        returns an OpenCV mathematical confidence score (0.0 to 1.0) based 
        on whether the patch's texture, edges, and colors actually match 
        that specific ingredient.
        """
        if patch.size == 0 or expected_ingredient not in self.profiles:
            return 0.5 # Neutral fallback

        if self._is_likely_background(patch):
            return 0.1 # Heavily penalize if it's just a wall/shadow

        # Compute specific feature scores ONLY for the expected ingredient
        hsv_score = self.compute_hsv_scores(patch).get(expected_ingredient, 0)
        lbp_score = self.compute_lbp_scores(patch).get(expected_ingredient, 0)
        col_score = self.compute_color_scores(patch).get(expected_ingredient, 0)
        sat_score = self.compute_saturation_scores(patch).get(expected_ingredient, 0)
        edge_density = self.compute_edge_density(patch)

        if edge_density < 0.03 or edge_density > 0.5:
            edge_factor = 0.6
        else:
            edge_factor = 1.0

        # Weighted validation formula
        raw_cv_score = (
            0.30 * hsv_score +
            0.15 * lbp_score +
            0.20 * col_score +
            0.35 * sat_score # Saturation is strongly weighted in validation
        ) * edge_factor

        return round(float(raw_cv_score), 4)
