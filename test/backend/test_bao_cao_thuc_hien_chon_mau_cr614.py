"""duoc-CR-614 — chọn MẪU khi khởi tạo khối Báo cáo thực hiện.

Mẫu 2 «Tiến độ kế hoạch công việc nhập khẩu» chép file Excel của Phòng Thu mua: 21 việc,
MỘT giai đoạn, mô tả ghi số ngày xử lý, không đặt ngày. Mẫu đã chọn LƯU ở đầu khối: nút
«Tạo mẫu» về sau phải đổ đúng mẫu đó — đổ nhầm mẫu chung vào khối kế hoạch là bày thêm 19
hồ sơ lạ mà người dùng phải xóa tay từng cái.
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.survey_request import report_service as svc
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.survey_request.report_constants import (DEFAULT_PHASES, DEFAULT_TEMPLATE_DOCS,
                                                         IMPORT_PLAN_PHASES, IMPORT_PLAN_TASKS,
                                                         REPORT_TEMPLATES, RT_COMMON,
                                                         RT_IMPORT_PLAN)
from app.modules.survey_request.report_model import ExecReport
from app.modules.survey_request.report_schema import ReportFirstDocIn, ReportInitIn


def _sr(db, code="YCKS-MAU1") -> SurveyRequest:
    s = SurveyRequest(code=code, status="processing")
    db.add(s)
    db.commit()
    s.rid = svc.ensure_report(db, "survey_request", s.id, user_id=1).id
    db.commit()
    return s


def _line(db, sr_id, name) -> SurveyRequestLine:
    ln = SurveyRequestLine(survey_request_id=sr_id, requirement_detail=name)
    db.add(ln)
    db.commit()
    return ln


def _init(db, s, template=RT_COMMON) -> int:
    added = svc.init_report(db, s.rid, svc.survey_request_lines(db, s.id), user_id=1,
                            template=template)
    db.commit()
    return added


def test_mau_ke_hoach_nhap_khau_dung_mot_giai_doan_21_viec_dung_thu_tu_excel(db):
    s = _sr(db)
    assert _init(db, s, RT_IMPORT_PLAN) == 21
    payload = svc.get_report_payload(db, s.rid)
    assert [p["name"] for p in payload["phases"]] == ["Kế hoạch công việc nhập khẩu"]
    titles = [d["title"] for d in payload["docs"]]
    assert titles[0] == "Tìm NCC nước ngoài"
    assert titles[-1] == "Theo dõi thanh toán công nợ"
    assert titles == [title for title, _, _ in IMPORT_PLAN_TASKS]
    #  Đại ca chốt: KHÔNG đặt ngày, số ngày xử lý nằm trong mô tả; đều là hồ sơ CHUNG.
    by_title = {d["title"]: d for d in payload["docs"]}
    assert by_title["Theo dõi thanh toán công nợ"]["description"] == "Thời gian xử lý: 90 ngày"
    assert by_title["Lấy mẫu"]["description"] == "Thời gian xử lý: 0 ngày"
    assert all(d["start_date"] == "" and d["planned_date"] == "" for d in payload["docs"])
    assert all(d["item_id"] == 0 and d["depends"] == [] for d in payload["docs"])
    #  Việc dự phòng không bắt buộc, còn lại bắt buộc.
    assert by_title["Phương án không kịp thời gian"]["required"] is False
    assert sum(d["required"] for d in payload["docs"]) == 20
    assert db.get(ExecReport, s.rid).template == RT_IMPORT_PLAN


def test_mau_excel_khong_lot_khoang_trang_thua_cua_file_goc():
    #  File Excel có tên kèm dấu cách cuối («Lấy mẫu ») và cách đôi giữa chữ — lọt vào là
    #  ô tìm kiếm / so trùng tên của «Tạo mẫu» lệch.
    for title, days, _ in IMPORT_PLAN_TASKS:
        assert title == " ".join(title.split())
        assert days >= 0
    assert len({title.casefold() for title, _, _ in IMPORT_PLAN_TASKS}) == len(IMPORT_PLAN_TASKS)


def test_khong_chon_mau_thi_van_la_mau_chung_nhu_truoc(db):
    s = _sr(db)
    assert _init(db, s) == len(DEFAULT_TEMPLATE_DOCS)
    payload = svc.get_report_payload(db, s.rid)
    assert [p["name"] for p in payload["phases"]] == [name for name, _ in DEFAULT_PHASES]
    assert db.get(ExecReport, s.rid).template == RT_COMMON
    #  Client cũ gửi thân rỗng → mẫu chung.
    assert ReportInitIn().template == RT_COMMON


def test_tao_mau_cho_dong_hang_do_dung_mau_cua_khoi(db):
    s = _sr(db)
    line = _line(db, s.id, "KNO3")
    _init(db, s, RT_IMPORT_PLAN)
    item = next(i for i in svc.get_report_payload(db, s.rid)["items"] if i["line_id"] == line.id)

    added = svc.apply_template(db, s.rid, item_id=item["id"], phase_id=None, user_id=1)
    db.commit()
    assert added == 21                     # 21 việc của mẫu kế hoạch, KHÔNG phải 19 hồ sơ mẫu chung
    payload = svc.get_report_payload(db, s.rid)
    #  Không đẻ thêm 5 giai đoạn của mẫu chung.
    assert [p["name"] for p in payload["phases"]] == [IMPORT_PLAN_PHASES[0][0]]
    #  Bấm lại không nhân đôi.
    assert svc.apply_template(db, s.rid, item_id=item["id"], phase_id=None, user_id=1) == 0


def test_tao_mau_vao_giai_doan_khong_co_trong_mau_cua_khoi_bi_chan(db):
    s = _sr(db)
    _init(db, s, RT_IMPORT_PLAN)
    phase = svc.create_phase(db, s.rid, DEFAULT_PHASES[0][0], "", 1)   # tên của MẪU CHUNG
    db.commit()
    with pytest.raises(HTTPException) as err:
        svc.apply_template(db, s.rid, item_id=0, phase_id=phase.id, user_id=1)
    assert err.value.status_code == 400
    assert "Tiến độ kế hoạch công việc nhập khẩu" in err.value.detail


def test_xoa_roi_khoi_tao_lai_bang_mau_khac_doi_mau_cua_khoi(db):
    s = _sr(db)
    _init(db, s, RT_IMPORT_PLAN)
    svc.delete_all(db, s.rid, user_id=1)
    db.commit()
    assert _init(db, s, RT_COMMON) == len(DEFAULT_TEMPLATE_DOCS)
    assert db.get(ExecReport, s.rid).template == RT_COMMON


def test_hoan_tac_tra_ca_mau_cua_khoi(db):
    s = _sr(db)
    _init(db, s, RT_IMPORT_PLAN)
    svc.delete_all(db, s.rid, user_id=1)
    db.commit()
    #  Xen giữa: «Thêm hồ sơ đầu tiên» dựng khung mẫu chung rồi lại xóa đi.
    svc.create_first_doc(db, s.rid, [], ReportFirstDocIn(title="X", line_id=0, phase_order=0),
                         user_id=1)
    db.commit()
    assert db.get(ExecReport, s.rid).template == RT_COMMON
    svc.delete_all(db, s.rid, user_id=1)
    db.commit()
    #  Hoàn tác lần xóa GẦN NHẤT = khối mẫu chung → mẫu chung.
    svc.restore_latest(db, s.rid, user_id=1)
    db.commit()
    assert db.get(ExecReport, s.rid).template == RT_COMMON


def test_hoan_tac_khoi_ke_hoach_tra_lai_ma_mau_ke_hoach(db):
    s = _sr(db)
    _init(db, s, RT_IMPORT_PLAN)
    svc.delete_all(db, s.rid, user_id=1)
    db.commit()
    db.get(ExecReport, s.rid).template = RT_COMMON      # đầu khối bị đổi trong lúc khối trống
    db.commit()
    svc.restore_latest(db, s.rid, user_id=1)
    db.commit()
    assert db.get(ExecReport, s.rid).template == RT_IMPORT_PLAN


def test_ho_so_dau_tien_ghi_mau_chung_len_dau_khoi(db):
    #  Đầu khối còn mã mẫu kế hoạch của lần khởi tạo đã xóa; «Thêm hồ sơ đầu tiên» dựng khung
    #  5 giai đoạn của MẪU CHUNG → mã phải theo, không thì «Tạo mẫu» đổ nhầm 21 việc.
    s = _sr(db)
    _init(db, s, RT_IMPORT_PLAN)
    svc.delete_all(db, s.rid, user_id=1)
    db.commit()
    svc.create_first_doc(db, s.rid, [], ReportFirstDocIn(title="X", line_id=0, phase_order=1),
                         user_id=1)
    db.commit()
    assert db.get(ExecReport, s.rid).template == RT_COMMON


@pytest.mark.parametrize("bad", [0, 3, -1, 999])
def test_schema_chan_ma_mau_la(bad):
    with pytest.raises(ValidationError):
        ReportInitIn(template=bad)


def test_ma_mau_la_trong_db_roi_ve_mau_chung_thay_vi_vo(db):
    s = _sr(db)
    db.get(ExecReport, s.rid).template = 77      # mẫu đã gỡ khỏi mã nguồn
    db.commit()
    assert svc.template_of(db, s.rid) == RT_COMMON


def test_danh_sach_mau_doc_tu_so_mau():
    templates = svc.list_templates()
    assert [t["id"] for t in templates] == list(REPORT_TEMPLATES)
    plan = next(t for t in templates if t["id"] == RT_IMPORT_PLAN)
    assert plan["name"] == "Tiến độ kế hoạch công việc nhập khẩu"
    assert plan["phase_count"] == 1 and plan["doc_count"] == 21


def test_khoi_da_co_noi_dung_thi_khoi_tao_mau_khac_khong_doi_gi(db):
    s = _sr(db)
    _init(db, s, RT_COMMON)
    assert _init(db, s, RT_IMPORT_PLAN) == -1
    assert db.get(ExecReport, s.rid).template == RT_COMMON
