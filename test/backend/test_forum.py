"""F0 Diễn đàn — điều kiện đủ của phase (doc/erp/dien-dan/02-lo-trinh-phase.md):
enum trạng thái chừa pending_review (QĐ-D2) + ràng buộc unique like + FILE_POLICY chỉ ảnh.

Chưa có API nào để gọi — F0 chỉ chốt NỀN dữ liệu và các dây đăng ký, nên test
ở đây kiểm đúng ba thứ đó, không hơn.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.file_registry import FILE_POLICY, _IMG, ext_of
from app.modules.forum.model import (ForumAudience, ForumModerationAction,
                                     ForumModerationLog, ForumPost,
                                     ForumPostStatus, ForumReaction)


# ── 1. Enum trạng thái — chốt cứng giá trị vì chúng nằm xuống DB ────────────────

def test_enum_trang_thai_chot_cung_gia_tri():
    """Đổi số của một thành viên IntEnum là đổi NGHĨA của dữ liệu đã lưu —
    chốt cứng ở đây để ai đổi phải sửa test, tức là phải nghĩ đến migration."""
    assert ForumPostStatus.PENDING_REVIEW == 0   # chừa sẵn theo QĐ-D2, đợt 1 chưa dùng
    assert ForumPostStatus.PUBLISHED == 1
    assert ForumPostStatus.HIDDEN == 2
    assert ForumPostStatus.REMOVED == 3

    assert ForumAudience.DEPT == 1
    assert ForumAudience.COMPANY == 2
    assert ForumAudience.PUBLIC == 3

    assert ForumModerationAction.HIDE == 1
    assert ForumModerationAction.REMOVE == 2
    assert ForumModerationAction.RESTORE == 3


def test_bai_moi_mac_dinh_da_dang_va_public(db):
    """QĐ-D1: không duyệt trước — bài tạo ra phải LÊN FEED ngay, không được
    rơi nhầm về pending_review."""
    post = ForumPost(body="Chào cả nhà", created_by=1)
    db.add(post)
    db.flush()
    assert post.status == ForumPostStatus.PUBLISHED
    assert post.audience == ForumAudience.PUBLIC
    assert post.dept_id == 0 and post.company_id == 0   # đóng băng ở service (F1), DB không đoán


# ── 2. Unique like ──────────────────────────────────────────────────────────────

def test_mot_nguoi_chi_like_mot_lan(db):
    """Bấm like hai lần không được ra hai dòng — chống đếm trùng ngay từ DB,
    không trông cậy service."""
    post = ForumPost(body="x", created_by=1)
    db.add(post)
    db.flush()

    db.add(ForumReaction(post_id=post.id, user_id=7))
    db.flush()
    db.add(ForumReaction(post_id=post.id, user_id=7))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_hai_nguoi_khac_nhau_like_duoc_cung_bai(db):
    post = ForumPost(body="x", created_by=1)
    db.add(post)
    db.flush()
    db.add_all([ForumReaction(post_id=post.id, user_id=7),
                ForumReaction(post_id=post.id, user_id=8)])
    db.flush()
    assert db.query(ForumReaction).filter(ForumReaction.post_id == post.id).count() == 2


# ── 3. FILE_POLICY — ảnh + video, trần 50MB ─────────────────────────────────────

def test_file_policy_anh_va_video_50mb():
    """`__self__` = không kiểm RBAC ở tầng đính kèm (người thường không có grant
    `forum_post`) — F1 thêm nhánh kiểm audience riêng, đúng khuôn comment.
    D-Q3 chốt 27/08/2026: video mp4/webm được đăng, trần nâng 10 → 50MB."""
    parent, exts, max_mb = FILE_POLICY["forum_post"]
    assert parent == "__self__"
    assert exts == _IMG | {"mp4", "webm"}
    assert max_mb == 50
    # đuôi tài liệu phải BỊ chặn — diễn đàn không phải chỗ chuyền file in ấn
    for name in ("bao_gia.pdf", "hop_dong.docx", "thiet_ke.cdr"):
        assert ext_of(name) not in exts
    for name in ("anh.jpg", "anh.jpeg", "anh.png", "anh.webp", "clip.mp4", "clip.webm"):
        assert ext_of(name) in exts


# ── 4. Dây phân quyền — forum_admin có, quản lý thu mua KHÔNG tự ăn theo ────────

def test_forum_admin_co_trong_seed_va_pur_manager_khong_dinh():
    """Kiểm duyệt diễn đàn là việc của `forum_admin`, không phải nghiệp vụ thu mua
    — `forum_post` phải nằm trong _SYS_ENTITIES để `pur_manager` không tự có."""
    from app.seed import STD_ROLES, _PUR_MANAGER_PERMS

    perms = STD_ROLES["forum_admin"]["perms"]
    actions, scope = perms["forum_post"]
    assert set(actions) == {"read", "write", "delete"}
    assert scope == "all"
    assert "forum_post" not in _PUR_MANAGER_PERMS
