"""
test_auto_assign.py — Kiểm tra resolve_for_group và auto_assign.

Test 1: resolve_for_group("Nhãn") → trả về emp_nstm (primary active).
Test 2: khi primary inactive → fallback về backup.
Test 3: auto_assign đặt đúng line.assignee.
Test 4: auto_assign KHÔNG ghi NSTM ở đầu phiếu (việc khảo sát thuộc về dòng — CR-018).
"""
import pytest
from app.modules.category_assignee.service import resolve_for_group
from app.modules.survey_request import service as S
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.employee.model import Employee


def _make_sr_with_lines(db, seed, item_groups=("Nhãn",)):
    """Tạo SurveyRequest ở trạng thái processing với các line theo item_groups."""
    sr = SurveyRequest(
        code=f"YCKS-ASSIGN-{'-'.join(item_groups)}",
        status="processing",
        company_id=seed.company_id,
        created_by=seed.u_req_id,
        updated_by=seed.u_req_id,
    )
    db.add(sr)
    db.flush()
    for i, ig in enumerate(item_groups):
        ln = SurveyRequestLine(
            survey_request_id=sr.id,
            item_group=ig,
            requirement_detail=f"Test {ig}",
            request_qty=100,
            uom="cái",
            created_by=seed.u_req_id,
            updated_by=seed.u_req_id,
        )
        db.add(ln)
        db.flush()
        ln.internal_line_code = f"YCKSL{ln.id:06d}"
    db.commit()
    return sr


class TestResolveForGroup:
    def test_resolve_returns_primary_when_active(self, db, seed):
        """resolve_for_group('Nhãn') → emp_nstm (primary, is_active=True)."""
        emp = resolve_for_group(db, "Nhãn")
        assert emp is not None
        assert emp.code == seed.emp_nstm_code

    def test_resolve_returns_backup_when_primary_inactive(self, db, seed):
        """Khi primary is_active=False → fallback về backup."""
        # Set primary inactive
        nstm = db.get(Employee, seed.emp_nstm_id)
        nstm.is_active = False
        db.commit()

        emp = resolve_for_group(db, "Nhãn")
        assert emp is not None
        assert emp.code == seed.emp_backup_code

        # Restore
        nstm.is_active = True
        db.commit()

    def test_resolve_unknown_group_returns_none(self, db, seed):
        """resolve_for_group cho phân loại chưa cấu hình → None."""
        emp = resolve_for_group(db, "PhanLoaiKhongTonTai")
        assert emp is None

    def test_resolve_empty_group_returns_none(self, db, seed):
        """resolve_for_group('') → None."""
        emp = resolve_for_group(db, "")
        assert emp is None


class TestAutoAssign:
    def test_auto_assign_sets_line_assignee(self, db, seed):
        """auto_assign → line.assignee = emp_nstm.code."""
        sr = _make_sr_with_lines(db, seed, item_groups=("Nhãn",))
        # Đảm bảo chưa có assignee
        lines = S.lines_of(db, sr.id)
        assert lines[0].assignee == "" or lines[0].assignee is None

        count = S.auto_assign(db, sr)
        assert count == 1

        db.refresh(lines[0])
        assert lines[0].assignee == seed.emp_nstm_code

    def test_auto_assign_khong_ghi_nstm_dau_phieu(self, db, seed):
        """CR-018: phiếu KHÔNG còn trường NSTM ở header — chỉ dòng mới có người phụ trách."""
        sr = _make_sr_with_lines(db, seed, item_groups=("Nhãn",))
        S.auto_assign(db, sr)
        db.refresh(sr)
        assert not hasattr(sr, "assignee_id")

    def test_auto_assign_skips_already_assigned(self, db, seed):
        """Dòng đã có assignee → auto_assign không ghi đè."""
        sr = _make_sr_with_lines(db, seed, item_groups=("Nhãn",))
        lines = S.lines_of(db, sr.id)
        lines[0].assignee = "SOMEONE_ELSE"
        db.commit()

        count = S.auto_assign(db, sr)
        assert count == 0
        db.refresh(lines[0])
        assert lines[0].assignee == "SOMEONE_ELSE"

    def test_auto_assign_multiple_lines(self, db, seed):
        """2 lines (Nhãn + Thùng) → cả 2 được gán nstm."""
        sr = _make_sr_with_lines(db, seed, item_groups=("Nhãn", "Thùng"))
        count = S.auto_assign(db, sr)
        assert count == 2
        for ln in S.lines_of(db, sr.id):
            db.refresh(ln)
            assert ln.assignee == seed.emp_nstm_code

    def test_auto_assign_with_backup_when_primary_inactive(self, db, seed):
        """Khi primary inactive → auto_assign dùng backup."""
        nstm = db.get(Employee, seed.emp_nstm_id)
        nstm.is_active = False
        db.commit()

        sr = _make_sr_with_lines(db, seed, item_groups=("Nhãn",))
        S.auto_assign(db, sr)

        lines = S.lines_of(db, sr.id)
        db.refresh(lines[0])
        assert lines[0].assignee == seed.emp_backup_code

        # Restore
        nstm.is_active = True
        db.commit()
