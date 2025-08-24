from __future__ import annotations

from typing import List
from pydantic import ValidationError
from ruamel.yaml import YAML

from .logging_setup import get_catalog_logger
from .models import Product


logger = get_catalog_logger()


def _read_text_with_fallback(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "utf-8-sig", "cp1251", "windows-1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def load_catalog(path: str) -> List[Product]:
    yaml = YAML(typ="rt")
    try:
        text = _read_text_with_fallback(path)
        data = yaml.load(text) or {}
    except FileNotFoundError as e:
        logger.warning(f"Catalog file not found: {path}")
        # Возвращаем пустой список вместо краша
        return []
    except Exception as e:  # noqa: BLE001
        logger.error("catalog_yaml_load_error", extra={"path": path, "error": str(e)})
        return []

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








