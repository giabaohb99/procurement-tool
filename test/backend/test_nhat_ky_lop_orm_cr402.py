"""Lớp sự kiện ORM ghi giá trị TRƯỚC/SAU — bao-CR-402 (P4 của bao-CR-312).

Bốn luật cứng của `core/change_tracker.py` đều được canh ở đây, vì cả bốn đều
hỏng trong im lặng: gom nhầm bảng của chính mình thì vòng lặp vô hạn, quên gộp
thì một lần nhập liệu đẻ vài chục nghìn dòng, quên che thì chuỗi băm mật khẩu
nằm vĩnh viễn trong một bảng chỉ-thêm, và ghi cả thứ đã quay đầu thì nhật ký kể
lại một thay đổi chưa từng xảy ra.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.3, §6.
"""
import uuid

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.change_tracker import (MAX_DETAIL_CHANGES, MAX_VALUE_LEN, _stringify,
                                     flush_changes)
from app.core.logging_codes import (ACTOR_KIND_SCRIPT, ACTOR_KIND_USER, CHANGE_OP_ADD,
                                    CHANGE_OP_DELETE, CHANGE_OP_UPDATE)
from app.core.request_context import RequestContext, reset_context, set_context
from app.modules.change_log.model import ChangeLog
from app.modules.notification.model import Notification
from app.modules.supplier.model import Supplier
from app.modules.user.model import User


@pytest.fixture
def ctx(db, monkeypatch):
    """Mở một ngữ cảnh thật và trỏ `SessionLocal` vào chính DB của test.

    Không vá `SessionLocal` thì `flush_changes` mở phiên tới MySQL thật — đúng
    thứ mà bộ test SQLite tồn tại để tránh.
    """
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)

    context = RequestContext(request_id=uuid.uuid4().bytes, user_id=7,
                             actor_kind=ACTOR_KIND_USER)
    token = set_context(context)
    try:
        yield context
    finally:
        reset_context(token)


def _make_supplier(db, code="NCC01"):
    supplier = Supplier(code=code, name="Cty A", created_by=1, updated_by=1)
    db.add(supplier)
    db.commit()
    return supplier


# ---------------------------------------------------------------------------
# Không có ngữ cảnh thì cả lớp này tắt
# ---------------------------------------------------------------------------
def test_khong_co_ngu_canh_thi_khong_gom_gi(db):
    """Bộ nghe gắn vào lớp `Session`, nên nó chạy trong MỌI test của kho này.

    Không có `RequestContext` là không có `request_id` để nối và không ai đứng
    ra ghi bộ đệm ở cuối — im lặng bỏ qua là đúng, và đó cũng là thứ giữ cho
    hàng nghìn bài kiểm cũ không đổi hành vi.
    """
    supplier = _make_supplier(db)
    supplier.name = "Cty B"
    db.commit()

    assert flush_changes(None) == 0


# ---------------------------------------------------------------------------
# Sửa: mỗi TRƯỜNG một dòng
# ---------------------------------------------------------------------------
def test_sua_ghi_moi_truong_mot_dong(db, ctx):
    supplier = _make_supplier(db)
    ctx.changes = []

    supplier.name = "Cty B"
    supplier.phone = "0900000000"
    db.commit()

    fields = {e.field: e for e in ctx.changes}
    assert set(fields) == {"name", "phone"}
    assert fields["name"].op == CHANGE_OP_UPDATE
    assert fields["name"].before_value == "Cty A"
    assert fields["name"].after_value == "Cty B"
    assert fields["name"].row_id == supplier.id
    assert fields["name"].table_name == "tab_supplier"


def test_doc_lai_gia_tri_cu_khi_thuoc_tinh_da_het_han(db, ctx):
    """Đi qua một `commit` là mọi cột hết hạn, và giá trị cũ rời khỏi bộ nhớ.

    Không dò ngược xuống DB thì dòng nhật ký chỉ còn nửa câu — "đổi thành Cty
    B", không nói đổi từ đâu — đúng nửa mà BM-005 phải đóng. Bài kiểm này dựng
    lại đúng nhịp đó: tạo, commit (hết hạn), rồi mới sửa.
    """
    supplier = _make_supplier(db)
    ctx.changes = []

    supplier.name = "Cty B"
    db.commit()

    entry = next(e for e in ctx.changes if e.field == "name")
    assert entry.before_value == "Cty A"


def test_doc_lai_gia_tri_cu_khi_ban_ghi_vua_duoc_nap(db, ctx):
    """Luồng thường (nạp -> sửa -> lưu): giá trị cũ có sẵn, không hỏi DB."""
    supplier = _make_supplier(db)
    db.expunge_all()
    ctx.changes = []

    fresh = db.query(Supplier).filter(Supplier.code == "NCC01").one()
    fresh.name = "Cty B"
    db.commit()

    entry = next(e for e in ctx.changes if e.field == "name")
    assert entry.before_value == "Cty A" and entry.after_value == "Cty B"


def test_cham_vao_ban_ghi_ma_khong_doi_gi_thi_khong_ghi(db, ctx):
    """Nằm trong `session.dirty` không có nghĩa là đã đổi — chỉ là đã chạm."""
    supplier = _make_supplier(db)
    ctx.changes = []

    supplier.name = supplier.name
    db.commit()

    assert ctx.changes == []


def test_cot_updated_at_khong_sinh_dong_nhat_ky(db, ctx):
    """`updated_at` đổi theo MÁY ở mọi lần sửa; ghi nó là nhân đôi số dòng."""
    supplier = _make_supplier(db)
    ctx.changes = []

    supplier.name = "Cty B"
    db.commit()

    assert [e.field for e in ctx.changes] == ["name"]


# ---------------------------------------------------------------------------
# Thêm / xóa: chụp cả bản ghi
# ---------------------------------------------------------------------------
def test_them_chup_ban_ghi_va_dien_khoa_chinh_sau_flush(db, ctx):
    """Trước flush bản ghi mới chưa có `id` — `after_flush` mới điền được."""
    supplier = Supplier(code="NCC09", name="Cty M", created_by=1, updated_by=1)
    db.add(supplier)
    db.commit()

    entries = [e for e in ctx.changes if e.table_name == "tab_supplier"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.op == CHANGE_OP_ADD
    assert entry.row_id == supplier.id and entry.row_id > 0
    assert entry.snapshot["code"] == "NCC09"
    assert entry.field == ""
    #  Tham chiếu tạm phải được buông ngay, đừng để nó sống hết lượt gọi.
    assert entry.pending_obj is None


def test_xoa_chup_ban_ghi_truoc_khi_mat(db, ctx):
    supplier = _make_supplier(db)
    ctx.changes = []

    db.delete(supplier)
    db.commit()

    entries = [e for e in ctx.changes if e.table_name == "tab_supplier"]
    assert len(entries) == 1
    assert entries[0].op == CHANGE_OP_DELETE
    assert entries[0].snapshot["name"] == "Cty A"


# ---------------------------------------------------------------------------
# Luật 2 — không bao giờ ghi bảng của chính mình
# ---------------------------------------------------------------------------
def test_bang_trong_no_log_tables_khong_sinh_dong_nao(db, ctx):
    """Thiếu một tên trong `NO_LOG_TABLES` là vòng lặp không có đáy."""
    db.add(Notification(user_id=1, title="Xin chào", body="Nội dung", created_by=1, updated_by=1))
    db.commit()

    assert [e for e in ctx.changes if e.table_name == "tab_notification"] == []


def test_ghi_bo_dem_khong_tu_sinh_bo_dem_moi(db, ctx):
    """`flush_changes` tự ghi `tab_change_log`, và bảng đó cũng bị cấm ghi."""
    supplier = _make_supplier(db)
    ctx.changes = []
    supplier.name = "Cty B"
    db.commit()

    assert flush_changes(ctx) == 1
    assert ctx.changes == []


# ---------------------------------------------------------------------------
# Che dữ liệu nhạy cảm
# ---------------------------------------------------------------------------
def test_che_gia_tri_cot_nhay_cam(db, ctx):
    """Tên cột vẫn ghi, GIÁ TRỊ thì không — biết "mật khẩu đã đổi" là đủ."""
    user = User(email="a@b.c", password_hash="cu", is_active=True, created_by=1, updated_by=1)
    db.add(user)
    db.commit()
    ctx.changes = []

    user.password_hash = "moi"
    db.commit()

    entry = next(e for e in ctx.changes if e.field == "password_hash")
    assert entry.is_masked is True
    assert entry.before_value is None and entry.after_value is None


def test_tab_user_cam_het_tru_cot_duoc_neu_ten(db, ctx):
    """Luật NGƯỢC cho `tab_user`: thêm cột bí mật sau này là tự động an toàn."""
    user = User(email="a@b.c", google_sub="sub-cu", is_active=True, created_by=1, updated_by=1)
    db.add(user)
    db.commit()
    ctx.changes = []

    user.email = "moi@b.c"
    user.google_sub = "sub-moi"
    db.commit()

    fields = {e.field: e for e in ctx.changes}
    #  `email` nằm trong danh sách cho phép — đổi email đăng nhập là đúng loại
    #  việc cần để lại dấu, và nó không phải bí mật.
    assert fields["email"].is_masked is False
    assert fields["email"].after_value == "moi@b.c"
    #  `google_sub` KHÔNG có tên trong danh sách, dù nó không khớp mốc chuỗi nào.
    assert fields["google_sub"].is_masked is True
    assert fields["google_sub"].after_value is None


def test_anh_chup_ban_ghi_cung_bi_che(db, ctx):
    """Chụp cả bản ghi mà quên che là đường vòng dễ quên nhất."""
    db.add(User(email="a@b.c", password_hash="bam", is_active=True, created_by=1, updated_by=1))
    db.commit()

    entry = next(e for e in ctx.changes if e.table_name == "tab_user")
    assert entry.snapshot["password_hash"] == "***"
    assert entry.snapshot["google_sub"] == "***"
    assert entry.snapshot["email"] == "a@b.c"


# ---------------------------------------------------------------------------
# Luật 4 — chỉ ghi thứ đã commit
# ---------------------------------------------------------------------------
def test_quay_dau_thi_vut_bo_dem(db, ctx):
    """Flush rồi rollback là chuyện thường; dấu vết ma tệ hơn không có dấu vết."""
    supplier = _make_supplier(db)
    ctx.changes = []

    supplier.name = "Cty B"
    db.flush()
    assert ctx.changes, "phải gom được trước đã, kẻo bài kiểm này xanh giả"
    db.rollback()

    assert ctx.changes == []


def test_chua_commit_thi_khong_ghi_xuong_bang(db, ctx):
    supplier = _make_supplier(db)
    ctx.changes = []

    supplier.name = "Cty B"
    db.flush()

    assert flush_changes(ctx) == 0
    assert ctx.changes == []


def test_dong_da_commit_song_qua_lan_quay_dau_sau_do(db, ctx):
    """Quay đầu của giao dịch SAU không được xóa dấu vết của giao dịch TRƯỚC."""
    supplier = _make_supplier(db)
    ctx.changes = []

    supplier.name = "Cty B"
    db.commit()
    supplier.phone = "0900000000"
    db.flush()
    db.rollback()

    assert [e.field for e in ctx.changes] == ["name"]


# ---------------------------------------------------------------------------
# Luật 3 — nhập liệu hàng loạt phải gộp
# ---------------------------------------------------------------------------
def test_script_gom_thanh_mot_dong_tong(db, ctx):
    """Tệp khảo sát 2.666 phiếu ghi từng trường là vài chục nghìn dòng."""
    ctx.actor_kind = ACTOR_KIND_SCRIPT

    for i in range(5):
        db.add(Supplier(code=f"NCC1{i}", name=f"Cty {i}", created_by=1, updated_by=1))
    db.commit()

    entries = [e for e in ctx.changes if e.table_name == "tab_supplier"]
    assert len(entries) == 1
    assert entries[0].agg_count == 5
    assert entries[0].op == CHANGE_OP_ADD


def test_dong_gop_ghi_xuong_bang_kem_so_dem(db, ctx):
    ctx.actor_kind = ACTOR_KIND_SCRIPT
    for i in range(3):
        db.add(Supplier(code=f"NCC2{i}", name=f"Cty {i}", created_by=1, updated_by=1))
    db.commit()
    ctx.changes = [e for e in ctx.changes if e.table_name == "tab_supplier"]

    flush_changes(ctx)

    row = db.query(ChangeLog).filter(ChangeLog.table_name == "tab_supplier").one()
    assert row.snapshot_json == {"_aggregated": True, "rows": 3}
    assert row.field == "" and row.row_id == 0


def test_khong_gop_vao_dong_da_dong_dau(db, ctx):
    """Cộng thêm vào một dòng đã commit là sửa lại quá khứ."""
    ctx.actor_kind = ACTOR_KIND_SCRIPT
    db.add(Supplier(code="NCC31", name="Cty 1", created_by=1, updated_by=1))
    db.commit()
    db.add(Supplier(code="NCC32", name="Cty 2", created_by=1, updated_by=1))
    db.commit()

    entries = [e for e in ctx.changes if e.table_name == "tab_supplier"]
    assert len(entries) == 2
    assert [e.agg_count for e in entries] == [1, 1]


def test_cau_chi_gop_cho_nguoi_dung_thuong(db, ctx):
    """Một cú duyệt hàng loạt cũng đủ chạm trần, dù `actor_kind` là người."""
    ctx.changes = [_dummy_detail() for _ in range(MAX_DETAIL_CHANGES)]

    db.add(Supplier(code="NCC41", name="Cty X", created_by=1, updated_by=1))
    db.commit()

    assert ctx.changes[-1].agg_count == 1


def _dummy_detail():
    from app.core.change_tracker import PendingChange

    return PendingChange(table_name="tab_supplier", op=CHANGE_OP_UPDATE, field="name")


# ---------------------------------------------------------------------------
# Ghi xuống bảng
# ---------------------------------------------------------------------------
def test_ghi_du_cot_ngu_canh_xuong_bang(db, ctx):
    ctx.session_id = 42
    supplier = _make_supplier(db)
    ctx.changes = []
    supplier.name = "Cty B"
    db.commit()

    assert flush_changes(ctx) == 1

    row = db.query(ChangeLog).one()
    assert row.request_id == ctx.request_id
    assert row.session_id == 42
    assert row.created_by == 7
    assert row.table_name == "tab_supplier"
    assert row.field == "name"
    assert row.before_value == "Cty A" and row.after_value == "Cty B"
    assert row.op == CHANGE_OP_UPDATE
    assert ctx.change_count == 1


def test_ghi_hong_thi_nuot_loi_chu_khong_lam_sap_luot_goi(db, ctx, monkeypatch):
    """Nhật ký hỏng không được kéo theo nghiệp vụ — nó chỉ là chỗ ghi chép."""
    supplier = _make_supplier(db)
    ctx.changes = []
    supplier.name = "Cty B"
    db.commit()

    def _no(*_args, **_kwargs):
        raise RuntimeError("DB đi vắng")

    monkeypatch.setattr("app.core.database.SessionLocal", _no)

    assert flush_changes(ctx) == 0
    assert ctx.changes == []


def test_dien_nguoc_changed_fields_len_dong_audit(db, ctx):
    """Dòng thời gian của một phiếu cần hiện "Sửa: tên, điện thoại" ngay tại chỗ."""
    from app.modules.audit.model import AuditLog

    supplier = _make_supplier(db)
    db.add(AuditLog(entity="supplier", entity_id=supplier.id, action="update",
                    request_id=ctx.request_id, created_by=7, updated_by=7))
    db.commit()
    ctx.changes = []

    supplier.name = "Cty B"
    supplier.phone = "0900000000"
    db.commit()
    flush_changes(ctx)

    row = db.query(AuditLog).one()
    assert set(row.changed_fields.split(", ")) == {"name", "phone"}
    assert row.change_count == 2


def test_khong_dien_nguoc_khi_khac_request_id(db, ctx):
    """Sai `request_id` mà vẫn điền thì dòng audit mang trường của lượt khác."""
    from app.modules.audit.model import AuditLog

    supplier = _make_supplier(db)
    db.add(AuditLog(entity="supplier", entity_id=supplier.id, action="update",
                    request_id=uuid.uuid4().bytes, created_by=7, updated_by=7))
    db.commit()
    ctx.changes = []

    supplier.name = "Cty B"
    db.commit()
    flush_changes(ctx)

    assert db.query(AuditLog).one().changed_fields == ""


# ---------------------------------------------------------------------------
# Đổi giá trị sang chuỗi
# ---------------------------------------------------------------------------
def test_o_trong_giu_nguyen_none_chu_khong_thanh_chuoi_rong():
    """"Chưa ai nhập" và "bị xóa trắng" là hai chuyện khác nhau."""
    assert _stringify(None) is None
    assert _stringify("") == ""


def test_cat_gia_tri_qua_dai_va_danh_dau():
    text = _stringify("x" * (MAX_VALUE_LEN + 50))

    assert text.endswith("…(cắt)")
    assert len(text) == MAX_VALUE_LEN + len("…(cắt)")


def test_gia_tri_nhi_phan_doi_sang_hex():
    assert _stringify(b"\x01\x02") == "0102"
