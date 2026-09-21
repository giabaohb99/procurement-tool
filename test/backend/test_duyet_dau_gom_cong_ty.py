"""Màn danh sách Duyệt dấu: danh sách công ty của cả trang phải hỏi MỘT lượt.

Một phiếu đóng dấu gắn nhiều công ty qua bảng nối, nên mỗi dòng danh sách đều cần
một danh sách con. Hỏi từng dòng thì hai mươi dòng là hai mươi lượt vào cơ sở dữ
liệu, hai trăm dòng là hai trăm lượt — đo thật trên bản sao dữ liệu dev: 200 dòng
mất 205 lượt và 129 ms, gom lại còn 6 lượt và 28 ms.

Hai điều phải giữ cùng lúc, và bài kiểm ở đây canh cả hai:

- **Số lượt hỏi không được lớn lên theo số dòng.** Đặt `get_company_ids` vào vòng
  lặp là quay lại đúng chỗ vừa sửa, mà không có gì đỏ lên để báo.
- **Thứ tự công ty phải y như bản hỏi từng phiếu.** Thứ tự đó là thứ tự người lập
  phiếu gõ vào, nó đi thẳng ra ô công ty trên màn hình và ra bản in đưa cho khách;
  gom theo lô mà quên sắp xếp thì cơ sở dữ liệu trả về theo thứ tự nào cũng được.
"""
from types import SimpleNamespace

from sqlalchemy import event

from app.modules.employee.model import Employee
from app.modules.seal_request.schema import SealRequestCreate
from app.modules.seal_request.service import (
    create_seal_request,
    get_company_ids,
    get_company_ids_map,
    serialize_seal_requests,
)

CTY_A, CTY_B, CTY_C, TBP_UID = 11, 22, 33, 500


def _actor(db):
    emp = Employee(code="NV901", full_name="Lâm Bích Dư", email="lbd@dego.vn",
                   phone="0939858582", position="Staff", department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=101, employee_id=emp.id, email="lbd@dego.vn")


def _make(db, actor, company_ids):
    payload = SealRequestCreate(purpose="Duyệt dấu Hợp đồng Hồ Gia - Dego",
                                company_ids=company_ids, first_approver_id=TBP_UID)
    return create_seal_request(db, payload, actor, submit=False)


def _reload(db, reqs):
    """Nạp lại phiếu bằng MỘT câu, y như màn danh sách thật.

    `db.commit()` làm hết hạn mọi bản ghi đang giữ, nên đọc lại thuộc tính đầu
    tiên là mỗi bản ghi một lượt `SELECT ... WHERE id = ?`. Đó là chuyện của bài
    kiểm chứ không phải của màn hình — không nạp lại thì bộ đếm dưới đây đếm
    nhầm lượt hết hạn thành N+1 của mã nguồn.
    """
    from app.modules.seal_request.model import SealRequest
    ids = [r.id for r in reqs]
    rows = db.query(SealRequest).filter(SealRequest.id.in_(ids)).all()
    return sorted(rows, key=lambda r: ids.index(r.id))


def _count_queries(db, fn, *, like: str = ""):
    """Chạy `fn` và đếm số câu lệnh xuống cơ sở dữ liệu; `like` để lọc theo tên bảng.

    Lọc bằng `FROM <bảng>` chứ đừng lọc bằng tên bảng trần: bí danh cột mà
    SQLAlchemy sinh ra có dạng `tab_seal_request_company_id`, tức câu hỏi bảng CHA
    cũng chứa nguyên tên bảng CON.
    """
    counted: list[str] = []

    def _on_exec(conn, cursor, statement, *args):
        if not like or like in statement:
            counted.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", _on_exec)
    try:
        result = fn()
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _on_exec)
    return result, counted


# ══════════════════════════════════════════════════════════════════════════════
#  Gom đúng: cùng dữ liệu ra, cùng thứ tự
# ══════════════════════════════════════════════════════════════════════════════

def test_ban_gom_ra_dung_y_nhu_ban_hoi_tung_phieu(db):
    """Bản gom là bản thay thế, nên nó phải trả về ĐÚNG thứ bản cũ trả về."""
    actor = _actor(db)
    reqs = [_make(db, actor, [CTY_A, CTY_B]),
            _make(db, actor, [CTY_C]),
            _make(db, actor, [CTY_B, CTY_C, CTY_A])]
    db.commit()

    ids_map = get_company_ids_map(db, [r.id for r in reqs])

    assert ids_map == {r.id: get_company_ids(db, r.id) for r in reqs}


def test_thu_tu_cong_ty_GIU_NGUYEN_thu_tu_nguoi_lap_go_vao(db):
    """Thứ tự này ra bản in đưa cho khách. Xáo nó là đổi thứ người dùng nhìn thấy,
    mà chẳng có gì báo lỗi cả — chỉ có người đọc phiếu thấy lạ."""
    actor = _actor(db)
    req = _make(db, actor, [CTY_C, CTY_A, CTY_B])
    db.commit()

    assert get_company_ids_map(db, [req.id])[req.id] == [CTY_C, CTY_A, CTY_B]


def test_phieu_chua_gan_cong_ty_van_co_KHOA_gia_tri_rong(db):
    """Thiếu khóa thì chỗ gọi phải tự đoán: "chưa gắn công ty" hay "quên hỏi phiếu
    này"? Trả khóa rỗng để câu trả lời chỉ có một nghĩa."""
    actor = _actor(db)
    req = _make(db, actor, [])
    db.commit()

    assert get_company_ids_map(db, [req.id]) == {req.id: []}


def test_danh_sach_rong_thi_KHONG_hoi_cau_nao(db):
    """Trang không có dòng nào vẫn đi qua hàm này. `IN ()` là câu hỏi vô nghĩa."""
    _, counted = _count_queries(db, lambda: get_company_ids_map(db, []),
                                like="FROM tab_seal_request_company")

    assert counted == []


# ══════════════════════════════════════════════════════════════════════════════
#  Gom đủ: số lượt hỏi không lớn lên theo số dòng
# ══════════════════════════════════════════════════════════════════════════════

def test_ba_muoi_phieu_van_chi_MOT_luot_hoi_bang_noi(db):
    """Trần CỨNG, không phải số đo tham khảo: một trang bao nhiêu dòng cũng chỉ
    một câu hỏi vào bảng nối."""
    actor = _actor(db)
    reqs = [_make(db, actor, [CTY_A, CTY_B]) for _ in range(30)]
    db.commit()
    reqs = _reload(db, reqs)

    _, counted = _count_queries(db, lambda: serialize_seal_requests(db, reqs),
                                like="FROM tab_seal_request_company")

    assert len(counted) == 1, f"Đã quay lại N+1: {len(counted)} truy vấn cho {len(reqs)} dòng"


def test_them_dong_thi_tong_so_luot_hoi_KHONG_tang(db):
    """Đếm theo tên bảng bắt được lần lười quay lại ở đúng chỗ này, nhưng lần sau
    N+1 có thể mọc ở bảng khác trong cùng hàm. So hai kích cỡ trang thì bắt được cả
    những chỗ đó."""
    actor = _actor(db)
    it = [_make(db, actor, [CTY_A, CTY_B]) for _ in range(12)]
    db.commit()
    it = _reload(db, it)

    _, it_counted = _count_queries(db, lambda: serialize_seal_requests(db, it[:3]))
    _, nhieu_counted = _count_queries(db, lambda: serialize_seal_requests(db, it))

    assert len(nhieu_counted) == len(it_counted), (
        f"3 dòng hết {len(it_counted)} truy vấn, 12 dòng hết {len(nhieu_counted)} — "
        "số lượt hỏi đang lớn lên theo số dòng")


def test_gom_roi_van_du_cong_ty_tren_tung_dong(db):
    """Đếm truy vấn mà không kiểm dữ liệu thì bỏ hết phần nối công ty đi cũng xanh."""
    actor = _actor(db)
    reqs = [_make(db, actor, [CTY_A, CTY_B]), _make(db, actor, [CTY_C])]
    db.commit()

    rows = serialize_seal_requests(db, reqs)

    assert [r["company_ids"] for r in rows] == [[CTY_A, CTY_B], [CTY_C]]
