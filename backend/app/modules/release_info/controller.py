"""`/api/system/version` + `/api/system/release-notes` (bao-CR-722) — ai đăng nhập cũng đọc được, không gác quyền.

Hai đường này chỉ nói "hệ đang chạy bản nào, đợt vừa rồi đổi gì" — không có dữ liệu nghiệp vụ, không có bí mật (mã commit
ngắn và giờ build là thứ ai mở trang Có gì mới cũng thấy). Tiền tố `/api/system` dùng chung với Việc chạy ngầm
(`/api/system/jobs`); không trùng đường.
"""
from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_user
from app.core.response import success

from . import service

router = APIRouter(prefix="/api/system", tags=["system-info"])


@router.get("/version")
def get_version(user=Depends(get_current_user)):
    """Phiên bản đang chạy: mục mới nhất của release_notes.json + commit / giờ build bơm lúc build image + môi trường."""
    return success(service.version_info())


@router.get("/release-notes")
def get_release_notes(limit: int = Query(20, ge=1, le=100), user=Depends(get_current_user)):
    """Các đợt phát hành, mới nhất trước, kèm danh sách phân hệ có trong các mục để màn lọc."""
    releases = service.load_releases()[:limit]
    modules = [m for m in service.MODULES if any(n["module"] == m for r in releases for n in r["notes"])]
    return success({
        "releases": [service.release_payload(r) for r in releases],
        "modules": modules,
        "kinds": [{"code": k, "label": v} for k, v in service.KINDS.items()],
        "version": service.version_info(),
    })
