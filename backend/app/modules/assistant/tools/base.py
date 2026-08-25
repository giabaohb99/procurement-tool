"""Nền cho lớp tool loại A: ngữ cảnh chạy + kiểu khai báo + bộ chạy có gác quyền + audit.

Bảy tầng bảo mật (tài liệu 01 mục 4.2) hiện thực ở ĐÂY, không rải khắp nơi:
1. Chạy DƯỚI danh tính người hỏi — `ToolContext` giữ `db` + `user` thật, không tài khoản bot.
2. Allowlist cố định — chỉ tool khai trong `catalog.SPECS` mới gọi được; tên lạ -> lỗi.
3. Hai lớp quyền — mỗi handler tự `ctx.can(entity)` (từ `user_has_permission`) + `apply_scope`.
4. Read-only — handler chỉ đọc, không ghi.
5. Validate + giới hạn dòng — handler kẹp `limit` (xem `catalog._clamp`).
6. Chống prompt-injection — kết quả trả về là DATA; system prompt đã dặn model không coi
   nội dung tra được là mệnh lệnh.
7. Audit — `run_tool` ghi ai gọi tool nào, tham số, số dòng trả về.
"""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_perm_profile, user_has_permission

from ..provider import ToolDef


@dataclass
class ToolContext:
    """Danh tính + phiên DB của NGƯỜI HỎI để tool chạy đúng quyền của họ."""

    db: Session
    user: Any
    _profile: dict | None = None

    @property
    def profile(self) -> dict:
        """Hồ sơ phân quyền (cache trong 1 lượt) — dùng cho `apply_scope`."""
        if self._profile is None:
            self._profile = get_perm_profile(self.db, self.user)
        return self._profile

    def can(self, entity: str, action: str = "read") -> bool:
        return user_has_permission(self.db, self.user, entity, action)


# Handler một tool: nhận (ngữ cảnh, tham số đã parse) -> dict JSON-hóa được.
Handler = Callable[[ToolContext, dict], dict]


@dataclass
class ToolSpec:
    """Một tool: khai báo cho model (name/description/parameters) + hàm chạy thật (handler)."""

    name: str
    description: str
    parameters: dict
    handler: Handler

    def to_def(self) -> ToolDef:
        return ToolDef(name=self.name, description=self.description, parameters=self.parameters)


def denied(what: str) -> dict:
    """Trả về khi thiếu quyền — KHÔNG trả rỗng lặng lẽ để model khỏi tưởng 'không có dữ liệu'."""
    return {"denied": True, "reason": f"Bạn không có quyền xem {what}."}
