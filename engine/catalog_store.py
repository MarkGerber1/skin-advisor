from __future__ import annotations

import os
import threading
from typing import List, Optional, Tuple

from .catalog import load_catalog
from .models import Product


class CatalogStore:
    """Процесс-глобальный кеш каталога (потокобезопасный)."""

    _instance: Optional["CatalogStore"] = None
    _lock = threading.Lock()

    def __init__(self, path: str):
        self.path = path
        self._catalog: List[Product] = []
        self._sig: Optional[Tuple[int, float]] = None
        self._catalog_lock = threading.Lock()

    @classmethod
    def instance(cls, path: str) -> "CatalogStore":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(path)
                cls._instance._load_if_needed(force=True)
            return cls._instance

    def _filesig(self) -> Optional[Tuple[int, float]]:
        try:
            st = os.stat(self.path)
            return (int(st.st_size), float(st.st_mtime))
        except FileNotFoundError:
            return None

    def _load_if_needed(self, force: bool = False) -> None:
        with self._catalog_lock:
            sig = self._filesig()
            if force or (sig and sig != self._sig):
                self._catalog = load_catalog(self.path)
                self._sig = sig

    def get(self) -> List[Product]:
        self._load_if_needed(force=False)
        return self._catalog


