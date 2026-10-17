"""Sổ bộ dữ liệu cho AI (ai-CR-210, K12 — tầng T2 doc/erp/21 §5.5). Một cửa: `run(ctx, key, args)`; khai bộ ở `catalog.py`.

Tool `dataset_query` (Trợ lý web / bot / MCP) và `analytics_query` cũ (nay là lớp vỏ của bộ `purchase`) cùng đi qua đây.
"""
from __future__ import annotations

from functools import lru_cache

from .base import MAX_GROUPS, Dataset
from . import base


@lru_cache(maxsize=1)
def registry() -> dict[str, Dataset]:
    from .catalog import build_registry

    return build_registry()


def describe_all() -> list[dict]:
    return [ds.describe() for ds in registry().values()]


def run(ctx, key: str, args: dict) -> dict:
    ds = registry().get(str(key or "").strip().lower())
    if ds is None:
        return {"error": f"Không có bộ dữ liệu {key!r}. Chọn: "
                         + ", ".join(f"{k} ({d.label})" for k, d in registry().items()) + "."}
    return base.run(ctx, ds, args or {})


__all__ = ["MAX_GROUPS", "Dataset", "describe_all", "registry", "run"]
