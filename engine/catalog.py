from __future__ import annotations

from typing import List
from pydantic import ValidationError
from ruamel.yaml import YAML

from .logging_setup import get_catalog_logger
from .models import Product


logger = get_catalog_logger()


def load_catalog(path: str) -> List[Product]:
    yaml = YAML(typ="rt")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f) or {}
    items = data.get("products", []) or []
    out: List[Product] = []
    for idx, raw in enumerate(items):
        try:
            out.append(Product.model_validate(raw))
        except ValidationError as e:
            logger.error(
                "catalog_validation_error",
                extra={
                    "payload": {
                        "index": idx,
                        "id": (raw or {}).get("id"),
                        "errors": e.errors(),
                        "raw_brand": (raw or {}).get("brand"),
                        "raw_name": (raw or {}).get("name"),
                        "path": path,
                    }
                },
            )
    return out


