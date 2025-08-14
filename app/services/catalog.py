import os
from functools import lru_cache
from pathlib import Path
from typing import List

from reco_engine import load_catalog as load_catalog_raw, Product


CANDIDATES = [
    os.getenv("CATALOG_PATH", "").strip(),
    "catalog_user.yaml",
    "catalog_user.json",
    "catalog_user_ga_full.json",
]


def _first_existing_path() -> Path | None:
    for p in [c for c in CANDIDATES if c]:
        pp = Path(p)
        if pp.exists():
            return pp
    return None


@lru_cache(maxsize=1)
def load_catalog_any() -> List[Product]:
    preferred = _first_existing_path()
    items = load_catalog_raw(preferred)  # returns list[dict]
    return [Product.from_dict(d) for d in items]

