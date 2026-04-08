"""
Custom Classifier — YOUR OWN ALGORITHM (no ML libraries)

Classifies image patches using:
1. HSV Color Segmentation
2. Local Binary Patterns (LBP) — manual NumPy implementation
3. Color Histogram Comparison — chi-squared distance
4. Weighted Scoring Function
"""

import json, os
import cv2
import numpy as np
from typing import Dict, List


class CustomClassifier:
    def __init__(self, profiles_path: str = None):
        if profiles_path is None:
            profiles_path = os.path.join(os.path.dirname(__file__), "reference_profiles.json")
        with open(profiles_path, "r", encoding="utf-8") as f:
            self.profiles = json.load(f)

    # 1. HSV Color Segmentation
    def compute_hsv_scores(self, patch: np.ndarray) -> Dict[str, float]:
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        total_px = hsv.shape[0] * hsv.shape[1]
        if total_px == 0:
            return {}
        scores = {}
        for name, profile in self.profiles.items():
            match = 0
            for r in profile["hsv_ranges"]:
                mask = cv2.inRange(hsv, np.array(r["lower"], dtype=np.uint8), np.array(r["upper"], dtype=np.uint8))
                match += np.count_nonzero(mask)
            scores[name] = min(match / total_px, 1.0)
        return scores

    # 2. LBP — Manual Implementation
    def compute_lbp(self, gray: np.ndarray) -> np.ndarray:
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
        eps = 1e-10
        return float(np.sum((a - b) ** 2 / (a + b + eps)))

    def compute_lbp_scores(self, patch: np.ndarray) -> Dict[str, float]:
        ph = self.compute_lbp_histogram(patch)
        scores = {}
        for name, p in self.profiles.items():
            rh = np.array(p["lbp_histogram"], dtype=np.float64)
            if rh.shape[0] != 256:
                scores[name] = 0.0; continue
            scores[name] = float(np.exp(-self.chi_squared(ph, rh) * 5.0))
        return scores

    # 3. Color Histogram Comparison
    def compute_color_histogram(self, patch: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
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
        ph = self.compute_color_histogram(patch)
        scores = {}
        for name, p in self.profiles.items():
            rh = np.array(p["color_histogram"], dtype=np.float64)
            if rh.shape[0] != 48:
                scores[name] = 0.0; continue
            scores[name] = float(np.exp(-self.chi_squared(ph, rh) * 3.0))
        return scores

    # 4. Shape (Aspect Ratio)
    def compute_shape_scores(self, w: int, h: int) -> Dict[str, float]:
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

    # 5. Combined Classification
    def classify(self, patch: np.ndarray, bbox: List[int] = None, top_n: int = 3) -> List[Dict]:
        if patch.size == 0 or patch.shape[0] < 4 or patch.shape[1] < 4:
            return []
        hsv_s = self.compute_hsv_scores(patch)
        lbp_s = self.compute_lbp_scores(patch)
        col_s = self.compute_color_scores(patch)
        if bbox and len(bbox) == 4:
            shp_s = self.compute_shape_scores(bbox[2]-bbox[0], bbox[3]-bbox[1])
        else:
            shp_s = self.compute_shape_scores(patch.shape[1], patch.shape[0])

        combined = {}
        for name in self.profiles:
            combined[name] = round(
                0.35*hsv_s.get(name,0) + 0.20*lbp_s.get(name,0) +
                0.30*col_s.get(name,0) + 0.15*shp_s.get(name,0), 4)

        top = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return [{"ingredient": n, "confidence": c} for n, c in top[:top_n]]
