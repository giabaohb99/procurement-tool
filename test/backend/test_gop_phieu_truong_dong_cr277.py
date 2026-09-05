"""P6-1 (bao-CR-277) — 6 trường của YCMH mang lên dòng Yêu cầu báo giá (phiếu gộp, doc/erp/12).

Ba thứ cần khóa lại bằng test:

1. Vòng lưu — 4 trường client gửi được (`product_code`/`warehouse`/`required_date`/`vat_pct`)
   phải đi từ `SurveyRequestLineIn` qua `_save_lines` xuống DB rồi quay ra. Pydantic để
   extra='ignore' nên quên khai một trường là dữ liệu mất trong im lặng.
2. `qty_ordered`/`qty_received` CỐ Ý không client-writable — hai cột đó do P6-4 (đồng bộ
   ngược từ ĐMH) ghi. Client gửi lên phải bị nuốt, DB giữ nguyên.
3. `_out_result` (bản trả cho người YC, lọc theo `_LINE_PUBLIC_FIELDS`) phải kèm đủ 6 trường —
   whitelist là cơ chế ẩn NCC nên trường mới không tự lộ ra, quên khai là FE nhận thiếu.
"""
from app.modules.survey_request import service
from app.modules.survey_request.controller import _LINE_PUBLIC_FIELDS, _out_result
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.survey_request.schema import SurveyRequestLineIn

P61 = {
    "product_code": "VT-P6-01",
    "warehouse": "Kho Cần Thơ",
    "required_date": "2026-09-30",
    "vat_pct": 8,
}


def _sr(db, **kw) -> SurveyRequest:
    base = dict(code="YCBG-P61", status="draft")
    base.update(kw)
    s = SurveyRequest(**base)
    db.add(s)
    db.commit()
    return s


def _line_of(db, sid: int) -> SurveyRequestLine:
    return db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sid).one()


def test_bon_truong_moi_luu_va_sua_duoc(db, seed):
    """Tạo mới rồi cập nhật tại chỗ (upsert theo id) — cả hai nhánh của `_save_lines`."""
    s = _sr(db)
    line = SurveyRequestLineIn(item_group="Thùng", request_qty=10, uom="cái", **P61)
    [lid] = service._save_lines(db, s.id, [line], user_id=1)

    ln = _line_of(db, s.id)
    for k, v in P61.items():
        assert getattr(ln, k) == v, f"trường {k} không lưu đúng"

    # Sửa tại chỗ: giữ id, đổi giá trị — phải cập nhật, không đẻ dòng mới.
    line2 = SurveyRequestLineIn(id=lid, item_group="Thùng", request_qty=10, uom="cái",
                                product_code="VT-P6-02", warehouse="Kho HCM",
                                required_date="2026-10-15", vat_pct=10)
    assert service._save_lines(db, s.id, [line2], user_id=1) == [lid]
    ln = _line_of(db, s.id)
    assert (ln.product_code, ln.warehouse) == ("VT-P6-02", "Kho HCM")
    assert (ln.required_date, float(ln.vat_pct)) == ("2026-10-15", 10.0)


def test_qty_ordered_received_khong_cho_client_ghi(db, seed):
    """Hai cột đồng bộ từ ĐMH (P6-4): client gửi kèm phải bị nuốt, DB giữ 0."""
    dump = SurveyRequestLineIn(**P61, qty_ordered=99, qty_received=88).model_dump()
    assert "qty_ordered" not in dump and "qty_received" not in dump

    s = _sr(db)
    service._save_lines(db, s.id, [SurveyRequestLineIn(**P61, qty_ordered=99)], user_id=1)
    ln = _line_of(db, s.id)
    assert float(ln.qty_ordered) == 0 and float(ln.qty_received) == 0


def test_ket_qua_tra_nguoi_yc_co_du_6_truong(db, seed):
    """`_out_result` đi qua whitelist `_LINE_PUBLIC_FIELDS` — 6 trường mới phải có mặt."""
    new_fields = {"product_code", "warehouse", "required_date", "vat_pct",
                  "qty_ordered", "qty_received"}
    assert new_fields <= set(_LINE_PUBLIC_FIELDS)

    s = _sr(db)
    service._save_lines(db, s.id, [SurveyRequestLineIn(item_group="Thùng", **P61)], user_id=1)
    dong = _out_result(db, s)["lines"][0]
    assert dong["product_code"] == "VT-P6-01"
    assert dong["warehouse"] == "Kho Cần Thơ"
    assert dong["required_date"] == "2026-09-30"
    assert float(dong["vat_pct"]) == 8.0
    assert float(dong["qty_ordered"]) == 0 and float(dong["qty_received"]) == 0


def test_dong_cu_mac_dinh_rong_khong_none(db, seed):
    """Dòng lập trước P6-1 không có 6 trường này — đọc ra phải là ''/0, không None (FE format số nổ)."""
    s = _sr(db, code="YCBG-P61-CU")
    db.add(SurveyRequestLine(survey_request_id=s.id, item_group="Dòng cũ"))
    db.commit()

    ln = _line_of(db, s.id)
    assert ln.product_code == "" and ln.warehouse == "" and ln.required_date == ""
    assert float(ln.vat_pct) == 0 and float(ln.qty_ordered) == 0 and float(ln.qty_received) == 0
