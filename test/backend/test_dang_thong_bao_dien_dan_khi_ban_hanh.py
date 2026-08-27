"""CR-200 (F12) — ô «Đăng thông báo lên diễn đàn» trong hộp thoại Ban hành.

Chốt với sếp 27/08/2026: «clone thành 1 bài viết bên này là đúng logic hơn» —
diễn đàn chỉ giữ MỘT BẢN SAO thông báo đã ghim (tiêu đề + số hiệu + link),
văn bản gốc vẫn nằm ở Văn thư. Ba thứ phải giữ:

  1. bài clone là bài ĐÃ GHIM, phạm vi toàn tập đoàn, đứng tên người ban hành;
  2. không tích ô thì không có bài nào sinh ra (cờ mặc định TẮT);
  3. diễn đàn hỏng không được kéo đổ việc ban hành — văn bản đã cấp số là xong.
"""
import pytest

from app.core.auth import get_perm_profile
from app.modules.doc_catalog.model import DocType
from app.modules.document import controller, issue_notification, service
from app.modules.document.model import STATUS_EFFECTIVE, Document
from app.modules.document.schema import ApproveIn, DocumentCreate
from app.modules.forum.model import ForumAudience, ForumPost
from app.modules.forum.service import list_pinned_posts
from app.modules.user.model import User


@pytest.fixture()
def issued(db, seed):
    """Một văn bản đã qua submit, sẵn sàng ban hành, người soạn = NSTM."""
    doc_type = DocType(code="TB-DD", name="Thông báo diễn đàn", id_scheme=2, number_when=2)
    db.add(doc_type)
    db.commit()
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id,
        company_id=seed.company_id,
        department_id=seed.dept_id,
        owner_employee_id=seed.emp_nstm_id,
        title="Thông báo nghỉ lễ Quốc khánh 2/9",
        content_html="<p>Nội dung thông báo.</p>",
    ), seed.u_nstm_id)
    service.submit(db, doc, seed.u_nstm_id)
    return doc


def test_clone_thanh_bai_ghim_toan_tap_doan(db, seed, issued):
    user = db.get(User, seed.u_nstm_id)
    service.approve(db, issued, user.id)

    post = issue_notification.create_forum_announcement(db, issued, user)

    assert post.pinned_at is not None                       # bài clone LÀ bài ghim
    assert post.audience == int(ForumAudience.PUBLIC)       # thông báo cho mọi người
    assert post.created_by == user.id                       # đứng tên người ban hành
    assert issued.title in post.body
    assert (issued.doc_code or issued.issue_number) in post.body
    assert f"/document/documents/{issued.id}" in post.body  # link về cửa Văn thư

    # Người KHÁC (không cùng phòng ban gì với người đăng) vẫn thấy trên dải ghim.
    other = db.get(User, seed.u_req_id)
    assert post.id in [p.id for p in list_pinned_posts(db, other, get_perm_profile(db, other))]


def test_khong_tich_o_thi_khong_co_bai(db, seed, issued, cap_quyen):
    """Cờ `forum_announce` mặc định TẮT — đường gọi cũ không lặng lẽ đăng bài."""
    assert ApproveIn().forum_announce is False

    user = db.get(User, seed.u_nstm_id)
    cap_quyen(user.id, "document", read=True, approve=True)
    controller.approve_document(issued.id, ApproveIn(), db=db, user=user)

    assert db.get(Document, issued.id).status == STATUS_EFFECTIVE
    assert db.query(ForumPost).count() == 0


def test_dien_dan_loi_khong_lam_that_bai_viec_ban_hanh(db, seed, issued, cap_quyen, monkeypatch):
    user = db.get(User, seed.u_nstm_id)
    cap_quyen(user.id, "document", read=True, approve=True)

    def fail(*_args):
        raise RuntimeError("Diễn đàn tạm hỏng")

    monkeypatch.setattr(issue_notification, "create_forum_announcement", fail)
    controller.approve_document(issued.id, ApproveIn(forum_announce=True), db=db, user=user)

    assert db.get(Document, issued.id).status == STATUS_EFFECTIVE   # ban hành vẫn xong
    assert db.query(ForumPost).count() == 0


def test_tich_o_qua_controller_thi_co_dung_mot_bai_ghim(db, seed, issued, cap_quyen):
    user = db.get(User, seed.u_nstm_id)
    cap_quyen(user.id, "document", read=True, approve=True)

    controller.approve_document(issued.id, ApproveIn(forum_announce=True), db=db, user=user)

    posts = db.query(ForumPost).all()
    assert len(posts) == 1
    assert posts[0].pinned_at is not None
