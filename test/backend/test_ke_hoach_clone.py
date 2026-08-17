"""KẾ HOẠCH CLONE — khai lúc TẠO văn bản, chạy lúc BAN HÀNH (F06 nhịp đầu).

Kế hoạch tồn tại vì hai sự thật đụng nhau: người soạn biết ngay từ lúc lập văn
bản là nó sẽ tách bản riêng cho những pháp nhân nào, nhưng `create_clones()`
không chạy được lúc đó — văn bản nháp chưa có phiên bản nào đang dùng để chép.

Bốn thứ dưới đây là bốn chỗ tính năng này hỏng âm thầm nếu không canh:
  1. khai được kế hoạch trên văn bản CÒN NHÁP (nếu không thì khối ở form tạo vô nghĩa);
  2. ghi đè chứ không cộng dồn (nếu không thì bỏ tick một nơi là không gỡ ra được);
  3. clone xong thì gỡ khỏi kế hoạch (nếu không thì pháp nhân đó nằm ở cả hai chỗ);
  4. không xếp vào kế hoạch nơi đã có bản clone thật (nếu không thì lần bấm sau
     đâm vào UNIQUE(source, company) và cả đợt clone hỏng theo).
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import clone_service, service
from app.modules.document.schema import DocumentCreate

ACTOR = 1


@pytest.fixture()
def boi_canh(db, seed):
    """Một quy chế CÒN NHÁP của Tập đoàn + hai công ty con."""
    me = db.get(Company, seed.company_id)
    me.issue_code = "DEGO"
    con_a = Company(code="ABA", name="Công ty A", issue_code="ABA", level=2, is_active=True)
    con_b = Company(code="IDA", name="Công ty B", issue_code="IDA", level=2, is_active=True)
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add_all([con_a, con_b, doc_type])
    db.commit()

    nhap = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế bảo mật",
        content_html="<p>Điều 1. Nội dung.</p>",
    ), ACTOR)

    return {"nhap": nhap, "a": con_a, "b": con_b, "doc_type": doc_type, "seed": seed}


def _ban_hanh(db, doc):
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    return doc


# ── 1 · khai được ngay khi văn bản còn nháp ─────────────────────────────────
def test_khai_ke_hoach_duoc_tren_van_ban_con_nhap(db, boi_canh):
    """Đây là toàn bộ lý do kế hoạch tồn tại — clone thật thì không làm được."""
    from datetime import date

    rows = clone_service.set_plan(
        db, boi_canh["nhap"], [boi_canh["a"].id, boi_canh["b"].id],
        date(2026, 9, 30), "Sửa hạn mức ở Điều 5", ACTOR,
    )

    assert {row.company_id for row in rows} == {boi_canh["a"].id, boi_canh["b"].id}
    assert all(row.due_date == date(2026, 9, 30) for row in rows)
    #  Khai kế hoạch KHÔNG được sinh văn bản nào.
    assert clone_service.clones_of(db, boi_canh["nhap"].id) == []


def test_khong_khai_ke_hoach_ve_chinh_phap_nhan_ban_hanh(db, boi_canh):
    with pytest.raises(HTTPException) as loi:
        clone_service.set_plan(
            db, boi_canh["nhap"], [boi_canh["seed"].company_id], None, "", ACTOR)
    assert "chính pháp nhân" in loi.value.detail


def test_khong_khai_ke_hoach_cho_phap_nhan_khong_ton_tai(db, boi_canh):
    with pytest.raises(HTTPException) as loi:
        clone_service.set_plan(db, boi_canh["nhap"], [999999], None, "", ACTOR)
    assert "không tồn tại" in loi.value.detail


# ── 2 · ghi đè, không cộng dồn ──────────────────────────────────────────────
def test_ghi_de_ke_hoach_chu_khong_cong_don(db, boi_canh):
    """Bỏ tick một pháp nhân trên màn hình phải là gỡ nó khỏi kế hoạch.

    Cộng dồn thì không có đường nào bỏ bớt: gửi lại danh sách ngắn hơn mà bảng
    vẫn giữ nguyên dòng cũ.
    """
    clone_service.set_plan(
        db, boi_canh["nhap"], [boi_canh["a"].id, boi_canh["b"].id], None, "", ACTOR)

    rows = clone_service.set_plan(db, boi_canh["nhap"], [boi_canh["b"].id], None, "", ACTOR)

    assert [row.company_id for row in rows] == [boi_canh["b"].id]


def test_ke_hoach_rong_la_huy_ke_hoach(db, boi_canh):
    clone_service.set_plan(db, boi_canh["nhap"], [boi_canh["a"].id], None, "", ACTOR)

    assert clone_service.set_plan(db, boi_canh["nhap"], [], None, "", ACTOR) == []


# ── 3 · clone xong thì gỡ khỏi kế hoạch ─────────────────────────────────────
def test_clone_xong_thi_go_khoi_ke_hoach(db, boi_canh):
    """Để nguyên thì pháp nhân đó vừa "dự kiến" vừa "đã có" — đếm hai lần."""
    clone_service.set_plan(
        db, boi_canh["nhap"], [boi_canh["a"].id, boi_canh["b"].id], None, "", ACTOR)
    goc = _ban_hanh(db, boi_canh["nhap"])

    clone_service.create_clones(db, goc, [boi_canh["a"].id], None, "", ACTOR)

    con_lai = clone_service.plan_for(db, goc.id)
    assert [row.company_id for row in con_lai] == [boi_canh["b"].id]


def test_clone_lay_han_va_ghi_chu_tu_ke_hoach_khi_khong_khai_de(db, boi_canh):
    """Hạn khai từ lúc tạo phải theo sang bản clone, không thì khai để làm gì."""
    from datetime import date

    clone_service.set_plan(
        db, boi_canh["nhap"], [boi_canh["a"].id],
        date(2026, 9, 30), "Giữ nguyên Điều 1–4", ACTOR,
    )
    goc = _ban_hanh(db, boi_canh["nhap"])

    clone = clone_service.create_clones(db, goc, [boi_canh["a"].id], None, "", ACTOR)[0]

    assert clone.clone_due_date == date(2026, 9, 30)
    assert clone.clone_note == "Giữ nguyên Điều 1–4"


def test_han_khai_luc_bam_clone_thang_han_trong_ke_hoach(db, boi_canh):
    from datetime import date

    clone_service.set_plan(
        db, boi_canh["nhap"], [boi_canh["a"].id], date(2026, 9, 30), "cũ", ACTOR)
    goc = _ban_hanh(db, boi_canh["nhap"])

    clone = clone_service.create_clones(
        db, goc, [boi_canh["a"].id], date(2026, 12, 31), "mới", ACTOR)[0]

    assert clone.clone_due_date == date(2026, 12, 31)
    assert clone.clone_note == "mới"


# ── 4 · nơi đã có bản clone thật thì không xếp lại vào kế hoạch ─────────────
def test_khong_xep_lai_phap_nhan_da_co_ban_clone(db, boi_canh):
    """Xếp lại thì lần bấm clone sau đâm vào UNIQUE(source, company)."""
    goc = _ban_hanh(db, boi_canh["nhap"])
    clone_service.create_clones(db, goc, [boi_canh["a"].id], None, "", ACTOR)

    rows = clone_service.set_plan(
        db, goc, [boi_canh["a"].id, boi_canh["b"].id], None, "", ACTOR)

    assert [row.company_id for row in rows] == [boi_canh["b"].id]


# ── Danh sách chờ phải nói rõ nơi nào đã khai ───────────────────────────────
def test_danh_sach_cho_danh_dau_phap_nhan_da_khai_ke_hoach(db, boi_canh):
    """Cờ này là thứ giúp hộp thoại tick sẵn — mất nó thì phải chọn lại từ đầu."""
    clone_service.set_plan(db, boi_canh["nhap"], [boi_canh["a"].id], None, "", ACTOR)
    goc = _ban_hanh(db, boi_canh["nhap"])

    theo_ten = {row["company_name"]: row for row in clone_service.pending_companies(db, goc)}

    assert theo_ten["Công ty A"]["planned"] is True
    assert theo_ten["Công ty B"]["planned"] is False
