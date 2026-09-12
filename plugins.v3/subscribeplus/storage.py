from __future__ import annotations

import json
import os
import tempfile
from threading import Lock
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class JsonStore:
    _write_lock = Lock()
    def __init__(self, data_dir: Path, max_rule_records: int = 100):
        self.data_dir = Path(data_dir)
        self.max_rule_records = max_rule_records
        self._read_cache: Dict[str, tuple[int, Any]] = {}
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.data_dir / name

    def _read(self, name: str, default: Any) -> Any:
        path = self._path(name)
        if not path.exists():
            return default
        try:
            mtime_ns = path.stat().st_mtime_ns
            cached = self._read_cache.get(name)
            if cached and cached[0] == mtime_ns:
                return cached[1]
            value = json.loads(path.read_text(encoding="utf-8") or json.dumps(default))
            self._read_cache[name] = (mtime_ns, value)
            return value
        except (OSError, json.JSONDecodeError):
            return default

    def _write(self, name: str, value: Any):
        path = self._path(name)
        payload = json.dumps(value, ensure_ascii=False, indent=2)
        with self._write_lock:
            fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_name, path)
            finally:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass

    def save_scan_results(self, results: List[Dict[str, Any]]):
        for result in results or []:
            if isinstance(result, dict) and not result.get("result_id"):
                result["result_id"] = self._new_record_id()
        self._write("scan_results.json", results)
        self._write("scan_meta.json", {"last_scan_at": datetime.now().isoformat(timespec="seconds")})

    def load_scan_results(self) -> List[Dict[str, Any]]:
        return self._read("scan_results.json", [])

    def replace_scan_results(self, results: List[Dict[str, Any]]):
        """仅覆写诊断结果本身，不刷新最后扫描时间，用于入库后剔除已完成的集。"""
        self._write("scan_results.json", results or [])

    def load_scan_meta(self) -> Dict[str, Any]:
        return self._read("scan_meta.json", {})

    def load_scan_cursor(self) -> int:
        return int(self._read("scan_cursor.json", {}).get("cursor") or 0)

    def save_scan_cursor(self, cursor: int):
        self._write("scan_cursor.json", {"cursor": max(int(cursor or 0), 0)})

    def clear_scan_results(self):
        for name in ("scan_results.json", "scan_meta.json", "scan_cursor.json"):
            try:
                self._path(name).unlink(missing_ok=True)
            except OSError:
                pass

    def append_rule_record(self, record: Dict[str, Any]):
        if not record.get("record_id"):
            record["record_id"] = self._new_record_id()
        records = [record] + self.load_rule_records()
        self._write("rule_records.json", records[: self.max_rule_records])

    def load_rule_records(self) -> List[Dict[str, Any]]:
        return self._read("rule_records.json", [])

    def clear_rule_records(self):
        try:
            self._path("rule_records.json").unlink(missing_ok=True)
        except OSError:
            pass

    def delete_rule_record(self, record_id: str) -> bool:
        records = self.load_rule_records()
        kept = [r for r in records if str(r.get("record_id")) != str(record_id)]
        if len(kept) == len(records):
            return False
        self._write("rule_records.json", kept)
        return True

    def delete_scan_result(self, result_id: str) -> bool:
        results = self.load_scan_results()
        kept = [r for r in results if str(r.get("result_id")) != str(result_id)]
        if len(kept) == len(results):
            return False
        self._write("scan_results.json", kept)
        return True

    @staticmethod
    def _new_record_id() -> str:
        import uuid

        return uuid.uuid4().hex[:12]

    def append_identifier_record(self, record: Dict[str, Any]):
        records = [record] + self.load_identifier_records()
        self._write("identifier_records.json", records[: self.max_rule_records])

    def load_identifier_records(self) -> List[Dict[str, Any]]:
        return self._read("identifier_records.json", [])

    def clear_identifier_records(self):
        try:
            self._path("identifier_records.json").unlink(missing_ok=True)
        except OSError:
            pass

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

    def prune_tmdb_cache(self, retention_days: int = 90) -> int:
        """清理超过保留期限的 TMDB 季集日历缓存记录。"""
        cache = self._read("tmdb_cache.json", {})
        if not isinstance(cache, dict):
            return 0
        cutoff = datetime.now() - timedelta(days=max(0, int(retention_days or 0)))
        removed = 0
        for key in list(cache.keys()):
            payload = cache.get(key)
            updated_at = payload.get("updated_at") if isinstance(payload, dict) else None
            try:
                expired = not updated_at or datetime.fromisoformat(str(updated_at)) < cutoff
            except (TypeError, ValueError):
                expired = True
            if expired:
                cache.pop(key, None)
                removed += 1
        if removed:
            self._write("tmdb_cache.json", cache)
        return removed


    def save_notification_queue(self, items: List[Dict[str, Any]]):
        self._write("notification_queue.json", items or [])

    def load_notification_queue(self) -> List[Dict[str, Any]]:
        return self._read("notification_queue.json", [])

    def pop_notification_queue(self) -> Optional[Dict[str, Any]]:
        queue = self.load_notification_queue()
        if not queue:
            return None
        item = queue.pop(0)
        self.save_notification_queue(queue)
        return item

    def save_snooze(self, key: str, until: str):
        snoozes = self._read("notification_suppressions.json", {})
        snoozes[str(key)] = str(until)
        self._write("notification_suppressions.json", snoozes)

    def is_snoozed(self, key: str) -> bool:
        snoozes = self._read("notification_suppressions.json", {})
        until = snoozes.get(str(key))
        if not until:
            return False
        try:
            if datetime.fromisoformat(until) > datetime.now():
                return True
        except ValueError:
            pass
        snoozes.pop(str(key), None)
        self._write("notification_suppressions.json", snoozes)
        return False

    def save_notification_suppression(self, key: str, until: str):
        """保存一条按期限生效的通知抑制记录。"""
        self.save_snooze(key, until)

    def is_notification_suppressed(self, key: str) -> bool:
        """判断诊断是否仍处于通知抑制期限内。"""
        return self.is_snoozed(key)

    def save_candidate_cache(self, candidate_id: str, payload: Dict[str, Any]):
        """保存候选下载所需的最小字段，用于内存上下文丢失后重建下载。"""
        cache = self._read("candidate_cache.json", {})
        cache[str(candidate_id)] = payload
        self._write("candidate_cache.json", cache)

    def prune_candidate_cache(self, cache_days: Optional[int] = None) -> int:
        """清理过期候选下载缓存，并可按当前配置重新计算缓存期限。

        ``cache_days`` 传入时以缓存记录的 ``cached_at`` 为准动态判断，确保
        用户修改候选下载缓存天数后，TG 下载入口立即采用新期限，而不是继续
        使用旧配置生成的 ``expires_at``。

        :param cache_days: 当前候选下载缓存天数；None 时使用记录自身期限
        :return: 清理的缓存条数
        """
        cache = self._read("candidate_cache.json", {})
        if not isinstance(cache, dict):
            return 0
        days = None if cache_days is None else max(0, int(cache_days or 0))
        now = datetime.now()
        removed = 0
        for key in list(cache.keys()):
            payload = cache.get(key) or {}
            expired = False
            if days is not None:
                cached_at = payload.get("cached_at")
                if days <= 0:
                    expired = True
                elif cached_at:
                    try:
                        expired = datetime.fromisoformat(str(cached_at)) + timedelta(days=days) < now
                    except (TypeError, ValueError):
                        expired = True
                else:
                    expires_at = payload.get("expires_at")
                    try:
                        expired = bool(expires_at and datetime.fromisoformat(str(expires_at)) < now)
                    except (TypeError, ValueError):
                        expired = True
            else:
                expires_at = payload.get("expires_at")
                if expires_at:
                    try:
                        expired = datetime.fromisoformat(str(expires_at)) < now
                    except (TypeError, ValueError):
                        expired = True
            if expired:
                cache.pop(key, None)
                removed += 1
        if removed:
            self._write("candidate_cache.json", cache)
        return removed

    def load_candidate_cache(self, candidate_id: str, cache_days: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """读取候选下载缓存，过期返回 None 并清除。"""
        cache = self._read("candidate_cache.json", {})
        payload = cache.get(str(candidate_id))
        if not payload:
            return None
        now = datetime.now()
        days = None if cache_days is None else max(0, int(cache_days or 0))
        expired = False
        if days is not None and days <= 0:
            expired = True
        elif days is not None and payload.get("cached_at"):
            try:
                expired = datetime.fromisoformat(str(payload["cached_at"])) + timedelta(days=days) < now
            except (TypeError, ValueError):
                expired = True
        else:
            expires_at = payload.get("expires_at")
            if expires_at:
                try:
                    expired = datetime.fromisoformat(str(expires_at)) < now
                except (TypeError, ValueError):
                    expired = True
        if expired:
            try:
                cache.pop(str(candidate_id), None)
                self._write("candidate_cache.json", cache)
            except OSError:
                pass
            return None
        return payload
