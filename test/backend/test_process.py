"""
test_process.py — Kiểm tra available_survey_lines, create_option, can_process_line.

Test 1: available_survey_lines("NX", "Nhãn") → trả về line nhãn đã duyệt.
Test 2: thay đổi line_approve → biến mất khỏi danh sách.
Test 3: create_option: public_id tăng 1→2, display_label chứa "Option", supplier_name đúng.
Test 4: gắn trùng psl_id → raise HTTPException 400.
Test 5: can_process_line: primary, backup, người lạ, scope-all.
"""
import pytest
from fastapi import HTTPException
from app.modules.survey_request import service as S
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.survey.model import SurveyProductLine


def _make_processing_line(db, seed, item_group="Nhãn"):
    sr = SurveyRequest(
        code=f"YCKS-PROC-{item_group}",
        status="processing",
        company_id=seed.company_id,
        created_by=seed.u_req_id,
        updated_by=seed.u_req_id,
    )
    db.add(sr)
    db.flush()
    ln = SurveyRequestLine(
        survey_request_id=sr.id,
        item_group=item_group,
        requirement_detail=f"Test {item_group}",
        request_qty=100,
        uom="cái",
        assignee=seed.emp_nstm_code,
        created_by=seed.u_req_id,
        updated_by=seed.u_req_id,
    )
    db.add(ln)
    db.flush()
    ln.internal_line_code = f"YCKSL{ln.id:06d}"
    db.commit()
    return sr, ln


class TestAvailableSurveyLines:
    def test_returns_approved_lines_for_supplier(self, db, seed):
        """available_survey_lines("NX", "Nhãn") → ≥1 dòng."""
        lines, total = S.available_survey_lines(db, "NX", "Nhãn")
        assert total >= 1
        assert len(lines) >= 1
        for ln in lines:
            assert ln.supplier_code == "NX"
            assert ln.line_approve == "Đã duyệt"

    def test_filters_by_item_group(self, db, seed):
        """Lọc theo item_group → không trộn Nhãn với Thùng."""
        nhan_lines, _ = S.available_survey_lines(db, "NX", "Nhãn")
        thung_lines, _ = S.available_survey_lines(db, "NX", "Thùng")
        assert len(nhan_lines) > 0
        assert len(thung_lines) > 0
        nhan_ids = {ln.id for ln in nhan_lines}
        thung_ids = {ln.id for ln in thung_lines}
        assert nhan_ids.isdisjoint(thung_ids), "Nhãn và Thùng không được trộn lẫn"

    def test_unapproved_line_excluded(self, db, seed):
        """Đổi 1 line thành line_approve khác → biến mất khỏi kết quả."""
        before, _ = S.available_survey_lines(db, "NX", "Nhãn")
        assert len(before) >= 2

        # Đổi psl_nhan_2 sang không duyệt
        psl = db.get(SurveyProductLine, seed.psl_nhan_2_id)
        psl.line_approve = "Không duyệt"
        db.commit()

        after, _ = S.available_survey_lines(db, "NX", "Nhãn")
        after_ids = {ln.id for ln in after}
        assert seed.psl_nhan_2_id not in after_ids

        # Restore
        psl.line_approve = "Đã duyệt"
        db.commit()

    def test_no_result_for_unknown_supplier(self, db, seed):
        """NCC không tồn tại → list rỗng."""
        lines, total = S.available_survey_lines(db, "UNKNOWN_SUP", "Nhãn")
        assert lines == []
        assert total == 0

    def test_sort_by_price_asc_desc(self, db, seed):
        """sort_by='price_by_volume' → asc tăng dần, desc giảm dần."""
        asc, _ = S.available_survey_lines(db, "NX", "Nhãn", page_size=100,
                                          sort_by="price_by_volume", sort_dir="asc")
        prices_asc = [float(ln.price_by_volume or 0) for ln in asc]
        assert prices_asc == sorted(prices_asc)

        desc, _ = S.available_survey_lines(db, "NX", "Nhãn", page_size=100,
                                           sort_by="price_by_volume", sort_dir="desc")
        prices_desc = [float(ln.price_by_volume or 0) for ln in desc]
        assert prices_desc == sorted(prices_desc, reverse=True)

    def test_invalid_sort_col_falls_back(self, db, seed):
        """sort_by không hợp lệ → không lỗi, dùng mặc định (id desc)."""
        lines, total = S.available_survey_lines(db, "NX", "Nhãn", page_size=100,
                                                sort_by="drop table; --", sort_dir="asc")
        assert total >= 1
        ids = [ln.id for ln in lines]
        assert ids == sorted(ids, reverse=True)


class TestCreateOption:
    def test_public_id_increments(self, db, seed):
        """Tạo 2 option → public_id = 1 rồi 2."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        o1 = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        o2 = S.create_option(db, ln, seed.psl_nhan_2_id, seed.u_nstm_id)
        assert o1.public_id == 1
        assert o2.public_id == 2

    def test_display_label_contains_option(self, db, seed):
        """display_label phải chứa 'Option'."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        o = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        assert "Option" in o.display_label

    def test_display_label_contains_id(self, db, seed):
        """display_label phải chứa ID của option (format 'Option X — ID Y')."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        o = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        assert str(o.id) in o.display_label

    def test_supplier_name_resolved(self, db, seed):
        """supplier_name phải được resolve từ Supplier.code → Supplier.name."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        o = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        assert o.supplier_name == seed.sup_name

    def test_duplicate_psl_raises_400(self, db, seed):
        """Gắn cùng psl_id lần 2 → HTTPException(400)."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        with pytest.raises(HTTPException) as exc_info:
            S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        assert exc_info.value.status_code == 400

    def test_unapproved_psl_raises_400(self, db, seed):
        """psl.line_approve != 'Đã duyệt' → HTTPException(400)."""
        psl = db.get(SurveyProductLine, seed.psl_nhan_1_id)
        psl.line_approve = "Chờ duyệt"
        db.commit()

        _, ln = _make_processing_line(db, seed, "Nhãn")
        with pytest.raises(HTTPException) as exc_info:
            S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        assert exc_info.value.status_code == 400

        # Restore
        psl.line_approve = "Đã duyệt"
        db.commit()


class TestCanProcessLine:
    def _proc_profile(self, emp_id, emp_code, scope="proc"):
        return {
            "grants": [{"perms": {"survey_request": {"read": True, "scope": scope}}}],
            "employee_id": emp_id,
            "emp_code": emp_code,
        }

    def test_primary_nstm_can_process(self, db, seed):
        """NSTM chính (assignee của line) được phép xử lý."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        # ln.assignee đã được set = emp_nstm_code
        profile = self._proc_profile(seed.emp_nstm_id, seed.emp_nstm_code)
        assert S.can_process_line(db, ln, profile) is True

    def test_backup_nstm_can_process(self, db, seed):
        """NSTM dự phòng (category backup) cũng được phép xử lý dù không phải assignee."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        # backup không phải assignee nhưng là backup của CategoryAssignee
        profile = self._proc_profile(seed.emp_backup_id, seed.emp_backup_code)
        assert S.can_process_line(db, ln, profile) is True

    def test_stranger_cannot_process(self, db, seed):
        """Người không liên quan → không được phép xử lý."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        profile = self._proc_profile(999, "STRANGER")
        assert S.can_process_line(db, ln, profile) is False

    def test_scope_all_can_process_any_line(self, db, seed):
        """scope='all' → được phép xử lý mọi dòng."""
        _, ln = _make_processing_line(db, seed, "Nhãn")
        profile = self._proc_profile(999, "ANYONE", scope="all")
        assert S.can_process_line(db, ln, profile) is True
