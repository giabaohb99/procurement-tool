"""BỘ LỌC NÂNG CAO của màn *Đơn nghỉ phép* — whitelist `FILTER_OPERATORS`.

Bài này canh đúng một cái bẫy: `apply_filters` **BỎ QUA IM LẶNG** điều kiện của
cột không nằm trong whitelist. Người dùng thêm điều kiện, bấm Áp dụng, danh sách
không đổi — và không có lỗi nào ở đâu cả. Nên bốn cột mà giao diện đang hỏi
(`code · reason · from_date · to_date · total_days`) phải thật sự cắm được vào
mệnh đề WHERE, chứ không phải chỉ có mặt trong danh sách khai ở TypeScript.

⚠️ Chốt thứ hai, quan trọng hơn: **param TRẦN `from_date=` phải KHÔNG bị
`apply_filters` đụng vào.** Ở endpoint này hai tên đó mang nghĩa KHÁC — chúng lọc
theo GIAO NHAU của khoảng cho màn Lịch nghỉ (`to_date >= from_date`), không phải
so từng cột. Ngày nào có người thấy `from_date` trong `FILTER_OPERATORS` rồi tiện
tay thêm nốt vào `FILTERABLE` thì Lịch nghỉ hỏng lặng lẽ: đơn nghỉ vắt từ tuần
trước sang tuần này biến mất khỏi tuần này.

Gọi thẳng hàm lọc chứ không qua HTTP — bài kiểm nhắm vào mệnh đề WHERE sinh ra.
"""
from datetime import date

from starlette.datastructures import QueryParams

from app.core.base_controller import apply_filters
from app.modules.leave import request_service
from app.modules.leave.request_model import LeaveRequest


class _Req:
    """Chỉ cần `query_params`, và phải là `QueryParams` thật (có `multi_items`)."""

    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _don(db, code, *, from_date, to_date, days, reason="", phone=""):
    row = LeaveRequest(code=code, from_date=from_date, to_date=to_date,
                       total_days=days, reason=reason, contact_phone=phone)
    db.add(row)
    db.commit()
    return row


def _loc(db, **params):
    """Đúng đường mà `request_controller.list_requests` đi."""
    query = apply_filters(db.query(LeaveRequest), LeaveRequest, _Req(**params),
                          request_service.FILTERABLE, request_service.FILTER_OPERATORS)
    return sorted(r.code for r in query.all())


def _seed(db):
    _don(db, "NP001", from_date=date(2026, 9, 1), to_date=date(2026, 9, 3),
         days=3, reason="Về quê", phone="0900000001")
    _don(db, "NP002", from_date=date(2026, 9, 10), to_date=date(2026, 9, 10),
         days=1, reason="Việc riêng", phone="0900000002")
    _don(db, "NP012", from_date=date(2026, 10, 8), to_date=date(2026, 10, 8),
         days=0.5, reason="Khám bệnh", phone="0900000003")


def test_loc_theo_SO_DON_bang_toan_tu_chua(db):
    _seed(db)
    assert _loc(db, code__contains="NP01") == ["NP012"]


def test_loc_theo_LY_DO(db):
    #  `reason` không nằm trong whitelist lọc trần (ô tìm nhanh lo), nhưng bộ lọc
    #  nâng cao vẫn phải với tới được — đó là lý do có hai whitelist.
    _seed(db)
    assert _loc(db, reason__contains="quê") == ["NP001"]


def test_loc_theo_KHOANG_NGAY(db):
    _seed(db)
    assert _loc(db, from_date__gte="2026-09-05") == ["NP002", "NP012"]
    assert _loc(db, to_date__lte="2026-09-05") == ["NP001"]


def test_loc_theo_SO_NGAY(db):
    _seed(db)
    assert _loc(db, total_days__gt="1") == ["NP001"]
    #  Nửa ngày phải lọt: cột là số thực, so bằng số chứ không phải chuỗi.
    assert _loc(db, total_days__lt="1") == ["NP012"]


def test_nhieu_dieu_kien_noi_bang_AND(db):
    _seed(db)
    assert _loc(db, from_date__gte="2026-09-01", total_days__gte="1") == ["NP001", "NP002"]


def test_cot_NGOAI_whitelist_bi_bo_qua_im_lang(db):
    #  Ghi lại hành vi thật để người sau khỏi mất buổi chiều: thêm một trường vào
    #  danh sách khai ở TypeScript mà quên `FILTER_OPERATORS` thì điều kiện đó
    #  KHÔNG lọc gì cả — và cũng không báo lỗi.
    _seed(db)
    assert _loc(db, contact_phone__contains="0900000001") == ["NP001", "NP002", "NP012"]


def test_param_TRAN_from_date_khong_bi_dung_toi(db):
    #  ⚠️ Chốt của màn Lịch nghỉ: `from_date=` trần là lọc GIAO NHAU khoảng, do
    #  chính endpoint xử. Thêm nó vào `FILTERABLE` là bài này đỏ.
    _seed(db)
    assert "from_date" not in request_service.FILTERABLE
    assert _loc(db, from_date="2026-09-10") == ["NP001", "NP002", "NP012"]
