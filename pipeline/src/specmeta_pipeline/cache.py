from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


class DiskCache:
    def __init__(self, root: Path, ttl: int = 21600) -> None:
        self.root = root
        self.ttl = ttl
        root.mkdir(parents=True, exist_ok=True)

    def _path(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode()).hexdigest()
        return self.root / namespace / f"{digest}.json"

    def get(self, namespace: str, key: str) -> Any | None:
        path = self._path(namespace, key)
        if not path.exists():
            return None
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - float(entry["stored_at"]) > self.ttl:
                return None
            return entry["value"]
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def set(self, namespace: str, key: str, value: Any, etag: str | None = None) -> None:
        path = self._path(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(
            json.dumps({"stored_at": time.time(), "etag": etag, "value": value}, sort_keys=True),
            encoding="utf-8",
        )
        temp.replace(path)

