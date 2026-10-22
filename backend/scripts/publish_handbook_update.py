# -*- coding: utf-8 -*-
"""Đưa nội dung MỚI của cẩm nang trợ lý (tệp .md hạt giống) lên hệ đang chạy — duoc-CR-670.

Vì sao cần. `ai_skill/handbook_seed.py::ensure_system_handbook` chỉ gieo khi bộ «Cẩm nang hệ thống»
(SYS-HANDBOOK) CHƯA có — có rồi thì KHÔNG đụng gì, đúng luật seed prod không ghi đè. Hệ quả: sửa
`app/modules/ai_skill/seed_handbook/*.md` không bao giờ tới được trợ lý trên DB đang chạy. Script này
là đường chính thống để ra PHIÊN BẢN MỚI: làm đúng việc `service.publish_skill` (chỉ thêm bản mới, đặt làm
bản hiện hành, nháp = bản xuất bản), chỉ khác là chạy từ dòng lệnh nên ghi `published_by = 0` như lúc gieo.

Trợ lý đọc cẩm nang thẳng từ bản xuất bản hiện hành của skill (`assistant/knowledge.py` → tool `read_skill`),
KHÔNG qua kho vector — nên xuất bản xong là lượt hỏi sau đã thấy bản mới, không cần nạp chỉ mục.

Chạy trong container api:
    docker compose exec -T api python scripts/publish_handbook_update.py --dry-run   # xem sẽ làm gì
    docker compose exec -T api python scripts/publish_handbook_update.py            # làm thật

Quy tắc cho từng skill (idempotent — chạy lại lần hai là "đã mới nhất", không sinh phiên bản):
  - nội dung xuất bản hiện hành == tệp                         → bỏ qua (đã mới nhất);
  - khác, và CHƯA ai sửa tay (mọi phiên bản đều do hạt giống `published_by = 0`, nháp == bản xuất bản,
    skill đang «Đang dùng», chưa xóa mềm)                      → tạo phiên bản mới;
  - khác, mà quản trị ĐÃ sửa tay (có phiên bản do người xuất bản, hoặc nháp lệch bản xuất bản, hoặc skill
    đã lưu trữ / xóa)                                          → KHÔNG đè, chỉ báo để người có quyền tự hợp nhất;
  - `--force`: đè cả ca vừa nói (phiên bản cũ vẫn còn trong lịch sử, lùi lại được ở màn Bộ skill).
Bộ SYS-HANDBOOK không tồn tại → không làm gì (để `seed` gieo bản đầu).
"""
import argparse
import logging
import sys
from datetime import datetime

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: F401,E402 — nạp đủ mapper trước khi query
from app.core.audit import record  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.modules.ai_skill.constants import SkillStatus  # noqa: E402
from app.modules.ai_skill.handbook_seed import SET_CODE, seed_files  # noqa: E402
from app.modules.ai_skill.model import AiSkill, AiSkillSet, AiSkillVersion  # noqa: E402

CHANGE_NOTE = "Cập nhật cẩm nang theo tính năng ngày 22/10/2026 (duoc-CR-670)"
SEED_USER_ID = 0  # cùng giá trị lúc gieo: không có người dùng đứng tên
AUDIT_SKILL = "ai_skill"
AUDIT_SET = "ai_skill_set"
log = logging.getLogger("publish_handbook_update")


def why_hand_edited(skill: AiSkill, versions: list[AiSkillVersion], current_body: str) -> str:
    """Lý do (rỗng = chưa ai sửa tay) cho thấy quản trị đã đụng vào skill."""
    if skill.deleted_at is not None:
        return "skill đã bị xóa mềm"
    if skill.status != int(SkillStatus.ACTIVE):
        return "skill không ở trạng thái «Đang dùng»"
    if any(v.published_by != SEED_USER_ID for v in versions):
        return "có phiên bản do quản trị xuất bản"
    if (skill.draft_body_md or "").strip() != current_body:
        return "bản nháp đang lệch bản xuất bản (quản trị đang soạn dở)"
    return ""


def publish_new_version(db, skill: AiSkill, versions: list[AiSkillVersion], body: str, title: str) -> int:
    """Chép `body` thành phiên bản mới — giống `service.publish_skill`, trừ người đứng tên."""
    now = datetime.now()
    version_no = max((v.version_no for v in versions), default=0) + 1
    version = AiSkillVersion(skill_id=skill.id, version_no=version_no, title=title, summary=skill.summary,
                             body_md=body, change_note=CHANGE_NOTE, published_at=now, published_by=SEED_USER_ID)
    db.add(version)
    db.flush()
    skill.draft_body_md = body
    skill.draft_updated_at = now
    skill.title = title
    skill.current_version_id = version.id
    skill.status = int(SkillStatus.ACTIVE)
    return version_no


def main() -> int:
    parser = argparse.ArgumentParser(description="Xuất bản phiên bản mới cho skill cẩm nang khi tệp hạt giống đổi")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ báo sẽ làm gì, không ghi DB")
    parser.add_argument("--force", action="store_true", help="Đè cả skill quản trị đã sửa tay")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        skill_set = (db.query(AiSkillSet).filter(AiSkillSet.code == SET_CODE, AiSkillSet.deleted_at.is_(None)).first())
        if skill_set is None:
            print(f"Chưa có bộ {SET_CODE} trên DB — chạy seed để gieo bản đầu, không cần script này.")
            return 0
        published = skipped = 0
        for slug, title, _summary, body in seed_files():
            skill = db.query(AiSkill).filter(AiSkill.skill_set_id == skill_set.id, AiSkill.slug == slug).first()
            if skill is None:
                print(f"[bỏ qua] {slug}: skill không có trong bộ (quản trị đã xóa hẳn hoặc chưa từng gieo).")
                skipped += 1
                continue
            versions = db.query(AiSkillVersion).filter(AiSkillVersion.skill_id == skill.id).all()
            current = next((v for v in versions if v.id == skill.current_version_id), None)
            current_body = (current.body_md if current else "").strip()
            if current_body == body and skill.deleted_at is None:
                print(f"[đã mới nhất] {slug}: phiên bản hiện hành trùng tệp.")
                continue
            reason = why_hand_edited(skill, versions, current_body)
            if reason and not args.force:
                print(f"[KHÔNG ĐÈ] {slug}: {reason} — tự hợp nhất tay ở màn Bộ skill, hoặc chạy lại với --force.")
                skipped += 1
                continue
            if args.dry_run:
                print(f"[sẽ xuất bản] {slug}: phiên bản {max((v.version_no for v in versions), default=0) + 1}"
                      f" ({len(current_body)} → {len(body)} ký tự){' (--force, đè bản sửa tay)' if reason else ''}.")
                published += 1
                continue
            version_no = publish_new_version(db, skill, versions, body, title)
            db.commit()
            try:
                record(db, SEED_USER_ID, AUDIT_SKILL, skill.id, "approve",
                       f"Xuất bản skill {slug} phiên bản {version_no}: {CHANGE_NOTE}",
                       doc_code=slug, parent=(AUDIT_SET, skill_set.id))
            except Exception:  # nhật ký hỏng không được làm mất phiên bản đã xuất bản
                db.rollback()
                log.warning("Không ghi được nhật ký cho skill %s", slug, exc_info=True)
            print(f"[đã xuất bản] {slug}: phiên bản {version_no}.")
            published += 1
        verb = "sẽ xuất bản" if args.dry_run else "đã xuất bản"
        print(f"Xong: {verb} {published} skill, bỏ qua / không đè {skipped}.")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
