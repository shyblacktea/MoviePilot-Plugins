"""已播进度换算的纯函数（番剧被 TMDB 合并成一季时的分季修正）。

单独成模块是为了可离线单测：插件里的网络/宿主依赖不参与这里的计算。
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple


def aired_max_and_count(episodes: Iterable[dict], today: str) -> Tuple[int, int]:
    """返回一季里 (已播出最大集号, 已播出集数)。

    ``today`` 用 ISO 日期字符串比较，播出日为空或晚于今天的集不算已播。
    """
    numbers = []
    for episode in episodes or []:
        if not isinstance(episode, dict):
            continue
        air_date = str(episode.get("air_date") or "").strip()
        try:
            number = int(episode.get("episode_number") or 0)
        except (TypeError, ValueError):
            continue
        if number > 0 and air_date and air_date <= today:
            numbers.append(number)
    return (max(numbers) if numbers else 0), len(numbers)


def preceding_episode_count(counts: Dict[int, int], season: int) -> int:
    """同一部剧里，目标分季之前各分季的集数之和。"""
    return sum(count for number, count in counts.items() if number < season and count > 0)


def ceiling_from_merged_season(aired_count: int, preceding: int) -> Optional[int]:
    """合并季已播集数减去前置集数，得到目标分季的已播集号。

    ``preceding`` 为 0 说明没有分季依据，返回 None 让调用方回落到旧逻辑。
    """
    if preceding <= 0:
        return None
    if aired_count <= preceding:
        return 0
    return aired_count - preceding
