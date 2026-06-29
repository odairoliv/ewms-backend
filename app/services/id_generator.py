def next_id(prefix: str, count_existing: int) -> str:
    return f"{prefix}-{count_existing + 1:03d}"
