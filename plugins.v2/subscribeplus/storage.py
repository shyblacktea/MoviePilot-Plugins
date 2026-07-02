from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class JsonStore:
    def __init__(self, data_dir: Path, max_rule_records: int = 100):
        self.data_dir = Path(data_dir)
        self.max_rule_records = max_rule_records
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.data_dir / name

    def _read(self, name: str, default: Any) -> Any:
        path = self._path(name)
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8") or json.dumps(default))
        except (OSError, json.JSONDecodeError):
            return default

    def _write(self, name: str, value: Any):
        self._path(name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save_scan_results(self, results: List[Dict[str, Any]]):
        self._write("scan_results.json", results)
        self._write("scan_meta.json", {"last_scan_at": datetime.now().isoformat(timespec="seconds")})

    def load_scan_results(self) -> List[Dict[str, Any]]:
        return self._read("scan_results.json", [])

    def load_scan_meta(self) -> Dict[str, Any]:
        return self._read("scan_meta.json", {})

    def clear_scan_results(self):
        for name in ("scan_results.json", "scan_meta.json"):
            try:
                self._path(name).unlink(missing_ok=True)
            except OSError:
                pass

    def append_rule_record(self, record: Dict[str, Any]):
        records = [record] + self.load_rule_records()
        self._write("rule_records.json", records[: self.max_rule_records])

    def load_rule_records(self) -> List[Dict[str, Any]]:
        return self._read("rule_records.json", [])

    def save_interaction(self, token: str, state: Dict[str, Any]):
        states = self._read("interactions.json", {})
        states[token] = state
        self._write("interactions.json", states)

    def load_interaction(self, token: str) -> Optional[Dict[str, Any]]:
        states = self._read("interactions.json", {})
        state = states.get(token)
        if not state:
            return None
        expires_at = state.get("expires_at")
        if expires_at:
            try:
                if datetime.fromisoformat(expires_at) < datetime.now():
                    states.pop(token, None)
                    self._write("interactions.json", states)
                    return None
            except ValueError:
                return None
        return state

    def delete_interaction(self, token: str):
        states = self._read("interactions.json", {})
        states.pop(token, None)
        self._write("interactions.json", states)

    def save_tmdb_cache(self, key: str, value: Dict[str, Any]):
        cache = self._read("tmdb_cache.json", {})
        cache[key] = value
        self._write("tmdb_cache.json", cache)

    def load_tmdb_cache(self, key: str) -> Optional[Dict[str, Any]]:
        return self._read("tmdb_cache.json", {}).get(key)

    def save_ignore(self, key: str):
        ignores = self._read("ignores.json", [])
        if key not in ignores:
            ignores.append(key)
        self._write("ignores.json", ignores)

    def is_ignored(self, key: str) -> bool:
        return key in self._read("ignores.json", [])
