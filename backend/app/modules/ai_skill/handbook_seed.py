"""Bộ skill «Cẩm nang hệ thống» — HẠT GIỐNG từ mã (ai-CR-220, K7 doc/erp/21 §7.2).

Trước K7 trợ lý web / bot nhồi 7 gói `assistant/packs/*.md` vào lời nhắc, còn 11 tệp gốc nhà máy nằm ở
`assistant/knowledge-source/`. Nay kho skill là nơi DUY NHẤT trợ lý đọc cẩm nang (gỡ chồng chéo C1 của doc 21 §2.1): các
tệp đó dời về `seed_handbook/` và chỉ dùng làm hạt giống.

`ensure_system_handbook` chạy ở `seed.py` + `seed_prod.py` (mỗi lần deploy):
  - chưa có bộ mã `SYS-HANDBOOK` → tạo bộ (Đang dùng, mức Mở), 7 skill, xuất bản phiên bản 1, gắn 11 tệp gốc nhà máy làm
    tệp đính kèm của skill nhà máy, gán quyền đọc cho TỪNG pháp nhân đang có;
  - có rồi (kể cả quản trị đã xóa mềm / lưu trữ / sửa nội dung) → KHÔNG đụng gì. Đúng luật seed prod không ghi đè.
Pháp nhân tạo SAU lần gieo phải gán tay ở màn Bộ skill (checklist «thêm pháp nhân», doc/agent-hub/06 §2.5).
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.subject_match import EFFECT_ALLOW, SUBJECT_COMPANY

from .constants import AccessTarget, SecurityLevel, SkillSetStatus, SkillStatus
from .model import AiSkill, AiSkillAccess, AiSkillFile, AiSkillSet, AiSkillVersion

SET_CODE = "SYS-HANDBOOK"
SET_NAME = "Cẩm nang hệ thống"
SET_DESCRIPTION = ("Cẩm nang dùng ERP và quy định công ty cho trợ lý AI. Hạt giống từ mã (ai-CR-220): quản trị sửa thoải mái, "
                   "seed không ghi đè. Gán sẵn cho mọi pháp nhân lúc gieo — pháp nhân tạo sau phải gán tay.")
SEED_DIR = Path(__file__).parent / "seed_handbook"
FACTORY_REFS_DIR = SEED_DIR / "nha-may-references"
CHANGE_NOTE = "Gieo từ gói tri thức cũ của trợ lý (ai-CR-220)"

#  (tệp, slug, tóm tắt KHI NÀO dùng — AI chọn skill bằng chính câu này, tối đa 500 ký tự).
SKILLS: tuple[tuple[str, str, str], ...] = (
    ("10-quy-trinh-thu-mua.md", "quy-trinh-thu-mua",
     "Quy trình thu mua DEGO: YCMH, YCBG, khảo sát giá, đơn mua hàng, nhận hàng, công nợ, đề nghị thanh toán; ai làm bước "
     "nào, trạng thái phiếu nghĩa là gì. Đọc khi được hỏi về mua hàng hay trước khi soạn phiếu mua."),
    ("20-van-thu-van-ban.md", "van-thu-van-ban",
     "Phân hệ Văn thư: soạn, trình duyệt, ban hành, đánh số, lưu trữ văn bản, thư mục và quyền xem. Đọc khi hỏi về văn bản, "
     "công văn, quyết định, tờ trình."),
    ("30-du-an-cong-viec.md", "du-an-cong-viec",
     "Phân hệ Dự án: giao việc, việc cha / con, giai đoạn, kanban, hạn chót, nhắc việc. Đọc khi hỏi về công việc, dự án "
     "hay trước khi soạn việc."),
    ("40-nghi-phep.md", "nghi-phep",
     "Nghỉ phép: loại nghỉ, quỹ phép, nộp đơn, duyệt, hủy đơn. Đọc khi hỏi về nghỉ phép hay trước khi soạn đơn nghỉ."),
    ("50-dat-phong-hop.md", "dat-phong-hop",
     "Đặt phòng họp: xem phòng trống, lập phiếu đặt, gửi duyệt, đổi / hủy. Đọc khi hỏi về phòng họp."),
    ("60-nhan-su-ho-so.md", "nhan-su-ho-so",
     "Hồ sơ nhân sự và danh mục Chức vụ: thông tin nhân viên, ai sửa được gì, hợp đồng lao động. Đọc khi hỏi về hồ sơ nhân sự."),
    ("nhamay-tri-thuc-co-dong.md", "nha-may-he-thong-cong-viec",
     "Hệ thống công việc Nhà máy DEGO Organic: quy định QĐ.HT, giao thức trợ lý AI nhà máy, bộ câu hỏi làm rõ việc, thuật "
     "ngữ, sổ đăng ký công việc, danh mục tài liệu. Đọc khi hỏi về nhà máy, sản xuất, ca làm, cải tiến. Bản gốc chi tiết nằm "
     "ở tệp đính kèm references/."),
)
FACTORY_SLUG = "nha-may-he-thong-cong-viec"


def _title_of(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip().lstrip("#").strip()[:200] or fallback
    return fallback


def seed_files() -> list[tuple[str, str, str, str]]:
    """(slug, tiêu đề, tóm tắt, nội dung) của từng skill hạt giống — tách ra để bài kiểm soi nội dung không cần DB."""
    out = []
    for name, slug, summary in SKILLS:
        body = (SEED_DIR / name).read_text(encoding="utf-8").strip()
        out.append((slug, _title_of(body, slug), summary, body))
    return out


def factory_reference_files() -> list[tuple[str, str]]:
    """(đường dẫn trong skill, nội dung) — 11 tệp gốc nhà máy."""
    return [(f"references/{p.name}", p.read_text(encoding="utf-8"))
            for p in sorted(FACTORY_REFS_DIR.glob("*.md"))]


def ensure_system_handbook(db: Session) -> int:
    """Gieo bộ «Cẩm nang hệ thống» nếu CHƯA từng có (kể cả bản đã xóa mềm). Trả số skill vừa tạo (0 = không đụng)."""
    from app.modules.company.model import Company

    if db.query(AiSkillSet.id).filter(AiSkillSet.code == SET_CODE).first() is not None:
        return 0
    now = datetime.now()
    skill_set = AiSkillSet(code=SET_CODE, name=SET_NAME, description=SET_DESCRIPTION[:500], company_id=0,
                           owner_department_id=0, status=int(SkillSetStatus.ACTIVE),
                           security_level=int(SecurityLevel.OPEN), sort_order=0)
    db.add(skill_set)
    db.flush()
    for order, (slug, title, summary, body) in enumerate(seed_files(), start=1):
        skill = AiSkill(skill_set_id=skill_set.id, slug=slug, title=title, summary=summary[:500],
                        status=int(SkillStatus.ACTIVE), draft_body_md=body, draft_updated_at=now, sort_order=order * 10)
        db.add(skill)
        db.flush()
        version = AiSkillVersion(skill_id=skill.id, version_no=1, title=title, summary=summary[:500], body_md=body,
                                 change_note=CHANGE_NOTE, published_at=now, published_by=0)
        db.add(version)
        db.flush()
        skill.current_version_id = version.id
        if slug == FACTORY_SLUG:
            for path, text in factory_reference_files():
                raw = text.encode("utf-8")
                db.add(AiSkillFile(skill_id=skill.id, path=path, size=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                                   content_text=text))
    for (company_id,) in db.query(Company.id).order_by(Company.id):
        db.add(AiSkillAccess(target_kind=int(AccessTarget.SKILL_SET), target_id=skill_set.id,
                             subject_kind=SUBJECT_COMPANY, subject_id=int(company_id), include_children=True,
                             effect=EFFECT_ALLOW, reason="Gieo sẵn: cẩm nang dùng chung cả công ty (ai-CR-220)"))
    db.commit()
    return len(SKILLS)


__all__ = ["ensure_system_handbook", "seed_files", "factory_reference_files", "SET_CODE", "SKILLS"]
