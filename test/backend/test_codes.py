"""
test_codes.py — Kiểm tra _gen_code và _gen_pr_code.

Test 1: _gen_code → khớp regex ^YCKS\\d{6}\\d{2}$.
Test 2: 2 SR liên tiếp → seq tăng (seq thứ 2 > seq thứ 1).
Test 3: _gen_pr_code → khớp regex ^PYC\\d{6}\\d{2}$.
Test 4: 2 PR code liên tiếp → seq tăng.
"""
import re
import pytest
from app.modules.survey_request import service as S
from app.modules.survey_request.model import SurveyRequest
from app.modules.purchase_request.model import PurchaseRequest


YCKS_PATTERN = re.compile(r"^YCKS\d{6}\d{2}$")
PYC_PATTERN = re.compile(r"^PYC\d{6}\d{2}$")


class TestGenCode:
    def test_gen_code_format(self, db, seed):
        """_gen_code → format YCKS + DDMMYY + 2-digit seq."""
        code = S._gen_code(db)
        assert YCKS_PATTERN.match(code), (
            f"_gen_code trả '{code}' không khớp pattern {YCKS_PATTERN.pattern}"
        )

    def test_gen_code_starts_with_ycks(self, db, seed):
        """_gen_code → bắt đầu bằng 'YCKS'."""
        code = S._gen_code(db)
        assert code.startswith("YCKS")

    def test_gen_code_seq_increments(self, db, seed):
        """Tạo 2 SR liên tiếp → seq tăng dần."""
        code1 = S._gen_code(db)
        # Tạo SR thật với code1 để counter tăng
        sr1 = SurveyRequest(
            code=code1,
            status="draft",
            company_id=seed.company_id,
            created_by=seed.u_req_id,
            updated_by=seed.u_req_id,
        )
        db.add(sr1)
        db.commit()

        code2 = S._gen_code(db)
        # Seq trong code2 phải lớn hơn seq trong code1
        seq1 = int(code1[-2:])
        seq2 = int(code2[-2:])
        assert seq2 > seq1, f"Seq không tăng: code1={code1}, code2={code2}"

    def test_gen_code_seq_is_two_digits(self, db, seed):
        """Seq phải luôn là 2 chữ số (có zero-padding)."""
        code = S._gen_code(db)
        # seq = 2 ký tự cuối
        seq_str = code[-2:]
        assert seq_str.isdigit(), f"2 ký tự cuối '{seq_str}' không phải số"
        assert len(seq_str) == 2


class TestGenPrCode:
    def test_gen_pr_code_format(self, db, seed):
        """_gen_pr_code → format PYC + DDMMYY + 2-digit seq."""
        code = S._gen_pr_code(db)
        assert PYC_PATTERN.match(code), (
            f"_gen_pr_code trả '{code}' không khớp pattern {PYC_PATTERN.pattern}"
        )

    def test_gen_pr_code_starts_with_pyc(self, db, seed):
        """_gen_pr_code → bắt đầu bằng 'PYC'."""
        code = S._gen_pr_code(db)
        assert code.startswith("PYC")

    def test_gen_pr_code_with_request_date(self, db, seed):
        """_gen_pr_code với request_date='2026-07-07' → PYC070726..."""
        code = S._gen_pr_code(db, "2026-07-07")
        # DDMMYY = 070726
        assert code.startswith("PYC070726"), f"Code '{code}' không bắt đầu bằng PYC070726"

    def test_gen_pr_code_seq_increments(self, db, seed):
        """Tạo 2 PR liên tiếp → seq tăng."""
        today = "2026-07-07"
        code1 = S._gen_pr_code(db, today)
        # Tạo PR thật để counter tăng
        pr1 = PurchaseRequest(
            code=code1,
            status="draft",
            company_id=seed.company_id,
            created_by=seed.u_req_id,
            updated_by=seed.u_req_id,
        )
        db.add(pr1)
        db.commit()

        code2 = S._gen_pr_code(db, today)
        seq1 = int(code1[-2:])
        seq2 = int(code2[-2:])
        assert seq2 > seq1, f"PR seq không tăng: code1={code1}, code2={code2}"

    def test_gen_pr_code_fallback_to_today_when_no_date(self, db, seed):
        """_gen_pr_code không có request_date → dùng ngày hôm nay."""
        from datetime import datetime
        today_prefix = "PYC" + datetime.now().strftime("%d%m%y")
        code = S._gen_pr_code(db)
        assert code.startswith(today_prefix), (
            f"Code '{code}' không bắt đầu bằng '{today_prefix}'"
        )
