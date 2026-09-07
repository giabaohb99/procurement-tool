"""
test_nhat_ky_phuong_an_cr311.py — Dấu vết khi GẮN / GỠ / CHỐT phương án trên YCBG.

Vì sao có tệp này: ngày 07/09/2026 khách báo phiếu YCBG05092603 hiện kết quả khảo sát
của mặt hàng khác. Truy ra được, nhưng phải đọc cột `created_by` trên chính dòng phương
án trong database — vì ba thao tác này KHÔNG ghi một dòng nhật ký nào. Người dùng mở
lịch sử phiếu ra chỉ thấy trống. Bộ test dưới đây canh đúng chỗ đó, đừng xóa.

Ba khẳng định quan trọng nhất, theo thứ tự dễ vỡ:
  * Dấu vết **KHÔNG được chứa tên nhà cung cấp** — nhật ký phiếu đọc bằng
    `survey_request.read`, mà người YÊU CẦU có khóa đó; cả cơ chế phương án sinh ra là
    để giấu NCC với chính họ.
  * Đường ĐỒNG BỘ TỰ ĐỘNG không được ghi dấu vết từng phương án — nó đã ghi một dòng
    `sync_options` tổng kết cả lượt rồi, ghi thêm là ghi đôi.
  * Chốt và bỏ chốt là HAI hành động khác nhau, không phải một.
"""
from app.modules.audit.model import AuditLog
from app.modules.survey_request import service as S
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine


def _logs(db, sr_id, action=None):
    q = db.query(AuditLog).filter(AuditLog.entity == "survey_request",
                                  AuditLog.entity_id == sr_id)
    if action:
        q = q.filter(AuditLog.action == action)
    return q.order_by(AuditLog.id).all()


def _make_line(db, seed, item_group="Nhãn", code="YCKS-LOG"):
    sr = SurveyRequest(code=code, status="processing", company_id=seed.company_id,
                       created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(sr)
    db.flush()
    ln = SurveyRequestLine(survey_request_id=sr.id, item_group=item_group,
                           requirement_detail=f"Test {item_group}", request_qty=100,
                           uom="cái", assignee=seed.emp_nstm_code,
                           created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(ln)
    db.flush()
    ln.internal_line_code = f"YCKSL{ln.id:06d}"
    db.commit()
    return sr, ln


def test_gan_phuong_an_ghi_dau_vet(db, seed):
    sr, ln = _make_line(db, seed, code="YCKS-LOG-1")
    o = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)

    rows = _logs(db, sr.id, "add_option")
    assert len(rows) == 1, "gắn một phương án phải ra đúng một dòng nhật ký"
    assert rows[0].created_by == seed.u_nstm_id, "phải ghi đúng người bấm, không phải 0"
    assert o.display_label in rows[0].message, "phải nêu tên phương án để đối chiếu"
    assert ln.item_group in rows[0].message, "phải nêu dòng nào bị gắn vào"


def test_dau_vet_khong_lo_ten_nha_cung_cap(db, seed):
    """Người YÊU CẦU đọc được nhật ký phiếu. Lộ NCC ở đây là phá luật ẩn NCC."""
    sr, ln = _make_line(db, seed, code="YCKS-LOG-2")
    o = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
    assert o.supplier_name, "seed phải có tên NCC thì khẳng định dưới mới có nghĩa"

    for r in _logs(db, sr.id):
        assert o.supplier_name not in r.message
        assert (o.supplier_code or "@@khong-co@@") not in r.message


def test_go_phuong_an_ghi_dau_vet(db, seed):
    sr, ln = _make_line(db, seed, code="YCKS-LOG-3")
    o = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
    label = o.display_label
    S.delete_option(db, ln.id, o.id, seed.u_nstm_id)

    rows = _logs(db, sr.id, "del_option")
    assert len(rows) == 1
    assert rows[0].created_by == seed.u_nstm_id
    assert label in rows[0].message, "gỡ rồi thì dòng dữ liệu mất, tên phải nằm trong nhật ký"


def test_go_phuong_an_khong_co_nguoi_thi_ghi_he_thong(db, seed):
    """`user_id` mặc định 0 — đường gỡ tự động (hủy duyệt phiếu khảo sát) đi lối này.
    Ghi 0 chứ ĐỪNG gán bừa cho một tài khoản nào đó."""
    sr, ln = _make_line(db, seed, code="YCKS-LOG-4")
    o = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
    S.delete_option(db, ln.id, o.id)

    rows = _logs(db, sr.id, "del_option")
    assert len(rows) == 1 and rows[0].created_by == 0


def test_chot_va_bo_chot_la_hai_hanh_dong(db, seed):
    sr, ln = _make_line(db, seed, code="YCKS-LOG-5")
    o = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)

    S.choose_option(db, ln.id, o.id, seed.u_req_id)
    assert len(_logs(db, sr.id, "choose_option")) == 1
    assert not _logs(db, sr.id, "unchoose_option")

    # Bấm lại đúng phương án đang chọn = BỎ chọn.
    S.choose_option(db, ln.id, o.id, seed.u_req_id)
    assert len(_logs(db, sr.id, "choose_option")) == 1, "bỏ chốt không được ghi thành chốt"
    assert len(_logs(db, sr.id, "unchoose_option")) == 1


def test_dong_bo_tu_dong_khong_ghi_dau_vet_tung_phuong_an(db, seed):
    """`sync_options_from_surveys` đã ghi một dòng `sync_options` tổng kết cả lượt.
    Thêm dấu vết từng phương án nữa là một thao tác hiện hai lần trên dòng thời gian."""
    sr, ln = _make_line(db, seed, code="YCKS-LOG-6")
    S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id, audit=False)
    assert not _logs(db, sr.id, "add_option")


def test_moi_hanh_dong_deu_co_nhan_tieng_viet(db, seed):
    """Thiếu nhãn thì dòng nhật ký hiện mã Anh trần cho người đọc
    («Huỳnh Gia Bảo — add_option: ...»), đúng lỗi đã phải đi vá 971 dòng ngày 05/09."""
    from app.modules.audit.controller import ACTION_LABEL
    for act in ("add_option", "del_option", "choose_option", "unchoose_option"):
        assert ACTION_LABEL.get(act), f"thiếu nhãn tiếng Việt cho hành động {act}"
