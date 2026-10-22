"""Khuôn vào của API đề xuất kế hoạch AI (kh-AI1-3). Ô `plan` là JSON tự do — `service.normalize` mới là chỗ chặn từng ô
(trần chuỗi, trần số dòng, người / loại việc phải còn dùng); ở đây chỉ chặn kích thước tổng để khỏi đọc cả khối khổng lồ."""
import json

from pydantic import BaseModel, Field, field_validator

from app.modules.ai_plan.service import MAX_PLAN_BYTES


def _cap(v):
    if v is not None and len(json.dumps(v, ensure_ascii=False, default=str)) > MAX_PLAN_BYTES:
        raise ValueError(f"kế hoạch quá lớn (tối đa {MAX_PLAN_BYTES // 1000} nghìn ký tự)")
    return v


class PlanEditIn(BaseModel):
    plan: dict

    _size = field_validator("plan")(_cap)


class PlanApproveIn(BaseModel):
    plan: dict | None = None

    _size = field_validator("plan")(_cap)


class PlanRejectIn(BaseModel):
    reason: str = Field("", max_length=500)
