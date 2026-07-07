"""
test_pipeline.py — Pipeline đầy đủ: SR 2 line → auto_assign → option → choose → PR.

Test 1: Pipeline hoàn chỉnh:
  - Tạo SR 2 line (Nhãn + Thùng), auto_assign.
  - Gắn option từ available_survey_lines cho từng line.
  - choose_option cho cả 2.
  - complete_sr → survey_done.
  - create_prs → 1 PR (cùng NCC "NX"), 2 items, amount = qty*price đúng.
  - line.is_completed=True, pr_code set, sr.status="pr_created".
  - finalize_sr → "done".

Test 2 (guards):
  - create_prs khi chưa survey_done → 400.
  - complete_sr khi 1 line chưa có option → 400.
"""
import pytest
from fastapi import HTTPException
from app.modules.survey_request import service as S
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine


def _make_sr_2lines(db, seed):
    """SR ở trạng thái processing với 2 line (Nhãn, Thùng)."""
    sr = SurveyRequest(
        code="YCKS-PIPELINE-001",
        status="processing",
        company_id=seed.company_id,
        requester="Người YC Test",
        request_date="2026-07-07",
        created_by=seed.u_req_id,
        updated_by=seed.u_req_id,
    )
    db.add(sr)
    db.flush()

    ln_nhan = SurveyRequestLine(
        survey_request_id=sr.id,
        item_group="Nhãn",
        requirement_detail="Cần nhãn",
        request_qty=100,
        uom="cuộn",
        proposed_price=5000,
        assignee=seed.emp_nstm_code,
        created_by=seed.u_req_id,
        updated_by=seed.u_req_id,
    )
    ln_thung = SurveyRequestLine(
        survey_request_id=sr.id,
        item_group="Thùng",
        requirement_detail="Cần thùng",
        request_qty=500,
        uom="cái",
        proposed_price=8000,
        assignee=seed.emp_nstm_code,
        created_by=seed.u_req_id,
        updated_by=seed.u_req_id,
    )
    db.add_all([ln_nhan, ln_thung])
    db.flush()
    ln_nhan.internal_line_code = f"YCKSL{ln_nhan.id:06d}"
    ln_thung.internal_line_code = f"YCKSL{ln_thung.id:06d}"
    db.commit()
    return sr, ln_nhan, ln_thung


class TestPipeline:
    def test_full_pipeline(self, db, seed):
        """Pipeline đầy đủ từ SR → PR."""
        sr, ln_nhan, ln_thung = _make_sr_2lines(db, seed)

        # Bước 1: auto_assign (đã có assignee, đếm = 0 vì đã set tay)
        # auto_assign chỉ gán nếu line.assignee rỗng — ở đây đã có nên không đếm
        # Kiểm tra available_survey_lines
        avail_nhan = S.available_survey_lines(db, "NX", "Nhãn")
        avail_thung = S.available_survey_lines(db, "NX", "Thùng")
        assert len(avail_nhan) >= 1
        assert len(avail_thung) >= 1

        # Bước 2: tạo option cho từng line (dùng psl đầu tiên)
        psl_nhan = avail_nhan[0]
        psl_thung = avail_thung[0]
        opt_nhan = S.create_option(db, ln_nhan, psl_nhan.id, seed.u_nstm_id)
        opt_thung = S.create_option(db, ln_thung, psl_thung.id, seed.u_nstm_id)
        assert opt_nhan.public_id == 1
        assert opt_thung.public_id == 1

        # Bước 3: complete_sr (cả 2 line có option)
        sr_done = S.complete_sr(db, sr.id, seed.u_nstm_id)
        assert sr_done.status == "survey_done"

        # Bước 4: choose_option
        S.choose_option(db, ln_nhan.id, opt_nhan.id, seed.u_req_id)
        S.choose_option(db, ln_thung.id, opt_thung.id, seed.u_req_id)

        db.refresh(opt_nhan)
        db.refresh(opt_thung)
        assert opt_nhan.is_chosen is True
        assert opt_thung.is_chosen is True

        # Bước 5: create_prs
        prs = S.create_prs(db, sr.id, seed.u_req_id)

        # Cả 2 line có supplier_code="NX" → 1 PR
        assert len(prs) == 1
        pr = prs[0]
        assert pr.status == "draft"
        assert pr.suggested_supplier == seed.sup_name

        # Kiểm tra items
        from app.modules.purchase_request.model import PurchaseRequestItem
        items = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
        assert len(items) == 2

        # Kiểm tra amount = qty * price
        for item in items:
            expected_amount = float(item.qty) * float(item.price)
            assert abs(float(item.amount) - expected_amount) < 0.01, (
                f"amount không khớp: {float(item.amount)} != {expected_amount}"
            )

        # Kiểm tra line.is_completed, pr_code
        db.refresh(ln_nhan)
        db.refresh(ln_thung)
        assert ln_nhan.is_completed is True
        assert ln_thung.is_completed is True
        assert ln_nhan.pr_code == pr.code
        assert ln_thung.pr_code == pr.code

        # Kiểm tra sr.status
        db.refresh(sr)
        assert sr.status == "pr_created"

        # Bước 6: finalize_sr
        sr_final = S.finalize_sr(db, sr.id, seed.u_req_id)
        assert sr_final.status == "done"

    def test_create_prs_requires_survey_done(self, db, seed):
        """create_prs khi chưa survey_done → HTTPException(400)."""
        sr, ln_nhan, ln_thung = _make_sr_2lines(db, seed)
        # sr đang ở "processing"
        with pytest.raises(HTTPException) as exc_info:
            S.create_prs(db, sr.id, seed.u_req_id)
        assert exc_info.value.status_code == 400

    def test_complete_sr_requires_all_lines_have_options(self, db, seed):
        """complete_sr khi 1 line chưa có option → HTTPException(400)."""
        sr, ln_nhan, ln_thung = _make_sr_2lines(db, seed)
        # Chỉ gắn option cho ln_nhan, không cho ln_thung
        S.create_option(db, ln_nhan, seed.psl_nhan_1_id, seed.u_nstm_id)
        with pytest.raises(HTTPException) as exc_info:
            S.complete_sr(db, sr.id, seed.u_nstm_id)
        assert exc_info.value.status_code == 400

    def test_finalize_requires_pr_created(self, db, seed):
        """finalize_sr khi không ở 'pr_created' → HTTPException(400)."""
        sr, _, _ = _make_sr_2lines(db, seed)
        # sr đang "processing"
        with pytest.raises(HTTPException) as exc_info:
            S.finalize_sr(db, sr.id, seed.u_req_id)
        assert exc_info.value.status_code == 400

    def test_choose_option_deselects_others(self, db, seed):
        """choose_option → chỉ 1 option is_chosen=True, các option khác=False."""
        sr, ln_nhan, _ = _make_sr_2lines(db, seed)
        o1 = S.create_option(db, ln_nhan, seed.psl_nhan_1_id, seed.u_nstm_id)
        o2 = S.create_option(db, ln_nhan, seed.psl_nhan_2_id, seed.u_nstm_id)

        # Chọn o1
        S.choose_option(db, ln_nhan.id, o1.id, seed.u_req_id)
        db.refresh(o1)
        db.refresh(o2)
        assert o1.is_chosen is True
        assert o2.is_chosen is False

        # Đổi sang o2
        S.choose_option(db, ln_nhan.id, o2.id, seed.u_req_id)
        db.refresh(o1)
        db.refresh(o2)
        assert o2.is_chosen is True
        assert o1.is_chosen is False

    def test_create_prs_groups_by_supplier(self, db, seed):
        """2 line cùng NCC → 1 PR với 2 items."""
        sr, ln_nhan, ln_thung = _make_sr_2lines(db, seed)

        avail_nhan = S.available_survey_lines(db, "NX", "Nhãn")
        avail_thung = S.available_survey_lines(db, "NX", "Thùng")
        opt1 = S.create_option(db, ln_nhan, avail_nhan[0].id, seed.u_nstm_id)
        opt2 = S.create_option(db, ln_thung, avail_thung[0].id, seed.u_nstm_id)

        S.complete_sr(db, sr.id, seed.u_nstm_id)
        S.choose_option(db, ln_nhan.id, opt1.id, seed.u_req_id)
        S.choose_option(db, ln_thung.id, opt2.id, seed.u_req_id)

        prs = S.create_prs(db, sr.id, seed.u_req_id)
        assert len(prs) == 1  # 2 lines cùng NCC "NX" → 1 PR

        from app.modules.purchase_request.model import PurchaseRequestItem
        items = db.query(PurchaseRequestItem).filter(
            PurchaseRequestItem.pr_id == prs[0].id
        ).all()
        assert len(items) == 2
