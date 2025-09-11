"""
🎨 Shade Normalization and Fallback System
This module handles shade matching and OOS fallback logic
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ShadeInfo:
    """Normalized shade information"""

    shade_id: str
    raw_name: str
    hex_color: Optional[str] = None
    undertone: Optional[str] = None
    depth: Optional[str] = None  # light, medium, deep
    finish: Optional[str] = None  # matte, satin, natural


class ShadeNormalizer:
    """Handles shade normalization and neighbor mapping"""

    def __init__(
        self,
        shade_map_path: str = "data/shade_map.json",
        neighbors_path: str = "data/shade_neighbors.json",
    ):
        self.shade_map_path = shade_map_path
        self.neighbors_path = neighbors_path
        self._shade_map: Dict[str, ShadeInfo] = {}
        self._neighbors: Dict[str, List[str]] = {}
        self._load_mappings()

    def _load_mappings(self):
        """Load shade mappings and neighbor relationships"""
        # Load shade map
        if os.path.exists(self.shade_map_path):
            try:
                with open(self.shade_map_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for raw_name, info in data.items():
                        self._shade_map[raw_name.lower().strip()] = ShadeInfo(
                            shade_id=info.get("shade_id", "unknown"),
                            raw_name=raw_name,
                            hex_color=info.get("hex"),
                            undertone=info.get("undertone"),
                            depth=info.get("depth"),
                            finish=info.get("finish"),
                        )
            except Exception as e:
                print(f"Warning: Could not load shade map: {e}")

        # Load neighbors
        if os.path.exists(self.neighbors_path):
            try:
                with open(self.neighbors_path, "r", encoding="utf-8") as f:
                    self._neighbors = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load shade neighbors: {e}")

        # Initialize default mappings if files don't exist
        if not self._shade_map:
            self._init_default_mappings()

    def _init_default_mappings(self):
        """Initialize basic shade mappings for common shades"""
        default_shades = {
            # Foundation shades
            "porcelain": {"shade_id": "found_001", "undertone": "cool", "depth": "light"},
            "ivory": {"shade_id": "found_002", "undertone": "neutral", "depth": "light"},
            "fair": {"shade_id": "found_003", "undertone": "warm", "depth": "light"},
            "light": {"shade_id": "found_004", "undertone": "neutral", "depth": "light"},
            "light medium": {"shade_id": "found_005", "undertone": "neutral", "depth": "medium"},
            "medium": {"shade_id": "found_006", "undertone": "neutral", "depth": "medium"},
            "medium deep": {"shade_id": "found_007", "undertone": "neutral", "depth": "medium"},
            "deep": {"shade_id": "found_008", "undertone": "neutral", "depth": "deep"},
            # Concealer shades
            "fair concealer": {"shade_id": "conc_001", "undertone": "neutral", "depth": "light"},
            "light concealer": {"shade_id": "conc_002", "undertone": "neutral", "depth": "light"},
            "medium concealer": {"shade_id": "conc_003", "undertone": "neutral", "depth": "medium"},
            # Lipstick colors
            "nude": {"shade_id": "lip_001", "undertone": "neutral", "finish": "satin"},
            "pink": {"shade_id": "lip_002", "undertone": "cool", "finish": "satin"},
            "coral": {"shade_id": "lip_003", "undertone": "warm", "finish": "satin"},
            "red": {"shade_id": "lip_004", "undertone": "neutral", "finish": "satin"},
            "berry": {"shade_id": "lip_005", "undertone": "cool", "finish": "satin"},
        }

        for raw_name, info in default_shades.items():
            self._shade_map[raw_name.lower()] = ShadeInfo(
                shade_id=info["shade_id"],
                raw_name=raw_name,
                undertone=info.get("undertone"),
                depth=info.get("depth"),
                finish=info.get("finish"),
            )

        # Default neighbor relationships
        self._neighbors = {
            "found_001": ["found_002", "found_003"],  # porcelain → ivory, fair
            "found_002": ["found_001", "found_003", "found_004"],  # ivory → porcelain, fair, light
            "found_003": ["found_002", "found_004"],  # fair → ivory, light
            "found_004": ["found_003", "found_005"],  # light → fair, light medium
            "found_005": ["found_004", "found_006"],  # light medium → light, medium
            "found_006": ["found_005", "found_007"],  # medium → light medium, medium deep
            "found_007": ["found_006", "found_008"],  # medium deep → medium, deep
            "found_008": ["found_007"],  # deep → medium deep
        }

    def normalize_shade(self, raw_shade_name: Optional[str]) -> ShadeInfo:
        """Normalize a raw shade name to ShadeInfo"""
        if not raw_shade_name:
            return ShadeInfo(shade_id="unknown", raw_name="")

        key = raw_shade_name.lower().strip()

        # Direct match
        if key in self._shade_map:
            return self._shade_map[key]

        # Fuzzy matching for common variations
        for mapped_key, shade_info in self._shade_map.items():
            if key in mapped_key or mapped_key in key:
                return shade_info

        # No match found
        return ShadeInfo(shade_id=f"unknown_{hash(key) % 1000:03d}", raw_name=raw_shade_name)

    def get_shade_neighbors(self, shade_id: str) -> List[str]:
        """Get neighboring shade IDs for fallback"""
        return self._neighbors.get(shade_id, [])

    def get_season_universals(self, season: str) -> List[str]:
        """Get universal shade IDs for a given season"""
        universals = {
            "spring": ["found_004", "found_005", "lip_003"],  # light, light-medium, coral
            "summer": ["found_002", "found_004", "lip_002"],  # ivory, light, pink
            "autumn": ["found_005", "found_006", "lip_003"],  # light-medium, medium, coral
            "winter": ["found_001", "found_008", "lip_005"],  # porcelain, deep, berry
        }
        return universals.get(season.lower(), ["found_004", "found_006"])  # neutral fallback

    def save_mappings(self):
        """Save current mappings to files"""
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.shade_map_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.neighbors_path), exist_ok=True)

        # Save shade map
        shade_data = {}
        for key, shade_info in self._shade_map.items():
            shade_data[shade_info.raw_name] = {
                "shade_id": shade_info.shade_id,
                "hex": shade_info.hex_color,
                "undertone": shade_info.undertone,
                "depth": shade_info.depth,
                "finish": shade_info.finish,
            }

        with open(self.shade_map_path, "w", encoding="utf-8") as f:
            json.dump(shade_data, f, indent=2, ensure_ascii=False)

        # Save neighbors
        with open(self.neighbors_path, "w", encoding="utf-8") as f:
            json.dump(self._neighbors, f, indent=2, ensure_ascii=False)

    def add_shade_mapping(
        self,
        raw_name: str,
        shade_id: str,
        hex_color: Optional[str] = None,
        undertone: Optional[str] = None,
        depth: Optional[str] = None,
        finish: Optional[str] = None,
    ):
        """Add a new shade mapping"""
        self._shade_map[raw_name.lower().strip()] = ShadeInfo(
            shade_id=shade_id,
            raw_name=raw_name,
            hex_color=hex_color,
            undertone=undertone,
            depth=depth,
            finish=finish,
        )

    def add_neighbor_relationship(self, shade_id: str, neighbor_ids: List[str]):
        """Add neighbor relationships for a shade"""
        self._neighbors[shade_id] = neighbor_ids


# Global instance
_normalizer = None


def get_shade_normalizer() -> ShadeNormalizer:
    """Get global shade normalizer instance"""
    global _normalizer
    if _normalizer is None:
        _normalizer = ShadeNormalizer()
    return _normalizer


if __name__ == "__main__":
    # Test the normalizer
    normalizer = ShadeNormalizer()

    # Test normalization
    test_shades = ["Ivory", "Light Medium", "unknown shade"]
    for shade in test_shades:
        info = normalizer.normalize_shade(shade)
        print(f"'{shade}' → {info.shade_id} (undertone: {info.undertone})")

    # Test neighbors
    neighbors = normalizer.get_shade_neighbors("found_002")
    print(f"Neighbors of found_002: {neighbors}")

    # Test universals
    universals = normalizer.get_season_universals("spring")
    print(f"Spring universals: {universals}")

    # Save mappings
    normalizer.save_mappings()
    print("Mappings saved!")
