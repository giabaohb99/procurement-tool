"""
test_ncc_hiding.py — Kiểm tra serializer ẩn NCC và is_purchaser.

Test 1: _out_result → options chỉ chứa whitelist field, KHÔNG có supplier_*,
         snap_internal_code, nstm_note, product_survey_line_id.
Test 2: is_purchaser với các profile khác nhau.
"""
import pytest
from app.modules.survey_request import service as S
from app.modules.survey_request import controller as C
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine


# ── Các field bị cấm trong option trả về người YC ──────────────────────────────
BANNED_FIELDS = [
    "supplier_code",
    "supplier_name",
    "supplier_survey_id",
    "snap_internal_code",
    "nstm_note",
    "product_survey_line_id",
]
REQUIRED_FIELDS = [
    "snap_product_name",
    "snap_price_by_volume",
    "is_chosen",
    "public_id",
    "display_label",
]


def _make_sr(db, seed):
    """Tạo SurveyRequest + 1 SurveyRequestLine ở trạng thái processing."""
    sr = SurveyRequest(
        code="YCKS-HIDE-TEST",
        status="processing",
        company_id=seed.company_id,
        created_by=seed.u_req_id,
        updated_by=seed.u_req_id,
    )
    db.add(sr)
    db.flush()
    ln = SurveyRequestLine(
        survey_request_id=sr.id,
        item_group="Nhãn",
        requirement_detail="Test ẩn NCC",
        request_qty=100,
        uom="cuộn",
        assignee=seed.emp_nstm_code,
        created_by=seed.u_req_id,
        updated_by=seed.u_req_id,
    )
    db.add(ln)
    db.flush()
    ln.internal_line_code = f"YCKSL{ln.id:06d}"
    db.commit()
    return sr, ln


class TestNccHiding:
    def test_opt_public_excludes_banned_fields(self, db, seed):
        """Option trả qua _out_result không được chứa bất kỳ field bị cấm."""
        sr, ln = _make_sr(db, seed)
        opt = S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        result = C._out_result(db, sr)

        # Lấy options của line đầu tiên
        lines = result["lines"]
        assert lines, "Phải có ít nhất 1 line trong kết quả"
        options = lines[0]["options"]
        assert options, "Phải có ít nhất 1 option"

        for opt_dict in options:
            for banned in BANNED_FIELDS:
                assert banned not in opt_dict, (
                    f"Field bị cấm '{banned}' xuất hiện trong option public: {list(opt_dict.keys())}"
                )

    def test_opt_public_includes_required_fields(self, db, seed):
        """Option trả qua _out_result phải có đủ các field bắt buộc."""
        sr, ln = _make_sr(db, seed)
        S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        result = C._out_result(db, sr)

        lines = result["lines"]
        options = lines[0]["options"]
        assert options

        for req in REQUIRED_FIELDS:
            assert req in options[0], f"Field bắt buộc '{req}' bị thiếu trong option public"

    def test_opt_public_has_correct_product_name(self, db, seed):
        """snap_product_name phải khớp với product_name của SurveyProductLine."""
        sr, ln = _make_sr(db, seed)
        S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        result = C._out_result(db, sr)
        opt_dict = result["lines"][0]["options"][0]
        assert opt_dict["snap_product_name"] == "Nhãn Sản Phẩm A"

    def test_opt_public_has_price(self, db, seed):
        """snap_price_by_volume phải là số > 0."""
        sr, ln = _make_sr(db, seed)
        S.create_option(db, ln, seed.psl_nhan_1_id, seed.u_nstm_id)
        result = C._out_result(db, sr)
        opt_dict = result["lines"][0]["options"][0]
        assert float(opt_dict["snap_price_by_volume"]) > 0


class TestIsPurchaser:
    def _profile(self, scope):
        return {
            "grants": [{"perms": {"survey_request": {"read": True, "scope": scope}}}],
            "employee_id": 1,
            "emp_code": "EMP",
        }

    def test_own_scope_is_not_purchaser(self):
        """scope='own' (người YC) → KHÔNG phải purchaser."""
        assert S.is_purchaser(self._profile("own")) is False

    def test_proc_scope_is_purchaser(self):
        """scope='proc' (NSTM) → là purchaser."""
        assert S.is_purchaser(self._profile("proc")) is True

    def test_dept_scope_is_not_purchaser(self):
        """scope='dept' (trưởng BP) → KHÔNG phải purchaser."""
        assert S.is_purchaser(self._profile("dept")) is False

    def test_all_scope_is_purchaser(self):
        """scope='all' (Admin/Quản lý) → là purchaser."""
        assert S.is_purchaser(self._profile("all")) is True

    def test_empty_grants_is_not_purchaser(self):
        """Profile không có grant → KHÔNG phải purchaser."""
        assert S.is_purchaser({"grants": [], "employee_id": 1, "emp_code": "X"}) is False
