"""bao-CR-580 — xóa YCMH sinh từ YCBG thì YCBG gỡ liên kết tới nó.

Đại ca báo 03/10/2026: «trên yêu cầu báo giá, tôi tạo ra YCMH, nhưng YCMH này tôi xóa đi
rồi mà vẫn còn hiển thị ra». Nguyên nhân: `delete_pr` chỉ đặt `is_deleted`, còn dây nối
`tab_survey_request_pr` cùng dấu trên dòng YCBG (`pr_id` / `pr_code` / `is_completed`) giữ
nguyên — YCBG vẫn bày YCMH đã xóa, vẫn đứng ở «Đã tạo YCMH», vẫn khóa chuyển phòng / trả
về, và việc tự hoàn thành YCBG vẫn chờ cả phiếu đã xóa.
"""
from app.modules.audit.model import AuditLog
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request import service as sr_service
from app.modules.survey_request.controller import _out_result
from app.modules.survey_request.model import (LS_COMPLETED, SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption, SurveyRequestPr)


def _ycbg(db, seed, *, status="survey_done", lines=1):
    s = SurveyRequest(code="YCBG-CR580", company_id=seed.company_id, requester="Người YC",
                      requester_id=seed.emp_req_id, department="Phòng Test",
                      department_id=seed.dept_id, request_date="2026-10-05", status=status,
                      created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(s)
    db.flush()
    out = []
    for i in range(lines):
        ln = SurveyRequestLine(survey_request_id=s.id, item_group="Nhãn", request_qty=10, uom="cuộn",
                               requirement_detail=f"Nhãn decal {i + 1}", assignee=seed.emp_nstm_code,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id)
        db.add(ln)
        db.flush()
        out.append(ln)
    db.commit()
    return s, out


def _choose(db, ln, supplier="NCC-A"):
    o = SurveyRequestOption(survey_request_line_id=ln.id, public_id=1, display_label="Option 1",
                            is_chosen=True, supplier_code=supplier, supplier_name=f"Công ty {supplier}",
                            snap_product_name="Nhãn decal", snap_quote_unit="cuộn",
                            snap_price_by_volume=1000, created_by=0, updated_by=0)
    db.add(o)
    db.commit()
    return o


def _make_pr(db, seed, s, ln):
    _choose(db, ln)
    (pr,) = sr_service.create_prs(db, s.id, seed.u_req_id)
    return pr


def _ycmh_shown(db, s):
    detail = _out_result(db, s)
    return [y["code"] for line in detail["lines"] for o in line["options"] for y in o["ycmh_list"]]


def _links(db, s):
    return db.query(SurveyRequestPr).filter(SurveyRequestPr.survey_request_id == s.id).all()


def test_deleting_the_only_pr_unlinks_it_and_rolls_the_ycbg_back(db, seed):
    s, (ln,) = _ycbg(db, seed)
    pr = _make_pr(db, seed, s, ln)
    db.refresh(s)
    assert s.status == "pr_created" and _links(db, s)
    assert _ycmh_shown(db, s) == [pr.code]

    pr_service.delete_pr(db, pr.id, seed.u_req_id)

    db.refresh(s)
    db.refresh(ln)
    assert _links(db, s) == []
    assert (ln.pr_id, ln.pr_code, ln.is_completed) == (0, "", False)
    assert s.status == "survey_done"
    # Màn chi tiết YCBG không còn bày YCMH đã xóa ở phương án.
    assert _ycmh_shown(db, s) == []
    # YCBG có dòng lịch sử nói rõ vì sao mất liên kết.
    log = (db.query(AuditLog).filter(AuditLog.entity == "survey_request", AuditLog.entity_id == s.id,
                                     AuditLog.action == "pr_unlinked").one())
    assert pr.code in log.message


def test_processing_ycbg_can_be_transferred_again_once_its_pr_is_deleted(db, seed):
    # Phiếu còn «Đang xử lý» mà đã mua trước vài dòng: dòng mang cờ đã sinh YCMH nên chuyển
    # phòng / trả về bị khóa. YCMH đó xóa đi thì khóa phải mở lại.
    s, (ln,) = _ycbg(db, seed, status="processing")
    pr = _make_pr(db, seed, s, ln)
    assert sr_service.can_transfer_dept(db, s) is False

    pr_service.delete_pr(db, pr.id, seed.u_req_id)

    db.refresh(s)
    assert s.status == "processing"
    assert sr_service.can_transfer_dept(db, s) is True


def test_rebuy_keeps_the_older_pr_and_the_ycbg_stays_pr_created(db, seed):
    s, (ln,) = _ycbg(db, seed)
    first = _make_pr(db, seed, s, ln)
    second = _make_pr(db, seed, s, ln)  # mua lại cùng dòng
    db.refresh(ln)
    assert ln.pr_code == second.code

    pr_service.delete_pr(db, second.id, seed.u_req_id)

    db.refresh(s)
    db.refresh(ln)
    assert [lk.pr_id for lk in _links(db, s)] == [first.id]
    assert (ln.pr_id, ln.pr_code, ln.is_completed) == (first.id, first.code, True)
    assert s.status == "pr_created"


def test_deleting_an_older_pr_leaves_the_line_on_the_newer_one(db, seed):
    s, (ln,) = _ycbg(db, seed)
    first = _make_pr(db, seed, s, ln)
    second = _make_pr(db, seed, s, ln)

    pr_service.delete_pr(db, first.id, seed.u_req_id)

    db.refresh(ln)
    assert (ln.pr_id, ln.pr_code) == (second.id, second.code)
    assert [lk.pr_id for lk in _links(db, s)] == [second.id]


def test_a_line_the_requester_marked_completed_stays_completed(db, seed):
    s, (ln,) = _ycbg(db, seed)
    pr = _make_pr(db, seed, s, ln)
    ln.line_status = LS_COMPLETED
    db.commit()

    pr_service.delete_pr(db, pr.id, seed.u_req_id)

    db.refresh(ln)
    assert ln.pr_code == "" and ln.is_completed is True


def test_only_lines_of_the_deleted_pr_change(db, seed):
    s, (a, b) = _ycbg(db, seed, lines=2)
    _choose(db, a, "NCC-A")
    _choose(db, b, "NCC-B")
    pr_a, pr_b = sorted(sr_service.create_prs(db, s.id, seed.u_req_id), key=lambda p: p.id)

    pr_service.delete_pr(db, pr_a.id, seed.u_req_id)

    db.refresh(a)
    db.refresh(b)
    db.refresh(s)
    assert a.pr_code == "" and b.pr_code == pr_b.code
    assert s.status == "pr_created"


def test_a_finished_ycbg_is_not_reopened(db, seed):
    s, (ln,) = _ycbg(db, seed)
    pr = _make_pr(db, seed, s, ln)
    s.status = "done"
    db.commit()

    pr_service.delete_pr(db, pr.id, seed.u_req_id)

    db.refresh(s)
    assert s.status == "done" and _links(db, s) == []


def test_ycbg_auto_completes_when_the_only_open_pr_left_is_deleted(db, seed):
    # Luật cũ (auto_complete_from_pr): mọi YCMH liên quan đã hoàn thành thì YCBG tự hoàn
    # thành. Phiếu nháp còn treo bị xóa thì phần còn lại đã đủ điều kiện đó.
    s, (a, b) = _ycbg(db, seed, lines=2)
    _choose(db, a, "NCC-A")
    _choose(db, b, "NCC-B")
    pr_a, pr_b = sorted(sr_service.create_prs(db, s.id, seed.u_req_id), key=lambda p: p.id)
    pr_a.status = "completed"
    db.commit()

    pr_service.delete_pr(db, pr_b.id, seed.u_req_id)

    db.refresh(s)
    assert s.status == "done"


def test_a_pr_typed_by_hand_deletes_as_before(db, seed):
    pr = PurchaseRequest(code="PYC-TAY-580", company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test", status="draft",
                         request_date="2026-10-05", created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.commit()
    pr_service.delete_pr(db, pr.id, seed.u_req_id)
    db.refresh(pr)
    assert pr.is_deleted is True


def test_cleanup_unlinks_prs_deleted_before_the_fix(db, seed):
    # Dữ liệu cũ: YCMH đã xóa mềm TRƯỚC bản vá vẫn còn dây nối — dọn một lượt.
    s, (ln,) = _ycbg(db, seed)
    pr = _make_pr(db, seed, s, ln)
    pr.is_deleted = True
    db.commit()

    assert sr_service.unlink_deleted_prs(db, seed.u_req_id) == [pr.code]
    assert sr_service.unlink_deleted_prs(db, seed.u_req_id) == []  # chạy lại không đổi gì

    db.refresh(s)
    db.refresh(ln)
    assert _links(db, s) == [] and ln.pr_code == "" and s.status == "survey_done"
