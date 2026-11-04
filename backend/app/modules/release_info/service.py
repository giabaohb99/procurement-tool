"""Phiên bản đang chạy + ghi chú phát hành (bao-CR-722).

Nguồn ghi chú: `app/data/release_notes.json` — A1 Điều phối ghi một mục mỗi lần đẩy prod, bằng lời người dùng. Tệp
nằm trong image nên "phiên bản" = mục mới nhất của tệp; mã commit và giờ build do Dockerfile.api bơm qua biến môi
trường `BUILD_COMMIT` / `BUILD_TIME` lúc build (`docker compose build` phải truyền hai build arg này, xem
doc/tai-lieu-ky-thuat/van-hanh/quy-trinh-nhanh-va-deploy.md B.3). Thiếu thì trả rỗng, màn hình ghi "không rõ".

Khuôn tệp được canh bằng `validate_releases` (bài kiểm chạy trên tệp thật) — tệp hỏng thì lúc import module nổ ngay,
không để tới lúc người dùng mở trang mới thấy lỗi.
"""
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.core.config import settings

RELEASE_FILE = Path(__file__).resolve().parents[2] / "data" / "release_notes.json"

#  Nhãn loại thay đổi — màn hình tô màu theo mã, không theo chữ.
KINDS = {"them": "Thêm", "sua": "Sửa", "bo": "Bỏ"}
#  Phân hệ được phép ghi — thêm phân hệ mới thì thêm ở đây (giao diện lọc theo đúng chuỗi này).
MODULES = [
    "Thu mua", "Nhập khẩu", "Kho", "Tra cứu thị trường", "Nhân sự", "Nghỉ phép", "Đặt xe", "Duyệt dấu", "Văn thư",
    "Công việc", "Diễn đàn", "Trợ lý AI", "Báo cáo", "Quản trị", "Nền tảng",
]
#  Đại ca chốt 04/11/2026: phiên bản dạng SỐ 2.X.Y — 2 = ERP v2 (2.0.0 = 11/09/2026), X tăng mỗi đợt prod có tính năng,
#  Y tăng khi đợt chỉ vá lỗi. Ngày phát hành ghi ở `date` của từng mục.
VERSION_RE = re.compile(r"^2\.\d+\.\d+$")   # A1 chốt: luôn bắt đầu bằng 2 (ERP v2)


def version_key(version: str) -> tuple[int, ...]:
    """So phiên bản theo từng số (2.10.0 > 2.9.0), không so chuỗi."""
    return tuple(int(x) for x in version.split("."))


def validate_releases(data: dict) -> list[dict]:
    """Kiểm khuôn rồi trả danh sách đợt, mới nhất trước. Sai chỗ nào nói rõ chỗ đó."""
    releases = data.get("releases")
    if not isinstance(releases, list) or not releases:
        raise ValueError("release_notes.json: thiếu danh sách `releases`")
    seen: set[str] = set()
    for i, rel in enumerate(releases):
        where = f"releases[{i}]"
        version = str(rel.get("version", ""))
        if not VERSION_RE.match(version):
            raise ValueError(f"{where}: version '{version}' phải dạng số 2.X.Y (vd 2.12.0)")
        if version in seen:
            raise ValueError(f"{where}: version '{version}' trùng")
        seen.add(version)
        try:
            date.fromisoformat(str(rel.get("date", "")))
        except ValueError:
            raise ValueError(f"{where}: date phải là YYYY-MM-DD") from None
        if not str(rel.get("title", "")).strip():
            raise ValueError(f"{where}: thiếu title")
        notes = rel.get("notes")
        if not isinstance(notes, list) or not notes:
            raise ValueError(f"{where}: thiếu notes")
        for j, note in enumerate(notes):
            nw = f"{where}.notes[{j}]"
            if note.get("module") not in MODULES:
                raise ValueError(f"{nw}: module '{note.get('module')}' không có trong MODULES")
            if note.get("kind") not in KINDS:
                raise ValueError(f"{nw}: kind phải là một trong {sorted(KINDS)}")
            text = str(note.get("text", "")).strip()
            if not text:
                raise ValueError(f"{nw}: thiếu text")
            if "«" in text or "»" in text:
                raise ValueError(f"{nw}: không dùng ngoặc kép góc")
            if not isinstance(note.get("cr", ""), str):
                raise ValueError(f"{nw}: cr phải là chuỗi (rỗng nếu không có)")
        if not isinstance(rel.get("remarks", []), list):
            raise ValueError(f"{where}: remarks phải là danh sách")
    ordered = sorted(releases, key=lambda r: version_key(r["version"]), reverse=True)
    if [r["version"] for r in ordered] != [r["version"] for r in releases]:
        raise ValueError("release_notes.json: các đợt phải xếp MỚI NHẤT ĐỨNG ĐẦU")
    return releases


@lru_cache(maxsize=1)
def load_releases() -> list[dict]:
    with RELEASE_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return validate_releases(data)


def release_payload(rel: dict) -> dict:
    return {
        "version": rel["version"],
        "date": rel["date"],
        "title": rel["title"],
        "notes": [{"module": n["module"], "kind": n["kind"], "kind_label": KINDS[n["kind"]],
                   "cr": n.get("cr", ""), "text": n["text"]} for n in rel["notes"]],
        "remarks": list(rel.get("remarks", [])),
    }


def environment_label() -> str:
    """`APP_ENV` do compose đặt (prod / dev); không đặt thì suy từ DEV_MODE (máy local)."""
    env = (settings.APP_ENV or "").strip().lower()
    if env:
        return env
    return "local" if settings.DEV_MODE else ""


def version_info() -> dict:
    latest = load_releases()[0]
    return {
        "version": latest["version"],
        "release_date": latest["date"],
        "release_title": latest["title"],
        "commit": (settings.BUILD_COMMIT or "").strip()[:12],
        "built_at": (settings.BUILD_TIME or "").strip(),
        "environment": environment_label(),
    }
