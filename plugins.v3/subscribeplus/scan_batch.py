from typing import List, Sequence, Tuple, TypeVar


T = TypeVar("T")


def select_scan_batch(items: Sequence[T], limit: int, cursor: int) -> Tuple[List[T], int]:
    values = list(items or [])
    if not values:
        return [], 0

    size = len(values)
    start = max(int(cursor or 0), 0) % size
    batch_size = min(max(int(limit or 0), 1), size)
    batch = [values[(start + offset) % size] for offset in range(batch_size)]
    return batch, (start + batch_size) % size
