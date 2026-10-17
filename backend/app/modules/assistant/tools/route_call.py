"""Gọi một hàm route FastAPI NGAY TRONG TIẾN TRÌNH, như FastAPI gọi (ai-CR-211; cùng cách `report_summary_tool`).

Không HTTP vòng: dựng `Request` giả mang bộ lọc làm chuỗi truy vấn, `db` của lượt, chạy LẠI đúng các dependency ở tham số
của route (`require(entity, action)` — ném 403 nếu thiếu quyền; `pagination` — lấy `page` / `page_size` từ bộ lọc), tham số
`Query` / `Path` lấy theo tên từ `params`. Trả phần `data` của phong bì `success(...)`.
"""
from __future__ import annotations

import inspect
import json
from typing import Callable
from urllib.parse import urlencode

from fastapi import params as fastapi_params
from pydantic.fields import FieldInfo
from starlette.requests import Request


def fake_request(params: dict) -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": [],
                    "query_string": urlencode({k: v for k, v in params.items() if v is not None}).encode("utf-8")})


def _resolve(fn: Callable, db, user, params: dict, request: Request) -> dict:
    kwargs = {}
    for name, p in inspect.signature(fn).parameters.items():
        default = p.default
        if name == "request":
            kwargs[name] = request
        elif name == "db":
            kwargs[name] = db
        elif name == "user" and not isinstance(default, fastapi_params.Depends):
            kwargs[name] = user
        elif isinstance(default, fastapi_params.Depends):
            dep = default.dependency
            if name == "user" and getattr(dep, "__name__", "") == "get_current_user":
                kwargs[name] = user
            else:
                kwargs[name] = dep(**_resolve(dep, db, user, params, request))
        elif isinstance(default, FieldInfo):
            kwargs[name] = params.get(name, default.default)
        else:
            kwargs[name] = params.get(name, None if default is inspect.Parameter.empty else default)
    return kwargs


def call_route(fn: Callable, db, user, params: dict) -> dict:
    request = fake_request(params)
    resp = fn(**_resolve(fn, db, user, params, request))
    return json.loads(resp.body)["data"]
